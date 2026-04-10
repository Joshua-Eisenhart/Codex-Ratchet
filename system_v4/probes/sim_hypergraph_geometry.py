#!/usr/bin/env python3
"""
PURE LEGO: Hypergraph Geometry
==============================
Direct local hypergraph carrier lego on one bounded multi-way relation set.
"""

import json
import pathlib
from itertools import combinations

import numpy as np
import xgi
from toponetx import CellComplex


CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for hypergraph carrier geometry on one bounded relation set, "
    "kept separate from broader family-level XGI surfaces."
)

LEGO_IDS = [
    "hypergraph_geometry",
]

PRIMARY_LEGO_IDS = [
    "hypergraph_geometry",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "shadow graph is computed directly without graph-library dependency"},
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "hypergraph construction, incidence, component, and edge-size checks are load-bearing",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "CellComplex lift and boundary-incidence checks are load-bearing for the same bounded multi-way carrier",
    },
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["xgi"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["toponetx"] = "load_bearing"


def shadow_graph_edges(h):
    edges = set()
    for eid in h.edges:
        members = list(h.edges.members(eid))
        for u, v in combinations(sorted(members), 2):
            edges.add((u, v))
    return sorted(edges)


def components(nodes, edges):
    adj = {n: set() for n in nodes}
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)
    seen = set()
    count = 0
    for n in nodes:
        if n in seen:
            continue
        count += 1
        stack = [n]
        seen.add(n)
        while stack:
            cur = stack.pop()
            for nxt in adj[cur]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
    return count


def build_cell_complex():
    cc = CellComplex()
    cc.add_cell(["a", "b"], rank=1)
    cc.add_cell(["a", "c"], rank=1)
    cc.add_cell(["b", "c"], rank=1)
    cc.add_cell(["c", "d"], rank=1)
    cc.add_cell(["a", "b", "c"], rank=2)
    return cc


def main():
    h = xgi.Hypergraph()
    h.add_nodes_from(["a", "b", "c", "d"])
    h.add_edge(["a", "b", "c"], id="triad")
    h.add_edge(["c", "d"], id="pair")

    shadow_edges = shadow_graph_edges(h)
    shadow_component_count = components(list(h.nodes), shadow_edges)

    h_no_triad = xgi.Hypergraph()
    h_no_triad.add_nodes_from(["a", "b", "c", "d"])
    h_no_triad.add_edge(["c", "d"], id="pair")
    cc = build_cell_complex()
    b1 = cc.incidence_matrix(rank=1, signed=True).toarray()
    b2 = cc.incidence_matrix(rank=2, signed=True).toarray()
    cc_shape = list(cc.shape)

    positive = {
        "incidence_and_counts_are_well_formed": {
            "num_nodes": h.num_nodes,
            "num_edges": h.num_edges,
            "edge_sizes": sorted(h.edges.size.aslist()),
            "pass": h.num_nodes == 4 and h.num_edges == 2 and sorted(h.edges.size.aslist()) == [2, 3],
        },
        "genuine_multiway_edge_is_present": {
            "edge_sizes": sorted(h.edges.size.aslist()),
            "pass": max(h.edges.size.aslist()) > 2,
        },
        "shadow_graph_preserves_connectivity": {
            "hypergraph_connected": xgi.is_connected(h),
            "shadow_component_count": shadow_component_count,
            "pass": xgi.is_connected(h) and shadow_component_count == 1,
        },
        "cell_complex_lift_preserves_multiway_carrier": {
            "cell_complex_shape": cc_shape,
            "rank_B1": int(np.linalg.matrix_rank(b1)),
            "rank_B2": int(np.linalg.matrix_rank(b2)),
            "pass": cc_shape == [4, 4, 1] and b1.shape == (4, 4) and b2.shape == (4, 1),
        },
    }

    negative = {
        "pairwise_shadow_does_not_retain_hyperedge_identity": {
            "shadow_edges": shadow_edges,
            "pass": len(shadow_edges) != h.num_edges,
        },
        "removing_multiway_edge_collapses_local_relation": {
            "original_edges": sorted(h.edges.size.aslist()),
            "collapsed_edges": sorted(h_no_triad.edges.size.aslist()),
            "pass": max(h_no_triad.edges.size.aslist()) <= 2 and not xgi.is_connected(h_no_triad),
        },
    }

    boundary = {
        "higher_order_profile_differs_from_shadow_profile": {
            "hypergraph_edge_sizes": sorted(h.edges.size.aslist()),
            "shadow_edge_count": len(shadow_edges),
            "pass": sorted(h.edges.size.aslist()) != [2] * len(shadow_edges),
        },
        "all_base_nodes_remain_present_after_relation_collapse": {
            "pass": set(h_no_triad.nodes) == set(h.nodes),
        },
        "cell_complex_boundary_composes_to_zero": {
            "pass": bool((b1 @ b2 == 0).all()),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "hypergraph_geometry",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "scope_note": "Direct local hypergraph-carrier lego contrasting one genuine triadic relation against its pairwise shadow and CellComplex lift.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "hypergraph_geometry_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
