#!/usr/bin/env python3
"""Lego 03: identity-via-indistinguishability for mixed states.
Claim: rho == sigma iff Tr(P rho) = Tr(P sigma) for all hermitian probes P.
z3 load-bearing: SAT-encodes existence of distinguishing probe when rho!=sigma.
"""
import json, os, numpy as np, z3

TOOL_MANIFEST = {t:{"tried":False,"used":False,"reason":"n/a"} for t in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_MANIFEST["z3"] = {"tried":True,"used":True,"reason":"existential probe search; load-bearing"}
TOOL_INTEGRATION_DEPTH = {"z3":"load_bearing"}

def probe_distinguishes_z3(r, s):
    # 2x2 hermitian probe P=[[a,b],[b,c]] real; find a,b,c s.t. tr(P r)!=tr(P s)
    sol = z3.Solver()
    a,b,c = z3.Reals('a b c')
    tr_r = a*r[0,0] + 2*b*r[1,0] + c*r[1,1]
    tr_s = a*s[0,0] + 2*b*s[1,0] + c*s[1,1]
    sol.add(tr_r != tr_s)
    return sol.check() == z3.sat

def run_positive_tests():
    rho = np.array([[0.7,0.1],[0.1,0.3]]); sig = np.array([[0.3,0.0],[0.0,0.7]])
    found = probe_distinguishes_z3(rho, sig)
    return {"distinct_mixed_have_probe": found}

def run_negative_tests():
    rho = np.array([[0.5,0.2],[0.2,0.5]]); sig = rho.copy()
    found = probe_distinguishes_z3(rho, sig)
    return {"identical_have_no_probe": not found}

def run_boundary_tests():
    eps = 1e-9
    rho = np.array([[0.5,0.0],[0.0,0.5]]); sig = np.array([[0.5+eps,0.0],[0.0,0.5-eps]])
    found = probe_distinguishes_z3(rho, sig)
    return {"near_identical_probe_found": found}

if __name__ == "__main__":
    pos=run_positive_tests(); neg=run_negative_tests(); bnd=run_boundary_tests()
    all_pass = all(list(pos.values())+list(neg.values())+list(bnd.values()))
    r = {"name":"lego_03_identity_via_indistinguishability_mixed","classification":"canonical",
         "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
         "positive":pos,"negative":neg,"boundary":bnd,"overall_pass":bool(all_pass)}
    od = os.path.join(os.path.dirname(__file__),"a2_state","sim_results"); os.makedirs(od,exist_ok=True)
    p = os.path.join(od,"lego_03_identity_via_indistinguishability_mixed_results.json")
    with open(p,"w") as f: json.dump(r,f,indent=2,default=str)
    print(p,"overall_pass=",all_pass)
