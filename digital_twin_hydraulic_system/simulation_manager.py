# -*- coding: utf-8 -*-
"""
Simulation Manager.

This class orchestrates the entire simulation, including the main loop,
data flow between components, and triggering of events/perturbations.
"""

from . import config
from .models import FVMChannelModel, IDChannelModel, GateModel
from .diagnostics import DataPreprocessor, FaultDetector, SystemIdentifier
from .sensor_simulator import SensorSimulator
from .visualization import Visualizer

import numpy as np
import time
import logging
from . import config
from .models import FVMChannelModel, IDChannelModel, GateModel
from .diagnostics import DataPreprocessor, FaultDetector, SystemIdentifier
from .sensor_simulator import SensorSimulator
from .visualization import Visualizer

logger = logging.getLogger(__name__)

class SimulationManager:
    def __init__(self, config):
        self.config = config

        # 1. Initialize all components
        logger.info("Initializing components...")
        self.gate_model = GateModel(config)
        self.model_a = FVMChannelModel(config) # High-fidelity "real world"
        self.model_b = IDChannelModel(config)  # Simplified "digital twin"

        self.sensor_sim = SensorSimulator(config)
        self.preprocessor = DataPreprocessor()
        self.identifier = SystemIdentifier(config)
        self.fault_detector = FaultDetector(config, self.gate_model)

        self.visualizer = Visualizer()

        # 2. Set initial state
        self.gate_opening = config.GATE_INITIAL_OPENING
        self.identified_params = self.identifier.get_identified_params()
        self.perturbations = []

        logger.info("Simulation Manager initialized successfully.")

    def add_perturbation(self, event_time, event_type, **kwargs):
        """Adds a scenario event to the simulation timeline."""
        self.perturbations.append({'time': event_time, 'type': event_type, 'params': kwargs})
        self.perturbations.sort(key=lambda x: x['time'])
        logger.info(f"Scheduled perturbation '{event_type}' at t={event_time}s.")

    def _apply_perturbation(self, p_type, params):
        """Internal method to execute a perturbation."""
        logger.warning(f"--- Applying Perturbation: {p_type} ---")
        if p_type == 'roughness_change':
            new_n = params.get('new_roughness', self.model_a.manning_n)
            self.model_a.manning_n = new_n
            logger.info(f"Model A (real world) Manning's n changed to {new_n}")
        elif p_type == 'sensor_fault':
            sensor_id = params.get('sensor_id')
            fault_type = params.get('fault_type')
            self.sensor_sim.induce_fault(sensor_id, fault_type)
        else:
            logger.warning(f"Unknown perturbation type '{p_type}'")

    def run_simulation(self):
        """
        Executes the main simulation loop using an adaptive timestep.
        """
        logger.info(f"Starting simulation for {self.config.SIMULATION_DURATION} seconds...")

        timestamp = 0.0
        p_idx = 0
        log_time_tracker = -100 # To ensure the first log prints at T=0

        # Initialize the downstream boundary condition (water level at the gate)
        h_true_gate_upstream = self.config.INITIAL_WATER_DEPTH

        while timestamp < self.config.SIMULATION_DURATION:
            # 1. Get adaptive timestep from the FVM model
            dt = self.model_a._calculate_cfl_dt()

            # 2. Check for and apply scheduled perturbations
            if p_idx < len(self.perturbations) and timestamp >= self.perturbations[p_idx]['time']:
                event = self.perturbations[p_idx]
                self._apply_perturbation(event['type'], event['params'])
                p_idx += 1

            # 3. Define boundary conditions and step the "Real World" Model (Model A)
            upstream_bc = {'type': 'inflow', 'value': self.config.UPSTREAM_INFLOW}
            # The downstream BC is the water level at the gate from the *previous* timestep
            downstream_bc = {'type': 'fixed_depth', 'value': h_true_gate_upstream}
            self.model_a.step(dt, upstream_bc, downstream_bc)

            # 4. Extract True Values from Model A for the sensors
            # The gate is at the downstream end of the channel, so we use the last cell's state.
            model_a_state = self.model_a.get_state()
            h_true_gate_upstream = model_a_state['h'][-1]

            # The "downstream" sensor is located some distance after the gate.
            # In this simplified setup, we assume a constant tailwater depth.
            h_true_gate_downstream = self.config.INITIAL_WATER_DEPTH

            # The flow through the gate is calculated by the gate model
            q_true_gate = self.gate_model.calculate_flow(
                h_up=h_true_gate_upstream,
                h_down=h_true_gate_downstream,
                opening=self.gate_opening,
                Cq=self.config.GATE_DISCHARGE_COEFFICIENT_TRUE
            )

            true_values = {
                'h_gate_up': h_true_gate_upstream,
                'h_gate_down': h_true_gate_downstream,
                'q_gate_down': q_true_gate
            }

            # 5. Simulate and Process Sensor Data
            raw_readings = self.sensor_sim.get_readings(true_values)
            cleaned_readings = self.preprocessor.filter(raw_readings)

            # 6. Diagnose Faults
            gate_cq_est = self.config.INITIAL_GATE_COEFF_GUESS
            reliable_data, status_msg = self.fault_detector.diagnose(cleaned_readings, self.gate_opening, gate_cq_est)

            # 7. System Identification (if data is reliable)
            if 'h_gate_down' in reliable_data and 'q_gate_down' in reliable_data:
                y_k = reliable_data['h_gate_down']
                if len(self.model_b.input_buffer) > self.model_b.delay_steps:
                    delayed_input = self.model_b.input_buffer[self.model_b.delay_steps]
                    phi_k = np.array([self.model_b.h_down_prev, delayed_input])
                    self.identifier.run_rls_step(y_k, phi_k)

            # 8. Update Digital Twin (Model B)
            self.identified_params = self.identifier.get_identified_params()
            self.model_b.update_params(self.identified_params['model_b_params'])

            q_input_for_b = self.gate_model.calculate_flow(
                h_up=h_true_gate_upstream,
                h_down=h_true_gate_downstream,
                opening=self.gate_opening,
                Cq=self.config.INITIAL_GATE_COEFF_GUESS # Using initial guess as it's not identified online yet
            )
            model_b_prediction = self.model_b.step(dt, q_input_for_b)

            # 9. Log and Print Status
            # 9. Log and Print Status
            if self.visualizer.plot_profiles:
                log_state = {'h_profile': self.model_a.get_state()['h']}
            else:
                log_state = {
                    'h_true': h_true_downstream,
                    'h_twin': model_b_prediction,
                    'param_a1': self.identified_params['model_b_params']['a1'],
                    'param_b1': self.identified_params['model_b_params']['b1'],
                    'status': status_msg
                }
            self.visualizer.log_state(timestamp, log_state)

            if timestamp - log_time_tracker >= 20: # Log more frequently for dam break
                current_h_profile = self.model_a.get_state()['h']
                log_msg = (
                    f"T={timestamp:5.1f}s | dt={dt:.3f}s | "
                    f"h_upstream={current_h_profile[0]:.3f}, h_gate_up={current_h_profile[-1]:.3f}"
                )
                logger.info(log_msg)
                log_time_tracker = timestamp

            # 10. Advance time
            timestamp += dt

        logger.info("Simulation finished.")

        # 11. Visualize Results
        if self.visualizer.plot_profiles:
            self.visualizer.plot_water_profiles()
        else:
            self.visualizer.plot_water_levels()
            self.visualizer.plot_parameter_convergence('param_a1')
            self.visualizer.plot_parameter_convergence('param_b1')
