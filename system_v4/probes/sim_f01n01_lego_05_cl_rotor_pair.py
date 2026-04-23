#!/usr/bin/env python3
"""Lego 05: Cl(3) rotor R and -R generate same two-sided action x -> R x R~.
Claim: double-cover => rotor and its negative are F01-indistinguishable as operators.
clifford load-bearing.
"""
import json, os
from clifford import Cl
import numpy as np

TOOL_MANIFEST = {t:{"tried":False,"used":False,"reason":"n/a"} for t in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_MANIFEST["clifford"] = {"tried":True,"used":True,"reason":"Cl(3) rotor sandwich; load-bearing"}
TOOL_INTEGRATION_DEPTH = {"clifford":"load_bearing"}

layout, blades = Cl(3)
e1,e2,e3 = blades['e1'], blades['e2'], blades['e3']

def sandwich(R, x): return R*x*~R

def run_positive_tests():
    theta = 0.7
    B = e1*e2
    R = np.cos(theta/2) - np.sin(theta/2)*B
    negR = -R
    x = e1 + 0.3*e2 + 0.5*e3
    a = sandwich(R, x); b = sandwich(negR, x)
    diff = (a - b)
    return {"R_and_negR_equivalent": abs(float(diff.mag2())) < 1e-20}

def run_negative_tests():
    theta = 0.7
    R1 = np.cos(theta/2) - np.sin(theta/2)*(e1*e2)
    R2 = np.cos(1.2/2) - np.sin(1.2/2)*(e1*e2)
    x = e1 + 0.3*e2
    a = sandwich(R1, x); b = sandwich(R2, x)
    return {"different_angles_distinguishable": abs(float((a-b).mag2())) > 1e-9}

def run_boundary_tests():
    # theta=0 rotor => identity; +/- still equivalent
    R = 1 + 0*(e1*e2)
    x = e1
    a = sandwich(R, x); b = sandwich(-R, x)
    return {"identity_pair_equivalent": abs(float((a-b).mag2())) < 1e-20}

if __name__ == "__main__":
    pos=run_positive_tests(); neg=run_negative_tests(); bnd=run_boundary_tests()
    all_pass = all(list(pos.values())+list(neg.values())+list(bnd.values()))
    r = {"name":"lego_05_cl_rotor_pair","classification":"canonical",
         "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
         "positive":pos,"negative":neg,"boundary":bnd,"overall_pass":bool(all_pass)}
    od = os.path.join(os.path.dirname(__file__),"a2_state","sim_results"); os.makedirs(od,exist_ok=True)
    p = os.path.join(od,"lego_05_cl_rotor_pair_results.json")
    with open(p,"w") as f: json.dump(r,f,indent=2,default=str)
    print(p,"overall_pass=",all_pass)
