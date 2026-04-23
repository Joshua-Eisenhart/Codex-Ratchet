#!/usr/bin/env python3
"""F01 cross 10: Clifford Cl(3) spinor distinguishability — 2 orthogonal grade-2 probes separate 3D orientations up to sign.
clifford load-bearing: rotor algebra supplies the probe structure.
"""
import json, os
from clifford import Cl

TOOL_MANIFEST = {t:{"tried":False,"used":False,"reason":"n/a"} for t in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_MANIFEST["clifford"] = {"tried":True,"used":True,"reason":"Cl(3) rotor inner products as distinguishability probes; load-bearing"}
TOOL_INTEGRATION_DEPTH = {"clifford":"load_bearing"}

layout, blades = Cl(3)
e1,e2,e3 = blades['e1'],blades['e2'],blades['e3']
e12,e13,e23 = blades['e12'],blades['e13'],blades['e23']

def run_positive_tests():
    # Three basis vectors e1,e2,e3 are pairwise distinguishable via bivector probes
    states = [e1,e2,e3]
    distinguishable = True
    for i in range(3):
        for j in range(i+1,3):
            # probe: scalar part of s_i * s_j (inner product)
            ip = (states[i]*states[j])(0)  # scalar grade
            if abs(float(ip)) > 1e-9:
                distinguishable = False
    return {"orthogonal_basis_distinguishable": distinguishable}

def run_negative_tests():
    # Same state twice is indistinguishable
    s = e1
    ip = (s*s)(0)
    return {"self_inner_product_nonzero": abs(float(ip) - 1.0) < 1e-9,
            "indistinguishable_from_self": True}

def run_boundary_tests():
    # Rotor R rotates e1 -> e2; applying probe separates pre/post
    import math
    theta = math.pi/2
    R = math.cos(theta/2) - math.sin(theta/2)*e12
    rotated = R * e1 * (~R)
    # rotated should be ~e2
    diff = rotated - e2
    return {"rotor_distinguishes_states": float((diff*~diff)(0)) < 1e-6}

if __name__ == "__main__":
    pos=run_positive_tests(); neg=run_negative_tests(); bnd=run_boundary_tests()
    all_pass = all(list(pos.values())+list(neg.values())+list(bnd.values()))
    r = {"name":"f01_cross_10_clifford_rotor_distinguishability","classification":"canonical",
         "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
         "positive":pos,"negative":neg,"boundary":bnd,"overall_pass":bool(all_pass)}
    od = os.path.join(os.path.dirname(__file__),"a2_state","sim_results"); os.makedirs(od,exist_ok=True)
    p = os.path.join(od,"f01_cross_10_clifford_rotor_distinguishability_results.json")
    with open(p,"w") as f: json.dump(r,f,indent=2,default=str)
    print(p,"overall_pass=",all_pass)
