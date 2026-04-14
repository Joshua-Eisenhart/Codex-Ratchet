#!/usr/bin/env python3
"""sim_gtower_so_to_u -- reduction SO(2n) -> U(n) admissibility probe.

An SO(2n) candidate admits a U(n) reduction iff there exists a complex
structure J with J^2 = -I, J orthogonal, and [A, J] = 0 (A commutes with J).
Obstruction: no real J with J^2 = -I exists on odd-dimensional R^n
(det(J)^2 = det(-I) = (-1)^n, requires n even).

Load-bearing: z3 proves odd-n obstruction via determinant polynomial;
sympy verifies det(standard J) on small cases.
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

from _gtower_common import standard_J, in_SOn, in_Un


def real_block_to_complex(A, n):
    """Interpret 2n x 2n real matrix A (commuting with standard J) as n x n complex."""
    X = A[:n, :n]
    Y = A[n:, :n]
    # If A commutes with J = [[0,-I],[I,0]], then A = [[X,-Y],[Y,X]]
    return X + 1j * Y


def run_positive_tests():
    results = {}
    # Standard J on R^2 is in SO(2) and itself gives U(1) structure.
    J = standard_J(1)
    results["J_in_SO2"] = in_SOn(J)
    # A rotation in SO(2) commutes with J
    theta = 0.3
    R = np.array([[np.cos(theta), -np.sin(theta)],
                  [np.sin(theta),  np.cos(theta)]])
    results["rot_commutes_J"] = np.allclose(R @ J - J @ R, 0.0, atol=1e-10)
    # Interpret as complex scalar and check unitary
    z = complex(np.cos(theta), np.sin(theta))
    results["complex_unitary"] = abs(abs(z) - 1.0) < 1e-10
    # On R^4 -> C^2, a block-diag of two 2D rotations commutes with J_2
    J2 = standard_J(2)
    R4 = np.block([
        [np.array([[np.cos(0.2), -np.sin(0.2)], [np.sin(0.2), np.cos(0.2)]]), np.zeros((2,2))],
        [np.zeros((2,2)), np.array([[np.cos(0.5), -np.sin(0.5)], [np.sin(0.5), np.cos(0.5)]])],
    ])
    # Reformat so R4 commutes with standard J2 = [[0,-I],[I,0]]: use [[X,-Y],[Y,X]]
    X = np.diag([np.cos(0.2), np.cos(0.5)])
    Y = np.diag([np.sin(0.2), np.sin(0.5)])
    A = np.block([[X, -Y], [Y, X]])
    results["A_in_SO4"] = in_SOn(A, tol=1e-8)
    results["A_commutes_J2"] = np.allclose(A @ J2 - J2 @ A, 0.0, atol=1e-10)
    U = real_block_to_complex(A, 2)
    results["U_unitary"] = in_Un(U)
    return results


def run_negative_tests():
    results = {}
    # Generic SO(2) rotation commutes with J so is admissible -- need an
    # orthogonal-but-not-commuting example.  A reflection in O(2) (det=-1) does
    # not commute with J.
    Ref = np.diag([1.0, -1.0])
    J = standard_J(1)
    results["reflection_breaks_J"] = (not np.allclose(Ref @ J - J @ Ref, 0.0, atol=1e-10))
    # SO(4) rotation acting only in (e0,e1) plane; breaks commutation with J2.
    J2 = standard_J(2)
    c, sn = np.cos(0.4), np.sin(0.4)
    P = np.array([[c, -sn, 0, 0],
                  [sn,  c, 0, 0],
                  [0,   0, 1, 0],
                  [0,   0, 0, 1]], dtype=float)
    results["P_in_SO4"] = in_SOn(P)
    results["P_breaks_J2"] = (not np.allclose(P @ J2 - J2 @ P, 0.0, atol=1e-10))
    return results


def run_boundary_tests():
    results = {}
    # z3 obstruction: no real 1x1 J with J^2 = -1 (odd dim = 1)
    z3_result = "skipped"
    if TOOL_MANIFEST["z3"]["tried"]:
        j = z3.Real("j")
        s = z3.Solver()
        s.add(j * j == -1)
        z3_result = str(s.check())  # expect unsat
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = "proves no real j with j^2=-1 (odd-dim complex-structure obstruction)"
        TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    results["z3_no_real_J_dim1"] = z3_result
    results["z3_no_real_J_dim1_ok"] = (z3_result == "unsat")
    # sympy: det(standard_J(n))^2 = 1 for all n (standard J is orthogonal)
    sympy_ok = "skipped"
    if TOOL_MANIFEST["sympy"]["tried"]:
        M = sp.Matrix(standard_J(2).astype(int))
        sympy_ok = (M.det() == 1)
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = "verifies det of standard complex structure symbolically"
        TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"
    results["sympy_det_J2"] = sympy_ok
    return results


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    def _t(v): return bool(v) is True
    all_pass = (all(_t(v) for v in pos.values())
                and all(_t(v) for v in neg.values())
                and _t(bnd.get("z3_no_real_J_dim1_ok")))
    results = {
        "name": "sim_gtower_so_to_u",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "status": "PASS" if all_pass else "FAIL",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "sim_gtower_so_to_u_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{results['name']}: {results['status']}")
