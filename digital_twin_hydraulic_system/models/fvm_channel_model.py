# -*- coding: utf-8 -*-
"""
High-fidelity channel model (Model A) using the Finite Volume Method
to solve the 1D Saint-Venant equations.
"""
import numpy as np
import logging

logger = logging.getLogger(__name__)

class FVMChannelModel:
    def __init__(self, config):
        """
        Initializes the high-fidelity Finite Volume Method model.
        """
        self.config = config
        self.g = 9.81
        self.nx = config.NUM_CELLS
        self.dx = config.get_channel_dx()
        self.S0 = config.CHANNEL_BED_SLOPE
        self.manning_n = config.MANNING_ROUGHNESS_TRUE
        self.bottom_width = config.CHANNEL_BOTTOM_WIDTH
        self.side_slope = config.CHANNEL_SIDE_SLOPE

        # We add two ghost cells for boundary conditions
        self.nx_with_ghost = self.nx + 2

        # State vectors [A, Q] - Area and Discharge
        self.U = np.zeros((2, self.nx_with_ghost))
        self.h = np.full(self.nx_with_ghost, config.INITIAL_WATER_DEPTH)
        self.A = self._area(self.h)

        initial_h = config.INITIAL_WATER_DEPTH
        initial_A = (self.bottom_width + self.side_slope * initial_h) * initial_h
        initial_P = self.bottom_width + 2 * initial_h * np.sqrt(1 + self.side_slope**2)
        initial_R = initial_A / initial_P if initial_P > 0 else 0

        # Calculate initial discharge for uniform flow, handle frictionless case
        if self.manning_n > 1e-9:
            q_initial = (1/self.manning_n) * initial_A * (initial_R**(2/3)) * (self.S0**0.5)
        else:
            q_initial = 0.0

        self.Q = np.full(self.nx_with_ghost, q_initial)
        self.U[0, :] = self.A
        self.U[1, :] = self.Q

        logger.debug("FVM Channel Model (Model A) initialized with ghost cells.")

    def set_initial_conditions(self, h_init, q_init):
        """Allows for setting custom initial conditions, e.g., for a dam break."""
        if len(h_init) == self.nx and len(q_init) == self.nx:
            self.h[1:-1] = h_init
            self.Q[1:-1] = q_init
            self.A = self._area(self.h)
            self.U[0, :] = self.A
            self.U[1, :] = self.Q
            logger.info("Custom initial conditions have been set for FVM model.")
        else:
            logger.error("Failed to set initial conditions; array length mismatch.")

    def _area(self, h):
        return (self.bottom_width + self.side_slope * h) * h

    def _wetted_perimeter(self, h):
        return self.bottom_width + 2 * h * np.sqrt(1 + self.side_slope**2)

    def _update_depth_from_area(self):
        """
        Calculates water depth h from cross-sectional area A for a trapezoid.
        Uses a Newton-Raphson iterative solver.
        A = (b + zh)h  => zh^2 + bh - A = 0
        """
        A = self.U[0, :]
        h = np.maximum(self.h, 1e-6)

        for _ in range(5):
            f = self.side_slope * h**2 + self.bottom_width * h - A
            fp = 2 * self.side_slope * h + self.bottom_width
            h_update = np.divide(f, fp, out=np.zeros_like(f), where=np.abs(fp) > 1e-6)
            h = h - h_update

        self.h = np.maximum(h, 0)
        self.A = self._area(self.h)

    def _calculate_hydro_vars(self):
        """Calculates and returns key hydraulic variables from the state vector U."""
        A = self.U[0, :]
        Q = self.U[1, :]
        h = self.h

        u = np.divide(Q, A, out=np.zeros_like(Q), where=A > 1e-6)
        top_width = self.bottom_width + 2 * self.side_slope * h
        D = np.divide(A, top_width, out=np.zeros_like(A), where=top_width > 1e-6)
        c = np.sqrt(self.g * D)

        return A, Q, u, c

    def _calculate_fluxes(self):
        """Calculates the physical flux vector F(U) for all cells."""
        A, Q, u, _ = self._calculate_hydro_vars()

        I1 = ( (self.bottom_width * self.h**2) / 2 + (self.side_slope * self.h**3) / 3 )

        F = np.zeros_like(self.U)
        F[0, :] = Q
        F[1, :] = (u * Q) + self.g * I1
        return F

    def _calculate_cfl_dt(self):
        """
        Calculates the maximum stable time step based on the CFL condition.
        dt = C_cfl * dx / max(|u| + c)
        """
        _, _, u, c = self._calculate_hydro_vars()
        max_wave_speed = np.max(np.abs(u) + c)

        if max_wave_speed < 1e-6:
            return self.config.TIMESTEP # Return a default if speed is zero

        # Use a Courant number of 0.5 for stability
        cfl_dt = 0.5 * self.dx / max_wave_speed

        # Do not exceed the user-defined maximum timestep
        return min(cfl_dt, self.config.TIMESTEP)

    def _apply_boundary_conditions(self, upstream_bc, downstream_bc):
        """Applies boundary conditions to ghost cells."""
        # Upstream
        if upstream_bc and upstream_bc.get('type') == 'wall':
            # Reflective wall at upstream end
            self.U[0, 0] = self.U[0, 1]  # Same depth
            self.U[1, 0] = -self.U[1, 1] # Reflect velocity
            self.h[0] = self.h[1]
        elif upstream_bc and upstream_bc.get('type') == 'inflow':
            # Inflow discharge is specified
            self.U[1, 0] = upstream_bc['value']
            # Extrapolate water depth from the first computational cell
            self.U[0, 0] = self.U[0, 1]
            self.h[0] = self.h[1]
        else: # Default: zero-gradient outflow
            self.U[:, 0] = self.U[:, 1]
            self.h[0] = self.h[1]

        # Downstream
        if downstream_bc and downstream_bc.get('type') == 'wall':
            # Reflective wall at downstream end
            self.U[0, -1] = self.U[0, -2]  # Same depth
            self.U[1, -1] = -self.U[1, -2] # Reflect velocity
            self.h[-1] = self.h[-2]
        elif downstream_bc and downstream_bc.get('type') == 'fixed_depth':
            # Water depth is specified
            self.h[-1] = downstream_bc['value']
            self.A[-1] = self._area(self.h[-1])
            self.U[0, -1] = self.A[-1]
            # Extrapolate discharge from last computational cell
            self.U[1, -1] = self.U[1, -2]
        else: # Default: zero-gradient outflow
            self.U[:, -1] = self.U[:, -2]
            self.h[-1] = self.h[-2]

    def _calculate_source_terms(self):
        """Calculates source terms (bed slope, friction)."""
        A = self.U[0, :]
        Q = self.U[1, :]
        h = self.h
        P = self._wetted_perimeter(h)
        R = np.divide(A, P, out=np.zeros_like(A), where=P > 1e-6)

        # Use np.divide to handle potential division by zero when A is small
        Sf = np.divide(self.manning_n**2 * Q * np.abs(Q),
                       (A**2 * R**(4/3)),
                       out=np.zeros_like(Q),
                       where=A > 1e-6)

        S = np.zeros_like(self.U)
        S[1, :] = self.g * A * (self.S0 - Sf)
        return S

    def _apply_hll_solver(self):
        """Applies the HLL solver to get inter-cell fluxes."""
        # Get primitive variables for all cells (including ghost cells)
        A, Q, u, c = self._calculate_hydro_vars()
        F = self._calculate_fluxes()

        # Create left and right states at each of the (nx+1) interfaces
        U_L, U_R = self.U[:, :-1], self.U[:, 1:]
        F_L, F_R = F[:, :-1], F[:, 1:]
        u_L, u_R = u[:-1], u[1:]
        c_L, c_R = c[:-1], c[1:]

        # Calculate wave speeds at interfaces
        s_L = u_L - c_L
        s_R = u_R + c_R

        # Initialize flux vector
        F_hll = np.zeros((2, self.nx + 1))

        # Vectorized HLL flux calculation
        # Identify the three regions based on wave speeds
        idx_L_pos = s_L >= 0
        idx_R_neg = s_R <= 0
        idx_star = np.logical_and(s_L < 0, s_R > 0)

        # Case 1: Supersonic flow from the left
        F_hll[:, idx_L_pos] = F_L[:, idx_L_pos]

        # Case 2: Supersonic flow from the right
        F_hll[:, idx_R_neg] = F_R[:, idx_R_neg]

        # Case 3: Subsonic/transonic flow (the "star" region)
        s_L_star, s_R_star = s_L[idx_star], s_R[idx_star]
        U_L_star, U_R_star = U_L[:, idx_star], U_R[:, idx_star]
        F_L_star, F_R_star = F_L[:, idx_star], F_R[:, idx_star]

        # Denominator for the HLL flux formula
        s_diff = s_R_star - s_L_star
        # Avoid division by zero
        s_diff[s_diff == 0] = 1e-9

        F_hll[:, idx_star] = (s_R_star * F_L_star - s_L_star * F_R_star +
                             s_L_star * s_R_star * (U_R_star - U_L_star)) / s_diff

        return F_hll

    def step(self, dt, upstream_bc, downstream_bc):
        """
        Advances the model state by one time step using a FVM scheme.
        """
        self._apply_boundary_conditions(upstream_bc, downstream_bc)

        fluxes = self._apply_hll_solver()
        source_terms = self._calculate_source_terms()

        # Update state vector for computational cells (from index 1 to -2)
        self.U[:, 1:-1] = (self.U[:, 1:-1] -
                           (dt / self.dx) * (fluxes[:, 1:] - fluxes[:, :-1]) +
                           dt * source_terms[:, 1:-1])

        self._update_depth_from_area()
        self.Q = self.U[1, :]

    def get_state(self):
        """Returns the current state of the channel (excluding ghost cells)."""
        return {'h': self.h[1:-1], 'Q': self.Q[1:-1]}
