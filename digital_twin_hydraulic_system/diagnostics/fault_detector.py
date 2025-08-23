# -*- coding: utf-8 -*-
"""
Fault Detector.

This module is responsible for detecting anomalies in sensor data,
distinguishing between sensor faults and actual system changes.
"""

import logging

logger = logging.getLogger(__name__)

class FaultDetector:
    def __init__(self, config, gate_model):
        """
        Initializes the fault detector.
        """
        self.config = config
        self.gate_model = gate_model
        self.fault_threshold = 0.15
        self.active_faults = set()
        logger.debug("Fault Detector initialized.")

    def reset(self):
        """Resets the fault detector's state."""
        self.active_faults.clear()
        logger.info("Fault detector has been reset.")

    def diagnose(self, cleaned_data, gate_opening, gate_cq_estimate):
        """
        Performs diagnosis on the latest set of cleaned sensor data.
        It maintains a state of which sensors are considered faulty.
        """
        reliable_data = cleaned_data.copy()
        status_messages = []

        for sensor_id in list(self.active_faults):
            if sensor_id in reliable_data:
                del reliable_data[sensor_id]
            status_messages.append(f"INFO: Sensor '{sensor_id}' is isolated due to a persistent fault.")

        check_key = 'q_gate_down'
        if check_key not in self.active_faults and all(k in reliable_data for k in ['h_gate_up', 'h_gate_down', check_key]):
            h_up = reliable_data['h_gate_up']
            h_down = reliable_data['h_gate_down']
            q_sensor = reliable_data[check_key]

            q_calc = self.gate_model.calculate_flow(h_up, h_down, gate_opening, gate_cq_estimate)

            is_stuck = q_sensor < 0.01 and q_calc > 1.0
            is_deviating = q_sensor > 0.1 and abs(q_calc - q_sensor) / q_sensor > self.fault_threshold

            if is_stuck or is_deviating:
                fault_msg = f"Fault detected in '{check_key}'! (Calc: {q_calc:.2f}, Sensor: {q_sensor:.2f}). Isolating sensor."
                logger.warning(fault_msg)
                status_messages.append(fault_msg)
                self.active_faults.add(check_key)
                if check_key in reliable_data:
                    del reliable_data[check_key]

        if not status_messages:
            final_status = "All systems nominal."
        else:
            final_status = " | ".join(sorted(list(set(status_messages))))

        return reliable_data, final_status
