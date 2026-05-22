#!/usr/bin/env python3
"""Widen the reset axis around the Szilard ordering-refinement carrier."""

from __future__ import annotations

import json
import pathlib

import numpy as np

import sim_szilard_record_ordering_refinement_sweep as refined


CLASSIFICATION = "diagnostic_only"
classification = CLASSIFICATION
divergence_log = (
    "Bounded successor probe for the Szilard record reset-swing blocker. It "
    "widens reset tilt, reset duration, and reset barrier around the existing "
    "ordering-refinement carrier, keeps the original reset_swing_gap observable, "
    "and does not claim QIT, GStack, axis, or engine admission."
)

LEGO_IDS = [
    "stochastic_thermodynamics",
    "measurement_feedback",
    "landauer_erasure",
]
PRIMARY_LEGO_IDS = ["stochastic_thermodynamics"]

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "runs finite stochastic reset-axis sweep"},
    "json": {"tried": True, "used": True, "reason": "loads source receipts and writes result receipt"},
    "pathlib": {"tried": True, "used": True, "reason": "resolves canonical receipt paths"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "json": "supportive",
    "pathlib": "supportive",
}

RESULT_DIR = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"
WEAK_RESET_TILT = 1.55
STRONG_RESET_TILT_GRID = [3.25, 4.25, 5.25, 6.25]
RESET_STEPS_GRID = [480, 720]
RESET_BARRIER_GRID = [1.25, 1.55, 1.85]
REPLICATES = 3
SEED_BASE = 20260411 + 10100


def load(name: str) -> dict:
    return json.loads((RESULT_DIR / name).read_text(encoding="utf-8"))


def mean(values: list[float]) -> float:
    return float(sum(values) / len(values))


def run_reset_entropy(
    *,
    reset_tilt: float,
    reset_steps: int,
    reset_barrier: float,
    best: dict,
    seed: int,
) -> dict:
    entropies = []
    closure_errors = []
    for replicate in range(REPLICATES):
        replicate_seed = seed + replicate * 10
        rng = np.random.default_rng(replicate_seed)
        x_init = refined.hard_base.base.sample_symmetric_initial_state(refined.hard_base.base.N_TRAJ, rng)
        ordered = refined.run_protocol_with_feedback(
            x_init,
            ["measurement", "record_wait", "feedback", "reset", "hold"],
            measurement_flip_prob=refined.MEASUREMENT_FLIP_PROB,
            record_lifetime_steps=refined.RECORD_LIFETIME_STEPS,
            reset_tilt=reset_tilt,
            reset_steps=reset_steps,
            reset_barrier=reset_barrier,
            feedback_strong_tilt=best["feedback_strong_tilt"],
            feedback_weak_tilt=best["feedback_strong_tilt"] * best["feedback_weak_ratio"],
            record_wait_steps=best["record_wait_steps"],
            feedback_steps=best["feedback_steps"],
            feedback_barrier_end=best["feedback_barrier_end"],
            rng=np.random.default_rng(replicate_seed + 1),
        )
        entropies.append(float(ordered["reset_stage_entropy"]))
        closure_errors.append(float(ordered["closure_error"]))
    return {
        "mean_reset_stage_entropy": mean(entropies),
        "replicate_reset_stage_entropy": entropies,
        "max_closure_error": float(max(closure_errors)),
    }


