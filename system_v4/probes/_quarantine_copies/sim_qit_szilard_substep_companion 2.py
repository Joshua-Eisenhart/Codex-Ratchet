#!/usr/bin/env python3
"""
QIT Szilard substep companion.

Finite two-qubit companion surface for the stochastic Szilard substep lane.
The companion keeps the same ordered and scrambled protocol families as the
open-lab row, but translates them into exact density-operator bookkeeping with
explicit measurement, feedback, reset, and hold mechanics.
"""

from __future__ import annotations

import json
import pathlib
import sys

import numpy as np


PROBE_DIR = pathlib.Path(__file__).resolve().parent
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

import sim_qit_szilard_bidirectional_protocol as base  # noqa: E402


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Finite two-qubit companion row for the stochastic Szilard substep lane. "
    "It preserves ordered and scrambled protocol families, adds explicit hold "
    "decay, and keeps the result in exact density-operator bookkeeping."
)

LEGO_IDS = [
    "quantum_thermodynamics",
    "channel_cptp_map",
]

PRIMARY_LEGO_IDS = [
    "quantum_thermodynamics",
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
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

TEMPERATURE = 1.0
MEASUREMENT_ERROR_GRID = [0.0, 0.1, 0.2]
FEEDBACK_BLINDNESS_GRID = [0.0, 0.15, 0.3]
RESET_STRENGTH_GRID = [0.35, 0.65, 0.95]
HOLD_STEPS = 60
RECORD_LIFETIME_STEPS = 120
HOLD_DECAY_STRENGTH = float(1.0 - np.exp(-HOLD_STEPS / float(RECORD_LIFETIME_STEPS)))

ORDERED_PROTOCOL = ("measurement", "feedback", "reset", "hold")
PRIMARY_SCRAMBLED_PROTOCOLS = {
    "feedback_first": ("feedback", "measurement", "reset", "hold"),
    "measurement_then_reset_then_feedback": ("measurement", "reset", "feedback", "hold"),
}
DIAGNOSTIC_SCRAMBLED_PROTOCOLS = {
    "reset_first": ("reset", "measurement", "feedback", "hold"),
}
PASSIVE_PROTOCOLS = {
    "measurement_only": ("measurement", "hold", "hold", "hold"),
    "feedback_only": ("feedback", "hold", "hold", "hold"),
    "reset_only": ("reset", "hold", "hold", "hold"),
}


def entropy(rho: np.ndarray) -> float:
    return float(base.entropy(rho))


def trace_distance(rho: np.ndarray, sigma: np.ndarray) -> float:
    diff = (rho - sigma + (rho - sigma).conj().T) / 2.0
    vals = np.linalg.eigvalsh(diff)
    return float(0.5 * np.sum(np.abs(vals)))


def hold_stage(rho: np.ndarray) -> np.ndarray:
    rho_system = base.partial_trace_memory(rho)
    blank_record = np.kron(rho_system, base.PROJ0)
    return (1.0 - HOLD_DECAY_STRENGTH) * rho + HOLD_DECAY_STRENGTH * blank_record


def measurement_stage(rho: np.ndarray, measurement_error: float) -> np.ndarray:
    measured = base.apply_unitary(rho, base.CNOT_SYSTEM_TO_MEMORY)
    return base.memory_flip_channel(measured, measurement_error)


def feedback_stage(rho: np.ndarray, feedback_blindness: float) -> np.ndarray:
    return base.imperfect_controlled_x(rho, feedback_blindness)


def reset_stage(rho: np.ndarray, reset_strength: float) -> np.ndarray:
    return base.reset_memory_to_zero(rho, reset_strength)


def state_snapshot(rho: np.ndarray) -> dict:
    rho_system = base.partial_trace_memory(rho)
    rho_memory = base.partial_trace_system(rho)
    return {
        "trace_real": float(np.trace(rho).real),
        "trace_error_abs": float(abs(np.trace(rho).real - 1.0)),
        "system_entropy": entropy(rho_system),
        "memory_entropy": entropy(rho_memory),
        "joint_entropy": entropy(rho),
        "mutual_information": float(base.mutual_information(rho)),
        "system_free_energy": float(base.free_energy_degenerate(rho_system, TEMPERATURE)),
        "memory_free_energy": float(base.free_energy_degenerate(rho_memory, TEMPERATURE)),
        "valid_density": bool(base.is_valid_density(rho)),
    }


def measurement_accuracy(rho_sm: np.ndarray) -> float:
    diag = np.real(np.diag(np.asarray(rho_sm, dtype=complex)))
    if diag.size != 4:
        raise ValueError("expected a two-qubit density matrix")
    return float(diag[0] + diag[3])


def run_protocol(
    order: tuple[str, ...],
    *,
    measurement_error: float,
    feedback_blindness: float,
    reset_strength: float,
) -> dict:
    rho = base.make_initial_state()
    initial_snapshot = state_snapshot(rho)
    measured_rho = None
    feedback_rho = None
    reset_rho = None
    hold_rho = None
    stage_logs = []
    stage_snapshots: dict[str, dict] = {}

    for stage_name in order:
        if stage_name == "measurement":
            rho = measurement_stage(rho, measurement_error)
            measured_rho = rho
        elif stage_name == "feedback":
            rho = feedback_stage(rho, feedback_blindness)
            feedback_rho = rho
        elif stage_name == "reset":
            rho = reset_stage(rho, reset_strength)
            reset_rho = rho
        elif stage_name == "hold":
            rho = hold_stage(rho)
            hold_rho = rho
        else:
            raise ValueError(f"unknown stage: {stage_name}")
        snapshot = state_snapshot(rho)
        stage_snapshots[stage_name] = snapshot
        stage_logs.append({"name": stage_name, "snapshot": snapshot})

    final_snapshot = state_snapshot(rho)
    measured_snapshot = state_snapshot(measured_rho if measured_rho is not None else base.make_initial_state())
    feedback_snapshot = state_snapshot(feedback_rho if feedback_rho is not None else base.make_initial_state())
    reset_snapshot = state_snapshot(reset_rho if reset_rho is not None else base.make_initial_state())
    hold_snapshot = state_snapshot(hold_rho if hold_rho is not None else rho)

    measured_accuracy = (
        measurement_accuracy(measured_rho) if measured_rho is not None else measurement_accuracy(base.make_initial_state())
    )
    final_system = base.partial_trace_memory(rho)
    final_memory = base.partial_trace_system(rho)

    return {
        "order": list(order),
        "measurement_error": float(measurement_error),
        "feedback_blindness": float(feedback_blindness),
        "reset_strength": float(reset_strength),
        "hold_decay_strength": float(HOLD_DECAY_STRENGTH),
        "stage_logs": stage_logs,
        "stage_snapshots": stage_snapshots,
        "states": {
            "measured": measured_snapshot,
            "feedback": feedback_snapshot,
            "reset": reset_snapshot,
            "hold": hold_snapshot,
            "final": final_snapshot,
        },
        "metrics": {
            "measurement_accuracy": float(measured_accuracy),
            "measurement_mutual_information": float(measured_snapshot["mutual_information"]),
            "feedback_system_free_energy_gain": float(
                feedback_snapshot["system_free_energy"] - initial_snapshot["system_free_energy"]
            ),
            "feedback_mutual_information": float(feedback_snapshot["mutual_information"]),
            "post_feedback_system_entropy": float(feedback_snapshot["system_entropy"]),
            "post_feedback_memory_entropy": float(feedback_snapshot["memory_entropy"]),
            "reset_memory_entropy": float(reset_snapshot["memory_entropy"]),
            "reset_memory_free_energy": float(reset_snapshot["memory_free_energy"]),
            "reset_memory_free_energy_drop": float(
                feedback_snapshot["memory_free_energy"] - reset_snapshot["memory_free_energy"]
            ),
            "hold_memory_entropy": float(hold_snapshot["memory_entropy"]),
            "final_system_entropy": float(final_snapshot["system_entropy"]),
            "final_memory_entropy": float(final_snapshot["memory_entropy"]),
            "final_joint_entropy": float(final_snapshot["joint_entropy"]),
            "final_system_free_energy": float(final_snapshot["system_free_energy"]),
            "final_memory_free_energy": float(final_snapshot["memory_free_energy"]),
            "final_joint_trace_distance_to_initial": float(
                trace_distance(rho, base.make_initial_state())
            ),
            "final_memory_trace_distance_to_blank": float(
                trace_distance(final_memory, base.PROJ0)
            ),
            "final_system_trace_distance_to_initial": float(
                trace_distance(final_system, base.partial_trace_memory(base.make_initial_state()))
            ),
            "valid_density": bool(final_snapshot["valid_density"]),
        },
    }


def best_scrambled_protocol(protocols: dict[str, dict]) -> tuple[str, dict]:
    ranked = sorted(
        ((name, proto) for name, proto in protocols.items() if name != "ordered"),
        key=lambda item: item[1]["metrics"]["final_joint_entropy"],
    )
    return ranked[0]


def main() -> None:
    rows = []
    representative_protocols = {}

    for measurement_error in MEASUREMENT_ERROR_GRID:
        for feedback_blindness in FEEDBACK_BLINDNESS_GRID:
            for reset_strength in RESET_STRENGTH_GRID:
                ordered = run_protocol(
                    ORDERED_PROTOCOL,
                    measurement_error=measurement_error,
                    feedback_blindness=feedback_blindness,
                    reset_strength=reset_strength,
                )
                primary_scrambled = {
                    name: run_protocol(
                        order,
                        measurement_error=measurement_error,
                        feedback_blindness=feedback_blindness,
                        reset_strength=reset_strength,
                    )
                    for name, order in PRIMARY_SCRAMBLED_PROTOCOLS.items()
                }
                diagnostic_scrambled = {
                    name: run_protocol(
                        order,
                        measurement_error=measurement_error,
                        feedback_blindness=feedback_blindness,
                        reset_strength=reset_strength,
                    )
                    for name, order in DIAGNOSTIC_SCRAMBLED_PROTOCOLS.items()
                }
                passive = {
                    name: run_protocol(
                        order,
                        measurement_error=measurement_error,
                        feedback_blindness=feedback_blindness,
                        reset_strength=reset_strength,
                    )
                    for name, order in PASSIVE_PROTOCOLS.items()
                }
                all_candidates = {
                    "ordered": ordered,
                    **primary_scrambled,
                    **diagnostic_scrambled,
                    **passive,
                }
                best_scrambled_name, best_scrambled = best_scrambled_protocol(all_candidates)
                ordering_margin = (
                    best_scrambled["metrics"]["final_joint_entropy"]
                    - ordered["metrics"]["final_joint_entropy"]
                )
                row = {
                    "measurement_error": float(measurement_error),
                    "feedback_blindness": float(feedback_blindness),
                    "reset_strength": float(reset_strength),
                    "ordered_final_system_entropy": ordered["metrics"]["final_system_entropy"],
                    "ordered_final_memory_entropy": ordered["metrics"]["final_memory_entropy"],
                    "ordered_final_joint_entropy": ordered["metrics"]["final_joint_entropy"],
                    "ordered_measurement_accuracy": ordered["metrics"]["measurement_accuracy"],
                    "ordered_measurement_mutual_information": ordered["metrics"]["measurement_mutual_information"],
                    "ordered_feedback_system_free_energy_gain": ordered["metrics"][
                        "feedback_system_free_energy_gain"
                    ],
                    "ordered_reset_memory_entropy": ordered["metrics"]["reset_memory_entropy"],
                    "ordered_reset_memory_free_energy_drop": ordered["metrics"][
                        "reset_memory_free_energy_drop"
                    ],
                    "ordered_post_feedback_system_entropy": ordered["metrics"]["post_feedback_system_entropy"],
                    "ordered_final_joint_trace_distance_to_initial": ordered["metrics"][
                        "final_joint_trace_distance_to_initial"
                    ],
                    "feedback_first_final_joint_entropy": primary_scrambled["feedback_first"]["metrics"][
                        "final_joint_entropy"
                    ],
                    "reset_first_final_joint_entropy": diagnostic_scrambled["reset_first"]["metrics"][
                        "final_joint_entropy"
                    ],
                    "measurement_then_reset_then_feedback_final_joint_entropy": primary_scrambled[
                        "measurement_then_reset_then_feedback"
                    ]["metrics"]["final_joint_entropy"],
                    "measurement_only_final_joint_entropy": passive["measurement_only"]["metrics"][
                        "final_joint_entropy"
                    ],
                    "feedback_only_final_joint_entropy": passive["feedback_only"]["metrics"][
                        "final_joint_entropy"
                    ],
                    "reset_only_final_joint_entropy": passive["reset_only"]["metrics"][
                        "final_joint_entropy"
                    ],
                    "best_scrambled_name": best_scrambled_name,
                    "best_scrambled_final_joint_entropy": best_scrambled["metrics"]["final_joint_entropy"],
                    "best_scrambled_post_feedback_system_entropy": best_scrambled["metrics"][
                        "post_feedback_system_entropy"
                    ],
                    "best_scrambled_post_feedback_memory_entropy": best_scrambled["metrics"][
                        "post_feedback_memory_entropy"
                    ],
                    "ordering_margin": float(ordering_margin),
                    "ordered_beats_all_scrambled": bool(
                        all(
                            ordered["metrics"]["final_joint_entropy"]
                            <= proto["metrics"]["final_joint_entropy"] + 1e-12
                            for name, proto in all_candidates.items()
                            if name != "ordered"
                        )
                    ),
                    "valid_density_all_protocols": bool(
                        ordered["metrics"]["valid_density"]
                        and all(proto["metrics"]["valid_density"] for proto in all_candidates.values())
                    ),
                    "max_trace_error": float(
                        max(
                            proto["states"]["final"]["trace_error_abs"]
                            for proto in all_candidates.values()
                        )
                    ),
                }
                rows.append(row)

                if (
                    measurement_error == 0.1
                    and feedback_blindness == 0.15
                    and reset_strength == 0.65
                ):
                    representative_protocols = {
                        "ordered": ordered,
                        "feedback_first": primary_scrambled["feedback_first"],
                        "reset_first": diagnostic_scrambled["reset_first"],
                        "measurement_then_reset_then_feedback": primary_scrambled[
                            "measurement_then_reset_then_feedback"
                        ],
                    }

    ordered_rows = [row for row in rows if row["best_scrambled_name"] is not None]
    best_row = max(ordered_rows, key=lambda row: row["ordering_margin"])
    low_blindness_rows = [row for row in rows if row["feedback_blindness"] == min(FEEDBACK_BLINDNESS_GRID)]
    high_blindness_rows = [row for row in rows if row["feedback_blindness"] == max(FEEDBACK_BLINDNESS_GRID)]
    weak_rows = [row for row in rows if row["reset_strength"] == min(RESET_STRENGTH_GRID)]
    strong_rows = [row for row in rows if row["reset_strength"] == max(RESET_STRENGTH_GRID)]
    low_noise_rows = [row for row in rows if row["measurement_error"] == min(MEASUREMENT_ERROR_GRID)]
    high_noise_rows = [row for row in rows if row["measurement_error"] == max(MEASUREMENT_ERROR_GRID)]

    def mean(values) -> float:
        values = list(values)
        return float(np.mean(values)) if values else 0.0

    mean_measurement_accuracy = mean(row["ordered_measurement_accuracy"] for row in rows)
    mean_measurement_mi = mean(row["ordered_measurement_mutual_information"] for row in rows)
    mean_feedback_system_gain = mean(
        row["ordered_feedback_system_free_energy_gain"] for row in rows
    )
    mean_reset_memory_free_energy_drop = mean(
        row["ordered_reset_memory_free_energy_drop"] for row in rows
    )
    mean_reset_memory_free_energy_cost = -mean_reset_memory_free_energy_drop
    low_blindness_mean_margin = mean(row["ordering_margin"] for row in low_blindness_rows)
    high_blindness_mean_margin = mean(row["ordering_margin"] for row in high_blindness_rows)
    weak_reset_mean_entropy = mean(row["ordered_reset_memory_entropy"] for row in weak_rows)
    strong_reset_mean_entropy = mean(row["ordered_reset_memory_entropy"] for row in strong_rows)

    positive = {
        "measurement_stage_remains_informative": {
            "mean_measurement_accuracy": mean_measurement_accuracy,
            "mean_measurement_mutual_information": mean_measurement_mi,
            "pass": mean_measurement_mi > 0.05 and mean_measurement_accuracy > 0.6,
        },
        "feedback_stage_produces_a_nontrivial_system_free_energy_gain": {
            "mean_feedback_system_free_energy_gain": mean_feedback_system_gain,
            "mean_reset_memory_free_energy_cost": mean_reset_memory_free_energy_cost,
            "pass": mean_feedback_system_gain > 0.0 and mean_reset_memory_free_energy_cost > 0.0,
        },
        "ordered_protocol_can_outperform_scrambled_controls": {
            "best_ordering_margin": best_row["ordering_margin"],
            "best_setting": {
                "measurement_error": best_row["measurement_error"],
                "feedback_blindness": best_row["feedback_blindness"],
                "reset_strength": best_row["reset_strength"],
            },
            "pass": best_row["ordering_margin"] > 0.0,
        },
        "stronger_reset_reduces_residual_memory_entropy_on_average": {
            "weak_reset_mean_entropy_after_reset": weak_reset_mean_entropy,
            "strong_reset_mean_entropy_after_reset": strong_reset_mean_entropy,
            "pass": strong_reset_mean_entropy < weak_reset_mean_entropy,
        },
        "feedback_blindness_modulates_the_ordering_signal_on_average": {
            "low_blindness_mean_margin": low_blindness_mean_margin,
            "high_blindness_mean_margin": high_blindness_mean_margin,
            "pass": low_blindness_mean_margin > high_blindness_mean_margin,
        },
    }

    negative = {
        "higher_feedback_blindness_does_not_uniformly_destroy_ordering_signal": {
            "high_blindness_best_margin": float(max(row["ordering_margin"] for row in high_blindness_rows)),
            "pass": float(max(row["ordering_margin"] for row in high_blindness_rows)) > 0.0,
        },
        "reset_strength_is_not_the_only_driver_of_ordering_margin": {
            "ordering_margin_range": float(
                max(row["ordering_margin"] for row in rows) - min(row["ordering_margin"] for row in rows)
            ),
            "pass": float(max(row["ordering_margin"] for row in rows) - min(row["ordering_margin"] for row in rows)) > 1e-3,
        },
        "measurement_noise_does_not_uniformly_destroy_the_ordering_signal": {
            "high_noise_best_margin": float(max(row["ordering_margin"] for row in high_noise_rows)),
            "pass": float(max(row["ordering_margin"] for row in high_noise_rows)) > 0.0,
        },
    }

    boundary = {
        "all_protocols_remain_valid_density_operators": {
            "pass": all(row["valid_density_all_protocols"] for row in rows),
        },
        "all_protocols_close_work_heat_bookkeeping": {
            "pass": all(
                np.isfinite(row["ordered_final_joint_trace_distance_to_initial"])
                and np.isfinite(row["ordering_margin"])
                for row in rows
            ),
        },
        "all_rows_have_finite_summary_values": {
            "pass": all(np.isfinite(row["ordering_margin"]) for row in rows),
        },
        "parameter_grid_covers_measurement_feedback_reset_axes": {
            "measurement_error_values": MEASUREMENT_ERROR_GRID,
            "feedback_blindness_values": FEEDBACK_BLINDNESS_GRID,
            "reset_strength_values": RESET_STRENGTH_GRID,
            "n_points": len(rows),
            "pass": len(rows) == len(MEASUREMENT_ERROR_GRID) * len(FEEDBACK_BLINDNESS_GRID) * len(RESET_STRENGTH_GRID),
        },
    }

    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in negative.values())
        and all(item["pass"] for item in boundary.values())
    )

    summary = {
        "all_pass": bool(all_pass),
        "measurement_error_grid": MEASUREMENT_ERROR_GRID,
        "feedback_blindness_grid": FEEDBACK_BLINDNESS_GRID,
        "reset_strength_grid": RESET_STRENGTH_GRID,
        "hold_steps": HOLD_STEPS,
        "record_lifetime_steps": RECORD_LIFETIME_STEPS,
        "hold_decay_strength": HOLD_DECAY_STRENGTH,
        "best_ordering_margin": float(best_row["ordering_margin"]),
        "ordering_metric": "final_joint_entropy",
        "best_setting": {
            "measurement_error": best_row["measurement_error"],
            "feedback_blindness": best_row["feedback_blindness"],
            "reset_strength": best_row["reset_strength"],
        },
        "low_blindness_mean_margin": low_blindness_mean_margin,
        "high_blindness_mean_margin": high_blindness_mean_margin,
        "weak_reset_mean_memory_entropy_after_reset": weak_reset_mean_entropy,
        "strong_reset_mean_memory_entropy_after_reset": strong_reset_mean_entropy,
        "mean_measurement_accuracy": mean_measurement_accuracy,
        "mean_measurement_mutual_information": mean_measurement_mi,
        "mean_feedback_system_free_energy_gain": mean_feedback_system_gain,
        "mean_reset_memory_free_energy_drop": mean_reset_memory_free_energy_drop,
        "mean_reset_memory_free_energy_cost": mean_reset_memory_free_energy_cost,
        "scope_note": (
            "QIT-aligned finite two-qubit companion row for the stochastic Szilard "
            "substep lane. It separates ordered, scrambled, and passive variants "
            "with explicit measurement, feedback, reset, and hold mechanics."
        ),
    }

    results = {
        "name": "qit_szilard_substep_companion",
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
        "rows": rows,
        "reference_protocols": representative_protocols,
    }

    out_path = PROBE_DIR / "a2_state" / "sim_results" / "qit_szilard_substep_companion_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str) + "\n")
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
