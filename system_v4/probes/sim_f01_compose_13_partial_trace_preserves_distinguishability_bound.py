#!/usr/bin/env python3
"""F01 compose 13: Partial trace reduces distinguishability (data-processing): F(Tr_B rho, Tr_B sigma) >= F(rho,sigma).
sympy load-bearing: symbolic trace-norm contraction on example.
"""
import json, os, sympy as sp

TOOL_MANIFEST = {t:{"tried":False,"used":False,"reason":"n/a"} for t in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_MANIFEST["sympy"] = {"tried":True,"used":True,"reason":"symbolic partial trace and 1-norm; load-bearing"}
TOOL_INTEGRATION_DEPTH = {"sympy":"load_bearing"}

def partial_trace_B(M, dA, dB):
    # Trace out B: result dA x dA
    out = sp.zeros(dA, dA)
    for i in range(dA):
        for j in range(dA):
            acc = 0
            for k in range(dB):
                acc += M[i*dB+k, j*dB+k]
            out[i,j] = acc
    return out

def trace_norm(M):
    # 1-norm = sum |eigenvalues| for Hermitian
    evs = list(M.eigenvals().keys())
    return sum(sp.Abs(e) for e in evs)

def run_positive_tests():
    # rho = |00><00|, sigma = |01><01| distinguishable on AB; traced to A both become |0><0| — indistinguishable
    rho = sp.zeros(4,4); rho[0,0]=1
    sig = sp.zeros(4,4); sig[1,1]=1
    d_full = trace_norm(rho - sig)
    rA = partial_trace_B(rho,2,2); sA = partial_trace_B(sig,2,2)
    d_reduced = trace_norm(rA - sA)
    return {"full_distinguishable": d_full == 2,
            "reduced_indistinguishable": d_reduced == 0,
            "data_processing": d_reduced <= d_full}

def run_negative_tests():
    # rho=|00><00|, sigma=|11><11|: full distinguishable, reduced also distinguishable
    rho = sp.zeros(4,4); rho[0,0]=1
    sig = sp.zeros(4,4); sig[3,3]=1
    rA = partial_trace_B(rho,2,2); sA = partial_trace_B(sig,2,2)
    d_reduced = trace_norm(rA - sA)
    return {"reduced_still_distinguishable": d_reduced == 2}

def run_boundary_tests():
    # rho=sigma -> both distances 0
    rho = sp.zeros(4,4); rho[0,0]=1
    d_full = trace_norm(rho - rho)
    rA = partial_trace_B(rho,2,2)
    d_reduced = trace_norm(rA - rA)
    return {"identical_zero_distance": d_full == 0 and d_reduced == 0}

if __name__ == "__main__":
    pos=run_positive_tests(); neg=run_negative_tests(); bnd=run_boundary_tests()
    all_pass = all(list(pos.values())+list(neg.values())+list(bnd.values()))
    r = {"name":"f01_compose_13_partial_trace_preserves_distinguishability_bound","classification":"canonical",
         "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
         "positive":pos,"negative":neg,"boundary":bnd,"overall_pass":bool(all_pass)}
    od = os.path.join(os.path.dirname(__file__),"a2_state","sim_results"); os.makedirs(od,exist_ok=True)
    p = os.path.join(od,"f01_compose_13_partial_trace_preserves_distinguishability_bound_results.json")
    with open(p,"w") as f: json.dump(r,f,indent=2,default=str)
    print(p,"overall_pass=",all_pass)
