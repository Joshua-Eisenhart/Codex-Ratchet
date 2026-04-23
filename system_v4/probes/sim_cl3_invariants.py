#!/usr/bin/env python3
"""sim_cl3_invariants -- Rotor sandwich preserves inner product, grade, and pseudoscalar."""
import json, os, numpy as np

classification = "classical_baseline"
DEMOTE_REASON = "no non-numpy load_bearing tool; numeric numpy only"

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": r} for k,r in {
    "pytorch":"not needed","pyg":"no graph","z3":"numeric","cvc5":"numeric",
    "sympy":"not used","clifford":"load_bearing: grade projection and inner product","geomstats":"not used",
    "e3nn":"not used","rustworkx":"no graph","xgi":"no hypergraph","toponetx":"no cells","gudhi":"no persistence",
}.items()}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

from clifford import Cl
TOOL_MANIFEST["clifford"].update(tried=True, used=True); TOOL_INTEGRATION_DEPTH["clifford"] = "load_bearing"

layout, blades = Cl(3)
e1, e2, e3 = blades['e1'], blades['e2'], blades['e3']
e12 = e1*e2
I = e1*e2*e3

def inner(a,b):
    return float(((a*b + b*a)/2).value[0])

def rotor(B, theta):
    return np.cos(theta/2) - np.sin(theta/2)*B

def apply(R, x):
    return R * x * ~R

def run_positive_tests():
    r = {}
    R = rotor(e12, 0.4)
    a, b = e1 + e2, e1 - 2*e3
    r["inner_preserved"] = abs(inner(a,b) - inner(apply(R,a), apply(R,b))) < 1e-10
    # grade preserved: vector stays a vector
    v = 3*e1 - e2 + 2*e3
    v_rot = apply(R, v)
    r["grade1_preserved"] = abs(float(v_rot.value[0])) < 1e-12 and float(abs((v_rot - v_rot(1)).value).max()) < 1e-12
    # pseudoscalar invariant (I commutes with rotor in Cl(3))
    r["pseudoscalar_invariant"] = float(abs((apply(R, I) - I).value).max()) < 1e-10
    return r

def run_negative_tests():
    r = {}
    # reversion flips sign of bivector
    R = rotor(e12, 0.4)
    r["reverse_flips_bivector_part"] = float(abs((~R - R).value).max()) > 1e-6
    # non-rotor (scaled rotor) does NOT preserve inner product
    S = 2 * rotor(e12, 0.4)
    a, b = e1+e2, e1-e3
    r["scaled_breaks_inner"] = abs(inner(a,b) - inner(S*a*~S, S*b*~S)) > 1e-6
    return r

def run_boundary_tests():
    r = {}
    # identity rotor preserves everything
    R = rotor(e12, 0.0)
    v = e1 + e2 + e3
    r["identity_rotor"] = float(abs((apply(R,v) - v).value).max()) < 1e-12
    # 2pi rotation returns vector (not spinor) unchanged
    R2 = rotor(e12, 2*np.pi)
    r["2pi_vector_unchanged"] = float(abs((apply(R2,v) - v).value).max()) < 1e-10
    return r

def main():
    results = {"name":"sim_cl3_invariants","classification":classification,
               "positive":run_positive_tests(),"negative":run_negative_tests(),"boundary":run_boundary_tests(),
               "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH}
    ok = all(v for s in ("positive","negative","boundary") for v in results[s].values())
    results["pass"] = bool(ok)
    out = os.path.join(os.path.dirname(__file__),"results","sim_cl3_invariants.json")
    os.makedirs(os.path.dirname(out),exist_ok=True)
    with open(out,"w") as f: json.dump(results,f,indent=2,default=str)
    print(json.dumps({"pass":results["pass"],"out":out}))
    return 0 if ok else 1

if __name__=="__main__": raise SystemExit(main())
