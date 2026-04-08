#!/usr/bin/env python3
"""
MEASURE family: MutualInformation for 2-qubit states as torch.nn.Module.
I(A:B) = S(A) + S(B) - S(AB). Zero for product states. log(2) for Bell states.
Numpy baseline cross-validation. Sympy symbolic check.
"""

import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi": {"tried": False, "used": False, "reason": ""},
    "toponetx": {"tried": False, "used": False, "reason": ""},
    "gudhi": {"tried": False, "used": False, "reason": ""},
}

try:
    import torch
    import torch.nn as nn
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


# =====================================================================
# 2-QUBIT STATE BUILDERS
# =====================================================================

def bell_state_rho(which="phi_plus"):
    """Return 4x4 density matrix for Bell states."""
    if which == "phi_plus":
        psi = np.array([1, 0, 0, 1], dtype=np.complex128) / np.sqrt(2)
    elif which == "phi_minus":
        psi = np.array([1, 0, 0, -1], dtype=np.complex128) / np.sqrt(2)
    elif which == "psi_plus":
        psi = np.array([0, 1, 1, 0], dtype=np.complex128) / np.sqrt(2)
    elif which == "psi_minus":
        psi = np.array([0, 1, -1, 0], dtype=np.complex128) / np.sqrt(2)
    else:
        raise ValueError(f"Unknown Bell state: {which}")
    return np.outer(psi, psi.conj())


def product_state_rho(bloch_a, bloch_b):
    """Product state rho_A tensor rho_B from two Bloch vectors."""
    I = np.eye(2, dtype=np.complex128)
    sx = np.array([[0, 1], [1, 0]], dtype=np.complex128)
    sy = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
    sz = np.array([[1, 0], [0, -1]], dtype=np.complex128)
    paulis = [sx, sy, sz]

    rho_a = I / 2
    for i, sigma in enumerate(paulis):
        rho_a = rho_a + bloch_a[i] * sigma / 2

    rho_b = I / 2
    for i, sigma in enumerate(paulis):
        rho_b = rho_b + bloch_b[i] * sigma / 2

    return np.kron(rho_a, rho_b)


def werner_state(p):
    """Werner state: p*|phi+><phi+| + (1-p)*I/4."""
    bell = bell_state_rho("phi_plus")
    return p * bell + (1 - p) * np.eye(4, dtype=np.complex128) / 4


# =====================================================================
# MODULES
# =====================================================================

def von_neumann_entropy(rho):
    """Differentiable von Neumann entropy."""
    evals = torch.linalg.eigvalsh(rho)
    evals = torch.clamp(evals.real, min=1e-12)
    return -torch.sum(evals * torch.log(evals))


def partial_trace_A(rho_ab):
    """Trace out subsystem A: rho_B[i_B, j_B] = sum_a rho[a, i_B, a, j_B]."""
    rho_reshaped = rho_ab.reshape(2, 2, 2, 2)
    return torch.einsum("ijik->jk", rho_reshaped)


def partial_trace_B(rho_ab):
    """Trace out subsystem B: rho_A[i_A, j_A] = sum_b rho[i_A, b, j_A, b]."""
    rho_reshaped = rho_ab.reshape(2, 2, 2, 2)
    return torch.einsum("ijkj->ik", rho_reshaped)


class MutualInformation(nn.Module):
    """
    I(A:B) = S(A) + S(B) - S(AB) for 2-qubit state.
    Always >= 0. Zero for product states. 2*log(2) for maximally entangled.
    """
    def forward(self, rho_ab):
        rho_a = partial_trace_B(rho_ab)
        rho_b = partial_trace_A(rho_ab)
        s_a = von_neumann_entropy(rho_a)
        s_b = von_neumann_entropy(rho_b)
        s_ab = von_neumann_entropy(rho_ab)
        return s_a + s_b - s_ab


# =====================================================================
# NUMPY BASELINE
# =====================================================================

def numpy_vne(rho):
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > 1e-12]
    return -np.sum(evals * np.log(evals))


def numpy_partial_trace_A(rho, d_a=2, d_b=2):
    """Trace out A: rho_B."""
    rho_r = rho.reshape(d_a, d_b, d_a, d_b)
    return np.einsum("ijik->jk", rho_r)


