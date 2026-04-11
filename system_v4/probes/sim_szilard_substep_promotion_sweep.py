#!/usr/bin/env python3
"""
Szilard Substep Promotion Sweep
==============================
Final promotion-focused search for the Szilard substep lane. It expands the
high-strength low-noise edge and scores directly for controller closeness.
"""

from __future__ import annotations

import json
import pathlib

import numpy as np

import sim_szilard_substep_refinement_sweep as coarse


CLASSIFICATION = "exploratory"
CLASSIFICATION_NOTE = (
    "Promotion-focused search on the strongest low-noise substep region. It "
    "expands high-strength feedback and reset controls and optimizes a "
    "controller-style closeness score."
)

LEGO_IDS = coarse.LEGO_IDS
PRIMARY_LEGO_IDS = coarse.PRIMARY_LEGO_IDS
TOOL_MANIFEST = coarse.TOOL_MANIFEST
TOOL_INTEGRATION_DEPTH = coarse.TOOL_INTEGRATION_DEPTH

MEASUREMENT_FLIP_PROB_GRID = [0.02]
FEEDBACK_STRONG_TILT_GRID = [3.75, 4.0, 4.25]
FEEDBACK_WEAK_RATIO_GRID = [0.45, 0.5, 0.55]
FEEDBACK_STEPS_GRID = [360, 420, 480, 540]
RESET_TILT_GRID = [2.6, 2.8, 3.0]
RESET_STEPS_GRID = [420, 480, 540]
SEED_BASE = 20260411 + 9600

QIT_ORDERING = 0.5350408605722448
QIT_MI = 0.41798538158339976
QIT_ACC = 0.9
QIT_RESET = 0.5136741792484837

RESULT_DIR = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"


def promotion_score(row: dict) -> float:
    ordering = max(0.0, min(1.0, row["ordering_margin"] / QIT_ORDERING))
    mi = max(0.0, min(1.0, row["measurement_mutual_information"] / QIT_MI))
    acc = max(0.0, min(1.0, row["measurement_accuracy"] / QIT_ACC))
    reset = max(0.0, min(1.0, row["reset_signal"] / QIT_RESET))
    return 0.45 * ordering + 0.15 * mi + 0.05 * acc + 0.25 * reset + 0.10 * min(1.0, 0.5 * (ordering + reset))


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
                            row["promotion_score"] = promotion_score(row)
                            rows.append(row)
                            seed += 10

    best_row = max(rows, key=lambda row: row["promotion_score"])
    positive = {
        "promotion_score_exceeds_0_68": {
            "best_promotion_score": best_row["promotion_score"],
            "pass": best_row["promotion_score"] > 0.68,
        },
        "ordering_margin_exceeds_0_21": {
            "best_ordering_margin": best_row["ordering_margin"],
            "pass": best_row["ordering_margin"] > 0.21,
        },
        "reset_signal_exceeds_0_49": {
            "best_reset_signal": best_row["reset_signal"],
            "pass": best_row["reset_signal"] > 0.49,
        },
        "measurement_mutual_information_stays_above_0_43": {
            "best_measurement_mutual_information": best_row["measurement_mutual_information"],
            "pass": best_row["measurement_mutual_information"] > 0.43,
        },
    }
    negative = {
        "not_every_promotion_setting_helps": {
            "worst_promotion_score": float(min(row["promotion_score"] for row in rows)),
            "pass": float(min(row["promotion_score"] for row in rows)) < 0.60,
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
        "name": "szilard_substep_promotion_sweep",
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
            "best_promotion_score": best_row["promotion_score"],
            "best_ordering_margin": best_row["ordering_margin"],
            "best_measurement_mutual_information": best_row["measurement_mutual_information"],
            "best_measurement_accuracy": best_row["measurement_accuracy"],
            "best_reset_signal": best_row["reset_signal"],
            "scope_note": (
                "Promotion-focused search for the stochastic Szilard substep lane. "
                "It expands the strongest low-noise controls and optimizes a "
                "controller-style closeness score."
            ),
        },
        "rows": rows,
    }

    out_path = RESULT_DIR / "szilard_substep_promotion_sweep_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
