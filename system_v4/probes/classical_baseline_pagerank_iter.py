#!/usr/bin/env python3
"""classical_baseline_pagerank_iter.py -- non-canon, lane_B-eligible
Generated classical baseline. numpy load_bearing. pos/neg/boundary all required PASS.
"""
import json, os, numpy as np

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed for classical baseline"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not a proof sim"},
    "cvc5": {"tried": False, "used": False, "reason": "not a proof sim"},
    "sympy": {"tried": False, "used": False, "reason": "numeric only"},
    "clifford": {"tried": False, "used": False, "reason": "no geometric algebra here"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold here"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariance"},
    "rustworkx": {"tried": False, "used": False, "reason": "numpy sufficient"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistence"},
    "numpy": {"tried": True, "used": True, "reason": "load-bearing numeric core for pagerank_iter"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing"}


def _pagerank(A, d=0.85, tol=1e-8, maxit=500):
    N=A.shape[0]
    out=A.sum(axis=1); out[out==0]=1
    M=(A/out[:,None]).T
    r=np.ones(N)/N
    for _ in range(maxit):
        r_new=(1-d)/N + d*M@r
        if np.linalg.norm(r_new-r,1)<tol: return r_new
        r=r_new
    return r

def run_positive_tests():
    A=np.array([[0,1,1],[0,0,1],[1,0,0]],float)
    r=_pagerank(A)
    return {"sums_to_one": bool(abs(r.sum()-1)<1e-6), "all_positive": bool(np.all(r>0))}

def run_negative_tests():
    # uniform ring: all ranks equal
    A=np.array([[0,1,0],[0,0,1],[1,0,0]],float)
    r=_pagerank(A)
    return {"ring_equal": bool(np.allclose(r, r[0], atol=1e-4))}

def run_boundary_tests():
    # Two-node mutual link graph: equal ranks summing to 1
    A=np.array([[0,1],[1,0]],float)
    r=_pagerank(A)
    return {"two_node_equal_half": bool(abs(r[0]-0.5)<1e-6 and abs(r[1]-0.5)<1e-6)}


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(v for v in list(pos.values())+list(neg.values())+list(bnd.values()))
    results = {
        "name": "classical_baseline_pagerank_iter",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": bool(all_pass),
        "classification": "classical_baseline",
        "lane": "lane_B",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_pagerank_iter_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if all_pass else 'FAIL'} pagerank_iter -> {out_path}")
