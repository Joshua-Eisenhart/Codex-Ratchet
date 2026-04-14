#!/usr/bin/env python3
"""Non-commutativity: Weyl rotor then Hopf projector vs Hopf then Weyl on S3 probe."""
import json, os, numpy as np
from clifford import Cl

TOOL_MANIFEST = {
    "clifford": {"tried": True, "used": True,
                 "reason": "Cl(3) rotors carry spinor/bivector structure that matrix algebra on R^4 alone would not preserve; the commutator [Weyl, Hopf] must be evaluated as rotor-sandwich products, not matrix multiplies."},
    "pytorch": {"tried": False, "used": False, "reason": "not needed for rotor commutator"},
    "z3": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {"clifford": "load_bearing", "pytorch": None, "z3": None, "sympy": None, "e3nn": None}

layout, blades = Cl(3)
e1, e2, e3 = blades['e1'], blades['e2'], blades['e3']
I3 = e1*e2*e3

def weyl_rotor(theta):
    # Weyl-like chiral rotor in e1^e2 plane
    return np.cos(theta/2) - (e1*e2)*np.sin(theta/2)

def hopf_rotor(phi):
    # Hopf fiber rotor in e2^e3 plane (different plane -> non-commuting)
    return np.cos(phi/2) - (e2*e3)*np.sin(phi/2)

def apply(R, v):
    return R*v*~R

def run_positive_tests():
    v = e1 + 0.3*e2 + 0.5*e3
    W, H = weyl_rotor(0.7), hopf_rotor(1.1)
    AB = apply(W, apply(H, v))
    BA = apply(H, apply(W, v))
    diff = (AB - BA).clean(1e-10)
    witness_nonzero = abs(float(diff.mag2())) > 1e-8
    return {"weyl_hopf_noncommute": witness_nonzero,
            "note": "A.B admits what B.A excludes: order swap excludes witness orientation",
            "pass": witness_nonzero}

def run_negative_tests():
    # Control: two rotors in SAME plane commute
    W1, W2 = weyl_rotor(0.4), weyl_rotor(1.2)
    v = e1 + e3
    AB = apply(W1, apply(W2, v))
    BA = apply(W2, apply(W1, v))
    diff = (AB - BA).clean(1e-10)
    commutes = abs(float(diff.mag2())) < 1e-10
    return {"same_plane_commutes_control": commutes, "pass": commutes}

def run_boundary_tests():
    # Scalar/identity case: trivially equal
    W, H = weyl_rotor(0.0), hopf_rotor(0.0)
    v = e1
    AB = apply(W, apply(H, v))
    BA = apply(H, apply(W, v))
    diff = (AB - BA).clean(1e-10)
    equal = abs(float(diff.mag2())) < 1e-12
    return {"identity_trivially_equal": equal, "pass": equal}

if __name__ == "__main__":
    results = {
        "name": "sim_geom_noncomm_weyl_then_hopf_vs_hopf_then_weyl",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "geom_noncomm_weyl_then_hopf_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    all_pass = all(r.get("pass") for r in [results["positive"], results["negative"], results["boundary"]])
    print(f"PASS={all_pass} -> {out_path}")
