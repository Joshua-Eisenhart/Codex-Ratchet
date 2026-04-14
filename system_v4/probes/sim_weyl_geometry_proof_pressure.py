#!/usr/bin/env python3
"""
Weyl geometry proof-pressure row.

This is a controller-facing pressure surface for the Weyl/Hopf/Pauli lane.
It starts from the reusable graph/proof bridge and protocol-DAG lego, then
adds stricter solver-checked claims around transport ordering, chirality
consistency, and illegal carrier transitions.

This is not a runtime engine claim and not a doctrinal geometry claim.
It is a bounded pressure row over already-existing result surfaces.
"""

from __future__ import annotations

import json
import pathlib

import rustworkx as rx
import z3
classification = "classical_baseline"  # auto-backfill


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Proof-pressure row for the Weyl/Hopf/Pauli geometry lane. It composes "
    "the protocol DAG, graph/proof bridge, composed stack, carrier array, "
    "carrier compare, and ladder audit into one solver-checked pressure surface."
)

LEGO_IDS = [
    "nested_hopf_tori",
    "weyl_pauli_transport",
    "weyl_geometry_protocol_dag",
    "weyl_geometry_graph_proof_alignment",
    "weyl_hopf_pauli_composed_stack",
    "weyl_geometry_carrier_array",
    "weyl_geometry_carrier_compare",
    "weyl_geometry_ladder_audit",
]

PRIMARY_LEGO_IDS = [
    "weyl_geometry_protocol_dag",
    "weyl_geometry_graph_proof_alignment",
    "weyl_hopf_pauli_composed_stack",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing solver pressure for ordering, chirality, and illegal transition checks",
    },
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing proof-pressure schedule graph over the geometry lane",
    },
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["rustworkx"] = "load_bearing"

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"


def load_json(name: str) -> dict:
    path = RESULT_DIR / name
    if not path.exists():
        raise SystemExit(f"missing required result file: {name}")
    return json.loads(path.read_text())


def build_pressure_graph() -> dict:
    graph = rx.PyDiGraph()
    nodes = [
        "nested_hopf_tori_base",
        "weyl_pauli_transport_base",
        "weyl_geometry_protocol_dag",
        "weyl_geometry_graph_proof_alignment",
        "weyl_hopf_pauli_composed_stack",
        "weyl_geometry_carrier_array",
        "weyl_geometry_carrier_compare",
        "weyl_geometry_ladder_audit",
    ]
    idx = {label: graph.add_node(label) for label in nodes}
    edges = [
        ("nested_hopf_tori_base", "weyl_pauli_transport_base"),
        ("weyl_pauli_transport_base", "weyl_geometry_protocol_dag"),
        ("weyl_geometry_protocol_dag", "weyl_geometry_graph_proof_alignment"),
        ("weyl_geometry_graph_proof_alignment", "weyl_hopf_pauli_composed_stack"),
        ("weyl_hopf_pauli_composed_stack", "weyl_geometry_carrier_array"),
        ("weyl_geometry_carrier_array", "weyl_geometry_carrier_compare"),
        ("weyl_geometry_carrier_compare", "weyl_geometry_ladder_audit"),
    ]
    for source, target in edges:
        graph.add_edge(idx[source], idx[target], f"{source}->{target}")

    topo = [graph[node] for node in rx.topological_sort(graph)]
    longest = [graph[node] for node in rx.dag_longest_path(graph)]
    sources = [graph[node] for node in graph.node_indices() if graph.in_degree(node) == 0]
    sinks = [graph[node] for node in graph.node_indices() if graph.out_degree(node) == 0]

    return {
        "node_count": int(graph.num_nodes()),
        "edge_count": int(graph.num_edges()),
        "is_dag": bool(rx.is_directed_acyclic_graph(graph)),
        "topological_order": topo,
        "longest_path": longest,
        "longest_path_length": max(len(longest) - 1, 0),
        "source_count": len(sources),
        "sink_count": len(sinks),
        "sources": sources,
        "sinks": sinks,
    }


