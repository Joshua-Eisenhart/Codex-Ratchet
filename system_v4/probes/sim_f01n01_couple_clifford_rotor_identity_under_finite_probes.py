#!/usr/bin/env python3
"""F01xN01 coupling 8: Cl(3) rotor identity under finite probes.
Exclusion claim: F01 (finite rotor-conjugation probes) + N01 (double-cover equivalence)
jointly exclude distinguishing R from -R via any probe in the rotor-sandwich family.
clifford load-bearing.
"""
import json, os, numpy as np
from clifford import Cl

TOOL_MANIFEST = {t:{"tried":False,"used":False,"reason":"n/a"} for t in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_MANIFEST["clifford"] = {"tried":True,"used":True,"reason":"Cl(3) rotor sandwich exclusion under finite probe family; load-bearing"}
TOOL_INTEGRATION_DEPTH = {"clifford":"load_bearing"}

layout, blades = Cl(3)
e1,e2,e3 = blades['e1'], blades['e2'], blades['e3']

def sandwich(R, x): return R*x*~R

def probe_family():
    # Three F01 probes = mag2 of sandwich on three basis vectors
    return [e1, e2, e3]

def run_positive_tests():
    theta = 0.7
    B = e1*e2
    R = np.cos(theta/2) - np.sin(theta/2)*B
    probes = probe_family()
    diffs = [float((sandwich(R,x) - sandwich(-R,x)).mag2()) for x in probes]
    return {"all_probes_coincide_on_R_and_negR": all(d < 1e-20 for d in diffs)}

def run_negative_tests():
    # different rotor angles: probes DO separate (so the double-cover equivalence is specific)
    R1 = np.cos(0.7/2) - np.sin(0.7/2)*(e1*e2)
    R2 = np.cos(1.1/2) - np.sin(1.1/2)*(e1*e2)
    probes = probe_family()
    diffs = [float((sandwich(R1,x) - sandwich(R2,x)).mag2()) for x in probes]
    return {"distinct_angles_separated": any(d > 1e-9 for d in diffs)}

def run_boundary_tests():
    # identity rotor: R=+1, -R=-1; sandwich equivalent across all probes
    R = 1 + 0*(e1*e2)
    probes = probe_family()
    diffs = [float((sandwich(R,x) - sandwich(-R,x)).mag2()) for x in probes]
    return {"identity_rotor_pair_indistinguishable": all(d < 1e-20 for d in diffs)}

if __name__ == "__main__":
    pos=run_positive_tests(); neg=run_negative_tests(); bnd=run_boundary_tests()
    all_pass = all(list(pos.values())+list(neg.values())+list(bnd.values()))
    r = {"name":"f01n01_couple_clifford_rotor_identity_under_finite_probes","classification":"canonical",
         "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
         "positive":pos,"negative":neg,"boundary":bnd,"overall_pass":bool(all_pass),
         "exclusion_statement":"F01+N01 jointly exclude separating R from -R under Cl(3) rotor-sandwich probe family."}
    od = os.path.join(os.path.dirname(__file__),"a2_state","sim_results"); os.makedirs(od,exist_ok=True)
    p = os.path.join(od,"f01n01_couple_clifford_rotor_identity_under_finite_probes_results.json")
    with open(p,"w") as f: json.dump(r,f,indent=2,default=str)
    print(p,"overall_pass=",all_pass)
