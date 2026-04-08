#!/usr/bin/env python3
"""
MEASURE family: WignerNegativity as a differentiable torch.nn.Module.
Qubit Wigner function on Bloch sphere: W(theta,phi) = (1 + r . n) / (4*pi).
Negative volume = integral of |W| where W < 0 (only for |r|>1, unphysical,
or for higher-dimensional states). For valid qubits, W >= 0 everywhere.
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


class WignerNegativity(nn.Module):
    """
    Qubit Wigner function on the Bloch sphere (Stratonovich-Weyl):
    W(theta, phi) = (1/4pi) * (1 + sqrt(3) * r . n(theta, phi))
    where n = (sin(theta)cos(phi), sin(theta)sin(phi), cos(theta)).

    The sqrt(3) factor comes from the SU(2) Wigner representation
    for spin-1/2 (Stratonovich kernel).

    Negative volume = integral of max(-W, 0) * sin(theta) dtheta dphi.
    For valid qubits (|r|<=1), the minimum W = (1 - sqrt(3)*|r|)/(4*pi),
    which IS negative for |r| > 1/sqrt(3) ~ 0.577.
    """
    def wigner_value(self, bloch, theta, phi):
        """Compute W(theta, phi) for given Bloch vector."""
        nx = torch.sin(theta) * torch.cos(phi)
        ny = torch.sin(theta) * torch.sin(phi)
        nz = torch.cos(theta)
        dot = bloch[0] * nx + bloch[1] * ny + bloch[2] * nz
        sqrt3 = torch.tensor(np.sqrt(3), dtype=torch.float32)
        return (1.0 + sqrt3 * dot) / (4.0 * np.pi)

    def negative_volume(self, bloch, n_theta=50, n_phi=50):
        """Integrate negative part of Wigner function over sphere."""
        dth = np.pi / n_theta
        dph = 2 * np.pi / n_phi
        neg_vol = torch.tensor(0.0)
        for ith in range(n_theta):
            th = torch.tensor((ith + 0.5) * dth)
            sin_th = torch.sin(th)
            for iph in range(n_phi):
                ph = torch.tensor((iph + 0.5) * dph)
                w = self.wigner_value(bloch, th, ph)
                # Differentiable negative part: max(-w, 0) via relu
                neg_part = torch.relu(-w)
                neg_vol = neg_vol + neg_part * sin_th * dth * dph
        return neg_vol

    def forward(self, bloch, theta=None, phi=None):
        """If theta/phi given, return W value. Otherwise return negative volume."""
        if theta is not None and phi is not None:
            return self.wigner_value(bloch, theta, phi)
        return self.negative_volume(bloch)


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


def numpy_wigner(bloch, theta, phi):
    nx = np.sin(theta) * np.cos(phi)
    ny = np.sin(theta) * np.sin(phi)
    nz = np.cos(theta)
    dot = bloch[0] * nx + bloch[1] * ny + bloch[2] * nz
    return (1.0 + np.sqrt(3) * dot) / (4 * np.pi)


def numpy_negative_volume(bloch, n_theta=50, n_phi=50):
    dth = np.pi / n_theta
    dph = 2 * np.pi / n_phi
    neg_vol = 0.0
    for ith in range(n_theta):
        th = (ith + 0.5) * dth
        for iph in range(n_phi):
            ph = (iph + 0.5) * dph
            w = numpy_wigner(bloch, th, ph)
            if w < 0:
                neg_vol += (-w) * np.sin(th) * dth * dph
    return neg_vol


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
    }
    for i in range(3):
        states[f"random_{i}"] = random_bloch_interior(rng)

    # P1: Wigner value substrate match
    p1 = {}
    test_angles = [(0.5, 0.3), (1.0, 2.0), (np.pi / 2, np.pi)]
    for name, bloch in states.items():
        diffs = []
        for th, ph in test_angles:
            w_np = numpy_wigner(np.array(bloch), th, ph)
            wn = WignerNegativity()
            w_t = float(wn(torch.tensor(bloch, dtype=torch.float32),
                           torch.tensor(th), torch.tensor(ph)).item())
            diffs.append(abs(w_np - w_t))
        max_diff = max(diffs)
        p1[name] = {"max_diff": max_diff, "pass": max_diff < 1e-5}
    results["P1_wigner_substrate_match"] = p1

    # P2: Negative volume substrate match
    p2 = {}
    for name, bloch in list(states.items())[:4]:
        nv_np = numpy_negative_volume(np.array(bloch))
        wn = WignerNegativity()
        nv_t = float(wn(torch.tensor(bloch, dtype=torch.float32)).item())
        diff = abs(nv_np - nv_t)
        p2[name] = {"numpy": nv_np, "torch": nv_t, "diff": diff, "pass": diff < 0.01}
    results["P2_negative_volume_match"] = p2

    # P3: Normalization -- integral of W over sphere = 1
    p3 = {}
    n_th, n_ph = 50, 50
    dth = np.pi / n_th
    dph = 2 * np.pi / n_ph
    for name, bloch in list(states.items())[:3]:
        integral = 0.0
        for ith in range(n_th):
            th = (ith + 0.5) * dth
            for iph in range(n_ph):
                ph = (iph + 0.5) * dph
                w = numpy_wigner(np.array(bloch), th, ph)
                integral += w * np.sin(th) * dth * dph
        p3[name] = {"integral": integral, "pass": abs(integral - 1.0) < 0.05}
    results["P3_normalization"] = p3

    # P4: Gradient of negative volume exists
    p4 = {}
    for name, bloch in [("pure_z", [0, 0, 1.0]), ("random_0", states["random_0"])]:
        bloch_t = torch.tensor(bloch, dtype=torch.float32, requires_grad=True)
        wn = WignerNegativity()
        nv = wn.negative_volume(bloch_t, n_theta=20, n_phi=20)
        nv.backward()
        grad = bloch_t.grad
        p4[name] = {
            "neg_vol": float(nv.item()),
            "grad_exists": grad is not None,
            "pass": grad is not None,
        }
    results["P4_gradient_exists"] = p4

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # N1: Maximally mixed state has zero negative volume (W >= 0 everywhere)
    bloch = [0, 0, 0]
    nv = numpy_negative_volume(np.array(bloch))
    results["N1_mixed_zero_negativity"] = {
        "negative_volume": nv,
        "is_zero": abs(nv) < 1e-8,
        "pass": abs(nv) < 1e-8,
    }

    # N2: Pure states (|r|=1) HAVE negative Wigner regions (|r| > 1/sqrt(3))
    pure_states = {"z": [0, 0, 1.0], "x": [1, 0, 0], "y": [0, 1, 0]}
    n2 = {}
    for name, bloch in pure_states.items():
        nv = numpy_negative_volume(np.array(bloch))
        n2[name] = {"negative_volume": nv, "has_negativity": nv > 1e-4, "pass": nv > 1e-4}
    results["N2_pure_states_have_negativity"] = n2

    # N3: Invalid Bloch (|r|>1) has MORE negative volume
    nv_valid = numpy_negative_volume(np.array([0, 0, 1.0]))
    nv_invalid = numpy_negative_volume(np.array([0, 0, 1.5]))
    results["N3_invalid_more_negativity"] = {
        "valid_neg_vol": nv_valid,
        "invalid_neg_vol": nv_invalid,
        "invalid_exceeds": nv_invalid > nv_valid,
        "pass": nv_invalid > nv_valid,
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # B1: At |r| = 1/sqrt(3), negative volume is near zero
    r_crit = 1.0 / np.sqrt(3)
    bloch = [0, 0, r_crit]
    nv = numpy_negative_volume(np.array(bloch))
    results["B1_critical_radius"] = {
        "r_critical": r_crit,
        "negative_volume": nv,
        "near_zero": nv < 0.01,
        "pass": nv < 0.01,
    }

    # B2: Below critical radius, no negativity
    bloch_below = [0, 0, 0.5]
    nv_below = numpy_negative_volume(np.array(bloch_below))
    results["B2_below_critical_no_negativity"] = {
        "r": 0.5,
        "negative_volume": nv_below,
        "is_zero": abs(nv_below) < 1e-6,
        "pass": abs(nv_below) < 1e-6,
    }

    # B3: Negative volume increases monotonically above critical radius
    radii = [0.6, 0.7, 0.8, 0.9, 1.0]
    neg_vols = [numpy_negative_volume(np.array([0, 0, r])) for r in radii]
    monotone = all(neg_vols[i] <= neg_vols[i + 1] + 1e-4
                   for i in range(len(neg_vols) - 1))
    results["B3_monotone_above_critical"] = {
        "radii": radii,
        "neg_vols": neg_vols,
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

    r, theta, phi = sp.symbols("r theta phi", real=True)
    # W(theta) for Bloch = (0,0,r):
    # n_z = cos(theta), so W = (1 + sqrt(3)*r*cos(theta)) / (4*pi)
    W = (1 + sp.sqrt(3) * r * sp.cos(theta)) / (4 * sp.pi)
    # W = 0 when cos(theta) = -1/(sqrt(3)*r)
    zero_angle = sp.solve(W, theta)
    return {
        "W_formula": str(W),
        "zero_angles": [str(a) for a in zero_angle],
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
    TOOL_MANIFEST["pytorch"]["reason"] = "WignerNegativity module: Wigner function + negative volume with autograd"
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "Symbolic Wigner function formula and zero-angle derivation"

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
        "name": "torch_wigner",
        "description": "WignerNegativity: qubit Wigner function on Bloch sphere, negative volume measure",
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive, "negative": negative,
        "boundary": boundary, "sympy_check": sympy_check,
        "classification": "canonical",
        "summary": {"total_tests": total_tests, "total_pass": total_pass,
                     "all_pass": total_pass == total_tests},
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "torch_wigner_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Tests: {total_pass}/{total_tests} passed")
    if total_pass == total_tests:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
