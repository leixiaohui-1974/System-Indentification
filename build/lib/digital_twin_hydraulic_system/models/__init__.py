# -*- coding: utf-8 -*-
"""
This package contains the different mathematical models for the simulation.
- gate_model: Calculates flow through the sluice gate.
- fvm_channel_model: High-fidelity 'real-world' simulation (Model A).
- id_channel_model: Simplified 'digital twin' model (Model B).
"""
# This makes it easier to import classes from the package
from .gate_model import GateModel
from .fvm_channel_model import FVMChannelModel
from .id_channel_model import IDChannelModel
