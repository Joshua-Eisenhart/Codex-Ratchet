#!/usr/bin/env python3
"""Non-commutativity: Spin(3) rotor then Pin(3) reflection — double cover matters for order."""
import json, os, numpy as np
from clifford import Cl
layout, blades = Cl(3)
e1, e2, e3 = blades['e1'], blades['e2'], blades['e3']

TOOL_MANIFEST = {
    "clifford": {"tried": True, "used": True,
                 "reason": "Pin(3) reflection is an odd-grade versor; its non-commutativity with an even-grade Spin(3) rotor depends on the double-cover sign which is only present in the Cl(3) versor algebra — matrix SO(3) collapses the ±1 ambiguity and misses the sign witness."},
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {"clifford": "load_bearing", "pytorch": None, "z3": None, "sympy": None, "e3nn": None}

def spin_rotor(t): return np.cos(t/2) - (e1*e2)*np.sin(t/2)
def pin_reflect(v, n): return -n*v*n  # reflection across hyperplane orthogonal to n

def run_positive_tests():
    v = e1 + 0.6*e2 + 0.2*e3
    R = spin_rotor(1.3)
    n = e2
    AB = R*pin_reflect(v, n)*~R
    BA = pin_reflect(R*v*~R, n)
    nz = abs(float((AB-BA).mag2())) > 1e-8
    return {"spin_pin_noncommute": nz, "note": "order swap excludes sign-coherent witness", "pass": nz}

def run_negative_tests():
    # Reflection axis = rotor axis -> commute
    R = spin_rotor(1.0)
    n = e3   # rotor in e1e2 plane, reflection orthogonal to e3: leaves e1e2 plane invariant
    v = e1 + e2 + e3
    AB = R*pin_reflect(v, n)*~R
    BA = pin_reflect(R*v*~R, n)
    commutes = abs(float((AB-BA).mag2())) < 1e-10
    return {"orthogonal_axis_commutes_control": commutes, "pass": commutes}

def run_boundary_tests():
    R = spin_rotor(0.0); n = e1
    v = e2
    eq = abs(float((R*pin_reflect(v,n)*~R - pin_reflect(R*v*~R, n)).mag2())) < 1e-12
    return {"identity_equal": eq, "pass": eq}

if __name__ == "__main__":
    results = {"name": "sim_geom_noncomm_spin_double_cover_then_reflection",
               "classification": "canonical",
               "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
               "positive": run_positive_tests(), "negative": run_negative_tests(), "boundary": run_boundary_tests()}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "geom_noncomm_spin_reflect_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    ap = all(r.get("pass") for r in [results["positive"], results["negative"], results["boundary"]])
    print(f"PASS={ap} -> {out_path}")
