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

def run_roughness_change_scenario():
    """
    Defines and runs a scenario to test system adaptation to a physical
    parameter change in the 'real world' model.
    """
    print("\n--- Running Roughness Change Scenario ---")
    sim_manager = SimulationManager(config)

    # Schedule a change in Manning's roughness coefficient in Model A
    sim_manager.add_perturbation(
        event_time=1800,
        event_type='roughness_change',
        new_roughness=0.040 # Simulate vegetation growth
    )

    sim_manager.run_simulation()
    print("\nRoughness change scenario complete.")

def run_combined_scenario():
    """
    Defines and runs a complex scenario with multiple, sequential perturbations.
    """
    print("\n--- Running Combined (Roughness + Fault) Scenario ---")
    sim_manager = SimulationManager(config)

    # 1. Schedule a change in Manning's roughness
    sim_manager.add_perturbation(
        event_time=1000,
        event_type='roughness_change',
        new_roughness=0.035
    )

    # 2. Schedule a subsequent sensor fault
    sim_manager.add_perturbation(
        event_time=2500,
        event_type='sensor_fault',
        sensor_id='q_gate_down',
        fault_type='stuck_at_zero'
    )

    sim_manager.run_simulation()
    print("\nCombined scenario complete.")


def main():
    """
    Orchestrates the setup and execution of a simulation scenario.
    """
    print("Hydraulic Digital Twin Simulation")
    print("=================================")

    # Run the desired scenario
    # run_sensor_fault_scenario()
    # run_roughness_change_scenario()
    run_combined_scenario()

if __name__ == "__main__":
    main()