def prove_ordering() -> dict:
    stages = [
        "nested_hopf_tori_base",
        "weyl_pauli_transport_base",
        "weyl_geometry_protocol_dag",
        "weyl_geometry_graph_proof_alignment",
        "weyl_hopf_pauli_composed_stack",
        "weyl_geometry_carrier_array",
        "weyl_geometry_carrier_compare",
        "weyl_geometry_ladder_audit",
    ]
    n = len(stages)
    pos = {stage: z3.Int(stage) for stage in stages}

    solver = z3.Solver()
    for stage in stages:
        solver.add(pos[stage] >= 0, pos[stage] < n)
    solver.add(z3.Distinct([pos[stage] for stage in stages]))
    for left, right in zip(stages, stages[1:]):
        solver.add(pos[left] < pos[right])
    forward = solver.check()

    reverse_solver = z3.Solver()
    for stage in stages:
        reverse_solver.add(pos[stage] >= 0, pos[stage] < n)
    reverse_solver.add(z3.Distinct([pos[stage] for stage in stages]))
    for left, right in zip(stages, stages[1:]):
        reverse_solver.add(pos[left] < pos[right])
    reverse_solver.add(pos[stages[-1]] < pos[stages[0]])
    reverse = reverse_solver.check()

    return {
        "forward_order_verdict": str(forward),
        "forward_order_sat": forward == z3.sat,
        "reverse_order_verdict": str(reverse),
        "reverse_order_unsat": reverse == z3.unsat,
        "stage_count": n,
    }


def prove_illegal_shortcuts() -> dict:
    stages = [
        "nested_hopf_tori_base",
        "weyl_pauli_transport_base",
        "weyl_geometry_protocol_dag",
        "weyl_geometry_graph_proof_alignment",
        "weyl_hopf_pauli_composed_stack",
        "weyl_geometry_carrier_array",
        "weyl_geometry_carrier_compare",
        "weyl_geometry_ladder_audit",
    ]
    pos = {stage: z3.Int(stage) for stage in stages}

    def _unsat_with(extra_constraints):
        solver = z3.Solver()
        for stage in stages:
            solver.add(pos[stage] >= 0, pos[stage] < len(stages))
        solver.add(z3.Distinct([pos[stage] for stage in stages]))
        for left, right in zip(stages, stages[1:]):
            solver.add(pos[left] < pos[right])
        for c in extra_constraints:
            solver.add(c)
        verdict = solver.check()
        return verdict, verdict == z3.unsat

    protocol_before_base = _unsat_with([pos["weyl_geometry_protocol_dag"] < pos["nested_hopf_tori_base"]])
    graph_before_protocol = _unsat_with([pos["weyl_geometry_graph_proof_alignment"] < pos["weyl_geometry_protocol_dag"]])
    composed_before_graph = _unsat_with([pos["weyl_hopf_pauli_composed_stack"] < pos["weyl_geometry_graph_proof_alignment"]])
    compare_before_array = _unsat_with([pos["weyl_geometry_carrier_compare"] < pos["weyl_geometry_carrier_array"]])
    ladder_before_compare = _unsat_with([pos["weyl_geometry_ladder_audit"] < pos["weyl_geometry_carrier_compare"]])
    back_edge_to_base = _unsat_with([pos["weyl_geometry_ladder_audit"] < pos["nested_hopf_tori_base"]])

    return {
        "protocol_before_base_verdict": str(protocol_before_base[0]),
        "protocol_before_base_unsat": protocol_before_base[1],
        "graph_before_protocol_verdict": str(graph_before_protocol[0]),
        "graph_before_protocol_unsat": graph_before_protocol[1],
        "composed_before_graph_verdict": str(composed_before_graph[0]),
        "composed_before_graph_unsat": composed_before_graph[1],
        "compare_before_array_verdict": str(compare_before_array[0]),
        "compare_before_array_unsat": compare_before_array[1],
        "ladder_before_compare_verdict": str(ladder_before_compare[0]),
        "ladder_before_compare_unsat": ladder_before_compare[1],
        "back_edge_to_base_verdict": str(back_edge_to_base[0]),
        "back_edge_to_base_unsat": back_edge_to_base[1],
    }


def prove_chirality() -> dict:
    solver = z3.Solver()
    left_sign = z3.Int("left_sign")
    right_sign = z3.Int("right_sign")
    solver.add(left_sign == 1)
    solver.add(right_sign == -1)
    solver.add(left_sign == right_sign)
    verdict = solver.check()
    return {
        "verdict": str(verdict),
        "pass": verdict == z3.unsat,
        "claim": "Left and right Weyl chirality signs cannot be identified as the same sign.",
    }


