#!/usr/bin/env python3
"""
Szilard Substep Ordering Push Sweep
==================================
Target the high-duration, high-reset edge of the balanced substep carrier to
see whether ordering can be pushed further without losing the low-noise gains.
"""

from __future__ import annotations

import json
import pathlib

import numpy as np

import sim_szilard_substep_refinement_sweep as coarse
classification = "classical_baseline"  # auto-backfill


CLASSIFICATION = "exploratory"
CLASSIFICATION_NOTE = (
    "Targeted push on the high-duration, high-reset edge of the balanced "
    "stochastic Szilard substep carrier."
)

LEGO_IDS = coarse.LEGO_IDS
PRIMARY_LEGO_IDS = coarse.PRIMARY_LEGO_IDS
TOOL_MANIFEST = coarse.TOOL_MANIFEST
TOOL_INTEGRATION_DEPTH = coarse.TOOL_INTEGRATION_DEPTH

MEASUREMENT_FLIP_PROB_GRID = [0.02]
FEEDBACK_STRONG_TILT_GRID = [3.25, 3.5, 3.75]
FEEDBACK_WEAK_RATIO_GRID = [0.35, 0.4, 0.45]
FEEDBACK_STEPS_GRID = [360, 420, 480]
RESET_TILT_GRID = [2.4, 2.6, 2.8]
RESET_STEPS_GRID = [300, 360, 420]
SEED_BASE = 20260411 + 9100

QIT_ORDERING = 0.5350408605722448
QIT_MI = 0.41798538158339976
QIT_ACC = 0.9
QIT_RESET = 0.5136741792484837

RESULT_DIR = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"


def push_score(row: dict) -> float:
    return (
        0.55 * max(0.0, min(1.0, row["ordering_margin"] / QIT_ORDERING))
        + 0.15 * max(0.0, min(1.0, row["measurement_mutual_information"] / QIT_MI))
        + 0.05 * max(0.0, min(1.0, row["measurement_accuracy"] / QIT_ACC))
        + 0.25 * max(0.0, min(1.0, row["reset_signal"] / QIT_RESET))
    )


def main() -> None:
    rows = []
    seed = SEED_BASE
    x_init = coarse.base.sample_symmetric_initial_state(
        coarse.base.N_TRAJ, np.random.default_rng(coarse.base.RNG_SEED)
    )
    for measurement_flip_prob in MEASUREMENT_FLIP_PROB_GRID:
        for feedback_strong_tilt in FEEDBACK_STRONG_TILT_GRID:
            for feedback_weak_ratio in FEEDBACK_WEAK_RATIO_GRID:
                for feedback_steps in FEEDBACK_STEPS_GRID:
                    for reset_tilt in RESET_TILT_GRID:
                        for reset_steps in RESET_STEPS_GRID:
                            row = coarse.run_with_settings(
                                x_init,
                                measurement_flip_prob=measurement_flip_prob,
                                feedback_strong_tilt=feedback_strong_tilt,
                                feedback_weak_ratio=feedback_weak_ratio,
                                feedback_steps=feedback_steps,
                                reset_tilt=reset_tilt,
                                reset_steps=reset_steps,
                                seed=seed,
                            )
                            row["push_score"] = push_score(row)
                            rows.append(row)
                            seed += 10

    best_row = max(rows, key=lambda row: row["push_score"])
    positive = {
        "ordering_margin_exceeds_0_17": {
            "best_ordering_margin": best_row["ordering_margin"],
            "pass": best_row["ordering_margin"] > 0.17,
        },
        "reset_signal_exceeds_0_38": {
            "best_reset_signal": best_row["reset_signal"],
            "pass": best_row["reset_signal"] > 0.38,
        },
        "measurement_mutual_information_stays_above_0_41": {
            "best_measurement_mutual_information": best_row["measurement_mutual_information"],
            "pass": best_row["measurement_mutual_information"] > 0.41,
        },
    }
    negative = {
        "not_every_push_setting_helps": {
            "worst_push_score": float(min(row["push_score"] for row in rows)),
            "pass": float(min(row["push_score"] for row in rows)) < 0.55,
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
        "name": "szilard_substep_ordering_push_sweep",
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
                "feedback_strong_tilt": best_row["feedback_strong_tilt"],
                "feedback_weak_ratio": best_row["feedback_weak_ratio"],
                "feedback_steps": best_row["feedback_steps"],
                "reset_tilt": best_row["reset_tilt"],
                "reset_steps": best_row["reset_steps"],
            },
            "best_push_score": best_row["push_score"],
            "best_ordering_margin": best_row["ordering_margin"],
            "best_measurement_mutual_information": best_row["measurement_mutual_information"],
            "best_measurement_accuracy": best_row["measurement_accuracy"],
            "best_reset_signal": best_row["reset_signal"],
            "scope_note": (
                "Targeted push on the strongest balanced substep region. It favors "
                "ordering improvement while preserving low-noise measurement and "
                "strong reset signal."
            ),
        },
        "rows": rows,
    }

    out_path = RESULT_DIR / "szilard_substep_ordering_push_sweep_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
