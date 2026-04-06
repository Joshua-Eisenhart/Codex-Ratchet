#!/usr/bin/env python3
"""
Geometric Operators — Layer 3 Library
======================================
First layer with dynamics. Operators act on pre-existing topology.

The four operators as CPTP maps on 2×2 density matrices (SU(2)):

  Ti (constraint/projection):
    Lüders projection toward a specific fiber.
    Acts ALONG the fiber direction.
    Reduces off-diagonal coherence.

  Fe (release/frame rotation):
    U_z(φ) unitary rotation on the Bloch sphere.
    F-kernel (rotation class) per locked Ax5 ledger.
    Preserves purity; z-axis phase evolution.

  Te (exploration/dephasing):
    σ_x dephasing channel (T-kernel per locked Ax5 ledger).
    Destroys x-coherence while preserving σ_x populations.
    Dissipative: increases entropy.

  Fi (filter/selection):
    U_x(θ) unitary rotation on the Bloch sphere.
    F-kernel (rotation class) per locked Ax5 ledger.
    Preserves purity; x-axis phase evolution.

Each operator has polarity (up/down):
  UP = active/forward direction
  DOWN = passive/reverse direction

Key constraint: operators do NOT define stages — they act on them.
The stages (Se/Si/Ne/Ni) are pre-existing topology from Layer 2.
"""

import numpy as np
from typing import Tuple

# Pauli matrices (the generators of SU(2))
SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)
I2 = np.eye(2, dtype=complex)


def _ensure_valid_density(rho: np.ndarray) -> np.ndarray:
    """Enforce ρ ≥ 0, Tr(ρ) = 1, Hermitian."""
    rho = (rho + rho.conj().T) / 2  # Hermiticity
    evals, evecs = np.linalg.eigh(rho)
    evals = np.maximum(evals, 0)  # PSD
    rho = evecs @ np.diag(evals.astype(complex)) @ evecs.conj().T
    tr = np.real(np.trace(rho))
    if tr > 1e-15:
        rho /= tr  # Trace 1
    else:
        rho = I2 / 2  # Fallback to maximally mixed
    return rho


def partial_trace_A(rho_AB: np.ndarray, dims: Tuple[int, int] = (2, 2)) -> np.ndarray:
    """Tr_A(rho_AB) = sum_i (<i| ⊗ I) rho_AB (|i> ⊗ I). Returns 2x2 density matrix for B subsystem."""
    d_A, d_B = dims
    rho_B = np.zeros((d_B, d_B), dtype=complex)
    for i in range(d_A):
        bra_i = np.zeros(d_A, dtype=complex)
        bra_i[i] = 1.0
        proj = np.kron(bra_i.reshape(1, -1), np.eye(d_B, dtype=complex))
        rho_B += proj @ rho_AB @ proj.conj().T
    return rho_B


def partial_trace_B(rho_AB: np.ndarray, dims: Tuple[int, int] = (2, 2)) -> np.ndarray:
    """Tr_B(rho_AB) = sum_j (I ⊗ <j|) rho_AB (I ⊗ |j>). Returns 2x2 density matrix for A subsystem."""
    d_A, d_B = dims
    rho_A = np.zeros((d_A, d_A), dtype=complex)
    for j in range(d_B):
        bra_j = np.zeros(d_B, dtype=complex)
        bra_j[j] = 1.0
        proj = np.kron(np.eye(d_A, dtype=complex), bra_j.reshape(1, -1))
        rho_A += proj @ rho_AB @ proj.conj().T
    return rho_A


# ═══════════════════════════════════════════════════════════════════
# Ti: CONSTRAINT / PROJECTION (acts along fiber)
# ═══════════════════════════════════════════════════════════════════

