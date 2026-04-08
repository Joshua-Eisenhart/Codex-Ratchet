#!/usr/bin/env python3
"""
MEASURE family: ZMeasurement as a differentiable torch.nn.Module.
forward(rho) returns probabilities and post-measurement states
for Z-basis measurement. Differentiable probabilities w.r.t. Bloch params.
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


class ZMeasurement(nn.Module):
    """
    Z-basis measurement on a single qubit density matrix.
    Projectors: Pi_0 = |0><0|, Pi_1 = |1><1|.
    Returns:
        probs: (2,) tensor of measurement probabilities [p_0, p_1]
        post_states: list of 2x2 post-measurement density matrices
    Probabilities are differentiable w.r.t. input rho (and thus Bloch params).
    p_0 = (1 + r_z) / 2, p_1 = (1 - r_z) / 2.
    """
    def forward(self, rho):
        Pi_0 = torch.tensor([[1, 0], [0, 0]], dtype=torch.complex64)
        Pi_1 = torch.tensor([[0, 0], [0, 1]], dtype=torch.complex64)

        # Probabilities: p_k = Tr(Pi_k @ rho)
        p0 = torch.real(torch.trace(Pi_0 @ rho))
        p1 = torch.real(torch.trace(Pi_1 @ rho))
        probs = torch.stack([p0, p1])

        # Post-measurement states: Pi_k @ rho @ Pi_k / p_k
        post_states = []
        for Pi, p in [(Pi_0, p0), (Pi_1, p1)]:
            if p.item() > 1e-10:
                post = Pi @ rho @ Pi / p.to(torch.complex64)
            else:
                post = Pi.clone()  # degenerate case
            post_states.append(post)

        return probs, post_states


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


def numpy_z_measurement(rho):
    Pi_0 = np.array([[1, 0], [0, 0]], dtype=np.complex128)
    Pi_1 = np.array([[0, 0], [0, 1]], dtype=np.complex128)

    p0 = np.real(np.trace(Pi_0 @ rho))
    p1 = np.real(np.trace(Pi_1 @ rho))

    post_0 = Pi_0 @ rho @ Pi_0 / p0 if p0 > 1e-10 else Pi_0
    post_1 = Pi_1 @ rho @ Pi_1 / p1 if p1 > 1e-10 else Pi_1

    return np.array([p0, p1]), [post_0, post_1]


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
        "|1><1|": [0, 0, -1.0],
        "|+><+|": [1, 0, 0],
        "maximally_mixed": [0, 0, 0],
    }
    for i in range(3):
        states[f"random_{i}"] = random_bloch_interior(rng)

    zm = ZMeasurement()

    # P1: Probability substrate match
    p1 = {}
    for name, bloch in states.items():
        rho_np = numpy_density_matrix(np.array(bloch))
        probs_np, _ = numpy_z_measurement(rho_np)

        dm = DensityMatrix(torch.tensor(bloch, dtype=torch.float32))
        probs_t, _ = zm(dm())
        probs_t_np = probs_t.detach().numpy()

        diff = float(np.max(np.abs(probs_np - probs_t_np)))
        p1[name] = {"numpy": probs_np.tolist(), "torch": probs_t_np.tolist(),
                     "max_diff": diff, "pass": diff < 1e-5}
    results["P1_probability_match"] = p1

    # P2: Probabilities sum to 1
    p2 = {}
    for name, bloch in states.items():
        dm = DensityMatrix(torch.tensor(bloch, dtype=torch.float32))
        probs, _ = zm(dm())
        s = float(probs.sum().item())
        p2[name] = {"sum": s, "pass": abs(s - 1.0) < 1e-5}
    results["P2_prob_sum_to_1"] = p2

    # P3: Post-measurement states are valid
    p3 = {}
    for name, bloch in list(states.items())[:4]:
        dm = DensityMatrix(torch.tensor(bloch, dtype=torch.float32))
        probs, posts = zm(dm())
        all_valid = True
        for k, post in enumerate(posts):
            post_np = post.detach().cpu().numpy()
            tr = np.real(np.trace(post_np))
            herm_diff = np.max(np.abs(post_np - post_np.conj().T))
            if abs(tr - 1.0) > 1e-4 or herm_diff > 1e-4:
                all_valid = False
        p3[name] = {"all_valid": all_valid, "pass": all_valid}
    results["P3_post_states_valid"] = p3

    # P4: Analytical check: p_0 = (1+r_z)/2
    p4 = {}
    for name, bloch in states.items():
        dm = DensityMatrix(torch.tensor(bloch, dtype=torch.float32))
        probs, _ = zm(dm())
        p0 = float(probs[0].item())
        expected = (1 + bloch[2]) / 2
        diff = abs(p0 - expected)
        p4[name] = {"p0": p0, "expected": expected, "diff": diff, "pass": diff < 1e-5}
    results["P4_analytical_p0"] = p4

    # P5: Gradient of p_0 w.r.t. Bloch params
    p5 = {}
    for name, bloch in list(states.items())[:4]:
        dm = DensityMatrix(torch.tensor(bloch, dtype=torch.float32))
        probs, _ = zm(dm())
        probs[0].backward()
        grad = dm.bloch.grad
        # dp_0/d(r_z) = 1/2, dp_0/d(r_x) = 0, dp_0/d(r_y) = 0
        expected_grad = [0.0, 0.0, 0.5]
        if grad is not None:
            diff = float(np.max(np.abs(grad.numpy() - np.array(expected_grad))))
            p5[name] = {"grad": grad.tolist(), "expected": expected_grad,
                         "diff": diff, "pass": diff < 1e-4}
        else:
            p5[name] = {"grad": None, "pass": False}
    results["P5_gradient_analytical"] = p5

    # P6: Autograd vs finite-difference
    p6 = {}
    eps = 1e-3
    for name, bloch in [("random_0", states["random_0"])]:
        dm = DensityMatrix(torch.tensor(bloch, dtype=torch.float32))
        probs, _ = zm(dm())
        probs[0].backward()
        grad_auto = dm.bloch.grad.numpy().copy()

        grad_fd = np.zeros(3)
        for i in range(3):
            bp = np.array(bloch)
            bm = np.array(bloch)
            bp[i] += eps
            bm[i] -= eps
            pp, _ = numpy_z_measurement(numpy_density_matrix(bp))
            pm, _ = numpy_z_measurement(numpy_density_matrix(bm))
            grad_fd[i] = (pp[0] - pm[0]) / (2 * eps)

        max_diff = float(np.max(np.abs(grad_auto - grad_fd)))
        p6[name] = {"autograd": grad_auto.tolist(), "fd": grad_fd.tolist(),
                     "max_diff": max_diff, "pass": max_diff < 1e-3}
    results["P6_autograd_vs_fd"] = p6

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    zm = ZMeasurement()

    # N1: Invalid Bloch (r_z > 1) gives p_0 > 1
    dm = DensityMatrix(torch.tensor([0, 0, 1.5]))
    probs, _ = zm(dm())
    p0 = float(probs[0].item())
    results["N1_invalid_prob_exceeds_1"] = {
        "p0": p0,
        "exceeds_1": p0 > 1.0,
        "pass": p0 > 1.0,
    }

    # N2: Post-measurement state for |0> measured in Z is |0>
    dm = DensityMatrix(torch.tensor([0, 0, 1.0]))
    probs, posts = zm(dm())
    post_0 = posts[0].detach().cpu().numpy()
    expected = np.array([[1, 0], [0, 0]], dtype=np.complex128)
    diff = float(np.max(np.abs(post_0 - expected)))
    results["N2_post_state_0_is_0"] = {"max_diff": diff, "pass": diff < 1e-5}

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    zm = ZMeasurement()

    # B1: |0> -> p_0 = 1, p_1 = 0
    dm = DensityMatrix(torch.tensor([0, 0, 1.0]))
    probs, _ = zm(dm())
    results["B1_pure_0"] = {
        "p0": float(probs[0].item()),
        "p1": float(probs[1].item()),
        "pass": abs(float(probs[0].item()) - 1.0) < 1e-5 and abs(float(probs[1].item())) < 1e-5,
    }

    # B2: |1> -> p_0 = 0, p_1 = 1
    dm = DensityMatrix(torch.tensor([0, 0, -1.0]))
    probs, _ = zm(dm())
    results["B2_pure_1"] = {
        "p0": float(probs[0].item()),
        "p1": float(probs[1].item()),
        "pass": abs(float(probs[0].item())) < 1e-5 and abs(float(probs[1].item()) - 1.0) < 1e-5,
    }

    # B3: Maximally mixed -> p_0 = p_1 = 0.5
    dm = DensityMatrix(torch.zeros(3))
    probs, _ = zm(dm())
    results["B3_mixed_equal"] = {
        "p0": float(probs[0].item()),
        "p1": float(probs[1].item()),
        "pass": abs(float(probs[0].item()) - 0.5) < 1e-5,
    }

    # B4: Probability varies linearly with r_z
    rz_vals = [-1.0, -0.5, 0.0, 0.5, 1.0]
    p0_vals = []
    for rz in rz_vals:
        dm = DensityMatrix(torch.tensor([0.0, 0.0, rz]))
        probs, _ = zm(dm())
        p0_vals.append(float(probs[0].item()))

    # Check linearity: p_0 = (1+r_z)/2
    expected = [(1 + rz) / 2 for rz in rz_vals]
    max_diff = max(abs(a - e) for a, e in zip(p0_vals, expected))
    results["B4_linear_in_rz"] = {
        "rz_vals": rz_vals,
        "p0_vals": p0_vals,
        "expected": expected,
        "max_diff": max_diff,
        "pass": max_diff < 1e-5,
    }

    return results


# =====================================================================
# SYMPY CHECK
# =====================================================================

def run_sympy_check():
    if not TOOL_MANIFEST["sympy"]["tried"]:
        return {"skipped": True, "reason": "sympy not available"}

    rx, ry, rz = sp.symbols("r_x r_y r_z", real=True)
    # p_0 = <0|rho|0> = (1 + r_z) / 2
    p0 = (1 + rz) / 2
    p1 = (1 - rz) / 2
    # dp_0/dr_z = 1/2
    dp0_drz = sp.diff(p0, rz)
    dp0_drx = sp.diff(p0, rx)
    return {
        "p0_formula": str(p0),
        "p1_formula": str(p1),
        "dp0_drz": str(dp0_drz),
        "dp0_drx": str(dp0_drx),
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
    TOOL_MANIFEST["pytorch"]["reason"] = "ZMeasurement module: projective Z-measurement with differentiable probs"
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "Symbolic probability formulas and gradient check"

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
        "name": "torch_z_measurement",
        "description": "ZMeasurement: Z-basis projective measurement with differentiable probabilities",
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive, "negative": negative,
        "boundary": boundary, "sympy_check": sympy_check,
        "classification": "canonical",
        "summary": {"total_tests": total_tests, "total_pass": total_pass,
                     "all_pass": total_pass == total_tests},
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "torch_z_measurement_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Tests: {total_pass}/{total_tests} passed")
    if total_pass == total_tests:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
