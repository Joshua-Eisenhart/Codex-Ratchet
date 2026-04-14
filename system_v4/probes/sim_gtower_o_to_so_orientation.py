#!/usr/bin/env python3
"""sim_gtower_o_to_so_orientation -- orientation (det=+1) admissibility.

Scope note: see system_v5/new docs/LADDERS_FENCES_ADMISSION_REFERENCE.md
(O(n) -> SO(n) fence is the det=+1 subgroup constraint).

Candidate in O(n) admitted to SO(n) iff det = +1. This sim uses sympy to
exhibit the orientation bifurcation symbolically and z3 to prove that
'orthogonal AND det notin {-1,+1}' is UNSAT (load-bearing).
"""
import json, os
import numpy as np

classification = "canonical"

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

from _gtower_common import in_On, in_SOn


def run_positive_tests():
    r = {}
    th = sp.symbols("theta", real=True)
    R = sp.Matrix([[sp.cos(th), -sp.sin(th)], [sp.sin(th), sp.cos(th)]])
    det = sp.simplify(R.det())
    r["sympy_rot_det_plus1"] = (det == 1)
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "symbolic det of rotation = +1 across all theta"
    TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"
    r["numeric_rot_in_SO"] = in_SOn(np.array([[0, -1], [1, 0]], dtype=float))
    return r


def run_negative_tests():
    r = {}
    Ref = sp.Matrix([[1, 0], [0, -1]])
    r["reflection_det_minus1"] = (Ref.det() == -1)
    r["reflection_excluded_from_SO"] = (in_On(np.diag([1.0, -1.0])) and
                                        not in_SOn(np.diag([1.0, -1.0])))
    return r


def run_boundary_tests():
    r = {}
    # z3 load-bearing: no orthogonal 2x2 has det != +/-1
    z3_res = "skipped"
    if TOOL_MANIFEST["z3"]["tried"]:
        a, b, c, d, t = z3.Reals("a b c d t")
        s = z3.Solver()
        s.add(a*a + c*c == 1, b*b + d*d == 1, a*b + c*d == 0)
        s.add(a*d - b*c == t)
        s.add(t != 1, t != -1)
        z3_res = str(s.check())
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = "proves orthogonal det in {-1,+1}; orientation fence is exhaustive"
        TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    r["z3_orientation_exhaustive"] = z3_res
    r["z3_ok"] = (z3_res == "unsat")
    # boundary: near-identity perturbation still admitted
    eps = 1e-10
    M = np.array([[np.cos(eps), -np.sin(eps)], [np.sin(eps), np.cos(eps)]])
    r["near_identity_admitted"] = in_SOn(M)
    return r


if __name__ == "__main__":
    pos, neg, bnd = run_positive_tests(), run_negative_tests(), run_boundary_tests()
    def _t(v): return bool(v) is True
    all_pass = (all(_t(v) for v in pos.values())
                and all(_t(v) for v in neg.values())
                and _t(bnd.get("z3_ok")) and _t(bnd.get("near_identity_admitted")))
    results = {
        "name": "sim_gtower_o_to_so_orientation",
        "classification": "canonical",
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md: O->SO orientation fence",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "status": "PASS" if all_pass else "FAIL",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "sim_gtower_o_to_so_orientation_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{results['name']}: {results['status']}")
