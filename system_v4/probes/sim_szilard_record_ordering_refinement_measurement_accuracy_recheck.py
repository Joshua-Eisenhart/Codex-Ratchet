#!/usr/bin/env python3
"""Re-emit measurement accuracy for the Szilard ordering-refinement carrier."""

from __future__ import annotations

import json
import pathlib

import numpy as np

import sim_szilard_record_ordering_refinement_sweep as refined


CLASSIFICATION = "diagnostic_only"
classification = CLASSIFICATION
divergence_log = (
    "Exact-observable recheck for the Szilard record translation blocker. It "
    "runs the ordering-refinement carrier and emits measurement_accuracy_gap, "
    "which the successor translation lane previously left unretested."
)

LEGO_IDS = [
    "stochastic_thermodynamics",
    "measurement_feedback",
    "state_distinguishability",
]
PRIMARY_LEGO_IDS = ["measurement_feedback"]

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "runs finite stochastic measurement recheck"},
    "json": {"tried": True, "used": True, "reason": "loads source receipts and writes result receipt"},
    "pathlib": {"tried": True, "used": True, "reason": "resolves canonical receipt paths"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "json": "supportive",
    "pathlib": "supportive",
}

RESULT_DIR = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"
REPLICATES = 5
SEED_BASE = 20260411 + 11100


def load(name: str) -> dict:
    return json.loads((RESULT_DIR / name).read_text(encoding="utf-8"))


def mean(values: list[float]) -> float:
    return float(sum(values) / len(values))


def main() -> None:
    source = load("szilard_record_ordering_refinement_sweep_results.json")
    qit = load("qit_szilard_record_companion_results.json")
    best = source["summary"]["best_setting"]
    qit_mean_measurement_accuracy = float(qit["summary"]["mean_measurement_accuracy"])

    rows = []
    for replicate in range(REPLICATES):
        seed = SEED_BASE + replicate * 10
        rng = np.random.default_rng(seed)
        x_init = refined.hard_base.base.sample_symmetric_initial_state(refined.hard_base.base.N_TRAJ, rng)
        ordered = refined.run_protocol_with_feedback(
            x_init,
            ["measurement", "record_wait", "feedback", "reset", "hold"],
            measurement_flip_prob=refined.MEASUREMENT_FLIP_PROB,
            record_lifetime_steps=refined.RECORD_LIFETIME_STEPS,
            reset_tilt=refined.RESET_TILT,
            reset_steps=refined.RESET_STEPS,
            reset_barrier=refined.RESET_BARRIER,
            feedback_strong_tilt=best["feedback_strong_tilt"],
            feedback_weak_tilt=best["feedback_strong_tilt"] * best["feedback_weak_ratio"],
            record_wait_steps=best["record_wait_steps"],
            feedback_steps=best["feedback_steps"],
            feedback_barrier_end=best["feedback_barrier_end"],
            rng=np.random.default_rng(seed + 1),
        )
        rows.append(
            {
                "replicate": replicate,
                "measurement_accuracy": float(ordered["measurement_accuracy"]),
                "measurement_mutual_information": float(ordered["measurement_mutual_information"]),
                "closure_error": float(ordered["closure_error"]),
            }
        )

    open_mean_measurement_accuracy = mean([row["measurement_accuracy"] for row in rows])
    measurement_accuracy_gap = qit_mean_measurement_accuracy - open_mean_measurement_accuracy
    positive = {
        "measurement_accuracy_gap_under_original_bound": {
            "open_mean_measurement_accuracy": open_mean_measurement_accuracy,
            "qit_mean_measurement_accuracy": qit_mean_measurement_accuracy,
            "measurement_accuracy_gap": measurement_accuracy_gap,
            "bound": 0.05,
            "pass": abs(measurement_accuracy_gap) < 0.05,
        },
        "measurement_stage_is_informative": {
            "open_mean_measurement_accuracy": open_mean_measurement_accuracy,
            "pass": open_mean_measurement_accuracy > 0.5,
        },
    }
    negative = {
        "not_qit_gstack_or_axis_admission": {"pass": True},
    }
    boundary = {
        "all_metrics_finite": {
            "pass": bool(
                np.isfinite(open_mean_measurement_accuracy)
                and np.isfinite(qit_mean_measurement_accuracy)
                and np.isfinite(measurement_accuracy_gap)
            )
        },
        "bookkeeping_stays_closed": {
            "max_closure_error": float(max(row["closure_error"] for row in rows)),
            "pass": float(max(row["closure_error"] for row in rows)) < 1e-8,
        },
    }
    all_pass = (
        all(check["pass"] for check in positive.values())
        and all(check["pass"] for check in negative.values())
        and all(check["pass"] for check in boundary.values())
    )
    out = {
        "name": "szilard_record_ordering_refinement_measurement_accuracy_recheck",
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
            "open_mean_measurement_accuracy": open_mean_measurement_accuracy,
            "qit_mean_measurement_accuracy": qit_mean_measurement_accuracy,
            "measurement_accuracy_gap": measurement_accuracy_gap,
            "qit_or_axis_promotion_allowed": False,
            "scope_note": divergence_log,
        },
        "rows": rows,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULT_DIR / "szilard_record_ordering_refinement_measurement_accuracy_recheck_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
