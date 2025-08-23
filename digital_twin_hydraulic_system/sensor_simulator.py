# -*- coding: utf-8 -*-
"""
Sensor Simulator.

This module is responsible for mimicking real-world sensors. It takes
true data from the high-fidelity model (Model A) and generates noisy
sensor readings. It can also simulate sensor faults.
"""
import numpy as np
import logging

logger = logging.getLogger(__name__)

class SensorSimulator:
    def __init__(self, config):
        self.config = config
        self.faults = {} # Stores active faults: {'sensor_id': {'type': 'stuck', 'value': 5.0}}
        self.drift_accumulators = {} # Stores accumulated drift: {'sensor_id': 0.1}
        logger.debug("Sensor Simulator initialized.")

    def get_readings(self, true_values, dt):
        """
        Generates sensor readings from true physical values for a given timestep.

        Args:
            true_values (dict): A dictionary of true values.
            dt (float): The current simulation timestep, used for drift calculation.

        Returns:
            dict: A dictionary of noisy sensor readings.
        """
        readings = {}
        for key, value in true_values.items():
            noise = self._get_noise(key) # Get base noise level

            # Check if a fault is active for this sensor
            if key in self.faults:
                fault = self.faults[key]
                fault_type = fault.get('type')

                if fault_type == 'stuck':
                    readings[key] = fault['value']
                    continue # Skip other processing

                elif fault_type == 'increased_noise':
                    # Apply noise with a higher magnitude
                    noise = self._get_noise(key, override_level=fault['value'])

                elif fault_type == 'drift':
                    # Accumulate drift over time
                    drift_rate = fault['value']
                    self.drift_accumulators[key] += drift_rate * dt

            # Apply final accumulated drift and noise
            accumulated_drift = self.drift_accumulators.get(key, 0.0)
            readings[key] = value + accumulated_drift + noise

        return readings

    def _get_noise(self, key, override_level=None):
        """
        Helper function to get noise for a sensor.
        Can be overridden with a specific noise level for fault simulation.
        """
        base_level = 0
        if 'h' in key: # Water level
            base_level = self.config.NOISE_LEVEL_WATER_LEVEL
        elif 'q' in key: # Flow
            base_level = self.config.NOISE_LEVEL_FLOW

        noise_level = override_level if override_level is not None else base_level
        return np.random.normal(0, noise_level)

    def induce_fault(self, sensor_id, fault_type, **kwargs):
        """
        Induces a fault on a specific sensor.

        Args:
            sensor_id (str): The ID of the sensor to affect (e.g., 'h_gate_up').
            fault_type (str): Type of fault ('stuck', 'drift', 'increased_noise').
            **kwargs:
                value (float): For 'stuck', the value to be stuck at.
                               For 'drift', the drift rate per second.
                               For 'increased_noise', the new noise standard deviation.
        """
        if fault_type not in ['stuck', 'drift', 'increased_noise']:
            logger.error(f"Unknown fault type '{fault_type}' requested.")
            return

        # Pop 'value' from kwargs, as it's the primary parameter
        value = kwargs.get('value', 0)
        fault_config = {'type': fault_type, 'value': value}
        self.faults[sensor_id] = fault_config

        if fault_type == 'drift':
            self.drift_accumulators[sensor_id] = self.drift_accumulators.get(sensor_id, 0.0)

        logger.info(f"Fault '{fault_type}' induced on sensor '{sensor_id}' with value {value}.")
