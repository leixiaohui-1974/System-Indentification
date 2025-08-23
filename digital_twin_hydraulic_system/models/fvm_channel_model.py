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

        self.U = np.zeros((2, self.nx))
        self.h = np.full(self.nx, config.INITIAL_WATER_DEPTH)
        self.A = self._area(self.h)

        initial_h = config.INITIAL_WATER_DEPTH
        initial_A = (self.bottom_width + self.side_slope * initial_h) * initial_h
        initial_P = self.bottom_width + 2 * initial_h * np.sqrt(1 + self.side_slope**2)
        initial_R = initial_A / initial_P if initial_P > 0 else 0
        q_initial = (1/self.manning_n) * initial_A * (initial_R**(2/3)) * (self.S0**0.5)

        self.Q = np.full(self.nx, q_initial)
        self.U[0, :] = self.A
        self.U[1, :] = self.Q

        logger.debug("FVM Channel Model (Model A) initialized.")

    def _area(self, h):
        return (self.bottom_width + self.side_slope * h) * h

    def _wetted_perimeter(self, h):
        return self.bottom_width + 2 * h * np.sqrt(1 + self.side_slope**2)

    def step(self, dt, upstream_bc, downstream_bc):
        """
        Advances the model state by one time step (dt).

        Args:
            dt (float): The time step.
            upstream_bc (dict): Upstream boundary condition, e.g., {'type': 'inflow', 'value': 50}.
            downstream_bc (dict): Downstream BC, e.g., {'type': 'depth', 'value': 2.5}.
        """
        # ---
        # This is where the core FVM solver logic will go.
        # It involves:
        # 1. Calculating fluxes at the interfaces between cells.
        # 2. Applying a numerical scheme (e.g., Roe, HLL) to compute inter-cell fluxes.
        # 3. Calculating source terms (bed slope, friction).
        # 4. Updating the state vector U using the conservative formula:
        #    U_new = U_old - (dt/dx) * (F_right - F_left) + dt * S
        # ---
        # For now, we'll just implement a placeholder update.
        # This is NOT a real solver yet.

        # Placeholder: a simple wave propagation for demonstration
        self.h = self.h + 0.001 * np.sin(np.linspace(0, 2*np.pi, self.nx))

        # Handle upstream boundary condition safely
        if upstream_bc and 'value' in upstream_bc:
            # Set inflow at the first cell and propagate it for this placeholder
            inflow_value = upstream_bc.get('value', self.Q[0])
            self.Q.fill(inflow_value)

        # Update state vector
        self.A = self._area(self.h)
        self.U[0, :] = self.A
        self.U[1, :] = self.Q

    def get_state(self):
        """Returns the current state of the channel."""
        return {'h': self.h, 'Q': self.Q}
