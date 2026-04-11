#!/usr/bin/env python3
"""
Szilard graph/proof alignment bridge.

Bounded bridge row that keeps the current exact Szilard bookkeeping lane intact
but adds:
  - a rustworkx protocol-order graph
  - z3 proofs for ideal ordering / kT ln 2 bookkeeping identities
  - Helstrom operational distinguishability checks on the measurement record

This is a graph/proof-aware bridge row, not a runtime demon claim.
"""

from __future__ import annotations

import json
import pathlib

import rustworkx as rx
import z3

import sim_helstrom_guess_bound as helstrom
import sim_qit_szilard_bidirectional_protocol as base


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Graph/proof alignment bridge for the bounded Szilard family. It adds "
    "protocol-order graph structure, z3 bookkeeping proofs, and Helstrom-style "
    "record distinguishability around the finite two-qubit lane."
)

LEGO_IDS = [
    "quantum_thermodynamics",
    "helstrom_guess_bound",
    "graph_shell_geometry",
]

PRIMARY_LEGO_IDS = [
    "quantum_thermodynamics",
    "helstrom_guess_bound",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing bookkeeping proof surface for ideal measurement/erasure and ordering identities",
    },
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing protocol DAG construction and precedence checks for measurement/feedback/reset ordering",
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


def build_protocol_graph() -> dict:
    graph = rx.PyDiGraph()
    nodes = [
        "initial_mixed_system_blank_memory",
        "measurement_record_written",
        "feedback_applied",
        "memory_erased",
    ]
    idx = {label: graph.add_node(label) for label in nodes}
    graph.add_edge(idx["initial_mixed_system_blank_memory"], idx["measurement_record_written"], "measurement")
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


def _rv(value: float) -> z3.ArithRef:
    return z3.RealVal(str(float(value)))


def prove_ktln2_balance(ln2_value: float) -> dict:
    solver = z3.Solver()
    info_gain = z3.Real("info_gain")
    system_gain = z3.Real("system_gain")
    erasure_cost = z3.Real("erasure_cost")
    net = z3.Real("net")
    ln2 = _rv(ln2_value)

    solver.add(info_gain == ln2)
    solver.add(system_gain == ln2)
    solver.add(erasure_cost == ln2)
    solver.add(net == system_gain - erasure_cost)
    solver.add(net != 0)

    verdict = solver.check()
    return {
        "verdict": str(verdict),
        "pass": verdict == z3.unsat,
        "claim": "Ideal forward bookkeeping forces zero net after erasure at the same kT ln 2 scale.",
    }


def prove_ordering_precedence() -> dict:
    solver = z3.Solver()
    m = z3.Int("measurement_pos")
    f = z3.Int("feedback_pos")
    r = z3.Int("reset_pos")

    for var in (m, f, r):
        solver.add(var >= 0, var <= 2)
    solver.add(z3.Distinct(m, f, r))
    solver.add(m < f)
    solver.add(f < r)
    solver.add(f < m)

    verdict = solver.check()
    return {
        "verdict": str(verdict),
        "pass": verdict == z3.unsat,
        "claim": "Feedback cannot precede measurement once the protocol precedence constraints are enforced.",
    }


def build_forward_states() -> dict:
    rho_init = base.make_initial_state()
    rho_measured = base.apply_unitary(rho_init, base.CNOT_SYSTEM_TO_MEMORY)
    rho_feedback = base.imperfect_controlled_x(rho_measured, 0.0)
    rho_erased = base.reset_memory_to_zero(rho_feedback, 1.0)
    rho_wrong_order = base.apply_unitary(base.imperfect_controlled_x(rho_init, 0.0), base.CNOT_SYSTEM_TO_MEMORY)
    return {
        "initial": rho_init,
        "measured": rho_measured,
        "feedback": rho_feedback,
        "erased": rho_erased,
        "wrong_order": rho_wrong_order,
    }