def apply_Ti(rho: np.ndarray, polarity_up: bool = True, strength: float = 1.0) -> np.ndarray:
    """Ti — Lüders projection (constraint operator).

    Projects ρ toward computational basis states (fiber alignment).
    This acts ALONG the Hopf fiber: it selects which phase the
    state sits at, reducing off-diagonal coherence.

    UP polarity: hard projection (complete dephasing)
    DOWN polarity: soft projection (partial dephasing)

    CPTP: Σᵢ Pᵢ ρ Pᵢ† where Pᵢ = |i⟩⟨i|
    """
    P0 = np.array([[1, 0], [0, 0]], dtype=complex)
    P1 = np.array([[0, 0], [0, 1]], dtype=complex)

    rho_projected = P0 @ rho @ P0 + P1 @ rho @ P1

    if polarity_up:
        # Hard: full dephasing
        mix = strength
    else:
        # Soft: partial dephasing
        mix = 0.3 * strength

    rho_out = mix * rho_projected + (1 - mix) * rho
    return _ensure_valid_density(rho_out)


# ═══════════════════════════════════════════════════════════════════
# Fe: DISSIPATION / RELEASE (acts across fibers on base)
# ═══════════════════════════════════════════════════════════════════

def apply_Fe(rho: np.ndarray, polarity_up: bool = True,
             strength: float = 1.0, phi: float = 0.4) -> np.ndarray:
    """Fe — U_z(φ) rotation (F-kernel, release operator).

    Unitary evolution: ρ → U_z(φ) ρ U_z(φ)†
    where U_z(φ) = exp(-i φ/2 σ_z) = diag(e^{-iφ/2}, e^{iφ/2}).
    F-kernel = rotation class per locked Ax5 ledger.

    UP polarity: positive rotation angle
    DOWN polarity: negative rotation angle

    Unitary: preserves purity and eigenvalues of ρ.

    NOTE: Previously implemented as amplitude damping — corrected 2026-03-29
    per v5_OPERATOR_MATH_LEDGER.md (Ax5 T/F kernel lock).
    """
    sign = 1.0 if polarity_up else -1.0
    angle = sign * phi * strength
    # U_z(φ) = diag(e^{-iφ/2}, e^{iφ/2})
    U = np.array([[np.exp(-1j * angle / 2), 0],
                  [0, np.exp(1j * angle / 2)]], dtype=complex)
    rho_out = U @ rho @ U.conj().T
    return _ensure_valid_density(rho_out)


# ═══════════════════════════════════════════════════════════════════
# Te: ROTATION / EXPLORATION (acts within fiber)
# ═══════════════════════════════════════════════════════════════════

def apply_Te(rho: np.ndarray, polarity_up: bool = True,
             strength: float = 1.0, q: float = 0.7) -> np.ndarray:
    """Te — σ_x dephasing (T-kernel, exploration operator).

    CPTP map: (1 - q₂)ρ + q₂(Q₊ρQ₊ + Q₋ρQ₋)
    where Q₊ = |+⟩⟨+| = [[1,1],[1,1]]/2 and Q₋ = |-⟩⟨-| = [[1,-1],[-1,1]]/2
    are the σ_x eigenprojectors.
    T-kernel = dissipative dephasing class per locked Ax5 ledger.

    UP polarity: strong dephasing (mix = q)
    DOWN polarity: weak dephasing (mix = 0.3 × q)

    Dissipative: destroys x-coherence, increases entropy toward σ_x eigenstate.

    NOTE: Previously implemented as σ_y Hamiltonian rotation — corrected 2026-03-29
    per v5_OPERATOR_MATH_LEDGER.md (Ax5 T/F kernel lock).
    """
    mix = strength * (q if polarity_up else 0.3 * q)
    mix = min(mix, 1.0)
    # σ_x eigenprojectors: Q± = |±⟩⟨±|
    Q_plus = np.array([[1, 1], [1, 1]], dtype=complex) / 2
    Q_minus = np.array([[1, -1], [-1, 1]], dtype=complex) / 2
    rho_out = (1 - mix) * rho + mix * (Q_plus @ rho @ Q_plus + Q_minus @ rho @ Q_minus)
    return _ensure_valid_density(rho_out)


