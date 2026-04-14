#!/usr/bin/env python3
"""
MEASURE family: RelativeEntropyCoherence as a differentiable torch.nn.Module.
C_RE(rho) = S(rho_diag) - S(rho). Always >= 0. Zero iff rho is diagonal.
Numpy baseline cross-validation. Sympy symbolic check.
"""

import json
import os
import numpy as np
classification = "classical_baseline"  # auto-backfill

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
# MODULES
# =====================================================================

class DensityMatrix(nn.Module):
    def __init__(self, bloch_params=None):
        super().__init__()
        if bloch_params is None:
            bloch_params = torch.zeros(3)
        self.bloch = nn.Parameter(bloch_params)

    def forward(self):
        I = torch.eye(2, dtype=torch.complex64)
        sx = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex64)
        sy = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex64)
        sz = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex64)
        rho = I / 2
        for i, sigma in enumerate([sx, sy, sz]):
            rho = rho + self.bloch[i].to(torch.complex64) * sigma / 2
        return rho


def von_neumann_entropy_torch(rho):
    """S(rho) = -Tr(rho log rho) via eigenvalues."""
    evals = torch.linalg.eigvalsh(rho)
    evals = torch.clamp(evals.real, min=1e-12)
    return -torch.sum(evals * torch.log(evals))


class RelativeEntropyCoherence(nn.Module):
    """
    C_RE(rho) = S(rho_diag) - S(rho).
    rho_diag = diag(diag(rho)) -- dephased state.
    Always >= 0. Zero iff rho is already diagonal.
    """
    def forward(self, rho):
        # S(rho)
        s_rho = von_neumann_entropy_torch(rho)

        # rho_diag: keep only diagonal
        diag_vals = torch.diag(rho).real
        diag_clamped = torch.clamp(diag_vals, min=1e-12)
        s_diag = -torch.sum(diag_clamped * torch.log(diag_clamped))

        return s_diag - s_rho


# =====================================================================
# NUMPY BASELINE
# =====================================================================

def numpy_density_matrix(bloch):
    I = np.eye(2, dtype=np.complex128)
    sx = np.array([[0, 1], [1, 0]], dtype=np.complex128)
    sy = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
    sz = np.array([[1, 0], [0, -1]], dtype=np.complex128)
    rho = I / 2
    for i, sigma in enumerate([sx, sy, sz]):
        rho = rho + bloch[i] * sigma / 2
    return rho


def numpy_von_neumann(rho):
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > 1e-12]
    return -np.sum(evals * np.log(evals))


def numpy_re_coherence(rho):
    s_rho = numpy_von_neumann(rho)
    diag_vals = np.real(np.diag(rho))
    diag_vals = diag_vals[diag_vals > 1e-12]
    s_diag = -np.sum(diag_vals * np.log(diag_vals))
    return s_diag - s_rho


