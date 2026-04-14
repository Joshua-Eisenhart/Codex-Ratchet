#!/usr/bin/env python3
"""
Measurement/feedback distinguishability lego.

Reusable finite Szilard-style operational-control probe.
It keeps the protocol as a small DAG, measures state distinguishability with
Helstrom-style guessing, and checks control degradation across a bounded error
grid. The row is QIT-clean and does not claim a runtime demon theorem.
"""

from __future__ import annotations

import json
import pathlib

import numpy as np
import rustworkx as rx

import sim_helstrom_guess_bound as helstrom
import sim_qit_szilard_bidirectional_protocol as base
classification = "classical_baseline"  # auto-backfill


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Finite measurement/feedback distinguishability lego for Szilard-like "
    "protocols. It combines a protocol DAG, Helstrom-style distinguishability, "
    "and bounded control-degradation sweeps without turning the result into a "
    "reservoir-runtime claim."
)

LEGO_IDS = [
    "quantum_thermodynamics",
    "helstrom_guess_bound",
    "state_distinguishability",
    "measurement_feedback",
]

PRIMARY_LEGO_IDS = [
    "quantum_thermodynamics",
    "helstrom_guess_bound",
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
        "reason": "load-bearing protocol DAG construction and topological legality checks",
    },
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["rustworkx"] = "load_bearing"

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"

MEASUREMENT_ERROR_GRID = [0.0, 0.1, 0.2]
FEEDBACK_ERROR_GRID = [0.0, 0.1, 0.2]
RESET_STRENGTH_GRID = [0.35, 0.65, 0.95]


def build_protocol_graph() -> dict:
    graph = rx.PyDiGraph()
    nodes = [
        "initial_blank_memory",
        "measurement_record_written",
        "feedback_applied",
        "memory_erased",
        "wrong_order_branch",
    ]
    idx = {label: graph.add_node(label) for label in nodes}
    graph.add_edge(idx["initial_blank_memory"], idx["measurement_record_written"], "measurement")
    graph.add_edge(idx["measurement_record_written"], idx["feedback_applied"], "feedback")
    graph.add_edge(idx["feedback_applied"], idx["memory_erased"], "reset")
    graph.add_edge(idx["initial_blank_memory"], idx["wrong_order_branch"], "wrong_order")
    topo = [graph[node] for node in rx.topological_sort(graph)]
    longest_path = [graph[node] for node in rx.dag_longest_path(graph)]
    return {
        "node_count": int(graph.num_nodes()),
        "edge_count": int(graph.num_edges()),
        "source_count": int(sum(graph.in_degree(node) == 0 for node in graph.node_indices())),
        "sink_count": int(sum(graph.out_degree(node) == 0 for node in graph.node_indices())),
        "is_dag": bool(rx.is_directed_acyclic_graph(graph)),
        "topological_order": topo,
        "longest_path": longest_path,
        "longest_path_length": max(len(longest_path) - 1, 0),
    }


def protocol_row(
    measurement_error: float,
    feedback_error: float,
    reset_strength: float,
    temperature: float = 1.0,
) -> dict:
    rho_init = base.make_initial_state()
    rho_measured = base.memory_flip_channel(
        base.apply_unitary(rho_init, base.CNOT_SYSTEM_TO_MEMORY),
        measurement_error,
    )
    rho_feedback = base.imperfect_controlled_x(rho_measured, feedback_error)
    rho_erased = base.reset_memory_to_zero(rho_feedback, reset_strength)
    rho_wrong_order = base.memory_flip_channel(
        base.apply_unitary(
            base.imperfect_controlled_x(rho_init, feedback_error),
            base.CNOT_SYSTEM_TO_MEMORY,
        ),
        measurement_error,
    )

    blank_joint = rho_init
    measured_joint = rho_measured
    feedback_joint = rho_feedback
    wrong_order_joint = rho_wrong_order

    blank_memory = base.partial_trace_system(rho_init)
    measured_memory = base.partial_trace_system(rho_measured)
    erased_memory = base.partial_trace_system(rho_erased)

    blank_vs_measured_guess_probability = helstrom.helstrom_guess_prob(
        blank_joint, measured_joint
    )
    feedback_vs_wrong_order_guess_probability = helstrom.helstrom_guess_prob(
        feedback_joint, wrong_order_joint
    )
    blank_vs_erased_guess_probability = helstrom.helstrom_guess_prob(
        blank_memory, erased_memory
    )
    reset_collapse_trace_distance = base.trace_distance(blank_memory, erased_memory)

    snapshots = {
        "initial": base.state_snapshot(rho_init, temperature),
        "measured": base.state_snapshot(rho_measured, temperature),
        "feedback": base.state_snapshot(rho_feedback, temperature),
        "erased": base.state_snapshot(rho_erased, temperature),
        "wrong_order": base.state_snapshot(rho_wrong_order, temperature),
    }

    return {
        "measurement_error": float(measurement_error),
        "feedback_error": float(feedback_error),
        "reset_strength": float(reset_strength),
        "blank_vs_measured_guess_probability": float(blank_vs_measured_guess_probability),
        "feedback_vs_wrong_order_guess_probability": float(feedback_vs_wrong_order_guess_probability),
        "blank_vs_erased_guess_probability": float(blank_vs_erased_guess_probability),
        "reset_collapse_trace_distance": float(reset_collapse_trace_distance),
        "system_entropy_after_feedback": float(snapshots["feedback"]["system_entropy"]),
        "memory_entropy_after_erasure": float(snapshots["erased"]["memory_entropy"]),
        "final_joint_entropy": float(snapshots["erased"]["joint_entropy"]),
        "valid_density": all(s["valid_density"] for s in snapshots.values()),
    }


