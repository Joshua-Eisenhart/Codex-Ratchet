#!/usr/bin/env python3
"""
Szilard Ordering Sensitivity Sweep
==================================
Inductive sweep over measurement noise and feedback strength for the explicit
Szilard measurement/feedback/reset substep probe.

The goal is to find where the correct order separates materially from the main
scrambled alternatives.
"""

from __future__ import annotations

import json
import pathlib

import numpy as np

import sim_stoch_doublewell_landauer_erasure as base


CLASSIFICATION = "exploratory"
CLASSIFICATION_NOTE = (
    "Ordering-sensitivity sweep over the explicit Szilard substep lane. "
    "It tracks when the correct measurement -> feedback -> reset order "
    "separates from scrambled alternatives as measurement noise and feedback "
    "strength vary."
)

LEGO_IDS = [
    "stochastic_thermodynamics",
    "landauer_erasure",
    "measurement_feedback",
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

MEASUREMENT_FLIP_GRID = [0.02, 0.08, 0.16, 0.30]
FEEDBACK_STRONG_TILT_GRID = [1.35, 1.85, 2.35]
FEEDBACK_WEAK_SCALE = 0.135
SEED_BASE = 20260410 + 1400


def run_setting(measurement_flip_prob: float, feedback_strong_tilt: float, seed: int) -> dict:
    base.MEASUREMENT_FLIP_PROB = measurement_flip_prob
    base.FEEDBACK_STRONG_TILT = feedback_strong_tilt
    base.FEEDBACK_WEAK_TILT = FEEDBACK_WEAK_SCALE * feedback_strong_tilt

    rng = np.random.default_rng(seed)
    x0 = base.sample_symmetric_initial_state(base.N_TRAJ, rng)

    ordered = base.simulate_ordered_protocol(x0, ["measurement", "feedback", "reset", "hold"], rng)
    feedback_first = base.simulate_ordered_protocol(x0, ["feedback", "measurement", "reset", "hold"], rng)
    reset_first = base.simulate_ordered_protocol(x0, ["reset", "measurement", "feedback", "hold"], rng)
    measurement_reset_feedback = base.simulate_ordered_protocol(x0, ["measurement", "reset", "feedback", "hold"], rng)

    scrambled = {
        "feedback_first": feedback_first["final_entropy"],
        "reset_first": reset_first["final_entropy"],
        "measurement_reset_feedback": measurement_reset_feedback["final_entropy"],
    }
    best_scrambled_name = min(scrambled, key=scrambled.get)
    best_scrambled_entropy = scrambled[best_scrambled_name]

    return {
        "measurement_flip_prob": float(measurement_flip_prob),
        "feedback_strong_tilt": float(feedback_strong_tilt),
        "feedback_weak_tilt": float(base.FEEDBACK_WEAK_TILT),
        "ordered_final_entropy": float(ordered["final_entropy"]),
        "ordered_final_left_fraction": float(ordered["final_left_fraction"]),
        "ordered_measurement_accuracy": float(ordered["measurement_accuracy"]),
        "ordered_measurement_mi": float(ordered["measurement_mutual_information"]),
        "feedback_first_final_entropy": float(feedback_first["final_entropy"]),
        "reset_first_final_entropy": float(reset_first["final_entropy"]),
        "measurement_reset_feedback_final_entropy": float(measurement_reset_feedback["final_entropy"]),
        "best_scrambled_name": best_scrambled_name,
        "best_scrambled_entropy": float(best_scrambled_entropy),
        "ordering_margin": float(best_scrambled_entropy - ordered["final_entropy"]),
        "ordered_beats_all_scrambled": bool(ordered["final_entropy"] < min(scrambled.values())),
        "closure_error_max": float(max(
            ordered["closure_error"],
            feedback_first["closure_error"],
            reset_first["closure_error"],
            measurement_reset_feedback["closure_error"],
        )),
    }


def main() -> None:
    rows = []
    seed = SEED_BASE
    for measurement_flip_prob in MEASUREMENT_FLIP_GRID:
        for feedback_strong_tilt in FEEDBACK_STRONG_TILT_GRID:
            rows.append(run_setting(measurement_flip_prob, feedback_strong_tilt, seed))
            seed += 1

    best_margin_row = max(rows, key=lambda row: row["ordering_margin"])
    low_noise_rows = [row for row in rows if row["measurement_flip_prob"] == min(MEASUREMENT_FLIP_GRID)]
    high_noise_rows = [row for row in rows if row["measurement_flip_prob"] == max(MEASUREMENT_FLIP_GRID)]
    strong_feedback_rows = [row for row in rows if row["feedback_strong_tilt"] == max(FEEDBACK_STRONG_TILT_GRID)]
    weak_feedback_rows = [row for row in rows if row["feedback_strong_tilt"] == min(FEEDBACK_STRONG_TILT_GRID)]

    positive = {
        "some_settings_make_the_correct_order_materially_better_than_scrambled_orders": {
            "best_margin": best_margin_row["ordering_margin"],
            "best_setting": {
                "measurement_flip_prob": best_margin_row["measurement_flip_prob"],
                "feedback_strong_tilt": best_margin_row["feedback_strong_tilt"],
            },
            "pass": best_margin_row["ordering_margin"] > 0.01,
        },
        "lower_measurement_noise_improves_ordering_margin_on_average": {
            "low_noise_mean_margin": float(np.mean([row["ordering_margin"] for row in low_noise_rows])),
            "high_noise_mean_margin": float(np.mean([row["ordering_margin"] for row in high_noise_rows])),
            "pass": float(np.mean([row["ordering_margin"] for row in low_noise_rows])) > float(np.mean([row["ordering_margin"] for row in high_noise_rows])),
        },
        "stronger_feedback_improves_ordering_margin_on_average": {
            "strong_feedback_mean_margin": float(np.mean([row["ordering_margin"] for row in strong_feedback_rows])),
            "weak_feedback_mean_margin": float(np.mean([row["ordering_margin"] for row in weak_feedback_rows])),
            "pass": float(np.mean([row["ordering_margin"] for row in strong_feedback_rows])) > float(np.mean([row["ordering_margin"] for row in weak_feedback_rows])),
        },
    }

    negative = {
        "high_noise_settings_do_not_give_clean_ordering_separation": {
            "high_noise_best_margin": float(max(row["ordering_margin"] for row in high_noise_rows)),
            "pass": float(max(row["ordering_margin"] for row in high_noise_rows)) < 0.01,
        },
        "not_every_setting_yields_ordered_beats_all_scrambled": {
            "success_count": int(sum(row["ordered_beats_all_scrambled"] for row in rows)),
            "total_settings": int(len(rows)),
            "pass": not all(row["ordered_beats_all_scrambled"] for row in rows),
        },
    }

    boundary = {
        "all_rows_have_closed_bookkeeping": {
            "max_closure_error": float(max(row["closure_error_max"] for row in rows)),
            "pass": float(max(row["closure_error_max"] for row in rows)) < 1e-8,
        },
        "all_rows_have_finite_statistics": {
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
        "name": "szilard_ordering_sensitivity_sweep",
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
            "feedback_strong_tilt_grid": FEEDBACK_STRONG_TILT_GRID,
            "best_margin": best_margin_row["ordering_margin"],
            "best_setting": {
                "measurement_flip_prob": best_margin_row["measurement_flip_prob"],
                "feedback_strong_tilt": best_margin_row["feedback_strong_tilt"],
            },
            "scope_note": (
                "Ordering-sensitivity sweep over the explicit Szilard substep lane. "
                "It is a parameter map for ordering separation, not a canonical engine result."
            ),
        },
        "rows": rows,
    }

    out_dir = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "szilard_ordering_sensitivity_sweep_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
