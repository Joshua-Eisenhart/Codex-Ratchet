#!/usr/bin/env python3
"""
sim_pairwise_coupling_classical.py

Lane B classical baseline for CP^1 pairwise shell coupling.
Numpy + sympy only. No pytorch, no z3.

This is the classical counterpart to
sim_pure_lego_pairwise_shell_coupling_cp1.py (nonclassical / canonical).

Test: two CP^1 shells A and B. Each shell has a coherent-state
parameterization |psi(theta, phi)>. Pairwise coupling = product-state
inner product and reduced-state fidelity averaged over a discrete grid
of (theta_A, phi_A, theta_B, phi_B).

Positive: average fidelity > 0 on aligned shells.
Negative: antipodal coupling drops to ~0.
Boundary: identical shell pairs -> fidelity = 1.
"""

import json
import os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "excluded; classical baseline"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "no proof claim"},
    "cvc5": {"tried": False, "used": False, "reason": "no proof claim"},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "symbolic check of CP1 inner product"
    TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"
    HAVE_SYMPY = True
except ImportError:
    HAVE_SYMPY = False


def cp1_state(theta, phi):
    # |psi> = cos(theta/2)|0> + e^{i phi} sin(theta/2)|1>
    return np.array([np.cos(theta / 2), np.exp(1j * phi) * np.sin(theta / 2)], dtype=complex)


def fidelity(psi, chi):
    return float(np.abs(np.vdot(psi, chi))**2)


def grid(n=8):
    th = np.linspace(0, np.pi, n)
    ph = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return th, ph


def average_fidelity(offset_theta=0.0, offset_phi=0.0, n=8):
    th, ph = grid(n)
    total = 0.0
    count = 0
    for t in th:
        for p in ph:
            a = cp1_state(t, p)
            b = cp1_state(t + offset_theta, p + offset_phi)
            total += fidelity(a, b)
            count += 1
    return total / count


def run_positive_tests():
    r = {}
    r["aligned_avg_fidelity"] = average_fidelity(0.0, 0.0)
    r["small_offset_avg_fidelity"] = average_fidelity(0.1, 0.1)
    r["pass"] = r["aligned_avg_fidelity"] > 0.99 and r["small_offset_avg_fidelity"] > 0.5
    # sympy symbolic cross check: |<psi|psi>|^2 = 1
    if HAVE_SYMPY:
        th, ph = sp.symbols('theta phi', real=True)
        c = sp.cos(th/2)
        s = sp.sin(th/2) * sp.exp(sp.I * ph)
        norm_sq = sp.simplify(sp.conjugate(c)*c + sp.conjugate(s)*s)
        r["symbolic_norm"] = str(norm_sq)
        r["symbolic_norm_is_one"] = bool(sp.simplify(norm_sq - 1) == 0)
        r["pass"] = r["pass"] and r["symbolic_norm_is_one"]
    return r


def run_negative_tests():
    r = {}
    # antipodal: offset theta by pi -> orthogonal on each pair -> avg fidelity = 0
    r["antipodal_avg_fidelity"] = average_fidelity(np.pi, 0.0)
    # large offset phi with theta=pi/2 moves pairs apart on equator
    r["equator_phi_pi_fidelity"] = average_fidelity(0.0, np.pi)
    r["pass"] = r["antipodal_avg_fidelity"] < 1e-10 and r["equator_phi_pi_fidelity"] < 0.9
    return r


def run_boundary_tests():
    r = {}
    # identical shells across whole grid -> fidelity == 1
    f = average_fidelity(0.0, 0.0, n=16)
    r["identical_fidelity"] = f
    r["identical_is_one"] = abs(f - 1.0) < 1e-12
    # minimal grid
    r["n2_aligned"] = average_fidelity(0.0, 0.0, n=2)
    # numerical stability at pole
    psi_pole = cp1_state(0.0, 0.7)
    r["pole_is_ground"] = bool(np.allclose(psi_pole, np.array([1.0, 0.0])))
    r["pass"] = r["identical_is_one"] and r["pole_is_ground"]
    return r


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    results = {
        "name": "pairwise_coupling_classical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "classification": "classical_baseline",
        "all_pass": bool(pos.get("pass") and neg.get("pass") and bnd.get("pass")),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "pairwise_coupling_classical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"all_pass={results['all_pass']}")
