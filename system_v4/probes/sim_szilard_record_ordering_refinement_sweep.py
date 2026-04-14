#!/usr/bin/env python3
"""
Szilard Record Ordering Refinement Sweep
=======================================
Refine the best ordering-amplified hard-reset carrier around its strongest
setting, adding feedback duration and feedback barrier depth as explicit axes.
"""

from __future__ import annotations

import json
import pathlib

import numpy as np

import sim_szilard_record_hard_reset_repair_sweep as hard_base
classification = "classical_baseline"  # auto-backfill


CLASSIFICATION = "exploratory"
CLASSIFICATION_NOTE = (
    "Second-order ordering refinement sweep on top of the hard-reset Szilard "
    "record carrier. It narrows the search around the best ordering-amplified "
    "setting and adds feedback duration and barrier depth as explicit axes."
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

MEASUREMENT_FLIP_PROB = 0.02
RECORD_LIFETIME_STEPS = 960
RESET_TILT = 3.25
RESET_STEPS = 480
RESET_BARRIER = 1.55

FEEDBACK_STRONG_TILT_GRID = [3.0, 3.25, 3.5]
FEEDBACK_WEAK_RATIO_GRID = [0.2, 0.25, 0.3, 0.35]
RECORD_WAIT_STEPS_GRID = [60, 90, 120, 150]
FEEDBACK_STEPS_GRID = [180, 240, 300, 360]
FEEDBACK_BARRIER_END_GRID = [1.25, 1.55, 1.85]
SEED_BASE = 20260411 + 6100

RESULT_DIR = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"


def run_protocol_with_feedback(
    x0: np.ndarray,
    order: list[str],
    *,
    measurement_flip_prob: float,
    record_lifetime_steps: int,
    reset_tilt: float,
    reset_steps: int,
    reset_barrier: float,
    feedback_strong_tilt: float,
    feedback_weak_tilt: float,
    record_wait_steps: int,
    feedback_steps: int,
    feedback_barrier_end: float,
    rng: np.random.Generator,
) -> dict:
    original_wait = hard_base.base.RECORD_WAIT_STEPS
    original_feedback_steps = hard_base.base.FEEDBACK_STEPS
    try:
        hard_base.base.RECORD_WAIT_STEPS = record_wait_steps
        hard_base.base.FEEDBACK_STEPS = feedback_steps
        library = hard_base.build_stage_library(reset_tilt, measurement_flip_prob, reset_steps, reset_barrier)
        library["feedback"] = hard_base.base.base.StageSpec(
            name="feedback_drive",
            kind="feedback",
            steps=feedback_steps,
            temperature=hard_base.base.TEMPERATURE,
            barrier_start=0.10,
            barrier_end=feedback_barrier_end,
            tilt_start=0.0,
            tilt_end=0.0,
            feedback_strong_tilt=feedback_strong_tilt,
            feedback_weak_tilt=feedback_weak_tilt,
        )
        library["record_wait"] = hard_base.base.base.StageSpec(
            name="record_wait_window",
            kind="record_wait",
            steps=record_wait_steps,
            temperature=hard_base.base.TEMPERATURE,
            barrier_start=feedback_barrier_end,
            barrier_end=feedback_barrier_end,
            tilt_start=0.0,
            tilt_end=0.0,
        )

        x = np.asarray(x0, dtype=float).copy()
        n = x.shape[0]
        total_work = np.zeros(n, dtype=float)
        total_heat = np.zeros(n, dtype=float)
        total_delta_u = np.zeros(n, dtype=float)
        measured_bits = None
        measurement_record = None
        record_history = []
        reset_stage_entropy = None
        initial_bits = (x >= hard_base.base.LEFT_STATE_THRESHOLD).astype(int)

        for stage_name in order:
            stage = library[stage_name]
            if stage.kind == "measurement":
                x_before = x.copy()
                x, stage_work, stage_heat, stage_delta_u, _ = hard_base.base.base.stage_simulation(
                    x, stage.barrier_start, stage.barrier_end, stage.tilt_start, stage.tilt_end, stage.steps, stage.temperature, rng
                )
                true_bits = (x_before >= hard_base.base.LEFT_STATE_THRESHOLD).astype(int)
                sensed_bits = hard_base.base.binary_readout(x, stage.measurement_flip_prob, rng)
                measured_bits = sensed_bits
                measurement_record = sensed_bits.copy()
            elif stage.kind == "record_wait":
                x, stage_work, stage_heat, stage_delta_u, _ = hard_base.base.base.stage_simulation(
                    x, stage.barrier_start, stage.barrier_end, stage.tilt_start, stage.tilt_end, stage.steps, stage.temperature, rng
                )
                if measurement_record is not None:
                    prior_record = measurement_record.copy()
                    decay_prob = 1.0 - float(
                        np.exp(-float(stage.steps) / max(float(record_lifetime_steps), hard_base.base.MEASUREMENT_RECORD_DECAY_FLOOR))
                    )
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
                    x_r, w_r, h_r, du_r, _ = hard_base.base.base.stage_simulation(
                        x[right_mask], stage.barrier_start, stage.barrier_end, 0.0, right_tilt, stage.steps, stage.temperature, rng
                    )
                    x_out[right_mask] = x_r
                    stage_work[right_mask] = w_r
                    stage_heat[right_mask] = h_r
                    stage_delta_u[right_mask] = du_r
                if np.any(left_mask):
                    x_l, w_l, h_l, du_l, _ = hard_base.base.base.stage_simulation(
                        x[left_mask], stage.barrier_start, stage.barrier_end, 0.0, left_tilt, stage.steps, stage.temperature, rng
                    )
                    x_out[left_mask] = x_l
                    stage_work[left_mask] = w_l
                    stage_heat[left_mask] = h_l
                    stage_delta_u[left_mask] = du_l
                x = x_out
            elif stage.kind == "reset":
                x, stage_work, stage_heat, stage_delta_u, _ = hard_base.base.base.stage_simulation(
                    x, stage.barrier_start, stage.barrier_end, stage.tilt_start, stage.tilt_end, stage.steps, stage.temperature, rng
                )
                measurement_record = None
                reset_stage_entropy = hard_base.stage_entropy(x)
            elif stage.kind == "hold":
                x, stage_work, stage_heat, stage_delta_u, _ = hard_base.base.base.stage_simulation(
                    x, stage.barrier_start, stage.barrier_end, stage.tilt_start, stage.tilt_end, stage.steps, stage.temperature, rng
                )
            else:
                raise ValueError(stage.kind)

            total_work += stage_work
            total_heat += stage_heat
            total_delta_u += stage_delta_u

        final_bits = (x < hard_base.base.LEFT_STATE_THRESHOLD).astype(int)
        final_entropy = hard_base.base.binary_entropy_nats(float(np.mean(final_bits == 1)))
        measured_mi = (
            hard_base.base.confusion_metrics(initial_bits, measured_bits)["mutual_information"]
            if measured_bits is not None
            else 0.0
        )
        record_survival = float(np.mean([item["survival_fraction"] for item in record_history])) if record_history else 0.0
        return {
            "final_entropy": float(final_entropy),
            "measurement_mutual_information": float(measured_mi),
            "record_survival_fraction": float(record_survival),
            "reset_stage_entropy": float(reset_stage_entropy) if reset_stage_entropy is not None else 0.0,
            "mean_work": float(np.mean(total_work)),
            "closure_error": float(abs(np.mean(total_delta_u) - np.mean(total_work) - np.mean(total_heat))),
        }
    finally:
        hard_base.base.RECORD_WAIT_STEPS = original_wait
        hard_base.base.FEEDBACK_STEPS = original_feedback_steps


def main() -> None:
    rows = []
    seed = SEED_BASE
    for feedback_strong_tilt in FEEDBACK_STRONG_TILT_GRID:
        for weak_ratio in FEEDBACK_WEAK_RATIO_GRID:
            for record_wait_steps in RECORD_WAIT_STEPS_GRID:
                for feedback_steps in FEEDBACK_STEPS_GRID:
                    for feedback_barrier_end in FEEDBACK_BARRIER_END_GRID:
                        feedback_weak_tilt = weak_ratio * feedback_strong_tilt
                        rng = np.random.default_rng(seed)
                        x_init = hard_base.base.sample_symmetric_initial_state(hard_base.base.N_TRAJ, rng)
                        ordered = run_protocol_with_feedback(
                            x_init,
                            ["measurement", "record_wait", "feedback", "reset", "hold"],
                            measurement_flip_prob=MEASUREMENT_FLIP_PROB,
                            record_lifetime_steps=RECORD_LIFETIME_STEPS,
                            reset_tilt=RESET_TILT,
                            reset_steps=RESET_STEPS,
                            reset_barrier=RESET_BARRIER,
                            feedback_strong_tilt=feedback_strong_tilt,
                            feedback_weak_tilt=feedback_weak_tilt,
                            record_wait_steps=record_wait_steps,
                            feedback_steps=feedback_steps,
                            feedback_barrier_end=feedback_barrier_end,
                            rng=np.random.default_rng(seed + 1),
                        )
                        feedback_first = run_protocol_with_feedback(
                            x_init,
                            ["feedback", "measurement", "record_wait", "reset", "hold"],
                            measurement_flip_prob=MEASUREMENT_FLIP_PROB,
                            record_lifetime_steps=RECORD_LIFETIME_STEPS,
                            reset_tilt=RESET_TILT,
                            reset_steps=RESET_STEPS,
                            reset_barrier=RESET_BARRIER,
                            feedback_strong_tilt=feedback_strong_tilt,
                            feedback_weak_tilt=feedback_weak_tilt,
                            record_wait_steps=record_wait_steps,
                            feedback_steps=feedback_steps,
                            feedback_barrier_end=feedback_barrier_end,
                            rng=np.random.default_rng(seed + 2),
                        )
                        reset_first = run_protocol_with_feedback(
                            x_init,
                            ["reset", "measurement", "record_wait", "feedback", "hold"],
                            measurement_flip_prob=MEASUREMENT_FLIP_PROB,
                            record_lifetime_steps=RECORD_LIFETIME_STEPS,
                            reset_tilt=RESET_TILT,
                            reset_steps=RESET_STEPS,
                            reset_barrier=RESET_BARRIER,
                            feedback_strong_tilt=feedback_strong_tilt,
                            feedback_weak_tilt=feedback_weak_tilt,
                            record_wait_steps=record_wait_steps,
                            feedback_steps=feedback_steps,
                            feedback_barrier_end=feedback_barrier_end,
                            rng=np.random.default_rng(seed + 3),
                        )
                        mrf = run_protocol_with_feedback(
                            x_init,
                            ["measurement", "reset", "record_wait", "feedback", "hold"],
                            measurement_flip_prob=MEASUREMENT_FLIP_PROB,
                            record_lifetime_steps=RECORD_LIFETIME_STEPS,
                            reset_tilt=RESET_TILT,
                            reset_steps=RESET_STEPS,
                            reset_barrier=RESET_BARRIER,
                            feedback_strong_tilt=feedback_strong_tilt,
                            feedback_weak_tilt=feedback_weak_tilt,
                            record_wait_steps=record_wait_steps,
                            feedback_steps=feedback_steps,
                            feedback_barrier_end=feedback_barrier_end,
                            rng=np.random.default_rng(seed + 4),
                        )
                        ordering_margin = min(
                            feedback_first["final_entropy"],
                            reset_first["final_entropy"],
                            mrf["final_entropy"],
                        ) - ordered["final_entropy"]
                        rows.append(
                            {
                                "feedback_strong_tilt": float(feedback_strong_tilt),
                                "feedback_weak_ratio": float(weak_ratio),
                                "feedback_weak_tilt": float(feedback_weak_tilt),
                                "record_wait_steps": int(record_wait_steps),
                                "feedback_steps": int(feedback_steps),
                                "feedback_barrier_end": float(feedback_barrier_end),
                                "ordering_margin": float(ordering_margin),
                                "measurement_mutual_information": float(ordered["measurement_mutual_information"]),
                                "record_survival_fraction": float(ordered["record_survival_fraction"]),
                                "reset_stage_entropy": float(ordered["reset_stage_entropy"]),
                                "closure_error": float(
                                    max(
                                        ordered["closure_error"],
                                        feedback_first["closure_error"],
                                        reset_first["closure_error"],
                                        mrf["closure_error"],
                                    )
                                ),
                            }
                        )
                        seed += 10

    best_row = max(rows, key=lambda r: r["ordering_margin"])
    positive = {
        "best_refined_setting_pushes_ordering_above_0_10": {
            "best_ordering_margin": best_row["ordering_margin"],
            "pass": best_row["ordering_margin"] > 0.10,
        },
        "measurement_information_stays_high": {
            "best_measurement_mutual_information": best_row["measurement_mutual_information"],
            "pass": best_row["measurement_mutual_information"] > 0.42,
        },
        "record_survival_stays_high": {
            "best_record_survival_fraction": best_row["record_survival_fraction"],
            "pass": best_row["record_survival_fraction"] > 0.85,
        },
    }
    negative = {
        "not_every_local_refinement_setting_helps": {
            "worst_ordering_margin": float(min(r["ordering_margin"] for r in rows)),
            "pass": float(min(r["ordering_margin"] for r in rows)) < 0.04,
        },
    }
    boundary = {
        "bookkeeping_stays_closed": {
            "max_closure_error": float(max(r["closure_error"] for r in rows)),
            "pass": float(max(r["closure_error"] for r in rows)) < 1e-8,
        }
    }
    all_pass = all(v["pass"] for v in positive.values()) and all(v["pass"] for v in negative.values()) and all(v["pass"] for v in boundary.values())
    out = {
        "name": "szilard_record_ordering_refinement_sweep",
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
            "best_setting": {
                "feedback_strong_tilt": best_row["feedback_strong_tilt"],
                "feedback_weak_ratio": best_row["feedback_weak_ratio"],
                "record_wait_steps": best_row["record_wait_steps"],
                "feedback_steps": best_row["feedback_steps"],
                "feedback_barrier_end": best_row["feedback_barrier_end"],
            },
            "best_ordering_margin": best_row["ordering_margin"],
            "best_measurement_mutual_information": best_row["measurement_mutual_information"],
            "best_record_survival_fraction": best_row["record_survival_fraction"],
            "best_reset_stage_entropy": best_row["reset_stage_entropy"],
            "scope_note": (
                "Local refinement sweep around the best ordering-amplified hard-reset Szilard carrier. "
                "It adds feedback duration and barrier depth to test whether ordering can be pushed "
                "past the remaining gap without losing measurement or survival quality."
            ),
        },
        "rows": rows,
    }

    out_path = RESULT_DIR / "szilard_record_ordering_refinement_sweep_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