def monotone_nonincreasing(values: list[float]) -> bool:
    return all(a >= b - 1e-12 for a, b in zip(values, values[1:]))


def axis_profile(rows: list[dict], axis: str, filter_a: tuple[str, float], filter_b: tuple[str, float]) -> list[dict]:
    axis_values = sorted({row[axis] for row in rows})
    out = []
    for value in axis_values:
        matched = [
            row
            for row in rows
            if row[axis] == value
            and abs(row[filter_a[0]] - filter_a[1]) < 1e-12
            and abs(row[filter_b[0]] - filter_b[1]) < 1e-12
        ]
        if not matched:
            continue
        out.append(
            {
                axis: float(value),
                "mean_blank_vs_measured_guess_probability": float(
                    np.mean([row["blank_vs_measured_guess_probability"] for row in matched])
                ),
                "mean_feedback_vs_wrong_order_guess_probability": float(
                    np.mean([row["feedback_vs_wrong_order_guess_probability"] for row in matched])
                ),
                "mean_blank_vs_erased_guess_probability": float(
                    np.mean([row["blank_vs_erased_guess_probability"] for row in matched])
                ),
                "mean_reset_collapse_trace_distance": float(
                    np.mean([row["reset_collapse_trace_distance"] for row in matched])
                ),
                "n": len(matched),
            }
        )
    return out


