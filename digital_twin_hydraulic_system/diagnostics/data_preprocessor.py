# -*- coding: utf-8 -*-
"""
Data Preprocessor.

This module contains algorithms for cleaning raw sensor data before it is
fed into the diagnostic and identification systems.
"""
from collections import deque
import numpy as np

class DataPreprocessor:
    def __init__(self, filter_type='moving_average', window_size=5):
        """
        Initializes the data preprocessor.
        """
        self.filter_type = filter_type
        self.window_size = window_size
        self.buffers = {} # One buffer per sensor signal
        print(f"Data Preprocessor initialized with {filter_type} filter (window={window_size}).")

    def filter(self, raw_data):
        """
        Applies the selected filter to the raw data.

        Args:
            raw_data (dict): A dictionary of raw sensor readings.

        Returns:
            dict: A dictionary of cleaned sensor readings.
        """
        cleaned_data = {}
        for key, value in raw_data.items():
            if key not in self.buffers:
                self.buffers[key] = deque(maxlen=self.window_size)

            self.buffers[key].append(value)

            if self.filter_type == 'moving_average':
                cleaned_data[key] = np.mean(self.buffers[key])
            else:
                # Default to no filter if type is unknown
                cleaned_data[key] = value

        return cleaned_data
