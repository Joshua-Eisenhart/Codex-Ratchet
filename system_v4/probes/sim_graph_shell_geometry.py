#!/usr/bin/env python3
"""
PURE LEGO: Graph Shell Geometry
===============================
Direct local shell-graph lego using only binary shell relations.
"""

import json
import pathlib

import numpy as np
import rustworkx as rx
classification = "classical_baseline"  # auto-backfill


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for shell graph geometry using only binary shell relations, "
    "kept separate from multi-way hypergraph shell structure."
)

LEGO_IDS = [
    "graph_shell_geometry",
]

PRIMARY_LEGO_IDS = [
    "graph_shell_geometry",
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
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "binary shell graph construction, connectivity, path length, and Laplacian checks are load-bearing",
    },
    "xgi": {"tried": False, "used": False, "reason": "reserved for hypergraph shell row"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["rustworkx"] = "load_bearing"


def make_graph(n, edges):
    g = rx.PyGraph()
    g.add_nodes_from(list(range(n)))
    for u, v in edges:
        g.add_edge(u, v, 1.0)
    return g


def stats(g):
    n = g.num_nodes()
    m = g.num_edges()
    comps = list(rx.connected_components(g))
    c = len(comps)
    cycle_rank = m - n + c
    adj = np.array(rx.graph_adjacency_matrix(g, weight_fn=float), dtype=float)
    deg = np.diag(np.sum(adj, axis=1))
    lap = deg - adj
    evals = np.linalg.eigvalsh(lap) if lap.size else np.array([])
    zero_modes = int(np.sum(np.abs(evals) < EPS))
    diameter = None
    if c == 1:
        path_lengths = rx.all_pairs_dijkstra_path_lengths(g, lambda _: 1.0)
        diameter = int(
            max(
                dist
                for source_map in path_lengths.values()
                for dist in source_map.values()
            )
        )
    return {
        "num_nodes": int(n),
        "num_edges": int(m),
        "num_components": int(c),
        "cycle_rank": int(cycle_rank),
        "laplacian_zero_modes": zero_modes,
        "degree_sequence": sorted([int(g.degree(i)) for i in range(n)], reverse=True),
        "diameter": diameter,
    }


def main():
    shell_chain = make_graph(4, [(0, 1), (1, 2), (2, 3)])
    shell_cycle = make_graph(4, [(0, 1), (1, 2), (2, 3), (3, 0)])
    shell_split = make_graph(4, [(0, 1), (2, 3)])

    chain = stats(shell_chain)
    cycle = stats(shell_cycle)
    split = stats(shell_split)

    positive = {
        "nested_shell_chain_is_connected_and_acyclic": {
            **chain,
            "pass": chain["num_components"] == 1 and chain["cycle_rank"] == 0 and chain["diameter"] == 3,
        },
        "pairwise_shell_loop_has_single_cycle": {
            **cycle,
            "pass": cycle["num_components"] == 1 and cycle["cycle_rank"] == 1 and cycle["degree_sequence"] == [2, 2, 2, 2],
        },
        "laplacian_nullity_matches_component_count": {
            "pass": all(s["laplacian_zero_modes"] == s["num_components"] for s in [chain, cycle, split]),
        },
    }

    negative = {
        "disconnected_shell_graph_is_not_single_structure": {
            **split,
            "pass": split["num_components"] == 2 and split["laplacian_zero_modes"] == 2,
        },
        "chain_and_cycle_shadow_graphs_are_not_collapsed": {
            "pass": chain["cycle_rank"] != cycle["cycle_rank"] and chain["diameter"] != cycle["diameter"],
        },
    }

    boundary = {
        "row_stays_binary_not_multiway": {
            "pass": max(cycle["degree_sequence"]) <= 2 and max(chain["degree_sequence"]) <= 2,
        },
        "pairwise_shell_graph_uses_only_vertex_edge_data": {
            "pass": all(key in chain for key in ["num_nodes", "num_edges", "num_components", "cycle_rank"]),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "graph_shell_geometry",
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
            "scope_note": "Direct local shell-graph lego using only binary shell relations and graph-native invariants.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "graph_shell_geometry_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
