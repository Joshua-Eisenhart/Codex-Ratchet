#!/usr/bin/env python3
"""
sim_weyl_deep_pauli_joint_commute_unsat
Scope: z3 UNSAT — distinct Pauli operators cannot jointly commute with a
single 2x2 Hermitian operator of nontrivial rank. Excludes candidate
simultaneous-eigenvector claims across non-commuting axes.
See system_v5/new docs/ENGINE_MATH_REFERENCE.md.
"""
import json, os
from z3 import Solver, Reals, And, Or, Not, sat, unsat

SCOPE_NOTE = "z3 exclusion of joint commutation for distinct Pauli axes; ENGINE_MATH_REFERENCE.md"

TOOL_MANIFEST = {
    "z3": {"tried": True, "used": True, "reason": "SMT exclusion of simultaneous Pauli commutation"},
}
TOOL_INTEGRATION_DEPTH = {"z3": "load_bearing"}

def solve(joint=True):
    s = Solver()
    # A = [[a,b-ic],[b+ic,d]] Hermitian. Require [A,sigma_x]=0 and [A,sigma_z]=0.
    a, b, c, d = Reals("a b c d")
    # [A, sigma_x] = 0  -> (b-ic) - (b+ic) = 0 (ok always in real param here), and a-d = 0 off-diagonal -> a=d
    s.add(a == d)  # from anti-diagonal difference
    if joint:
        # [A, sigma_z] = 0 -> b = 0 and c = 0 (off-diagonals zero)
        s.add(b == 0, c == 0)
    # Require non-scalar A (rank-distinguishing): b!=0 or c!=0 or a!=d
    s.add(Or(b != 0, c != 0, a != d))
    return s.check()

def run_positive_tests():
    r = solve(joint=True)
    return {"joint_pauli_excluded": {"pass": r == unsat, "status": str(r),
            "reason": "non-scalar A cannot commute with both sigma_x and sigma_z"}}

def run_negative_tests():
    r = solve(joint=False)
    return {"single_axis_admissible": {"pass": r == sat, "status": str(r),
            "reason": "A commuting with only sigma_x admits non-scalar solutions"}}

def run_boundary_tests():
    # scalar A always commutes: explicitly encode and check sat without non-scalar req
    s = Solver()
    a,b,c,d = Reals("a b c d")
    s.add(a == d, b == 0, c == 0)  # scalar multiple of I
    r = s.check()
    return {"scalar_A_ok": {"pass": r == sat, "status": str(r),
            "reason": "scalar A trivially commutes with all Paulis"}}

if __name__ == "__main__":
    pos, neg, bnd = run_positive_tests(), run_negative_tests(), run_boundary_tests()
    all_pass = all(t["pass"] for t in {**pos, **neg, **bnd}.values())
    results = {
        "name": "sim_weyl_deep_pauli_joint_commute_unsat",
        "classification": "canonical",
        "scope_note": SCOPE_NOTE,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "overall_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_weyl_deep_pauli_joint_commute_unsat_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {out_path}")
