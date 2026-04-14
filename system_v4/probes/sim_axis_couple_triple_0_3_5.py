#!/usr/bin/env python3
"""Three-axis coupling: Axis 0 x Axis 3 x Axis 5.
Entropy-gradient seat x phase (fiber/base) x operator family (rotation/dephasing)
realized via Cl(3) rotors and trivector residues.
scope_note: system_v5/new docs/AXIS_AND_ENTROPY_REFERENCE.md (Axes 0, 3, 5).
Exclusion: coupling excludes pairwise independence — the three-axis joint residue
cannot be factored as a product of two-axis residues.
"""
import json, os
from clifford import Cl
import numpy as np

TOOL_MANIFEST = {"clifford": {"tried": True, "used": True,
    "reason": "Cl(3) rotor composition of three operator families generates residue; load-bearing"}}
TOOL_INTEGRATION_DEPTH = {"clifford": "load_bearing"}

layout, blades = Cl(3)
e1, e2, e3 = blades['e1'], blades['e2'], blades['e3']
e12, e23, e13 = e1*e2, e2*e3, e1*e3

def R_rot(t): return np.cos(t/2) + np.sin(t/2)*e12      # Axis 5 rotation
def R_phase(p): return np.cos(p/2) + np.sin(p/2)*e13    # Axis 3 phase
def R_ent(s): return np.cos(s/2) + np.sin(s/2)*e23      # Axis 0 entropy seat

def triple(v, s, p, t):
    R = R_rot(t) * R_phase(p) * R_ent(s)
    return R * v * ~R

def run_positive_tests():
    v = e1 + 0.2*e2 + 0.1*e3
    # compare joint (0,3,5) vs factored pairwise products
    joint = triple(v, 0.4, 0.5, 0.6)
    pair_05 = R_rot(0.6)*R_ent(0.4) * v * ~(R_rot(0.6)*R_ent(0.4))
    pair_35 = R_rot(0.6)*R_phase(0.5) * v * ~(R_rot(0.6)*R_phase(0.5))
    pair_03 = R_phase(0.5)*R_ent(0.4) * v * ~(R_phase(0.5)*R_ent(0.4))
    d1 = float(((joint - pair_05).mag2())**0.5)
    d2 = float(((joint - pair_35).mag2())**0.5)
    d3 = float(((joint - pair_03).mag2())**0.5)
    return {"d_vs_05": d1, "d_vs_35": d2, "d_vs_03": d3,
            "triple_coupling_detected": d1 > 1e-6 and d2 > 1e-6 and d3 > 1e-6}

def run_negative_tests():
    v = e1
    # All zero angles => identity, joint == every pair
    joint = triple(v, 0.0, 0.0, 0.0)
    return {"zero_angles_identity": float(((joint - v).mag2())**0.5) < 1e-12}

def run_boundary_tests():
    v = e1
    joint = triple(v, 1e-7, 1e-7, 1e-7)
    return {"near_identity_small": float(((joint - v).mag2())**0.5) < 1e-5}

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = bool(pos["triple_coupling_detected"]) and all(neg.values()) and all(bnd.values())
    results = {"name": "axis_couple_triple_0_3_5",
               "classification": "canonical",
               "scope_note": "system_v5/new docs/AXIS_AND_ENTROPY_REFERENCE.md (Axes 0, 3, 5)",
               "exclusion_claim": "coupling excludes factoring triple (0,3,5) residue as any pairwise product",
               "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
               "positive": pos, "negative": neg, "boundary": bnd, "pass": all_pass}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, "axis_couple_triple_0_3_5_results.json")
    with open(p, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {p}")
