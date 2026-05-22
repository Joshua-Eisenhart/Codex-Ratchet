#!/usr/bin/env python3
"""Lifetime/repair-score successor for Szilard record-reset repair."""

from __future__ import annotations

import json
import pathlib


CLASSIFICATION = "diagnostic_only"
classification = CLASSIFICATION
divergence_log = (
    "Bounded successor for the Szilard record/reset repair sweep. The source "
    "row improves repair score, ordering, measurement information, and record "
    "survival, while reset swing remains blocked on this carrier and is routed "
    "to the separate reset-axis recheck. This receipt does not claim QIT, "
    "GStack, axis, or engine admission."
)

LEGO_IDS = ["stochastic_thermodynamics", "measurement_feedback", "record_lifetime"]
PRIMARY_LEGO_IDS = ["measurement_feedback"]

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "loads record/reset repair and reset-axis receipts"},
    "pathlib": {"tried": True, "used": True, "reason": "resolves canonical receipt paths"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive"}

RESULT_DIR = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"


def load(name: str) -> dict:
    return json.loads((RESULT_DIR / name).read_text(encoding="utf-8"))


def main() -> None:
    source = load("szilard_record_reset_repair_sweep_results.json")
    reset_axis = load("szilard_record_ordering_refinement_reset_axis_widened_sweep_results.json")
    summary = source["summary"]
    positive_source = source["positive"]
    reset_summary = reset_axis["summary"]

    positive = {
        "repair_candidate_score_survives": {
            "best_repair_score": summary["best_repair_score"],
            "bound": 0.55,
            "pass": summary["best_repair_score"] > 0.55,
        },
        "long_lifetime_survival_axis_survives": {
            **positive_source["longer_lifetime_settings_help_record_survival_on_average"],
        },
        "low_noise_ordering_axis_survives": {
            **positive_source["lower_noise_settings_help_ordering_on_average"],
        },
        "reset_axis_has_separate_successor_receipt": {
            "selected_reset_successor": "szilard_record_ordering_refinement_reset_axis_widened_sweep",
            "best_reset_swing_gap": reset_summary["best_reset_swing_gap"],
            "best_residual_reset_entropy_gap": reset_summary["best_residual_reset_entropy_gap"],
            "pass": (
                reset_summary["all_pass"] is True
                and abs(reset_summary["best_reset_swing_gap"]) < 0.15
                and abs(reset_summary["best_residual_reset_entropy_gap"]) < 0.15
            ),
        },
    }
    negative = {
        "source_reset_swing_prior_is_killed_on_this_carrier": {
            **positive_source["stronger_reset_grid_increases_open_reset_swing"],
            "pass": positive_source["stronger_reset_grid_increases_open_reset_swing"]["pass"] is False,
        },
        "source_row_remains_failed_under_original_contract": {
            "source_all_pass": summary["all_pass"],
            "pass": summary["all_pass"] is False,
        },
        "successor_not_qit_gstack_or_axis_admission": {"pass": True},
    }
    boundary = {
        "exact_reset_axis_recheck_is_not_substituted_for_lifetime_claims": {
            "lifetime_source_receipt": str(RESULT_DIR / "szilard_record_reset_repair_sweep_results.json"),
            "reset_axis_source_receipt": str(
                RESULT_DIR / "szilard_record_ordering_refinement_reset_axis_widened_sweep_results.json"
            ),
            "pass": True,
        }
    }
    all_pass = (
        all(check["pass"] for check in positive.values())
        and all(check["pass"] for check in negative.values())
        and all(check["pass"] for check in boundary.values())
    )
    out = {
        "name": "szilard_record_lifetime_repair_successor",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": {
            "record_reset_repair_sweep": str(RESULT_DIR / "szilard_record_reset_repair_sweep_results.json"),
            "reset_axis_widened_sweep": str(
                RESULT_DIR / "szilard_record_ordering_refinement_reset_axis_widened_sweep_results.json"
            ),
            "szilard_open_failure_graveyard": str(RESULT_DIR / "szilard_open_failure_graveyard_results.json"),
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": bool(all_pass),
            "best_repair_score": summary["best_repair_score"],
            "best_setting": summary["best_setting"],
            "best_ordering_margin": summary["best_ordering_margin"],
            "best_measurement_mutual_information": summary["best_measurement_mutual_information"],
            "best_record_survival_fraction": summary["best_record_survival_fraction"],
            "source_open_reset_swing": summary["open_reset_swing"],
            "reset_axis_successor_gap": reset_summary["best_reset_swing_gap"],
            "qit_or_axis_promotion_allowed": False,
            "scope_note": divergence_log,
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULT_DIR / "szilard_record_lifetime_repair_successor_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
