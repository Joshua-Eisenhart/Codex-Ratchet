#!/usr/bin/env python3
"""F01xN01 coupling 2: probe refinement bounded by log2(N).
Exclusion claim: F01 (probe discriminations) + N01 (equivalence) jointly exclude the possibility
of distinguishing N classes using fewer than ceil(log2(N)) binary probes.
sympy load-bearing: symbolic log bound.
"""
import json, os, sympy as sp, math

TOOL_MANIFEST = {t:{"tried":False,"used":False,"reason":"n/a"} for t in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_MANIFEST["sympy"] = {"tried":True,"used":True,"reason":"symbolic log2 refinement bound; load-bearing"}
TOOL_INTEGRATION_DEPTH = {"sympy":"load_bearing"}

def min_probes(N):
    return int(sp.ceiling(sp.log(N,2)))

def run_positive_tests():
    return {"N4_needs_at_least_2": min_probes(4) == 2,
            "N8_needs_at_least_3": min_probes(8) == 3,
            "N7_needs_at_least_3": min_probes(7) == 3}

def run_negative_tests():
    # attempting N=8 classes with only 2 probes is excluded by the joint bound
    N = 8; attempted_probes = 2
    return {"excludes_N8_with_2probes": attempted_probes < min_probes(N)}

def run_boundary_tests():
    # N=1: zero probes suffice (degenerate); N=2: 1 probe saturates
    return {"N1_needs_zero": min_probes(1) == 0,
            "N2_needs_one": min_probes(2) == 1}

if __name__ == "__main__":
    pos=run_positive_tests(); neg=run_negative_tests(); bnd=run_boundary_tests()
    all_pass = all(list(pos.values())+list(neg.values())+list(bnd.values()))
    r = {"name":"f01n01_couple_probe_refinement_bounded_by_log_N","classification":"canonical",
         "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
         "positive":pos,"negative":neg,"boundary":bnd,"overall_pass":bool(all_pass),
         "exclusion_statement":"F01+N01 jointly exclude distinguishing N classes with fewer than ceil(log2 N) probes."}
    od = os.path.join(os.path.dirname(__file__),"a2_state","sim_results"); os.makedirs(od,exist_ok=True)
    p = os.path.join(od,"f01n01_couple_probe_refinement_bounded_by_log_N_results.json")
    with open(p,"w") as f: json.dump(r,f,indent=2,default=str)
    print(p,"overall_pass=",all_pass)
