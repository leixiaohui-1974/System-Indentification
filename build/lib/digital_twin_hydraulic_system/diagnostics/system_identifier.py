# -*- coding: utf-8 -*-
"""
System Identifier.

This module contains the core online system identification algorithms,
including RLS for simple models and EKF/UKF for complex, non-linear
state and parameter estimation.
"""
import numpy as np
import logging

logger = logging.getLogger(__name__)

class SystemIdentifier:
    def __init__(self, config):
        """
        Initializes the system identification engine.
        """
        self.config = config
        self.rls_theta = np.array([0.9, 0.1])
        self.rls_P = np.identity(2) * 1000
        self.rls_lambda = config.RLS_FORGETTING_FACTOR

        self.kf_state_estimate = None
        self.kf_param_estimate = {'manning_n': config.INITIAL_MANNING_GUESS}

        logger.debug("System Identifier initialized.")

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

from copy import deepcopy

class ExtendedKalmanFilter:
    def __init__(self, fvm_model, x_initial, P_initial, Q, R):
        """
        Initializes the Extended Kalman Filter for state and parameter estimation.
        The state vector x is augmented with parameters to be estimated.
        x = [A_1, ..., A_nx, Q_1, ..., Q_nx, n_manning]

        Args:
            fvm_model: An instance of the FVMChannelModel.
            x_initial (np.ndarray): Initial augmented state estimate vector.
            P_initial (np.ndarray): Initial augmented state covariance matrix.
            Q (np.ndarray): Process noise covariance matrix.
            R (np.ndarray): Measurement noise covariance matrix.
        """
        self.fvm_model = fvm_model
        self.x = x_initial
        self.P = P_initial
        self.Q = Q
        self.R = R
        self.n_states = 2 * self.fvm_model.nx # Number of hydraulic states (A, Q)
        self.n_params = 1 # Number of parameters (just n_manning for now)
        self.n_aug = self.n_states + self.n_params # Total size of augmented state

        if len(x_initial) != self.n_aug or P_initial.shape[0] != self.n_aug:
            raise ValueError("Initial state or covariance matrix has incorrect dimensions.")

        logger.info(f"EKF initialized with augmented state size n={self.n_aug}")

    def _calculate_F_jacobian_numerical(self, dt, upstream_bc, downstream_bc):
        """Numerically approximates the Jacobian of the augmented FVM step function."""
        F_jac = np.zeros((self.n_aug, self.n_aug))
        epsilon = 1e-6

        # Base step
        model_copy = deepcopy(self.fvm_model)
        self._set_model_state(model_copy, self.x)
        model_copy.step(dt, upstream_bc, downstream_bc)
        x_base_next = self._get_model_state(model_copy)

        for j in range(self.n_aug):
            # Perturb the j-th state variable
            x_perturbed = self.x.copy()
            x_perturbed[j] += epsilon

            model_copy_perturbed = deepcopy(self.fvm_model)
            self._set_model_state(model_copy_perturbed, x_perturbed)
            model_copy_perturbed.step(dt, upstream_bc, downstream_bc)
            x_perturbed_next = self._get_model_state(model_copy_perturbed)

            F_jac[:, j] = (x_perturbed_next - x_base_next) / epsilon

        return F_jac

    def predict(self, dt, upstream_bc, downstream_bc):
        """EKF predict step for the augmented state."""
        # The parameter part of the state is assumed to be a random walk
        # n_{k+1} = n_k + w_k, so the prediction is just the old value.
        # The FVM step handles the hydraulic states.

        # 1. Calculate Jacobian of F wrt x
        F_jac = self._calculate_F_jacobian_numerical(dt, upstream_bc, downstream_bc)

        # 2. Predict state covariance
        self.P = F_jac @ self.P @ F_jac.T + self.Q

        # 3. Predict state estimate
        self._set_model_state(self.fvm_model, self.x)
        self.fvm_model.step(dt, upstream_bc, downstream_bc)
        self.x = self._get_model_state(self.fvm_model)

    def update(self, z, H_jac, h_func):
        """EKF update step (no changes needed for augmented state here)."""
        S = H_jac @ self.P @ H_jac.T + self.R
        K = self.P @ H_jac.T @ np.linalg.inv(S)
        y = z - h_func(self.x)
        self.x = self.x + K @ y
        I = np.identity(self.n_aug)
        self.P = (I - K @ H_jac) @ self.P

    def _set_model_state(self, model, x_aug):
        """Sets the FVM model's state from the augmented state vector."""
        nx = model.nx
        model.U[0, 1:-1] = x_aug[:nx]
        model.U[1, 1:-1] = x_aug[nx:self.n_states]
        model.manning_n = x_aug[self.n_states]

    def _get_model_state(self, model):
        """Gets the augmented state vector from the FVM model."""
        nx = model.nx
        A = model.U[0, 1:-1]
        Q = model.U[1, 1:-1]
        n_param = model.manning_n
        return np.concatenate([A, Q, [n_param]])
