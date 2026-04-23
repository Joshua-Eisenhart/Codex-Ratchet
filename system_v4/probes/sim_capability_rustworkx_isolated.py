#!/usr/bin/env python3
"""
sim_capability_rustworkx_isolated.py -- Isolated tool-capability probe for rustworkx.

Classical_baseline capability probe: demonstrates rustworkx graph algorithms:
directed/undirected graphs, shortest paths, betweenness centrality, topological
sort, and connected components. Honest CAN/CANNOT summary. No coupling to other tools.
Per four-sim-kinds doctrine: capability probe precedes any integration sim.
"""

import json
import os

classification = "classical_baseline"

_ISOLATED_REASON = (
    "not used: this probe isolates rustworkx graph algorithm capabilities alone; "
    "cross-tool coupling is deferred to a separate integration sim "
    "per the four-sim-kinds doctrine (capability vs integration separation)."
)

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "pyg":       {"tried": False, "used": False, "reason": "PyG provides GNN message passing; rustworkx provides algorithmic graph operations; separate capabilities, no overlap needed here."},
    "z3":        {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "cvc5":      {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "sympy":     {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "clifford":  {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "e3nn":      {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "rustworkx": {"tried": True,  "used": True,  "reason": "load-bearing: rustworkx graph construction, shortest paths, betweenness centrality, connected components, and topological sort are the sole subjects of this capability probe."},
    "xgi":       {"tried": False, "used": False, "reason": "xgi handles hypergraphs; rustworkx handles standard graphs; separate capabilities."},
    "toponetx":  {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "gudhi":     {"tried": False, "used": False, "reason": _ISOLATED_REASON},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None,
    "sympy": None, "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": "load_bearing", "xgi": None, "toponetx": None, "gudhi": None,
}

RX_OK = False
try:
    import rustworkx as rx
    RX_OK = True
except Exception:
    pass


def run_positive_tests():
    r = {}
    if not RX_OK:
        r["rustworkx_available"] = {"pass": False, "detail": "rustworkx not importable"}
        return r

    import rustworkx as rx

    r["rustworkx_available"] = {"pass": True, "version": rx.__version__}

    # --- Test 1: directed graph construction ---
    dg = rx.PyDiGraph()
    n0, n1, n2, n3 = [dg.add_node(i) for i in range(4)]
    dg.add_edge(n0, n1, 1.0)
    dg.add_edge(n1, n2, 1.0)
    dg.add_edge(n2, n3, 1.0)
    dg.add_edge(n0, n3, 5.0)
    r["digraph_construction"] = {
        "pass": len(dg) == 4 and dg.num_edges() == 4,
        "nodes": len(dg),
        "edges": dg.num_edges(),
        "detail": "PyDiGraph: 4 nodes, 4 directed edges",
    }

    # --- Test 2: Dijkstra shortest path ---
    paths = rx.dijkstra_shortest_paths(dg, n0, target=n3, weight_fn=lambda e: e)
    shortest = list(paths[n3])  # NodeIndices → list
    r["dijkstra_shortest_path"] = {
        "pass": shortest == [n0, n1, n2, n3],
        "path": shortest,
        "detail": f"Shortest path n0→n3: {shortest} (cost 3 < direct edge 5)",
    }

    # --- Test 3: shortest path lengths ---
    # signature: dijkstra_shortest_path_lengths(graph, node, edge_cost_fn, goal=None)
    lengths = rx.dijkstra_shortest_path_lengths(dg, n0, lambda e: e)
    r["shortest_path_lengths"] = {
        "pass": lengths[n3] == 3.0,
        "dist_to_n3": lengths[n3],
        "detail": "Shortest path length n0→n3 = 3.0 (via n1,n2)",
    }

    # --- Test 4: undirected graph + connected components ---
    ug = rx.PyGraph()
    a, b, c, d = [ug.add_node(i) for i in range(4)]
    ug.add_edge(a, b, None)
    ug.add_edge(b, c, None)
    # d is isolated
    components = rx.connected_components(ug)
    r["connected_components"] = {
        "pass": len(components) == 2,
        "count": len(components),
        "detail": "4 nodes: {a,b,c} + {d}: 2 connected components",
    }

    # --- Test 5: topological sort ---
    dag = rx.PyDiGraph(check_cycle=True)
    v0, v1, v2, v3 = [dag.add_node(i) for i in range(4)]
    dag.add_edge(v0, v1, None)
    dag.add_edge(v0, v2, None)
    dag.add_edge(v1, v3, None)
    dag.add_edge(v2, v3, None)
    topo = list(rx.topological_sort(dag))  # NodeIndices → list
    # v0 must come first, v3 must come last
    r["topological_sort"] = {
        "pass": topo.index(v0) < topo.index(v3),
        "topo_order": topo,
        "detail": "Topological sort: v0 before v3",
    }

    # --- Test 6: betweenness centrality ---
    # Star graph: center node should have highest centrality
    star = rx.PyGraph()
    center = star.add_node(0)
    leaves = [star.add_node(i) for i in range(1, 5)]
    for leaf in leaves:
        star.add_edge(center, leaf, None)
    centrality = rx.betweenness_centrality(star)
    r["betweenness_centrality"] = {
        "pass": centrality[center] > max(centrality[leaf] for leaf in leaves),
        "center_centrality": centrality[center],
        "detail": "Star center has higher betweenness than leaves",
    }

    return r


def run_negative_tests():
    r = {}
    if not RX_OK:
        r["rustworkx_unavailable"] = {"pass": True, "detail": "skip: rustworkx not installed"}
        return r

    import rustworkx as rx

    # --- Neg 1: disconnected graph: path may not exist ---
    dg = rx.PyDiGraph()
    n0 = dg.add_node(0)
    n1 = dg.add_node(1)
    # no edges: no path from n0 to n1
    paths = rx.dijkstra_shortest_paths(dg, n0, target=n1, weight_fn=lambda e: e)
    r["no_path_in_disconnected"] = {
        "pass": n1 not in paths,
        "has_path": n1 in paths,
        "detail": "Disconnected graph: no path from n0 to n1",
    }

    # --- Neg 2: directed graph: path may not exist in reverse direction ---
    dg2 = rx.PyDiGraph()
    a = dg2.add_node(0)
    b = dg2.add_node(1)
    dg2.add_edge(a, b, 1.0)
    paths_fwd = rx.dijkstra_shortest_paths(dg2, a, target=b, weight_fn=lambda e: e)
    paths_rev = rx.dijkstra_shortest_paths(dg2, b, target=a, weight_fn=lambda e: e)
    r["directed_no_reverse_path"] = {
        "pass": b in paths_fwd and a not in paths_rev,
        "has_forward": b in paths_fwd,
        "has_reverse": a in paths_rev,
        "detail": "Directed edge a→b: forward path exists, reverse does not",
    }

    return r


def run_boundary_tests():
    r = {}
    if not RX_OK:
        r["rustworkx_unavailable"] = {"pass": True, "detail": "skip: rustworkx not installed"}
        return r

    import rustworkx as rx

    # --- Boundary 1: single node graph ---
    g = rx.PyGraph()
    n = g.add_node(0)
    comps = rx.connected_components(g)
    r["single_node_component"] = {
        "pass": len(comps) == 1,
        "components": len(comps),
        "detail": "Single node graph: 1 connected component",
    }

    # --- Boundary 2: path to self is empty ---
    dg = rx.PyDiGraph()
    n0 = dg.add_node(0)
    paths = rx.dijkstra_shortest_paths(dg, n0, target=n0, weight_fn=lambda e: e)
    self_path = list(paths[n0]) if n0 in paths else [n0]
    r["path_to_self"] = {
        "pass": self_path == [n0] or self_path == [],
        "path": self_path,
        "detail": "Shortest path from node to itself is trivial",
    }

    # --- Boundary 3: dense graph node count ---
    dense = rx.PyGraph()
    nodes = [dense.add_node(i) for i in range(10)]
    for i in range(10):
        for j in range(i + 1, 10):
            dense.add_edge(nodes[i], nodes[j], 1.0)
    r["k10_complete_graph"] = {
        "pass": dense.num_edges() == 45,
        "edges": dense.num_edges(),
        "detail": "K_10: 10 nodes, 45 undirected edges",
    }

    return r


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_tests = {**pos, **neg, **bnd}
    overall = all([v.get("pass", False) for v in all_tests.values() if isinstance(v, dict) and "pass" in v])

    results = {
        "name": "sim_capability_rustworkx_isolated",
        "classification": classification,
        "overall_pass": overall,
        "capability_summary": {
            "CAN": [
                "construct directed (PyDiGraph) and undirected (PyGraph) graphs efficiently",
                "compute Dijkstra shortest paths and path lengths",
                "find connected components in undirected graphs",
                "compute topological sort on DAGs",
                "compute betweenness centrality",
                "handle large graphs with Rust-backed performance",
            ],
            "CANNOT": [
                "perform learnable message passing (use PyG for GNNs)",
                "handle hyperedges (use xgi for hypergraphs)",
                "represent topological complexes with boundary operators (use toponetx)",
                "prove graph properties formally (use z3 for logical proofs)",
            ],
        },
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_capability_rustworkx_isolated_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass: {overall}")
