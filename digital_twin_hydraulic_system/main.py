# -*- coding: utf-8 -*-
"""
Main entry point for the hydraulic digital twin simulation.
"""

from . import config
from .simulation_manager import SimulationManager

def run_sensor_fault_scenario():
    """
    Defines and runs a scenario to test sensor fault detection.
    """
    print("\n--- Running Sensor Fault Scenario ---")
    # 1. Initialize the Simulation Manager
    sim_manager = SimulationManager(config)

    # 2. Schedule the perturbation
    sim_manager.add_perturbation(
        event_time=1500,
        event_type='sensor_fault',
        sensor_id='q_gate_down',
        fault_type='stuck_at_zero'
    )

    # 3. Run the simulation
    sim_manager.run_simulation()

    print("\nSensor fault scenario complete.")

def main():
    """
    Orchestrates the setup and execution of a simulation scenario.
    """
    print("Hydraulic Digital Twin Simulation")
    print("=================================")

    # Run the desired scenario
    run_sensor_fault_scenario()

if __name__ == "__main__":
    main()
