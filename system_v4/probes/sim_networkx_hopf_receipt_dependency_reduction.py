#!/usr/bin/env python3
"""NetworkX Hopf receipt dependency reduction baseline."""

from __future__ import annotations

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import json
from pathlib import Path

import networkx as nx
from receipt_boundary import apply_default_receipt_boundary


NAME = "networkx_hopf_receipt_dependency_reduction"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "networkx": {
        "tried": True,
        "used": True,
        "reason": "DiGraph, topological_sort, ancestors, descendants, and transitive_reduction check the bounded Hopf receipt dependency DAG",
    }
}
TOOL_INTEGRATION_DEPTH = {"networkx": "load_bearing"}

NODES = [
    "sympy_hopf_loop_holonomy_area_dependence",
    "scipy_hopf_horizontal_lift_chi_shift",
    "gudhi_hopf_torus_fiber_base_homology",
    "toponetx_two_hopf_torus_layer_incidence",
    "cvc5_hopf_torus_readout_vector_separation",
    "z3_hopf_torus_readout_vector_separation",
]

EDGES = [
    ("sympy_hopf_loop_holonomy_area_dependence", "toponetx_two_hopf_torus_layer_incidence"),
    ("scipy_hopf_horizontal_lift_chi_shift", "toponetx_two_hopf_torus_layer_incidence"),
    ("gudhi_hopf_torus_fiber_base_homology", "toponetx_two_hopf_torus_layer_incidence"),
    ("toponetx_two_hopf_torus_layer_incidence", "cvc5_hopf_torus_readout_vector_separation"),
    ("toponetx_two_hopf_torus_layer_incidence", "z3_hopf_torus_readout_vector_separation"),
    ("sympy_hopf_loop_holonomy_area_dependence", "cvc5_hopf_torus_readout_vector_separation"),
    ("sympy_hopf_loop_holonomy_area_dependence", "z3_hopf_torus_readout_vector_separation"),
]


def build_graph(edges: list[tuple[str, str]]) -> nx.DiGraph:
    graph = nx.DiGraph()
    graph.add_nodes_from(NODES)
    graph.add_edges_from(edges)
    return graph


def sorted_edges(graph: nx.DiGraph) -> list[tuple[str, str]]:
    return sorted((str(source), str(target)) for source, target in graph.edges())


def sorted_nodes(nodes) -> list[str]:
    return sorted(str(node) for node in nodes)


def run_positive() -> dict[str, object]:
    graph = build_graph(EDGES)
    reduced = nx.transitive_reduction(graph)
    order = list(nx.topological_sort(graph))
    reduced_edges = sorted_edges(reduced)
    redundant_edges_removed = sorted(set(EDGES) - set(reduced_edges))
    ancestors_cvc5 = sorted_nodes(nx.ancestors(graph, "cvc5_hopf_torus_readout_vector_separation"))
    descendants_sympy = sorted_nodes(nx.descendants(graph, "sympy_hopf_loop_holonomy_area_dependence"))
    return {
        "topological_order": order,
        "edge_count": len(EDGES),
        "transitive_reduction_edge_count": len(reduced_edges),
        "transitive_reduction_edges": reduced_edges,
        "redundant_edges_removed": redundant_edges_removed,
        "ancestors_of_cvc5_readout": ancestors_cvc5,
        "descendants_of_sympy_holonomy": descendants_sympy,
        "survives_dependency_reduction": bool(
            order.index("toponetx_two_hopf_torus_layer_incidence")
            > order.index("gudhi_hopf_torus_fiber_base_homology")
            and order.index("cvc5_hopf_torus_readout_vector_separation")
            > order.index("toponetx_two_hopf_torus_layer_incidence")
            and order.index("z3_hopf_torus_readout_vector_separation")
            > order.index("toponetx_two_hopf_torus_layer_incidence")
            and ("sympy_hopf_loop_holonomy_area_dependence", "cvc5_hopf_torus_readout_vector_separation")
            in redundant_edges_removed
            and ("sympy_hopf_loop_holonomy_area_dependence", "z3_hopf_torus_readout_vector_separation")
            in redundant_edges_removed
            and "toponetx_two_hopf_torus_layer_incidence" in ancestors_cvc5
            and "cvc5_hopf_torus_readout_vector_separation" in descendants_sympy
        ),
    }


