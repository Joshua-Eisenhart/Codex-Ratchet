#!/usr/bin/env python3
"""F01 deep 01: k < log2(N) binary probes cannot distinguish N states.
z3 load-bearing: UNSAT proves exclusion for N=8,k=2.
"""
import json, os
from z3 import Solver, BitVec, Distinct, Extract, ForAll, Implies, sat, unsat, Function, IntSort, BitVecSort, Bool, Bools, And, Or, Not

TOOL_MANIFEST = {t:{"tried":False,"used":False,"reason":"n/a"} for t in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_MANIFEST["z3"] = {"tried":True,"used":True,"reason":"UNSAT: no 2 binary probes separate 8 states; load-bearing"}
TOOL_INTEGRATION_DEPTH = {"z3":"load_bearing"}

def probes_separate(N, k):
    # Encode: for each state i in [0,N) and probe j in [0,k), value p[i][j] in {0,1}.
    # Require all N states to have distinct probe-vectors.
    s = Solver()
    P = [[Bool(f"p_{i}_{j}") for j in range(k)] for i in range(N)]
    # Distinct codewords: for each pair, at least one bit differs
    for i in range(N):
        for i2 in range(i+1, N):
            s.add(Or([P[i][j] != P[i2][j] for j in range(k)]))
    return s.check()

def run_positive_tests():
    # k = log2(N) should be satisfiable
    return {"N8_k3_sat": probes_separate(8,3) == sat,
            "N4_k2_sat": probes_separate(4,2) == sat}

def run_negative_tests():
    # k < log2(N) -> UNSAT
    return {"N8_k2_unsat": probes_separate(8,2) == unsat,
            "N4_k1_unsat": probes_separate(4,1) == unsat,
            "N16_k3_unsat": probes_separate(16,3) == unsat}

def run_boundary_tests():
    # N=1 always sat with k=0
    return {"N1_k0_sat": probes_separate(1,0) == sat,
            "N2_k1_sat": probes_separate(2,1) == sat,
            "N2_k0_unsat": probes_separate(2,0) == unsat}

if __name__ == "__main__":
    pos=run_positive_tests(); neg=run_negative_tests(); bnd=run_boundary_tests()
    all_pass = all(list(pos.values())+list(neg.values())+list(bnd.values()))
    r = {"name":"f01_deep_01_probe_size_lower_bound_log2_N","classification":"canonical",
         "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
         "positive":pos,"negative":neg,"boundary":bnd,"overall_pass":bool(all_pass)}
    od = os.path.join(os.path.dirname(__file__),"a2_state","sim_results"); os.makedirs(od,exist_ok=True)
    p = os.path.join(od,"f01_deep_01_probe_size_lower_bound_log2_N_results.json")
    with open(p,"w") as f: json.dump(r,f,indent=2,default=str)
    print(p,"overall_pass=",all_pass)
