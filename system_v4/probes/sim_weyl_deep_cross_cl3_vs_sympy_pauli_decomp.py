#!/usr/bin/env python3
"""
sim_weyl_deep_cross_cl3_vs_sympy_pauli_decomp
Scope: Cross-check Cl(3) bivector coefficients against sympy Pauli-matrix
decomposition. Survives only when both decompositions agree; divergence
excludes the candidate identification.
See system_v5/new docs/ENGINE_MATH_REFERENCE.md.
"""
import json, os, numpy as np
from clifford import Cl
import sympy as sp

SCOPE_NOTE = "Cl(3) bivector <-> Pauli i*sigma cross-check; ENGINE_MATH_REFERENCE.md"

TOOL_MANIFEST = {
    "clifford": {"tried": True, "used": True, "reason": "Cl(3) bivector coefficient extraction"},
    "sympy":    {"tried": True, "used": True, "reason": "symbolic Pauli matrix trace decomposition"},
    "z3": {"tried": False, "used": False, "reason": "real-valued coefficient match, not SAT"},
}
TOOL_INTEGRATION_DEPTH = {"clifford": "load_bearing", "sympy": "load_bearing"}

layout, blades = Cl(3)
e1,e2,e3 = blades["e1"], blades["e2"], blades["e3"]

s1 = sp.Matrix([[0,1],[1,0]])
s2 = sp.Matrix([[0,-sp.I],[sp.I,0]])
s3 = sp.Matrix([[1,0],[0,-1]])

def cl3_bivector_coeffs(B):
    # B = a*e1e2 + b*e2e3 + c*e3e1; note B[(1,3)] stores e1e3 = -e3e1, so negate
    return float(B[(1,2)]), float(B[(2,3)]), -float(B[(1,3)])

def sympy_pauli_coeffs(M):
    # M = i*(a*s3 + b*s1 + c*s2)  <-- mapping e12 ~ i s3, e23 ~ i s1, e31 ~ i s2
    a = sp.simplify(sp.trace(M * (-sp.I*s3))/2)
    b = sp.simplify(sp.trace(M * (-sp.I*s1))/2)
    c = sp.simplify(sp.trace(M * (-sp.I*s2))/2)
    return float(a), float(b), float(c)

def build_pair(a,b,c):
    B = a*e1*e2 + b*e2*e3 + c*e3*e1
    M = sp.I*(a*s3 + b*s1 + c*s2)
    return B, M

def run_positive_tests():
    B,M = build_pair(0.3, -0.7, 1.1)
    ca = cl3_bivector_coeffs(B)
    cb = sympy_pauli_coeffs(M)
    ok = all(abs(ca[i]-cb[i])<1e-9 for i in range(3))
    return {"decomps_agree": {"pass": ok, "cl3": ca, "pauli": cb,
            "reason": "agreement admits identification of bivector with i*sigma"}}

def run_negative_tests():
    # corrupted Pauli matrix excludes identification
    B,_ = build_pair(0.3, -0.7, 1.1)
    Mbad = sp.I*(0.3*s3 + 0.1*s1 + 1.1*s2)   # b mismatched
    ca = cl3_bivector_coeffs(B); cb = sympy_pauli_coeffs(Mbad)
    excluded = not all(abs(ca[i]-cb[i])<1e-9 for i in range(3))
    return {"mismatch_excluded": {"pass": excluded, "cl3": ca, "pauli": cb,
            "reason": "coefficient divergence excludes shared decomposition"}}

def run_boundary_tests():
    B,M = build_pair(0,0,0)
    ca = cl3_bivector_coeffs(B); cb = sympy_pauli_coeffs(M)
    ok = all(abs(ca[i])<1e-12 and abs(cb[i])<1e-12 for i in range(3))
    return {"zero_vector": {"pass": ok, "reason": "zero bivector matches zero Pauli combo"}}

if __name__ == "__main__":
    pos, neg, bnd = run_positive_tests(), run_negative_tests(), run_boundary_tests()
    all_pass = all(t["pass"] for t in {**pos, **neg, **bnd}.values())
    results = {
        "name": "sim_weyl_deep_cross_cl3_vs_sympy_pauli_decomp",
        "classification": "canonical",
        "scope_note": SCOPE_NOTE,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "overall_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_weyl_deep_cross_cl3_vs_sympy_pauli_decomp_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {out_path}")
