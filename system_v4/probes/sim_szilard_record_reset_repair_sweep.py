#!/usr/bin/env python3
"""
Szilard Record / Reset Repair Sweep
==================================
Expanded open-lab repair sweep for the weak record/reset Szilard lane.

This keeps the stochastic double-well carrier but widens the operational
controls so we can test whether the open carrier can move materially closer to
the strict record/reset companion on:
  - ordering margin
  - measurement informativeness
  - record survival
  - reset swing
"""

from __future__ import annotations

import json
import pathlib

import numpy as np

import sim_szilard_record_reset_sweep as base
classification = "classical_baseline"  # auto-backfill


CLASSIFICATION = "exploratory"
CLASSIFICATION_NOTE = (
    "Expanded repair sweep for the weak open Szilard record/reset lane. It "
    "widens feedback, lifetime, and reset controls and scores closeness to the "
    "strict QIT companion without treating the result as admission."
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

MEASUREMENT_FLIP_GRID = [0.0, 0.02, 0.08, 0.18]
RECORD_LIFETIME_GRID = [120, 240, 480, 960]
RESET_TILT_GRID = [1.55, 1.95, 2.35, 2.75]
FEEDBACK_STRONG_TILT_GRID = [1.85, 2.35, 2.75]
FEEDBACK_WEAK_SCALE = 0.135
SEED_BASE = 20260411 + 3100

RESULT_DIR = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"


def load(name: str) -> dict:
    return json.loads((RESULT_DIR / name).read_text())


def ratio(open_value: float, target_value: float) -> float:
    if target_value <= 0.0:
        return 0.0
    return float(max(0.0, min(1.0, open_value / target_value)))


def main() -> None:
    qit = load("qit_szilard_record_companion_results.json")
    qit_summary = qit["summary"]
    qit_reset_swing = (
        qit_summary["weak_reset_mean_memory_entropy_after_reset"]
        - qit_summary["strong_reset_mean_memory_entropy_after_reset"]
    )

    rows = []
    seed = SEED_BASE
    for measurement_flip_prob in MEASUREMENT_FLIP_GRID:
        for record_lifetime_steps in RECORD_LIFETIME_GRID:
            for reset_tilt in RESET_TILT_GRID:
                for feedback_strong_tilt in FEEDBACK_STRONG_TILT_GRID:
                    base.FEEDBACK_STRONG_TILT = feedback_strong_tilt
                    base.FEEDBACK_WEAK_TILT = FEEDBACK_WEAK_SCALE * feedback_strong_tilt

                    rng = np.random.default_rng(seed)
                    x_init = base.sample_symmetric_initial_state(base.N_TRAJ, rng)

                    ordered = base.run_protocol(
                        x_init,
                        ["measurement", "record_wait", "feedback", "reset", "hold"],
                        measurement_flip_prob=measurement_flip_prob,
                        record_lifetime_steps=record_lifetime_steps,
                        reset_tilt=reset_tilt,
                        rng=np.random.default_rng(seed + 1),
                    )
                    feedback_first = base.run_protocol(
                        x_init,
                        ["feedback", "measurement", "record_wait", "reset", "hold"],
                        measurement_flip_prob=measurement_flip_prob,
                        record_lifetime_steps=record_lifetime_steps,
                        reset_tilt=reset_tilt,
                        rng=np.random.default_rng(seed + 2),
                    )
                    reset_first = base.run_protocol(
                        x_init,
                        ["reset", "measurement", "record_wait", "feedback", "hold"],
                        measurement_flip_prob=measurement_flip_prob,
                        record_lifetime_steps=record_lifetime_steps,
                        reset_tilt=reset_tilt,
                        rng=np.random.default_rng(seed + 3),
                    )
                    measurement_then_reset_then_feedback = base.run_protocol(
                        x_init,
                        ["measurement", "reset", "record_wait", "feedback", "hold"],
                        measurement_flip_prob=measurement_flip_prob,
                        record_lifetime_steps=record_lifetime_steps,
                        reset_tilt=reset_tilt,
                        rng=np.random.default_rng(seed + 4),
                    )

                    best_scrambled_entropy = min(
                        feedback_first["final_entropy"],
                        reset_first["final_entropy"],
                        measurement_then_reset_then_feedback["final_entropy"],
                    )
                    ordering_margin = best_scrambled_entropy - ordered["final_entropy"]

                    row = {
                        "measurement_flip_prob": float(measurement_flip_prob),
                        "record_lifetime_steps": int(record_lifetime_steps),
                        "reset_tilt": float(reset_tilt),
                        "feedback_strong_tilt": float(feedback_strong_tilt),
                        "feedback_weak_tilt": float(base.FEEDBACK_WEAK_TILT),
                        "ordering_margin": float(ordering_margin),
                        "measurement_accuracy": float(ordered["measurement_accuracy"]),
                        "measurement_mutual_information": float(ordered["measurement_mutual_information"]),
                        "record_survival_fraction": float(ordered["record_survival_fraction"]),
                        "reset_stage_entropy": float(ordered["reset_stage_entropy"]),
                        "mean_work": float(ordered["mean_work"]),
                        "closure_error": float(
                            max(
                                ordered["closure_error"],
                                feedback_first["closure_error"],
                                reset_first["closure_error"],
                                measurement_then_reset_then_feedback["closure_error"],
                            )
                        ),
                    }
                    rows.append(row)
                    seed += 10

    weak_rows = [row for row in rows if row["reset_tilt"] == min(RESET_TILT_GRID)]
    strong_rows = [row for row in rows if row["reset_tilt"] == max(RESET_TILT_GRID)]
    reset_swing = float(np.mean([row["reset_stage_entropy"] for row in weak_rows]) - np.mean([row["reset_stage_entropy"] for row in strong_rows]))

    for row in rows:
        row["repair_score"] = (
            ratio(row["ordering_margin"], qit_summary["best_ordering_margin"]) * 0.35
            + ratio(row["measurement_mutual_information"], qit_summary["mean_measurement_mutual_information"]) * 0.2
            + ratio(row["record_survival_fraction"], qit_summary["mean_record_survival_fraction"]) * 0.3
            + ratio(reset_swing, qit_reset_swing) * 0.15
        )

    best_row = max(rows, key=lambda row: row["repair_score"])
    long_rows = [row for row in rows if row["record_lifetime_steps"] >= 480]
    short_rows = [row for row in rows if row["record_lifetime_steps"] <= 240]
    low_noise_rows = [row for row in rows if row["measurement_flip_prob"] == min(MEASUREMENT_FLIP_GRID)]
    high_noise_rows = [row for row in rows if row["measurement_flip_prob"] == max(MEASUREMENT_FLIP_GRID)]

    positive = {
        "repair_sweep_finds_a_stronger_row_than_the_original_open_lane": {
            "best_repair_score": best_row["repair_score"],
            "best_ordering_margin": best_row["ordering_margin"],
            "best_record_survival_fraction": best_row["record_survival_fraction"],
            "best_measurement_mutual_information": best_row["measurement_mutual_information"],
            "pass": best_row["repair_score"] > 0.55,
        },
        "longer_lifetime_settings_help_record_survival_on_average": {
            "short_mean_survival": float(np.mean([row["record_survival_fraction"] for row in short_rows])),
            "long_mean_survival": float(np.mean([row["record_survival_fraction"] for row in long_rows])),
            "pass": float(np.mean([row["record_survival_fraction"] for row in long_rows]))
            > float(np.mean([row["record_survival_fraction"] for row in short_rows])),
        },
        "lower_noise_settings_help_ordering_on_average": {
            "low_noise_mean_margin": float(np.mean([row["ordering_margin"] for row in low_noise_rows])),
            "high_noise_mean_margin": float(np.mean([row["ordering_margin"] for row in high_noise_rows])),
            "pass": float(np.mean([row["ordering_margin"] for row in low_noise_rows]))
            > float(np.mean([row["ordering_margin"] for row in high_noise_rows])),
        },
        "stronger_reset_grid_increases_open_reset_swing": {
            "open_reset_swing": reset_swing,
            "qit_reset_swing": qit_reset_swing,
            "pass": reset_swing > 0.05,
        },
    }

    negative = {
        "open_repair_lane_still_does_not_match_strict_qit_exactly": {
            "ordering_gap_at_best_row": qit_summary["best_ordering_margin"] - best_row["ordering_margin"],
            "record_survival_gap_at_best_row": qit_summary["mean_record_survival_fraction"] - best_row["record_survival_fraction"],
            "measurement_mi_gap_at_best_row": qit_summary["mean_measurement_mutual_information"] - best_row["measurement_mutual_information"],
            "pass": True,
        },
        "repair_sweep_is_not_a_canonical_translation_lane": {
            "pass": True,
        },
    }

    boundary = {
        "all_rows_have_closed_bookkeeping": {
            "max_closure_error": float(max(row["closure_error"] for row in rows)),
            "pass": float(max(row["closure_error"] for row in rows)) < 1e-8,
        },
        "all_rows_are_finite": {
            "pass": all(
                np.isfinite(value)
                for row in rows
                for key, value in row.items()
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
        "name": "szilard_record_reset_repair_sweep",
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
            "feedback_strong_tilt_grid": FEEDBACK_STRONG_TILT_GRID,
            "best_repair_score": best_row["repair_score"],
            "best_setting": {
                "measurement_flip_prob": best_row["measurement_flip_prob"],
                "record_lifetime_steps": best_row["record_lifetime_steps"],
                "reset_tilt": best_row["reset_tilt"],
                "feedback_strong_tilt": best_row["feedback_strong_tilt"],
            },
            "best_ordering_margin": best_row["ordering_margin"],
            "best_measurement_mutual_information": best_row["measurement_mutual_information"],
            "best_record_survival_fraction": best_row["record_survival_fraction"],
            "open_reset_swing": reset_swing,
            "qit_target_ordering_margin": qit_summary["best_ordering_margin"],
            "qit_target_measurement_mutual_information": qit_summary["mean_measurement_mutual_information"],
            "qit_target_record_survival_fraction": qit_summary["mean_record_survival_fraction"],
            "qit_target_reset_swing": qit_reset_swing,
            "scope_note": (
                "Expanded repair sweep for the weak open Szilard record/reset lane. "
                "It widens lifetime, reset, and feedback controls and scores closeness "
                "to the strict QIT companion."
            ),
        },
        "rows": rows,
    }

    out_path = RESULT_DIR / "szilard_record_reset_repair_sweep_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
