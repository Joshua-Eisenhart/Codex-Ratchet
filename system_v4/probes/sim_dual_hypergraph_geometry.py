#!/usr/bin/env python3
"""
PURE LEGO: Dual Hypergraph Geometry
===================================
Direct local dual-hypergraph conversion lego on one bounded carrier.
"""

import json
import pathlib

import xgi


CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for dual-hypergraph geometry on a bounded carrier, kept "
    "separate from broad family-level hypergraph or integration surfaces."
)

LEGO_IDS = [
    "dual_hypergraph_geometry",
]

PRIMARY_LEGO_IDS = [
    "dual_hypergraph_geometry",
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
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "hypergraph and dual-hypergraph construction are load-bearing",
    },
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["xgi"] = "load_bearing"


def main():
    # bounded local carrier: 4 nodes, 3 hyperedges
    h = xgi.Hypergraph()
    h.add_nodes_from(["a", "b", "c", "d"])
    h.add_edge(["a", "b", "c"], id="e0")
    h.add_edge(["b", "c"], id="e1")
    h.add_edge(["c", "d"], id="e2")

    d = h.dual()

    original_node_count = h.num_nodes
    original_edge_count = h.num_edges
    dual_node_count = d.num_nodes
    dual_edge_count = d.num_edges

    original_sizes = sorted(h.edges.size.aslist())
    dual_sizes = sorted(d.edges.size.aslist())

    positive = {
        "dual_swaps_node_and_edge_counts": {
            "original_nodes": original_node_count,
            "original_edges": original_edge_count,
            "dual_nodes": dual_node_count,
            "dual_edges": dual_edge_count,
            "pass": original_node_count == dual_edge_count and original_edge_count == dual_node_count,
        },
        "shared_membership_creates_dual_connections": {
            "dual_edge_sizes": dual_sizes,
            "pass": any(size >= 2 for size in dual_sizes),
        },
        "dual_preserves_connectedness_on_bounded_example": {
            "pass": xgi.is_connected(h) and xgi.is_connected(d),
        },
    }

    negative = {
        "dual_is_not_identical_to_original_object": {
            "original_size_profile": original_sizes,
            "dual_size_profile": dual_sizes,
            "pass": original_sizes != dual_sizes,
        },
        "singleton_free_structure_stays_nontrivial": {
            "pass": min(dual_sizes) >= 1 and max(dual_sizes) > 1,
        },
    }

    boundary = {
        "double_dual_restores_counts": {
            "pass": d.dual().num_nodes == h.num_nodes and d.dual().num_edges == h.num_edges,
        },
        "incidence_roles_are_exposed_differently_in_dual": {
            "original_size_profile": original_sizes,
            "dual_size_profile": dual_sizes,
            "pass": original_sizes != dual_sizes,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "dual_hypergraph_geometry",
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
            "scope_note": "Direct local dual-hypergraph lego on one bounded hypergraph carrier.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "dual_hypergraph_geometry_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