def main() -> None:
    graph_summary = build_protocol_graph()

    rows = [
        protocol_row(m_err, f_err, r_str)
        for m_err in MEASUREMENT_ERROR_GRID
        for f_err in FEEDBACK_ERROR_GRID
        for r_str in RESET_STRENGTH_GRID
    ]

    ideal = protocol_row(0.0, 0.0, 1.0)
    degraded = protocol_row(0.2, 0.2, 0.35)

    measurement_profile = axis_profile(
        rows, "measurement_error", ("feedback_error", 0.0), ("reset_strength", 0.95)
    )
    feedback_profile = axis_profile(
        rows, "feedback_error", ("measurement_error", 0.0), ("reset_strength", 0.95)
    )
    reset_profile = axis_profile(
        rows, "reset_strength", ("measurement_error", 0.0), ("feedback_error", 0.0)
    )

    positive = {
        "protocol_graph_is_a_valid_branching_dag": {
            **graph_summary,
            "pass": (
                graph_summary["is_dag"]
                and graph_summary["node_count"] == 5
                and graph_summary["edge_count"] == 4
                and graph_summary["source_count"] == 1
                and graph_summary["sink_count"] == 2
                and graph_summary["longest_path_length"] == 3
            ),
        },
        "ideal_blank_vs_measured_record_is_operationally_distinguishable": {
            "blank_vs_measured_guess_probability": ideal["blank_vs_measured_guess_probability"],
            "pass": abs(ideal["blank_vs_measured_guess_probability"] - 0.75) < 1e-9,
        },
        "ideal_feedback_state_is_more_distinguishable_from_wrong_order_than_blank_reset_is": {
            "feedback_vs_wrong_order_guess_probability": ideal[
                "feedback_vs_wrong_order_guess_probability"
            ],
            "blank_vs_erased_guess_probability": ideal["blank_vs_erased_guess_probability"],
            "pass": (
                ideal["feedback_vs_wrong_order_guess_probability"] > ideal["blank_vs_erased_guess_probability"] + 1e-9
                and abs(ideal["blank_vs_erased_guess_probability"] - 0.5) < 1e-9
            ),
        },
        "degraded_control_is_weaker_than_ideal_control": {
            "ideal_feedback_vs_wrong_order": ideal["feedback_vs_wrong_order_guess_probability"],
            "degraded_feedback_vs_wrong_order": degraded["feedback_vs_wrong_order_guess_probability"],
            "ideal_reset_collapse_trace_distance": ideal["reset_collapse_trace_distance"],
            "degraded_reset_collapse_trace_distance": degraded["reset_collapse_trace_distance"],
            "pass": (
                degraded["feedback_vs_wrong_order_guess_probability"]
                < ideal["feedback_vs_wrong_order_guess_probability"] - 1e-6
                and degraded["reset_collapse_trace_distance"]
                > ideal["reset_collapse_trace_distance"] + 1e-6
            ),
        },
    }

    negative = {
        "reset_collapse_has_near_zero_distinguishability_at_ideal_strength": {
            "reset_collapse_trace_distance": ideal["reset_collapse_trace_distance"],
            "pass": ideal["reset_collapse_trace_distance"] < 1e-9,
        },
        "wrong_order_is_not_as_good_as_post_feedback_state": {
            "pass": ideal["feedback_vs_wrong_order_guess_probability"] > 0.5 + 1e-9,
        },
    }

    boundary = {
        "measurement_error_axis_degrades_monotonically": {
            "profile": measurement_profile,
            "pass": monotone_nonincreasing(
                [row["mean_blank_vs_measured_guess_probability"] for row in measurement_profile]
            ),
        },
        "feedback_error_axis_degrades_monotonically": {
            "profile": feedback_profile,
            "pass": monotone_nonincreasing(
                [row["mean_feedback_vs_wrong_order_guess_probability"] for row in feedback_profile]
            ),
        },
        "reset_strength_axis_collapses_monotonically": {
            "profile": reset_profile,
            "pass": monotone_nonincreasing(
                [row["mean_reset_collapse_trace_distance"] for row in reset_profile]
            ),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
        and all(row["valid_density"] for row in rows)
    )

    results = {
        "name": "lego_measurement_feedback_distinguishability",
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
        "rows": rows,
        "summary": {
            "all_pass": all_pass,
            "row_count": len(rows),
            "ideal_blank_vs_measured_guess_probability": ideal["blank_vs_measured_guess_probability"],
            "ideal_feedback_vs_wrong_order_guess_probability": ideal[
                "feedback_vs_wrong_order_guess_probability"
            ],
            "ideal_blank_vs_erased_guess_probability": ideal["blank_vs_erased_guess_probability"],
            "ideal_reset_collapse_trace_distance": ideal["reset_collapse_trace_distance"],
            "best_blank_vs_measured_guess_probability": float(
                max(row["blank_vs_measured_guess_probability"] for row in rows)
            ),
            "worst_blank_vs_measured_guess_probability": float(
                min(row["blank_vs_measured_guess_probability"] for row in rows)
            ),
            "best_feedback_vs_wrong_order_guess_probability": float(
                max(row["feedback_vs_wrong_order_guess_probability"] for row in rows)
            ),
            "worst_feedback_vs_wrong_order_guess_probability": float(
                min(row["feedback_vs_wrong_order_guess_probability"] for row in rows)
            ),
            "best_reset_collapse_trace_distance": float(
                min(row["reset_collapse_trace_distance"] for row in rows)
            ),
            "worst_reset_collapse_trace_distance": float(
                max(row["reset_collapse_trace_distance"] for row in rows)
            ),
            "scope_note": (
                "Finite measurement/feedback distinguishability lego for Szilard-like control. "
                "It is a reusable operational-control row, not a reservoir-runtime theorem."
            ),
        },
    }

    out_path = RESULT_DIR / "lego_measurement_feedback_distinguishability_results.json"
    out_path.write_text(json.dumps(results, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
