#!/usr/bin/env python3
"""
sim_capability_igraph_isolated.py
igraph isolated capability probe.
Isolates and characterizes fast graph algorithms via the igraph library.
classification = "classical_baseline"
"""

import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST -- 12 standard tools, all not-used (isolation probe)
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "not used: this probe isolates igraph graph algorithm capability; tensor operations are handled in dedicated integration sims per four-sim-kinds doctrine"},
    "pyg":       {"tried": False, "used": False, "reason": "not used: this probe isolates igraph graph algorithm capability; PyG graph-neural message passing is a separate concern deferred to integration sims per four-sim-kinds doctrine"},
    "z3":        {"tried": False, "used": False, "reason": "not used: this probe isolates igraph graph algorithm capability; logical constraint verification over graph properties deferred to integration sims per four-sim-kinds doctrine"},
    "cvc5":      {"tried": False, "used": False, "reason": "not used: this probe isolates igraph graph algorithm capability; formal SMT proof checking deferred to integration sims per four-sim-kinds doctrine"},
    "sympy":     {"tried": False, "used": False, "reason": "not used: this probe isolates igraph graph algorithm capability; symbolic analysis of graph invariants deferred to integration sims per four-sim-kinds doctrine"},
    "clifford":  {"tried": False, "used": False, "reason": "not used: this probe isolates igraph graph algorithm capability; geometric algebra coupling over graph structures deferred to integration sims per four-sim-kinds doctrine"},
    "geomstats": {"tried": False, "used": False, "reason": "not used: this probe isolates igraph graph algorithm capability; Riemannian manifold graph embedding deferred to integration sims per four-sim-kinds doctrine"},
    "e3nn":      {"tried": False, "used": False, "reason": "not used: this probe isolates igraph graph algorithm capability; equivariant network coupling deferred to integration sims per four-sim-kinds doctrine"},
    "rustworkx": {"tried": False, "used": False, "reason": "not used: this probe isolates igraph graph algorithm capability; rustworkx cross-validation is handled in the dedicated networkx-rustworkx crosscheck sim"},
    "xgi":       {"tried": False, "used": False, "reason": "not used: this probe isolates igraph graph algorithm capability; igraph handles pairwise edges while xgi handles hyperedges, deferred to integration sim"},
    "toponetx":  {"tried": False, "used": False, "reason": "not used: this probe isolates igraph graph algorithm capability; topological complex operations are out of scope for this isolation probe"},
    "gudhi":     {"tried": False, "used": False, "reason": "not used: this probe isolates igraph graph algorithm capability; persistent homology over graph filtrations deferred to integration sims per four-sim-kinds doctrine"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None,
    "sympy": None, "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

TARGET_TOOL = {
    "name": "igraph",
    "import": "import igraph as ig; ig.Graph",
    "role": "load_bearing",
    "can": [
        "fast C-backed graph algorithms for shortest paths, community detection, centrality",
        "directed and undirected graphs with weighted edges and vertex/edge attributes",
        "community detection via Leiden, Louvain, and multilevel algorithms",
        "large graph processing significantly faster than networkx for algorithmic tasks",
    ],
    "cannot": [
        "perform tensor operations (use pytorch for that)",
        "represent hyperedges natively (use xgi for that)",
        "represent topological complexes such as simplicial or cell complexes (use toponetx)",
        "guarantee globally optimal community structure (NP-hard in general)",
    ],
}

import igraph as ig


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # Positive 1: weighted shortest path on directed graph
    # Graph: 0→1:1, 1→2:1, 2→3:1, 0→3:5
    # Shortest path 0→3 = [0,1,2,3] with total weight 3
    g = ig.Graph(n=4, directed=True)
    g.add_edges([(0, 1), (1, 2), (2, 3), (0, 3)])
    g.es["weight"] = [1.0, 1.0, 1.0, 5.0]

    paths = g.get_shortest_paths(0, to=3, weights="weight", output="vpath")
    path = paths[0] if paths else []

    path_weights = g.distances(source=0, target=3, weights="weight")
    total_weight = float(path_weights[0][0]) if path_weights else None

    pass_path = (path == [0, 1, 2, 3])
    pass_weight = (total_weight is not None and abs(total_weight - 3.0) < 1e-9)

    results["positive_weighted_shortest_path"] = {
        "path_found": path,
        "expected_path": [0, 1, 2, 3],
        "total_weight": total_weight,
        "expected_weight": 3.0,
        "pass_path": pass_path,
        "pass_weight": pass_weight,
        "pass": pass_path and pass_weight,
    }

    # Positive 2: community detection on karate-like graph
    # Use the built-in Zachary karate club graph
    karate = ig.Graph.Famous("Petersen")  # 10-node symmetric graph for reproducibility
    # Use find_community_multilevel (Louvain-style)
    communities = karate.community_multilevel()
    n_communities = len(communities)
    pass_communities = n_communities >= 2

    results["positive_community_detection"] = {
        "graph": "Petersen (10 nodes, 15 edges)",
        "n_communities_found": n_communities,
        "community_sizes": [len(c) for c in communities],
        "pass_at_least_2": pass_communities,
        "pass": pass_communities,
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # Negative: disconnected graph, shortest path returns empty list
    g_disconnected = ig.Graph(n=4, directed=False)
    g_disconnected.add_edges([(0, 1), (2, 3)])  # two disconnected components

    paths = g_disconnected.get_shortest_paths(0, to=3, output="vpath")
    path = paths[0] if paths else []
    is_empty = (len(path) == 0)

    results["negative_disconnected_path"] = {
        "path_found": path,
        "expected": "empty list (no path between disconnected nodes)",
        "is_empty": is_empty,
        "pass": is_empty,
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # Boundary: self-loop — igraph handles without error
    g_loop = ig.Graph(n=3, directed=True)
    g_loop.add_edges([(0, 0), (0, 1), (1, 2)])  # self-loop on node 0
    g_loop.es["weight"] = [0.0, 1.0, 1.0]

    error_msg = None
    completed = False
    n_edges = 0
    try:
        n_edges = g_loop.ecount()
        completed = True
    except Exception as e:
        error_msg = str(e)

    has_self_loop = g_loop.is_loop().count(True) > 0

    results["boundary_self_loop"] = {
        "n_edges": n_edges,
        "has_self_loop": has_self_loop,
        "completed_without_error": completed,
        "error": error_msg,
        "pass": completed and has_self_loop,
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_pass = (
        pos["positive_weighted_shortest_path"]["pass"]
        and pos["positive_community_detection"]["pass"]
        and neg["negative_disconnected_path"]["pass"]
        and bnd["boundary_self_loop"]["pass"]
    )

    results = {
        "name": "sim_capability_igraph_isolated",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "target_tool": TARGET_TOOL,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "overall_pass": all_pass,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_capability_igraph_isolated_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass: {all_pass}")
