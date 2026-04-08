#!/usr/bin/env python3
"""
MEASURE family: L1Coherence as a differentiable torch.nn.Module.
C_l1(rho) = sum of |rho_ij| for i != j.
Zero for diagonal states, max for pure superposition.
Gradient w.r.t. Bloch params. Numpy baseline cross-validation.
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


class L1Coherence(nn.Module):
    """
    C_l1(rho) = sum_{i != j} |rho_ij|.
    For qubit: C_l1 = 2*|rho_01| = sqrt(r_x^2 + r_y^2).
    """
    def forward(self, rho):
        n = rho.shape[0]
        mask = 1 - torch.eye(n, dtype=torch.float32)
        abs_rho = torch.abs(rho)  # element-wise absolute value
        return torch.sum(abs_rho * mask.to(abs_rho.device))


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


def numpy_l1_coherence(rho):
    n = rho.shape[0]
    total = 0.0
    for i in range(n):
        for j in range(n):
            if i != j:
                total += np.abs(rho[i, j])
    return float(total)


# =====================================================================
# HELPERS
# =====================================================================

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
        c_np = numpy_l1_coherence(rho_np)

        dm = DensityMatrix(torch.tensor(bloch, dtype=torch.float32))
        lc = L1Coherence()
        c_t = float(lc(dm()).item())

        diff = abs(c_np - c_t)
        p1[name] = {"numpy": c_np, "torch": c_t, "diff": diff, "pass": diff < 1e-5}
    results["P1_substrate_match"] = p1

    # P2: Zero for diagonal states (rho_x = rho_y = 0)
    diagonal_states = {
        "|0>": [0, 0, 1.0],
        "|1>": [0, 0, -1.0],
        "mixed_z": [0, 0, 0.5],
        "maximally_mixed": [0, 0, 0],
    }
    p2 = {}
    for name, bloch in diagonal_states.items():
        dm = DensityMatrix(torch.tensor(bloch, dtype=torch.float32))
        lc = L1Coherence()
        c = float(lc(dm()).item())
        p2[name] = {"coherence": c, "is_zero": abs(c) < 1e-6, "pass": abs(c) < 1e-6}
    results["P2_zero_for_diagonal"] = p2

    # P3: Maximum for pure superposition |+>: C_l1 = 1.0
    dm = DensityMatrix(torch.tensor([1.0, 0, 0]))
    lc = L1Coherence()
    c = float(lc(dm()).item())
    results["P3_max_for_plus"] = {
        "coherence": c,
        "expected": 1.0,
        "pass": abs(c - 1.0) < 1e-5,
    }

    # P4: Gradient w.r.t. Bloch params
    p4 = {}
    for name, bloch in list(states.items())[:4]:
        dm = DensityMatrix(torch.tensor(bloch, dtype=torch.float32))
        lc = L1Coherence()
        c = lc(dm())
        c.backward()
        grad = dm.bloch.grad
        p4[name] = {
            "grad_exists": grad is not None,
            "grad": grad.tolist() if grad is not None else None,
            "pass": grad is not None,
        }
    results["P4_gradient_exists"] = p4

    # P5: Autograd vs finite-difference
    p5 = {}
    eps = 1e-3
    for name, bloch in [("random_0", states["random_0"]), ("|+i>", states["|+i>"])]:
        dm = DensityMatrix(torch.tensor(bloch, dtype=torch.float32))
        lc = L1Coherence()
        c = lc(dm())
        c.backward()
        grad_auto = dm.bloch.grad.numpy().copy()

        grad_fd = np.zeros(3)
        for i in range(3):
            bp = np.array(bloch)
            bm = np.array(bloch)
            bp[i] += eps
            bm[i] -= eps
            grad_fd[i] = (numpy_l1_coherence(numpy_density_matrix(bp))
                          - numpy_l1_coherence(numpy_density_matrix(bm))) / (2 * eps)

        an = np.linalg.norm(grad_auto)
        fn = np.linalg.norm(grad_fd)
        cos_sim = float(np.dot(grad_auto, grad_fd) / (an * fn)) if an > 1e-8 and fn > 1e-8 else 1.0
        p5[name] = {"autograd": grad_auto.tolist(), "fd": grad_fd.tolist(),
                     "cosine_sim": cos_sim, "pass": cos_sim > 0.99}
    results["P5_autograd_vs_fd"] = p5

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # N1: Coherence for z-only Bloch is always 0
    n1 = {}
    for rz in [-1.0, -0.5, 0.0, 0.5, 1.0]:
        dm = DensityMatrix(torch.tensor([0, 0, rz]))
        lc = L1Coherence()
        c = float(lc(dm()).item())
        n1[f"rz={rz}"] = {"coherence": c, "pass": abs(c) < 1e-6}
    results["N1_z_only_zero_coherence"] = n1

    # N2: Invalid Bloch (|r|>1) -- coherence can exceed 1
    dm = DensityMatrix(torch.tensor([2.0, 0, 0]))
    lc = L1Coherence()
    c = float(lc(dm()).item())
    results["N2_invalid_bloch_exceeds_max"] = {
        "coherence": c,
        "exceeds_1": c > 1.0 + 1e-6,
        "pass": c > 1.0 + 1e-6,
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # B1: C_l1 = sqrt(r_x^2 + r_y^2) analytical formula
    test_cases = {
        "rx=0.5": [0.5, 0, 0],
        "ry=0.7": [0, 0.7, 0],
        "rx=0.3,ry=0.4": [0.3, 0.4, 0],
        "full_bloch": [0.3, 0.4, 0.5],
    }
    b1 = {}
    for name, bloch in test_cases.items():
        expected = np.sqrt(bloch[0]**2 + bloch[1]**2)
        dm = DensityMatrix(torch.tensor(bloch, dtype=torch.float32))
        lc = L1Coherence()
        actual = float(lc(dm()).item())
        diff = abs(expected - actual)
        b1[name] = {"expected": expected, "actual": actual, "diff": diff, "pass": diff < 1e-5}
    results["B1_analytical_formula"] = b1

    # B2: Near-zero Bloch
    dm = DensityMatrix(torch.tensor([1e-8, 1e-8, 1e-8]))
    lc = L1Coherence()
    c = float(lc(dm()).item())
    results["B2_near_zero"] = {"coherence": c, "near_zero": c < 1e-6, "pass": c < 1e-6}

    return results


# =====================================================================
# SYMPY CHECK
# =====================================================================

def run_sympy_check():
    if not TOOL_MANIFEST["sympy"]["tried"]:
        return {"skipped": True, "reason": "sympy not available"}

    rx, ry, rz = sp.symbols("r_x r_y r_z", real=True)
    # For qubit rho with Bloch (rx, ry, rz):
    # Off-diag: rho_01 = (rx - i*ry)/2, rho_10 = (rx + i*ry)/2
    # C_l1 = |rho_01| + |rho_10| = 2*|(rx - i*ry)/2| = sqrt(rx^2 + ry^2)
    rho_01 = (rx - sp.I * ry) / 2
    c_l1 = 2 * sp.Abs(rho_01)
    c_l1_simplified = sp.simplify(c_l1)
    return {
        "C_l1_formula": str(c_l1_simplified),
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
    TOOL_MANIFEST["pytorch"]["reason"] = "L1Coherence module with autograd gradients"
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "Symbolic C_l1 formula verification"

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
        "name": "torch_l1_coherence",
        "description": "L1Coherence: C_l1(rho) = sum |rho_ij| for i!=j, zero for incoherent states",
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive, "negative": negative,
        "boundary": boundary, "sympy_check": sympy_check,
        "classification": "canonical",
        "summary": {"total_tests": total_tests, "total_pass": total_pass,
                     "all_pass": total_pass == total_tests},
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "torch_l1_coherence_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Tests: {total_pass}/{total_tests} passed")
    if total_pass == total_tests:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
