# -*- coding: utf-8 -*-
"""
System Identifier.

This module contains the core online system identification algorithms,
including RLS for simple models and EKF/UKF for complex, non-linear
state and parameter estimation.
"""
import numpy as np

class SystemIdentifier:
    def __init__(self, config):
        """
        Initializes the system identification engine.
        """
        self.config = config
        # --- RLS for Model B (ID Model) ---
        # y(k) = theta' * phi(k-1)
        # We need to identify theta = [a1, b1]'
        self.rls_theta = np.array([0.9, 0.1]) # Initial guess for [a1, b1]
        self.rls_P = np.identity(2) * 1000 # Covariance matrix
        self.rls_lambda = config.RLS_FORGETTING_FACTOR # Forgetting factor

        # --- EKF/UKF for Model A (FVM Model) ---
        # This is more complex and will be set up later.
        # It will estimate states (h, Q) and parameters (n, q_lat)
        self.kf_state_estimate = None
        self.kf_param_estimate = {'manning_n': config.INITIAL_MANNING_GUESS}

        print("System Identifier initialized.")

    def run_rls_step(self, y_k, phi_k):
        """
        Performs one step of the Recursive Least Squares (RLS) algorithm
        with a forgetting factor.

        This method updates the parameter estimate theta for a model of the form:
        y(k) = theta' * phi(k) + e(k)

        Args:
            y_k (float): The current measured output (the value to be predicted).
            phi_k (np.ndarray): The regressor vector, containing inputs and past
                                outputs that predict y_k.
        """
        # Ensure phi_k is a column vector
        phi_k = phi_k.reshape(-1, 1)

        # 1. Calculate Gain Vector (K)
        P_phi = self.rls_P @ phi_k
        denominator = self.rls_lambda + phi_k.T @ P_phi
        if denominator < 1e-9: # Avoid division by zero
            return
        K = P_phi / denominator

        # 2. Calculate Prediction Error (e)
        y_pred = self.rls_theta.T @ phi_k
        error = y_k - y_pred

        # 3. Update Parameter Estimate (theta)
        self.rls_theta = self.rls_theta + (K @ error).flatten()

        # 4. Update Covariance Matrix (P)
        self.rls_P = (self.rls_P - K @ phi_k.T @ self.rls_P) / self.rls_lambda

    def run_kalman_filter_step(self, measurements):
        """
        Performs one step of the chosen Kalman Filter (EKF or UKF).
        """
        # This will involve:
        # 1. Prediction step based on the FVM model.
        # 2. Update step based on sensor measurements.
        # TODO: Implement the EKF/UKF logic
        pass

    def get_identified_params(self):
        """
        Returns the latest set of identified parameters.
        """
        return {
            'model_b_params': {'a1': self.rls_theta[0], 'b1': self.rls_theta[1]},
            'model_a_params': self.kf_param_estimate
        }
