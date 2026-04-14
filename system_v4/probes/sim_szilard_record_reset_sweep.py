#!/usr/bin/env python3
"""
Szilard Record / Reset Sweep
============================
Exploratory stochastic sweep over three distinct sub-mechanics:

  - record reliability at measurement time
  - record lifetime during a waiting window
  - reset strength during the clearing stage

The probe keeps the existing finite double-well memory model, but it now asks a
different question:
  does a record that survives longer actually improve ordered-vs-scrambled
  separation, and does a stronger reset reduce the residual memory entropy?

This is a controller-facing sweep, not a canonical engine theorem.
"""

from __future__ import annotations

import json
import pathlib

import numpy as np

import sim_stoch_doublewell_landauer_erasure as base
classification = "classical_baseline"  # auto-backfill


CLASSIFICATION = "exploratory"
CLASSIFICATION_NOTE = (
    "Exploratory Szilard sweep over record lifetime, record reliability, and "
    "reset strength on a finite double-well carrier. The probe checks whether "
    "a longer-lived record materially improves ordered-vs-scrambled separation "
    "and whether stronger reset lowers residual memory entropy."
)

LEGO_IDS = [
    "stochastic_thermodynamics",
    "measurement_feedback",
    "landauer_erasure",
]

PRIMARY_LEGO_IDS = [
    "stochastic_thermodynamics",
    "measurement_feedback",
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

DT = 0.0025
GAMMA = 1.0
TEMPERATURE = 1.0
N_TRAJ = 2400
MEAS_STEPS = 90
RECORD_WAIT_STEPS = 120
FEEDBACK_STEPS = 120
RESET_STEPS = 120
HOLD_STEPS = 60
RNG_SEED = 20260410
LEFT_STATE_THRESHOLD = 0.0
MEASUREMENT_FLIP_GRID = [0.02, 0.08, 0.18]
RECORD_LIFETIME_GRID = [60, 120, 240, 480]
RESET_TILT_GRID = [1.15, 1.55, 1.95]
FEEDBACK_STRONG_TILT = 1.85
FEEDBACK_WEAK_TILT = 0.25
MEASUREMENT_RECORD_DECAY_FLOOR = 1e-15


def binary_entropy_nats(p: float) -> float:
    p = min(max(float(p), 1e-15), 1.0 - 1e-15)
    return float(-(p * np.log(p) + (1.0 - p) * np.log(1.0 - p)))


def double_well_potential(x: np.ndarray, barrier: float, tilt: float) -> np.ndarray:
    return barrier * (x * x - 1.0) ** 2 + tilt * x


def double_well_force(x: np.ndarray, barrier: float, tilt: float) -> np.ndarray:
    d_u_dx = 4.0 * barrier * x * (x * x - 1.0) + tilt
    return -d_u_dx


def sample_symmetric_initial_state(n_traj: int, rng: np.random.Generator) -> np.ndarray:
    base = rng.choice([-1.0, 1.0], size=n_traj)
    return base + 0.18 * rng.standard_normal(n_traj)


def binary_readout(x: np.ndarray, flip_prob: float, rng: np.random.Generator) -> np.ndarray:
    observed = (np.asarray(x) >= LEFT_STATE_THRESHOLD).astype(int)
    if flip_prob <= 0.0:
        return observed
    flips = rng.random(observed.shape[0]) < flip_prob
    return np.where(flips, 1 - observed, observed).astype(int)


def confusion_metrics(true_bits: np.ndarray, obs_bits: np.ndarray) -> dict:
    true_bits = np.asarray(true_bits, dtype=int).reshape(-1)
    obs_bits = np.asarray(obs_bits, dtype=int).reshape(-1)
    if true_bits.shape != obs_bits.shape:
        raise ValueError("bit arrays must align")

    p_true1 = float(np.mean(true_bits == 1))
    p_obs1 = float(np.mean(obs_bits == 1))
    p11 = float(np.mean((true_bits == 1) & (obs_bits == 1)))
    p10 = float(np.mean((true_bits == 1) & (obs_bits == 0)))
    p01 = float(np.mean((true_bits == 0) & (obs_bits == 1)))
    p00 = float(np.mean((true_bits == 0) & (obs_bits == 0)))

    mutual_information = 0.0
    for pxy, px, py in [
        (p11, p_true1, p_obs1),
        (p10, p_true1, 1.0 - p_obs1),
        (p01, 1.0 - p_true1, p_obs1),
        (p00, 1.0 - p_true1, 1.0 - p_obs1),
    ]:
        if pxy > 0.0:
            mutual_information += pxy * np.log(pxy / (px * py))

    return {
        "p_true_right": p_true1,
        "p_obs_right": p_obs1,
        "accuracy": float(np.mean(true_bits == obs_bits)),
        "false_positive_rate": p01 / max(1.0 - p_true1, 1e-15),
        "false_negative_rate": p10 / max(p_true1, 1e-15),
        "mutual_information": float(mutual_information),
        "joint_right_right": p11,
        "joint_right_left": p10,
        "joint_left_right": p01,
        "joint_left_left": p00,
        "n": float(true_bits.size),
    }


def stage_entropy(x: np.ndarray) -> float:
    return binary_entropy_nats(float(np.mean(np.asarray(x) < LEFT_STATE_THRESHOLD)))


def build_stage_library(reset_tilt: float, measurement_flip_prob: float) -> dict:
    return {
        "measurement": base.StageSpec(
            name="measurement_window",
            kind="measurement",
            steps=MEAS_STEPS,
            temperature=TEMPERATURE,
            barrier_start=1.55,
            barrier_end=0.10,
            tilt_start=0.0,
            tilt_end=0.0,
            measurement_flip_prob=measurement_flip_prob,
        ),
        "record_wait": base.StageSpec(
            name="record_wait_window",
            kind="record_wait",
            steps=RECORD_WAIT_STEPS,
            temperature=TEMPERATURE,
            barrier_start=1.55,
            barrier_end=1.55,
            tilt_start=0.0,
            tilt_end=0.0,
        ),
        "feedback": base.StageSpec(
            name="feedback_drive",
            kind="feedback",
            steps=FEEDBACK_STEPS,
            temperature=TEMPERATURE,
            barrier_start=0.10,
            barrier_end=1.55,
            tilt_start=0.0,
            tilt_end=0.0,
            feedback_strong_tilt=FEEDBACK_STRONG_TILT,
            feedback_weak_tilt=FEEDBACK_WEAK_TILT,
        ),
        "reset": base.StageSpec(
            name="reset_lock",
            kind="reset",
            steps=RESET_STEPS,
            temperature=TEMPERATURE,
            barrier_start=1.55,
            barrier_end=1.55,
            tilt_start=FEEDBACK_WEAK_TILT,
            tilt_end=reset_tilt,
        ),
        "hold": base.StageSpec(
            name="left_hold",
            kind="hold",
            steps=HOLD_STEPS,
            temperature=TEMPERATURE,
            barrier_start=1.55,
            barrier_end=1.55,
            tilt_start=reset_tilt,
            tilt_end=reset_tilt,
        ),
    }


def run_protocol(
    x0: np.ndarray,
    order: list[str],
    measurement_flip_prob: float,
    record_lifetime_steps: int,
    reset_tilt: float,
    rng: np.random.Generator,
) -> dict:
    library = build_stage_library(reset_tilt=reset_tilt, measurement_flip_prob=measurement_flip_prob)

    x = np.asarray(x0, dtype=float).copy()
    n = x.shape[0]
    total_work = np.zeros(n, dtype=float)
    total_heat = np.zeros(n, dtype=float)
    total_delta_u = np.zeros(n, dtype=float)
    stage_logs = []

    measured_bits = None
    measurement_record = None
    record_history = []
    reset_stage_entropy = None
    initial_bits = (x >= LEFT_STATE_THRESHOLD).astype(int)

    for stage_name in order:
        stage = library[stage_name]
        stage_entry = {
            "name": stage.name,
            "kind": stage.kind,
        }

        if stage.kind == "measurement":
            x_before = x.copy()
            x, stage_work, stage_heat, stage_delta_u, stage_log = base.stage_simulation(
                x,
                stage.barrier_start,
                stage.barrier_end,
                stage.tilt_start,
                stage.tilt_end,
                stage.steps,
                stage.temperature,
                rng,
            )
            true_bits = (x_before >= LEFT_STATE_THRESHOLD).astype(int)
            sensed_bits = binary_readout(x, stage.measurement_flip_prob, rng)
            measured_bits = sensed_bits
            measurement_record = sensed_bits.copy()
            stage_entry.update(stage_log)
            stage_entry["measurement"] = confusion_metrics(true_bits, sensed_bits)
            stage_entry["record_after_stage"] = "present"
            stage_entry["record_accuracy_against_truth"] = float(np.mean(sensed_bits == true_bits))

        elif stage.kind == "record_wait":
            x, stage_work, stage_heat, stage_delta_u, stage_log = base.stage_simulation(
                x,
                stage.barrier_start,
                stage.barrier_end,
                stage.tilt_start,
                stage.tilt_end,
                stage.steps,
                stage.temperature,
                rng,
            )
            if measurement_record is not None:
                prior_record = measurement_record.copy()
                decay_prob = 1.0 - float(np.exp(-float(stage.steps) / max(float(record_lifetime_steps), MEASUREMENT_RECORD_DECAY_FLOOR)))
                flips = rng.random(prior_record.shape[0]) < decay_prob
                measurement_record = np.where(flips, 1 - measurement_record, measurement_record)
                stage_entry["record_decay_probability"] = float(decay_prob)
                stage_entry["record_survival_fraction"] = float(np.mean(measurement_record == prior_record))
                stage_entry["record_accuracy_against_measurement"] = float(np.mean(measurement_record == measured_bits))
                record_history.append(
                    {
                        "stage": stage.name,
                        "survival_fraction": stage_entry["record_survival_fraction"],
                        "accuracy_against_measurement": stage_entry["record_accuracy_against_measurement"],
                        "decay_probability": float(decay_prob),
                    }
                )
            stage_entry["record_after_stage"] = "present" if measurement_record is not None else "absent"

        elif stage.kind == "feedback":
            if measurement_record is None:
                control_bits = rng.integers(0, 2, size=n)
                control_mode = "blind_guess"
                right_tilt = stage.feedback_strong_tilt
                left_tilt = -stage.feedback_strong_tilt
            else:
                control_bits = measurement_record
                control_mode = "recorded"
                right_tilt = stage.feedback_strong_tilt
                left_tilt = stage.feedback_weak_tilt

            right_mask = control_bits == 1
            left_mask = ~right_mask
            x_out = x.copy()
            stage_work = np.zeros(n, dtype=float)
            stage_heat = np.zeros(n, dtype=float)
            stage_delta_u = np.zeros(n, dtype=float)
            branch_metrics = {}

            if np.any(right_mask):
                x_right, work_right, heat_right, delta_u_right, log_right = base.stage_simulation(
                    x[right_mask],
                    stage.barrier_start,
                    stage.barrier_end,
                    0.0,
                    right_tilt,
                    stage.steps,
                    stage.temperature,
                    rng,
                )
                x_out[right_mask] = x_right
                stage_work[right_mask] = work_right
                stage_heat[right_mask] = heat_right
                stage_delta_u[right_mask] = delta_u_right
                branch_metrics["right_branch"] = {
                    "mean_work": float(np.mean(work_right)),
                    "mean_heat": float(np.mean(heat_right)),
                    "mean_delta_u": float(np.mean(delta_u_right)),
                    "closure_error": float(abs(np.mean(delta_u_right) - np.mean(work_right) - np.mean(heat_right))),
                    "count": int(np.sum(right_mask)),
                    "final_left_fraction": float(np.mean(x_right < LEFT_STATE_THRESHOLD)),
                }
                stage_entry.setdefault("branch_logs", []).append({"branch": "right", **log_right, "count": int(np.sum(right_mask))})

            if np.any(left_mask):
                x_left, work_left, heat_left, delta_u_left, log_left = base.stage_simulation(
                    x[left_mask],
                    stage.barrier_start,
                    stage.barrier_end,
                    0.0,
                    left_tilt,
                    stage.steps,
                    stage.temperature,
                    rng,
                )
                x_out[left_mask] = x_left
                stage_work[left_mask] = work_left
                stage_heat[left_mask] = heat_left
                stage_delta_u[left_mask] = delta_u_left
                branch_metrics["left_branch"] = {
                    "mean_work": float(np.mean(work_left)),
                    "mean_heat": float(np.mean(heat_left)),
                    "mean_delta_u": float(np.mean(delta_u_left)),
                    "closure_error": float(abs(np.mean(delta_u_left) - np.mean(work_left) - np.mean(heat_left))),
                    "count": int(np.sum(left_mask)),
                    "final_left_fraction": float(np.mean(x_left < LEFT_STATE_THRESHOLD)),
                }
                stage_entry.setdefault("branch_logs", []).append({"branch": "left", **log_left, "count": int(np.sum(left_mask))})

            x = x_out
            stage_entry["control_mode"] = control_mode
            stage_entry["branch_metrics"] = branch_metrics
            stage_entry["mean_work"] = float(np.mean(stage_work))
            stage_entry["mean_heat"] = float(np.mean(stage_heat))
            stage_entry["mean_delta_u"] = float(np.mean(stage_delta_u))
            stage_entry["record_after_stage"] = "present" if measurement_record is not None else "absent"

        elif stage.kind == "reset":
            x, stage_work, stage_heat, stage_delta_u, stage_log = base.stage_simulation(
                x,
                stage.barrier_start,
                stage.barrier_end,
                stage.tilt_start,
                stage.tilt_end,
                stage.steps,
                stage.temperature,
                rng,
            )
            measurement_record = None
            stage_entry.update(stage_log)
            stage_entry["record_after_stage"] = "cleared"
            reset_stage_entropy = stage_entropy(x)

        elif stage.kind == "hold":
            x, stage_work, stage_heat, stage_delta_u, stage_log = base.stage_simulation(
                x,
                stage.barrier_start,
                stage.barrier_end,
                stage.tilt_start,
                stage.tilt_end,
                stage.steps,
                stage.temperature,
                rng,
            )
            stage_entry.update(stage_log)
            stage_entry["record_after_stage"] = "unchanged"

        else:
            raise ValueError(f"unknown stage kind: {stage.kind}")

        total_work += stage_work
        total_heat += stage_heat
        total_delta_u += stage_delta_u
        stage_entry["entropy_after_stage"] = stage_entropy(x)
        stage_logs.append(stage_entry)

    final_bits = (x < LEFT_STATE_THRESHOLD).astype(int)
    final_entropy = binary_entropy_nats(float(np.mean(final_bits == 1)))
    initial_entropy = binary_entropy_nats(float(np.mean(initial_bits == 1)))
    measured_accuracy = None
    measured_mutual_information = None
    if measured_bits is not None:
        measured_accuracy = float(np.mean(measured_bits == initial_bits))
        measured_mutual_information = confusion_metrics(initial_bits, measured_bits)["mutual_information"]

    record_survival_fraction = None
    record_accuracy_against_measurement = None
    if record_history:
        record_survival_fraction = float(np.mean([item["survival_fraction"] for item in record_history]))
        record_accuracy_against_measurement = float(np.mean([item["accuracy_against_measurement"] for item in record_history]))

    return {
        "order": order,
        "measurement_flip_prob": float(measurement_flip_prob),
        "record_lifetime_steps": int(record_lifetime_steps),
        "reset_tilt": float(reset_tilt),
        "initial_left_fraction": float(np.mean(initial_bits == 0)),
        "final_left_fraction": float(np.mean(final_bits == 0)),
        "initial_entropy": float(initial_entropy),
        "final_entropy": float(final_entropy),
        "reset_stage_entropy": float(reset_stage_entropy) if reset_stage_entropy is not None else None,
        "measurement_record_present_at_end": bool(measurement_record is not None),
        "measurement_accuracy": measured_accuracy,
        "measurement_mutual_information": measured_mutual_information,
        "record_survival_fraction": record_survival_fraction,
        "record_accuracy_against_measurement": record_accuracy_against_measurement,
        "record_history": record_history,
        "mean_work": float(np.mean(total_work)),
        "mean_heat": float(np.mean(total_heat)),
        "mean_delta_u": float(np.mean(total_delta_u)),
        "closure_error": float(abs(np.mean(total_delta_u) - np.mean(total_work) - np.mean(total_heat))),
        "stage_logs": stage_logs,
    }


def main() -> None:
    rows = []
    by_setting = {}
    seed = RNG_SEED

    for measurement_flip_prob in MEASUREMENT_FLIP_GRID:
        for record_lifetime_steps in RECORD_LIFETIME_GRID:
            for reset_tilt in RESET_TILT_GRID:
                rng = np.random.default_rng(seed)
                x_init = sample_symmetric_initial_state(N_TRAJ, rng)

                ordered = run_protocol(
                    x_init,
                    ["measurement", "record_wait", "feedback", "reset", "hold"],
                    measurement_flip_prob=measurement_flip_prob,
                    record_lifetime_steps=record_lifetime_steps,
                    reset_tilt=reset_tilt,
                    rng=np.random.default_rng(seed + 1),
                )
                feedback_first = run_protocol(
                    x_init,
                    ["feedback", "measurement", "record_wait", "reset", "hold"],
                    measurement_flip_prob=measurement_flip_prob,
                    record_lifetime_steps=record_lifetime_steps,
                    reset_tilt=reset_tilt,
                    rng=np.random.default_rng(seed + 2),
                )
                reset_first = run_protocol(
                    x_init,
                    ["reset", "measurement", "record_wait", "feedback", "hold"],
                    measurement_flip_prob=measurement_flip_prob,
                    record_lifetime_steps=record_lifetime_steps,
                    reset_tilt=reset_tilt,
                    rng=np.random.default_rng(seed + 3),
                )
                measurement_then_reset_then_feedback = run_protocol(
                    x_init,
                    ["measurement", "reset", "record_wait", "feedback", "hold"],
                    measurement_flip_prob=measurement_flip_prob,
                    record_lifetime_steps=record_lifetime_steps,
                    reset_tilt=reset_tilt,
                    rng=np.random.default_rng(seed + 4),
                )
                measurement_only = run_protocol(
                    x_init,
                    ["measurement", "record_wait", "hold"],
                    measurement_flip_prob=measurement_flip_prob,
                    record_lifetime_steps=record_lifetime_steps,
                    reset_tilt=reset_tilt,
                    rng=np.random.default_rng(seed + 5),
                )

                scrambled = {
                    "feedback_first": feedback_first["final_entropy"],
                    "reset_first": reset_first["final_entropy"],
                    "measurement_then_reset_then_feedback": measurement_then_reset_then_feedback["final_entropy"],
                }
                best_scrambled_name = min(scrambled, key=scrambled.get)
                best_scrambled_entropy = scrambled[best_scrambled_name]

                rows.append(
                    {
                        "measurement_flip_prob": float(measurement_flip_prob),
                        "record_lifetime_steps": int(record_lifetime_steps),
                        "reset_tilt": float(reset_tilt),
                        "ordered_final_entropy": float(ordered["final_entropy"]),
                        "ordered_reset_stage_entropy": float(ordered["reset_stage_entropy"]),
                        "ordered_measurement_accuracy": float(ordered["measurement_accuracy"]),
                        "ordered_measurement_mi": float(ordered["measurement_mutual_information"]),
                        "ordered_record_survival_fraction": float(ordered["record_survival_fraction"]),
                        "ordered_record_accuracy_against_measurement": float(ordered["record_accuracy_against_measurement"]),
                        "measurement_only_final_entropy": float(measurement_only["final_entropy"]),
                        "feedback_first_final_entropy": float(feedback_first["final_entropy"]),
                        "reset_first_final_entropy": float(reset_first["final_entropy"]),
                        "measurement_then_reset_then_feedback_final_entropy": float(
                            measurement_then_reset_then_feedback["final_entropy"]
                        ),
                        "best_scrambled_name": best_scrambled_name,
                        "best_scrambled_entropy": float(best_scrambled_entropy),
                        "ordering_margin": float(best_scrambled_entropy - ordered["final_entropy"]),
                        "ordered_beats_all_scrambled": bool(ordered["final_entropy"] < min(scrambled.values())),
                        "closure_error_max": float(
                            max(
                                ordered["closure_error"],
                                feedback_first["closure_error"],
                                reset_first["closure_error"],
                                measurement_then_reset_then_feedback["closure_error"],
                                measurement_only["closure_error"],
                            )
                        ),
                    }
                )

                by_setting[f"{measurement_flip_prob:.2f}|{record_lifetime_steps}|{reset_tilt:.2f}"] = {
                    "ordered": ordered,
                    "feedback_first": feedback_first,
                    "reset_first": reset_first,
                    "measurement_then_reset_then_feedback": measurement_then_reset_then_feedback,
                    "measurement_only": measurement_only,
                }

                seed += 1

    best_margin_row = max(rows, key=lambda row: row["ordering_margin"])
    low_lifetime_rows = [row for row in rows if row["record_lifetime_steps"] == min(RECORD_LIFETIME_GRID)]
    high_lifetime_rows = [row for row in rows if row["record_lifetime_steps"] == max(RECORD_LIFETIME_GRID)]
    low_reset_rows = [row for row in rows if row["reset_tilt"] == min(RESET_TILT_GRID)]
    high_reset_rows = [row for row in rows if row["reset_tilt"] == max(RESET_TILT_GRID)]
    low_noise_rows = [row for row in rows if row["measurement_flip_prob"] == min(MEASUREMENT_FLIP_GRID)]
    high_noise_rows = [row for row in rows if row["measurement_flip_prob"] == max(MEASUREMENT_FLIP_GRID)]

    positive = {
        "measurement_stage_remains_informative": {
            "accuracy": float(np.mean([row["ordered_measurement_accuracy"] for row in rows])),
            "mutual_information": float(np.mean([row["ordered_measurement_mi"] for row in rows])),
            "pass": float(np.mean([row["ordered_measurement_accuracy"] for row in rows])) > 0.58
            and float(np.mean([row["ordered_measurement_mi"] for row in rows])) > 0.03,
        },
        "some_settings_make_correct_order_better_than_scrambled_alternatives": {
            "best_margin": float(best_margin_row["ordering_margin"]),
            "best_setting": {
                "measurement_flip_prob": float(best_margin_row["measurement_flip_prob"]),
                "record_lifetime_steps": int(best_margin_row["record_lifetime_steps"]),
                "reset_tilt": float(best_margin_row["reset_tilt"]),
            },
            "pass": float(best_margin_row["ordering_margin"]) > 0.01,
        },
        "longer_lived_records_help_ordered_vs_scrambled_separation_on_average": {
            "short_lifetime_mean_margin": float(np.mean([row["ordering_margin"] for row in low_lifetime_rows])),
            "long_lifetime_mean_margin": float(np.mean([row["ordering_margin"] for row in high_lifetime_rows])),
            "pass": float(np.mean([row["ordering_margin"] for row in high_lifetime_rows]))
            > float(np.mean([row["ordering_margin"] for row in low_lifetime_rows])),
        },
        "stronger_reset_reduces_residual_memory_entropy_on_average": {
            "weak_reset_mean_entropy_after_reset": float(
                np.mean([row["ordered_reset_stage_entropy"] for row in low_reset_rows])
            ),
            "strong_reset_mean_entropy_after_reset": float(
                np.mean([row["ordered_reset_stage_entropy"] for row in high_reset_rows])
            ),
            "pass": float(np.mean([row["ordered_reset_stage_entropy"] for row in high_reset_rows]))
            < float(np.mean([row["ordered_reset_stage_entropy"] for row in low_reset_rows])) - 0.005,
        },
    }

    negative = {
        "short_lived_records_do_not_uniformly_match_long_lived_separation": {
            "short_lifetime_best_margin": float(max(row["ordering_margin"] for row in low_lifetime_rows)),
            "long_lifetime_best_margin": float(max(row["ordering_margin"] for row in high_lifetime_rows)),
            "pass": float(max(row["ordering_margin"] for row in low_lifetime_rows))
            < float(max(row["ordering_margin"] for row in high_lifetime_rows)),
        },
        "high_noise_rows_do_not_rescue_record_separation_by_themselves": {
            "high_noise_best_margin": float(max(row["ordering_margin"] for row in high_noise_rows)),
            "low_noise_best_margin": float(max(row["ordering_margin"] for row in low_noise_rows)),
            "pass": not all(
                high_row["ordering_margin"] > low_row["ordering_margin"]
                for high_row in high_noise_rows
                for low_row in low_noise_rows
            ),
        },
    }

    boundary = {
        "all_protocols_close_work_heat_bookkeeping": {
            "max_closure_error": float(max(row["closure_error_max"] for row in rows)),
            "pass": float(max(row["closure_error_max"] for row in rows)) < 1e-9,
        },
        "all_rows_have_finite_summary_values": {
            "pass": all(
                np.isfinite(value)
                for row in rows
                for value in row.values()
                if isinstance(value, (int, float))
            ),
        },
    }

    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in negative.values())
        and all(item["pass"] for item in boundary.values())
    )

    out = {
        "name": "szilard_record_reset_sweep",
        "classification": CLASSIFICATION,
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
            "measurement_flip_grid": MEASUREMENT_FLIP_GRID,
            "record_lifetime_grid": RECORD_LIFETIME_GRID,
            "reset_tilt_grid": RESET_TILT_GRID,
            "record_wait_steps": RECORD_WAIT_STEPS,
            "best_ordering_margin": float(best_margin_row["ordering_margin"]),
            "best_setting": {
                "measurement_flip_prob": float(best_margin_row["measurement_flip_prob"]),
                "record_lifetime_steps": int(best_margin_row["record_lifetime_steps"]),
                "reset_tilt": float(best_margin_row["reset_tilt"]),
            },
            "scope_note": (
                "Exploratory Szilard sweep that separates record reliability, record "
                "lifetime, and reset strength on a finite double-well carrier."
            ),
        },
        "rows": rows,
        "by_setting": by_setting,
    }

    out_dir = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "szilard_record_reset_sweep_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
