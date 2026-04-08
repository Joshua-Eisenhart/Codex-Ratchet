"""
qit_partial_trace.py — Canonical partial trace utilities for QIT probes.

Correct einsum index conventions for a bipartite system rho_AB
reshaped as (d_A, d_B, d_A, d_B):

    partial_trace_A: traces out A -> rho_B = einsum('aiaj->ij', rho)
    partial_trace_B: traces out B -> rho_A = einsum('iaja->ij', rho)

Use these instead of inline einsum calls to avoid index bugs.
"""

import torch
import numpy as np


# ---------------------------------------------------------------------------
# Torch versions
# ---------------------------------------------------------------------------

def partial_trace_A(rho_AB, d_A=2, d_B=2):
    """Trace out subsystem A, return rho_B (shape d_B x d_B)."""
    reshaped = rho_AB.reshape(d_A, d_B, d_A, d_B)
    return torch.einsum('aiaj->ij', reshaped)


def partial_trace_B(rho_AB, d_A=2, d_B=2):
    """Trace out subsystem B, return rho_A (shape d_A x d_A)."""
    reshaped = rho_AB.reshape(d_A, d_B, d_A, d_B)
    return torch.einsum('iaja->ij', reshaped)


# ---------------------------------------------------------------------------
# Numpy versions
# ---------------------------------------------------------------------------

def np_partial_trace_A(rho_AB, d_A=2, d_B=2):
    """Trace out subsystem A, return rho_B (shape d_B x d_B)."""
    reshaped = rho_AB.reshape(d_A, d_B, d_A, d_B)
    return np.einsum('aiaj->ij', reshaped)


def np_partial_trace_B(rho_AB, d_A=2, d_B=2):
    """Trace out subsystem B, return rho_A (shape d_A x d_A)."""
    reshaped = rho_AB.reshape(d_A, d_B, d_A, d_B)
    return np.einsum('iaja->ij', reshaped)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def _run_tests():
    """Verify on Bell state: Tr_A(Bell) = Tr_B(Bell) = I/2."""
    print("=" * 60)
    print("qit_partial_trace self-test")
    print("=" * 60)

    # |Bell> = (|00> + |11>) / sqrt(2)
    bell = np.zeros(4, dtype=complex)
    bell[0] = 1.0 / np.sqrt(2)
    bell[3] = 1.0 / np.sqrt(2)
    rho_bell = np.outer(bell, bell.conj())
    I_over_2 = np.eye(2, dtype=complex) / 2.0

    # Numpy tests
    rho_B_np = np_partial_trace_A(rho_bell)
    rho_A_np = np_partial_trace_B(rho_bell)

    assert rho_B_np.shape == (2, 2), f"rho_B shape wrong: {rho_B_np.shape}"
    assert rho_A_np.shape == (2, 2), f"rho_A shape wrong: {rho_A_np.shape}"
    assert np.allclose(rho_B_np, I_over_2), f"Tr_A(Bell) != I/2:\n{rho_B_np}"
    assert np.allclose(rho_A_np, I_over_2), f"Tr_B(Bell) != I/2:\n{rho_A_np}"
    print("[PASS] numpy Tr_A(Bell) = I/2")
    print("[PASS] numpy Tr_B(Bell) = I/2")

    # Torch tests
    rho_bell_t = torch.tensor(rho_bell, dtype=torch.complex128)
    rho_B_t = partial_trace_A(rho_bell_t)
    rho_A_t = partial_trace_B(rho_bell_t)
    I_over_2_t = torch.eye(2, dtype=torch.complex128) / 2.0

    assert rho_B_t.shape == (2, 2), f"rho_B shape wrong: {rho_B_t.shape}"
    assert rho_A_t.shape == (2, 2), f"rho_A shape wrong: {rho_A_t.shape}"
    assert torch.allclose(rho_B_t, I_over_2_t), f"Tr_A(Bell) != I/2:\n{rho_B_t}"
    assert torch.allclose(rho_A_t, I_over_2_t), f"Tr_B(Bell) != I/2:\n{rho_A_t}"
    print("[PASS] torch Tr_A(Bell) = I/2")
    print("[PASS] torch Tr_B(Bell) = I/2")

    # Additional: product state |0>|1> should give pure reduced states
    psi = np.zeros(4, dtype=complex)
    psi[1] = 1.0  # |01>
    rho_prod = np.outer(psi, psi.conj())
    rho_B_prod = np_partial_trace_A(rho_prod)
    rho_A_prod = np_partial_trace_B(rho_prod)
    assert np.allclose(rho_A_prod, np.array([[1, 0], [0, 0]], dtype=complex)), "Tr_B(|01>) != |0><0|"
    assert np.allclose(rho_B_prod, np.array([[0, 0], [0, 1]], dtype=complex)), "Tr_A(|01>) != |1><1|"
    print("[PASS] product state |01>: Tr_B = |0><0|, Tr_A = |1><1|")

    # Trace preservation
    rho_bell_t2 = torch.tensor(rho_bell, dtype=torch.complex128)
    assert abs(torch.trace(partial_trace_A(rho_bell_t2)).real - 1.0) < 1e-10, "Tr(rho_B) != 1"
    assert abs(torch.trace(partial_trace_B(rho_bell_t2)).real - 1.0) < 1e-10, "Tr(rho_A) != 1"
    print("[PASS] trace preservation: Tr(rho_A) = Tr(rho_B) = 1")

    print("=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    _run_tests()
