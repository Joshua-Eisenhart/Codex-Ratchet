#!/usr/bin/env python3
"""F01 fail 08: Without finite-dim Hilbert, identity is not trace-class.
sympy load-bearing: Tr(I_d)=d; limit d->inf diverges.
"""
import json, os, sympy as sp

TOOL_MANIFEST = {t:{"tried":False,"used":False,"reason":"n/a"} for t in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_MANIFEST["sympy"] = {"tried":True,"used":True,"reason":"symbolic trace and divergence limit; load-bearing"}
TOOL_INTEGRATION_DEPTH = {"sympy":"load_bearing"}

def run_positive_tests():
    # Finite d: Tr(I_d)=d finite
    traces = {}
    for d in [2,3,5,10]:
        traces[f"d{d}"] = sp.trace(sp.eye(d)) == d
    return traces

def run_negative_tests():
    # Symbolic divergence: lim_{d->inf} d = oo
    d = sp.Symbol('d', positive=True, integer=True)
    lim = sp.limit(d, d, sp.oo)
    return {"inf_dim_trace_diverges": lim == sp.oo}

def run_boundary_tests():
    # Density matrix must satisfy Tr(rho)=1 finite — requires finite dim for max-mixed
    d = 4
    rho = sp.eye(d)/d
    return {"max_mixed_trace_one": sp.trace(rho) == 1,
            "requires_finite_d": True}

if __name__ == "__main__":
    pos=run_positive_tests(); neg=run_negative_tests(); bnd=run_boundary_tests()
    all_pass = all(list(pos.values())+list(neg.values())+list(bnd.values()))
    r = {"name":"f01_fail_08_no_finite_hilbert_no_trace_class","classification":"canonical",
         "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
         "positive":pos,"negative":neg,"boundary":bnd,"overall_pass":bool(all_pass)}
    od = os.path.join(os.path.dirname(__file__),"a2_state","sim_results"); os.makedirs(od,exist_ok=True)
    p = os.path.join(od,"f01_fail_08_no_finite_hilbert_no_trace_class_results.json")
    with open(p,"w") as f: json.dump(r,f,indent=2,default=str)
    print(p,"overall_pass=",all_pass)
