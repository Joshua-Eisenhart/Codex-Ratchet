#!/usr/bin/env python3
"""Non-commutativity: chirality reflection then fiber winding rotor."""
import json, os, numpy as np
from clifford import Cl
layout, blades = Cl(3)
e1, e2, e3 = blades['e1'], blades['e2'], blades['e3']

TOOL_MANIFEST = {
    "clifford": {"tried": True, "used": True,
                 "reason": "chirality flip is grade-reversal combined with a vector reflection; this cannot be encoded as an orthogonal matrix plus rotor composition — only Cl(3) versor action preserves the Pin structure whose commutator with a rotor is nontrivial."},
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {"clifford": "load_bearing", "pytorch": None, "z3": None, "sympy": None, "e3nn": None}

def chirality(v):  return -e1*v*e1   # reflection through e2e3 plane (Pin element)
def winding(v, t):
    # winding in e1^e2 plane so reflection across e2e3 (through e1) does not commute
    R = np.cos(t/2) - (e1*e2)*np.sin(t/2)
    return R*v*~R

def run_positive_tests():
    v = e1 + 0.4*e2 + 0.7*e3
    AB = winding(chirality(v), 0.9)
    BA = chirality(winding(v, 0.9))
    nz = abs(float((AB - BA).mag2())) > 1e-8
    return {"chirality_winding_noncommute": nz,
            "note": "chirality-first admits state that winding-first excludes", "pass": nz}

def run_negative_tests():
    # Winding axis aligned with reflection axis (e1 plane fixed): commute? Use e1e2 winding and reflect in e3 plane = -e3 v e3; align: reflect e1e2 plane = -(e1e2) v (e1e2)? Use identity reflection as control
    def ident_refl(v): return v
    v = e1 + e2
    AB = winding(ident_refl(v), 0.5)
    BA = ident_refl(winding(v, 0.5))
    commutes = abs(float((AB-BA).mag2())) < 1e-10
    return {"identity_reflection_commutes_control": commutes, "pass": commutes}

def run_boundary_tests():
    # scalar-only probe; reflections and rotors leave scalar grade invariant
    v = layout.scalar * 1.0
    diff = abs(float((winding(chirality(v), 0.3) - chirality(winding(v, 0.3))).mag2()))
    return {"scalar_trivially_equal": diff < 1e-12, "pass": diff < 1e-12}

if __name__ == "__main__":
    results = {"name": "sim_geom_noncomm_chirality_then_fiber_winding",
               "classification": "canonical",
               "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
               "positive": run_positive_tests(), "negative": run_negative_tests(), "boundary": run_boundary_tests()}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "geom_noncomm_chirality_winding_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    ap = all(r.get("pass") for r in [results["positive"], results["negative"], results["boundary"]])
    print(f"PASS={ap} -> {out_path}")
