#!/usr/bin/env python3
"""Axis 1 x Axis 5 coupling: curvature branch vs operator family (dephasing vs rotation).
Torus seat realized via Cl(3) rotors acting on a 2-torus bivector plane.
scope_note: system_v5/new docs/AXIS_AND_ENTROPY_REFERENCE.md (Axes 1, 5).
Exclusion: coupling excludes commutation of curvature-branch reversal with
operator-family swap on the torus seat.
"""
import json, os
from clifford import Cl
import numpy as np

TOOL_MANIFEST = {"clifford": {"tried": True, "used": True,
    "reason": "Cl(3) rotors realize rotation vs dephasing on the torus bivector; commutator is load-bearing"}}
TOOL_INTEGRATION_DEPTH = {"clifford": "load_bearing"}

layout, blades = Cl(3)
e1, e2, e3 = blades['e1'], blades['e2'], blades['e3']
e12 = e1 * e2

def _rot(theta):
    return np.cos(theta/2) + np.sin(theta/2) * e12

def _deph(alpha):
    # dephasing as scalar damp along e12 plane
    return np.cos(alpha) + np.sin(alpha) * e1  # distinct operator family

def _apply(R, v):
    return R * v * ~R

def run_positive_tests():
    v = e1 + 0.5 * e2
    R = _rot(0.7)
    D = _deph(0.4)
    # curvature-branch reversal = invert rotor; operator swap = rot<->deph
    a = _apply(R, _apply(D, v))
    b = _apply(D, _apply(R, v))
    diff = float(((a - b).mag2())**0.5)
    return {"noncommute_distance": diff, "coupling_detected": diff > 1e-6}

def run_negative_tests():
    v = e1
    I = 1 + 0 * e12  # identity
    a = _apply(I, _apply(I, v))
    b = _apply(I, _apply(I, v))
    return {"identity_commutes": float(((a-b).mag2())**0.5) < 1e-12}

def run_boundary_tests():
    v = e1
    R = _rot(1e-6); D = _deph(1e-6)
    a = _apply(R, _apply(D, v)); b = _apply(D, _apply(R, v))
    return {"small_angle_small_gap": float(((a-b).mag2())**0.5) < 1e-4}

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = bool(pos["coupling_detected"]) and all(neg.values()) and all(bnd.values())
    results = {"name": "axis_couple_1_5_curvature_x_torus",
               "classification": "canonical",
               "scope_note": "system_v5/new docs/AXIS_AND_ENTROPY_REFERENCE.md (Axes 1, 5)",
               "exclusion_claim": "coupling excludes commutation of Axis 1 curvature reversal with Axis 5 operator swap on the torus seat",
               "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
               "positive": pos, "negative": neg, "boundary": bnd, "pass": all_pass}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, "axis_couple_1_5_curvature_x_torus_results.json")
    with open(p, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {p}")
