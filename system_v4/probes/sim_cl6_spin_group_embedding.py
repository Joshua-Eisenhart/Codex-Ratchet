#!/usr/bin/env python3
"""sim_cl6_spin_group_embedding -- Spin(6) rotors preserve quadratic form; Cl(3) embeds into Cl(6)."""
import json, os, numpy as np

classification = "classical_baseline"
DEMOTE_REASON = "no non-numpy load_bearing tool; numeric numpy only"

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": r} for k,r in {
    "pytorch":"not needed","pyg":"no graph","z3":"numeric","cvc5":"numeric",
    "sympy":"not used","clifford":"load_bearing: Spin(6) sandwich + Cl(3) subalgebra check","geomstats":"not used",
    "e3nn":"not used","rustworkx":"no graph","xgi":"no hypergraph","toponetx":"no cells","gudhi":"no persistence",
}.items()}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

from clifford import Cl
TOOL_MANIFEST["clifford"].update(tried=True, used=True); TOOL_INTEGRATION_DEPTH["clifford"] = "load_bearing"

layout6, blades6 = Cl(6)
E6 = [blades6[f'e{i}'] for i in range(1,7)]

layout3, blades3 = Cl(3)
E3 = [blades3[f'e{i}'] for i in range(1,4)]

def qform6(v):
    # v is grade-1 in Cl(6); q(v) = v*v = scalar
    return float((v*v).value[0])

def rotor(B, theta):
    return np.cos(theta/2) - np.sin(theta/2)*B

def apply(R, v):
    return R * v * ~R

def run_positive_tests():
    r = {}
    # Spin(6) rotor preserves quadratic form
    B = E6[0]*E6[1]
    R = rotor(B, 0.5)
    v = 1.0*E6[0] + 2.0*E6[1] + 3.0*E6[4]
    q1 = qform6(v)
    vp = apply(R, v)
    # ensure grade 1
    grade1_only = float(abs((vp - vp(1)).value).max()) < 1e-10
    r["rotor_preserves_quadratic_form"] = abs(q1 - qform6(vp)) < 1e-10
    r["rotor_preserves_grade1"] = grade1_only
    # Sub-rotor in {e1,e2,e3} generators of Cl(6) reproduces Cl(3) rotor behavior
    B_sub = E6[0]*E6[1]
    Rsub = rotor(B_sub, 0.7)
    v3_in_6 = 1.0*E6[0] + 0.5*E6[1] + 0.3*E6[2]
    w6 = apply(Rsub, v3_in_6)
    # now do same in Cl(3)
    B3 = E3[0]*E3[1]
    R3 = rotor(B3, 0.7)
    v3 = 1.0*E3[0] + 0.5*E3[1] + 0.3*E3[2]
    w3 = R3 * v3 * ~R3
    # coefficients on e1,e2,e3 must match
    c6 = [float(w6.value[1]), float(w6.value[2]), float(w6.value[3])]
    c3 = [float(w3.value[1]), float(w3.value[2]), float(w3.value[3])]
    r["cl3_embeds_in_cl6"] = all(abs(a-b) < 1e-10 for a,b in zip(c6,c3))
    return r

def run_negative_tests():
    r = {}
    # Scaling rotor breaks preservation
    B = E6[0]*E6[1]
    S = 1.5 * rotor(B, 0.5)
    v = 1.0*E6[0] + 2.0*E6[1]
    q1 = qform6(v)
    # Apply naive sandwich (not true rotor anymore)
    vp = S * v * ~S
    q2 = qform6(vp) if float(abs((vp - vp(1)).value).max()) < 1e-8 else None
    # Either grade shifted OR magnitude changed -- both count as failure-of-preservation
    shifted = float(abs((vp - vp(1)).value).max()) > 1e-8
    changed = (q2 is not None) and abs(q1 - q2) > 1e-6
    r["scaled_rotor_fails"] = shifted or changed
    return r

def run_boundary_tests():
    r = {}
    # Identity rotor
    R = rotor(E6[0]*E6[1], 0.0)
    v = E6[2] + E6[5]
    r["identity_preserves"] = float(abs((apply(R,v) - v).value).max()) < 1e-12
    # Disjoint-plane rotor leaves orthogonal vector fixed
    R = rotor(E6[0]*E6[1], 1.3)
    r["orthogonal_vector_fixed"] = float(abs((apply(R, E6[4]) - E6[4]).value).max()) < 1e-10
    return r

def main():
    results = {"name":"sim_cl6_spin_group_embedding","classification":classification,
               "positive":run_positive_tests(),"negative":run_negative_tests(),"boundary":run_boundary_tests(),
               "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH}
    ok = all(v for s in ("positive","negative","boundary") for v in results[s].values())
    results["pass"] = bool(ok)
    out = os.path.join(os.path.dirname(__file__),"results","sim_cl6_spin_group_embedding.json")
    os.makedirs(os.path.dirname(out),exist_ok=True)
    with open(out,"w") as f: json.dump(results,f,indent=2,default=str)
    print(json.dumps({"pass":results["pass"],"out":out}))
    return 0 if ok else 1

if __name__=="__main__": raise SystemExit(main())
