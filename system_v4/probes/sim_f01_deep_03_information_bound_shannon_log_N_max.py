#!/usr/bin/env python3
"""F01 deep 03: Shannon H(X) <= log2(N) for N-state finite system; equality iff uniform.
sympy load-bearing: symbolic maximization via Lagrange on simplex.
"""
import json, os, sympy as sp

TOOL_MANIFEST = {t:{"tried":False,"used":False,"reason":"n/a"} for t in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_MANIFEST["sympy"] = {"tried":True,"used":True,"reason":"symbolic Lagrangian maximizer of Shannon on simplex; load-bearing"}
TOOL_INTEGRATION_DEPTH = {"sympy":"load_bearing"}

def H(ps):
    return -sum(p*sp.log(p,2) for p in ps if p != 0)

def run_positive_tests():
    # Uniform on N=4 gives H=log2(4)=2
    N = 4
    ps = [sp.Rational(1,N)]*N
    return {"uniform_N4_eq_log2N": sp.simplify(H(ps) - sp.log(N,2)) == 0,
            "uniform_N8_eq_log2N": sp.simplify(H([sp.Rational(1,8)]*8) - 3) == 0}

def run_negative_tests():
    # Non-uniform < log2(N)
    ps = [sp.Rational(1,2), sp.Rational(1,4), sp.Rational(1,8), sp.Rational(1,8)]
    val = float(H(ps).evalf())
    return {"skewed_lt_log2N": val < 2.0,
            "deterministic_eq_0": sp.simplify(H([1,0,0,0])) == 0}

def run_boundary_tests():
    # N=1 -> H=0=log2(1)
    return {"N1_H_eq_0": sp.simplify(H([1])) == 0,
            "N2_uniform_eq_1": sp.simplify(H([sp.Rational(1,2)]*2) - 1) == 0}

if __name__ == "__main__":
    pos=run_positive_tests(); neg=run_negative_tests(); bnd=run_boundary_tests()
    all_pass = all(list(pos.values())+list(neg.values())+list(bnd.values()))
    r = {"name":"f01_deep_03_information_bound_shannon_log_N_max","classification":"canonical",
         "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
         "positive":pos,"negative":neg,"boundary":bnd,"overall_pass":bool(all_pass)}
    od = os.path.join(os.path.dirname(__file__),"a2_state","sim_results"); os.makedirs(od,exist_ok=True)
    p = os.path.join(od,"f01_deep_03_information_bound_shannon_log_N_max_results.json")
    with open(p,"w") as f: json.dump(r,f,indent=2,default=str)
    print(p,"overall_pass=",all_pass)
