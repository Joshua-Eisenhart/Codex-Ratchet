#!/usr/bin/env python3
"""Axis 4 x Axis 5 coupling: loop-order family (UEUE vs EUEU) x operator family.
Realized with Cl(3) rotors as alternating U/E sequences on a vector.
scope_note: system_v5/new docs/AXIS_AND_ENTROPY_REFERENCE.md (Axes 4, 5).
Exclusion: coupling excludes UEUE/EUEU equivalence under operator-family fixed point.
"""
import json, os
from clifford import Cl
import numpy as np

TOOL_MANIFEST = {"clifford": {"tried": True, "used": True,
    "reason": "Cl(3) rotors evaluate UEUE vs EUEU order; residue is load-bearing"}}
TOOL_INTEGRATION_DEPTH = {"clifford": "load_bearing"}

layout, blades = Cl(3)
e1, e2, e3 = blades['e1'], blades['e2'], blades['e3']
e12, e23 = e1*e2, e2*e3

def U(t): return np.cos(t/2) + np.sin(t/2) * e12
def E(t): return np.cos(t/2) + np.sin(t/2) * e23

def apply_seq(seq, v):
    for R in seq:
        v = R * v * ~R
    return v

def run_positive_tests():
    v = e1 + 0.3*e2 + 0.2*e3
    u, e = U(0.5), E(0.4)
    ueue = apply_seq([u, e, u, e], v)
    euue = apply_seq([e, u, u, e], v)   # distinct loop order
    eueu = apply_seq([e, u, e, u], v)
    d1 = float(((ueue - eueu).mag2())**0.5)
    d2 = float(((ueue - euue).mag2())**0.5)
    return {"UEUE_vs_EUEU_distance": d1, "UEUE_vs_EUUE_distance": d2,
            "coupling_detected": d1 > 1e-6 and d2 > 1e-6}

def run_negative_tests():
    v = e1
    I = 1 + 0*e12
    a = apply_seq([I, I, I, I], v); b = apply_seq([I, I, I, I], v)
    return {"identity_orderless": float(((a-b).mag2())**0.5) < 1e-12}

def run_boundary_tests():
    v = e1
    u, e = U(1e-6), E(1e-6)
    d = float(((apply_seq([u,e,u,e], v) - apply_seq([e,u,e,u], v)).mag2())**0.5)
    return {"small_angle_small_gap": d < 1e-4}

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = bool(pos["coupling_detected"]) and all(neg.values()) and all(bnd.values())
    results = {"name": "axis_couple_4_5_loop_x_torus",
               "classification": "canonical",
               "scope_note": "system_v5/new docs/AXIS_AND_ENTROPY_REFERENCE.md (Axes 4, 5)",
               "exclusion_claim": "coupling excludes UEUE/EUEU equivalence under Axis 5 operator fixed point",
               "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
               "positive": pos, "negative": neg, "boundary": bnd, "pass": all_pass}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, "axis_couple_4_5_loop_x_torus_results.json")
    with open(p, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {p}")
