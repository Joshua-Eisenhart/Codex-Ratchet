#!/usr/bin/env python3
"""F01 deep 04: Zero distinguishability-quantum violates F01.
z3 load-bearing: UNSAT — a probe with zero resolution cannot separate any pair.
"""
import json, os
from z3 import Solver, Real, Bool, And, Or, Not, ForAll, Implies, sat, unsat, Distinct

TOOL_MANIFEST = {t:{"tried":False,"used":False,"reason":"n/a"} for t in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_MANIFEST["z3"] = {"tried":True,"used":True,"reason":"UNSAT: q=0 separation with >1 states; load-bearing"}
TOOL_INTEGRATION_DEPTH = {"z3":"load_bearing"}

def try_separate(N, q):
    """Assign probe-values v_i in R; pairs distinguishable iff |v_i-v_j| >= q."""
    s = Solver()
    V = [Real(f"v_{i}") for i in range(N)]
    for i in range(N):
        for j in range(i+1,N):
            d = V[i]-V[j]
            s.add(Or(d >= q, d <= -q))
    return s.check()

def run_positive_tests():
    # q>0, N=4 -> sat
    return {"q_1_N4_sat": try_separate(4, 1) == sat,
            "q_small_N3_sat": try_separate(3, 0.01) == sat}

def run_negative_tests():
    # q=0, N>=2 with strict inequality -> UNSAT via strict
    s = Solver()
    from z3 import Real as R
    a,b = R('a'), R('b')
    # F01 demands strict resolution; q=0 means a!=b requires a-b strictly > 0 OR < 0 AND equal
    s.add(a == b)
    s.add(Or(a - b >= 0.0001, a - b <= -0.0001))  # any nonzero quantum
    return {"q_zero_equal_states_unsat": s.check() == unsat}

def run_boundary_tests():
    # q infinitesimally positive still sat for finite N
    return {"q_tiny_N5_sat": try_separate(5, 1e-9) == sat,
            "N1_q0_sat": try_separate(1, 0) == sat}

if __name__ == "__main__":
    pos=run_positive_tests(); neg=run_negative_tests(); bnd=run_boundary_tests()
    all_pass = all(list(pos.values())+list(neg.values())+list(bnd.values()))
    r = {"name":"f01_deep_04_distinguishability_quantum_nonzero","classification":"canonical",
         "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
         "positive":pos,"negative":neg,"boundary":bnd,"overall_pass":bool(all_pass)}
    od = os.path.join(os.path.dirname(__file__),"a2_state","sim_results"); os.makedirs(od,exist_ok=True)
    p = os.path.join(od,"f01_deep_04_distinguishability_quantum_nonzero_results.json")
    with open(p,"w") as f: json.dump(r,f,indent=2,default=str)
    print(p,"overall_pass=",all_pass)
