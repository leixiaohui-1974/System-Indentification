# -*- coding: utf-8 -*-
"""
Visualization Module.

Contains functions to plot simulation results, such as comparing Model A
and Model B, showing parameter convergence, etc.
"""
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import pandas as pd

class Visualizer:
    def __init__(self):
        self.results_log = []
        self.df = None
        print("Visualizer initialized.")

    def log_state(self, timestamp, state):
        """
        Logs the state of the system at a given timestamp.
        'state' should be a dictionary containing all relevant data.
        """
        self.results_log.append({'t': timestamp, **state})

    def _prepare_dataframe(self):
        """Converts the log list to a pandas DataFrame for easy plotting."""
        if not self.results_log:
            print("Warning: No data logged to visualize.")
            return False
        if self.df is None or len(self.df) != len(self.results_log):
            self.df = pd.DataFrame(self.results_log).set_index('t')
        return True

    def plot_water_levels(self):
        """
        Plots the comparison of water levels from Model A and Model B.
        """
        if not self._prepare_dataframe():
            return

        print("Plotting water levels...")
        plt.figure(figsize=(12, 6))
        plt.plot(self.df.index, self.df['h_true'], label='Model A (True)', color='blue')
        plt.plot(self.df.index, self.df['h_twin'], label='Model B (Twin)', color='red', linestyle='--')
        plt.title("Model A vs. Model B: Downstream Water Level")
        plt.xlabel("Time (s)")
        plt.ylabel("Water Level (m)")
        plt.legend()
        plt.grid(True)
        plt.savefig("water_level_comparison.png")
        print("INFO: Water level plot saved to water_level_comparison.png")
        plt.close()

    def plot_parameter_convergence(self, param_name):
        """
        Plots the convergence of a specific identified parameter.
        """
        if not self._prepare_dataframe() or param_name not in self.df.columns:
            print(f"Warning: Parameter '{param_name}' not in logged data.")
            return

        print(f"Plotting convergence of {param_name}...")
        plt.figure(figsize=(12, 6))
        plt.plot(self.df.index, self.df[param_name], label=f'Identified {param_name}')
        plt.title(f"Convergence of Parameter: {param_name}")
        plt.xlabel("Time (s)")
        plt.ylabel("Parameter Value")
        plt.legend()
        plt.grid(True)
        plt.savefig(f"parameter_convergence_{param_name}.png")
        print(f"INFO: Parameter convergence plot saved to parameter_convergence_{param_name}.png")
        plt.close()
