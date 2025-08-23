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

class SimulationManager:
    def __init__(self, config):
        self.config = config

        # 1. Initialize all components
        print("Initializing components...")
        self.gate_model = GateModel(config)
        self.model_a = FVMChannelModel(config) # High-fidelity "real world"
        self.model_b = IDChannelModel(config)  # Simplified "digital twin"

        self.sensor_sim = SensorSimulator(config)
        self.preprocessor = DataPreprocessor()
        self.identifier = SystemIdentifier(config)
        self.fault_detector = FaultDetector(config, self.gate_model)

        self.visualizer = Visualizer()

        # Initial state
        self.gate_opening = config.GATE_INITIAL_OPENING
        self.identified_params = self.identifier.get_identified_params()

        print("Simulation Manager initialized successfully.")

    def __init__(self, config):
        self.config = config

        # 1. Initialize all components
        print("Initializing components...")
        self.gate_model = GateModel(config)
        self.model_a = FVMChannelModel(config) # High-fidelity "real world"
        self.model_b = IDChannelModel(config)  # Simplified "digital twin"

        self.sensor_sim = SensorSimulator(config)
        self.preprocessor = DataPreprocessor()
        self.identifier = SystemIdentifier(config)
        self.fault_detector = FaultDetector(config, self.gate_model)

        self.visualizer = Visualizer()

        # Initial state & scenario planning
        self.gate_opening = config.GATE_INITIAL_OPENING
        self.identified_params = self.identifier.get_identified_params()
        self.perturbations = []

        print("Simulation Manager initialized successfully.")

    def add_perturbation(self, event_time, event_type, **kwargs):
        """Adds a scenario event to the simulation timeline."""
        self.perturbations.append({'time': event_time, 'type': event_type, 'params': kwargs})
        self.perturbations.sort(key=lambda x: x['time']) # Keep events in order
        print(f"INFO: Scheduled perturbation '{event_type}' at t={event_time}s.")

    def _apply_perturbation(self, p_type, params):
        """Internal method to execute a perturbation."""
        print(f"\n--- Applying Perturbation: {p_type} ---")
        if p_type == 'roughness_change':
            new_n = params.get('new_roughness', self.model_a.manning_n)
            self.model_a.manning_n = new_n
            print(f"Model A (real world) Manning's n changed to {new_n}")
        elif p_type == 'sensor_fault':
            sensor_id = params.get('sensor_id')
            fault_type = params.get('fault_type')
            self.sensor_sim.induce_fault(sensor_id, fault_type)
        else:
            print(f"WARNING: Unknown perturbation type '{p_type}'")
        print("----------------------------------------\n")

    def run_simulation(self):
        """
        Executes the main simulation loop.
        """
        print(f"Starting simulation for {self.config.SIMULATION_DURATION} seconds...")

        num_steps = int(self.config.SIMULATION_DURATION / self.config.TIMESTEP)
        p_idx = 0 # Perturbation index

        for i in range(num_steps):
            timestamp = i * self.config.TIMESTEP

            # Check for and apply scheduled perturbations
            if p_idx < len(self.perturbations) and timestamp >= self.perturbations[p_idx]['time']:
                event = self.perturbations[p_idx]
                self._apply_perturbation(event['type'], event['params'])
                p_idx += 1

            # 1. Step the "Real World" Model (Model A)
            downstream_bc = {'type': 'depth', 'value': self.config.INITIAL_WATER_DEPTH}
            self.model_a.step(self.config.TIMESTEP, None, downstream_bc)

            # 2. Extract True Values at Sensor Locations
            h_true_downstream = self.model_a.get_state()['h'][0]
            q_true_downstream = self.model_a.get_state()['Q'][0]
            h_true_upstream = self.config.INITIAL_WATER_DEPTH * 1.2

            true_values = {
                'h_gate_up': h_true_upstream, 'h_gate_down': h_true_downstream, 'q_gate_down': q_true_downstream
            }

            # 3. Simulate and Process Sensor Data
            raw_readings = self.sensor_sim.get_readings(true_values)
            cleaned_readings = self.preprocessor.filter(raw_readings)

            # 4. Diagnose Faults
            gate_cq_est = self.config.INITIAL_GATE_COEFF_GUESS # Placeholder for now
            reliable_data, status_msg = self.fault_detector.diagnose(cleaned_readings, self.gate_opening, gate_cq_est)

            # 5. System Identification (if data is reliable)
            if 'h_gate_down' in reliable_data and 'q_gate_down' in reliable_data:
                y_k = reliable_data['h_gate_down']
                # Ensure buffer is full enough before accessing delayed input
                if len(self.model_b.input_buffer) > self.model_b.delay_steps:
                    delayed_input = self.model_b.input_buffer[self.model_b.delay_steps]
                    phi_k = np.array([self.model_b.h_down_prev, delayed_input])
                    self.identifier.run_rls_step(y_k, phi_k)

            # 6. Update Digital Twin (Model B)
            self.identified_params = self.identifier.get_identified_params()
            self.model_b.update_params(self.identified_params['model_b_params'])

            q_input_for_b = self.gate_model.calculate_flow(
                h_true_upstream, h_true_downstream, self.gate_opening, self.config.GATE_DISCHARGE_COEFFICIENT_TRUE
            )
            model_b_prediction = self.model_b.step(self.config.TIMESTEP, q_input_for_b)

            # 7. Log and Print Status
            log_state = {
                'h_true': h_true_downstream,
                'h_twin': model_b_prediction,
                'param_a1': self.identified_params['model_b_params']['a1'],
                'param_b1': self.identified_params['model_b_params']['b1'],
                'status': status_msg
            }
            self.visualizer.log_state(timestamp, log_state)

            if i % 100 == 0:
                print(f"T={timestamp:5.0f}s | {status_msg} | h_true={h_true_downstream:.3f}, h_twin={model_b_prediction:.3f} | a1={log_state['param_a1']:.3f}, b1={log_state['param_b1']:.3f}")

        print("Simulation finished.")
        # 8. Visualize Results
        self.visualizer.plot_water_levels()
        self.visualizer.plot_parameter_convergence('param_a1')
        self.visualizer.plot_parameter_convergence('param_b1')
