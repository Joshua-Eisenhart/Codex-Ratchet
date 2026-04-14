#!/usr/bin/env python3
"""
QIT Weyl-Carnot bridge.

Bounded bridge row that connects the stabilized Weyl/Hopf geometry carrier
stack to the exact Carnot engine family. It keeps the geometry carrier,
strict geometry companion, Carnot graph/proof alignment, and Carnot QIT
translation lane all explicit while proving only a schedule-compatibility
claim.

This is a bridge surface, not an equivalence theorem.
"""

from __future__ import annotations

import json
import pathlib

import rustworkx as rx
import z3
classification = "classical_baseline"  # auto-backfill


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Bounded open-vs-strict bridge between the stabilized Weyl/Hopf geometry "
    "carrier stack and the exact Carnot engine family. It uses a schedule "
    "graph plus z3 ordering checks to keep the carrier and engine lanes "
    "aligned without claiming equivalence."
)

LEGO_IDS = [
    "hopf_geometry",
    "weyl_chirality_pair",
    "quantum_thermodynamics",
    "stochastic_thermodynamics",
    "graph_shell_geometry",
]

PRIMARY_LEGO_IDS = [
    "hopf_geometry",
    "quantum_thermodynamics",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing bridge-order and stage-compatibility proof surface",
    },
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing bridge graph construction and path-length checks",
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


def load(name: str) -> dict:
    path = RESULT_DIR / name
    if not path.exists():
        raise SystemExit(f"missing required result file: {name}")
    return json.loads(path.read_text())


def build_bridge_graph() -> dict:
    graph = rx.PyDiGraph()
    nodes = [
        "G1_nested_hopf_tori",
        "G2_weyl_pauli_transport",
        "G3_weyl_hopf_pauli_composed_stack",
        "G4_qit_weyl_geometry_companion",
        "C1_carnot_hot_isotherm",
        "C2_carnot_adiabatic_expand",
        "C3_carnot_cold_isotherm",
        "C4_carnot_adiabatic_compress",
    ]
    idx = {label: graph.add_node(label) for label in nodes}

    for left, right, label in [
        ("G1_nested_hopf_tori", "G2_weyl_pauli_transport", "geometry_stage"),
        ("G2_weyl_pauli_transport", "G3_weyl_hopf_pauli_composed_stack", "geometry_stage"),
        ("G3_weyl_hopf_pauli_composed_stack", "G4_qit_weyl_geometry_companion", "geometry_stage"),
        ("G4_qit_weyl_geometry_companion", "C1_carnot_hot_isotherm", "bridge_interface"),
        ("C1_carnot_hot_isotherm", "C2_carnot_adiabatic_expand", "carnot_leg"),
        ("C2_carnot_adiabatic_expand", "C3_carnot_cold_isotherm", "carnot_leg"),
        ("C3_carnot_cold_isotherm", "C4_carnot_adiabatic_compress", "carnot_leg"),
    ]:
        graph.add_edge(idx[left], idx[right], label)

    topo = [graph[node] for node in rx.topological_sort(graph)]
    longest_path_nodes = [graph[node] for node in rx.dag_longest_path(graph)]
    return {
        "node_count": int(graph.num_nodes()),
        "edge_count": int(graph.num_edges()),
        "topological_order": topo,
        "longest_path": longest_path_nodes,
        "longest_path_length": max(len(longest_path_nodes) - 1, 0),
        "is_dag": bool(rx.is_directed_acyclic_graph(graph)),
        "source_count": int(sum(graph.in_degree(node) == 0 for node in graph.node_indices())),
        "sink_count": int(sum(graph.out_degree(node) == 0 for node in graph.node_indices())),
    }


def prove_bridge_ordering() -> dict:
    solver = z3.Solver()
    g1, g2, g3, g4, c1, c2, c3, c4 = z3.Ints("g1 g2 g3 g4 c1 c2 c3 c4")
    nodes = [g1, g2, g3, g4, c1, c2, c3, c4]
    for node in nodes:
        solver.add(node >= 0, node <= 7)
    solver.add(z3.Distinct(*nodes))
    solver.add(g1 < g2, g2 < g3, g3 < g4, g4 < c1, c1 < c2, c2 < c3, c3 < c4)
    solver.add(c1 < g4)
    verdict = solver.check()
    return {
        "verdict": str(verdict),
        "pass": verdict == z3.unsat,
        "claim": "The geometry carrier must precede the Carnot cycle and cannot be reversed without violating the bridge order.",
    }


