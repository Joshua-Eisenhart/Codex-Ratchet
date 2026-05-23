#!/usr/bin/env python3
"""rustworkx Hopf receipt dependency reduction baseline."""

from __future__ import annotations

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import json
from pathlib import Path

import rustworkx as rx
from receipt_boundary import apply_default_receipt_boundary


NAME = "rustworkx_hopf_receipt_dependency_reduction"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "PyDiGraph, topological_sort, ancestors, descendants, and transitive_reduction check the bounded Hopf receipt dependency DAG",
    }
}
TOOL_INTEGRATION_DEPTH = {"rustworkx": "load_bearing"}

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


def build_graph(edges: list[tuple[str, str]]) -> tuple[rx.PyDiGraph, dict[str, int]]:
    graph = rx.PyDiGraph(check_cycle=True)
    indices = {name: graph.add_node(name) for name in NODES}
    for source, target in edges:
        graph.add_edge(indices[source], indices[target], "depends")
    return graph, indices


def edge_names(graph: rx.PyDiGraph) -> list[tuple[str, str]]:
    names = []
    for source, target in graph.edge_list():
        names.append((graph[source], graph[target]))
    return sorted(names)


def transitive_reduction_graph(graph: rx.PyDiGraph) -> rx.PyDiGraph:
    reduction = rx.transitive_reduction(graph)
    if isinstance(reduction, tuple):
        return reduction[0]
    return reduction


def node_names(graph: rx.PyDiGraph, indices: set[int]) -> list[str]:
    return sorted(graph[idx] for idx in indices)


