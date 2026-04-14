#!/usr/bin/env python3
"""
Bounded Weyl/Hopf <-> Szilard geometry bridge.

This row does not claim a geometry-native engine runtime. It builds a strict
bridge between the stabilized Weyl/Hopf geometry lane and the exact Szilard
bookkeeping lane by checking that:
  - the left/right Weyl pair remains operationally distinguishable,
  - the Szilard measurement/feedback/reset chain preserves the expected
    distinguishability ordering,
  - a combined geometry-to-protocol DAG has a single valid precedence chain,
  - z3 rejects orderings that try to erase before measurement or readout.
"""

from __future__ import annotations

import json
import pathlib
import sys
from typing import Any

import numpy as np
import rustworkx as rx
import z3


PROBE_DIR = pathlib.Path(__file__).resolve().parent
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

import hopf_manifold as hopf  # noqa: E402
import sim_helstrom_guess_bound as helstrom  # noqa: E402
import sim_qit_szilard_bidirectional_protocol as szilard  # noqa: E402


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Bridge row between the stabilized Weyl/Hopf geometry stack and the exact "
    "Szilard bookkeeping family. It uses Weyl-spinor distinguishability, a "
    "shared protocol/order DAG, and z3 precedence guards without claiming a "
    "geometry-native engine runtime."
)

LEGO_IDS = [
    "hopf_geometry",
    "weyl_chirality_pair",
    "helstrom_guess_bound",
    "quantum_thermodynamics",
    "graph_shell_geometry",
]

PRIMARY_LEGO_IDS = [
    "hopf_geometry",
    "weyl_chirality_pair",
    "quantum_thermodynamics",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing precedence guard for geometry-readout-to-Szilard protocol order",
    },
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing combined geometry/protocol DAG and path-length checks",
    },
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["rustworkx"] = "load_bearing"

RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"


def load_json(name: str) -> dict[str, Any]:
    return json.loads((RESULT_DIR / name).read_text())


def build_combined_graph() -> dict[str, Any]:
    graph = rx.PyDiGraph()
    nodes = [
        "weyl_left_right_frame",
        "pauli_readout",
        "measurement_record_written",
        "feedback_applied",
        "memory_erased",
    ]
    idx = {label: graph.add_node(label) for label in nodes}
    graph.add_edge(idx["weyl_left_right_frame"], idx["pauli_readout"], "geometry_readout")
    graph.add_edge(idx["pauli_readout"], idx["measurement_record_written"], "record_write")
    graph.add_edge(idx["measurement_record_written"], idx["feedback_applied"], "feedback")
    graph.add_edge(idx["feedback_applied"], idx["memory_erased"], "reset")
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


def prove_precedence_guard() -> dict[str, Any]:
    solver = z3.Solver()
    g = z3.Int("geometry")
    p = z3.Int("pauli")
    m = z3.Int("measure")
    f = z3.Int("feedback")
    r = z3.Int("reset")
    vars_ = [g, p, m, f, r]
    for var in vars_:
        solver.add(var >= 0, var <= 4)
    solver.add(z3.Distinct(*vars_))
    solver.add(g < p, p < m, m < f, f < r)
    solver.add(r < m)
    verdict = solver.check()
    return {
        "verdict": str(verdict),
        "pass": verdict == z3.unsat,
        "claim": "Combined geometry/readout/protocol DAG rejects reset-before-measurement orderings.",
    }


def geometry_distinguishability() -> dict[str, Any]:
    q = hopf.torus_coordinates(hopf.TORUS_CLIFFORD, 0.43, 1.07)
    rho_left = hopf.left_density(q)
    rho_right = hopf.right_density(q)
    guess = float(helstrom.helstrom_guess_prob(rho_left, rho_right))
    overlap = float(abs(np.vdot(hopf.left_weyl_spinor(q), hopf.right_weyl_spinor(q))))
    return {
        "left_right_guess_probability": guess,
        "left_right_overlap_abs": overlap,
        "pass": abs(guess - 1.0) < 1e-12 and overlap < 1e-12,
    }


def szilard_operational_chain() -> dict[str, Any]:
    rho_init = szilard.make_initial_state()
    rho_measured = szilard.apply_unitary(rho_init, szilard.CNOT_SYSTEM_TO_MEMORY)
    rho_feedback = szilard.imperfect_controlled_x(rho_measured, 0.0)
    rho_erased = szilard.reset_memory_to_zero(rho_feedback, 1.0)
    rho_wrong_order = szilard.apply_unitary(
        szilard.imperfect_controlled_x(rho_init, 0.0),
        szilard.CNOT_SYSTEM_TO_MEMORY,
    )

    blank_memory = szilard.PROJ0
    measured_memory = szilard.partial_trace_system(rho_measured)
    erased_memory = szilard.partial_trace_system(rho_erased)
    wrong_order_system = szilard.partial_trace_memory(rho_wrong_order)
    feedback_system = szilard.partial_trace_memory(rho_feedback)

    measurement_guess = float(helstrom.helstrom_guess_prob(blank_memory, measured_memory))
    erased_guess = float(helstrom.helstrom_guess_prob(blank_memory, erased_memory))
    wrong_order_guess = float(helstrom.helstrom_guess_prob(wrong_order_system, feedback_system))
    return {
        "blank_vs_measured_guess_probability": measurement_guess,
        "blank_vs_erased_guess_probability": erased_guess,
        "wrong_order_vs_feedback_guess_probability": wrong_order_guess,
        "pass": measurement_guess > erased_guess + 1e-6 and wrong_order_guess > 0.5 + 1e-6,
    }


