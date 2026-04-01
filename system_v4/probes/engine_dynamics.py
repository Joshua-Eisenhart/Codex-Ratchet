#!/usr/bin/env python3
"""
Engine Dynamics — Layer 1 Path Integration
===========================================
Implements the continuous Lindblad dynamics for the 8 QIT terrains.
Provides the "Engine Substrate" for path integration on S³.

Math Source: apple axes terrain operator math.md
"""

import numpy as np
from typing import List, Tuple

# Pauli Matrices (The Basis)
I2 = np.eye(2, dtype=complex)
SX = np.array([[0, 1], [1, 0]], dtype=complex)
SY = np.array([[0, -1j], [1j, 0]], dtype=complex)
SZ = np.array([[1, 0], [0, -1]], dtype=complex)
SM = np.array([[0, 0], [1, 0]], dtype=complex)  # sigma_minus (sink)
SP = np.array([[0, 1], [0, 0]], dtype=complex)  # sigma_plus (source)

def dissipator(L: np.ndarray, rho: np.ndarray) -> np.ndarray:
    """Lindblad Dissipator: D[L](rho) = L rho L† - 1/2 {L†L, rho}."""
    return L @ rho @ L.conj().T - 0.5 * (L.conj().T @ L @ rho + rho @ L.conj().T @ L)

def lindblad_update(rho: np.ndarray, H: np.ndarray, L_list: List[np.ndarray], dt: float) -> np.ndarray:
    """One-step integration: dρ/dt = -i[H, ρ] + Σ D[L_k](ρ)."""
    # Hamiltonian part
    drho = -1j * (H @ rho - rho @ H)
    # Dissipative part
    for L in L_list:
        drho += dissipator(L, rho)
    
    new_rho = rho + drho * dt
    # Re-normalize to ensure trace 1 and Hermiticity
    new_rho = (new_rho + new_rho.conj().T) / 2
    return new_rho / np.trace(new_rho)

# ═══════════════════════════════════════════════════════════════════
# THE 8 TERRAIN GENERATORS (X_τ,s)
# ═══════════════════════════════════════════════════════════════════

class TerrainGenerators:
    def __init__(self, gamma: float = 0.1, epsilon: float = 0.05, n_vec: np.ndarray = None):
        self.gamma = gamma
        self.epsilon = epsilon
        # Default Hamiltonian direction
        if n_vec is None:
            n_vec = np.array([0, 0, 1.0])
        self.H0 = n_vec[0]*SX + n_vec[1]*SY + n_vec[2]*SZ

    def get_params(self, engine_type: int, terrain_topo: str) -> Tuple[np.ndarray, List[np.ndarray]]:
        """Returns (H, [L_list]) for a specific terrain placement.
        
        Type 1 (Left Weyl): H = +H0
        Type 2 (Right Weyl): H = -H0
        """
        s = 1 if engine_type == 1 else -1
        H = s * self.H0
        
        if terrain_topo == "Se": # Funnel / Cannon
            # Radial Expansion: L = sqrt(gamma) * sigma_z (diagonal expansion)
            L = [np.sqrt(self.gamma) * SZ]
            return H * self.epsilon, L
            
        elif terrain_topo == "Ne": # Vortex / Spiral
            # Tangential Circulation: H is dominant, L is small correction
            L = [np.sqrt(self.epsilon) * SX]
            return H, L
            
        elif terrain_topo == "Ni": # Pit / Source
            # Radial Contraction: L = sigma_minus (sink) or sigma_plus (source)
            L_mat = SM if engine_type == 1 else SP
            L = [np.sqrt(self.gamma) * L_mat]
            return H * self.epsilon, L
            
        elif terrain_topo == "Si": # Hill / Citadel
            # Stratified Retention: Commuting H_C, invariant subspaces
            # Minimal Hill: Projector onto Z-pole
            P_hill = (I2 + SZ) / 2
            L = [np.sqrt(self.gamma) * P_hill]
            return H, L
            
        raise ValueError(f"Unknown topology: {terrain_topo}")

def integrate_path(rho_init: np.ndarray, engine_type: int, terrain_topo: str, 
                   steps: int = 10, dt: float = 0.01) -> np.ndarray:
    """Integrates the Lindblad equation for a stage."""
    gen = TerrainGenerators()
    H, L_list = gen.get_params(engine_type, terrain_topo)
    
    rho = rho_init
    for _ in range(steps):
        rho = lindblad_update(rho, H, L_list, dt)
    return rho
