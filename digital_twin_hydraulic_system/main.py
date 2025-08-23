# -*- coding: utf-8 -*-
"""
Main entry point for the hydraulic digital twin simulation.
"""

import logging
import numpy as np
from . import config
from .simulation_manager import SimulationManager
from .logging_config import setup_logging

logger = logging.getLogger(__name__)

def run_sensor_fault_scenario():
    """
    Defines and runs a scenario to test sensor fault detection.
    """
    logger.info("--- Running Sensor Fault Scenario ---")
    sim_manager = SimulationManager(config)

    sim_manager.add_perturbation(
        event_time=1500,
        event_type='sensor_fault',
        sensor_id='q_gate_down',
        fault_type='stuck',
        value=0.0
    )

    sim_manager.run_full_simulation()
    logger.info("--- Sensor fault scenario complete. ---")

def run_roughness_change_scenario():
    """
    Defines and runs a scenario to test system adaptation to a physical
    parameter change in the 'real world' model.
    """
    logger.info("--- Running Roughness Change Scenario ---")
    sim_manager = SimulationManager(config)

    sim_manager.add_perturbation(
        event_time=1800,
        event_type='roughness_change',
        new_roughness=0.040
    )

    sim_manager.run_full_simulation()
    logger.info("--- Roughness change scenario complete. ---")

def run_combined_scenario():
    """
    Defines and runs a complex scenario with multiple, sequential perturbations.
    """
    logger.info("--- Running Combined (Roughness + Fault) Scenario ---")
    sim_manager = SimulationManager(config)

    sim_manager.add_perturbation(
        event_time=1000,
        event_type='roughness_change',
        new_roughness=0.035
    )

    sim_manager.add_perturbation(
        event_time=2500,
        event_type='sensor_fault',
        sensor_id='q_gate_down',
        fault_type='stuck',
        value=0.0
    )

    sim_manager.run_full_simulation()
    logger.info("--- Combined scenario complete. ---")


def run_noise_fault_scenario():
    """
    Defines and runs a scenario to test the 'increased_noise' fault detection.
    """
    logger.info("--- Running Increased Noise Fault Scenario ---")
    # Reset duration to normal if it was changed by another scenario
    config.SIMULATION_DURATION = 3600
    sim_manager = SimulationManager(config)

    # Schedule a fault where the noise level of a sensor increases dramatically
    sim_manager.add_perturbation(
        event_time=1000,
        event_type='sensor_fault',
        sensor_id='h_gate_down',
        fault_type='increased_noise',
        value=config.NOISE_LEVEL_WATER_LEVEL * 5 # 5x the normal noise
    )

    sim_manager.run_full_simulation()
    logger.info("--- Increased noise fault scenario complete. ---")

def main():
    """
    Orchestrates the setup and execution of a simulation scenario.
    """
    setup_logging()
    logger.info("=================================")
    logger.info("Hydraulic Digital Twin Simulation")
    logger.info("=================================")

    # Run the desired scenario
    # run_sensor_fault_scenario()
    # run_roughness_change_scenario()
    # run_combined_scenario()
    # run_dam_break_scenario()
    # run_noise_fault_scenario()
    # run_parameter_estimation_scenario()
    # run_drift_fault_scenario()

def run_drift_fault_scenario():
    """
    Defines and runs a scenario to test the 'drift' fault detection.
    """
    logger.info("--- Running Drift Fault Scenario ---")
    config.SIMULATION_DURATION = 3000
    sim_manager = SimulationManager(config)

    # Schedule a fault where a sensor starts to drift slowly
    sim_manager.add_perturbation(
        event_time=500,
        event_type='sensor_fault',
        sensor_id='h_gate_up',
        fault_type='drift',
        value=0.002 # Drifting at 2mm per second
    )

    sim_manager.run_full_simulation()
    logger.info("--- Drift fault scenario complete. ---")

def run_parameter_estimation_scenario():
    """
    Defines and runs a scenario to validate the EKF's ability to estimate
    a physical parameter (Manning's n) online.
    """
    logger.info("--- Running Parameter Estimation (EKF) Scenario ---")
    config.SIMULATION_DURATION = 1800 # Shorter run for this test
    sim_manager = SimulationManager(config)

    # 1. Create a discrepancy between the real world and the twin's model
    true_roughness = 0.035
    twin_initial_guess = 0.025
    sim_manager.model_a.manning_n = true_roughness
    sim_manager.model_twin_fvm.manning_n = twin_initial_guess
    logger.warning(f"Discrepancy introduced: Real N={true_roughness}, Twin N={twin_initial_guess}")

    # 2. Run the simulation
    sim_manager.run_full_simulation()
    logger.info("--- EKF validation scenario complete. ---")


def run_dam_break_scenario():
    """
    Defines and runs a dam-break scenario to validate the FVM solver.
    """
    logger.info("--- Running Dam-Break Validation Scenario ---")

    # Use a shorter duration for this specific test
    config.SIMULATION_DURATION = 200
    sim_manager = SimulationManager(config)

    # Create the initial condition: a step in water level
    nx = config.NUM_CELLS
    h_init = np.full(nx, 1.5)
    h_init[:nx // 2] = 3.0
    q_init = np.full(nx, 0.0)

    # Set the custom initial condition in the FVM model
    sim_manager.model_a.set_initial_conditions(h_init, q_init)

    # We need a new kind of visualization for this
    sim_manager.visualizer.plot_profiles = True

    sim_manager.run_full_simulation()
    logger.info("--- Dam-break scenario complete. ---")


if __name__ == "__main__":
    main()