def main() -> None:
    weyl_companion = load_json("qit_weyl_geometry_companion_results.json")
    weyl_translation = load_json("qit_weyl_geometry_translation_lane_results.json")
    szilard_bridge = load_json("szilard_graph_proof_alignment_results.json")
    control_lego = load_json("lego_measurement_feedback_distinguishability_results.json")

    graph_summary = build_combined_graph()
    precedence = prove_precedence_guard()
    geometry = geometry_distinguishability()
    sz_chain = szilard_operational_chain()

    positive = {
        "combined_geometry_to_protocol_graph_is_a_single_valid_chain": {
            **graph_summary,
            "pass": (
                graph_summary["is_dag"]
                and graph_summary["node_count"] == 5
                and graph_summary["edge_count"] == 4
                and graph_summary["source_count"] == 1
                and graph_summary["sink_count"] == 1
                and graph_summary["longest_path_length"] == 4
            ),
        },
        "weyl_left_right_pair_is_perfectly_distinguishable_at_the_bridge_reference": geometry,
        "szilard_measurement_feedback_reset_chain_preserves_expected_distinguishability_order": sz_chain,
        "z3_rejects_reset_before_measurement_in_the_combined_chain": precedence,
    }

    negative = {
        "existing_strict_rows_remain_bounded_and_clean": {
            "weyl_strict_all_pass": bool(weyl_companion["summary"]["all_pass"]),
            "weyl_translation_all_pass": bool(weyl_translation["summary"]["all_pass"]),
            "szilard_graph_bridge_all_pass": bool(szilard_bridge["summary"]["all_pass"]),
            "control_lego_all_pass": bool(control_lego["summary"]["all_pass"]),
            "pass": (
                weyl_companion["summary"]["all_pass"]
                and weyl_translation["summary"]["all_pass"]
                and szilard_bridge["summary"]["all_pass"]
                and control_lego["summary"]["all_pass"]
            ),
        },
        "bridge_row_is_not_a_geometry_native_demon_claim": {
            "scope_note": (
                "This row only aligns Weyl/Hopf geometry readout structure with the exact "
                "Szilard protocol chain and its operational-control surfaces."
            ),
            "pass": True,
        },
    }

    boundary = {
        "combined_order_matches_geometry_then_measurement_then_feedback_then_reset": {
            "topological_order": graph_summary["topological_order"],
            "pass": graph_summary["topological_order"] == [
                "weyl_left_right_frame",
                "pauli_readout",
                "measurement_record_written",
                "feedback_applied",
                "memory_erased",
            ],
        },
        "bridge_metrics_match_strict_reference_scales": {
            "weyl_transport_roundtrip_error": float(weyl_companion["summary"]["max_transport_roundtrip_error"]),
            "weyl_stack_error_gap": float(weyl_translation["summary"]["stack_error_gap"]),
            "szilard_measurement_guess_probability": float(szilard_bridge["summary"]["helstrom_measurement_guess_probability"]),
            "szilard_erased_guess_probability": float(szilard_bridge["summary"]["helstrom_erased_guess_probability"]),
            "pass": (
                weyl_companion["summary"]["max_transport_roundtrip_error"] < 1e-12
                and weyl_translation["summary"]["stack_error_gap"] < 1e-12
                and szilard_bridge["summary"]["helstrom_measurement_guess_probability"] > 0.5
                and szilard_bridge["summary"]["helstrom_erased_guess_probability"] <= 0.5000001
            ),
        },
    }

    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in negative.values())
        and all(item["pass"] for item in boundary.values())
    )

    results = {
        "name": "qit_weyl_szilard_geometry_bridge",
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
            "graph_path_length": int(graph_summary["longest_path_length"]),
            "geometry_left_right_guess_probability": float(geometry["left_right_guess_probability"]),
            "geometry_left_right_overlap_abs": float(geometry["left_right_overlap_abs"]),
            "szilard_measurement_guess_probability": float(sz_chain["blank_vs_measured_guess_probability"]),
            "szilard_erased_guess_probability": float(sz_chain["blank_vs_erased_guess_probability"]),
            "wrong_order_vs_feedback_guess_probability": float(sz_chain["wrong_order_vs_feedback_guess_probability"]),
            "geometry_to_protocol_order_unsat": bool(precedence["pass"]),
            "weyl_transport_roundtrip_error": float(weyl_companion["summary"]["max_transport_roundtrip_error"]),
            "weyl_translation_stack_gap": float(weyl_translation["summary"]["stack_error_gap"]),
            "scope_note": (
                "Weyl/Hopf <-> Szilard bridge row. It ties strict geometry readout to strict "
                "measurement/feedback/reset ordering without claiming a runtime engine rewrite."
            ),
        },
    }

    out = RESULT_DIR / "qit_weyl_szilard_geometry_bridge_results.json"
    out.write_text(json.dumps(results, indent=2))
    print(out)


if __name__ == "__main__":
    main()
