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

  Fe (dissipation/release):
    Lindblad dissipation along the base S².
    Acts ACROSS fibers (base transport).
    Drives toward a fixed point via jump operators.

  Te (rotation/exploration):
    Hamiltonian rotation around the fiber S¹.
    Unitary evolution WITHIN a fiber.
    Preserves purity, redistributes coherence.

  Fi (filter/selection):
    Spectral filter on the base S².
    Selects which fiber states survive.
    Amplifies dominant eigenstates.

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
             strength: float = 1.0, dt: float = 0.05) -> np.ndarray:
    """Fe — Lindblad dissipation (release operator).

    Drives ρ toward a fixed point via amplitude damping.
    This acts ACROSS the Hopf fibers: it transports population
    from one fiber to another (base motion on S²).

    UP polarity: strong coupling (fast decay)
    DOWN polarity: weak coupling (slow decay)

    CPTP: amplitude damping channel with γ = strength × dt
    """
    # Amplitude damping: decay toward |0⟩
    gamma = strength * dt * (3.0 if polarity_up else 1.0)
    gamma = min(gamma, 1.0)  # Clamp

    # Kraus operators for amplitude damping
    K0 = np.array([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=complex)
    K1 = np.array([[0, np.sqrt(gamma)], [0, 0]], dtype=complex)

    rho_out = K0 @ rho @ K0.conj().T + K1 @ rho @ K1.conj().T
    return _ensure_valid_density(rho_out)


# ═══════════════════════════════════════════════════════════════════
# Te: ROTATION / EXPLORATION (acts within fiber)
# ═══════════════════════════════════════════════════════════════════

def apply_Te(rho: np.ndarray, polarity_up: bool = True,
             strength: float = 1.0, angle: float = 0.3) -> np.ndarray:
    """Te — Hamiltonian rotation (exploration operator).

    Unitary evolution: ρ → U ρ U† where U = exp(-i θ H).
    This acts WITHIN the Hopf fiber: it rotates the state
    around the Bloch sphere without leaving the fiber.

    UP polarity: positive rotation (explore forward)
    DOWN polarity: negative rotation (explore backward)

    Unitary: preserves eigenvalues of ρ (isometric).
    """
    # Hamiltonian: rotation around y-axis (moves between |0⟩ and |1⟩)
    H = SIGMA_Y
    sign = 1.0 if polarity_up else -1.0
    theta = sign * angle * strength

    # U = exp(-i θ H) = cos(θ)I - i sin(θ)H for Pauli matrix
    U = np.cos(theta) * I2 - 1j * np.sin(theta) * H
    rho_out = U @ rho @ U.conj().T
    return _ensure_valid_density(rho_out)


# ═══════════════════════════════════════════════════════════════════
# Fi: FILTER / SELECTION (acts on base, selects fibers)
# ═══════════════════════════════════════════════════════════════════

def apply_Fi(rho: np.ndarray, polarity_up: bool = True,
             strength: float = 1.0) -> np.ndarray:
    """Fi — Spectral filter (selection operator).

    Selectively amplifies one eigenstate of ρ.
    This acts ON the base S²: it selects which fiber
    (which Bloch direction) survives.

    UP polarity: emissive (amplify dominant, suppress rest)
    DOWN polarity: absorptive (retain more, gentle selection)

    CPTP: generalized measurement with selective amplification.

    Important nuance:
      - On mixed inputs, Fi typically changes eigenvalues and therefore entropy.
      - On pure inputs, Fi can preserve purity (ΔΦ ≈ 0) while still strongly
        changing direction/population bias after renormalization.
    """
    # Filter operator: amplify |0⟩ component relative to |1⟩
    # r = attenuation factor for |1⟩ component. r=1 → identity, r→0 → project onto |0⟩.
    # At strength=0, r must be 1 (identity). At strength=1, maximum filtering.
    if polarity_up:
        r = 1.0 - 0.7 * strength  # Strong filter at s=1: r=0.3
    else:
        r = 1.0 - 0.3 * strength  # Gentle filter at s=1: r=0.7

    F = np.array([[1, 0], [0, r]], dtype=complex)
    rho_out = F @ rho @ F.conj().T
    tr = np.real(np.trace(rho_out))
    if tr > 1e-15:
        rho_out /= tr
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
    """Negentropy Φ = log(d) - S(ρ) for d=2."""
    from hopf_manifold import von_neumann_entropy_2x2
    return np.log(2) - von_neumann_entropy_2x2(rho) * np.log(2)


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