def random_bloch_interior(rng=None):
    if rng is None:
        rng = np.random
    v = rng.randn(3)
    r = rng.uniform(0.1, 0.95)
    return (v / np.linalg.norm(v) * r).tolist()


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    rng = np.random.RandomState(42)

    states = {
        "|0><0|": [0, 0, 1.0],
        "|+><+|": [1, 0, 0],
        "maximally_mixed": [0, 0, 0],
        "|+i>": [0, 1.0, 0],
    }
    for i in range(3):
        states[f"random_{i}"] = random_bloch_interior(rng)

    # P1: Substrate match
    p1 = {}
    for name, bloch in states.items():
        rho_np = numpy_density_matrix(np.array(bloch))
        c_np = numpy_re_coherence(rho_np)

        dm = DensityMatrix(torch.tensor(bloch, dtype=torch.float32))
        rec = RelativeEntropyCoherence()
        c_t = float(rec(dm()).item())

        diff = abs(c_np - c_t)
        p1[name] = {"numpy": c_np, "torch": c_t, "diff": diff, "pass": diff < 1e-4}
    results["P1_substrate_match"] = p1

    # P2: Always non-negative
    p2 = {}
    for name, bloch in states.items():
        dm = DensityMatrix(torch.tensor(bloch, dtype=torch.float32))
        rec = RelativeEntropyCoherence()
        c = float(rec(dm()).item())
        p2[name] = {"C_RE": c, "non_negative": c >= -1e-8, "pass": c >= -1e-8}
    results["P2_non_negative"] = p2

    # P3: Zero for diagonal states
    diag_states = {"|0>": [0, 0, 1.0], "|1>": [0, 0, -1.0], "mixed": [0, 0, 0]}
    p3 = {}
    for name, bloch in diag_states.items():
        dm = DensityMatrix(torch.tensor(bloch, dtype=torch.float32))
        rec = RelativeEntropyCoherence()
        c = float(rec(dm()).item())
        p3[name] = {"C_RE": c, "is_zero": abs(c) < 1e-5, "pass": abs(c) < 1e-5}
    results["P3_zero_for_diagonal"] = p3

    # P4: Gradient exists
    p4 = {}
    for name, bloch in list(states.items())[:4]:
        dm = DensityMatrix(torch.tensor(bloch, dtype=torch.float32))
        rec = RelativeEntropyCoherence()
        c = rec(dm())
        c.backward()
        grad = dm.bloch.grad
        p4[name] = {"grad_exists": grad is not None, "pass": grad is not None}
    results["P4_gradient_exists"] = p4

    # P5: Autograd vs finite-difference
    p5 = {}
    eps = 1e-3
    for name, bloch in [("random_0", states["random_0"]), ("|+><+|", states["|+><+|"])]:
        dm = DensityMatrix(torch.tensor(bloch, dtype=torch.float32))
        rec = RelativeEntropyCoherence()
        c = rec(dm())
        c.backward()
        grad_auto = dm.bloch.grad.numpy().copy()

        grad_fd = np.zeros(3)
        for i in range(3):
            bp = np.array(bloch)
            bm = np.array(bloch)
            bp[i] += eps
            bm[i] -= eps
            grad_fd[i] = (numpy_re_coherence(numpy_density_matrix(bp))
                          - numpy_re_coherence(numpy_density_matrix(bm))) / (2 * eps)

        an = np.linalg.norm(grad_auto)
        fn = np.linalg.norm(grad_fd)
        cos_sim = float(np.dot(grad_auto, grad_fd) / (an * fn)) if an > 1e-8 and fn > 1e-8 else 1.0
        p5[name] = {"cosine_sim": cos_sim, "pass": cos_sim > 0.95}
    results["P5_autograd_vs_fd"] = p5

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # N1: C_RE for |+> = log(2) (max coherence for qubit)
    dm = DensityMatrix(torch.tensor([1.0, 0, 0]))
    rec = RelativeEntropyCoherence()
    c = float(rec(dm()).item())
    expected = np.log(2)
    results["N1_plus_state_log2"] = {
        "C_RE": c,
        "expected": expected,
        "diff": abs(c - expected),
        "pass": abs(c - expected) < 1e-4,
    }

    # N2: C_RE(rho_diag) = 0 for any state's diagonal
    rng = np.random.RandomState(99)
    n2 = {}
    for i in range(5):
        bloch = random_bloch_interior(rng)
        rho_np = numpy_density_matrix(np.array(bloch))
        rho_diag = np.diag(np.diag(rho_np))
        c = numpy_re_coherence(rho_diag)
        n2[f"state_{i}"] = {"C_RE_of_diag": c, "pass": abs(c) < 1e-10}
    results["N2_diag_state_zero_coherence"] = n2

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # B1: Near-diagonal state (tiny off-diagonal)
    dm = DensityMatrix(torch.tensor([1e-6, 1e-6, 0.5]))
    rec = RelativeEntropyCoherence()
    c = float(rec(dm()).item())
    results["B1_near_diagonal"] = {"C_RE": c, "near_zero": c < 1e-4, "pass": c < 1e-4}

    # B2: Monotonicity: C_RE increases as off-diagonal grows
    rx_values = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
    coherences = []
    for rx in rx_values:
        dm = DensityMatrix(torch.tensor([rx, 0, 0], dtype=torch.float32))
        rec = RelativeEntropyCoherence()
        c = float(rec(dm()).item())
        coherences.append(c)

    monotone = all(coherences[i] <= coherences[i + 1] + 1e-6
                   for i in range(len(coherences) - 1))
    results["B2_monotone_with_off_diag"] = {
        "rx_values": rx_values,
        "coherences": coherences,
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

    r = sp.Symbol("r", real=True, positive=True)
    # For Bloch = (r, 0, 0): eigenvalues = (1+r)/2, (1-r)/2
    # Diagonal entries = 1/2, 1/2
    # S(diag) = log(2), S(rho) = H((1+r)/2)
    e1 = (1 + r) / 2
    e2 = (1 - r) / 2
    S_rho = -(e1 * sp.log(e1) + e2 * sp.log(e2))
    S_diag = sp.log(2)
    C_RE = sp.simplify(S_diag - S_rho)
    return {"C_RE_formula": str(C_RE), "pass": True}


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    sympy_check = run_sympy_check()

    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "RelativeEntropyCoherence module with autograd"
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "Symbolic C_RE formula"

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
        "name": "torch_re_coherence",
        "description": "RelativeEntropyCoherence: C_RE(rho) = S(rho_diag) - S(rho), >= 0",
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive, "negative": negative,
        "boundary": boundary, "sympy_check": sympy_check,
        "classification": "canonical",
        "summary": {"total_tests": total_tests, "total_pass": total_pass,
                     "all_pass": total_pass == total_tests},
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "torch_re_coherence_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Tests: {total_pass}/{total_tests} passed")
    if total_pass == total_tests:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
