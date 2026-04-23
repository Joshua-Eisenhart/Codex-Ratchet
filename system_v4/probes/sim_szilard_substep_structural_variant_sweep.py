#!/usr/bin/env python3
"""
Szilard Substep Structural Variant Sweep
=======================================
Probe whether adding an explicit short-lived record-wait stage to the substep
family improves ordering translation beyond the scalar-only push lanes.
"""

from __future__ import annotations

import json
import pathlib

import numpy as np

import sim_szilard_record_ordering_refinement_sweep as record_base
classification = "classical_baseline"  # auto-backfill


CLASSIFICATION = "exploratory"
CLASSIFICATION_NOTE = (
    "Structural substep variant that inserts an explicit record-wait stage "
    "before feedback. This tests whether the remaining substep ordering gap is "
    "structural rather than purely parametric."
)

LEGO_IDS = [
    "stochastic_thermodynamics",
    "measurement_feedback",
    "landauer_erasure",
]

PRIMARY_LEGO_IDS = [
    "stochastic_thermodynamics",
]

TOOL_MANIFEST = record_base.TOOL_MANIFEST
TOOL_INTEGRATION_DEPTH = record_base.TOOL_INTEGRATION_DEPTH

MEASUREMENT_FLIP_PROB_GRID = [0.02]
RECORD_LIFETIME_STEPS = 960
RESET_TILT_GRID = [2.6, 2.8]
RESET_STEPS_GRID = [360, 420]
RESET_BARRIER = 1.55
FEEDBACK_STRONG_TILT_GRID = [3.5, 3.75, 4.0]
FEEDBACK_WEAK_RATIO_GRID = [0.35, 0.45]
RECORD_WAIT_STEPS_GRID = [60, 90, 120]
FEEDBACK_STEPS_GRID = [360, 420, 480]
FEEDBACK_BARRIER_END_GRID = [1.55]
SEED_BASE = 20260411 + 10100

QIT_ORDERING = 0.5350408605722448
QIT_MI = 0.41798538158339976
QIT_RESET = 0.5136741792484837

RESULT_DIR = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"


def structural_score(row: dict) -> float:
    return (
        0.5 * max(0.0, min(1.0, row["ordering_margin"] / QIT_ORDERING))
        + 0.2 * max(0.0, min(1.0, row["measurement_mutual_information"] / QIT_MI))
        + 0.2 * max(0.0, min(1.0, row["reset_signal"] / QIT_RESET))
        + 0.1 * max(0.0, min(1.0, row["record_survival_fraction"]))
    )


