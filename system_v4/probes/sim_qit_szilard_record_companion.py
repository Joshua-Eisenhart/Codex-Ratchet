#!/usr/bin/env python3
"""
QIT Szilard Record Companion
============================
Finite two-qubit companion row for the stochastic Szilard record/reset lane.

This keeps the same basic carrier pattern as the bidirectional Szilard probe,
but adds a record-lifetime axis and a reset-strength axis so the controller can
compare ordered versus scrambled protocols under explicit record decay.
"""

from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
classification = "classical_baseline"  # auto-backfill


PROBE_DIR = pathlib.Path(__file__).resolve().parent
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

import sim_qit_szilard_bidirectional_protocol as base  # noqa: E402


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Finite two-qubit companion row for Szilard record lifetime, record decay, "
    "and reset-strength mechanics. It stays in exact density-operator bookkeeping "
    "and is meant for QIT-aligned comparison, not canonical admission."
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
RECORD_WAIT_STEPS = 120
MEASUREMENT_ERROR_GRID = [0.0, 0.1, 0.2]
RECORD_LIFETIME_GRID = [60, 120, 240, 480]
RESET_STRENGTH_GRID = [0.35, 0.65, 0.95]
ROW_SEED = 20260410
ORDERED_PROTOCOL = ("measurement", "record_decay", "feedback", "reset")
PRIMARY_SCRAMBLED_PROTOCOLS = {
    "feedback_first": ("feedback", "measurement", "record_decay", "reset"),
    "measurement_then_reset_then_feedback": ("measurement", "reset", "feedback", "record_decay"),
}
DIAGNOSTIC_SCRAMBLED_PROTOCOLS = {
    "reset_first": ("reset", "measurement", "record_decay", "feedback"),
}


def entropy(rho: np.ndarray) -> float:
    return float(base.entropy(rho))


def state_snapshot(rho_sm: np.ndarray) -> dict:
    trace_real = float(np.trace(rho_sm).real)
    return {
        "trace_real": trace_real,
        "trace_error_abs": float(abs(trace_real - 1.0)),
        "system_entropy": entropy(base.partial_trace_memory(rho_sm)),
        "memory_entropy": entropy(base.partial_trace_system(rho_sm)),
        "joint_entropy": entropy(rho_sm),
        "mutual_information": float(base.mutual_information(rho_sm)),
        "system_free_energy": float(base.free_energy_degenerate(base.partial_trace_memory(rho_sm), TEMPERATURE)),
        "memory_free_energy": float(base.free_energy_degenerate(base.partial_trace_system(rho_sm), TEMPERATURE)),
        "valid_density": bool(base.is_valid_density(rho_sm)),
    }


def measurement_accuracy(rho_sm: np.ndarray) -> float:
    diag = np.real(np.diag(np.asarray(rho_sm, dtype=complex)))
    if diag.size != 4:
        raise ValueError("expected a two-qubit density matrix")
    return float(diag[0] + diag[3])


def record_decay_strength(record_lifetime_steps: int) -> float:
    return float(1.0 - np.exp(-RECORD_WAIT_STEPS / float(record_lifetime_steps)))


def decay_record_to_blank(rho_sm: np.ndarray, decay_strength: float) -> np.ndarray:
    rho_system = base.partial_trace_memory(rho_sm)
    blank_record = np.kron(rho_system, base.PROJ0)
    return (1.0 - decay_strength) * rho_sm + decay_strength * blank_record


def measurement_stage(rho: np.ndarray, measurement_error: float) -> np.ndarray:
    measured = base.apply_unitary(rho, base.CNOT_SYSTEM_TO_MEMORY)
    return base.memory_flip_channel(measured, measurement_error)


def feedback_stage(rho: np.ndarray) -> np.ndarray:
    return base.imperfect_controlled_x(rho, 0.0)


def reset_stage(rho: np.ndarray, reset_strength: float) -> np.ndarray:
    return base.reset_memory_to_zero(rho, reset_strength)