def run_positive() -> dict[str, object]:
    graph, indices = build_graph(EDGES)
    order = [graph[idx] for idx in rx.topological_sort(graph)]
    reduced = transitive_reduction_graph(graph)
    ancestors_cvc5 = node_names(graph, rx.ancestors(graph, indices["cvc5_hopf_torus_readout_vector_separation"]))
    descendants_sympy = node_names(graph, rx.descendants(graph, indices["sympy_hopf_loop_holonomy_area_dependence"]))
    reduced_edges = edge_names(reduced)
    redundant_edges_removed = sorted(set(EDGES) - set(reduced_edges))
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
    graph, indices = build_graph(EDGES)
    missing_toponetx_edges = [edge for edge in EDGES if edge[0] != "toponetx_two_hopf_torus_layer_incidence"]
    missing_graph, missing_indices = build_graph(missing_toponetx_edges)
    missing_ancestors = node_names(
        missing_graph,
        rx.ancestors(missing_graph, missing_indices["cvc5_hopf_torus_readout_vector_separation"]),
    )

    cycle_error = None
    try:
        cyclic = rx.PyDiGraph(check_cycle=True)
        a = cyclic.add_node("toponetx_two_hopf_torus_layer_incidence")
        b = cyclic.add_node("cvc5_hopf_torus_readout_vector_separation")
        cyclic.add_edge(a, b, "depends")
        cyclic.add_edge(b, a, "depends")
    except Exception as exc:  # rustworkx raises on checked-cycle insertion.
        cycle_error = type(exc).__name__

    reversed_edges = [
        ("toponetx_two_hopf_torus_layer_incidence", "sympy_hopf_loop_holonomy_area_dependence"),
        ("toponetx_two_hopf_torus_layer_incidence", "scipy_hopf_horizontal_lift_chi_shift"),
        ("toponetx_two_hopf_torus_layer_incidence", "gudhi_hopf_torus_fiber_base_homology"),
    ]
    reversed_graph, _ = build_graph(reversed_edges)
    reversed_order = [reversed_graph[idx] for idx in rx.topological_sort(reversed_graph)]

    isolated = rx.PyDiGraph(check_cycle=True)
    only = isolated.add_node("single_receipt")
    return {
        "missing_toponetx_parent_removes_readout_ancestor": {
            "ancestors_of_cvc5_readout": missing_ancestors,
            "passed": "toponetx_two_hopf_torus_layer_incidence" not in missing_ancestors,
        },
        "cycle_input_rejected_by_checked_graph": {
            "error_type": cycle_error,
            "passed": cycle_error is not None,
        },
        "reversed_edges_invert_parent_order_as_expected_bad_control": {
            "topological_order": reversed_order,
            "expected_inversion": True,
            "passed": reversed_order.index("toponetx_two_hopf_torus_layer_incidence")
            < reversed_order.index("sympy_hopf_loop_holonomy_area_dependence"),
        },
        "isolated_single_receipt_has_no_dependencies": {
            "ancestors": list(rx.ancestors(isolated, only)),
            "descendants": list(rx.descendants(isolated, only)),
            "passed": not rx.ancestors(isolated, only) and not rx.descendants(isolated, only),
        },
        "transitive_reduction_keeps_direct_parent_edges": {
            "edges": edge_names(transitive_reduction_graph(graph)),
            "passed": (
                "toponetx_two_hopf_torus_layer_incidence",
                "cvc5_hopf_torus_readout_vector_separation",
            )
            in edge_names(transitive_reduction_graph(graph)),
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
            "rustworkx dependency-DAG and transitive-reduction baseline over Hopf receipt names only; "
            "no physical distinguishability, QIT, GStack, axis, bridge, nonclassical, flux, Pauli shortcut, "
            "target-system, or full geometric-constraint-manifold admission"
        ),
        "next_lego_target": "nested_hopf_torus_loop_geometry_baseline",
        "promotion_condition": (
            "May only support later receipt routing after exact physical carrier-evolution and topology receipts "
            "define the dependencies being ordered."
        ),
        "demotion_condition": (
            "Demote if topological order ignores parent receipts, if transitive reduction fails to remove redundant "
            "edges, if missing-parent controls still show the parent, or if cycle insertion is accepted."
        ),
        "blocked_until": "blocked from admission or target-system claims until physical-evolution fixtures and exact lower receipts exist",
        "out_of_scope": [
            "No physical Hopf/Weyl evolution.",
            "No full geometric-constraint-manifold implementation.",
            "No flux representation or Pauli shortcut.",
            "No QIT, GStack, axis, bridge, or nonclassical admission.",
        ],
        "divergence_log": (
            "This baseline checks receipt dependency ordering only. It can prevent route collapse in later packets, "
            "but it does not add evidence that the geometry itself is true."
        ),
        "operation_sequence": [
            "declare Hopf geometry receipt names as DAG nodes",
            "add dependency edges from lower geometry receipts into the TopoNetX layer receipt",
            "add dependency edges from the TopoNetX layer receipt into cvc5 and z3 readout-vector receipts",
            "compute topological order, ancestors, descendants, and transitive reduction",
            "run missing-parent, cycle, reversed-edge, isolated-node, and reduction-retention graveyards",
        ],
        "carrier_topology": "receipt dependency graph over bounded Hopf geometry and readout-vector fixtures",
        "observable": "topological order, ancestor/descendant sets, transitive-reduction edges, and checked-cycle rejection",
        "pass_fail_predicate": (
            "parent geometry receipts precede readout-vector receipts, redundant direct edges reduce away, direct "
            "TopoNetX-to-solver parent edges remain, and adjacent graph controls collapse or invert"
        ),
        "graveyards": [
            "missing TopoNetX parent removes readout ancestor",
            "cycle input is rejected by checked graph",
            "reversed edges invert parent order as expected bad control",
            "isolated single receipt has no dependencies",
            "transitive reduction keeps direct parent edges",
        ],
        "baselines": [
            "TopoNetX two Hopf-torus layer incidence fixture",
            "cvc5 Hopf torus readout-vector separation fixture",
            "z3 Hopf torus readout-vector separation fixture",
            "rustworkx DAG reachability micro fixture",
        ],
        "alternative_formulations": [
            "NetworkX dependency DAG cross-check",
            "z3 partial-order constraints over receipt nodes",
            "cvc5 partial-order constraints over receipt nodes",
        ],
        "exact_tool_function_needs": {
            "rustworkx": [
                "PyDiGraph",
                "topological_sort",
                "ancestors",
                "descendants",
                "transitive_reduction",
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
    print(f"Results written to {out_path}")
    print(f"PASS={results['pass']}  name={NAME}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
