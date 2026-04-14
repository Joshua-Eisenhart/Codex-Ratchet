#!/usr/bin/env python3
"""sim_cl3_composition -- Composition of two reflections = rotation by twice the angle between normals."""
import json, os, numpy as np

classification = "canonical"

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": r} for k,r in {
    "pytorch":"not needed","pyg":"no graph","z3":"numeric","cvc5":"numeric",
    "sympy":"not used","clifford":"load_bearing: rotor == reflection chain","geomstats":"not used",
    "e3nn":"not used","rustworkx":"no graph","xgi":"no hypergraph","toponetx":"no cells","gudhi":"no persistence",
}.items()}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

from clifford import Cl
TOOL_MANIFEST["clifford"].update(tried=True, used=True); TOOL_INTEGRATION_DEPTH["clifford"] = "load_bearing"

layout, blades = Cl(3)
e1, e2, e3 = blades['e1'], blades['e2'], blades['e3']
e12 = e1*e2

def close(a,b,tol=1e-10):
    return float(abs((a-b).value).max()) < tol

def reflect(v, n):
    return -n * v * n

def run_positive_tests():
    r = {}
    # Two reflections across planes meeting at angle alpha/2 produce rotation by alpha
    alpha = np.pi/3
    n1 = e1
    n2 = np.cos(alpha/2)*e1 + np.sin(alpha/2)*e2
    v = e1 + 0.5*e3
    # reflect twice
    w = reflect(reflect(v, n1), n2)
    # rotor for angle alpha in e12 plane
    R = np.cos(alpha/2) - np.sin(alpha/2)*e12
    v_rot = R * v * ~R
    r["two_reflections_equal_rotation"] = close(w, v_rot, 1e-10)
    return r

def run_negative_tests():
    r = {}
    # Same plane reflected twice: identity, not a nontrivial rotation
    n = e1
    v = e2 + e3
    w = reflect(reflect(v, n), n)
    r["same_plane_is_identity"] = close(w, v)
    # Rotor for wrong angle should NOT match
    alpha = np.pi/4
    n1 = e1
    n2 = np.cos(alpha/2)*e1 + np.sin(alpha/2)*e2
    v = e1
    w = reflect(reflect(v, n1), n2)
    R_wrong = np.cos(np.pi/3) - np.sin(np.pi/3)*e12
    r["wrong_angle_mismatch"] = not close(w, R_wrong * v * ~R_wrong, 1e-8)
    return r

def run_boundary_tests():
    r = {}
    # orthogonal reflections -> rotation by pi in their plane
    v = e1
    w = reflect(reflect(v, e1), e2)
    R = np.cos(np.pi/2) - np.sin(np.pi/2)*e12  # = -e12
    r["orthogonal_gives_pi_rotation"] = close(w, R * v * ~R, 1e-10)
    return r

def main():
    results = {"name":"sim_cl3_composition","classification":classification,
               "positive":run_positive_tests(),"negative":run_negative_tests(),"boundary":run_boundary_tests(),
               "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH}
    ok = all(v for s in ("positive","negative","boundary") for v in results[s].values())
    results["pass"] = bool(ok)
    out = os.path.join(os.path.dirname(__file__),"results","sim_cl3_composition.json")
    os.makedirs(os.path.dirname(out),exist_ok=True)
    with open(out,"w") as f: json.dump(results,f,indent=2,default=str)
    print(json.dumps({"pass":results["pass"],"out":out}))
    return 0 if ok else 1

if __name__=="__main__": raise SystemExit(main())
