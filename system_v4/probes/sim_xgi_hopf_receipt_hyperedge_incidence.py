#!/usr/bin/env python3
"""XGI Hopf receipt hyperedge incidence baseline."""

from __future__ import annotations

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import json
from pathlib import Path

import xgi
from receipt_boundary import apply_default_receipt_boundary


NAME = "xgi_hopf_receipt_hyperedge_incidence"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "xgi": {
        "tried": True,
        "used": True,
        "reason": (
            "Hypergraph, named hyperedges, edge memberships, node memberships, "
            "connected_components, and incidence_matrix check higher-order receipt grouping"
        ),
    }
}
TOOL_INTEGRATION_DEPTH = {"xgi": "load_bearing"}

RECEIPTS = [
    "sympy_hopf_loop_holonomy_area_dependence",
    "scipy_hopf_horizontal_lift_chi_shift",
    "gudhi_hopf_torus_fiber_base_homology",
    "toponetx_two_hopf_torus_layer_incidence",
    "cvc5_hopf_torus_readout_vector_separation",
    "z3_hopf_torus_readout_vector_separation",
    "e3nn_hopf_base_loop_so3_equivariance",
]

HYPEREDGES = {
    "base_geometry_parent_set": {
        "sympy_hopf_loop_holonomy_area_dependence",
        "scipy_hopf_horizontal_lift_chi_shift",
        "gudhi_hopf_torus_fiber_base_homology",
        "toponetx_two_hopf_torus_layer_incidence",
    },
    "solver_readout_set": {
        "toponetx_two_hopf_torus_layer_incidence",
        "cvc5_hopf_torus_readout_vector_separation",
        "z3_hopf_torus_readout_vector_separation",
    },
    "equivariance_readout_set": {
        "sympy_hopf_loop_holonomy_area_dependence",
        "e3nn_hopf_base_loop_so3_equivariance",
    },
}


def build_hypergraph(edge_map: dict[str, set[str]]) -> xgi.Hypergraph:
    graph = xgi.Hypergraph()
    graph.add_nodes_from(RECEIPTS)
    for edge_name, members in edge_map.items():
        graph.add_edge(members, idx=edge_name)
    return graph


def sorted_memberships(graph: xgi.Hypergraph) -> dict[str, list[str]]:
    return {node: sorted(graph.nodes.memberships(node)) for node in sorted(graph.nodes)}


def sorted_edge_members(graph: xgi.Hypergraph) -> dict[str, list[str]]:
    return {edge: sorted(graph.edges.members(edge)) for edge in sorted(graph.edges)}


def incidence_readout(graph: xgi.Hypergraph) -> dict[str, object]:
    matrix, node_index, edge_index = xgi.incidence_matrix(graph, sparse=False, index=True)
    ordered_nodes = [node_index[idx] for idx in sorted(node_index)]
    ordered_edges = [edge_index[idx] for idx in sorted(edge_index)]
    return {
        "shape": list(matrix.shape),
        "nodes": ordered_nodes,
        "edges": ordered_edges,
        "ones": int(matrix.sum()),
    }


def intersections(edge_map: dict[str, set[str]]) -> dict[str, list[str]]:
    names = sorted(edge_map)
    out: dict[str, list[str]] = {}
    for left_index, left in enumerate(names):
        for right in names[left_index + 1 :]:
            out[f"{left}__{right}"] = sorted(edge_map[left] & edge_map[right])
    return out


def component_count(graph: xgi.Hypergraph) -> int:
    return len(list(xgi.connected_components(graph)))


