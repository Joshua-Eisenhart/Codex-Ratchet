#!/usr/bin/env python3
"""
All-pairs shortest path on a weighted constraint-manifold skeleton.
30-node weighted directed graph representing a constraint skeleton.
rustworkx all_pairs_dijkstra_path_lengths — load-bearing (Rust backend, strict typed weights).
Ablation: naive numpy Floyd-Warshall O(n^3) loop.
"""
import json, os, time, math
import numpy as np
import rustworkx as rx

TOOL_MANIFEST = {
    "rustworkx": {"tried": True, "used": True,
                  "reason": "all_pairs_dijkstra_path_lengths with edge_cost_fn — load-bearing typed-weight APSP"},
    "numpy": {"tried": True, "used": True, "reason": "Floyd-Warshall ablation"},
}
TOOL_INTEGRATION_DEPTH = {"rustworkx": "load_bearing", "numpy": "supportive"}

def build_skeleton(n=30, seed=7):
    import random
    rng = random.Random(seed)
    g = rx.PyDiGraph()
    for _ in range(n): g.add_node(None)
    # backbone path
    for i in range(n-1):
        g.add_edge(i, i+1, float(1 + rng.random()))
    # cross-chords
    for _ in range(40):
        u = rng.randrange(n); v = rng.randrange(n)
        if u != v:
            g.add_edge(u, v, float(0.5 + 3*rng.random()))
    return g

def apsp_floyd_warshall(g):
    n = len(g)
    INF = math.inf
    D = np.full((n,n), INF)
    for i in range(n): D[i,i] = 0.0
    for (u,v) in g.edge_list():
        w = g.get_edge_data(u,v)
        if w < D[u,v]: D[u,v] = w
    for k in range(n):
        D = np.minimum(D, D[:,k:k+1] + D[k:k+1,:])
    return D

def apsp_rx(g):
    d = rx.all_pairs_dijkstra_path_lengths(g, edge_cost_fn=lambda w: w)
    n = len(g)
    D = np.full((n,n), math.inf)
    for s, targets in d.items():
        D[s,s] = 0.0
        for t, length in targets.items():
            D[s,t] = length
    return D

def run_positive_tests():
    g = build_skeleton()
    D = apsp_rx(g)
    # self-distance zero
    self_zero = bool(np.all(np.diag(D) == 0.0))
    # triangle inequality: D[i,k] <= D[i,j] + D[j,k] for all finite triples
    finite = np.isfinite(D)
    violations = 0
    n = len(g)
    for i in range(n):
        for j in range(n):
            if not finite[i,j]: continue
            for k in range(n):
                if finite[j,k] and finite[i,k]:
                    if D[i,k] > D[i,j] + D[j,k] + 1e-9:
                        violations += 1
    # backbone path 0->n-1 must be finite
    backbone_reachable = math.isfinite(D[0, n-1])
    return {
        "n_nodes": n,
        "n_edges": len(g.edge_list()),
        "self_distance_zero": self_zero,
        "triangle_violations": violations,
        "backbone_reachable": backbone_reachable,
        "backbone_distance": float(D[0, n-1]),
        "pass": self_zero and violations == 0 and backbone_reachable,
    }

def run_negative_tests():
    # Isolated node at index n must have infinite distance to everyone else
    g = build_skeleton(n=20)
    g.add_node(None)  # index 20 — no edges
    D = apsp_rx(g)
    iso_inf = bool(np.all(np.isinf(D[20, :20])))
    return {
        "isolated_node_unreachable": iso_inf,
        "pass": iso_inf,
    }

def run_boundary_tests():
    g = build_skeleton()
    t0 = time.time(); D_rx = apsp_rx(g); t_rx = time.time()-t0
    t0 = time.time(); D_fw = apsp_floyd_warshall(g); t_fw = time.time()-t0
    # compare finite entries
    mask = np.isfinite(D_rx) & np.isfinite(D_fw)
    agree = bool(np.allclose(D_rx[mask], D_fw[mask], atol=1e-9))
    # unreachable pairs must match
    inf_agree = bool(np.array_equal(np.isinf(D_rx), np.isinf(D_fw)))
    return {
        "t_rx_dijkstra_s": t_rx,
        "t_numpy_floyd_s": t_fw,
        "finite_entries_agree": agree,
        "infinite_mask_agree": inf_agree,
        "pass": agree and inf_agree,
    }

if __name__ == "__main__":
    results = {
        "name": "rustworkx_apsp_constraint_skeleton",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "rustworkx_apsp_constraint_skeleton_results.json")
    with open(out,"w") as f: json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out}")
    print(json.dumps(results["positive"], indent=2))
