# -*- coding: utf-8 -*-
"""
Unit tests for the SystemIdentifier, particularly the RLS algorithm.
"""
import pytest
import numpy as np
from digital_twin_hydraulic_system import config
from digital_twin_hydraulic_system.diagnostics import SystemIdentifier

def test_rls_convergence():
    """
    Tests if the RLS algorithm can correctly identify the parameters of a
    known, simple linear system.
    """
    # 1. Setup: Define a simple, known linear system
    # y(k) = true_a * y(k-1) + true_b * u(k-1) + noise
    true_params = np.array([0.75, 0.25])
    y_prev = 1.0

    # Instantiate the identifier. It starts with a poor guess.
    identifier = SystemIdentifier(config)
    identifier.rls_theta = np.array([0.1, 0.9]) # Poor initial guess

    # 2. Action: Feed synthetic data to the RLS algorithm for many steps
    num_steps = 500
    for k in range(num_steps):
        # Generate a new input and the "true" output with some noise
        u_prev = np.sin(k / 10.0) # A varying input signal
        noise = np.random.normal(0, 0.01)

        phi_k = np.array([y_prev, u_prev])
        y_k = (true_params @ phi_k) + noise

        # Run one step of the RLS algorithm
        identifier.run_rls_step(y_k, phi_k)

        # Update the system for the next iteration
        y_prev = y_k

    # 3. Assert: Check if the identified parameters have converged to the true ones
    identified_params = identifier.get_identified_params()['model_b_params']
    final_theta = np.array([identified_params['a1'], identified_params['b1']])

    # We expect the parameters to be very close to the true values after enough iterations.
    # We use a relatively high tolerance because RLS convergence depends on the
    # input signal and noise.
    assert final_theta == pytest.approx(true_params, abs=1e-2)
