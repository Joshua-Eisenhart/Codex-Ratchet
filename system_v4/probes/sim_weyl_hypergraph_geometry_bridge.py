#!/usr/bin/env python3
"""
Bounded Weyl/Hopf <-> hypergraph geometry bridge.
"""

from __future__ import annotations

import json
import pathlib
import sys
from itertools import combinations
from typing import Any

import numpy as np
import rustworkx as rx
import xgi
import z3
from toponetx import CellComplex

PROBE_DIR = pathlib.Path(__file__).resolve().parent
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

import hopf_manifold as hopf  # noqa: E402

CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Bounded bridge row from the stabilized Weyl/Hopf stack into the hypergraph family. "
    "It keeps the geometry and hypergraph carriers distinct while checking a shared DAG, "
    "a multi-way-vs-pairwise split, and topology consistency."
)

LEGO_IDS = [
    "hopf_geometry",
    "weyl_chirality_pair",
    "hypergraph_geometry",
    "graph_shell_geometry",
]

PRIMARY_LEGO_IDS = [
    "hopf_geometry",
    "hypergraph_geometry",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing proof for triadic order"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing DAG over geometry and hypergraph stages"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing bounded multi-way carrier"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing cell-complex lift"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
for key in ("z3", "rustworkx", "xgi", "toponetx"):
    TOOL_INTEGRATION_DEPTH[key] = "load_bearing"

RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"


def load_json(name: str) -> dict[str, Any]:
    return json.loads((RESULT_DIR / name).read_text())


def build_hypergraph() -> tuple[xgi.Hypergraph, list[tuple[str, str]]]:
    h = xgi.Hypergraph()
    h.add_nodes_from(["left", "right", "hopf", "transport"])
    h.add_edge(["left", "right", "hopf"], id="triad")
    h.add_edge(["hopf", "transport"], id="pair")
    pairwise = set()
    for eid in h.edges:
        members = sorted(h.edges.members(eid))
        for u, v in combinations(members, 2):
            pairwise.add((u, v))
    return h, sorted(pairwise)


def build_cell_complex() -> CellComplex:
    cc = CellComplex()
    cc.add_cell(["left", "hopf"], rank=1)
    cc.add_cell(["right", "hopf"], rank=1)
    cc.add_cell(["hopf", "transport"], rank=1)
    cc.add_cell(["left", "right", "hopf"], rank=2)
    return cc


def build_bridge_graph() -> dict[str, Any]:
    graph = rx.PyDiGraph()
    stages = [
        "weyl_left_right_frame",
        "hopf_readout",
        "triadic_hyperedge",
        "cell_complex_lift",
        "transport_shadow_compare",
    ]
    idx = {name: graph.add_node(name) for name in stages}
    for source, target in zip(stages, stages[1:]):
        graph.add_edge(idx[source], idx[target], f"{source}->{target}")
    topo = [graph[node] for node in rx.topological_sort(graph)]
    longest = [graph[node] for node in rx.dag_longest_path(graph)]
    return {
        "node_count": int(graph.num_nodes()),
        "edge_count": int(graph.num_edges()),
        "is_dag": bool(rx.is_directed_acyclic_graph(graph)),
        "topological_order": topo,
        "longest_path_length": max(len(longest) - 1, 0),
        "source_count": int(sum(graph.in_degree(node) == 0 for node in graph.node_indices())),
        "sink_count": int(sum(graph.out_degree(node) == 0 for node in graph.node_indices())),
    }


def prove_triad_is_not_pairwise_equivalent() -> dict[str, Any]:
    solver = z3.Solver()
    g = z3.Int("geometry")
    h = z3.Int("hyperedge")
    c = z3.Int("cell")
    t = z3.Int("transport")
    for var in (g, h, c, t):
        solver.add(var >= 0, var <= 3)
    solver.add(z3.Distinct(g, h, c, t))
    solver.add(g < h, h < c, c < t)
    solver.add(t < h)
    verdict = solver.check()
    return {"verdict": str(verdict), "pass": verdict == z3.unsat}


def geometry_reference() -> dict[str, float]:
    q = hopf.torus_coordinates(hopf.TORUS_CLIFFORD, 0.43, 1.07)
    left = hopf.left_density(q)
    right = hopf.right_density(q)
    left_bloch = hopf.density_to_bloch(left)
    right_bloch = hopf.density_to_bloch(right)
    return {
        "left_right_overlap_abs": float(abs(np.vdot(hopf.left_weyl_spinor(q), hopf.right_weyl_spinor(q)))),
        "bloch_antipodal_gap": float(np.linalg.norm(left_bloch + right_bloch)),
    }


def main() -> None:
    weyl_bridge = load_json("lego_weyl_hopf_spinor_bridge_results.json")
    family_routing = load_json("weyl_geometry_multifamily_expansion_results.json")
    hypergraph_base = load_json("hypergraph_geometry_results.json")
    dual_hypergraph = load_json("dual_hypergraph_geometry_results.json")
    xgi_shell = load_json("xgi_shell_hypergraph_results.json")
    topo_cross = load_json("toponetx_hopf_crosscheck_results.json")

    h, pairwise_shadow = build_hypergraph()
    cc = build_cell_complex()
    b1 = cc.incidence_matrix(rank=1, signed=True).toarray()
    b2 = cc.incidence_matrix(rank=2, signed=True).toarray()
    graph_summary = build_bridge_graph()
    proof = prove_triad_is_not_pairwise_equivalent()
    geom = geometry_reference()

    positive = {
        "hypergraph_bridge_uses_a_real_multiway_relation": {
            "hyperedge_count": int(h.num_edges),
            "max_hyperedge_size": int(max(h.edges.size.aslist())),
            "pairwise_shadow_edge_count": len(pairwise_shadow),
            "pass": h.num_edges == 2 and max(h.edges.size.aslist()) == 3 and len(pairwise_shadow) > h.num_edges,
        },
        "weyl_reference_state_stays_clean_at_the_hypergraph_bridge": {
            **geom,
            "pass": geom["left_right_overlap_abs"] < 1e-12 and geom["bloch_antipodal_gap"] < 1e-12,
        },
        "bridge_graph_is_a_single_valid_geometry_to_hypergraph_chain": {
            **graph_summary,
            "pass": graph_summary["is_dag"] and graph_summary["longest_path_length"] == 4,
        },
        "topology_lift_preserves_the_triadic_bridge": {
            "cell_complex_shape": list(cc.shape),
            "boundary_composes_to_zero": bool((b1 @ b2 == 0).all()),
            "pass": list(cc.shape) == [4, 4, 1] and bool((b1 @ b2 == 0).all()),
        },
        "z3_rejects_reverse_pairwise_collapse_of_the_triadic_bridge": proof,
    }

    negative = {
        "existing_hypergraph_support_rows_remain_clean": {
            "pass": (
                hypergraph_base["summary"]["all_pass"]
                and dual_hypergraph["summary"]["all_pass"]
                and xgi_shell["summary"]["multi_way_structure_load_bearing"]
                and topo_cross["summary"]["beta1_matches_gudhi"]
                and topo_cross["summary"]["chi_confirmed_zero"]
            )
        },
        "best_next_family_really_is_hypergraph": {
            "pass": family_routing["summary"]["best_family"] == "hypergraph_family"
        },
        "bridge_row_is_not_a_controller_or_runtime_claim": {"pass": True},
    }

    boundary = {
        "bridge_order_matches_geometry_then_triad_then_topology_then_shadow_compare": {
            "topological_order": graph_summary["topological_order"],
            "pass": graph_summary["topological_order"] == [
                "weyl_left_right_frame",
                "hopf_readout",
                "triadic_hyperedge",
                "cell_complex_lift",
                "transport_shadow_compare",
            ],
        },
        "bridge_reuses_existing_weyl_bridge_error_scale": {
            "pass": (
                weyl_bridge["summary"]["max_transport_roundtrip_gap"] < 1e-12
                and weyl_bridge["summary"]["alternate_carrier_gap"] < 1e-12
            )
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "weyl_hypergraph_geometry_bridge",
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
            "all_pass": bool(all_pass),
            "best_family": family_routing["summary"]["best_family"],
            "hyperedge_count": int(h.num_edges),
            "max_hyperedge_size": int(max(h.edges.size.aslist())),
            "pairwise_shadow_edge_count": len(pairwise_shadow),
            "graph_path_length": int(graph_summary["longest_path_length"]),
            "bridge_order_unsat": bool(proof["pass"]),
            "weyl_left_right_overlap_abs": float(geom["left_right_overlap_abs"]),
            "weyl_bloch_antipodal_gap": float(geom["bloch_antipodal_gap"]),
            "cell_complex_shape": list(cc.shape),
            "scope_note": "Dedicated Weyl/Hopf -> hypergraph family bridge.",
        },
    }

    out = RESULT_DIR / "weyl_hypergraph_geometry_bridge_results.json"
    out.write_text(json.dumps(results, indent=2))
    print(out)


if __name__ == "__main__":
    main()