def main() -> None:
    source = load("szilard_record_ordering_refinement_sweep_results.json")
    qit = load("qit_szilard_record_companion_results.json")
    best = source["summary"]["best_setting"]
    qit_summary = qit["summary"]
    qit_strong_reset_entropy = float(qit_summary["strong_reset_mean_memory_entropy_after_reset"])
    qit_reset_swing = float(
        qit_summary["weak_reset_mean_memory_entropy_after_reset"]
        - qit_summary["strong_reset_mean_memory_entropy_after_reset"]
    )

    rows = []
    seed = SEED_BASE
    for reset_steps in RESET_STEPS_GRID:
        for reset_barrier in RESET_BARRIER_GRID:
            weak = run_reset_entropy(
                reset_tilt=WEAK_RESET_TILT,
                reset_steps=reset_steps,
                reset_barrier=reset_barrier,
                best=best,
                seed=seed,
            )
            seed += 100
            for strong_reset_tilt in STRONG_RESET_TILT_GRID:
                strong = run_reset_entropy(
                    reset_tilt=strong_reset_tilt,
                    reset_steps=reset_steps,
                    reset_barrier=reset_barrier,
                    best=best,
                    seed=seed,
                )
                seed += 100
                open_reset_swing = weak["mean_reset_stage_entropy"] - strong["mean_reset_stage_entropy"]
                reset_swing_gap = qit_reset_swing - open_reset_swing
                residual_reset_entropy_gap = strong["mean_reset_stage_entropy"] - qit_strong_reset_entropy
                row = {
                    "weak_reset_tilt": float(WEAK_RESET_TILT),
                    "strong_reset_tilt": float(strong_reset_tilt),
                    "reset_steps": int(reset_steps),
                    "reset_barrier": float(reset_barrier),
                    "weak_mean_reset_stage_entropy": weak["mean_reset_stage_entropy"],
                    "strong_mean_reset_stage_entropy": strong["mean_reset_stage_entropy"],
                    "weak_replicate_reset_stage_entropy": weak["replicate_reset_stage_entropy"],
                    "strong_replicate_reset_stage_entropy": strong["replicate_reset_stage_entropy"],
                    "open_reset_swing": float(open_reset_swing),
                    "qit_reset_swing": float(qit_reset_swing),
                    "reset_swing_gap": float(reset_swing_gap),
                    "residual_reset_entropy_gap": float(residual_reset_entropy_gap),
                    "max_closure_error": float(max(weak["max_closure_error"], strong["max_closure_error"])),
                }
                row["candidate_pass"] = bool(
                    abs(row["reset_swing_gap"]) < 0.15
                    and abs(row["residual_reset_entropy_gap"]) < 0.15
                    and row["max_closure_error"] < 1e-8
                )
                rows.append(row)

    best_candidate = min(
        rows,
        key=lambda row: max(abs(row["reset_swing_gap"]), abs(row["residual_reset_entropy_gap"])),
    )
    positive = {
        "best_reset_swing_gap_under_original_bound": {
            "reset_swing_gap": best_candidate["reset_swing_gap"],
            "bound": 0.15,
            "pass": abs(best_candidate["reset_swing_gap"]) < 0.15,
        },
        "best_residual_reset_entropy_gap_under_original_bound": {
            "residual_reset_entropy_gap": best_candidate["residual_reset_entropy_gap"],
            "bound": 0.15,
            "pass": abs(best_candidate["residual_reset_entropy_gap"]) < 0.15,
        },
        "widened_axis_has_candidate_with_both_reset_checks": {
            "passing_candidate_count": int(sum(row["candidate_pass"] for row in rows)),
            "pass": any(row["candidate_pass"] for row in rows),
        },
    }
    negative = {
        "not_every_widened_axis_setting_closes_reset_gap": {
            "failing_candidate_count": int(sum(not row["candidate_pass"] for row in rows)),
            "pass": any(not row["candidate_pass"] for row in rows),
        },
        "successor_not_qit_gstack_or_axis_admission": {"pass": True},
    }
    boundary = {
        "all_metrics_finite": {
            "pass": bool(
                all(
                    np.isfinite(value)
                    for row in rows
                    for value in [
                        row["weak_mean_reset_stage_entropy"],
                        row["strong_mean_reset_stage_entropy"],
                        row["open_reset_swing"],
                        row["qit_reset_swing"],
                        row["reset_swing_gap"],
                        row["residual_reset_entropy_gap"],
                    ]
                )
            )
        },
        "bookkeeping_stays_closed": {
            "max_closure_error": float(max(row["max_closure_error"] for row in rows)),
            "pass": float(max(row["max_closure_error"] for row in rows)) < 1e-8,
        },
    }
    all_pass = (
        all(check["pass"] for check in positive.values())
        and all(check["pass"] for check in negative.values())
        and all(check["pass"] for check in boundary.values())
    )
    out = {
        "name": "szilard_record_ordering_refinement_reset_axis_widened_sweep",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": {
            "ordering_refinement": str(RESULT_DIR / "szilard_record_ordering_refinement_sweep_results.json"),
            "qit_companion": str(RESULT_DIR / "qit_szilard_record_companion_results.json"),
            "prior_failed_reset_swing_recheck": str(
                RESULT_DIR / "szilard_record_ordering_refinement_reset_swing_sweep_results.json"
            ),
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": bool(all_pass),
            "best_setting": best,
            "weak_reset_tilt": float(WEAK_RESET_TILT),
            "strong_reset_tilt_grid": STRONG_RESET_TILT_GRID,
            "reset_steps_grid": RESET_STEPS_GRID,
            "reset_barrier_grid": RESET_BARRIER_GRID,
            "best_candidate": best_candidate,
            "best_open_reset_swing": best_candidate["open_reset_swing"],
            "qit_reset_swing": float(qit_reset_swing),
            "best_reset_swing_gap": best_candidate["reset_swing_gap"],
            "best_residual_reset_entropy_gap": best_candidate["residual_reset_entropy_gap"],
            "passing_candidate_count": int(sum(row["candidate_pass"] for row in rows)),
            "qit_or_axis_promotion_allowed": False,
            "scope_note": divergence_log,
        },
        "rows": rows,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULT_DIR / "szilard_record_ordering_refinement_reset_axis_widened_sweep_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
