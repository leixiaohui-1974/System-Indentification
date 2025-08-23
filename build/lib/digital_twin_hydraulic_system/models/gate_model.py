# -*- coding: utf-8 -*-
"""
Implements the hydraulic model for a sluice gate.
"""
import numpy as np

class GateModel:
    def __init__(self, config):
        """
        Initializes the gate model with parameters from the config.
        """
        self.width = config.GATE_WIDTH
        self.g = 9.81  # Gravity

    def calculate_flow(self, h_up, h_down, opening, Cq):
        """
        Calculates the flow through the gate using the standard orifice equation,
        considering both free and submerged flow conditions.

        Args:
            h_up (float): Upstream water depth.
            h_down (float): Downstream water depth.
            opening (float): Gate opening height.
            Cq (float): Discharge coefficient (this will be identified online).

        Returns:
            float: The calculated flow rate (Q) in m^3/s.
        """
        # This is a simplified model. A more accurate one would distinguish
        # between free-flow and submerged-flow more rigorously.
        # For now, we use a common formulation for orifice flow.
        if h_up <= 0:
            return 0.0

        # Effective area of the orifice
        area = self.width * opening

        # Driving head - simplified for this example
        driving_head = h_up

        # Orifice equation
        flow = Cq * area * np.sqrt(2 * self.g * driving_head)

        # Ensure flow is not negative and handle submerged conditions simplistically
        # A proper model would check if h_down > critical_depth_downstream
        if h_down >= h_up:
             return 0.0

        return flow
