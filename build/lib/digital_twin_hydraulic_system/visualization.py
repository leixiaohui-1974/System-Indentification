# -*- coding: utf-8 -*-
"""
Visualization Module.

Contains functions to plot simulation results, such as comparing Model A
and Model B, showing parameter convergence, etc.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import logging
import numpy as np
from . import config

logger = logging.getLogger(__name__)

class Visualizer:
    def __init__(self):
        self.results_log = []
        self.profile_log = []
        self.plot_profiles = False # Flag for dam-break style plotting
        self.df = None
        logger.debug("Visualizer initialized.")

    def log_state(self, timestamp, state):
        """
        Logs the state of the system at a given timestamp.
        'state' should be a dictionary containing all relevant data.
        """
        if self.plot_profiles:
            # For profile plots, we store the entire array at intervals
            if not self.profile_log or timestamp - self.profile_log[-1]['t'] >= 25:
                self.profile_log.append({'t': timestamp, 'h': state['h_profile']})
        else:
            # For regular time-series plots
            self.results_log.append({'t': timestamp, **state})


    def _prepare_dataframe(self):
        """Converts the log list to a pandas DataFrame for easy plotting."""
        if not self.results_log:
            logger.warning("No time-series data logged to visualize.")
            return False
        if self.df is None or len(self.df) != len(self.results_log):
            self.df = pd.DataFrame(self.results_log).set_index('t')
        return True

    def plot_water_profiles(self):
        """Plots the water surface profile at different timestamps."""
        if not self.profile_log:
            logger.warning("No profile data logged to visualize.")
            return

        logger.info("Plotting water surface profiles for dam-break scenario...")
        plt.figure(figsize=(12, 6))

        for record in self.profile_log:
            t = record['t']
            h = record['h']
            x = np.linspace(0, config.CHANNEL_LENGTH, len(h))
            plt.plot(x, h, label=f't = {t:.1f} s')

        plt.title("Dam-Break Scenario: Water Surface Profile")
        plt.xlabel("Channel Distance (m)")
        plt.ylabel("Water Depth (m)")
        plt.legend()
        plt.grid(True)

        filename = "dam_break_profiles.png"
        plt.savefig(filename)
        logger.info(f"Dam-break profile plot saved to {filename}")
        plt.close()


    def plot_water_levels(self):
        """
        Plots the comparison of water levels from Model A and Model B.
        """
        if not self._prepare_dataframe():
            return

        logger.info("Plotting water levels...")
        plt.figure(figsize=(12, 6))
        plt.plot(self.df.index, self.df['h_true'], label='Model A (True)', color='blue')
        plt.plot(self.df.index, self.df['h_twin'], label='Model B (Twin)', color='red', linestyle='--')
        plt.title("Model A vs. Model B: Downstream Water Level")
        plt.xlabel("Time (s)")
        plt.ylabel("Water Level (m)")
        plt.legend()
        plt.grid(True)

        filename = "water_level_comparison.png"
        plt.savefig(filename)
        logger.info(f"Water level plot saved to {filename}")
        plt.close()

    def plot_parameter_convergence(self, est_param_name, true_param_name=None, title_param_name=None):
        """
        Plots the convergence of a specific identified parameter, with an optional true value line.
        """
        if not self._prepare_dataframe() or est_param_name not in self.df.columns:
            logger.warning(f"Parameter '{est_param_name}' not in logged data. Cannot plot convergence.")
            return

        title = title_param_name if title_param_name else est_param_name
        logger.info(f"Plotting convergence of {title}...")
        plt.figure(figsize=(12, 6))

        plt.plot(self.df.index, self.df[est_param_name], label=f'Estimated {title}')

        if true_param_name and true_param_name in self.df.columns:
            plt.plot(self.df.index, self.df[true_param_name], label=f'True {title}', linestyle='--', color='k')

        plt.title(f"Convergence of Parameter: {title}")
        plt.xlabel("Time (s)")
        plt.ylabel("Parameter Value")
        plt.legend()
        plt.grid(True)

        filename = f"parameter_convergence_{est_param_name}.png"
        plt.savefig(filename)
        logger.info(f"Parameter convergence plot saved to {filename}")
        plt.close()
