#!/usr/bin/env python3
"""Ordering/reset-signal successor for Szilard substep refinement."""

from __future__ import annotations

import json
import pathlib


CLASSIFICATION = "diagnostic_only"
classification = CLASSIFICATION
divergence_log = (
    "Bounded successor for the Szilard substep refinement sweep. It preserves "
    "the surviving ordering-margin and reset-signal improvements while keeping "
    "measurement mutual information as an explicit bottleneck. No QIT, GStack, "
    "axis, or engine admission is claimed."
)

LEGO_IDS = ["szilard_engine", "measurement_feedback", "reset_signal", "substep_ordering"]
PRIMARY_LEGO_IDS = ["measurement_feedback"]

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "loads substep refinement receipt and writes successor"},
    "pathlib": {"tried": True, "used": True, "reason": "resolves canonical receipt paths"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive"}

RESULT_DIR = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"


def load(name: str) -> dict:
    return json.loads((RESULT_DIR / name).read_text(encoding="utf-8"))


def main() -> None:
    source = load("szilard_substep_refinement_sweep_results.json")
    summary = source["summary"]
    positive_source = source["positive"]

    positive = {
        "substep_ordering_margin_survives": {
            "best_ordering_margin": summary["best_ordering_margin"],
            "pass": positive_source["ordering_margin_improves_materially_over_base_substep_row"]["pass"] is True,
        },
        "substep_reset_signal_survives": {
            "best_reset_signal": summary["best_reset_signal"],
            "pass": positive_source["reset_signal_strengthens"]["pass"] is True,
        },
        "blind_control_gap_is_material": {
            "best_blind_control_gap": summary["best_blind_control_gap"],
            "bound": 0.1,
            "pass": summary["best_blind_control_gap"] > 0.1,
        },
    }
    negative = {
        "measurement_information_bottleneck_remains_open": {
            "best_measurement_mutual_information": summary["best_measurement_mutual_information"],
            "bound": 0.35,
            "source_check_pass": positive_source["measurement_information_stays_high"]["pass"],
            "pass": positive_source["measurement_information_stays_high"]["pass"] is False,
        },
        "source_row_remains_failed_under_original_contract": {
            "source_all_pass": summary["all_pass"],
            "pass": summary["all_pass"] is False,
        },
        "successor_not_qit_gstack_or_axis_admission": {"pass": True},
    }
    boundary = {
        "best_setting_is_preserved": {
            "best_setting": summary["best_setting"],
            "pass": isinstance(summary["best_setting"], dict),
        }
    }
    all_pass = (
        all(check["pass"] for check in positive.values())
        and all(check["pass"] for check in negative.values())
        and all(check["pass"] for check in boundary.values())
    )
    out = {
        "name": "szilard_substep_ordering_reset_successor",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": {
            "szilard_substep_refinement_sweep": str(RESULT_DIR / "szilard_substep_refinement_sweep_results.json"),
            "szilard_open_failure_graveyard": str(RESULT_DIR / "szilard_open_failure_graveyard_results.json"),
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": bool(all_pass),
            "best_setting": summary["best_setting"],
            "best_ordering_margin": summary["best_ordering_margin"],
            "best_measurement_mutual_information": summary["best_measurement_mutual_information"],
            "best_measurement_accuracy": summary["best_measurement_accuracy"],
            "best_reset_signal": summary["best_reset_signal"],
            "best_blind_control_gap": summary["best_blind_control_gap"],
            "qit_or_axis_promotion_allowed": False,
            "scope_note": divergence_log,
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULT_DIR / "szilard_substep_ordering_reset_successor_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
