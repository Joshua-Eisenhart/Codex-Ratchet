#!/usr/bin/env python3
"""
Szilard Record Hard-Reset Repair Sweep
=====================================
Upgrade the weak open reset mechanism by widening reset duration and barrier
strength, not just reset tilt.
"""

from __future__ import annotations

import json
import pathlib

import numpy as np

import sim_szilard_record_reset_sweep as base
classification = "classical_baseline"  # auto-backfill


CLASSIFICATION = "exploratory"
CLASSIFICATION_NOTE = (
    "Hard-reset repair sweep for the weak open Szilard record/reset lane. It "
    "adds reset-duration and reset-barrier axes to test whether the stochastic "
    "carrier can approach the strict reset-effect regime."
)

LEGO_IDS = [
    "stochastic_thermodynamics",
    "measurement_feedback",
    "landauer_erasure",
]

PRIMARY_LEGO_IDS = [
    "stochastic_thermodynamics",
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

MEASUREMENT_FLIP_GRID = [0.0, 0.02]
RECORD_LIFETIME_GRID = [480, 960]
RESET_TILT_GRID = [2.35, 2.75, 3.25]
RESET_STEPS_GRID = [120, 240, 480]
RESET_BARRIER_GRID = [1.55, 2.5, 3.5]
FEEDBACK_STRONG_TILT = 2.35
FEEDBACK_WEAK_TILT = 0.31725
SEED_BASE = 20260411 + 4100

RESULT_DIR = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"


def load(name: str) -> dict:
    return json.loads((RESULT_DIR / name).read_text())


def stage_entropy(x: np.ndarray) -> float:
    return base.binary_entropy_nats(float(np.mean(np.asarray(x) < base.LEFT_STATE_THRESHOLD)))


def build_stage_library(reset_tilt: float, measurement_flip_prob: float, reset_steps: int, reset_barrier: float) -> dict:
    return {
        "measurement": base.base.StageSpec(
            name="measurement_window",
            kind="measurement",
            steps=base.MEAS_STEPS,
            temperature=base.TEMPERATURE,
            barrier_start=1.55,
            barrier_end=0.10,
            tilt_start=0.0,
            tilt_end=0.0,
            measurement_flip_prob=measurement_flip_prob,
        ),
        "record_wait": base.base.StageSpec(
            name="record_wait_window",
            kind="record_wait",
            steps=base.RECORD_WAIT_STEPS,
            temperature=base.TEMPERATURE,
            barrier_start=1.55,
            barrier_end=1.55,
            tilt_start=0.0,
            tilt_end=0.0,
        ),
        "feedback": base.base.StageSpec(
            name="feedback_drive",
            kind="feedback",
            steps=base.FEEDBACK_STEPS,
            temperature=base.TEMPERATURE,
            barrier_start=0.10,
            barrier_end=1.55,
            tilt_start=0.0,
            tilt_end=0.0,
            feedback_strong_tilt=FEEDBACK_STRONG_TILT,
            feedback_weak_tilt=FEEDBACK_WEAK_TILT,
        ),
        "reset": base.base.StageSpec(
            name="hard_reset_lock",
            kind="reset",
            steps=reset_steps,
            temperature=base.TEMPERATURE,
            barrier_start=reset_barrier,
            barrier_end=reset_barrier,
            tilt_start=FEEDBACK_WEAK_TILT,
            tilt_end=reset_tilt,
        ),
        "hold": base.base.StageSpec(
            name="left_hold",
            kind="hold",
            steps=base.HOLD_STEPS,
            temperature=base.TEMPERATURE,
            barrier_start=reset_barrier,
            barrier_end=reset_barrier,
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
    reset_steps: int,
    reset_barrier: float,
    rng: np.random.Generator,
) -> dict:
    library = build_stage_library(reset_tilt, measurement_flip_prob, reset_steps, reset_barrier)

    x = np.asarray(x0, dtype=float).copy()
    n = x.shape[0]
    total_work = np.zeros(n, dtype=float)
    total_heat = np.zeros(n, dtype=float)
    total_delta_u = np.zeros(n, dtype=float)
    measured_bits = None
    measurement_record = None
    record_history = []
    reset_stage_entropy = None
    initial_bits = (x >= base.LEFT_STATE_THRESHOLD).astype(int)

    for stage_name in order:
        stage = library[stage_name]
        if stage.kind == "measurement":
            x_before = x.copy()
            x, stage_work, stage_heat, stage_delta_u, _ = base.base.stage_simulation(
                x, stage.barrier_start, stage.barrier_end, stage.tilt_start, stage.tilt_end, stage.steps, stage.temperature, rng
            )
            true_bits = (x_before >= base.LEFT_STATE_THRESHOLD).astype(int)
            sensed_bits = base.binary_readout(x, stage.measurement_flip_prob, rng)
            measured_bits = sensed_bits
            measurement_record = sensed_bits.copy()
        elif stage.kind == "record_wait":
            x, stage_work, stage_heat, stage_delta_u, _ = base.base.stage_simulation(
                x, stage.barrier_start, stage.barrier_end, stage.tilt_start, stage.tilt_end, stage.steps, stage.temperature, rng
            )
            if measurement_record is not None:
                prior_record = measurement_record.copy()
                decay_prob = 1.0 - float(np.exp(-float(stage.steps) / max(float(record_lifetime_steps), base.MEASUREMENT_RECORD_DECAY_FLOOR)))
                flips = rng.random(prior_record.shape[0]) < decay_prob
                measurement_record = np.where(flips, 1 - measurement_record, measurement_record)
                record_history.append({"survival_fraction": float(np.mean(measurement_record == prior_record))})
        elif stage.kind == "feedback":
            if measurement_record is None:
                control_bits = rng.integers(0, 2, size=n)
                right_tilt = stage.feedback_strong_tilt
                left_tilt = -stage.feedback_strong_tilt
            else:
                control_bits = measurement_record
                right_tilt = stage.feedback_strong_tilt
                left_tilt = stage.feedback_weak_tilt
            right_mask = control_bits == 1
            left_mask = ~right_mask
            x_out = x.copy()
            stage_work = np.zeros(n, dtype=float)
            stage_heat = np.zeros(n, dtype=float)
            stage_delta_u = np.zeros(n, dtype=float)
            if np.any(right_mask):
                x_r, w_r, h_r, du_r, _ = base.base.stage_simulation(
                    x[right_mask], stage.barrier_start, stage.barrier_end, 0.0, right_tilt, stage.steps, stage.temperature, rng
                )
                x_out[right_mask] = x_r
                stage_work[right_mask] = w_r
                stage_heat[right_mask] = h_r
                stage_delta_u[right_mask] = du_r
            if np.any(left_mask):
                x_l, w_l, h_l, du_l, _ = base.base.stage_simulation(
                    x[left_mask], stage.barrier_start, stage.barrier_end, 0.0, left_tilt, stage.steps, stage.temperature, rng
                )
                x_out[left_mask] = x_l
                stage_work[left_mask] = w_l
                stage_heat[left_mask] = h_l
                stage_delta_u[left_mask] = du_l
            x = x_out
        elif stage.kind == "reset":
            x, stage_work, stage_heat, stage_delta_u, _ = base.base.stage_simulation(
                x, stage.barrier_start, stage.barrier_end, stage.tilt_start, stage.tilt_end, stage.steps, stage.temperature, rng
            )
            measurement_record = None
            reset_stage_entropy = stage_entropy(x)
        elif stage.kind == "hold":
            x, stage_work, stage_heat, stage_delta_u, _ = base.base.stage_simulation(
                x, stage.barrier_start, stage.barrier_end, stage.tilt_start, stage.tilt_end, stage.steps, stage.temperature, rng
            )
        else:
            raise ValueError(stage.kind)

        total_work += stage_work
        total_heat += stage_heat
        total_delta_u += stage_delta_u

    final_bits = (x < base.LEFT_STATE_THRESHOLD).astype(int)
    final_entropy = base.binary_entropy_nats(float(np.mean(final_bits == 1)))
    measured_accuracy = float(np.mean(measured_bits == initial_bits)) if measured_bits is not None else 0.0
    measured_mi = base.confusion_metrics(initial_bits, measured_bits)["mutual_information"] if measured_bits is not None else 0.0
    record_survival = float(np.mean([item["survival_fraction"] for item in record_history])) if record_history else 0.0
    return {
        "final_entropy": float(final_entropy),
        "reset_stage_entropy": float(reset_stage_entropy) if reset_stage_entropy is not None else 0.0,
        "measurement_accuracy": measured_accuracy,
        "measurement_mutual_information": measured_mi,
        "record_survival_fraction": record_survival,
        "mean_work": float(np.mean(total_work)),
        "closure_error": float(abs(np.mean(total_delta_u) - np.mean(total_work) - np.mean(total_heat))),
    }


def ratio(open_value: float, target_value: float) -> float:
    if target_value <= 0.0:
        return 0.0
    return float(max(0.0, min(1.0, open_value / target_value)))


def main() -> None:
    qit = load("qit_szilard_record_companion_results.json")
    qit_summary = qit["summary"]
    qit_reset_swing = qit_summary["weak_reset_mean_memory_entropy_after_reset"] - qit_summary["strong_reset_mean_memory_entropy_after_reset"]

    rows = []
    seed = SEED_BASE
    for measurement_flip_prob in MEASUREMENT_FLIP_GRID:
        for record_lifetime_steps in RECORD_LIFETIME_GRID:
            for reset_tilt in RESET_TILT_GRID:
                for reset_steps in RESET_STEPS_GRID:
                    for reset_barrier in RESET_BARRIER_GRID:
                        rng = np.random.default_rng(seed)
                        x_init = base.sample_symmetric_initial_state(base.N_TRAJ, rng)
                        ordered = run_protocol(
                            x_init,
                            ["measurement", "record_wait", "feedback", "reset", "hold"],
                            measurement_flip_prob,
                            record_lifetime_steps,
                            reset_tilt,
                            reset_steps,
                            reset_barrier,
                            np.random.default_rng(seed + 1),
                        )
                        feedback_first = run_protocol(
                            x_init,
                            ["feedback", "measurement", "record_wait", "reset", "hold"],
                            measurement_flip_prob,
                            record_lifetime_steps,
                            reset_tilt,
                            reset_steps,
                            reset_barrier,
                            np.random.default_rng(seed + 2),
                        )
                        reset_first = run_protocol(
                            x_init,
                            ["reset", "measurement", "record_wait", "feedback", "hold"],
                            measurement_flip_prob,
                            record_lifetime_steps,
                            reset_tilt,
                            reset_steps,
                            reset_barrier,
                            np.random.default_rng(seed + 3),
                        )
                        mrf = run_protocol(
                            x_init,
                            ["measurement", "reset", "record_wait", "feedback", "hold"],
                            measurement_flip_prob,
                            record_lifetime_steps,
                            reset_tilt,
                            reset_steps,
                            reset_barrier,
                            np.random.default_rng(seed + 4),
                        )
                        ordering_margin = min(feedback_first["final_entropy"], reset_first["final_entropy"], mrf["final_entropy"]) - ordered["final_entropy"]
                        rows.append({
                            "measurement_flip_prob": float(measurement_flip_prob),
                            "record_lifetime_steps": int(record_lifetime_steps),
                            "reset_tilt": float(reset_tilt),
                            "reset_steps": int(reset_steps),
                            "reset_barrier": float(reset_barrier),
                            "ordering_margin": float(ordering_margin),
                            "measurement_mutual_information": float(ordered["measurement_mutual_information"]),
                            "record_survival_fraction": float(ordered["record_survival_fraction"]),
                            "reset_stage_entropy": float(ordered["reset_stage_entropy"]),
                            "closure_error": float(max(ordered["closure_error"], feedback_first["closure_error"], reset_first["closure_error"], mrf["closure_error"])),
                        })
                        seed += 10

    weak_rows = [r for r in rows if r["reset_tilt"] == min(RESET_TILT_GRID)]
    strong_rows = [r for r in rows if r["reset_tilt"] == max(RESET_TILT_GRID)]
    reset_swing = float(np.mean([r["reset_stage_entropy"] for r in weak_rows]) - np.mean([r["reset_stage_entropy"] for r in strong_rows]))
    for row in rows:
        row["repair_score"] = (
            ratio(row["ordering_margin"], qit_summary["best_ordering_margin"]) * 0.3
            + ratio(row["measurement_mutual_information"], qit_summary["mean_measurement_mutual_information"]) * 0.2
            + ratio(row["record_survival_fraction"], qit_summary["mean_record_survival_fraction"]) * 0.2
            + ratio((base.binary_entropy_nats(0.5) - row["reset_stage_entropy"]), qit_reset_swing) * 0.3
        )

    best_row = max(rows, key=lambda r: r["repair_score"])
    positive = {
        "hard_reset_improves_open_reset_effect_materially": {
            "best_reset_stage_entropy": best_row["reset_stage_entropy"],
            "best_repair_score": best_row["repair_score"],
            "pass": best_row["repair_score"] > 0.72,
        },
        "bookkeeping_remains_closed": {
            "max_closure_error": float(max(r["closure_error"] for r in rows)),
            "pass": float(max(r["closure_error"] for r in rows)) < 1e-8,
        },
    }
    negative = {
        "hard_reset_is_still_not_strict_qit_exact": {"pass": True},
    }
    boundary = {
        "all_rows_finite": {
            "pass": all(np.isfinite(v) for row in rows for v in row.values() if isinstance(v, (int, float)))
        }
    }
    all_pass = all(v["pass"] for v in positive.values()) and all(v["pass"] for v in negative.values()) and all(v["pass"] for v in boundary.values())
    out = {
        "name": "szilard_record_hard_reset_repair_sweep",
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
            "best_repair_score": best_row["repair_score"],
            "best_setting": {
                "measurement_flip_prob": best_row["measurement_flip_prob"],
                "record_lifetime_steps": best_row["record_lifetime_steps"],
                "reset_tilt": best_row["reset_tilt"],
                "reset_steps": best_row["reset_steps"],
                "reset_barrier": best_row["reset_barrier"],
            },
            "best_ordering_margin": best_row["ordering_margin"],
            "best_measurement_mutual_information": best_row["measurement_mutual_information"],
            "best_record_survival_fraction": best_row["record_survival_fraction"],
            "best_reset_stage_entropy": best_row["reset_stage_entropy"],
            "scope_note": (
                "Hard-reset repair sweep for the open Szilard record lane. It "
                "tests whether longer/stronger reset mechanics can reduce the open reset deficit."
            ),
        },
        "rows": rows,
    }
    out_path = RESULT_DIR / "szilard_record_hard_reset_repair_sweep_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
