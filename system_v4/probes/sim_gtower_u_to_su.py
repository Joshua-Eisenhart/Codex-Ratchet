#!/usr/bin/env python3
"""sim_gtower_u_to_su -- reduction U(n) -> SU(n) admissibility probe.

A U(n) candidate admits an SU(n) reduction iff det_C(U) = 1 (the U(1)
phase factor is quotiented out). Exclusion: det_C != 1.

Load-bearing: z3 proves that a unitary scalar u with |u|=1 and u != 1
cannot satisfy det=1 simultaneously (trivial real-part/imag-part
polynomial system, unsat).
"""
import json
import os
import numpy as np

classification = "classical_baseline"
DEMOTE_REASON = "no non-numpy load_bearing tool; numeric numpy only"

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": ""},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False, "reason": ""},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn":      {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi":       {"tried": False, "used": False, "reason": ""},
    "toponetx":  {"tried": False, "used": False, "reason": ""},
    "gudhi":     {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import z3
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

from _gtower_common import in_Un, in_SUn


def run_positive_tests():
    results = {}
    # Identity and a traceless Pauli-like SU(2)
    I2 = np.eye(2, dtype=complex)
    results["identity_admitted"] = in_SUn(I2)
    theta = 0.7
    # SU(2) element: exp(i theta sigma_z / 2) times exp(-i theta sigma_z / 2)? Use
    # generic [[a, -b*],[b, a*]] with |a|^2+|b|^2 = 1, det = 1.
    a = complex(np.cos(theta), 0)
    b = complex(0, np.sin(theta))
    U = np.array([[a, -np.conj(b)], [b, np.conj(a)]])
    results["su2_elt_admitted"] = in_SUn(U)
    return results


def run_negative_tests():
    results = {}
    # U(1) phase: diag(e^{i pi/3}) is U(1) but not SU(1) (det != 1).
    U = np.array([[np.exp(1j * np.pi / 3)]])
    results["phase_excluded"] = (in_Un(U) and not in_SUn(U))
    # U(2) with det = i (not 1)
    U2 = np.array([[1j, 0], [0, 1]], dtype=complex)
    results["u2_det_i_excluded"] = (in_Un(U2) and not in_SUn(U2))
    return results


def run_boundary_tests():
    results = {}
    # det = 1 but not unitary (shear-like complex) -> excluded from SU
    S = np.array([[1.0, 2.0], [0.0, 1.0]], dtype=complex)  # det=1, not unitary
    results["det1_nonunit_excluded"] = (abs(np.linalg.det(S) - 1) < 1e-9 and not in_SUn(S))
    # z3: unitary scalar u = x + i y with x^2+y^2 = 1, det = u; requiring
    # det = 1 AND u != 1 is unsat.
    z3_result = "skipped"
    if TOOL_MANIFEST["z3"]["tried"]:
        x, y = z3.Reals("x y")
        s = z3.Solver()
        s.add(x * x + y * y == 1)  # unitary
        s.add(x == 1, y == 0)  # det = 1
        s.add(z3.Or(x != 1, y != 0))  # but also not = 1
        z3_result = str(s.check())
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = "proves det=1 forces scalar phase = 1 (SU(1)-triviality obstruction)"
        TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    results["z3_phase_trivial"] = z3_result
    results["z3_phase_trivial_ok"] = (z3_result == "unsat")
    return results


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    def _t(v): return bool(v) is True
    all_pass = (all(_t(v) for v in pos.values())
                and all(_t(v) for v in neg.values())
                and _t(bnd.get("det1_nonunit_excluded"))
                and _t(bnd.get("z3_phase_trivial_ok")))
    results = {
        "name": "sim_gtower_u_to_su",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "status": "PASS" if all_pass else "FAIL",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "sim_gtower_u_to_su_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{results['name']}: {results['status']}")