def main() -> None:
    rows = []
    seed = SEED_BASE
    x_init = record_base.hard_base.base.sample_symmetric_initial_state(
        record_base.hard_base.base.N_TRAJ,
        np.random.default_rng(record_base.hard_base.base.RNG_SEED if hasattr(record_base.hard_base.base, "RNG_SEED") else 20260410),
    )
    for measurement_flip_prob in MEASUREMENT_FLIP_PROB_GRID:
        for reset_tilt in RESET_TILT_GRID:
            for reset_steps in RESET_STEPS_GRID:
                for feedback_strong_tilt in FEEDBACK_STRONG_TILT_GRID:
                    for feedback_weak_ratio in FEEDBACK_WEAK_RATIO_GRID:
                        for record_wait_steps in RECORD_WAIT_STEPS_GRID:
                            for feedback_steps in FEEDBACK_STEPS_GRID:
                                for feedback_barrier_end in FEEDBACK_BARRIER_END_GRID:
                                    feedback_weak_tilt = feedback_weak_ratio * feedback_strong_tilt
                                    ordered = record_base.run_protocol_with_feedback(
                                        x_init,
                                        ["measurement", "record_wait", "feedback", "reset", "hold"],
                                        measurement_flip_prob=measurement_flip_prob,
                                        record_lifetime_steps=RECORD_LIFETIME_STEPS,
                                        reset_tilt=reset_tilt,
                                        reset_steps=reset_steps,
                                        reset_barrier=RESET_BARRIER,
                                        feedback_strong_tilt=feedback_strong_tilt,
                                        feedback_weak_tilt=feedback_weak_tilt,
                                        record_wait_steps=record_wait_steps,
                                        feedback_steps=feedback_steps,
                                        feedback_barrier_end=feedback_barrier_end,
                                        rng=np.random.default_rng(seed + 1),
                                    )
                                    feedback_first = record_base.run_protocol_with_feedback(
                                        x_init,
                                        ["feedback", "measurement", "record_wait", "reset", "hold"],
                                        measurement_flip_prob=measurement_flip_prob,
                                        record_lifetime_steps=RECORD_LIFETIME_STEPS,
                                        reset_tilt=reset_tilt,
                                        reset_steps=reset_steps,
                                        reset_barrier=RESET_BARRIER,
                                        feedback_strong_tilt=feedback_strong_tilt,
                                        feedback_weak_tilt=feedback_weak_tilt,
                                        record_wait_steps=record_wait_steps,
                                        feedback_steps=feedback_steps,
                                        feedback_barrier_end=feedback_barrier_end,
                                        rng=np.random.default_rng(seed + 2),
                                    )
                                    reset_first = record_base.run_protocol_with_feedback(
                                        x_init,
                                        ["reset", "measurement", "record_wait", "feedback", "hold"],
                                        measurement_flip_prob=measurement_flip_prob,
                                        record_lifetime_steps=RECORD_LIFETIME_STEPS,
                                        reset_tilt=reset_tilt,
                                        reset_steps=reset_steps,
                                        reset_barrier=RESET_BARRIER,
                                        feedback_strong_tilt=feedback_strong_tilt,
                                        feedback_weak_tilt=feedback_weak_tilt,
                                        record_wait_steps=record_wait_steps,
                                        feedback_steps=feedback_steps,
                                        feedback_barrier_end=feedback_barrier_end,
                                        rng=np.random.default_rng(seed + 3),
                                    )
                                    measurement_then_reset_then_feedback = record_base.run_protocol_with_feedback(
                                        x_init,
                                        ["measurement", "reset", "record_wait", "feedback", "hold"],
                                        measurement_flip_prob=measurement_flip_prob,
                                        record_lifetime_steps=RECORD_LIFETIME_STEPS,
                                        reset_tilt=reset_tilt,
                                        reset_steps=reset_steps,
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
                                        measurement_then_reset_then_feedback["final_entropy"],
                                    ) - ordered["final_entropy"]
                                    reset_signal = measurement_then_reset_then_feedback["final_entropy"] - ordered["final_entropy"]
                                    row = {
                                        "measurement_flip_prob": float(measurement_flip_prob),
                                        "reset_tilt": float(reset_tilt),
                                        "reset_steps": int(reset_steps),
                                        "feedback_strong_tilt": float(feedback_strong_tilt),
                                        "feedback_weak_ratio": float(feedback_weak_ratio),
                                        "feedback_steps": int(feedback_steps),
                                        "record_wait_steps": int(record_wait_steps),
                                        "ordering_margin": float(ordering_margin),
                                        "measurement_mutual_information": float(ordered["measurement_mutual_information"]),
                                        "record_survival_fraction": float(ordered["record_survival_fraction"]),
                                        "reset_signal": float(reset_signal),
                                        "reset_stage_entropy": float(ordered["reset_stage_entropy"]),
                                        "closure_error": float(
                                            max(
                                                ordered["closure_error"],
                                                feedback_first["closure_error"],
                                                reset_first["closure_error"],
                                                measurement_then_reset_then_feedback["closure_error"],
                                            )
                                        ),
                                    }
                                    row["structural_score"] = structural_score(row)
                                    rows.append(row)
                                    seed += 10

    best_row = max(rows, key=lambda row: row["structural_score"])
    positive = {
        "ordering_margin_exceeds_current_push_lane": {
            "best_ordering_margin": best_row["ordering_margin"],
            "pass": best_row["ordering_margin"] > 0.189932047460173,
        },
        "reset_signal_stays_high": {
            "best_reset_signal": best_row["reset_signal"],
            "pass": best_row["reset_signal"] > 0.40,
        },
        "measurement_information_stays_high": {
            "best_measurement_mutual_information": best_row["measurement_mutual_information"],
            "pass": best_row["measurement_mutual_information"] > 0.42,
        },
    }
    negative = {
        "not_every_structural_setting_helps": {
            "worst_structural_score": float(min(row["structural_score"] for row in rows)),
            "pass": float(min(row["structural_score"] for row in rows)) < 0.55,
        },
    }
    boundary = {
        "bookkeeping_stays_closed": {
            "max_closure_error": float(max(row["closure_error"] for row in rows)),
            "pass": float(max(row["closure_error"] for row in rows)) < 1e-8,
        }
    }
    all_pass = all(v["pass"] for v in positive.values()) and all(v["pass"] for v in negative.values()) and all(v["pass"] for v in boundary.values())

    out = {
        "name": "szilard_substep_structural_variant_sweep",
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
                "measurement_flip_prob": best_row["measurement_flip_prob"],
                "reset_tilt": best_row["reset_tilt"],
                "reset_steps": best_row["reset_steps"],
                "feedback_strong_tilt": best_row["feedback_strong_tilt"],
                "feedback_weak_ratio": best_row["feedback_weak_ratio"],
                "feedback_steps": best_row["feedback_steps"],
                "record_wait_steps": best_row["record_wait_steps"],
            },
            "best_structural_score": best_row["structural_score"],
            "best_ordering_margin": best_row["ordering_margin"],
            "best_measurement_mutual_information": best_row["measurement_mutual_information"],
            "best_record_survival_fraction": best_row["record_survival_fraction"],
            "best_reset_signal": best_row["reset_signal"],
            "best_reset_stage_entropy": best_row["reset_stage_entropy"],
            "scope_note": (
                "Structural substep variant with explicit record-wait before feedback. "
                "It tests whether substep ordering can improve beyond the scalar-only push lane."
            ),
        },
        "rows": rows,
    }

    out_path = RESULT_DIR / "szilard_substep_structural_variant_sweep_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
