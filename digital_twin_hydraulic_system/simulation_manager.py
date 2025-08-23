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

        # --- EKF Initialization for State and Parameter Estimation---
        nx = self.config.NUM_CELLS
        n_states = 2 * nx
        n_params = 1 # Just manning_n
        n_aug = n_states + n_params

        # Initial state estimate (A, Q) from the twin's FVM
        x_hydraulic_initial = np.concatenate([self.model_twin_fvm.A[1:-1], self.model_twin_fvm.Q[1:-1]])
        # Initial parameter estimate (n) from config
        x_param_initial = np.array([self.config.INITIAL_MANNING_GUESS])
        x_initial = np.concatenate([x_hydraulic_initial, x_param_initial])

        # Initial covariance P: diagonal, with higher uncertainty for the parameter
        P_hydraulic = np.identity(n_states) * 0.1
        P_param = np.identity(n_params) * (0.01**2) # High uncertainty on n
        P_initial = np.block([
            [P_hydraulic, np.zeros((n_states, n_params))],
            [np.zeros((n_params, n_states)), P_param]
        ])

        # Process noise Q: Add process noise for the parameter n
        Q_hydraulic = np.identity(n_states) * self.config.PROCESS_NOISE_Q_FACTOR
        Q_param = np.identity(n_params) * (1e-7**2) # Low process noise on n (it changes slowly)
        Q = np.block([
            [Q_hydraulic, np.zeros((n_states, n_params))],
            [np.zeros((n_params, n_states)), Q_param]
        ])

        # Measurement noise R (remains the same size)
        r_h = self.config.NOISE_LEVEL_WATER_LEVEL**2
        r_q = self.config.NOISE_LEVEL_FLOW**2
        R = np.diag([r_h, r_q]) * self.config.MEASUREMENT_NOISE_R_FACTOR

        self.ekf = ExtendedKalmanFilter(self.model_twin_fvm, x_initial, P_initial, Q, R)

        # --- General State Initialization ---
        self.gate_opening = config.GATE_INITIAL_OPENING
        self.identified_params = self.identifier.get_identified_params()
        self.perturbations = []
        self.reset_simulation_state()

        logger.info("Simulation Manager initialized successfully with EKF.")

    def reset_simulation_state(self):
        """Resets the time-dependent state of the simulation."""
        self.timestamp = 0.0
        self.p_idx = 0
        self.h_true_gate_upstream = self.config.INITIAL_WATER_DEPTH
        logger.info("Simulation state has been reset.")

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
            sensor_id = params.pop('sensor_id', None)
            fault_type = params.pop('fault_type', None)
            if sensor_id and fault_type:
                self.sensor_sim.induce_fault(sensor_id, fault_type, **params)
        else:
            logger.warning(f"Unknown perturbation type '{p_type}'")

    def _get_observation_model(self, state_vector):
        """
        Calculates the expected sensor readings (h_func) and the observation
        Jacobian (H_jac) from the current augmented state vector.
        """
        nx = self.config.NUM_CELLS
        n_aug = 2 * nx + 1
        H_jac = np.zeros((2, n_aug))
        A_nx = state_vector[nx-1]
        h_nx = self.model_twin_fvm._get_depth_from_area_scalar(A_nx)
        b = self.config.CHANNEL_BOTTOM_WIDTH
        z = self.config.CHANNEL_SIDE_SLOPE
        H_jac[0, nx-1] = 1.0 / (b + 2 * z * h_nx) if (b + 2 * z * h_nx) > 1e-6 else 0.0
        H_jac[1, 2*nx-1] = 1.0
        def h_func(x):
            h = self.model_twin_fvm._get_depth_from_area_scalar(x[nx-1])
            q = x[2*nx-1]
            return np.array([h, q])
        return h_func, H_jac

    def step_simulation(self, num_steps=1):
        """
        Executes a given number of simulation steps.
        """
        for _ in range(num_steps):
            if self.timestamp >= self.config.SIMULATION_DURATION:
                logger.info("Simulation duration reached.")
                return False # Indicate simulation is finished

            dt = self.model_a._calculate_cfl_dt()
            if self.timestamp + dt > self.config.SIMULATION_DURATION:
                dt = self.config.SIMULATION_DURATION - self.timestamp

            if self.p_idx < len(self.perturbations) and self.timestamp >= self.perturbations[self.p_idx]['time']:
                self._apply_perturbation(self.perturbations[self.p_idx]['type'], self.perturbations[self.p_idx]['params'])
                self.p_idx += 1

            self.model_a.step(dt, {'type': 'inflow', 'value': self.config.UPSTREAM_INFLOW}, {'type': 'fixed_depth', 'value': self.h_true_gate_upstream})
            model_a_state = self.model_a.get_state()
            self.h_true_gate_upstream = model_a_state['h'][-1]
            q_true_gate = self.gate_model.calculate_flow(self.h_true_gate_upstream, self.config.INITIAL_WATER_DEPTH, self.gate_opening, self.config.GATE_DISCHARGE_COEFFICIENT_TRUE)
            true_values = {'h_gate_up': self.h_true_gate_upstream, 'q_gate_down': q_true_gate}

            h_twin_gate_up = self.model_twin_fvm._get_depth_from_area_scalar(self.ekf.x[self.config.NUM_CELLS-1])
            self.ekf.predict(dt, {'type': 'inflow', 'value': self.config.UPSTREAM_INFLOW}, {'type': 'fixed_depth', 'value': h_twin_gate_up})

            raw_readings = self.sensor_sim.get_readings(true_values, dt)
            z = np.array([raw_readings.get('h_gate_up', 0), raw_readings.get('q_gate_down', 0)])
            h_func, H_jac = self._get_observation_model(self.ekf.x)

            # --- Fault Detection & EKF Update ---
            # First, diagnose faults based on the PREDICTED state vs sensor readings
            cleaned_readings = self.preprocessor.filter(raw_readings)
            nx = self.config.NUM_CELLS
            h_twin_pred = self.model_twin_fvm._get_depth_from_area_scalar(self.ekf.x[nx-1])
            q_twin_pred = self.ekf.x[2*nx-1]
            model_predictions = {'h_gate_up': h_twin_pred, 'q_gate_down': q_twin_pred}

            _, status_msg, active_faults = self.fault_detector.diagnose(
                cleaned_readings, model_predictions, self.gate_opening, self.config.INITIAL_GATE_COEFF_GUESS
            )

            # Now, create a custom R matrix for the EKF update step
            # If a sensor has a fault, we dramatically increase its noise variance
            # to make the EKF ignore its measurement.
            R_step = self.ekf.R.copy()
            if 'h_gate_up' in active_faults:
                R_step[0, 0] *= 1e6
            if 'q_gate_down' in active_faults:
                R_step[1, 1] *= 1e6

            # Update the EKF with the (potentially untrustworthy) measurements
            self.ekf.update(z, H_jac, h_func, R_override=R_step)

            h_twin_best_est = self.model_twin_fvm._get_depth_from_area_scalar(self.ekf.x[self.config.NUM_CELLS-1])
            self.visualizer.log_state(self.timestamp, {
                'h_true': self.h_true_gate_upstream,
                'h_twin': h_twin_best_est,
                'n_true': self.model_a.manning_n,
                'n_est': self.ekf.x[-1],
                'status': status_msg
            })
            self.timestamp += dt

        return True # Indicate simulation is ongoing

    def run_full_simulation(self):
        """Runs the entire simulation from start to finish (for non-interactive modes)."""
        logger.info(f"Starting full EKF simulation for {self.config.SIMULATION_DURATION} seconds...")
        self.reset_simulation_state()
        log_time_tracker = -100
        while self.step_simulation(num_steps=1):
            if self.timestamp - log_time_tracker >= 50:
                nx = self.config.NUM_CELLS
                h_twin_best_est = self.model_twin_fvm._get_depth_from_area_scalar(self.ekf.x[nx-1])
                n_est = self.ekf.x[-1]
                logger.info(f"T={self.timestamp:5.1f}s | h_true={self.h_true_gate_upstream:.3f}, h_twin_est={h_twin_best_est:.3f} | n_est={n_est:.4f}")
                log_time_tracker = self.timestamp
        logger.info("Full simulation finished.")
        self.visualizer.plot_water_levels()
        self.visualizer.plot_parameter_convergence('n_est', 'n_true', 'Manning\'s n')
