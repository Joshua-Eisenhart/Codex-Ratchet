#!/usr/bin/env python3
"""
Strongly-connected components on a directed admissibility graph.
rustworkx Tarjan SCC is load-bearing.
Ablation: numpy reachability matrix (A | A^2 | ... | A^n) intersected with transpose.
"""
import json, os, time
import numpy as np
import rustworkx as rx

TOOL_MANIFEST = {
    "rustworkx": {"tried": True, "used": True,
                  "reason": "Tarjan SCC on PyDiGraph — load-bearing; networkx equivalent exists but we exercise rustworkx's typed DiGraph for downstream integration"},
    "numpy": {"tried": True, "used": True, "reason": "reachability-matrix ablation"},
}
TOOL_INTEGRATION_DEPTH = {"rustworkx": "load_bearing", "numpy": "supportive"}

def build_admissibility_graph():
    """
    10 admissibility states. Edges = 'transition survives constraint probe'.
    Designed with three known SCCs: {0,1,2}, {3,4,5,6}, {7,8,9}
    plus one-way bridges 2->3 and 6->7 (no backflow).
    """
    g = rx.PyDiGraph()
    for _ in range(10): g.add_node(None)
    cycles = [[0,1,2,0],[3,4,5,6,3],[7,8,9,7]]
    for c in cycles:
        for i in range(len(c)-1):
            g.add_edge(c[i], c[i+1], 1)
    g.add_edge(2,3,1); g.add_edge(6,7,1)
    g.add_edge(4,6,1); g.add_edge(8,7,1)
    return g

def scc_numpy_ablation(g):
    n = len(g)
    A = np.zeros((n,n), dtype=bool)
    for (u,v) in g.edge_list(): A[u,v] = True
    R = np.eye(n, dtype=bool) | A
    for _ in range(n):
        R = R | (R @ R)
    mutual = R & R.T
    seen = [False]*n; comps = []
    for i in range(n):
        if seen[i]: continue
        c = [j for j in range(n) if mutual[i,j]]
        for j in c: seen[j] = True
        comps.append(sorted(c))
    return sorted(comps)

def run_positive_tests():
    g = build_admissibility_graph()
    sccs = [sorted(list(c)) for c in rx.strongly_connected_components(g)]
    sccs.sort()
    expected = [[0,1,2],[3,4,5,6],[7,8,9]]
    return {
        "n_sccs": len(sccs),
        "sccs": sccs,
        "expected": expected,
        "pass": sccs == expected,
    }

def run_negative_tests():
    # DAG (no cycles) — every node is its own SCC
    g = rx.PyDiGraph()
    for _ in range(6): g.add_node(None)
    for u,v in [(0,1),(1,2),(2,3),(3,4),(4,5)]: g.add_edge(u,v,1)
    sccs = [sorted(list(c)) for c in rx.strongly_connected_components(g)]
    return {
        "n_sccs": len(sccs),
        "expected": 6,
        "pass": len(sccs) == 6 and all(len(c)==1 for c in sccs),
    }

def run_boundary_tests():
    g = build_admissibility_graph()
    t0=time.time()
    rx_sccs = sorted([sorted(list(c)) for c in rx.strongly_connected_components(g)])
    t_rx = time.time()-t0
    t0=time.time()
    np_sccs = scc_numpy_ablation(g)
    t_np = time.time()-t0
    return {
        "rx_sccs": rx_sccs, "np_sccs": np_sccs,
        "agree": rx_sccs == np_sccs,
        "t_rx_s": t_rx, "t_np_s": t_np,
    }

if __name__ == "__main__":
    results = {
        "name": "rustworkx_scc_admissibility",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "rustworkx_scc_admissibility_results.json")
    with open(out,"w") as f: json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out}")
    print(json.dumps(results["positive"], indent=2))