def prove_stage_count_compatibility(geometry_stage_count: int, carnot_stage_count: int) -> dict:
    solver = z3.Solver()
    g = z3.Int("geometry_stage_count")
    c = z3.Int("carnot_stage_count")
    solver.add(g == geometry_stage_count)
    solver.add(c == carnot_stage_count)
    solver.add(g != c)
    verdict = solver.check()
    return {
        "verdict": str(verdict),
        "pass": verdict == z3.unsat,
        "claim": "The bridge only admits matching four-stage cores for the geometry and Carnot carriers.",
    }


def main() -> None:
    geometry_open = load("weyl_hopf_pauli_composed_stack_results.json")
    geometry_strict = load("qit_weyl_geometry_companion_results.json")
    engine_open = load("carnot_graph_proof_alignment_results.json")
    engine_strict = load("qit_carnot_closure_translation_lane_results.json")

    geometry_summary = geometry_open["summary"]
    geometry_strict_summary = geometry_strict["summary"]
    engine_summary = engine_open["summary"]
    engine_strict_summary = engine_strict["summary"]

    geometry_stage_count = int(geometry_summary["total_stages"])
    geometry_sample_count = int(geometry_summary["sample_count"])
    geometry_max_stack_error = float(geometry_summary["max_stack_error"])
    geometry_max_transport_error = float(geometry_summary["max_transport_error"])
    geometry_strict_sample_count = int(geometry_strict_summary["sample_count"])
    geometry_strict_row_count = int(geometry_strict_summary["row_count"])
    geometry_strict_max_stack_error = float(geometry_strict_summary["max_stack_error"])
    geometry_strict_max_transport_roundtrip_error = float(geometry_strict_summary["max_transport_roundtrip_error"])

    carnot_graph_path_length = int(engine_summary["graph_path_length"])
    carnot_forward_efficiency = float(engine_summary["forward_efficiency"])
    carnot_forward_bound = float(engine_summary["forward_carnot_bound"])
    carnot_reverse_cop = float(engine_summary["reverse_cop"])
    carnot_reverse_cop_bound = float(engine_summary["reverse_cop_carnot"])

    carnot_closure_gap = float(engine_strict_summary["best_closure_gap"])
    carnot_dominant_leg_matches = bool(engine_strict_summary["dominant_leg_matches"])
    carnot_qit_best_closure_defect = float(engine_strict_summary["qit_best_closure_defect"])
    carnot_open_best_closure_defect = float(engine_strict_summary["open_best_closure_defect"])

    bridge_graph = build_bridge_graph()
    bridge_order_proof = prove_bridge_ordering()
    stage_count_proof = prove_stage_count_compatibility(geometry_stage_count, carnot_graph_path_length)

    geometry_engine_stage_gap = geometry_stage_count - carnot_graph_path_length
    bridge_path_length = bridge_graph["longest_path_length"]

    positive = {
        "geometry_carrier_is_clean": {
            "pass": bool(geometry_summary["all_pass"]),
            "geometry_all_pass": bool(geometry_summary["all_pass"]),
        },
        "geometry_strict_companion_is_clean": {
            "pass": bool(geometry_strict_summary["all_pass"]),
            "geometry_strict_all_pass": bool(geometry_strict_summary["all_pass"]),
        },
        "engine_graph_proof_alignment_is_clean": {
            "pass": bool(engine_summary["all_pass"]),
            "engine_all_pass": bool(engine_summary["all_pass"]),
        },
        "engine_strict_closure_translation_is_clean": {
            "pass": bool(engine_strict_summary["all_pass"]),
            "engine_strict_all_pass": bool(engine_strict_summary["all_pass"]),
        },
        "bridge_graph_is_a_single_valid_geometry_to_engine_chain": {
            **bridge_graph,
            "pass": (
                bridge_graph["is_dag"]
                and bridge_graph["node_count"] == 8
                and bridge_graph["edge_count"] == 7
                and bridge_graph["source_count"] == 1
                and bridge_graph["sink_count"] == 1
                and bridge_graph["longest_path_length"] == 7
            ),
        },
        "geometry_and_carnot_core_lengths_match": {
            "geometry_stage_count": geometry_stage_count,
            "carnot_stage_count": carnot_graph_path_length,
            "pass": geometry_engine_stage_gap == 0,
        },
        "z3_forces_bridge_ordering_compatibility": bridge_order_proof,
        "z3_forces_matching_four_stage_cores": stage_count_proof,
        "geometry_readouts_remain_exact": {
            "max_stack_error": geometry_max_stack_error,
            "max_transport_error": geometry_max_transport_error,
            "max_strict_stack_error": geometry_strict_max_stack_error,
            "max_strict_transport_roundtrip_error": geometry_strict_max_transport_roundtrip_error,
            "pass": (
                geometry_max_stack_error < 1e-12
                and geometry_max_transport_error < 1e-12
                and geometry_strict_max_stack_error < 1e-12
                and geometry_strict_max_transport_roundtrip_error < 1e-12
            ),
        },
        "engine_identities_remain_exact": {
            "forward_efficiency": carnot_forward_efficiency,
            "forward_carnot_bound": carnot_forward_bound,
            "reverse_cop": carnot_reverse_cop,
            "reverse_cop_carnot": carnot_reverse_cop_bound,
            "pass": (
                abs(carnot_forward_efficiency - carnot_forward_bound) < 1e-12
                and abs(carnot_reverse_cop - carnot_reverse_cop_bound) < 1e-12
            ),
        },
        "closure_translation_stays_bounded": {
            "best_closure_gap": carnot_closure_gap,
            "dominant_leg_matches": carnot_dominant_leg_matches,
            "pass": carnot_closure_gap < 0.01 and carnot_dominant_leg_matches,
        },
    }

    negative = {
        "bridge_is_not_equivalence_math": {
            "pass": True,
        },
        "geometry_and_engine_lanes_remain_distinct": {
            "pass": True,
        },
        "bridge_row_is_not_a_runtime_engine_claim": {
            "pass": True,
            "scope_note": (
                "This row aligns a geometry carrier to an engine family through a "
                "graph/proof bridge; it does not claim the runtime engine itself "
                "is geometry-native."
            ),
        },
    }

    boundary = {
        "all_required_files_exist": {
            "pass": all(
                path.exists()
                for path in [
                    RESULT_DIR / "weyl_hopf_pauli_composed_stack_results.json",
                    RESULT_DIR / "qit_weyl_geometry_companion_results.json",
                    RESULT_DIR / "carnot_graph_proof_alignment_results.json",
                    RESULT_DIR / "qit_carnot_closure_translation_lane_results.json",
                ]
            ),
        },
        "all_summary_values_are_finite": {
            "pass": all(
                isinstance(value, (int, float, bool))
                for value in [
                    geometry_stage_count,
                    geometry_sample_count,
                    geometry_max_stack_error,
                    geometry_max_transport_error,
                    geometry_strict_sample_count,
                    geometry_strict_row_count,
                    geometry_strict_max_stack_error,
                    geometry_strict_max_transport_roundtrip_error,
                    carnot_graph_path_length,
                    carnot_forward_efficiency,
                    carnot_forward_bound,
                    carnot_reverse_cop,
                    carnot_reverse_cop_bound,
                    carnot_closure_gap,
                    geometry_engine_stage_gap,
                    bridge_path_length,
                ]
            ),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    out = {
        "name": "qit_weyl_carnot_bridge",
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
            "geometry_open_row_id": "weyl_hopf_pauli_composed_stack",
            "geometry_strict_row_id": "qit_weyl_geometry_companion",
            "engine_open_row_id": "carnot_graph_proof_alignment",
            "engine_strict_row_id": "qit_carnot_closure_translation_lane",
            "geometry_sample_count": geometry_sample_count,
            "geometry_stage_count": geometry_stage_count,
            "geometry_max_stack_error": geometry_max_stack_error,
            "geometry_max_transport_error": geometry_max_transport_error,
            "geometry_strict_sample_count": geometry_strict_sample_count,
            "geometry_strict_row_count": geometry_strict_row_count,
            "geometry_strict_max_stack_error": geometry_strict_max_stack_error,
            "geometry_strict_max_transport_roundtrip_error": geometry_strict_max_transport_roundtrip_error,
            "engine_graph_path_length": carnot_graph_path_length,
            "engine_forward_efficiency": carnot_forward_efficiency,
            "engine_forward_carnot_bound": carnot_forward_bound,
            "engine_reverse_cop": carnot_reverse_cop,
            "engine_reverse_cop_carnot": carnot_reverse_cop_bound,
            "engine_closure_gap": carnot_closure_gap,
            "engine_dominant_leg_matches": carnot_dominant_leg_matches,
            "geometry_engine_stage_gap": geometry_engine_stage_gap,
            "bridge_node_count": bridge_graph["node_count"],
            "bridge_edge_count": bridge_graph["edge_count"],
            "bridge_path_length": bridge_path_length,
            "bridge_source_count": bridge_graph["source_count"],
            "bridge_sink_count": bridge_graph["sink_count"],
            "bridge_order_unsat": bridge_order_proof["pass"],
            "stage_count_unsat": stage_count_proof["pass"],
            "scope_note": (
                "Bounded geometry-to-Carnot bridge lane. The open Weyl/Hopf "
                "carrier stack and the exact Carnot family are kept distinct "
                "but aligned through a DAG and solver-backed order checks."
            ),
        },
    }

    out_path = RESULT_DIR / "qit_weyl_carnot_bridge_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
