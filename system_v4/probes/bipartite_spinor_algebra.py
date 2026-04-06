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
