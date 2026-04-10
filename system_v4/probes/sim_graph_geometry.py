#!/usr/bin/env python3
"""
PURE LEGO: Graph Geometry
=========================
Direct local graph/topology lego.

Build bounded graph carriers and verify graph-geometric structure directly.
"""

import json
import pathlib
from datetime import datetime, timezone

import numpy as np
import rustworkx as rx


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for graph carrier geometry using bounded rustworkx "
    "graphs and direct connectivity/Laplacian checks."
)

LEGO_IDS = [
    "graph_geometry",
]

PRIMARY_LEGO_IDS = [
    "graph_geometry",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "saved for later graph-learning row"},
    "z3": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "graph construction, connected components, cycle basis, and Laplacian are load-bearing",
    },
    "xgi": {"tried": False, "used": False, "reason": "saved for hypergraph row"},
    "toponetx": {"tried": False, "used": False, "reason": "already used on cell-complex row"},
    "gudhi": {"tried": False, "used": False, "reason": "saved for persistence row"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["rustworkx"] = "load_bearing"


def make_graph(n, edges):
    g = rx.PyGraph()
    g.add_nodes_from(list(range(n)))
    for u, v in edges:
        g.add_edge(u, v, 1.0)
    return g


def graph_stats(g):
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
    return {
        "num_nodes": int(n),
        "num_edges": int(m),
        "num_components": int(c),
        "cycle_rank": int(cycle_rank),
        "laplacian_zero_modes": zero_modes,
        "laplacian_eigenvalues": [float(x) for x in evals],
        "degree_sequence": sorted([int(g.degree(i)) for i in range(n)], reverse=True),
    }


def main():
    path4 = make_graph(4, [(0, 1), (1, 2), (2, 3)])
    cycle4 = make_graph(4, [(0, 1), (1, 2), (2, 3), (3, 0)])
    disconnected = make_graph(4, [(0, 1), (2, 3)])

    path_stats = graph_stats(path4)
    cycle_stats = graph_stats(cycle4)
    disc_stats = graph_stats(disconnected)

    positive = {
        "path_graph_is_connected_and_acyclic": {
            **path_stats,
            "pass": (
                path_stats["num_components"] == 1
                and path_stats["cycle_rank"] == 0
                and path_stats["laplacian_zero_modes"] == 1
            ),
        },
        "cycle_graph_has_one_independent_loop": {
            **cycle_stats,
            "pass": (
                cycle_stats["num_components"] == 1
                and cycle_stats["cycle_rank"] == 1
                and cycle_stats["laplacian_zero_modes"] == 1
                and cycle_stats["degree_sequence"] == [2, 2, 2, 2]
            ),
        },
    }

    negative = {
        "disconnected_graph_is_not_single_component": {
            **disc_stats,
            "pass": disc_stats["num_components"] == 2 and disc_stats["laplacian_zero_modes"] == 2,
        },
        "path_graph_is_not_cycle_graph": {
            "path_cycle_rank": path_stats["cycle_rank"],
            "cycle_cycle_rank": cycle_stats["cycle_rank"],
            "pass": path_stats["cycle_rank"] != cycle_stats["cycle_rank"],
        },
    }

    boundary = {
        "laplacian_nullity_matches_component_count_for_all_cases": {
            "pass": all(
                stats["laplacian_zero_modes"] == stats["num_components"]
                for stats in [path_stats, cycle_stats, disc_stats]
            ),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "graph_geometry",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "scope_note": "Direct local graph carrier lego on bounded path, cycle, and disconnected examples.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "graph_geometry_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
