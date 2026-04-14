#!/usr/bin/env python3
"""sim_cl3_reflection -- Reflection v -> -n v n (unit n) is length-preserving, involutive."""
import json, os, numpy as np

classification = "canonical"

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": r} for k,r in {
    "pytorch":"not needed","pyg":"no graph","z3":"numeric","cvc5":"numeric",
    "sympy":"not used","clifford":"load_bearing: sandwich product","geomstats":"not used",
    "e3nn":"not used","rustworkx":"no graph","xgi":"no hypergraph","toponetx":"no cells","gudhi":"no persistence",
}.items()}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

from clifford import Cl
TOOL_MANIFEST["clifford"].update(tried=True, used=True); TOOL_INTEGRATION_DEPTH["clifford"] = "load_bearing"

layout, blades = Cl(3)
e1, e2, e3 = blades['e1'], blades['e2'], blades['e3']

def reflect(v, n):
    return -n * v * n

def norm_sq(x):
    return float((x * ~x).value[0])

def close(a,b,tol=1e-10):
    return float(abs((a-b).value).max()) < tol

def run_positive_tests():
    r = {}
    v = 2*e1 + 3*e2 - e3
    n = e1  # reflect across plane perpendicular to e1
    w = reflect(v, n)
    # length preserved
    r["length_preserved"] = abs(norm_sq(v) - norm_sq(w)) < 1e-10
    # component parallel to n flips
    r["e1_flipped"] = abs(float(w.value[1]) - (-2.0)) < 1e-10  # e1 coefficient
    # involution: reflecting twice = identity
    r["involutive"] = close(reflect(w, n), v)
    return r

def run_negative_tests():
    r = {}
    v = e1 + e2
    n = e1
    w = reflect(v, n)
    r["w_neq_v"] = not close(w, v)
    # non-unit n breaks length preservation
    n2 = 2*e1
    w2 = reflect(v, n2)
    r["nonunit_breaks_length"] = abs(norm_sq(v) - norm_sq(w2)) > 1e-6
    return r

def run_boundary_tests():
    r = {}
    # reflect n across n itself -> -n
    n = e1
    r["reflect_n_is_minus_n"] = close(reflect(n, n), -n)
    # reflect vector perpendicular to n -> itself
    r["perp_preserved"] = close(reflect(e2, e1), e2)
    return r

def main():
    results = {"name":"sim_cl3_reflection","classification":classification,
               "positive":run_positive_tests(),"negative":run_negative_tests(),"boundary":run_boundary_tests(),
               "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH}
    ok = all(v for s in ("positive","negative","boundary") for v in results[s].values())
    results["pass"] = bool(ok)
    out = os.path.join(os.path.dirname(__file__),"results","sim_cl3_reflection.json")
    os.makedirs(os.path.dirname(out),exist_ok=True)
    with open(out,"w") as f: json.dump(results,f,indent=2,default=str)
    print(json.dumps({"pass":results["pass"],"out":out}))
    return 0 if ok else 1

if __name__=="__main__": raise SystemExit(main())
