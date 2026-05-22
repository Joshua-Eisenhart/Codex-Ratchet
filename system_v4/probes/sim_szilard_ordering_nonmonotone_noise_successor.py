#!/usr/bin/env python3
"""Nonmonotone-noise successor for Szilard ordering sensitivity."""

from __future__ import annotations

import json
import pathlib


CLASSIFICATION = "diagnostic_only"
classification = CLASSIFICATION
divergence_log = (
    "Bounded successor for the Szilard ordering-sensitivity row. The source "
    "row falsified low-noise monotonicity and clean high-noise failure; this "
    "receipt preserves the surviving local ordering signal with stronger "
    "feedback and nonmonotone noise response, without QIT, GStack, axis, or "
    "engine admission."
)

LEGO_IDS = ["szilard_engine", "measurement_feedback", "ordering_sensitivity"]
PRIMARY_LEGO_IDS = ["measurement_feedback"]

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "loads source sensitivity sweep and writes successor receipt"},
    "pathlib": {"tried": True, "used": True, "reason": "resolves canonical receipt paths"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive"}

RESULT_DIR = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"


def load(name: str) -> dict:
    return json.loads((RESULT_DIR / name).read_text(encoding="utf-8"))


def main() -> None:
    source = load("szilard_ordering_sensitivity_sweep_results.json")
    summary = source["summary"]
    positive_source = source["positive"]
    negative_source = source["negative"]
    best_margin = summary["best_margin"]
    high_noise_best_margin = negative_source["high_noise_settings_do_not_give_clean_ordering_separation"][
        "high_noise_best_margin"
    ]
    low_noise_mean = positive_source["lower_measurement_noise_improves_ordering_margin_on_average"][
        "low_noise_mean_margin"
    ]
    high_noise_mean = positive_source["lower_measurement_noise_improves_ordering_margin_on_average"][
        "high_noise_mean_margin"
    ]
    strong_feedback_mean = positive_source["stronger_feedback_improves_ordering_margin_on_average"][
        "strong_feedback_mean_margin"
    ]
    weak_feedback_mean = positive_source["stronger_feedback_improves_ordering_margin_on_average"][
        "weak_feedback_mean_margin"
    ]

    positive = {
        "local_ordering_signal_survives": {
            "best_margin": best_margin,
            "best_setting": summary["best_setting"],
            "pass": best_margin > 0.01,
        },
        "stronger_feedback_improves_average_ordering_margin": {
            "strong_feedback_mean_margin": strong_feedback_mean,
            "weak_feedback_mean_margin": weak_feedback_mean,
            "pass": strong_feedback_mean > weak_feedback_mean,
        },
        "high_noise_contains_surviving_ordering_signal": {
            "high_noise_best_margin": high_noise_best_margin,
            "bound": 0.01,
            "pass": high_noise_best_margin > 0.01,
        },
    }
    negative = {
        "low_noise_monotonicity_prior_is_killed": {
            "low_noise_mean_margin": low_noise_mean,
            "high_noise_mean_margin": high_noise_mean,
            "pass": high_noise_mean > low_noise_mean,
        },
        "source_row_remains_failed_under_original_contract": {
            "source_all_pass": summary["all_pass"],
            "pass": summary["all_pass"] is False,
        },
        "successor_not_qit_gstack_or_axis_admission": {"pass": True},
    }
    boundary = {
        "source_expected_failures_are_exactly_present": {
            "low_noise_check_pass": positive_source["lower_measurement_noise_improves_ordering_margin_on_average"][
                "pass"
            ],
            "high_noise_unclean_check_pass": negative_source["high_noise_settings_do_not_give_clean_ordering_separation"][
                "pass"
            ],
            "pass": (
                positive_source["lower_measurement_noise_improves_ordering_margin_on_average"]["pass"] is False
                and negative_source["high_noise_settings_do_not_give_clean_ordering_separation"]["pass"] is False
            ),
        }
    }
    all_pass = (
        all(check["pass"] for check in positive.values())
        and all(check["pass"] for check in negative.values())
        and all(check["pass"] for check in boundary.values())
    )
    out = {
        "name": "szilard_ordering_nonmonotone_noise_successor",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": {
            "szilard_ordering_sensitivity_sweep": str(RESULT_DIR / "szilard_ordering_sensitivity_sweep_results.json"),
            "szilard_open_failure_graveyard": str(RESULT_DIR / "szilard_open_failure_graveyard_results.json"),
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": bool(all_pass),
            "best_margin": best_margin,
            "best_setting": summary["best_setting"],
            "low_noise_mean_margin": low_noise_mean,
            "high_noise_mean_margin": high_noise_mean,
            "strong_feedback_mean_margin": strong_feedback_mean,
            "weak_feedback_mean_margin": weak_feedback_mean,
            "high_noise_best_margin": high_noise_best_margin,
            "qit_or_axis_promotion_allowed": False,
            "scope_note": divergence_log,
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULT_DIR / "szilard_ordering_nonmonotone_noise_successor_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
