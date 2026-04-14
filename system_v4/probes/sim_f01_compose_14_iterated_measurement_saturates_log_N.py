#!/usr/bin/env python3
"""F01 compose 14: Iterated binary measurements saturate log2(N) — k=log2(N) suffices, k<log2(N) doesn't.
z3 load-bearing: UNSAT exclusion at k=log2(N)-1.
"""
import json, os
from z3 import Solver, Bool, Or, sat, unsat

TOOL_MANIFEST = {t:{"tried":False,"used":False,"reason":"n/a"} for t in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_MANIFEST["z3"] = {"tried":True,"used":True,"reason":"saturation at log2(N) binary probes; load-bearing"}
TOOL_INTEGRATION_DEPTH = {"z3":"load_bearing"}

def separable(N,k):
    s = Solver()
    P = [[Bool(f"p_{i}_{j}") for j in range(k)] for i in range(N)]
    for i in range(N):
        for j in range(i+1,N):
            s.add(Or([P[i][b] != P[j][b] for b in range(k)]))
    return s.check()

def run_positive_tests():
    # Saturation: k=log2(N) works
    return {"N2_k1_sat": separable(2,1) == sat,
            "N4_k2_sat": separable(4,2) == sat,
            "N16_k4_sat": separable(16,4) == sat}

def run_negative_tests():
    return {"N4_k1_unsat": separable(4,1) == unsat,
            "N16_k3_unsat": separable(16,3) == unsat}

def run_boundary_tests():
    # k=log2(N) exactly is tight — removing one probe fails
    return {"N8_k3_sat": separable(8,3) == sat,
            "N8_k2_unsat": separable(8,2) == unsat}

if __name__ == "__main__":
    pos=run_positive_tests(); neg=run_negative_tests(); bnd=run_boundary_tests()
    all_pass = all(list(pos.values())+list(neg.values())+list(bnd.values()))
    r = {"name":"f01_compose_14_iterated_measurement_saturates_log_N","classification":"canonical",
         "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
         "positive":pos,"negative":neg,"boundary":bnd,"overall_pass":bool(all_pass)}
    od = os.path.join(os.path.dirname(__file__),"a2_state","sim_results"); os.makedirs(od,exist_ok=True)
    p = os.path.join(od,"f01_compose_14_iterated_measurement_saturates_log_N_results.json")
    with open(p,"w") as f: json.dump(r,f,indent=2,default=str)
    print(p,"overall_pass=",all_pass)