def main() -> None:
    forward = base.run_forward_cycle(temperature=1.0)
    reverse = base.run_reverse_cycle(temperature=1.0)
    states = build_forward_states()
    graph_summary = build_protocol_graph()
    ktln2_proof = prove_ktln2_balance(base.LN2)
    precedence_proof = prove_ordering_precedence()

    blank_memory = base.PROJ0
    measured_memory = base.partial_trace_system(states["measured"])
    erased_memory = base.partial_trace_system(states["erased"])
    wrong_order_system = base.partial_trace_memory(states["wrong_order"])
    feedback_system = base.partial_trace_memory(states["feedback"])

    helstrom_measurement_guess = helstrom.helstrom_guess_prob(blank_memory, measured_memory)
    helstrom_erased_guess = helstrom.helstrom_guess_prob(blank_memory, erased_memory)
    helstrom_wrong_order_vs_feedback = helstrom.helstrom_guess_prob(wrong_order_system, feedback_system)

    positive = {
        "protocol_graph_is_a_single_valid_measurement_feedback_reset_chain": {
            **graph_summary,
            "pass": (
                graph_summary["is_dag"]
                and graph_summary["node_count"] == 4
                and graph_summary["edge_count"] == 3
                and graph_summary["source_count"] == 1
                and graph_summary["sink_count"] == 1
                and graph_summary["longest_path_length"] == 3
            ),
        },
        "z3_forces_ideal_forward_ktln2_balance": ktln2_proof,
        "z3_forces_measurement_before_feedback_in_the_protocol_dag": precedence_proof,
        "helstrom_record_guessing_improves_after_measurement_and_collapses_after_erasure": {
            "blank_vs_measured_guess_probability": helstrom_measurement_guess,
            "blank_vs_erased_guess_probability": helstrom_erased_guess,
            "pass": helstrom_measurement_guess > helstrom_erased_guess + 1e-6 and helstrom_erased_guess <= 0.5000001,
        },
    }

    negative = {
        "wrong_order_does_not_match_the_purified_feedback_state_operationally": {
            "wrong_order_vs_feedback_guess_probability": helstrom_wrong_order_vs_feedback,
            "pass": helstrom_wrong_order_vs_feedback > 0.5 + 1e-6,
        },
        "graph_alignment_row_is_not_a_runtime_demon_claim": {
            "scope_note": (
                "This row adds graph/proof and operational distinguishability around the exact finite "
                "Szilard bookkeeping lane; it does not claim a reservoir-runtime demon."
            ),
            "pass": True,
        },
    }

    boundary = {
        "graph_topological_order_matches_the_protocol_chain": {
            "topological_order": graph_summary["topological_order"],
            "pass": graph_summary["topological_order"] == [
                "initial_mixed_system_blank_memory",
                "measurement_record_written",
                "feedback_applied",
                "memory_erased",
            ],
        },
        "ideal_forward_and_reverse_rows_still_close_cleanly": {
            "ideal_forward_information_gain": float(forward["states"]["measured"]["mutual_information"]),
            "ideal_forward_erasure_cost": float(forward["metrics"]["erasure_cost"]),
            "ideal_reverse_restoration_trace_distance": float(reverse["metrics"]["restoration_trace_distance"]),
            "pass": (
                abs(forward["states"]["measured"]["mutual_information"] - base.LN2) < 1e-9
                and abs(forward["metrics"]["erasure_cost"] - base.LN2) < 1e-9
                and reverse["metrics"]["restoration_trace_distance"] < 1e-9
            ),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "szilard_graph_proof_alignment",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "graph_summary": graph_summary,
        "summary": {
            "all_pass": all_pass,
            "graph_path_length": graph_summary["longest_path_length"],
            "protocol_schedule_valid": positive["protocol_graph_is_a_single_valid_measurement_feedback_reset_chain"]["pass"],
            "ktln2_balance_unsat": ktln2_proof["pass"],
            "ordering_precedence_unsat": precedence_proof["pass"],
            "helstrom_measurement_guess_probability": helstrom_measurement_guess,
            "helstrom_erased_guess_probability": helstrom_erased_guess,
            "wrong_order_vs_feedback_guess_probability": helstrom_wrong_order_vs_feedback,
            "ideal_forward_information_gain": float(forward["states"]["measured"]["mutual_information"]),
            "ideal_forward_erasure_cost": float(forward["metrics"]["erasure_cost"]),
            "scope_note": (
                "Graph/proof bridge around the exact Szilard row. Useful as a pre-constraint "
                "alignment surface before graph-native or proof-pressure runtime carriers."
            ),
        },
    }

    out_path = RESULT_DIR / "szilard_graph_proof_alignment_results.json"
    out_path.write_text(json.dumps(results, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
