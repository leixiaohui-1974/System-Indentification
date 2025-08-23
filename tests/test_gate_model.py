# -*- coding: utf-8 -*-
"""
Unit tests for the GateModel.
"""
import pytest
from digital_twin_hydraulic_system import config
from digital_twin_hydraulic_system.models import GateModel
import numpy as np

def test_calculate_flow_normal():
    """
    Tests the gate flow calculation under normal, expected conditions.
    """
    # 1. Setup
    gate_model = GateModel(config)

    # Inputs
    h_up = 3.0
    h_down = 2.5
    opening = 1.815
    Cq = 0.55

    # 2. Expected Result Calculation
    # Q = Cq * a * b * sqrt(2 * g * h_up)
    # Using the same formula as in the model to get the precise expected value.
    expected_flow = Cq * (config.GATE_WIDTH * opening) * np.sqrt(2 * 9.81 * h_up)

    # 3. Action
    calculated_flow = gate_model.calculate_flow(h_up, h_down, opening, Cq)

    # 4. Assert
    # Use pytest.approx for safe floating-point comparison.
    assert calculated_flow == pytest.approx(expected_flow)

def test_calculate_flow_zero_head():
    """
    Tests that flow is zero when there is no upstream water head.
    """
    gate_model = GateModel(config)
    calculated_flow = gate_model.calculate_flow(h_up=0, h_down=0, opening=1.0, Cq=0.6)
    assert calculated_flow == 0.0

def test_calculate_flow_submerged():
    """
    Tests that flow is zero when the downstream level is higher than upstream.
    """
    gate_model = GateModel(config)
    calculated_flow = gate_model.calculate_flow(h_up=2.5, h_down=2.6, opening=1.0, Cq=0.6)
    assert calculated_flow == 0.0