def run_protocol(
    order: tuple[str, ...],
    measurement_error: float,
    record_lifetime_steps: int,
    reset_strength: float,
) -> dict:
    rho = base.make_initial_state()
    measured_rho = None
    decayed_rho = None
    reset_rho = None
    stage_logs = []
    stage_snapshots: dict[str, dict] = {}
    decay_strength = record_decay_strength(record_lifetime_steps)
    record_quality = 0.0

    for stage_name in order:
        if stage_name == "measurement":
            rho = measurement_stage(rho, measurement_error)
            measured_rho = rho
            record_quality = max(record_quality, 1.0 - float(measurement_error))
        elif stage_name == "record_decay":
            rho = decay_record_to_blank(rho, decay_strength)
            decayed_rho = rho
            record_quality *= 1.0 - decay_strength
        elif stage_name == "feedback":
            rho = base.imperfect_controlled_x(rho, 1.0 - record_quality)
        elif stage_name == "reset":
            rho = reset_stage(rho, reset_strength)
            reset_rho = rho
            record_quality = 0.0
        else:
            raise ValueError(f"unknown stage: {stage_name}")
        stage_snapshots[stage_name] = state_snapshot(rho)
        stage_logs.append(
            {
                "name": stage_name,
                "snapshot": state_snapshot(rho),
            }
        )

    final_snapshot = state_snapshot(rho)
    measured_snapshot = state_snapshot(measured_rho if measured_rho is not None else base.make_initial_state())
    decayed_snapshot = state_snapshot(decayed_rho if decayed_rho is not None else base.make_initial_state())
    reset_snapshot = state_snapshot(reset_rho if reset_rho is not None else rho)

    measured_accuracy = measurement_accuracy(measured_rho) if measured_rho is not None else measurement_accuracy(base.make_initial_state())
    decayed_accuracy = measurement_accuracy(decayed_rho) if decayed_rho is not None else measured_accuracy
    record_survival_fraction = float(decayed_accuracy / measured_accuracy) if measured_accuracy > 1e-12 else 0.0

    return {
        "order": list(order),
        "measurement_error": float(measurement_error),
        "record_lifetime_steps": int(record_lifetime_steps),
        "record_decay_strength": float(decay_strength),
        "reset_strength": float(reset_strength),
        "stage_logs": stage_logs,
        "stage_snapshots": stage_snapshots,
        "states": {
            "measured": measured_snapshot,
            "decayed": decayed_snapshot,
            "reset": reset_snapshot,
            "final": final_snapshot,
        },
        "metrics": {
            "measurement_accuracy": float(measured_accuracy),
            "measurement_mutual_information": float(measured_snapshot["mutual_information"]),
            "record_accuracy_after_decay": float(decayed_accuracy),
            "record_survival_fraction": float(record_survival_fraction),
            "record_quality_after_sequence": float(record_quality),
            "post_feedback_system_entropy": float(stage_snapshots.get("feedback", final_snapshot)["system_entropy"]),
            "post_feedback_memory_entropy": float(stage_snapshots.get("feedback", final_snapshot)["memory_entropy"]),
            "final_system_entropy": float(final_snapshot["system_entropy"]),
            "final_memory_entropy": float(final_snapshot["memory_entropy"]),
            "final_joint_entropy": float(final_snapshot["joint_entropy"]),
            "final_system_free_energy": float(final_snapshot["system_free_energy"]),
            "final_memory_free_energy": float(final_snapshot["memory_free_energy"]),
            "reset_memory_entropy": float(reset_snapshot["memory_entropy"]),
            "reset_memory_free_energy": float(reset_snapshot["memory_free_energy"]),
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
        for record_lifetime_steps in RECORD_LIFETIME_GRID:
            for reset_strength in RESET_STRENGTH_GRID:
                ordered = run_protocol(
                    ORDERED_PROTOCOL,
                    measurement_error=measurement_error,
                    record_lifetime_steps=record_lifetime_steps,
                    reset_strength=reset_strength,
                )
                primary_scrambled = {
                    name: run_protocol(
                        order,
                        measurement_error=measurement_error,
                        record_lifetime_steps=record_lifetime_steps,
                        reset_strength=reset_strength,
                    )
                    for name, order in PRIMARY_SCRAMBLED_PROTOCOLS.items()
                }
                diagnostic_scrambled = {
                    name: run_protocol(
                        order,
                        measurement_error=measurement_error,
                        record_lifetime_steps=record_lifetime_steps,
                        reset_strength=reset_strength,
                    )
                    for name, order in DIAGNOSTIC_SCRAMBLED_PROTOCOLS.items()
                }
                best_scrambled_name, best_scrambled = best_scrambled_protocol(
                    {"ordered": ordered, **primary_scrambled}
                )
                ordering_margin = (
                    best_scrambled["metrics"]["final_joint_entropy"]
                    - ordered["metrics"]["final_joint_entropy"]
                )
                row = {
                    "measurement_error": float(measurement_error),
                    "record_lifetime_steps": int(record_lifetime_steps),
                    "reset_strength": float(reset_strength),
                    "ordered_final_system_entropy": ordered["metrics"]["final_system_entropy"],
                    "ordered_final_memory_entropy": ordered["metrics"]["final_memory_entropy"],
                    "ordered_final_joint_entropy": ordered["metrics"]["final_joint_entropy"],
                    "ordered_measurement_accuracy": ordered["metrics"]["measurement_accuracy"],
                    "ordered_measurement_mutual_information": ordered["metrics"]["measurement_mutual_information"],
                    "ordered_record_accuracy_after_decay": ordered["metrics"]["record_accuracy_after_decay"],
                    "ordered_record_survival_fraction": ordered["metrics"]["record_survival_fraction"],
                    "ordered_reset_memory_entropy": ordered["metrics"]["reset_memory_entropy"],
                    "ordered_post_feedback_system_entropy": ordered["metrics"]["post_feedback_system_entropy"],
                    "feedback_first_final_joint_entropy": primary_scrambled["feedback_first"]["metrics"]["final_joint_entropy"],
                    "reset_first_final_joint_entropy": diagnostic_scrambled["reset_first"]["metrics"]["final_joint_entropy"],
                    "measurement_then_reset_then_feedback_final_joint_entropy": primary_scrambled[
                        "measurement_then_reset_then_feedback"
                    ]["metrics"]["final_joint_entropy"],
                    "feedback_first_post_feedback_system_entropy": primary_scrambled["feedback_first"]["metrics"]["post_feedback_system_entropy"],
                    "reset_first_post_feedback_system_entropy": diagnostic_scrambled["reset_first"]["metrics"]["post_feedback_system_entropy"],
                    "measurement_then_reset_then_feedback_post_feedback_system_entropy": primary_scrambled[
                        "measurement_then_reset_then_feedback"
                    ]["metrics"]["post_feedback_system_entropy"],
                    "best_scrambled_name": best_scrambled_name,
                    "best_scrambled_final_joint_entropy": best_scrambled["metrics"]["final_joint_entropy"],
                    "best_scrambled_post_feedback_system_entropy": best_scrambled["metrics"]["post_feedback_system_entropy"],
                    "best_scrambled_post_feedback_memory_entropy": best_scrambled["metrics"]["post_feedback_memory_entropy"],
                    "ordering_margin": float(ordering_margin),
                    "ordered_beats_all_scrambled": bool(
                        all(
                            ordered["metrics"]["final_joint_entropy"]
                            <= proto["metrics"]["final_joint_entropy"] + 1e-12
                            for proto in primary_scrambled.values()
                        )
                    ),
                    "valid_density_all_protocols": bool(
                        ordered["metrics"]["valid_density"]
                        and all(proto["metrics"]["valid_density"] for proto in primary_scrambled.values())
                        and all(proto["metrics"]["valid_density"] for proto in diagnostic_scrambled.values())
                    ),
                    "max_trace_error": float(
                        max(
                            proto["states"]["final"]["trace_error_abs"]
                            for proto in [ordered, *primary_scrambled.values(), *diagnostic_scrambled.values()]
                        )
                    ),
                }
                rows.append(row)

                if (
                    measurement_error == 0.1
                    and record_lifetime_steps == 120
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
    short_rows = [row for row in rows if row["record_lifetime_steps"] in (60, 120)]
    long_rows = [row for row in rows if row["record_lifetime_steps"] in (240, 480)]
    weak_rows = [row for row in rows if row["reset_strength"] == min(RESET_STRENGTH_GRID)]
    strong_rows = [row for row in rows if row["reset_strength"] == max(RESET_STRENGTH_GRID)]
    low_noise_rows = [row for row in rows if row["measurement_error"] == min(MEASUREMENT_ERROR_GRID)]
    high_noise_rows = [row for row in rows if row["measurement_error"] == max(MEASUREMENT_ERROR_GRID)]

    def mean(values) -> float:
        values = list(values)
        return float(np.mean(values)) if values else 0.0

    mean_measurement_accuracy = mean(row["ordered_measurement_accuracy"] for row in rows)
    mean_measurement_mi = mean(row["ordered_measurement_mutual_information"] for row in rows)
    short_lifetime_mean_margin = mean(row["ordering_margin"] for row in short_rows)
    long_lifetime_mean_margin = mean(row["ordering_margin"] for row in long_rows)
    weak_reset_mean_entropy = mean(row["ordered_reset_memory_entropy"] for row in weak_rows)
    strong_reset_mean_entropy = mean(row["ordered_reset_memory_entropy"] for row in strong_rows)

    positive = {
        "measurement_stage_remains_informative": {
            "mean_measurement_accuracy": mean_measurement_accuracy,
            "mean_measurement_mutual_information": mean_measurement_mi,
            "pass": mean_measurement_mi > 0.05 and mean_measurement_accuracy > 0.6,
        },
        "ordered_protocol_can_outperform_scrambled_controls": {
            "best_ordering_margin": best_row["ordering_margin"],
            "best_setting": {
                "measurement_error": best_row["measurement_error"],
                "record_lifetime_steps": best_row["record_lifetime_steps"],
                "reset_strength": best_row["reset_strength"],
            },
            "pass": best_row["ordering_margin"] > 0.0,
        },
        "longer_lived_records_help_ordered_vs_scrambled_separation_on_average": {
            "short_lifetime_mean_margin": short_lifetime_mean_margin,
            "long_lifetime_mean_margin": long_lifetime_mean_margin,
            "pass": long_lifetime_mean_margin > short_lifetime_mean_margin,
        },
        "stronger_reset_reduces_residual_memory_entropy_on_average": {
            "weak_reset_mean_entropy_after_reset": weak_reset_mean_entropy,
            "strong_reset_mean_entropy_after_reset": strong_reset_mean_entropy,
            "pass": strong_reset_mean_entropy < weak_reset_mean_entropy,
        },
    }

    negative = {
        "long_lived_records_do_not_uniformly_dominate_short_lived_records": {
            "short_best_margin": float(max(row["ordering_margin"] for row in short_rows)),
            "long_worst_margin": float(min(row["ordering_margin"] for row in long_rows)),
            "pass": float(max(row["ordering_margin"] for row in short_rows))
            > float(min(row["ordering_margin"] for row in long_rows)),
        },
        "higher_measurement_noise_does_not_uniformly_destroy_the_ordering_signal": {
            "high_noise_best_margin": float(
                max(
                    row["ordering_margin"]
                    for row in rows
                    if row["measurement_error"] == max(MEASUREMENT_ERROR_GRID)
                )
            ),
            "pass": float(
                max(
                    row["ordering_margin"]
                    for row in rows
                    if row["measurement_error"] == max(MEASUREMENT_ERROR_GRID)
                )
            )
            > 0.0,
        },
        "record_lifetime_is_not_the_only_driver_of_ordering_margin": {
            "ordering_margin_range": float(max(row["ordering_margin"] for row in rows) - min(row["ordering_margin"] for row in rows)),
            "pass": float(max(row["ordering_margin"] for row in rows) - min(row["ordering_margin"] for row in rows)) > 1e-3,
        },
    }

    boundary = {
        "all_protocols_remain_valid_density_operators": {
            "pass": all(row["valid_density_all_protocols"] for row in rows),
        },
        "all_rows_have_finite_summary_values": {
            "pass": all(np.isfinite(row["ordering_margin"]) for row in rows),
        },
        "parameter_grid_covers_measurement_lifetime_and_reset_axes": {
            "measurement_error_values": MEASUREMENT_ERROR_GRID,
            "record_lifetime_steps_values": RECORD_LIFETIME_GRID,
            "reset_strength_values": RESET_STRENGTH_GRID,
            "n_points": len(rows),
            "pass": len(rows) == len(MEASUREMENT_ERROR_GRID) * len(RECORD_LIFETIME_GRID) * len(RESET_STRENGTH_GRID),
        },
    }

    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in negative.values())
        and all(item["pass"] for item in boundary.values())
    )

    summary = {
        "all_pass": all_pass,
        "measurement_error_grid": MEASUREMENT_ERROR_GRID,
        "record_lifetime_grid": RECORD_LIFETIME_GRID,
        "reset_strength_grid": RESET_STRENGTH_GRID,
        "record_wait_steps": RECORD_WAIT_STEPS,
        "best_ordering_margin": float(best_row["ordering_margin"]),
        "ordering_metric": "final_joint_entropy",
        "best_setting": {
            "measurement_error": best_row["measurement_error"],
            "record_lifetime_steps": best_row["record_lifetime_steps"],
            "reset_strength": best_row["reset_strength"],
        },
        "short_lifetime_mean_margin": short_lifetime_mean_margin,
        "long_lifetime_mean_margin": long_lifetime_mean_margin,
        "weak_reset_mean_memory_entropy_after_reset": weak_reset_mean_entropy,
        "strong_reset_mean_memory_entropy_after_reset": strong_reset_mean_entropy,
        "mean_measurement_accuracy": mean_measurement_accuracy,
        "mean_measurement_mutual_information": mean_measurement_mi,
        "mean_record_survival_fraction": mean(row["ordered_record_survival_fraction"] for row in rows),
        "scope_note": (
            "QIT-aligned finite two-qubit companion row for record lifetime, record decay, "
            "and reset strength. It separates ordered, scrambled, and repair-oriented "
            "protocols without promoting the row to canonical status."
        ),
    }

    results = {
        "name": "qit_szilard_record_companion",
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

    out_path = PROBE_DIR / "a2_state" / "sim_results" / "qit_szilard_record_companion_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str) + "\n")
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
