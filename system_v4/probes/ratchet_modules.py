#!/usr/bin/env python3
"""
ratchet_modules.py -- Shared importable module hub.

Re-exports the nn.Module classes from individual sim files so that
downstream integration sims can build REAL dependency chains via:

    from ratchet_modules import DensityMatrix, ZDephasing, CNOT, ...

This file imports from the original sim files. The classes live there.
This is a thin re-export layer, not a copy.
"""

# --- DensityMatrix: Bloch-parameterized 2x2 density matrix ---
from sim_torch_density_matrix_pilot import DensityMatrix

# --- Channels ---
from torch_modules.amplitude_damping import AmplitudeDamping
from torch_modules.bit_flip import BitFlip
from torch_modules.depolarizing import Depolarizing
from torch_modules.phase_damping import PhaseDamping
from torch_modules.z_dephasing import ZDephasing

# --- Gates ---
from sim_torch_cnot import CNOT

# --- Measures ---
from sim_torch_mutual_info import MutualInformation, partial_trace_A, partial_trace_B

# --- Geometry ---
from sim_torch_hopf_connection import HopfConnection

__all__ = [
    "DensityMatrix",
    "ZDephasing",
    "AmplitudeDamping",
    "BitFlip",
    "Depolarizing",
    "PhaseDamping",
    "CNOT",
    "MutualInformation",
    "partial_trace_A",
    "partial_trace_B",
    "HopfConnection",
]