# ═══════════════════════════════════════════════════════════════════
# Fi: FILTER / SELECTION (acts on base, selects fibers)
# ═══════════════════════════════════════════════════════════════════

def apply_Fi(rho: np.ndarray, polarity_up: bool = True,
             strength: float = 1.0, theta: float = 0.4) -> np.ndarray:
    """Fi — U_x(θ) rotation (F-kernel, selection operator).

    Unitary evolution: ρ → U_x(θ) ρ U_x(θ)†
    where U_x(θ) = exp(-i θ/2 σ_x) = cos(θ/2)I - i sin(θ/2)σ_x.
    F-kernel = rotation class per locked Ax5 ledger.
    Unlike Fe (U_z), Fi rotates around the x-axis, mixing |0⟩ and |1⟩
    populations — produces genuine non-commutativity with Ti (σ_z dephasing).

    UP polarity: positive rotation angle
    DOWN polarity: negative rotation angle

    Unitary: preserves purity and eigenvalues of ρ.

    NOTE: Previously implemented as spectral amplitude filter — corrected 2026-03-29
    per v5_OPERATOR_MATH_LEDGER.md (Ax5 T/F kernel lock).
    """
    sign = 1.0 if polarity_up else -1.0
    angle = sign * theta * strength
    # U_x(θ) = cos(θ/2)I - i sin(θ/2)σ_x
    U = np.cos(angle / 2) * I2 - 1j * np.sin(angle / 2) * SIGMA_X
    rho_out = U @ rho @ U.conj().T
    return _ensure_valid_density(rho_out)


# ═══════════════════════════════════════════════════════════════════
# OPERATOR REGISTRY
# ═══════════════════════════════════════════════════════════════════

OPERATOR_MAP = {
    "Ti": apply_Ti,
    "Fe": apply_Fe,
    "Te": apply_Te,
    "Fi": apply_Fi,
}


def apply_operator(name: str, rho: np.ndarray,
                   polarity_up: bool = True,
                   strength: float = 1.0) -> np.ndarray:
    """Apply a named operator to a density matrix.

    Args:
        name: One of 'Ti', 'Fe', 'Te', 'Fi'.
        rho: 2×2 density matrix.
        polarity_up: Direction of operator action.
        strength: Amplitude of operator [0, 1].

    Returns:
        Transformed 2×2 density matrix.
    """
    if name not in OPERATOR_MAP:
        raise ValueError(f"Unknown operator: {name}. Must be one of {list(OPERATOR_MAP.keys())}")
    return OPERATOR_MAP[name](rho, polarity_up=polarity_up, strength=strength)


def negentropy(rho: np.ndarray) -> float:
    """Negentropy Φ = log(d) - S(ρ). For 2x2 d=2, for 4x4 d=4."""
    from hopf_manifold import von_neumann_entropy_2x2
    # Determine dimension from shape
    d = rho.shape[0]
    # Re-use the entropy compute logic which works for any hermitian PSD matrix
    rho_copy = (rho + rho.conj().T) / 2
    evals = np.linalg.eigvalsh(rho_copy)
    evals = evals[evals > 1e-15]
    s = float(-np.sum(evals * np.log2(evals))) if len(evals) > 0 else 0.0
    return np.log2(d) - s


def delta_phi(rho_before: np.ndarray, rho_after: np.ndarray) -> float:
    """Change in negentropy: ΔΦ = Φ(after) - Φ(before)."""
    return negentropy(rho_after) - negentropy(rho_before)


def trace_distance_4x4(rho: np.ndarray, sigma: np.ndarray) -> float:
    """Trace distance D(ρ, σ) = ½ Tr|ρ - σ| for 4x4 matrices."""
    diff = rho - sigma
    evals = np.linalg.eigvalsh(diff)
    return float(0.5 * np.sum(np.abs(evals)))


# ═══════════════════════════════════════════════════════════════════
# JOINT 4x4 OPERATORS
# ═══════════════════════════════════════════════════════════════════

