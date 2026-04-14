#!/usr/bin/env python3
"""Axis 1 x Axis 4 coupling: curvature branch x loop-order family.
sympy symbolic commutator of curvature-signed generator and loop permutation.
scope_note: system_v5/new docs/AXIS_AND_ENTROPY_REFERENCE.md (Axes 1, 4).
Exclusion: coupling excludes commutation of curvature reversal with loop-order permutation.
"""
import json, os
import sympy as sp

TOOL_MANIFEST = {"sympy": {"tried": True, "used": True,
    "reason": "symbolic commutator on curvature-signed matrix algebra; load-bearing"}}
TOOL_INTEGRATION_DEPTH = {"sympy": "load_bearing"}

def run_positive_tests():
    k, t = sp.symbols('k t', real=True)
    # curvature-signed generator
    A = sp.Matrix([[0, -k], [k, 0]])
    # loop-permutation generator
    B = sp.Matrix([[t, 1], [0, -t]])
    C = sp.simplify(A*B - B*A)
    # substitute generic values
    val = sp.simplify(C.subs({k: sp.Rational(1,2), t: sp.Rational(1,3)}).norm())
    return {"commutator": str(C), "sample_norm": str(val),
            "coupling_detected": not val.equals(0)}

def run_negative_tests():
    k = sp.symbols('k', real=True)
    A = sp.Matrix([[0, -k], [k, 0]])
    I = sp.eye(2)
    C = sp.simplify(A*I - I*A)
    return {"identity_commutes": C.equals(sp.zeros(2,2))}

def run_boundary_tests():
    k, t = sp.symbols('k t', real=True)
    A = sp.Matrix([[0, -k], [k, 0]])
    B = sp.Matrix([[t, 1], [0, -t]])
    C = sp.simplify((A*B - B*A).subs(k, 0))
    return {"zero_curvature_commutes": C.equals(sp.zeros(2,2))}

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = bool(pos["coupling_detected"]) and all(neg.values()) and all(bnd.values())
    results = {"name": "axis_couple_1_4_curvature_x_loop",
               "classification": "canonical",
               "scope_note": "system_v5/new docs/AXIS_AND_ENTROPY_REFERENCE.md (Axes 1, 4)",
               "exclusion_claim": "coupling excludes commutation of Axis 1 curvature reversal with Axis 4 loop-order",
               "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
               "positive": pos, "negative": neg, "boundary": bnd, "pass": all_pass}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, "axis_couple_1_4_curvature_x_loop_results.json")
    with open(p, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {p}")
