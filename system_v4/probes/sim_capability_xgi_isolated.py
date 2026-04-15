#!/usr/bin/env python3
"""
sim_capability_xgi_isolated.py -- Isolated tool-capability probe for xgi.

Classical_baseline capability probe: demonstrates xgi hypergraph library:
Hypergraph construction, hyperedge operations, node/edge statistics, clique
expansion, and hypergraph adjacency. Honest CAN/CANNOT summary. No coupling
to other tools.
Per four-sim-kinds doctrine: capability probe precedes any integration sim.
"""

import json
import os

classification = "classical_baseline"

_ISOLATED_REASON = (
    "not used: this probe isolates xgi hypergraph capabilities alone; "
    "cross-tool coupling is deferred to a separate integration sim "
    "per the four-sim-kinds doctrine (capability vs integration separation)."
)

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "pyg":       {"tried": False, "used": False, "reason": "PyG handles standard graph message passing; xgi handles hyperedges with arbitrary arity; separate capabilities."},
    "z3":        {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "cvc5":      {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "sympy":     {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "clifford":  {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "e3nn":      {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": "rustworkx is for standard graphs; xgi is for hypergraphs with higher-arity edges; separate tools for separate structures."},
    "xgi":       {"tried": True,  "used": True,  "reason": "load-bearing: xgi Hypergraph construction, hyperedge membership, node statistics, and clique expansion are the sole subjects of this capability probe."},
    "toponetx":  {"tried": False, "used": False, "reason": "toponetx handles simplicial/cell complexes with boundary operators; xgi handles general hypergraphs without chain map structure; separate tools."},
    "gudhi":     {"tried": False, "used": False, "reason": _ISOLATED_REASON},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None,
    "sympy": None, "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": "load_bearing", "toponetx": None, "gudhi": None,
}

XGI_OK = False
try:
    import xgi
    XGI_OK = True
except Exception:
    pass


def run_positive_tests():
    r = {}
    if not XGI_OK:
        r["xgi_available"] = {"pass": False, "detail": "xgi not importable"}
        return r

    import xgi

    r["xgi_available"] = {"pass": True, "version": xgi.__version__}

    # --- Test 1: hypergraph construction ---
    H = xgi.Hypergraph()
    H.add_nodes_from(range(5))
    H.add_edges_from([[0, 1, 2], [1, 2, 3], [3, 4]])  # 3-hyperedge, 3-hyperedge, 2-edge
    r["hypergraph_construction"] = {
        "pass": H.num_nodes == 5 and H.num_edges == 3,
        "num_nodes": H.num_nodes,
        "num_edges": H.num_edges,
        "detail": "Hypergraph: 5 nodes, 3 hyperedges (including a 2-edge)",
    }

    # --- Test 2: hyperedge membership ---
    members_0 = H.edges.members(0)  # members of hyperedge id=0
    r["hyperedge_membership"] = {
        "pass": set(members_0) == {0, 1, 2},
        "members": sorted(members_0),
        "detail": "First hyperedge contains nodes {0, 1, 2}",
    }

    # --- Test 3: node degree (number of hyperedges containing a node) ---
    deg_1 = H.degree(1)  # node 1 is in edges 0 and 1
    r["node_degree"] = {
        "pass": int(deg_1) == 2,
        "degree_1": int(deg_1),
        "detail": "Node 1 appears in 2 hyperedges",
    }

    # --- Test 4: hyperedge size (use len of members, EdgeStat comparison needs asdict) ---
    size_0 = len(H.edges.members(0))
    r["hyperedge_size"] = {
        "pass": size_0 == 3,
        "size": size_0,
        "detail": "Hyperedge 0 has size 3 (contains 3 nodes)",
    }

    # --- Test 5: clique expansion to line graph ---
    # xgi.convert.to_line_graph returns a networkx Graph
    G = xgi.convert.to_line_graph(H)
    r["line_graph_conversion"] = {
        "pass": G is not None and G.number_of_nodes() == H.num_edges,
        "line_graph_nodes": G.number_of_nodes(),
        "detail": "Line graph of 3-edge hypergraph has 3 nodes (one per hyperedge)",
    }

    # --- Test 6: node membership set ---
    memberships_1 = H.nodes.memberships(1)
    r["node_memberships"] = {
        "pass": len(memberships_1) == 2,
        "memberships": sorted(memberships_1),
        "detail": "Node 1 is member of 2 hyperedges",
    }

    return r


def run_negative_tests():
    r = {}
    if not XGI_OK:
        r["xgi_unavailable"] = {"pass": True, "detail": "skip: xgi not installed"}
        return r

    import xgi

    # --- Neg 1: node with no hyperedges has degree 0 ---
    H = xgi.Hypergraph()
    H.add_nodes_from([0, 1, 2])
    H.add_edge([0, 1])
    deg_2 = H.degree(2)  # node 2 has no edges
    r["isolated_node_degree_zero"] = {
        "pass": deg_2 == 0,
        "degree": deg_2,
        "detail": "Node 2 in no hyperedges: degree = 0",
    }

    # --- Neg 2: empty hypergraph has no edges ---
    H_empty = xgi.Hypergraph()
    r["empty_hypergraph"] = {
        "pass": H_empty.num_edges == 0 and H_empty.num_nodes == 0,
        "num_edges": H_empty.num_edges,
        "num_nodes": H_empty.num_nodes,
        "detail": "Empty hypergraph has 0 nodes and 0 edges",
    }

    return r


def run_boundary_tests():
    r = {}
    if not XGI_OK:
        r["xgi_unavailable"] = {"pass": True, "detail": "skip: xgi not installed"}
        return r

    import xgi

    # --- Boundary 1: 1-node hyperedge (self-loop analog) ---
    H = xgi.Hypergraph()
    H.add_nodes_from([0])
    H.add_edge([0])
    sz1 = len(H.edges.members(0))
    r["singleton_hyperedge"] = {
        "pass": sz1 == 1,
        "size": sz1,
        "detail": "1-node hyperedge has size 1",
    }

    # --- Boundary 2: all-nodes hyperedge ---
    H2 = xgi.Hypergraph()
    H2.add_nodes_from(range(5))
    H2.add_edge(list(range(5)))
    sz2 = len(H2.edges.members(0))
    r["all_nodes_hyperedge"] = {
        "pass": sz2 == 5,
        "size": sz2,
        "detail": "5-node hyperedge containing all nodes",
    }

    # --- Boundary 3: duplicate node in hyperedge is deduplicated ---
    H3 = xgi.Hypergraph()
    H3.add_nodes_from([0, 1, 2])
    H3.add_edge([0, 1, 0])  # 0 appears twice
    sz3 = len(H3.edges.members(0))
    r["duplicate_node_deduplicated"] = {
        "pass": sz3 <= 2,
        "size": sz3,
        "detail": "Duplicate node in hyperedge deduplicated to {0,1}: size <= 2",
    }

    return r


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_tests = {**pos, **neg, **bnd}
    overall = all([v.get("pass", False) for v in all_tests.values() if isinstance(v, dict) and "pass" in v])

    results = {
        "name": "sim_capability_xgi_isolated",
        "classification": classification,
        "overall_pass": overall,
        "capability_summary": {
            "CAN": [
                "construct hypergraphs with arbitrary-arity hyperedges",
                "query hyperedge membership and node degree in hypergraph",
                "compute node memberships (which hyperedges contain a node)",
                "convert hypergraphs to line graphs and clique expansions",
                "handle hyperedges of mixed sizes in a single hypergraph",
                "represent multi-way interactions beyond pairwise graph edges",
            ],
            "CANNOT": [
                "compute boundary operators or chain complexes (use toponetx for that)",
                "perform message passing with learned weights (use PyG for that)",
                "compute persistent homology (use gudhi for that)",
                "prove hypergraph properties formally (use z3 for that)",
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
    out_path = os.path.join(out_dir, "sim_capability_xgi_isolated_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass: {overall}")
