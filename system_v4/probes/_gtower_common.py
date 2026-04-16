"""Shared helpers for G-structure tower sims.

Reduction chain: GL(n) -> O(n) -> SO(n) -> U(n) -> SU(n) -> Sp(n)

These are admissibility probes: given a matrix (or pair) we ask whether it
is admitted by the reduced structure. 'Admitted' does not mean 'is the
correct object' -- it means the probe cannot exclude it at this tier.
"""
import numpy as np

classification = "canonical"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "shared helper only; tool usage is delegated to tower sims"},
    "pyg": {"tried": False, "used": False, "reason": "shared helper only; tool usage is delegated to tower sims"},
    "z3": {"tried": False, "used": False, "reason": "shared helper only; proof use is delegated to tower sims"},
    "cvc5": {"tried": False, "used": False, "reason": "shared helper only; proof use is delegated to tower sims"},
    "sympy": {"tried": False, "used": False, "reason": "shared helper only; symbolic use is delegated to tower sims"},
    "clifford": {"tried": False, "used": False, "reason": "shared helper only; geometric algebra use is delegated to tower sims"},
    "geomstats": {"tried": False, "used": False, "reason": "shared helper only; manifold use is delegated to tower sims"},
    "e3nn": {"tried": False, "used": False, "reason": "shared helper only; equivariant use is delegated to tower sims"},
    "rustworkx": {"tried": False, "used": False, "reason": "shared helper only; graph use is delegated to tower sims"},
    "xgi": {"tried": False, "used": False, "reason": "shared helper only; hypergraph use is delegated to tower sims"},
    "toponetx": {"tried": False, "used": False, "reason": "shared helper only; cell-complex use is delegated to tower sims"},
    "gudhi": {"tried": False, "used": False, "reason": "shared helper only; persistence use is delegated to tower sims"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

TOL = 1e-9


def is_invertible(A, tol=TOL):
    A = np.asarray(A)
    if A.ndim != 2 or A.shape[0] != A.shape[1]:
        return False
    return abs(np.linalg.det(A)) > tol


def in_On(A, tol=1e-8):
    A = np.asarray(A, dtype=float)
    n = A.shape[0]
    return np.allclose(A.T @ A, np.eye(n), atol=tol)


def in_SOn(A, tol=1e-8):
    return in_On(A, tol) and np.linalg.det(A) > 0


def in_Un(U, tol=1e-8):
    U = np.asarray(U, dtype=complex)
    n = U.shape[0]
    return np.allclose(U.conj().T @ U, np.eye(n), atol=tol)


def in_SUn(U, tol=1e-8):
    if not in_Un(U, tol):
        return False
    return abs(np.linalg.det(U) - 1.0) < tol


def standard_J(n):
    """Standard complex structure J on R^{2n}: J^2 = -I."""
    I = np.eye(n)
    Z = np.zeros((n, n))
    return np.block([[Z, -I], [I, Z]])


def standard_omega(n):
    """Standard symplectic form on R^{2n}."""
    I = np.eye(n)
    Z = np.zeros((n, n))
    return np.block([[Z, I], [-I, Z]])


def in_Spn_real(A, tol=1e-8):
    """A in Sp(2n, R): A^T omega A = omega."""
    A = np.asarray(A, dtype=float)
    m = A.shape[0]
    if m % 2 != 0:
        return False
    omega = standard_omega(m // 2)
    return np.allclose(A.T @ omega @ A, omega, atol=tol)
