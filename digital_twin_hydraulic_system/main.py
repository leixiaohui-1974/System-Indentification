# -*- coding: utf-8 -*-
"""
Main entry point for the hydraulic digital twin simulation.
"""

import logging
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
        fault_type='stuck_at_zero'
    )

    sim_manager.run_simulation()
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

    sim_manager.run_simulation()
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
        fault_type='stuck_at_zero'
    )

    sim_manager.run_simulation()
    logger.info("--- Combined scenario complete. ---")


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
    run_combined_scenario()

if __name__ == "__main__":
    main()
