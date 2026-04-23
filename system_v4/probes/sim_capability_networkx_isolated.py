#!/usr/bin/env python3
"""
sim_capability_networkx_isolated.py
networkx isolated capability probe.
Isolates and characterizes rich graph algorithm coverage via the networkx library.
classification = "classical_baseline"
"""

import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST -- 12 standard tools, all not-used (isolation probe)
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "not used: this probe isolates networkx graph algorithm capability; pytorch tensor operations are addressed in dedicated integration sims per four-sim-kinds doctrine"},
    "pyg":       {"tried": False, "used": False, "reason": "not used: this probe isolates networkx graph algorithm capability; PyG message-passing neural networks are a separate concern addressed in integration sims per four-sim-kinds doctrine"},
    "z3":        {"tried": False, "used": False, "reason": "not used: this probe isolates networkx graph algorithm capability; SMT constraint verification over graph properties deferred to integration sims per four-sim-kinds doctrine"},
    "cvc5":      {"tried": False, "used": False, "reason": "not used: this probe isolates networkx graph algorithm capability; cvc5 formal proof checking deferred to integration sims per four-sim-kinds doctrine"},
    "sympy":     {"tried": False, "used": False, "reason": "not used: this probe isolates networkx graph algorithm capability; symbolic verification of graph invariants deferred to integration sims per four-sim-kinds doctrine"},
    "clifford":  {"tried": False, "used": False, "reason": "not used: this probe isolates networkx graph algorithm capability; geometric algebra over graph structures deferred to integration sims per four-sim-kinds doctrine"},
    "geomstats": {"tried": False, "used": False, "reason": "not used: this probe isolates networkx graph algorithm capability; Riemannian geometry embedding deferred to integration sims per four-sim-kinds doctrine"},
    "e3nn":      {"tried": False, "used": False, "reason": "not used: this probe isolates networkx graph algorithm capability; equivariant spherical harmonic networks deferred to integration sims per four-sim-kinds doctrine"},
    "rustworkx": {"tried": False, "used": False, "reason": "not used: this probe isolates networkx graph algorithm capability; rustworkx cross-validation is the focus of the dedicated crosscheck integration sim"},
    "xgi":       {"tried": False, "used": False, "reason": "not used: this probe isolates networkx graph algorithm capability; hyperedge structures handled by xgi are out of scope for this isolation probe"},
    "toponetx":  {"tried": False, "used": False, "reason": "not used: this probe isolates networkx graph algorithm capability; topological complex operations are out of scope for this isolation probe"},
    "gudhi":     {"tried": False, "used": False, "reason": "not used: this probe isolates networkx graph algorithm capability; persistent homology analysis deferred to integration sims per four-sim-kinds doctrine"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None,
    "sympy": None, "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

TARGET_TOOL = {
    "name": "networkx",
    "import": "import networkx as nx; nx.DiGraph",
    "role": "load_bearing",
    "can": [
        "rich graph algorithm library covering paths, centrality, clustering, flows, matching",
        "interoperates with scipy sparse arrays and numpy for numeric analysis",
        "directed and undirected graphs with arbitrary node and edge attributes",
        "DAG detection, topological sort, and ancestor/descendant queries",
    ],
    "cannot": [
        "GPU acceleration — slower than rustworkx or igraph for large graphs",
        "hyperedges or higher-order structures (use xgi or toponetx for those)",
        "formal constraint satisfaction over graph properties (use z3 for that)",
    ],
}

import networkx as nx


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # Positive 1: DiGraph with weighted edges, shortest path and DAG check
    G = nx.DiGraph()
    G.add_nodes_from([0, 1, 2, 3])
    G.add_edge(0, 1, weight=1.0)
    G.add_edge(1, 2, weight=1.0)
    G.add_edge(2, 3, weight=1.0)
    G.add_edge(0, 3, weight=5.0)

    path = nx.dijkstra_path(G, 0, 3, weight="weight")
    path_length = nx.dijkstra_path_length(G, 0, 3, weight="weight")
    is_dag = nx.is_directed_acyclic_graph(G)
    bc = nx.betweenness_centrality(G)
    # Interior nodes 1 and 2 lie on the only short path, so must have nonzero centrality
    interior_nonzero = bc[1] > 0 or bc[2] > 0

    pass_path = (path == [0, 1, 2, 3])
    pass_length = abs(path_length - 3.0) < 1e-9
    pass_dag = is_dag
    pass_bc = interior_nonzero

    results["positive_digraph_path_dag_centrality"] = {
        "path_found": path,
        "expected_path": [0, 1, 2, 3],
        "path_length": path_length,
        "expected_length": 3.0,
        "is_dag": is_dag,
        "betweenness_centrality": {str(k): v for k, v in bc.items()},
        "interior_nonzero": interior_nonzero,
        "pass_path": pass_path,
        "pass_length": pass_length,
        "pass_dag": pass_dag,
        "pass_bc": pass_bc,
        "pass": pass_path and pass_length and pass_dag and pass_bc,
    }

    # Positive 2: scipy sparse bridge
    try:
        import scipy  # noqa: F401
        A = nx.to_scipy_sparse_array(G)
        sparse_ok = (A.shape == (4, 4))
    except Exception as e:
        sparse_ok = False
        results["positive_scipy_bridge"] = {"error": str(e), "pass": False}

    results["positive_scipy_bridge"] = {
        "matrix_shape": list(A.shape) if sparse_ok else None,
        "expected_shape": [4, 4],
        "pass": sparse_ok,
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # Negative: cyclic graph is NOT a DAG
    G_cyclic = nx.DiGraph()
    G_cyclic.add_edges_from([(0, 1), (1, 2), (2, 0)])  # cycle
    is_dag_cyclic = nx.is_directed_acyclic_graph(G_cyclic)
    pass_not_dag = not is_dag_cyclic

    results["negative_cyclic_not_dag"] = {
        "is_dag": is_dag_cyclic,
        "expected": False,
        "pass_returns_false": pass_not_dag,
        "pass": pass_not_dag,
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # Boundary 1: empty graph has 0 nodes, 0 edges
    G_empty = nx.empty_graph(0)
    pass_empty = (G_empty.number_of_nodes() == 0 and G_empty.number_of_edges() == 0)

    results["boundary_empty_graph"] = {
        "n_nodes": G_empty.number_of_nodes(),
        "n_edges": G_empty.number_of_edges(),
        "pass": pass_empty,
    }

    # Boundary 2: complete graph K4 has exactly 6 edges
    G_k4 = nx.complete_graph(4)
    pass_k4 = (G_k4.number_of_edges() == 6)

    results["boundary_complete_graph_k4"] = {
        "n_nodes": G_k4.number_of_nodes(),
        "n_edges": G_k4.number_of_edges(),
        "expected_edges": 6,
        "pass": pass_k4,
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
        pos["positive_digraph_path_dag_centrality"]["pass"]
        and pos["positive_scipy_bridge"]["pass"]
        and neg["negative_cyclic_not_dag"]["pass"]
        and bnd["boundary_empty_graph"]["pass"]
        and bnd["boundary_complete_graph_k4"]["pass"]
    )

    results = {
        "name": "sim_capability_networkx_isolated",
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
    out_path = os.path.join(out_dir, "sim_capability_networkx_isolated_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass: {all_pass}")