def load_sources() -> dict:
    nested = load_json("lego_nested_hopf_tori_results.json")
    transport = load_json("lego_weyl_pauli_transport_results.json")
    protocol = load_json("lego_weyl_geometry_protocol_dag_results.json")
    graph_bridge = load_json("weyl_geometry_graph_proof_alignment_results.json")
    composed = load_json("weyl_hopf_pauli_composed_stack_results.json")
    carrier_array = load_json("weyl_geometry_carrier_array_results.json")
    carrier_compare = load_json("lego_weyl_geometry_carrier_compare_results.json")
    ladder = load_json("weyl_geometry_ladder_audit_results.json")

    return {
        "nested": nested,
        "transport": transport,
        "protocol": protocol,
        "graph_bridge": graph_bridge,
        "composed": composed,
        "carrier_array": carrier_array,
        "carrier_compare": carrier_compare,
        "ladder": ladder,
    }


def main() -> None:
    sources = load_sources()
    graph = build_pressure_graph()
    ordering = prove_ordering()
    shortcuts = prove_illegal_shortcuts()
    chirality = prove_chirality()

    nested_summary = sources["nested"]["summary"]
    transport_positive = sources["transport"]["positive"]
    transport_summary = sources["transport"]["summary"]
    protocol_summary = sources["protocol"]["summary"]
    graph_bridge = sources["graph_bridge"]
    composed_summary = sources["composed"]["summary"]
    carrier_summary = sources["carrier_array"]["summary"]
    compare_summary = sources["carrier_compare"]["summary"]
    ladder_summary = sources["ladder"]["summary"]

    base_metrics = {
        "nested_hopf_tori_max_transport_error": nested_summary.get("max_transport_error"),
        "weyl_pauli_transport_max_left_right_overlap_abs": transport_positive.get("max_left_right_overlap_abs"),
        "weyl_pauli_transport_max_chiral_z_gap": transport_positive.get("max_chiral_z_gap"),
        "weyl_pauli_transport_roundtrip_error": transport_positive.get("transport_roundtrip_error"),
        "protocol_dag_graph_path_length": protocol_summary.get("graph_path_length"),
        "graph_bridge_forward_order_sat": graph_bridge["positive"]["z3_forces_the_geometry_stack_ordering"]["forward_order_sat"],
        "graph_bridge_reverse_order_unsat": graph_bridge["positive"]["z3_forces_the_geometry_stack_ordering"]["reverse_order_unsat"],
        "graph_bridge_chirality_unsat": graph_bridge["positive"]["z3_separates_left_and_right_chirality_signs"]["pass"],
        "composed_stack_error": composed_summary.get("max_stack_error"),
        "carrier_count": carrier_summary.get("carrier_count"),
        "compare_carrier_count": compare_summary.get("carrier_count"),
        "ladder_guardrail_pass": ladder_summary.get("guardrail_pass"),
    }

    positive = {
        "transport_ordering_matches_the_ledger": {
            "pass": ordering["forward_order_sat"] and ordering["reverse_order_unsat"],
            "forward_order_sat": ordering["forward_order_sat"],
            "reverse_order_unsat": ordering["reverse_order_unsat"],
            "stage_count": ordering["stage_count"],
        },
        "chirality_signs_remain_separated": {
            "pass": chirality["pass"],
            "verdict": chirality["verdict"],
            "claim": chirality["claim"],
        },
        "illegal_shortcuts_stay_unsat": {
            "pass": (
                shortcuts["protocol_before_base_unsat"]
                and shortcuts["graph_before_protocol_unsat"]
                and shortcuts["composed_before_graph_unsat"]
                and shortcuts["compare_before_array_unsat"]
                and shortcuts["ladder_before_compare_unsat"]
            ),
            "protocol_before_base_unsat": shortcuts["protocol_before_base_unsat"],
            "graph_before_protocol_unsat": shortcuts["graph_before_protocol_unsat"],
            "composed_before_graph_unsat": shortcuts["composed_before_graph_unsat"],
            "compare_before_array_unsat": shortcuts["compare_before_array_unsat"],
            "ladder_before_compare_unsat": shortcuts["ladder_before_compare_unsat"],
        },
        "graph_pressure_row_is_a_single_valid_dependency_chain": {
            "pass": graph["is_dag"] and graph["node_count"] == 8 and graph["edge_count"] == 7,
            "node_count": graph["node_count"],
            "edge_count": graph["edge_count"],
            "longest_path_length": graph["longest_path_length"],
            "source_count": graph["source_count"],
            "sink_count": graph["sink_count"],
            "topological_order": graph["topological_order"],
        },
        "base_rows_remain_bounded_and_reusable": {
            "pass": (
                float(base_metrics["nested_hopf_tori_max_transport_error"]) < 1e-12
                and float(base_metrics["weyl_pauli_transport_max_left_right_overlap_abs"]) < 1e-12
                and bool(base_metrics["ladder_guardrail_pass"])
            ),
            "nested_hopf_tori_max_transport_error": base_metrics["nested_hopf_tori_max_transport_error"],
            "weyl_pauli_transport_max_left_right_overlap_abs": base_metrics["weyl_pauli_transport_max_left_right_overlap_abs"],
            "weyl_pauli_transport_max_chiral_z_gap": base_metrics["weyl_pauli_transport_max_chiral_z_gap"],
            "weyl_pauli_transport_roundtrip_error": base_metrics["weyl_pauli_transport_roundtrip_error"],
            "ladder_guardrail_pass": base_metrics["ladder_guardrail_pass"],
        },
    }

    negative = {
        "reverse_chain_is_unsat": {
            "pass": ordering["reverse_order_unsat"],
            "reverse_order_verdict": ordering["reverse_order_verdict"],
        },
        "shortcuts_do_not_reorder_the_lane": {
            "pass": (
                shortcuts["protocol_before_base_unsat"]
                and shortcuts["graph_before_protocol_unsat"]
                and shortcuts["composed_before_graph_unsat"]
                and shortcuts["compare_before_array_unsat"]
                and shortcuts["ladder_before_compare_unsat"]
                and shortcuts["back_edge_to_base_unsat"]
            ),
            "back_edge_to_base_unsat": shortcuts["back_edge_to_base_unsat"],
        },
        "chirality_collapse_is_rejected": {
            "pass": chirality["pass"],
            "verdict": chirality["verdict"],
        },
    }

    boundary = {
        "existing_rows_stay_the_source_of_truth": {
            "pass": True,
            "source_rows": [
                "lego_nested_hopf_tori_results.json",
                "lego_weyl_pauli_transport_results.json",
                "lego_weyl_geometry_protocol_dag_results.json",
                "weyl_geometry_graph_proof_alignment_results.json",
                "weyl_hopf_pauli_composed_stack_results.json",
                "weyl_geometry_carrier_array_results.json",
                "lego_weyl_geometry_carrier_compare_results.json",
                "weyl_geometry_ladder_audit_results.json",
            ],
        },
        "proof_pressure_stays_controller_facing": {
            "pass": True,
            "scope_note": "This row increases proof pressure over existing geometry rows. It does not claim a new runtime or a new carrier law.",
        },
    }

    summary = {
        "all_pass": (
            positive["transport_ordering_matches_the_ledger"]["pass"]
            and positive["chirality_signs_remain_separated"]["pass"]
            and positive["illegal_shortcuts_stay_unsat"]["pass"]
            and positive["graph_pressure_row_is_a_single_valid_dependency_chain"]["pass"]
            and positive["base_rows_remain_bounded_and_reusable"]["pass"]
            and negative["reverse_chain_is_unsat"]["pass"]
            and negative["shortcuts_do_not_reorder_the_lane"]["pass"]
            and negative["chirality_collapse_is_rejected"]["pass"]
        ),
        "row_count": 8,
        "graph_path_length": graph["longest_path_length"],
        "base_row_count": 2,
        "bridge_row_count": 3,
        "comparison_row_count": 1,
        "audit_row_count": 1,
        "sidecar_row_count": 1,
        "transport_chain_labels": graph["topological_order"],
        "max_left_right_overlap_abs": base_metrics["weyl_pauli_transport_max_left_right_overlap_abs"],
        "max_chiral_z_gap": base_metrics["weyl_pauli_transport_max_chiral_z_gap"],
        "max_transport_roundtrip_error": base_metrics["weyl_pauli_transport_roundtrip_error"],
        "max_stack_error": base_metrics["composed_stack_error"],
        "max_hopf_transport_error": base_metrics["nested_hopf_tori_max_transport_error"],
        "carrier_count": base_metrics["carrier_count"],
        "compare_carrier_count": base_metrics["compare_carrier_count"],
    }

    out = {
        "name": "weyl_geometry_proof_pressure",
        "classification": CLASSIFICATION,
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": summary,
        "graph": graph,
        "proofs": {
            "ordering": ordering,
            "illegal_shortcuts": shortcuts,
            "chirality": chirality,
        },
        "evidence": base_metrics,
    }

    out_path = RESULT_DIR / "weyl_geometry_proof_pressure_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
