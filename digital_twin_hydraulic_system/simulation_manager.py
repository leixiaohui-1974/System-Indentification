# -*- coding: utf-8 -*-
"""
Simulation Manager.

This class orchestrates the entire simulation, including the main loop,
data flow between components, and triggering of events/perturbations.
"""

from . import config
from .models import FVMChannelModel, IDChannelModel, GateModel
from .diagnostics import DataPreprocessor, FaultDetector, SystemIdentifier, ExtendedKalmanFilter
from .sensor_simulator import SensorSimulator
from .visualization import Visualizer

import numpy as np
import time
import logging
from . import config

logger = logging.getLogger(__name__)

class SimulationManager:
    def __init__(self, config):
        self.config = config
        logger.info("Initializing components...")

        # --- Component Initialization ---
        self.gate_model = GateModel(config)
        self.model_a = FVMChannelModel(config) # "Real World"
        self.model_twin_fvm = FVMChannelModel(config) # Twin's internal physics model
        self.model_b = IDChannelModel(config) # Simplified twin model

        self.sensor_sim = SensorSimulator(config)
        self.preprocessor = DataPreprocessor()
        self.identifier = SystemIdentifier(config)
        self.fault_detector = FaultDetector(config, self.gate_model)
        self.visualizer = Visualizer()

        # --- EKF Initialization ---
        nx = self.config.NUM_CELLS
        n_states = 2 * nx

        # Initial state estimate (from the twin's FVM)
        x_initial = np.concatenate([self.model_twin_fvm.A[1:-1], self.model_twin_fvm.Q[1:-1]])

        # Initial covariance: diagonal, assuming some initial uncertainty
        P_initial = np.identity(n_states) * 0.1

        # Process noise covariance Q
        Q = np.identity(n_states) * self.config.PROCESS_NOISE_Q_FACTOR

        # Measurement noise covariance R
        # Assuming 2 measurements: h_gate_up, q_gate_down
        # Their variances are based on sensor noise levels
        r_h = self.config.NOISE_LEVEL_WATER_LEVEL**2
        r_q = self.config.NOISE_LEVEL_FLOW**2
        R = np.diag([r_h, r_q]) * self.config.MEASUREMENT_NOISE_R_FACTOR

        self.ekf = ExtendedKalmanFilter(self.model_twin_fvm, x_initial, P_initial, Q, R)

        # --- General State Initialization ---
        self.gate_opening = config.GATE_INITIAL_OPENING
        self.identified_params = self.identifier.get_identified_params()
        self.perturbations = []

        logger.info("Simulation Manager initialized successfully with EKF.")

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
            # Pop the main identifiers, pass the rest as fault parameters (e.g., value)
            sensor_id = params.pop('sensor_id', None)
            fault_type = params.pop('fault_type', None)
            if sensor_id and fault_type:
                self.sensor_sim.induce_fault(sensor_id, fault_type, **params)
        else:
            logger.warning(f"Unknown perturbation type '{p_type}'")

    def _get_observation_model(self, state_vector):
        """
        Calculates the expected sensor readings (h_func) and the observation
        Jacobian (H_jac) from the current state vector.
        """
        nx = self.config.NUM_CELLS
        n_states = 2 * nx

        # We observe h_gate_up (from A_nx) and q_gate_down (which is Q_nx)
        H_jac = np.zeros((2, n_states))

        # 1. Derivative of h_gate_up wrt A_nx
        A_nx = state_vector[nx-1]
        h_nx = self.model_twin_fvm._get_depth_from_area_scalar(A_nx)
        b = self.config.CHANNEL_BOTTOM_WIDTH
        z = self.config.CHANNEL_SIDE_SLOPE
        # dh/dA = 1 / (b + 2zh)
        H_jac[0, nx-1] = 1.0 / (b + 2 * z * h_nx) if (b + 2 * z * h_nx) > 1e-6 else 0.0

        # 2. Derivative of q_gate_down wrt Q_nx
        H_jac[1, 2*nx-1] = 1.0

        # This function calculates what the sensors should read given a state vector
        def h_func(x):
            h = self.model_twin_fvm._get_depth_from_area_scalar(x[nx-1])
            q = x[2*nx-1]
            return np.array([h, q])

        return h_func, H_jac

    def run_simulation(self):
        """
        Executes the main simulation loop, now driven by the EKF.
        """
        logger.info(f"Starting EKF simulation for {self.config.SIMULATION_DURATION} seconds...")

        timestamp = 0.0
        p_idx = 0
        log_time_tracker = -100

        # Initial downstream BC for the 'real' model
        h_true_gate_upstream = self.config.INITIAL_WATER_DEPTH

        while timestamp < self.config.SIMULATION_DURATION:
            # Determine timestep, ensuring it doesn't overshoot the end time
            dt = self.model_a._calculate_cfl_dt()
            if timestamp + dt > self.config.SIMULATION_DURATION:
                dt = self.config.SIMULATION_DURATION - timestamp

            # --- Perturbation Step ---
            if p_idx < len(self.perturbations) and timestamp >= self.perturbations[p_idx]['time']:
                event = self.perturbations[p_idx]
                self._apply_perturbation(event['type'], event['params'])
                p_idx += 1

            # --- "Real World" Model Step ---
            real_upstream_bc = {'type': 'inflow', 'value': self.config.UPSTREAM_INFLOW}
            real_downstream_bc = {'type': 'fixed_depth', 'value': h_true_gate_upstream}
            self.model_a.step(dt, real_upstream_bc, real_downstream_bc)

            model_a_state = self.model_a.get_state()
            h_true_gate_upstream = model_a_state['h'][-1]
            h_true_gate_downstream = self.config.INITIAL_WATER_DEPTH
            q_true_gate = self.gate_model.calculate_flow(h_true_gate_upstream, h_true_gate_downstream, self.gate_opening, self.config.GATE_DISCHARGE_COEFFICIENT_TRUE)
            true_values = {'h_gate_up': h_true_gate_upstream, 'q_gate_down': q_true_gate}

            # --- EKF Cycle: Predict and Update ---
            # 1. Predict the twin's state
            twin_upstream_bc = {'type': 'inflow', 'value': self.config.UPSTREAM_INFLOW}
            # The twin's downstream BC is its own last known water depth
            h_twin_gate_up = self.model_twin_fvm._get_depth_from_area_scalar(self.ekf.x[self.config.NUM_CELLS-1])
            twin_downstream_bc = {'type': 'fixed_depth', 'value': h_twin_gate_up}
            self.ekf.predict(dt, twin_upstream_bc, twin_downstream_bc)

            # 2. Get sensor readings and update the EKF estimate
            raw_readings = self.sensor_sim.get_readings(true_values, dt)
            # For the EKF, we assume we have sensors for the states we want to correct
            z = np.array([raw_readings.get('h_gate_up', 0), raw_readings.get('q_gate_down', 0)])

            h_func, H_jac = self._get_observation_model(self.ekf.x)
            self.ekf.update(z, H_jac, h_func)

            # --- Logging and Visualization ---
            if timestamp - log_time_tracker >= 50:
                nx = self.config.NUM_CELLS
                h_twin_best_estimate = self.model_twin_fvm._get_depth_from_area_scalar(self.ekf.x[nx-1])
                log_msg = (
                    f"T={timestamp:5.1f}s | "
                    f"h_true={h_true_gate_upstream:.3f}, h_twin_est={h_twin_best_estimate:.3f}"
                )
                logger.info(log_msg)
                log_time_tracker = timestamp

            # Log data for plotting
            self.visualizer.log_state(timestamp, {
                'h_true': h_true_gate_upstream,
                'h_twin': self.model_twin_fvm._get_depth_from_area_scalar(self.ekf.x[self.config.NUM_CELLS-1])
            })

            timestamp += dt

        logger.info("Simulation finished.")
        self.visualizer.plot_water_levels()