def apply_Ti_4x4(rho_AB: np.ndarray, polarity_up: bool = True, strength: float = 1.0) -> np.ndarray:
    """Ti — Lüders projection natively on 4x4 joint space using ZZ interaction."""
    # Ti entangler is ZZ
    op = np.kron(SIGMA_Z, SIGMA_Z)
    
    # We apply the dephasing native to the bipartite state
    P0 = (np.eye(4, dtype=complex) + op) / 2
    P1 = (np.eye(4, dtype=complex) - op) / 2
    
    rho_projected = P0 @ rho_AB @ P0 + P1 @ rho_AB @ P1
    mix = strength if polarity_up else 0.3 * strength
    
    rho_out = mix * rho_projected + (1 - mix) * rho_AB
    return _ensure_valid_density(rho_out)

def apply_Fe_4x4(rho_AB: np.ndarray, polarity_up: bool = True, strength: float = 1.0, phi: float = 0.4) -> np.ndarray:
    """Fe — U_xx rotation natively on 4x4 joint space."""
    # Fe rotates using XX entangling Hamiltonian
    sign = 1.0 if polarity_up else -1.0
    angle = sign * phi * strength
    H_int = np.kron(SIGMA_X, SIGMA_X)
    U = np.cos(angle / 2) * np.eye(4, dtype=complex) - 1j * np.sin(angle / 2) * H_int
    
    rho_out = U @ rho_AB @ U.conj().T
    return _ensure_valid_density(rho_out)

def apply_Te_4x4(rho_AB: np.ndarray, polarity_up: bool = True, strength: float = 1.0, q: float = 0.7) -> np.ndarray:
    """Te — Dephasing natively on 4x4 joint space using YY interaction."""
    op = np.kron(SIGMA_Y, SIGMA_Y)
    
    # YY Eigenprojectors
    P_plus = (np.eye(4, dtype=complex) + op) / 2
    P_minus = (np.eye(4, dtype=complex) - op) / 2
    
    mix = min(strength * (q if polarity_up else 0.3 * q), 1.0)
    rho_projected = P_plus @ rho_AB @ P_plus + P_minus @ rho_AB @ P_minus
    
    rho_out = (1 - mix) * rho_AB + mix * rho_projected
    return _ensure_valid_density(rho_out)

def apply_Fi_4x4(rho_AB: np.ndarray, polarity_up: bool = True, strength: float = 1.0, theta: float = 0.4) -> np.ndarray:
    """Fi — U_xz rotation natively on 4x4 joint space (selection logic mapping)."""
    # Fi rotates using XZ entangling Hamiltonian so it is distinct from Fe (XX)
    sign = 1.0 if polarity_up else -1.0
    angle = sign * theta * strength
    H_int = np.kron(SIGMA_X, SIGMA_Z)
    U = np.cos(angle / 2) * np.eye(4, dtype=complex) - 1j * np.sin(angle / 2) * H_int
    
    rho_out = U @ rho_AB @ U.conj().T
    return _ensure_valid_density(rho_out)

OPERATOR_MAP_4X4 = {
    "Ti": apply_Ti_4x4,
    "Fe": apply_Fe_4x4,
    "Te": apply_Te_4x4,
    "Fi": apply_Fi_4x4,
}


def delta_phi(rho_before: np.ndarray, rho_after: np.ndarray) -> float:
    """Change in negentropy: ΔΦ = Φ(after) - Φ(before).
    Positive = structure gained (SG).
    Negative = entropy emitted (EE).
    """
    return negentropy(rho_after) - negentropy(rho_before)


def trace_distance_2x2(rho: np.ndarray, sigma: np.ndarray) -> float:
    """Trace distance D(ρ, σ) = ½ Tr|ρ - σ|."""
    diff = rho - sigma
    evals = np.linalg.eigvalsh(diff)
    return float(0.5 * np.sum(np.abs(evals)))
