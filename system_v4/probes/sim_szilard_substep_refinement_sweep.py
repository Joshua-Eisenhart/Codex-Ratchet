#!/usr/bin/env python3
"""
Szilard Substep Refinement Sweep
================================
Refine the weak open Szilard substep carrier by varying feedback and reset
mechanics while preserving the same ordered-vs-scrambled protocol family.
"""

from __future__ import annotations

import json
import pathlib

import numpy as np

import sim_stoch_doublewell_landauer_erasure as base


CLASSIFICATION = "exploratory"
CLASSIFICATION_NOTE = (
    "Refinement sweep over the weak open Szilard substep carrier. It varies "
    "feedback strength, weak-branch ratio, feedback duration, reset tilt, and "
    "reset duration while preserving the same ordered and scrambled control "
    "protocol family used by the base substep row."
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

MEASUREMENT_FLIP_PROB_GRID = [0.02, 0.08]
FEEDBACK_STRONG_TILT_GRID = [2.35, 2.75, 3.25]
FEEDBACK_WEAK_RATIO_GRID = [0.1, 0.2, 0.3]
FEEDBACK_STEPS_GRID = [120, 180, 240]
RESET_TILT_GRID = [1.4, 1.8, 2.2]
RESET_STEPS_GRID = [120, 180, 240]
SEED_BASE = 20260411 + 8100

RESULT_DIR = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"


def run_with_settings(
    x_init: np.ndarray,
    *,
    measurement_flip_prob: float,
    feedback_strong_tilt: float,
    feedback_weak_ratio: float,
    feedback_steps: int,
    reset_tilt: float,
    reset_steps: int,
    seed: int,
) -> dict:
    original = {
        "MEASUREMENT_FLIP_PROB": base.MEASUREMENT_FLIP_PROB,
        "FEEDBACK_STRONG_TILT": base.FEEDBACK_STRONG_TILT,
        "FEEDBACK_WEAK_TILT": base.FEEDBACK_WEAK_TILT,
        "FEEDBACK_STEPS": base.FEEDBACK_STEPS,
        "RESET_TILT": base.RESET_TILT,
        "RESET_STEPS": base.RESET_STEPS,
    }
    try:
        base.MEASUREMENT_FLIP_PROB = measurement_flip_prob
        base.FEEDBACK_STRONG_TILT = feedback_strong_tilt
        base.FEEDBACK_WEAK_TILT = feedback_weak_ratio * feedback_strong_tilt
        base.FEEDBACK_STEPS = feedback_steps
        base.RESET_TILT = reset_tilt
        base.RESET_STEPS = reset_steps

        ordered = base.simulate_ordered_protocol(
            x_init,
            order=["measurement", "feedback", "reset", "hold"],
            rng=np.random.default_rng(seed + 1),
        )
        feedback_first = base.simulate_ordered_protocol(
            x_init,
            order=["feedback", "measurement", "reset", "hold"],
            rng=np.random.default_rng(seed + 2),
        )
        reset_first = base.simulate_ordered_protocol(
            x_init,
            order=["reset", "measurement", "feedback", "hold"],
            rng=np.random.default_rng(seed + 3),
        )
        measurement_then_reset_then_feedback = base.simulate_ordered_protocol(
            x_init,
            order=["measurement", "reset", "feedback", "hold"],
            rng=np.random.default_rng(seed + 4),
        )
        feedback_only = base.simulate_ordered_protocol(
            x_init,
            order=["feedback", "hold"],
            rng=np.random.default_rng(seed + 5),
        )

        ordering_margin = min(
            feedback_first["final_entropy"],
            reset_first["final_entropy"],
            measurement_then_reset_then_feedback["final_entropy"],
        ) - ordered["final_entropy"]
        reset_signal = measurement_then_reset_then_feedback["final_entropy"] - ordered["final_entropy"]
        blind_control_gap = feedback_only["final_entropy"] - ordered["final_entropy"]

        return {
            "measurement_flip_prob": float(measurement_flip_prob),
            "feedback_strong_tilt": float(feedback_strong_tilt),
            "feedback_weak_ratio": float(feedback_weak_ratio),
            "feedback_weak_tilt": float(base.FEEDBACK_WEAK_TILT),
            "feedback_steps": int(feedback_steps),
            "reset_tilt": float(reset_tilt),
            "reset_steps": int(reset_steps),
            "ordering_margin": float(ordering_margin),
            "measurement_mutual_information": float(ordered["measurement_mutual_information"]),
            "measurement_accuracy": float(ordered["measurement_accuracy"]),
            "reset_signal": float(reset_signal),
            "blind_control_gap": float(blind_control_gap),
            "ordered_final_entropy": float(ordered["final_entropy"]),
            "feedback_first_final_entropy": float(feedback_first["final_entropy"]),
            "reset_first_final_entropy": float(reset_first["final_entropy"]),
            "measurement_then_reset_then_feedback_final_entropy": float(measurement_then_reset_then_feedback["final_entropy"]),
            "closure_error": float(
                max(
                    ordered["closure_error"],
                    feedback_first["closure_error"],
                    reset_first["closure_error"],
                    measurement_then_reset_then_feedback["closure_error"],
                    feedback_only["closure_error"],
                )
            ),
        }
    finally:
        for key, value in original.items():
            setattr(base, key, value)


def main() -> None:
    rows = []
    seed = SEED_BASE
    x_init = base.sample_symmetric_initial_state(base.N_TRAJ, np.random.default_rng(base.RNG_SEED))
    for measurement_flip_prob in MEASUREMENT_FLIP_PROB_GRID:
        for feedback_strong_tilt in FEEDBACK_STRONG_TILT_GRID:
            for feedback_weak_ratio in FEEDBACK_WEAK_RATIO_GRID:
                for feedback_steps in FEEDBACK_STEPS_GRID:
                    for reset_tilt in RESET_TILT_GRID:
                        for reset_steps in RESET_STEPS_GRID:
                            rows.append(
                                run_with_settings(
                                    x_init,
                                    measurement_flip_prob=measurement_flip_prob,
                                    feedback_strong_tilt=feedback_strong_tilt,
                                    feedback_weak_ratio=feedback_weak_ratio,
                                    feedback_steps=feedback_steps,
                                    reset_tilt=reset_tilt,
                                    reset_steps=reset_steps,
                                    seed=seed,
                                )
                            )
                            seed += 10

    best_row = max(rows, key=lambda row: row["ordering_margin"])
    positive = {
        "ordering_margin_improves_materially_over_base_substep_row": {
            "best_ordering_margin": best_row["ordering_margin"],
            "pass": best_row["ordering_margin"] > 0.05,
        },
        "measurement_information_stays_high": {
            "best_measurement_mutual_information": best_row["measurement_mutual_information"],
            "pass": best_row["measurement_mutual_information"] > 0.32,
        },
        "reset_signal_strengthens": {
            "best_reset_signal": best_row["reset_signal"],
            "pass": best_row["reset_signal"] > 0.10,
        },
    }
    negative = {
        "not_every_substep_refinement_setting_helps": {
            "worst_ordering_margin": float(min(row["ordering_margin"] for row in rows)),
            "pass": float(min(row["ordering_margin"] for row in rows)) < 0.01,
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
        "name": "szilard_substep_refinement_sweep",
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
            "best_ordering_margin": best_row["ordering_margin"],
            "best_measurement_mutual_information": best_row["measurement_mutual_information"],
            "best_measurement_accuracy": best_row["measurement_accuracy"],
            "best_reset_signal": best_row["reset_signal"],
            "best_blind_control_gap": best_row["blind_control_gap"],
            "scope_note": (
                "Local refinement sweep for the weak stochastic Szilard substep lane. "
                "It varies feedback and reset mechanics against the same ordered and "
                "scrambled protocol family to see whether the open carrier can produce "
                "a materially stronger ordering and reset signal."
            ),
        },
        "rows": rows,
    }

    out_path = RESULT_DIR / "szilard_substep_refinement_sweep_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