def run_graveyards() -> dict[str, object]:
    graph = build_graph(EDGES)
    missing_toponetx_edges = [edge for edge in EDGES if edge[0] != "toponetx_two_hopf_torus_layer_incidence"]
    missing_graph = build_graph(missing_toponetx_edges)
    missing_ancestors = sorted_nodes(nx.ancestors(missing_graph, "cvc5_hopf_torus_readout_vector_separation"))

    cyclic = nx.DiGraph()
    cyclic.add_edges_from(
        [
            ("toponetx_two_hopf_torus_layer_incidence", "cvc5_hopf_torus_readout_vector_separation"),
            ("cvc5_hopf_torus_readout_vector_separation", "toponetx_two_hopf_torus_layer_incidence"),
        ]
    )
    reversed_graph = build_graph(
        [
            ("toponetx_two_hopf_torus_layer_incidence", "sympy_hopf_loop_holonomy_area_dependence"),
            ("toponetx_two_hopf_torus_layer_incidence", "scipy_hopf_horizontal_lift_chi_shift"),
            ("toponetx_two_hopf_torus_layer_incidence", "gudhi_hopf_torus_fiber_base_homology"),
        ]
    )
    reversed_order = list(nx.topological_sort(reversed_graph))

    isolated = nx.DiGraph()
    isolated.add_node("single_receipt")
    reduced_edges = sorted_edges(nx.transitive_reduction(graph))
    return {
        "missing_toponetx_parent_removes_readout_ancestor": {
            "ancestors_of_cvc5_readout": missing_ancestors,
            "passed": "toponetx_two_hopf_torus_layer_incidence" not in missing_ancestors,
        },
        "cycle_input_detected_by_dag_check": {
            "is_directed_acyclic_graph": nx.is_directed_acyclic_graph(cyclic),
            "passed": not nx.is_directed_acyclic_graph(cyclic),
        },
        "reversed_edges_invert_parent_order_as_expected_bad_control": {
            "topological_order": reversed_order,
            "expected_inversion": True,
            "passed": reversed_order.index("toponetx_two_hopf_torus_layer_incidence")
            < reversed_order.index("sympy_hopf_loop_holonomy_area_dependence"),
        },
        "isolated_single_receipt_has_no_dependencies": {
            "ancestors": sorted_nodes(nx.ancestors(isolated, "single_receipt")),
            "descendants": sorted_nodes(nx.descendants(isolated, "single_receipt")),
            "passed": not nx.ancestors(isolated, "single_receipt") and not nx.descendants(isolated, "single_receipt"),
        },
        "transitive_reduction_keeps_direct_parent_edges": {
            "edges": reduced_edges,
            "passed": (
                "toponetx_two_hopf_torus_layer_incidence",
                "cvc5_hopf_torus_readout_vector_separation",
            )
            in reduced_edges,
        },
    }


def main() -> int:
    positive = run_positive()
    graveyards = run_graveyards()
    all_pass = bool(
        positive["survives_dependency_reduction"]
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "NetworkX dependency-DAG and transitive-reduction baseline over Hopf receipt names only; no physical "
            "distinguishability, QIT, GStack, axis, bridge, nonclassical, flux, Pauli shortcut, target-system, "
            "or full geometric-constraint-manifold admission"
        ),
        "next_lego_target": "nested_hopf_torus_loop_geometry_baseline",
        "promotion_condition": (
            "May only support later receipt routing after exact physical carrier-evolution and topology receipts "
            "define the dependencies being ordered."
        ),
        "demotion_condition": (
            "Demote if topological order ignores parent receipts, if transitive reduction fails to remove redundant "
            "edges, if missing-parent controls still show the parent, or if cycle detection fails."
        ),
        "blocked_until": "blocked from admission or target-system claims until physical-evolution fixtures and exact lower receipts exist",
        "out_of_scope": [
            "No physical Hopf/Weyl evolution.",
            "No full geometric-constraint-manifold implementation.",
            "No flux representation or Pauli shortcut.",
            "No QIT, GStack, axis, bridge, or nonclassical admission.",
        ],
        "divergence_log": (
            "This NetworkX baseline cross-checks the rustworkx receipt dependency ordering. It can prevent route "
            "collapse in later packets, but it does not add evidence that the geometry itself is true."
        ),
        "operation_sequence": [
            "declare Hopf geometry receipt names as DAG nodes",
            "add dependency edges from lower geometry receipts into the TopoNetX layer receipt",
            "add dependency edges from the TopoNetX layer receipt into cvc5 and z3 readout-vector receipts",
            "compute topological order, ancestors, descendants, and transitive reduction",
            "run missing-parent, cycle, reversed-edge, isolated-node, and reduction-retention graveyards",
        ],
        "carrier_topology": "receipt dependency graph over bounded Hopf geometry and readout-vector fixtures",
        "observable": "topological order, ancestor/descendant sets, transitive-reduction edges, and cycle detection",
        "pass_fail_predicate": (
            "parent geometry receipts precede readout-vector receipts, redundant direct edges reduce away, direct "
            "TopoNetX-to-solver parent edges remain, and adjacent graph controls collapse or invert"
        ),
        "graveyards": [
            "missing TopoNetX parent removes readout ancestor",
            "cycle input is detected by DAG check",
            "reversed edges invert parent order as expected bad control",
            "isolated single receipt has no dependencies",
            "transitive reduction keeps direct parent edges",
        ],
        "baselines": [
            "rustworkx Hopf receipt dependency reduction fixture",
            "TopoNetX two Hopf-torus layer incidence fixture",
            "cvc5 Hopf torus readout-vector separation fixture",
            "z3 Hopf torus readout-vector separation fixture",
        ],
        "alternative_formulations": [
            "rustworkx dependency DAG cross-check",
            "z3 partial-order constraints over receipt nodes",
            "cvc5 partial-order constraints over receipt nodes",
        ],
        "exact_tool_function_needs": {
            "networkx": [
                "DiGraph",
                "topological_sort",
                "ancestors",
                "descendants",
                "transitive_reduction",
                "is_directed_acyclic_graph",
            ],
        },
        "lego_or_coupling_target": "nested_hopf_torus_loop_geometry_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "nodes": NODES,
        "edges": EDGES,
        "positive": positive,
        "graveyards_detail": graveyards,
        "promotion_allowed": False,
        "pass": all_pass,
    }
    results = apply_default_receipt_boundary(results, source_name=f"sim_{NAME}")
    out_path = RESULTS_DIR / f"{NAME}_results.json"
    out_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"name": NAME, "all_pass": all_pass, "result": str(out_path)}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