def run_positive() -> dict[str, object]:
    graph = build_hypergraph(HYPEREDGES)
    edge_sizes = {edge: len(graph.edges.members(edge)) for edge in sorted(graph.edges)}
    node_degrees = {node: len(graph.nodes.memberships(node)) for node in sorted(graph.nodes)}
    shared = intersections(HYPEREDGES)
    return {
        "edge_members": sorted_edge_members(graph),
        "node_memberships": sorted_memberships(graph),
        "edge_sizes": edge_sizes,
        "node_degrees": node_degrees,
        "incidence": incidence_readout(graph),
        "intersections": shared,
        "component_count": component_count(graph),
        "survives_hyperedge_incidence": bool(
            component_count(graph) == 1
            and edge_sizes["base_geometry_parent_set"] == 4
            and edge_sizes["solver_readout_set"] == 3
            and shared["base_geometry_parent_set__solver_readout_set"]
            == ["toponetx_two_hopf_torus_layer_incidence"]
            and shared["base_geometry_parent_set__equivariance_readout_set"]
            == ["sympy_hopf_loop_holonomy_area_dependence"]
            and node_degrees["toponetx_two_hopf_torus_layer_incidence"] == 2
            and node_degrees["cvc5_hopf_torus_readout_vector_separation"] == 1
        ),
    }


def run_graveyards() -> dict[str, object]:
    pairwise_edges = {
        "sympy_to_toponetx_pair": {
            "sympy_hopf_loop_holonomy_area_dependence",
            "toponetx_two_hopf_torus_layer_incidence",
        },
        "scipy_to_toponetx_pair": {
            "scipy_hopf_horizontal_lift_chi_shift",
            "toponetx_two_hopf_torus_layer_incidence",
        },
        "gudhi_to_toponetx_pair": {
            "gudhi_hopf_torus_fiber_base_homology",
            "toponetx_two_hopf_torus_layer_incidence",
        },
        "toponetx_to_cvc5_pair": {
            "toponetx_two_hopf_torus_layer_incidence",
            "cvc5_hopf_torus_readout_vector_separation",
        },
        "toponetx_to_z3_pair": {
            "toponetx_two_hopf_torus_layer_incidence",
            "z3_hopf_torus_readout_vector_separation",
        },
    }
    missing_toponetx = {
        key: {node for node in members if node != "toponetx_two_hopf_torus_layer_incidence"}
        for key, members in HYPEREDGES.items()
    }
    singleton_edges = {f"{node}_singleton": {node} for node in RECEIPTS}
    disconnected_edges = {
        "geometry_only": {
            "sympy_hopf_loop_holonomy_area_dependence",
            "scipy_hopf_horizontal_lift_chi_shift",
            "gudhi_hopf_torus_fiber_base_homology",
        },
        "solver_only": {
            "cvc5_hopf_torus_readout_vector_separation",
            "z3_hopf_torus_readout_vector_separation",
        },
        "equivariance_only": {"e3nn_hopf_base_loop_so3_equivariance"},
    }
    all_in_one = {"all_receipts_single_hyperedge": set(RECEIPTS)}

    pairwise_graph = build_hypergraph(pairwise_edges)
    missing_graph = build_hypergraph(missing_toponetx)
    singleton_graph = build_hypergraph(singleton_edges)
    disconnected_graph = build_hypergraph(disconnected_edges)
    all_in_one_graph = build_hypergraph(all_in_one)

    return {
        "pairwise_only_loses_higher_order_parent_grouping": {
            "edge_sizes": {edge: len(pairwise_graph.edges.members(edge)) for edge in sorted(pairwise_graph.edges)},
            "passed": max(len(pairwise_graph.edges.members(edge)) for edge in pairwise_graph.edges) == 2,
        },
        "missing_toponetx_removes_geometry_solver_intersection": {
            "intersections": intersections(missing_toponetx),
            "passed": not intersections(missing_toponetx)["base_geometry_parent_set__solver_readout_set"],
        },
        "singleton_edges_do_not_form_multi_receipt_groups": {
            "edge_sizes": {edge: len(singleton_graph.edges.members(edge)) for edge in sorted(singleton_graph.edges)},
            "passed": max(len(singleton_graph.edges.members(edge)) for edge in singleton_graph.edges) == 1,
        },
        "disconnected_groups_have_multiple_components": {
            "component_count": component_count(disconnected_graph),
            "passed": component_count(disconnected_graph) > 1,
        },
        "all_in_one_hyperedge_loses_group_distinctions": {
            "incidence": incidence_readout(all_in_one_graph),
            "edge_count": all_in_one_graph.num_edges,
            "passed": all_in_one_graph.num_edges == 1,
        },
    }


