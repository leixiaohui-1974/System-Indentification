# -*- coding: utf-8 -*-
"""
Configuration file for the hydraulic digital twin simulation.
All units are in SI (meters, seconds, etc.).
"""
import numpy as np

# --- Simulation Control ---
TIMESTEP = 1.0  # Simulation timestep in seconds
SIMULATION_DURATION = 3600  # Total simulation time in seconds
NOISE_LEVEL_WATER_LEVEL = 0.005  # Std deviation of Gaussian noise for water level sensors
NOISE_LEVEL_FLOW = 0.01       # Std deviation of Gaussian noise for flow sensors

# --- Channel Geometry ---
CHANNEL_LENGTH = 5000.0  # Length of the channel in meters
CHANNEL_BED_SLOPE = 0.0001  # Bed slope (S0)
CHANNEL_BOTTOM_WIDTH = 20.0  # Bottom width of the trapezoidal channel
CHANNEL_SIDE_SLOPE = 1.5  # Side slope of the trapezoidal channel (z in A=(b+zy)y)

# --- FVM Model (Model A) ---
NUM_CELLS = 50  # Number of finite volume cells
MANNING_ROUGHNESS_TRUE = 0.025  # True Manning's n for the 'real world' model

# --- Gate Model ---
GATE_WIDTH = 5.0  # Width of the sluice gate
# This initial opening is calculated to be consistent with the uniform flow
# in the channel at the initial water depth, to ensure a stable start.
# Q_uniform = 38.28 m^3/s. a = Q / (Cq_guess*b*sqrt(2*g*h_up))
GATE_INITIAL_OPENING = 1.815  # Initial opening of the gate
GATE_DISCHARGE_COEFFICIENT_TRUE = 0.61  # True discharge coefficient

# --- Initial and Boundary Conditions ---
INITIAL_WATER_DEPTH = 2.5  # Initial water depth along the channel
UPSTREAM_INFLOW = 50.0  # Constant inflow at the upstream end of the first channel

# --- System Identification & Digital Twin ---
# Initial guesses for parameters to be identified
INITIAL_MANNING_GUESS = 0.022
INITIAL_GATE_COEFF_GUESS = 0.55

# RLS (Recursive Least Squares) parameters
RLS_FORGETTING_FACTOR = 0.98

# EKF/UKF parameters (placeholders)
PROCESS_NOISE_COV = 1e-5
MEASUREMENT_NOISE_COV = 1e-2

# --- Helper function ---
def get_channel_dx():
    """Computes the spatial step size."""
    return CHANNEL_LENGTH / NUM_CELLS
