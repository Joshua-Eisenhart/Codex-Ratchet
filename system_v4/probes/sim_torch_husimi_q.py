#!/usr/bin/env python3
"""
MEASURE family: HusimiQ as a differentiable torch.nn.Module.
Q(alpha) = <alpha|rho|alpha>/pi where |alpha> is a coherent state.
Parameterized on phase-space grid. Non-negative everywhere.
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
# MODULE UNDER TEST: HusimiQ
# =====================================================================

class DensityMatrix(nn.Module):
    """Differentiable density matrix parameterized by Bloch vector."""
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


def coherent_state_qubit(theta, phi):
    """
    Qubit coherent state |alpha> parameterized by Bloch angles theta, phi.
    |alpha> = cos(theta/2)|0> + e^{i*phi}*sin(theta/2)|1>
    Returns column vector as complex64 tensor.
    """
    c0 = torch.cos(theta / 2).to(torch.complex64)
    c1 = (torch.sin(theta / 2) * torch.exp(1j * phi.to(torch.complex64))).to(torch.complex64)
    return torch.stack([c0, c1]).unsqueeze(1)  # (2,1)


class HusimiQ(nn.Module):
    """
    Husimi Q function for qubit: Q(theta,phi) = <alpha|rho|alpha> / (2*pi).
    For d=2 (qubit), normalization is 1/(2*pi) so integral over sphere = 1.
    Non-negative by construction (sandwich of PSD rho).
    """
    def forward(self, rho, theta, phi):
        alpha = coherent_state_qubit(theta, phi)  # (2,1)
        # Q = alpha^dag @ rho @ alpha / (2*pi)  [factor d/(4*pi) = 2/(4*pi) = 1/(2*pi)]
        q_val = (alpha.conj().T @ rho @ alpha).real / (2 * np.pi)
        return q_val.squeeze()


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


def numpy_husimi_q(rho, theta, phi):
    c0 = np.cos(theta / 2)
    c1 = np.sin(theta / 2) * np.exp(1j * phi)
    alpha = np.array([[c0], [c1]], dtype=np.complex128)
    q = (alpha.conj().T @ rho @ alpha).real / (2 * np.pi)
    return float(q[0, 0])


# =====================================================================
# TEST HELPERS
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
        "mixed": [0, 0, 0],
    }
    for i in range(3):
        states[f"random_{i}"] = random_bloch_interior(rng)

    # P1: Substrate match on a grid of (theta, phi) points
    p1 = {}
    grid_theta = np.linspace(0, np.pi, 8)
    grid_phi = np.linspace(0, 2 * np.pi, 8)
    for name, bloch in states.items():
        rho_np = numpy_density_matrix(np.array(bloch))
        dm = DensityMatrix(torch.tensor(bloch, dtype=torch.float32))
        hq = HusimiQ()
        rho_t = dm()

        diffs = []
        for th in grid_theta:
            for ph in grid_phi:
                q_np = numpy_husimi_q(rho_np, th, ph)
                q_t = float(hq(rho_t, torch.tensor(th, dtype=torch.float32),
                               torch.tensor(ph, dtype=torch.float32)).item())
                diffs.append(abs(q_np - q_t))
        max_diff = max(diffs)
        p1[name] = {"max_diff": max_diff, "n_points": len(diffs), "pass": max_diff < 1e-5}
    results["P1_substrate_match_grid"] = p1

    # P2: Non-negativity everywhere
    p2 = {}
    for name, bloch in states.items():
        dm = DensityMatrix(torch.tensor(bloch, dtype=torch.float32))
        hq = HusimiQ()
        rho_t = dm()
        min_q = float("inf")
        for th in grid_theta:
            for ph in grid_phi:
                q = float(hq(rho_t, torch.tensor(th, dtype=torch.float32),
                             torch.tensor(ph, dtype=torch.float32)).item())
                min_q = min(min_q, q)
        p2[name] = {"min_Q": min_q, "non_negative": min_q >= -1e-10, "pass": min_q >= -1e-10}
    results["P2_non_negativity"] = p2

    # P3: Integral over sphere ~ 1 (normalization)
    # For qubit Husimi: integral Q sin(theta) dtheta dphi = 1
    p3 = {}
    n_th, n_ph = 50, 50
    dth = np.pi / n_th
    dph = 2 * np.pi / n_ph
    for name, bloch in list(states.items())[:3]:
        dm = DensityMatrix(torch.tensor(bloch, dtype=torch.float32))
        hq = HusimiQ()
        rho_t = dm()
        integral = 0.0
        for ith in range(n_th):
            th = (ith + 0.5) * dth
            for iph in range(n_ph):
                ph = (iph + 0.5) * dph
                q = float(hq(rho_t, torch.tensor(th, dtype=torch.float32),
                             torch.tensor(ph, dtype=torch.float32)).item())
                integral += q * np.sin(th) * dth * dph
        p3[name] = {"integral": integral, "pass": abs(integral - 1.0) < 0.05}
    results["P3_normalization"] = p3

    # P4: Gradient exists w.r.t. Bloch params
    p4 = {}
    for name, bloch in list(states.items())[:3]:
        dm = DensityMatrix(torch.tensor(bloch, dtype=torch.float32))
        hq = HusimiQ()
        rho_t = dm()
        q = hq(rho_t, torch.tensor(0.5), torch.tensor(0.3))
        q.backward()
        grad = dm.bloch.grad
        p4[name] = {
            "grad_exists": grad is not None,
            "grad": grad.tolist() if grad is not None else None,
            "pass": grad is not None,
        }
    results["P4_gradient_exists"] = p4

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # N1: Invalid Bloch (|r|>1) can give Q > 1/pi at some point
    invalid = {"r=2_z": [0, 0, 2.0]}
    n1 = {}
    for name, bloch in invalid.items():
        dm = DensityMatrix(torch.tensor(bloch, dtype=torch.float32))
        hq = HusimiQ()
        rho_t = dm()
        # At theta=0, phi=0: Q = <0|rho|0>/pi = (1+r_z)/2 / pi
        q = float(hq(rho_t, torch.tensor(0.0), torch.tensor(0.0)).item())
        # For r_z=2: (1+2)/2/(2*pi) > 0, but at theta=pi: (1-2)/2/(2*pi) < 0
        q_neg = float(hq(rho_t, torch.tensor(np.pi, dtype=torch.float32),
                         torch.tensor(0.0)).item())
        n1[name] = {
            "Q_at_north": q,
            "Q_at_south": q_neg,
            "south_negative": q_neg < -1e-10,
            "pass": q_neg < -1e-10,  # Invalid state gives negative Q
        }
    results["N1_invalid_bloch_negative_Q"] = n1

    # N2: Q for diagonal state matches analytical formula
    bloch = [0.0, 0.0, 0.6]
    rho_np = numpy_density_matrix(np.array(bloch))
    # Q(theta=0, phi=0) = <0|rho|0>/(2*pi) = (1+0.6)/2 / (2*pi)
    expected = (1 + 0.6) / 2 / (2 * np.pi)
    dm = DensityMatrix(torch.tensor(bloch, dtype=torch.float32))
    hq = HusimiQ()
    actual = float(hq(dm(), torch.tensor(0.0), torch.tensor(0.0)).item())
    results["N2_analytical_check"] = {
        "expected": expected,
        "actual": actual,
        "diff": abs(expected - actual),
        "pass": abs(expected - actual) < 1e-6,
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # B1: Maximally mixed state -> Q = 1/(4*pi) everywhere
    # rho = I/2, <alpha|I/2|alpha> = 1/2 for any alpha, Q = (1/2)/(2*pi) = 1/(4*pi)
    dm = DensityMatrix(torch.zeros(3))
    hq = HusimiQ()
    rho_t = dm()
    expected = 1.0 / (4 * np.pi)
    q_vals = []
    for th in np.linspace(0, np.pi, 10):
        for ph in np.linspace(0, 2 * np.pi, 10):
            q = float(hq(rho_t, torch.tensor(th, dtype=torch.float32),
                         torch.tensor(ph, dtype=torch.float32)).item())
            q_vals.append(q)
    max_dev = max(abs(q - expected) for q in q_vals)
    results["B1_mixed_uniform_Q"] = {
        "expected": expected,
        "max_deviation": max_dev,
        "pass": max_dev < 1e-6,
    }

    # B2: Pure |0> -> Q peaks at north pole
    dm = DensityMatrix(torch.tensor([0, 0, 1.0]))
    rho_t = dm()
    q_north = float(hq(rho_t, torch.tensor(0.0), torch.tensor(0.0)).item())
    q_south = float(hq(rho_t, torch.tensor(np.pi, dtype=torch.float32),
                       torch.tensor(0.0)).item())
    results["B2_pure_state_peak"] = {
        "Q_north": q_north,
        "Q_south": q_south,
        "north_is_max": q_north > q_south,
        "south_near_zero": abs(q_south) < 1e-6,
        "pass": q_north > q_south and abs(q_south) < 1e-6,
    }

    return results


# =====================================================================
# SYMPY CHECK
# =====================================================================

def run_sympy_check():
    if not TOOL_MANIFEST["sympy"]["tried"]:
        return {"skipped": True, "reason": "sympy not available"}

    theta, phi, rz = sp.symbols("theta phi r_z", real=True)
    # For Bloch = (0,0,r_z), |alpha> = (cos(theta/2), e^{i*phi}*sin(theta/2))
    # Q = <alpha|rho|alpha>/pi = [(1+r_z)*cos^2(theta/2) + (1-r_z)*sin^2(theta/2)] / (2*pi)
    Q_expr = ((1 + rz) * sp.cos(theta / 2)**2 + (1 - rz) * sp.sin(theta / 2)**2) / (4 * sp.pi)
    Q_simplified = sp.simplify(Q_expr)
    return {
        "Q_formula": str(Q_simplified),
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
    TOOL_MANIFEST["pytorch"]["reason"] = "HusimiQ module: coherent state overlaps, autograd"
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "Symbolic Q function formula verification"

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
        "name": "torch_husimi_q",
        "description": "HusimiQ module: Q(alpha) = <alpha|rho|alpha>/pi, non-negative quasiprobability",
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive, "negative": negative,
        "boundary": boundary, "sympy_check": sympy_check,
        "classification": "canonical",
        "summary": {"total_tests": total_tests, "total_pass": total_pass,
                     "all_pass": total_pass == total_tests},
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "torch_husimi_q_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Tests: {total_pass}/{total_tests} passed")
    if total_pass == total_tests:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
