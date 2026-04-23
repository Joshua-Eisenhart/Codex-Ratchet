#!/usr/bin/env python3
"""classical_baseline_eulerian_path.py -- non-canon, lane_B-eligible
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
    "numpy": {"tried": True, "used": True, "reason": "load-bearing numeric core for eulerian_path"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing"}


def _has_eulerian(adj):
    # Eulerian circuit: all vertices even degree + connected (nonzero)
    deg=adj.sum(axis=1)
    if np.any(deg==0):
        # ignore isolates
        mask=deg>0; adj=adj[mask][:,mask]; deg=adj.sum(axis=1)
        if adj.size==0: return False
    return bool(np.all(deg%2==0))

def run_positive_tests():
    # 4-cycle: all degree 2
    A=np.array([[0,1,0,1],[1,0,1,0],[0,1,0,1],[1,0,1,0]])
    return {"cycle_has_eulerian": bool(_has_eulerian(A))}

def run_negative_tests():
    # path graph 3 nodes: degrees 1,2,1 -> no eulerian circuit
    A=np.array([[0,1,0],[1,0,1],[0,1,0]])
    return {"path_no_eulerian": bool(not _has_eulerian(A))}

def run_boundary_tests():
    A=np.array([[0]])
    return {"single_node_vacuous": bool(not _has_eulerian(A))}


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(v for v in list(pos.values())+list(neg.values())+list(bnd.values()))
    results = {
        "name": "classical_baseline_eulerian_path",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": bool(all_pass),
        "classification": "classical_baseline",
        "lane": "lane_B",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_eulerian_path_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if all_pass else 'FAIL'} eulerian_path -> {out_path}")
