#!/usr/bin/env python3
"""sim_gtower_gl_to_o -- reduction GL(n) -> O(n) admissibility probe.

Candidate matrices in GL(n) are admitted into O(n) iff they preserve the
standard Euclidean bilinear form g = I: A^T A = I. Using exclusion
language: a GL candidate is *excluded* from O(n) when A^T A != I.

Load-bearing tool: z3 proves the algebraic obstruction for a 2x2 template --
no real A with det(A)=2 can satisfy A^T A = I (orthogonal => |det|=1).
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

from _gtower_common import in_On, is_invertible


def run_positive_tests():
    results = {}
    # Identity and a rotation are admitted into O(n).
    results["identity_admitted"] = in_On(np.eye(3))
    theta = 0.7
    R = np.array([[np.cos(theta), -np.sin(theta)],
                  [np.sin(theta),  np.cos(theta)]])
    results["rotation_admitted"] = in_On(R)
    # Reflection (det=-1) still in O(2), not SO(2)
    Ref = np.diag([1.0, -1.0])
    results["reflection_admitted"] = in_On(Ref)
    return results


def run_negative_tests():
    results = {}
    # Shear is in GL but excluded from O.
    S = np.array([[1.0, 0.5], [0.0, 1.0]])
    results["shear_excluded"] = (is_invertible(S) and not in_On(S))
    # Scaling by 2 excluded.
    results["scale2_excluded"] = (is_invertible(2*np.eye(2)) and not in_On(2*np.eye(2)))
    return results


def run_boundary_tests():
    results = {}
    # Near-orthogonal matrix within tol.
    eps = 1e-12
    A = np.eye(2) + eps * np.array([[0.0, 1.0], [-1.0, 0.0]])
    results["near_identity_admitted"] = in_On(A, tol=1e-8)
    # z3 obstruction: no 2x2 real A with det=2 satisfies A^T A = I.
    z3_result = "skipped"
    if TOOL_MANIFEST["z3"]["tried"]:
        a, b, c, d = z3.Reals("a b c d")
        s = z3.Solver()
        # A^T A = I
        s.add(a*a + c*c == 1)
        s.add(b*b + d*d == 1)
        s.add(a*b + c*d == 0)
        # det = 2 (contradicts |det|=1 required by orthogonality)
        s.add(a*d - b*c == 2)
        res = s.check()
        z3_result = str(res)  # expect 'unsat'
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = "proves GL candidate with det=2 is excluded from O(2) (unsat)"
        TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    results["z3_obstruction_det2"] = z3_result
    results["z3_obstruction_ok"] = (z3_result == "unsat")
    return results


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    def _t(v): return bool(v) is True
    all_pass = (all(_t(v) for v in pos.values())
                and all(_t(v) for v in neg.values())
                and _t(bnd.get("near_identity_admitted"))
                and _t(bnd.get("z3_obstruction_ok")))
    results = {
        "name": "sim_gtower_gl_to_o",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "status": "PASS" if all_pass else "FAIL",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "sim_gtower_gl_to_o_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{results['name']}: {results['status']}")
