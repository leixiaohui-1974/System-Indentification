# -*- coding: utf-8 -*-
"""
Simplified digital twin model (Model B) using a discrete-time
Integral-Delay representation.
"""
import numpy as np
from collections import deque

class IDChannelModel:
    def __init__(self, config):
        """
        Initializes the simplified Integral-Delay model.
        """
        self.config = config

        # Initial parameter guesses from config
        # These will be updated online by the RLS algorithm
        self.K = 1.0  # Proportional/Integral constant (placeholder)
        self.a1 = 0.98 # Autoregressive term, related to T_i
        self.b1 = 0.02 # Input term, related to K
        self.delay_steps = 5 # Time delay in integer steps, related to T_d

        # Input/output buffers for the discrete model
        # We model h_down(k) = a1*h_down(k-1) + b1*q_up(k-d)
        self.input_buffer = deque(np.zeros(50), maxlen=50) # Buffer for q_up
        self.h_down_prev = config.INITIAL_WATER_DEPTH

        print("Integral-Delay Channel Model (Model B) initialized.")

    def step(self, dt, upstream_flow):
        """
        Advances the model state by one time step (dt).

        Args:
            dt (float): The time step (assumed constant).
            upstream_flow (float): The input flow at the upstream end.

        Returns:
            float: The predicted downstream water depth.
        """
        self.input_buffer.appendleft(upstream_flow)

        # Get the delayed input
        delayed_input = 0
        if len(self.input_buffer) > self.delay_steps:
            delayed_input = self.input_buffer[self.delay_steps]

        # Apply the discrete transfer function
        # y(k) = a1*y(k-1) + b1*u(k-d)
        h_down_current = self.a1 * self.h_down_prev + self.b1 * delayed_input

        # Update state for next iteration
        self.h_down_prev = h_down_current

        return h_down_current

    def update_params(self, params):
        """
        Updates the model parameters from the identification module.

        Args:
            params (dict): A dictionary with new parameters, e.g.,
                           {'a1': 0.985, 'b1': 0.019, 'delay': 6}.
        """
        self.a1 = params.get('a1', self.a1)
        self.b1 = params.get('b1', self.b1)
        self.delay_steps = params.get('delay', self.delay_steps)
        print(f"INFO: Model B parameters updated: a1={self.a1:.3f}, b1={self.b1:.3f}, delay={self.delay_steps}")
