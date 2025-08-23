# -*- coding: utf-8 -*-
"""
Fault Detector.

This module is responsible for detecting anomalies in sensor data,
distinguishing between sensor faults and actual system changes.
"""

import logging
import numpy as np
from collections import deque

logger = logging.getLogger(__name__)

class FaultDetector:
    def __init__(self, config, gate_model):
        """
        Initializes the fault detector.
        """
        self.config = config
        self.gate_model = gate_model

        # --- Fault detection parameters ---
        self.window_size = 20
        self.redundancy_threshold = 0.20 # 20% deviation
        self.noise_factor_threshold = 3.0
        self.drift_threshold_h = 0.1 # 10cm drift for water level
        self.drift_threshold_q = 1.0 # 1 m^3/s drift for flow

        # --- State tracking ---
        self.reading_windows = {} # {'sensor_id': deque([val1, val2, ...])}
        self.active_faults = {}   # {'sensor_id': 'fault_type'}
        logger.debug("Fault Detector initialized.")

    def reset(self):
        """Resets the fault detector's state."""
        self.active_faults.clear()
        self.reading_windows.clear()
        logger.info("Fault detector has been reset.")

    def _update_windows(self, cleaned_data):
        """Update the moving windows with new sensor data."""
        for sensor_id, value in cleaned_data.items():
            if sensor_id not in self.reading_windows:
                self.reading_windows[sensor_id] = deque(maxlen=self.window_size)
            self.reading_windows[sensor_id].append(value)

    def _check_increased_noise(self, sensor_id, window):
        """Check for statistically significant increase in noise."""
        std_dev = np.std(window)
        is_water_level = 'h' in sensor_id
        base_noise = self.config.NOISE_LEVEL_WATER_LEVEL if is_water_level else self.config.NOISE_LEVEL_FLOW
        noise_threshold = base_noise * self.noise_factor_threshold

        if std_dev > noise_threshold:
            return f"Increased Noise (StdDev: {std_dev:.3f} > {noise_threshold:.3f})"
        return None

    def _check_model_deviation(self, sensor_id, window, model_b_predictions):
        """Check for significant deviation from the twin model's prediction (detects drift/bias)."""
        if sensor_id not in model_b_predictions:
            return None

        prediction = model_b_predictions[sensor_id]
        residuals = [reading - prediction for reading in window]
        mean_residual = np.mean(residuals)

        threshold = self.drift_threshold_h if 'h' in sensor_id else self.drift_threshold_q

        if abs(mean_residual) > threshold:
            return f"Model Deviation (Mean Residual: {mean_residual:.3f})"
        return None

    def _check_redundancy(self, reliable_data, gate_opening, gate_cq_estimate):
        """Check for inconsistencies using physical redundancy (gate equation)."""
        sensor_id = 'q_gate_down'
        if sensor_id in self.active_faults or not all(k in reliable_data for k in ['h_gate_up', 'h_gate_down', sensor_id]):
            return None, None

        h_up = reliable_data['h_gate_up']
        h_down = reliable_data['h_gate_down']
        q_sensor = reliable_data[sensor_id]

        q_calc = self.gate_model.calculate_flow(h_up, h_down, gate_opening, gate_cq_estimate)

        # Check for two conditions: 1) sensor stuck at low value when it should be high, 2) relative deviation is large
        is_stuck = q_sensor < 0.1 and q_calc > 1.0
        is_deviating = q_sensor > 0.1 and abs(q_calc - q_sensor) / q_sensor > self.redundancy_threshold

        if is_stuck or is_deviating:
            return sensor_id, f"Redundancy Error (Calc: {q_calc:.2f}, Sensor: {q_sensor:.2f})"
        return None, None

    def diagnose(self, cleaned_data, model_b_predictions, gate_opening, gate_cq_estimate):
        """
        Performs diagnosis on the latest set of cleaned sensor data.
        """
        self._update_windows(cleaned_data)
        status_messages = []

        # First, run checks on all sensors that are not already flagged
        for sensor_id, window in self.reading_windows.items():
            if sensor_id in self.active_faults or len(window) < self.window_size:
                continue

            fault_reason = self._check_increased_noise(sensor_id, window)
            if not fault_reason:
                 # For now, let's assume model deviation check is not yet implemented
                 # fault_reason = self._check_model_deviation(sensor_id, window, model_b_predictions)
                 pass

            if fault_reason:
                fault_msg = f"Fault detected in '{sensor_id}'! (Type: {fault_reason}). Isolating sensor."
                logger.warning(fault_msg)
                status_messages.append(fault_msg)
                self.active_faults[sensor_id] = fault_reason

        # Run redundancy check on data that has not been flagged yet
        temp_reliable_data = {k: v for k, v in cleaned_data.items() if k not in self.active_faults}
        faulty_sensor, fault_reason = self._check_redundancy(temp_reliable_data, gate_opening, gate_cq_estimate)
        if faulty_sensor:
            fault_msg = f"Fault detected in '{faulty_sensor}'! (Type: {fault_reason}). Isolating sensor."
            logger.warning(fault_msg)
            status_messages.append(fault_msg)
            self.active_faults[faulty_sensor] = fault_reason

        # Prepare final output
        reliable_data = {k: v for k, v in cleaned_data.items() if k not in self.active_faults}

        for sensor_id, reason in self.active_faults.items():
            status_messages.append(f"INFO: Sensor '{sensor_id}' is isolated due to: {reason}.")

        if not status_messages:
            final_status = "All systems nominal."
        else:
            final_status = " | ".join(sorted(list(set(status_messages))))

        return reliable_data, final_status
