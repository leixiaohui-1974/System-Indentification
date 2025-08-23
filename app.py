# -*- coding: utf-8 -*-
"""
Main entry point for the Streamlit-based interactive web application.
"""
import streamlit as st
import numpy as np
import pandas as pd
import time
from digital_twin_hydraulic_system import config
from digital_twin_hydraulic_system.simulation_manager import SimulationManager

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="Hydraulic Digital Twin")

# --- Helper Functions ---
def initialize_simulation(scenario_name):
    """Initializes or resets the simulation in Streamlit's session state."""
    st.session_state.is_running = False

    # Apply scenario-specific configurations
    if scenario_name == "Parameter Estimation (EKF)":
        config.SIMULATION_DURATION = 1800
        sim_manager = SimulationManager(config)
        # Create a discrepancy for the EKF to solve
        true_roughness = 0.035
        twin_initial_guess = 0.025
        sim_manager.model_a.manning_n = true_roughness
        sim_manager.model_twin_fvm.manning_n = twin_initial_guess
        st.toast(f"EKF scenario started! Real N={true_roughness}, Twin Guess N={twin_initial_guess}")
    else:
        # Default scenario settings
        config.SIMULATION_DURATION = 3600
        sim_manager = SimulationManager(config)
        st.toast("Normal operation scenario started!")

    st.session_state.sim_manager = sim_manager
    st.session_state.log_messages = []

def get_logger_messages():
    """Retrieves log messages to display in the UI."""
    # In a real app, this would read from a log file or a dedicated handler.
    # For simplicity, we'll just show a few recent status messages.
    return st.session_state.log_messages[-5:] if st.session_state.log_messages else ["No log messages yet."]

# --- Main App ---
def main():
    st.title("🚰 Digital Twin for a Canal-Gate System")

    # --- Sidebar for controls ---
    with st.sidebar:
        st.header("⚙️ Controls")

        scenario = st.selectbox(
            "1. Select Scenario",
            ("Normal Operation", "Parameter Estimation (EKF)"),
            key="scenario_select"
        )

        if st.button("🚀 Start / Restart Simulation"):
            initialize_simulation(scenario)
            st.session_state.is_running = True
            st.rerun()

        if st.button("⏸️ Pause Simulation"):
            st.session_state.is_running = False
            st.rerun()

        st.subheader("🛠️ Manual Adjustments")
        # These sliders will only take effect if the simulation is restarted
        gate_opening = st.slider("Gate Opening (m)", 0.1, 5.0, 1.8, 0.1, key="gate_slider")
        inflow = st.slider("Upstream Inflow (m³/s)", 20.0, 100.0, 50.0, 1.0, key="inflow_slider")

        if 'sim_manager' in st.session_state:
            st.session_state.sim_manager.gate_opening = gate_opening
            st.session_state.sim_manager.config.UPSTREAM_INFLOW = inflow

        st.subheader("💥 Fault Injection")
        fault_sensor = st.selectbox("Sensor to Target", ('h_gate_up', 'q_gate_down'))
        fault_type = st.selectbox("Fault Type", ('stuck', 'increased_noise'))

        if st.button("Inject Fault Now"):
            if 'sim_manager' in st.session_state:
                fault_params = {'sensor_id': fault_sensor, 'fault_type': fault_type}
                if fault_type == 'stuck':
                    fault_params['value'] = st.session_state.sim_manager.model_a.get_state()['h'][-1] * 0.5 # Stuck at 50% of current value
                elif fault_type == 'increased_noise':
                    fault_params['value'] = config.NOISE_LEVEL_WATER_LEVEL * 10

                st.session_state.sim_manager.add_perturbation(
                    st.session_state.sim_manager.timestamp, **fault_params
                )
                st.toast(f"Injecting {fault_type} fault into {fault_sensor}!", icon="🔥")
            else:
                st.warning("Start the simulation before injecting a fault.")

    # --- Main area for plots and logs ---
    if 'sim_manager' not in st.session_state:
        st.info("Select a scenario and click 'Start / Restart Simulation' to begin.")
        return

    sim = st.session_state.sim_manager

    # Prepare plotting areas
    st.header("📊 Simulation Results")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("State Comparison (True vs. Twin)")
        plot1_area = st.empty()
    with col2:
        st.subheader("Parameter Convergence")
        plot2_area = st.empty()
    st.header("📜 Simulation Log")
    log_area = st.text_area("Log Output", "", height=200)

    # Main simulation loop controlled by session state
    if st.session_state.get('is_running', False):
        if sim.step_simulation(num_steps=10): # Run 10 steps per refresh for speed
            # Prepare data for plotting
            sim.visualizer._prepare_dataframe()
            df = sim.visualizer.df

            # Update plots
            fig1, ax1 = plt.subplots()
            ax1.plot(df.index, df['h_true'], label='Model A (True)')
            ax1.plot(df.index, df['h_twin'], label='EKF Estimate (Twin)', linestyle='--')
            ax1.set_title("Downstream Water Level")
            ax1.set_xlabel("Time (s)"); ax1.set_ylabel("Water Level (m)"); ax1.grid(True); ax1.legend()
            plot1_area.pyplot(fig1)

            fig2, ax2 = plt.subplots()
            if 'n_est' in df.columns:
                ax2.plot(df.index, df['n_est'], label="Estimated n")
                ax2.plot(df.index, df['n_true'], label="True n", linestyle='--', color='k')
            ax2.set_title("Manning's n Estimate")
            ax2.set_xlabel("Time (s)"); ax2.set_ylabel("Parameter Value"); ax2.grid(True); ax2.legend()
            plot2_area.pyplot(fig2)

            # Update logs (simplified)
            current_n = sim.ekf.x[-1]
            log_area.text(f"T={sim.timestamp:.1f}s | h_true={sim.h_true_gate_upstream:.3f} | h_twin_est={sim.model_twin_fvm._get_depth_from_area_scalar(sim.ekf.x[sim.config.NUM_CELLS-1]):.3f} | n_est={current_n:.4f}")

            time.sleep(0.1) # Small delay to make animation visible
            st.rerun()
        else:
            st.session_state.is_running = False
            st.success("Simulation finished!")
            st.rerun()

if __name__ == "__main__":
    main()
