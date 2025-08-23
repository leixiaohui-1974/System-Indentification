# -*- coding: utf-8 -*-
"""
Unit tests for the FaultDetector.
"""
import pytest
from digital_twin_hydraulic_system import config
from digital_twin_hydraulic_system.diagnostics import FaultDetector
from digital_twin_hydraulic_system.models import GateModel

@pytest.fixture
def fault_detector():
    """Pytest fixture to create a FaultDetector instance for each test."""
    gate_model = GateModel(config)
    return FaultDetector(config, gate_model)

def test_diagnose_nominal_conditions(fault_detector):
    """
    Tests that no fault is detected under normal, consistent conditions.
    """
    # 1. Setup: Data where sensor readings are consistent with calculations
    gate_opening = 1.815
    gate_cq_estimate = 0.55
    cleaned_data = {
        'h_gate_up': 3.0,
        'h_gate_down': 2.5,
        'q_gate_down': 38.28 # Consistent with gate formula
    }

    # 2. Action
    reliable_data, status = fault_detector.diagnose(cleaned_data, gate_opening, gate_cq_estimate)

    # 3. Assert
    assert status == "All systems nominal."
    assert reliable_data == cleaned_data # No data should be removed

def test_diagnose_stuck_at_zero_fault(fault_detector):
    """
    Tests the detection of a 'stuck at zero' fault.
    """
    # 1. Setup: Sensor reads near zero, but high flow is expected
    gate_opening = 1.815
    gate_cq_estimate = 0.55
    cleaned_data = {
        'h_gate_up': 3.0,
        'h_gate_down': 2.5,
        'q_gate_down': 0.005 # Sensor is stuck
    }

    # 2. Action
    reliable_data, status = fault_detector.diagnose(cleaned_data, gate_opening, gate_cq_estimate)

    # 3. Assert
    assert "Fault detected in 'q_gate_down'" in status
    assert 'q_gate_down' not in reliable_data # Sensor data should be removed

def test_fault_persistence(fault_detector):
    """
    Tests that once a fault is detected, it is remembered and data is
    consistently isolated in subsequent calls.
    """
    # 1. Setup: First, trigger a fault
    gate_opening = 1.815
    gate_cq_estimate = 0.55
    faulty_data = {
        'h_gate_up': 3.0,
        'h_gate_down': 2.5,
        'q_gate_down': 0.005
    }
    fault_detector.diagnose(faulty_data, gate_opening, gate_cq_estimate)

    # Assert that the fault is now active internally
    assert 'q_gate_down' in fault_detector.active_faults

    # 2. Action: Call diagnose again with new data, which may even be valid
    # The system should ignore it because the sensor is already flagged.
    new_data = {
        'h_gate_up': 3.1,
        'h_gate_down': 2.6,
        'q_gate_down': 40.0 # A new, valid-looking reading
    }
    reliable_data, status = fault_detector.diagnose(new_data, gate_opening, gate_cq_estimate)

    # 3. Assert
    assert "is isolated due to a persistent fault" in status
    assert 'q_gate_down' not in reliable_data # Data should still be removed