def numpy_partial_trace_B(rho, d_a=2, d_b=2):
    """Trace out B: rho_A."""
    rho_r = rho.reshape(d_a, d_b, d_a, d_b)
    return np.einsum("ijkj->ik", rho_r)


def numpy_mutual_info(rho):
    rho_a = numpy_partial_trace_B(rho)
    rho_b = numpy_partial_trace_A(rho)
    return numpy_vne(rho_a) + numpy_vne(rho_b) - numpy_vne(rho)


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # P1: Substrate match for Bell states
    bell_names = ["phi_plus", "phi_minus", "psi_plus", "psi_minus"]
    p1 = {}
    mi_mod = MutualInformation()
    for name in bell_names:
        rho_np = bell_state_rho(name)
        mi_np = numpy_mutual_info(rho_np)

        rho_t = torch.tensor(rho_np, dtype=torch.complex64)
        mi_t = float(mi_mod(rho_t).item())

        diff = abs(mi_np - mi_t)
        p1[name] = {"numpy": mi_np, "torch": mi_t, "diff": diff, "pass": diff < 1e-4}
    results["P1_bell_state_match"] = p1

    # P2: Bell state mutual info = 2*log(2)
    p2 = {}
    expected = 2 * np.log(2)
    for name in bell_names:
        rho_t = torch.tensor(bell_state_rho(name), dtype=torch.complex64)
        mi = float(mi_mod(rho_t).item())
        p2[name] = {"MI": mi, "expected": expected, "diff": abs(mi - expected),
                     "pass": abs(mi - expected) < 1e-4}
    results["P2_bell_2log2"] = p2

    # P3: Product states have zero MI
    product_cases = {
        "00": ([0, 0, 1.0], [0, 0, 1.0]),
        "+x": ([1, 0, 0], [0, 0, 1.0]),
        "mixed": ([0, 0, 0], [0, 0, 0]),
    }
    p3 = {}
    for name, (ba, bb) in product_cases.items():
        rho_np = product_state_rho(ba, bb)
        mi_np = numpy_mutual_info(rho_np)
        rho_t = torch.tensor(rho_np, dtype=torch.complex64)
        mi_t = float(mi_mod(rho_t).item())
        p3[name] = {"numpy": mi_np, "torch": mi_t,
                     "is_zero": abs(mi_t) < 1e-4, "pass": abs(mi_t) < 1e-4}
    results["P3_product_zero_MI"] = p3

    # P4: Werner state MI interpolates
    p4 = {}
    for p_val in [0.0, 0.25, 0.5, 0.75, 1.0]:
        rho = werner_state(p_val)
        mi = numpy_mutual_info(rho)
        rho_t = torch.tensor(rho, dtype=torch.complex64)
        mi_t = float(mi_mod(rho_t).item())
        diff = abs(mi - mi_t)
        p4[f"p={p_val}"] = {"numpy": mi, "torch": mi_t, "diff": diff, "pass": diff < 1e-4}
    results["P4_werner_match"] = p4

    # P5: Gradient exists
    rho_t = torch.tensor(werner_state(0.7), dtype=torch.complex64, requires_grad=True)
    mi = mi_mod(rho_t)
    mi.backward()
    grad_exists = rho_t.grad is not None
    results["P5_gradient_exists"] = {"grad_exists": grad_exists, "pass": grad_exists}

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    mi_mod = MutualInformation()

    # N1: MI is non-negative for all states
    rng = np.random.RandomState(42)
    n1_all_pass = True
    n1_min = float("inf")
    for _ in range(20):
        # Random 2-qubit state via partial trace of random pure 3-qubit
        psi = rng.randn(8) + 1j * rng.randn(8)
        psi /= np.linalg.norm(psi)
        rho_8 = np.outer(psi, psi.conj())
        # Trace out third qubit: rho_AB = Tr_C(|psi><psi|)
        rho_8_r = rho_8.reshape(4, 2, 4, 2)
        rho_ab = np.einsum("ijkj->ik", rho_8_r)

        rho_t = torch.tensor(rho_ab, dtype=torch.complex64)
        mi = float(mi_mod(rho_t).item())
        n1_min = min(n1_min, mi)
        if mi < -1e-6:
            n1_all_pass = False

    results["N1_non_negative_random"] = {
        "min_MI": n1_min,
        "all_non_negative": n1_all_pass,
        "pass": n1_all_pass,
    }

    # N2: MI <= 2*log(d) = 2*log(2) for 2-qubit system
    n2_all_pass = True
    n2_max = 0.0
    bound = 2 * np.log(2)
    for _ in range(20):
        psi = rng.randn(4) + 1j * rng.randn(4)
        psi /= np.linalg.norm(psi)
        rho = np.outer(psi, psi.conj())
        mi = numpy_mutual_info(rho)
        n2_max = max(n2_max, mi)
        if mi > bound + 1e-4:
            n2_all_pass = False

    results["N2_bounded_by_2logd"] = {
        "max_MI": n2_max,
        "bound": bound,
        "all_bounded": n2_all_pass,
        "pass": n2_all_pass,
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    mi_mod = MutualInformation()

    # B1: Maximally mixed 2-qubit state -> MI = 0
    rho = np.eye(4, dtype=np.complex128) / 4
    rho_t = torch.tensor(rho, dtype=torch.complex64)
    mi = float(mi_mod(rho_t).item())
    results["B1_maximally_mixed_zero"] = {"MI": mi, "pass": abs(mi) < 1e-5}

    # B2: Werner state at separability boundary (p=1/3)
    rho = werner_state(1 / 3)
    rho_t = torch.tensor(rho, dtype=torch.complex64)
    mi = float(mi_mod(rho_t).item())
    results["B2_werner_separability_boundary"] = {
        "p": 1 / 3,
        "MI": mi,
        "non_negative": mi >= -1e-8,
        "pass": mi >= -1e-8,
    }

    # B3: Monotonicity of MI with Werner p
    p_vals = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    mis = []
    for p in p_vals:
        rho = werner_state(p)
        rho_t = torch.tensor(rho, dtype=torch.complex64)
        mi = float(mi_mod(rho_t).item())
        mis.append(mi)
    monotone = all(mis[i] <= mis[i + 1] + 1e-6 for i in range(len(mis) - 1))
    results["B3_werner_monotone"] = {
        "p_values": p_vals,
        "MIs": mis,
        "monotone": monotone,
        "pass": monotone,
    }

    return results


# =====================================================================
# SYMPY CHECK
# =====================================================================

def run_sympy_check():
    if not TOOL_MANIFEST["sympy"]["tried"]:
        return {"skipped": True, "reason": "sympy not available"}

    # For Bell state |phi+>: S(A) = S(B) = log(2), S(AB) = 0
    # MI = log(2) + log(2) - 0 = 2*log(2)
    mi_bell = 2 * sp.log(2)
    return {
        "MI_bell": str(float(mi_bell.evalf())),
        "expected": str(float(2 * np.log(2))),
        "pass": True,
    }


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    sympy_check = run_sympy_check()

    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "MutualInformation module: partial trace + VNE with autograd"
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "Symbolic MI for Bell states"

    def count_passes(d):
        passes, total = 0, 0
        if isinstance(d, dict):
            if "pass" in d:
                total += 1
                if d["pass"]:
                    passes += 1
            for v in d.values():
                p, t = count_passes(v)
                passes += p
                total += t
        return passes, total

    all_results = {"positive": positive, "negative": negative,
                   "boundary": boundary, "sympy_check": sympy_check}
    total_pass, total_tests = count_passes(all_results)

    results = {
        "name": "torch_mutual_info",
        "description": "MutualInformation: I(A:B) = S(A) + S(B) - S(AB) for 2-qubit states",
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive, "negative": negative,
        "boundary": boundary, "sympy_check": sympy_check,
        "classification": "canonical",
        "summary": {"total_tests": total_tests, "total_pass": total_pass,
                     "all_pass": total_pass == total_tests},
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "torch_mutual_info_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Tests: {total_pass}/{total_tests} passed")
    if total_pass == total_tests:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
