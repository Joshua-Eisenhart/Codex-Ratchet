#!/usr/bin/env python3
"""
sim_weyl_deep_left_right_projector_unsat_mix
Scope: z3 UNSAT proof that left and right Weyl projectors cannot simultaneously
admit a non-trivial shared eigenvector. Candidate-admissibility test: excludes
chirality-mixed survivors under P_L + P_R = I, P_L P_R = 0.
See system_v5/new docs/ENGINE_MATH_REFERENCE.md.
"""
import json, os
from z3 import Solver, Reals, And, Or, Not, sat, unsat

SCOPE_NOTE = "Weyl P_L/P_R orthogonal projector exclusion; see ENGINE_MATH_REFERENCE.md"

TOOL_MANIFEST = {
    "z3": {"tried": True, "used": True, "reason": "UNSAT proof of forbidden chirality-mixed eigenvector"},
    "pytorch": {"tried": False, "used": False, "reason": "not load-bearing; z3 owns proof"},
    "sympy": {"tried": False, "used": False, "reason": "numeric unneeded for structural UNSAT"},
    "clifford": {"tried": False, "used": False, "reason": "Pauli algebra encoded in z3 constraints"},
}
TOOL_INTEGRATION_DEPTH = {"z3": "load_bearing"}

def _solve_mix(alpha, beta):
    # spinor (a,b); require P_L v = alpha v and P_R v = beta v simultaneously.
    # P_L = diag(1,0), P_R = diag(0,1). Shared nonzero eigenvector requires
    # a = alpha a, b = 0 and a = 0, b = beta b with (a,b) != 0.
    s = Solver()
    a, b = Reals("a b")
    s.add(a*(1-alpha) == 0, b*(0-alpha) == 0)   # P_L v = alpha v
    s.add(a*(0-beta) == 0, b*(1-beta) == 0)     # P_R v = beta v
    s.add(Or(a != 0, b != 0))
    return s.check()

def run_positive_tests():
    # exclude mixed case: both eigenvalues 1
    r = _solve_mix(1, 1)
    return {"mixed_both_one_excluded": {"pass": r == unsat, "status": str(r),
            "reason": "P_L and P_R joint eigenvalue 1 has no common nonzero eigenvector"}}

def run_negative_tests():
    # pure L chirality admissible: alpha=1, beta=0
    r = _solve_mix(1, 0)
    return {"pure_left_admissible": {"pass": r == sat, "status": str(r),
            "reason": "pure left eigenvector survives"}}

def run_boundary_tests():
    # boundary: both zero -> requires v=0; should be unsat under v!=0
    r = _solve_mix(0, 0)
    return {"both_zero_excluded": {"pass": r == unsat, "status": str(r),
            "reason": "zero eigenvalue pair excludes nonzero spinor"}}

if __name__ == "__main__":
    pos, neg, bnd = run_positive_tests(), run_negative_tests(), run_boundary_tests()
    all_pass = all(t["pass"] for t in {**pos, **neg, **bnd}.values())
    results = {
        "name": "sim_weyl_deep_left_right_projector_unsat_mix",
        "classification": "canonical",
        "scope_note": SCOPE_NOTE,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "overall_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_weyl_deep_left_right_projector_unsat_mix_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {out_path}")
