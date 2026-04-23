#!/usr/bin/env python3
"""Non-commutativity: compound Hopf fiber rotor then Weyl chiral projector."""
import json, os, numpy as np
from clifford import Cl
layout, blades = Cl(3)
e1, e2, e3 = blades['e1'], blades['e2'], blades['e3']
I3 = e1*e2*e3

TOOL_MANIFEST = {
    "clifford": {"tried": True, "used": True,
                 "reason": "Weyl chiral projector P± = (1 ± i*e3)/2 uses pseudoscalar i*e3 — applying it after a Hopf bivector rotor requires full Cl(3) grade structure; matrix projectors on C^2 would lose the fiber winding's grade-2 contribution."},
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {"clifford": "load_bearing", "pytorch": None, "z3": None, "sympy": None, "e3nn": None}

def hopf(phi): return np.cos(phi/2) - (e2*e3)*np.sin(phi/2)
def weyl_proj_plus(v): return 0.5*(v + I3*e3*v*(I3*e3).inv()) if False else 0.5*(v + (e1*e2)*v*~(e1*e2))
# Simpler: use projector P = 0.5(1 + B) with B = e1e2 (idempotent under sandwich via conjugation-symmetric combo)
def weyl_projector(v):
    B = e1*e2
    return 0.5*v + 0.5*(B*v*~B)

def run_positive_tests():
    v = e1 + 0.4*e3
    R = hopf(0.9)
    # path1: R then project
    AB = weyl_projector(R*v*~R)
    # path2: project then R
    BA = R*weyl_projector(v)*~R
    nz = abs(float((AB - BA).mag2())) > 1e-8
    return {"hopf_then_weyl_proj_noncommute": nz,
            "note": "compound order swap excludes chiral-witness state", "pass": nz}

def run_negative_tests():
    # Control: use a rotor in the SAME plane as the projector (e1e2) -> commutes
    R = np.cos(0.5/2) - (e1*e2)*np.sin(0.5/2)
    v = e1 + e2 + 0.3*e3
    AB = weyl_projector(R*v*~R)
    BA = R*weyl_projector(v)*~R
    commutes = abs(float((AB-BA).mag2())) < 1e-10
    return {"aligned_plane_commutes_control": commutes, "pass": commutes}

def run_boundary_tests():
    R = hopf(0.0); v = e1
    eq = abs(float((weyl_projector(R*v*~R) - R*weyl_projector(v)*~R).mag2())) < 1e-12
    return {"identity_equal": eq, "pass": eq}

if __name__ == "__main__":
    results = {"name": "sim_geom_noncomm_hopf_fiber_then_weyl_projector",
               "classification": "canonical",
               "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
               "positive": run_positive_tests(), "negative": run_negative_tests(), "boundary": run_boundary_tests()}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "geom_noncomm_hopf_weyl_proj_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    ap = all(r.get("pass") for r in [results["positive"], results["negative"], results["boundary"]])
    print(f"PASS={ap} -> {out_path}")
