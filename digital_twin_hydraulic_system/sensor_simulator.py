# -*- coding: utf-8 -*-
"""
Sensor Simulator.

This module is responsible for mimicking real-world sensors. It takes
true data from the high-fidelity model (Model A) and generates noisy
sensor readings. It can also simulate sensor faults.
"""
import numpy as np

class SensorSimulator:
    def __init__(self, config):
        self.config = config
        self.faults = {} # Dictionary to store fault configurations

    def get_readings(self, true_values):
        """
        Generates sensor readings from true physical values.

        Args:
            true_values (dict): A dictionary of true values, e.g.,
                                {'h_up': 3.0, 'q_down': 50.5}.

        Returns:
            dict: A dictionary of noisy sensor readings.
        """
        readings = {}
        for key, value in true_values.items():
            # Check if a fault is active for this sensor
            if key in self.faults:
                fault = self.faults[key]
                if fault['type'] == 'stuck_at_zero':
                    readings[key] = 0.0
                elif fault['type'] == 'drift':
                    readings[key] = value + fault['value'] # Add drift instead of noise
                else: # Default to normal operation with noise
                    readings[key] = value + self._get_noise(key)
            else:
                # Normal operation
                readings[key] = value + self._get_noise(key)
        return readings

    def _get_noise(self, key):
        """Helper function to get noise based on sensor type."""
        if 'h' in key: # Water level
            return np.random.normal(0, self.config.NOISE_LEVEL_WATER_LEVEL)
        elif 'q' in key: # Flow
            return np.random.normal(0, self.config.NOISE_LEVEL_FLOW)
        return 0

    def induce_fault(self, sensor_id, fault_type, value=0):
        """
        Induces a fault on a specific sensor.
        Example: fault_type='stuck_at_zero', 'drift', 'loss_of_signal'
        """
        self.faults[sensor_id] = {'type': fault_type, 'value': value}
        print(f"INFO: Fault '{fault_type}' induced on sensor '{sensor_id}'.")
