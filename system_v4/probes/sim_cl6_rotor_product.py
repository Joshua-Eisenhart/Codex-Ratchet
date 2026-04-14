#!/usr/bin/env python3
"""sim_cl6_rotor_product -- Rotors in Cl(6,0) multiply to rotors; R~R = 1."""
import json, os, numpy as np

classification = "canonical"

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": r} for k,r in {
    "pytorch":"not needed","pyg":"no graph","z3":"numeric","cvc5":"numeric",
    "sympy":"not used","clifford":"load_bearing: Cl(6,0) rotor algebra","geomstats":"not used",
    "e3nn":"not used","rustworkx":"no graph","xgi":"no hypergraph","toponetx":"no cells","gudhi":"no persistence",
}.items()}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

from clifford import Cl
TOOL_MANIFEST["clifford"].update(tried=True, used=True); TOOL_INTEGRATION_DEPTH["clifford"] = "load_bearing"

layout, blades = Cl(6)
E = [blades[f'e{i}'] for i in range(1,7)]

def close_scalar(R, target=1.0, tol=1e-10):
    RRt = R * ~R
    v = RRt.value
    ok_scalar = abs(float(v[0]) - target) < tol
    # all other components ~ 0
    rest = np.delete(v, 0)
    return ok_scalar and float(np.max(np.abs(rest))) < tol

def rotor(B_unit, theta):
    # B_unit is a unit bivector with B^2 = -1
    return np.cos(theta/2) - np.sin(theta/2)*B_unit

def run_positive_tests():
    r = {}
    B12 = E[0]*E[1]
    B34 = E[2]*E[3]
    B56 = E[4]*E[5]
    R1 = rotor(B12, 0.5)
    R2 = rotor(B34, 0.7)
    R3 = rotor(B56, 1.1)
    r["R1_unitary"] = close_scalar(R1)
    r["R2_unitary"] = close_scalar(R2)
    r["product_unitary"] = close_scalar(R1*R2*R3)
    # B12^2 = -1
    r["B12_sq_minus_one"] = float((B12*B12).value[0]) == -1.0
    return r

def run_negative_tests():
    r = {}
    # Mixed-plane bivector that is NOT simple: B = e12 + e34 squares to something with grade 4
    B = E[0]*E[1] + E[2]*E[3]
    sq = B*B
    # scalar part = -2, but grade-4 part nonzero -> not a unit bivector; naive exp NOT a rotor
    has_grade4 = float(abs(sq(4).value).max()) > 0
    r["nonsimple_bivector_has_grade4"] = has_grade4
    fake = np.cos(0.3) - np.sin(0.3)*B  # not a proper rotor
    r["naive_exp_not_unitary"] = not close_scalar(fake)
    return r

def run_boundary_tests():
    r = {}
    # theta=0
    R = rotor(E[0]*E[1], 0.0)
    r["identity_is_one"] = close_scalar(R, 1.0)
    # 4*pi = identity
    R2 = rotor(E[0]*E[1], 4*np.pi)
    v = R2.value
    r["4pi_is_one"] = abs(float(v[0]) - 1.0) < 1e-8 and float(np.max(np.abs(np.delete(v,0)))) < 1e-8
    return r

def main():
    results = {"name":"sim_cl6_rotor_product","classification":classification,
               "positive":run_positive_tests(),"negative":run_negative_tests(),"boundary":run_boundary_tests(),
               "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH}
    ok = all(v for s in ("positive","negative","boundary") for v in results[s].values())
    results["pass"] = bool(ok)
    out = os.path.join(os.path.dirname(__file__),"results","sim_cl6_rotor_product.json")
    os.makedirs(os.path.dirname(out),exist_ok=True)
    with open(out,"w") as f: json.dump(results,f,indent=2,default=str)
    print(json.dumps({"pass":results["pass"],"out":out}))
    return 0 if ok else 1

if __name__=="__main__": raise SystemExit(main())
