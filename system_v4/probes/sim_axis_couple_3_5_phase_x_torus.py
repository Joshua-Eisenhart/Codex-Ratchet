#!/usr/bin/env python3
"""Axis 3 x Axis 5 coupling: phase (fiber vs lifted-base loop) x operator family (dephasing vs rotation).
scope_note: system_v5/new docs/AXIS_AND_ENTROPY_REFERENCE.md (Axes 3, 5).
Exclusion: coupling excludes phase invariance under operator-family swap.
"""
import json, os
import sympy as sp

TOOL_MANIFEST = {"sympy": {"tried": True, "used": True,
    "reason": "symbolic commutator of dephasing and rotation on fibered phase loop is load-bearing"}}
TOOL_INTEGRATION_DEPTH = {"sympy": "load_bearing"}

def run_positive_tests():
    theta, phi, alpha = sp.symbols('theta phi alpha', real=True)
    R = sp.Matrix([[sp.cos(theta), -sp.sin(theta)], [sp.sin(theta), sp.cos(theta)]])
    D = sp.diag(sp.exp(sp.I*alpha), sp.exp(-sp.I*alpha))
    fiber = sp.Matrix([sp.cos(phi), sp.sin(phi)])
    a = R * (D * fiber)
    b = D * (R * fiber)
    diff = sp.simplify((a - b).norm())
    nonzero = sp.simplify(diff.subs({theta: sp.Rational(1,3), phi: sp.Rational(1,5), alpha: sp.Rational(2,7)}))
    return {"commutator_symbolic_nonzero": not nonzero.equals(0),
            "sample_value": str(nonzero),
            "coupling_detected": not nonzero.equals(0)}

def run_negative_tests():
    theta, phi = sp.symbols('theta phi', real=True)
    R = sp.Matrix([[sp.cos(theta), -sp.sin(theta)], [sp.sin(theta), sp.cos(theta)]])
    I = sp.eye(2)
    fiber = sp.Matrix([sp.cos(phi), sp.sin(phi)])
    diff = sp.simplify((R*(I*fiber) - I*(R*fiber)).norm())
    return {"identity_commutes": diff.equals(0)}

def run_boundary_tests():
    theta, phi, alpha = sp.symbols('theta phi alpha', real=True)
    R = sp.Matrix([[sp.cos(theta), -sp.sin(theta)], [sp.sin(theta), sp.cos(theta)]])
    D = sp.diag(sp.exp(sp.I*alpha), sp.exp(-sp.I*alpha))
    fiber = sp.Matrix([sp.cos(phi), sp.sin(phi)])
    diff = sp.simplify(((R*(D*fiber) - D*(R*fiber)).subs(alpha, 0)).norm())
    return {"zero_dephasing_commutes": diff.equals(0)}

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = bool(pos["coupling_detected"]) and all(neg.values()) and all(bnd.values())
    results = {"name": "axis_couple_3_5_phase_x_torus",
               "classification": "canonical",
               "scope_note": "system_v5/new docs/AXIS_AND_ENTROPY_REFERENCE.md (Axes 3, 5)",
               "exclusion_claim": "coupling excludes Axis 3 phase invariance under Axis 5 operator-family swap",
               "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
               "positive": pos, "negative": neg, "boundary": bnd, "pass": all_pass}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, "axis_couple_3_5_phase_x_torus_results.json")
    with open(p, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {p}")
