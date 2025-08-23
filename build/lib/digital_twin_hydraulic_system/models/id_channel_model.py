# -*- coding: utf-8 -*-
"""
Simplified digital twin model (Model B) using a discrete-time
Integral-Delay representation.
"""
import numpy as np
from collections import deque
import logging

logger = logging.getLogger(__name__)

class IDChannelModel:
    def __init__(self, config):
        """
        Initializes the simplified Integral-Delay model.
        """
        self.config = config

        self.K = 1.0
        self.a1 = 0.98
        self.b1 = 0.02
        self.delay_steps = 5

        self.input_buffer = deque(np.zeros(50), maxlen=50)
        self.h_down_prev = config.INITIAL_WATER_DEPTH

        logger.debug("Integral-Delay Channel Model (Model B) initialized.")

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
        logger.debug(f"Model B parameters updated: a1={self.a1:.3f}, b1={self.b1:.3f}, delay={self.delay_steps}")