def main() -> int:
    positive = run_positive()
    graveyards = run_graveyards()
    all_pass = bool(
        positive["survives_hyperedge_incidence"]
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "XGI hyperedge incidence baseline over Hopf receipt dependency groups only; "
            "no physical inner/outer loop independence, no full geometric-constraint-manifold, "
            "no QIT, GStack, axis, bridge, nonclassical, flux-to-Pauli, or target-system claim"
        ),
        "next_lego_target": "nested_hopf_torus_loop_geometry_baseline",
        "promotion_condition": (
            "May only support later receipt routing after exact physical Hopf/Weyl carrier-evolution "
            "fixtures define the receipt groups being connected."
        ),
        "demotion_condition": (
            "Demote if XGI loses named hyperedge memberships, misses the TopoNetX shared parent, "
            "collapses disconnected groups, or cannot distinguish pairwise and all-in-one controls."
        ),
        "blocked_until": (
            "blocked from inner/outer geometry admission until full carrier fixtures and physical-evolution "
            "graveyards exist"
        ),
        "out_of_scope": [
            "No physical Hopf/Weyl evolution.",
            "No inner/outer loop independence result.",
            "No full geometric-constraint-manifold implementation.",
            "No flux representation or Pauli shortcut.",
            "No QIT, GStack, axis, bridge, or nonclassical admission.",
        ],
        "divergence_log": (
            "This baseline checks higher-order receipt grouping only. It can keep dependency groups visible "
            "for later geometry packets, but it does not show that inner and outer Hopf/Weyl loops are independent."
        ),
        "operation_sequence": [
            "declare Hopf geometry and readout receipt names as hypergraph nodes",
            "declare named hyperedges for base-geometry parents, solver readouts, and equivariance readouts",
            "read XGI node memberships, edge memberships, incidence matrix, intersections, and components",
            "run pairwise-only, missing-parent, singleton, disconnected, and all-in-one graveyards",
        ],
        "carrier_topology": "receipt hypergraph over bounded Hopf geometry and readout-vector fixtures",
        "observable": "hyperedge order, node memberships, edge intersections, incidence shape, and component count",
        "pass_fail_predicate": (
            "the TopoNetX layer receipt is the unique shared geometry-to-solver parent, the SymPy holonomy "
            "receipt is the shared geometry-to-equivariance parent, grouped hyperedges remain connected, and "
            "adjacent controls collapse or lose the required grouping"
        ),
        "graveyards": [
            "pairwise-only edges lose higher-order parent grouping",
            "missing TopoNetX removes geometry-solver intersection",
            "singleton edges do not form multi-receipt groups",
            "disconnected groups have multiple components",
            "all-in-one hyperedge loses group distinctions",
        ],
        "baselines": [
            "TopoNetX two Hopf-torus layer incidence fixture",
            "cvc5 Hopf torus readout-vector separation fixture",
            "z3 Hopf torus readout-vector separation fixture",
            "e3nn Hopf base-loop SO3 equivariance fixture",
            "rustworkx Hopf receipt dependency DAG fixture",
        ],
        "alternative_formulations": [
            "rustworkx bipartite incidence graph",
            "TopoNetX cell complex over receipt groups",
            "z3 set-intersection constraints over receipt groups",
        ],
        "exact_tool_function_needs": {
            "xgi": [
                "Hypergraph",
                "add_nodes_from",
                "add_edge",
                "nodes.memberships",
                "edges.members",
                "incidence_matrix",
                "connected_components",
            ],
        },
        "lego_or_coupling_target": "nested_hopf_torus_loop_geometry_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "receipts": RECEIPTS,
        "hyperedges": {key: sorted(value) for key, value in HYPEREDGES.items()},
        "positive": positive,
        "graveyards_detail": graveyards,
        "promotion_allowed": False,
        "pass": all_pass,
    }
    results = apply_default_receipt_boundary(results, source_name=f"sim_{NAME}")
    out_path = RESULTS_DIR / f"{NAME}_results.json"
    out_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"PASS={results['pass']}  name={NAME}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
