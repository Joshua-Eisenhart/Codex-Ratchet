#!/usr/bin/env python3
"""Bipartite spinor algebra for the 2-qubit geometric engine.

This module keeps the joint-state path explicit and geometry-first:
- no np.kron in the hot path
- explicit 4x4 tensor-product construction
- Pauli-basis reconstruction/extraction
- partial traces, correlations, concurrence
- involutory two-qubit gates from geometric bivectors

The goal is to let the engine keep a real 4D tensor product structure
without falling back to a generic kron-heavy helper path.
"""

from __future__ import annotations

import numpy as np

I2 = np.array([[1, 0], [0, 1]], dtype=complex)
SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)


def tensor2(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """Explicit 2x2 ⊗ 2x2 -> 4x4 tensor product using block structure."""
    A = np.asarray(A, dtype=complex)
    B = np.asarray(B, dtype=complex)
    out = np.zeros((4, 4), dtype=complex)
    out[0:2, 0:2] = A[0, 0] * B
    out[0:2, 2:4] = A[0, 1] * B
    out[2:4, 0:2] = A[1, 0] * B
    out[2:4, 2:4] = A[1, 1] * B
    return out


I4 = tensor2(I2, I2)
XX = tensor2(SIGMA_X, SIGMA_X)
XY = tensor2(SIGMA_X, SIGMA_Y)
XZ = tensor2(SIGMA_X, SIGMA_Z)
YX = tensor2(SIGMA_Y, SIGMA_X)
YY = tensor2(SIGMA_Y, SIGMA_Y)
YZ = tensor2(SIGMA_Y, SIGMA_Z)
ZX = tensor2(SIGMA_Z, SIGMA_X)
ZY = tensor2(SIGMA_Z, SIGMA_Y)
ZZ = tensor2(SIGMA_Z, SIGMA_Z)

PAULI = (SIGMA_X, SIGMA_Y, SIGMA_Z)
PAULI_4 = (
    (tensor2(SIGMA_X, I2), tensor2(SIGMA_Y, I2), tensor2(SIGMA_Z, I2)),
    (tensor2(I2, SIGMA_X), tensor2(I2, SIGMA_Y), tensor2(I2, SIGMA_Z)),
)
PAULI_TENSOR = (
    (XX, XY, XZ),
    (YX, YY, YZ),
    (ZX, ZY, ZZ),
)


def ensure_valid_density(rho: np.ndarray) -> np.ndarray:
    """Hermitize, PSD-project, and renormalize a density matrix."""
    rho = np.asarray(rho, dtype=complex)
    rho = (rho + rho.conj().T) / 2
    evals, evecs = np.linalg.eigh(rho)
    evals = np.maximum(evals, 0.0)
    rho = evecs @ np.diag(evals.astype(complex)) @ evecs.conj().T
    tr = np.real(np.trace(rho))
    if tr > 1e-15:
        rho /= tr
    else:
        rho = I4 / 4.0
    return rho


def bloch_to_density(r: np.ndarray) -> np.ndarray:
    r = np.asarray(r, dtype=float)
    return (I2 + r[0] * SIGMA_X + r[1] * SIGMA_Y + r[2] * SIGMA_Z) / 2.0


def density_to_bloch(rho: np.ndarray) -> np.ndarray:
    rho = np.asarray(rho, dtype=complex)
    return np.array([
        np.real(np.trace(SIGMA_X @ rho)),
        np.real(np.trace(SIGMA_Y @ rho)),
        np.real(np.trace(SIGMA_Z @ rho)),
    ], dtype=float)


def partial_trace_B(rho_ab: np.ndarray) -> np.ndarray:
    """Trace out B from a 4x4 joint state (keep A)."""
    rho = np.asarray(rho_ab, dtype=complex).reshape(2, 2, 2, 2)
    return rho[:, 0, :, 0] + rho[:, 1, :, 1]


def partial_trace_A(rho_ab: np.ndarray) -> np.ndarray:
    """Trace out A from a 4x4 joint state (keep B)."""
    rho = np.asarray(rho_ab, dtype=complex).reshape(2, 2, 2, 2)
    return rho[0, :, 0, :] + rho[1, :, 1, :]


def product_density_from_bloch(r_L: np.ndarray, r_R: np.ndarray) -> np.ndarray:
    """Exact product state ρ_L ⊗ ρ_R in the computational basis."""
    rho_L = bloch_to_density(r_L)
    rho_R = bloch_to_density(r_R)
    out = np.zeros((4, 4), dtype=complex)
    for i in range(2):
        for j in range(2):
            out[i * 2:(i + 1) * 2, j * 2:(j + 1) * 2] = rho_L[i, j] * rho_R
    return ensure_valid_density(out)


def build_joint_density(r_L: np.ndarray, r_R: np.ndarray, C: np.ndarray) -> np.ndarray:
    """Build ρ_AB from marginals plus excess correlation tensor C."""
    r_L = np.asarray(r_L, dtype=float)
    r_R = np.asarray(r_R, dtype=float)
    C = np.asarray(C, dtype=float)
    T = np.outer(r_L, r_R) + C
    rho = I4.copy()
    for i in range(3):
        rho = rho + r_L[i] * PAULI_4[0][i]
        rho = rho + r_R[i] * PAULI_4[1][i]
    for i in range(3):
        for j in range(3):
            rho = rho + T[i, j] * PAULI_TENSOR[i][j]
    return ensure_valid_density(rho / 4.0)


def correlation_tensor(rho_ab: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (r_L, r_R, C_excess) for a 4x4 joint state."""
    rho_ab = ensure_valid_density(rho_ab)
    rho_L = partial_trace_B(rho_ab)
    rho_R = partial_trace_A(rho_ab)
    r_L = density_to_bloch(rho_L)
    r_R = density_to_bloch(rho_R)
    T = np.zeros((3, 3), dtype=float)
    for i in range(3):
        for j in range(3):
            T[i, j] = np.real(np.trace(rho_ab @ PAULI_TENSOR[i][j]))
    C = T - np.outer(r_L, r_R)
    return r_L, r_R, C


def entangling_hamiltonian(n_hat: np.ndarray) -> np.ndarray:
    """H = (n·σ) ⊗ (n·σ) with explicit tensor basis."""
    n_hat = np.asarray(n_hat, dtype=float)
    n_sigma = n_hat[0] * SIGMA_X + n_hat[1] * SIGMA_Y + n_hat[2] * SIGMA_Z
    return tensor2(n_sigma, n_sigma)


def involution_unitary(H: np.ndarray, angle: float) -> np.ndarray:
    """U = cos(a/2) I - i sin(a/2) H for Hermitian involution H^2 = I."""
    H = np.asarray(H, dtype=complex)
    return np.cos(angle / 2.0) * I4 - 1j * np.sin(angle / 2.0) * H


def concurrence_4x4(rho_ab: np.ndarray) -> float:
    """Wootters concurrence without np.kron in the hot path."""
    rho_ab = ensure_valid_density(rho_ab)
    sy_sy = YY
    rho_tilde = sy_sy @ rho_ab.conj() @ sy_sy
    evals = np.linalg.eigvals(rho_ab @ rho_tilde)
    roots = np.sort(np.real(np.sqrt(np.maximum(evals, 0.0))))[::-1]
    return float(max(0.0, roots[0] - roots[1] - roots[2] - roots[3]))


def trace_distance(rho: np.ndarray, sigma: np.ndarray) -> float:
    diff = ensure_valid_density(rho) - ensure_valid_density(sigma)
    evals = np.linalg.eigvalsh(diff)
    return float(0.5 * np.sum(np.abs(evals)))


# =====================================================================
# BELL BASIS — explicit computational-basis vectors, no kron
# =====================================================================

# Computational basis kets for 2-qubit system
_KET_00 = np.array([1, 0, 0, 0], dtype=complex)
_KET_01 = np.array([0, 1, 0, 0], dtype=complex)
_KET_10 = np.array([0, 0, 1, 0], dtype=complex)
_KET_11 = np.array([0, 0, 0, 1], dtype=complex)

# Bell states: |Φ±⟩ = (|00⟩ ± |11⟩)/√2,  |Ψ±⟩ = (|01⟩ ± |10⟩)/√2
BELL_PHI_PLUS  = (_KET_00 + _KET_11) / np.sqrt(2)
BELL_PHI_MINUS = (_KET_00 - _KET_11) / np.sqrt(2)
BELL_PSI_PLUS  = (_KET_01 + _KET_10) / np.sqrt(2)
BELL_PSI_MINUS = (_KET_01 - _KET_10) / np.sqrt(2)

BELL_STATES = (BELL_PHI_PLUS, BELL_PHI_MINUS, BELL_PSI_PLUS, BELL_PSI_MINUS)

# Bell projectors (rank-1)
BELL_PROJECTORS = tuple(np.outer(b, b.conj()) for b in BELL_STATES)


def bell_diagonal(p_phi_p: float, p_phi_m: float,
                  p_psi_p: float, p_psi_m: float) -> np.ndarray:
    """Build a Bell-diagonal state from four probabilities (must sum to 1)."""
    return (p_phi_p * BELL_PROJECTORS[0] +
            p_phi_m * BELL_PROJECTORS[1] +
            p_psi_p * BELL_PROJECTORS[2] +
            p_psi_m * BELL_PROJECTORS[3])


def bell_mix(rho_ab: np.ndarray, alpha: float) -> np.ndarray:
    """Mix ρ_AB toward the nearest Bell-diagonal state.

    alpha=0 → unchanged, alpha=1 → fully Bell-diagonal projection.
    The Bell-diagonal projection keeps only the diagonal in the Bell basis.
    """
    rho_ab = np.asarray(rho_ab, dtype=complex)
    # Project: keep only ⟨Bk|ρ|Bk⟩ components
    probs = np.array([np.real(b.conj() @ rho_ab @ b) for b in BELL_STATES])
    probs = np.maximum(probs, 0.0)
    s = probs.sum()
    if s > 1e-15:
        probs /= s
    else:
        probs = np.array([0.25, 0.25, 0.25, 0.25])
    rho_bell = bell_diagonal(*probs)
    rho_out = (1.0 - alpha) * rho_ab + alpha * rho_bell
    return ensure_valid_density(rho_out)


def bell_decompose(rho_ab: np.ndarray) -> np.ndarray:
    """Return the 4-vector of Bell-basis probabilities [p_Φ+, p_Φ-, p_Ψ+, p_Ψ-]."""
    rho_ab = np.asarray(rho_ab, dtype=complex)
    return np.array([np.real(b.conj() @ rho_ab @ b) for b in BELL_STATES])


# =====================================================================
# LOCAL OPERATOR APPLICATION — algebraic lift 2x2 → 4x4
# =====================================================================

def lift_left(op_2x2: np.ndarray) -> np.ndarray:
    """Lift a 2x2 operator to (op ⊗ I) as a 4x4 matrix."""
    return tensor2(op_2x2, I2)


def lift_right(op_2x2: np.ndarray) -> np.ndarray:
    """Lift a 2x2 operator to (I ⊗ op) as a 4x4 matrix."""
    return tensor2(I2, op_2x2)


def apply_local_unitary_left(rho_ab: np.ndarray, U: np.ndarray) -> np.ndarray:
    """Apply (U ⊗ I) ρ (U† ⊗ I) — unitary on subsystem A."""
    U4 = lift_left(U)
    return U4 @ rho_ab @ U4.conj().T


def apply_local_unitary_right(rho_ab: np.ndarray, U: np.ndarray) -> np.ndarray:
    """Apply (I ⊗ U) ρ (I ⊗ U†) — unitary on subsystem B."""
    U4 = lift_right(U)
    return U4 @ rho_ab @ U4.conj().T


def apply_local_channel_left(rho_ab: np.ndarray,
                             kraus_ops: list[np.ndarray]) -> np.ndarray:
    """Apply Σ_i (K_i ⊗ I) ρ (K_i† ⊗ I) — CPTP channel on subsystem A."""
    out = np.zeros((4, 4), dtype=complex)
    for K in kraus_ops:
        K4 = lift_left(K)
        out += K4 @ rho_ab @ K4.conj().T
    return out


def apply_local_channel_right(rho_ab: np.ndarray,
                              kraus_ops: list[np.ndarray]) -> np.ndarray:
    """Apply Σ_i (I ⊗ K_i) ρ (I ⊗ K_i†) — CPTP channel on subsystem B."""
    out = np.zeros((4, 4), dtype=complex)
    for K in kraus_ops:
        K4 = lift_right(K)
        out += K4 @ rho_ab @ K4.conj().T
    return out


def apply_local_channel_both(rho_ab: np.ndarray,
                             kraus_L: list[np.ndarray],
                             kraus_R: list[np.ndarray]) -> np.ndarray:
    """Apply independent channels on L and R: Σ_{i,j} (K^L_i ⊗ K^R_j) ρ (...)†.

    This is the algebraically exact way to apply two independent local
    channels to a joint state — no basis probing, no approximation.
    """
    out = np.zeros((4, 4), dtype=complex)
    for KL in kraus_L:
        for KR in kraus_R:
            K4 = tensor2(KL, KR)
            out += K4 @ rho_ab @ K4.conj().T
    return out


# =====================================================================
# KRAUS DECOMPOSITIONS for Ti/Fe/Te/Fi operators
# =====================================================================

def kraus_Ti(polarity_up: bool = True, strength: float = 1.0) -> list[np.ndarray]:
    """Kraus operators for Ti (σ_z dephasing / Lüders projection).

    Channel: (1-p)ρ + p(P0 ρ P0 + P1 ρ P1)  where p = mix.
    Kraus: {√(1-p) I, √p P0, √p P1}  with P0=|0⟩⟨0|, P1=|1⟩⟨1|.
    """
    mix = strength if polarity_up else 0.3 * strength
    P0 = np.array([[1, 0], [0, 0]], dtype=complex)
    P1 = np.array([[0, 0], [0, 1]], dtype=complex)
    return [np.sqrt(1 - mix) * I2, np.sqrt(mix) * P0, np.sqrt(mix) * P1]


def kraus_Fe(polarity_up: bool = True, strength: float = 1.0,
             phi: float = 0.4) -> list[np.ndarray]:
    """Kraus operators for Fe (U_z rotation). Single unitary Kraus op."""
    sign = 1.0 if polarity_up else -1.0
    angle = sign * phi * strength
    U = np.array([[np.exp(-1j * angle / 2), 0],
                  [0, np.exp(1j * angle / 2)]], dtype=complex)
    return [U]


def kraus_Te(polarity_up: bool = True, strength: float = 1.0,
             q: float = 0.7) -> list[np.ndarray]:
    """Kraus operators for Te (σ_x dephasing).

    Channel: (1-p)ρ + p(Q+ ρ Q+ + Q- ρ Q-)  where p = mix.
    Kraus: {√(1-p) I, √p Q+, √p Q-}  with Q± = |±⟩⟨±|.
    """
    mix = min(strength * (q if polarity_up else 0.3 * q), 1.0)
    Q_plus = np.array([[1, 1], [1, 1]], dtype=complex) / 2
    Q_minus = np.array([[1, -1], [-1, 1]], dtype=complex) / 2
    return [np.sqrt(1 - mix) * I2, np.sqrt(mix) * Q_plus, np.sqrt(mix) * Q_minus]


def kraus_Fi(polarity_up: bool = True, strength: float = 1.0,
             theta: float = 0.4) -> list[np.ndarray]:
    """Kraus operators for Fi (U_x rotation). Single unitary Kraus op."""
    sign = 1.0 if polarity_up else -1.0
    angle = sign * theta * strength
    U = np.cos(angle / 2) * I2 - 1j * np.sin(angle / 2) * SIGMA_X
    return [U]


KRAUS_MAP = {
    "Ti": kraus_Ti,
    "Fe": kraus_Fe,
    "Te": kraus_Te,
    "Fi": kraus_Fi,
}


# =====================================================================
# BLOCH MAP EXTRACTION — algebraic, not basis-probing
# =====================================================================

def bloch_map_from_kraus(kraus_ops: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    """Compute the affine Bloch map (M, t) for a single-qubit channel.

    For channel Φ(ρ) = Σ K_i ρ K_i†, the Bloch vector transforms as:
        r' = M @ r + t
    where M is 3×3 and t is 3-vector.

    M_jk = Σ_i ½ Re[Tr(σ_j K_i σ_k K_i†)]
    t_j   = Σ_i ½ Re[Tr(σ_j K_i K_i†)]  (but Σ K_i K_i† = I for CPTP → t from I/2 image)

    This is the exact algebraic formula — no basis probing.
    """
    M = np.zeros((3, 3), dtype=float)
    t = np.zeros(3, dtype=float)
    for K in kraus_ops:
        KdK = K.conj().T
        for j in range(3):
            # t contribution: Tr(σ_j K I/2 K†) summed = Tr(σ_j Φ(I/2))
            # but we compute per-K and sum
            t[j] += 0.5 * np.real(np.trace(PAULI[j] @ K @ KdK))
            for k in range(3):
                M[j, k] += 0.5 * np.real(np.trace(PAULI[j] @ K @ PAULI[k] @ KdK))
    # t is already the image of the zero Bloch vector (maximally mixed state)
    # but Φ(I/2) = I/2 + t·σ/2 for CPTP, so t = bloch(Φ(I/2))
    # However, M already captures the linear part. The full transform is r' = M@r + t.
    # For trace-preserving channels t = bloch(Φ(I/2)) which we computed above.
    # But actually: Φ(ρ) = (I + (M@r + t)·σ)/2, and Φ(I/2) = (I + t·σ)/2
    # so t_j = Tr(σ_j Φ(I/2)). Let's recompute t cleanly:
    rho_max_mixed = I2 / 2.0
    phi_mm = sum(K @ rho_max_mixed @ K.conj().T for K in kraus_ops)
    t = np.array([np.real(np.trace(PAULI[j] @ phi_mm)) for j in range(3)])
    return M, t


def correlation_transform(C: np.ndarray,
                          M_L: np.ndarray, M_R: np.ndarray) -> np.ndarray:
    """Transform excess correlation tensor under local channels: C' = M_L @ C @ M_R^T."""
    return M_L @ C @ M_R.T
