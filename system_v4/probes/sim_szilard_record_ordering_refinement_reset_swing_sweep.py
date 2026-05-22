#!/usr/bin/env python3
"""Reset-swing recheck at the Szilard record ordering-refinement setting."""

from __future__ import annotations

import json
import pathlib

import numpy as np

import sim_szilard_record_ordering_refinement_sweep as refined


CLASSIFICATION = "diagnostic_only"
classification = CLASSIFICATION
divergence_log = (
    "Row-local reset-swing sensitivity recheck for the Szilard record ordering "
    "refinement. It emits the original reset_swing_gap observable instead of "
    "substituting residual reset entropy."
)

LEGO_IDS = [
    "stochastic_thermodynamics",
    "measurement_feedback",
    "landauer_erasure",
]
PRIMARY_LEGO_IDS = ["stochastic_thermodynamics"]

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "runs finite stochastic reset-swing sweep"},
    "json": {"tried": True, "used": True, "reason": "loads source receipts and writes result receipt"},
    "pathlib": {"tried": True, "used": True, "reason": "resolves canonical receipt paths"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "json": "supportive",
    "pathlib": "supportive",
}

RESULT_DIR = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESET_TILT_GRID = [2.35, 2.75, 3.25]
REPLICATES = 3
SEED_BASE = 20260411 + 9100


def load(name: str) -> dict:
    return json.loads((RESULT_DIR / name).read_text(encoding="utf-8"))


def mean(values: list[float]) -> float:
    return float(sum(values) / len(values))


def main() -> None:
    source = load("szilard_record_ordering_refinement_sweep_results.json")
    qit = load("qit_szilard_record_companion_results.json")
    source_summary = source["summary"]
    best = source_summary["best_setting"]
    qit_summary = qit["summary"]

    rows = []
    seed = SEED_BASE
    for reset_tilt in RESET_TILT_GRID:
        entropies = []
        closure_errors = []
        for replicate in range(REPLICATES):
            rng = np.random.default_rng(seed)
            x_init = refined.hard_base.base.sample_symmetric_initial_state(refined.hard_base.base.N_TRAJ, rng)
            ordered = refined.run_protocol_with_feedback(
                x_init,
                ["measurement", "record_wait", "feedback", "reset", "hold"],
                measurement_flip_prob=refined.MEASUREMENT_FLIP_PROB,
                record_lifetime_steps=refined.RECORD_LIFETIME_STEPS,
                reset_tilt=reset_tilt,
                reset_steps=refined.RESET_STEPS,
                reset_barrier=refined.RESET_BARRIER,
                feedback_strong_tilt=best["feedback_strong_tilt"],
                feedback_weak_tilt=best["feedback_strong_tilt"] * best["feedback_weak_ratio"],
                record_wait_steps=best["record_wait_steps"],
                feedback_steps=best["feedback_steps"],
                feedback_barrier_end=best["feedback_barrier_end"],
                rng=np.random.default_rng(seed + 1),
            )
            entropies.append(float(ordered["reset_stage_entropy"]))
            closure_errors.append(float(ordered["closure_error"]))
            seed += 10
        rows.append(
            {
                "reset_tilt": float(reset_tilt),
                "mean_reset_stage_entropy": mean(entropies),
                "replicate_reset_stage_entropy": entropies,
                "max_closure_error": float(max(closure_errors)),
            }
        )

    weak = next(row for row in rows if row["reset_tilt"] == min(RESET_TILT_GRID))
    strong = next(row for row in rows if row["reset_tilt"] == max(RESET_TILT_GRID))
    open_reset_swing = weak["mean_reset_stage_entropy"] - strong["mean_reset_stage_entropy"]
    qit_reset_swing = (
        qit_summary["weak_reset_mean_memory_entropy_after_reset"]
        - qit_summary["strong_reset_mean_memory_entropy_after_reset"]
    )
    reset_swing_gap = qit_reset_swing - open_reset_swing
    residual_reset_entropy_gap = (
        strong["mean_reset_stage_entropy"] - qit_summary["strong_reset_mean_memory_entropy_after_reset"]
    )

    positive = {
        "original_reset_swing_observable_is_emitted": {
            "open_reset_swing": open_reset_swing,
            "qit_reset_swing": qit_reset_swing,
            "reset_swing_gap": reset_swing_gap,
            "pass": True,
        },
        "reset_swing_gap_under_original_bound": {
            "reset_swing_gap": reset_swing_gap,
            "bound": 0.15,
            "pass": abs(reset_swing_gap) < 0.15,
        },
        "residual_reset_entropy_gap_under_original_bound": {
            "residual_reset_entropy_gap": residual_reset_entropy_gap,
            "bound": 0.15,
            "pass": residual_reset_entropy_gap < 0.15,
        },
    }
    negative = {
        "row_local_recheck_not_qit_or_axis_admission": {"pass": True},
    }
    boundary = {
        "all_metrics_finite": {
            "pass": bool(
                all(np.isfinite(v) for row in rows for v in row["replicate_reset_stage_entropy"])
                and np.isfinite(open_reset_swing)
                and np.isfinite(qit_reset_swing)
                and np.isfinite(reset_swing_gap)
                and np.isfinite(residual_reset_entropy_gap)
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
        "name": "szilard_record_ordering_refinement_reset_swing_sweep",
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
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": bool(all_pass),
            "best_setting": best,
            "reset_tilt_grid": RESET_TILT_GRID,
            "open_reset_swing": open_reset_swing,
            "qit_reset_swing": qit_reset_swing,
            "reset_swing_gap": reset_swing_gap,
            "residual_reset_entropy_gap": residual_reset_entropy_gap,
            "qit_or_axis_promotion_allowed": False,
            "scope_note": divergence_log,
        },
        "rows": rows,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULT_DIR / "szilard_record_ordering_refinement_reset_swing_sweep_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
