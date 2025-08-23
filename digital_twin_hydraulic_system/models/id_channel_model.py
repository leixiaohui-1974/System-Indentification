# -*- coding: utf-8 -*-
"""
Simplified digital twin model (Model B) using a discrete-time
Integral-Delay representation.
"""
import numpy as np
from collections import deque
import logging

logger = logging.getLogger(__name__)

import json

class IDChannelModel:
    def __init__(self, config):
        """
        Initializes the integral-delay channel model.
        It can load piecewise-linear parameters from a JSON file.
        """
        self.config = config
        self.delay_steps = 2 # Default, can be refined
        self.input_buffer = deque(maxlen=self.delay_steps + 5) # A bit larger for safety
        self.h_down_prev = config.INITIAL_WATER_DEPTH
        self._load_piecewise_params()
        logger.debug("Integral-Delay Channel Model (Model B) initialized.")

    def _load_piecewise_params(self):
        """Loads piecewise parameters from a JSON file."""
        try:
            with open("id_model_params.json", 'r') as f:
                self.piecewise_params = json.load(f)
                # Sort segments by threshold to make selection easier
                self.sorted_segments = sorted(
                    self.piecewise_params.items(),
                    key=lambda item: item[1].get('h_threshold', float('inf'))
                )
                logger.info("Successfully loaded piecewise ID model parameters.")
        except FileNotFoundError:
            logger.warning("id_model_params.json not found. Using default single-segment parameters.")
            self.piecewise_params = {
                "default": {
                    "params": {'a1': 0.98, 'b1': 0.02},
                    "h_threshold": float('inf')
                }
            }
            self.sorted_segments = list(self.piecewise_params.items())

    def _get_current_params(self):
        """Selects the appropriate (a1, b1) parameters based on the current water level."""
        current_h = self.h_down_prev
        for name, segment_data in self.sorted_segments:
            if current_h <= segment_data['h_threshold']:
                return segment_data['params']
        # Fallback to the last segment's parameters if something goes wrong
        return self.sorted_segments[-1][1]['params']

    def update_params(self, params):
        """
        Online parameter updates are disabled when using offline piecewise parameters
        to avoid conflicts. The RLS identifier is now effectively unused.
        """
        pass

    def step(self, dt, q_in):
        """
        Advances the model by one time step using piecewise parameters.
        h_down(k) = a1 * h_down(k-1) + b1 * q_in(k-d)
        """
        self.input_buffer.appendleft(q_in)

        if len(self.input_buffer) < self.delay_steps + 1:
            return self.h_down_prev

        delayed_input = self.input_buffer[self.delay_steps]

        # Get parameters for the current operating point
        current_params = self._get_current_params()
        a1 = current_params['a1']
        b1 = current_params['b1']

        h_down_new = a1 * self.h_down_prev + b1 * delayed_input

        self.h_down_prev = h_down_new
        return h_down_new
