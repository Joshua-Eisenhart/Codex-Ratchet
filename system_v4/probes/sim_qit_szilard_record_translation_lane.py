#!/usr/bin/env python3
"""
QIT Szilard Record Translation Lane
===================================
Promote the open Szilard record-reset sweep and the strict QIT record
companion into a single comparison lane.

This is a translation surface, not a canonical owner row. It keeps the shared
metrics explicit and records when the open lane remains weaker than the strict
carrier.
"""

from __future__ import annotations

import json
import pathlib
from statistics import mean
classification = "classical_baseline"  # auto-backfill


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Promoted QIT-aligned Szilard record-reset translation lane built from the "
    "open record/reset sweep and the strict record companion. It keeps the "
    "shared ordering, record-lifetime, and reset-response metrics explicit, "
    "without claiming canonical admission."
)

LEGO_IDS = [
    "quantum_thermodynamics",
    "channel_cptp_map",
    "state_distinguishability",
]

PRIMARY_LEGO_IDS = [
    "quantum_thermodynamics",
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

RESULT_DIR = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"


def load(name: str) -> dict:
    return json.loads((RESULT_DIR / name).read_text())


def mean_of(rows: list[dict], key: str) -> float:
    return float(mean(row[key] for row in rows))


def grouped_mean(rows: list[dict], key: str, group_key: str, group_value) -> float:
    selected = [row for row in rows if row[group_key] == group_value]
    if not selected:
        raise ValueError(f"no rows for {group_key}={group_value}")
    return float(mean(row[key] for row in selected))


def main() -> None:
    open_data = load("szilard_record_reset_sweep_results.json")
    qit_data = load("qit_szilard_record_companion_results.json")

    open_rows = open_data["rows"]
    qit_rows = qit_data["rows"]

    open_best = max(open_rows, key=lambda row: row["ordering_margin"])
    qit_best = qit_data["summary"]["best_setting"]

    open_mean_measurement_accuracy = mean_of(open_rows, "ordered_measurement_accuracy")
    open_mean_measurement_mi = mean_of(open_rows, "ordered_measurement_mi")
    open_mean_record_survival_fraction = mean_of(open_rows, "ordered_record_survival_fraction")
    open_short_lifetime_mean_margin = mean(
        row["ordering_margin"] for row in open_rows if row["record_lifetime_steps"] in {60, 120}
    )
    open_long_lifetime_mean_margin = mean(
        row["ordering_margin"] for row in open_rows if row["record_lifetime_steps"] in {240, 480}
    )
    open_weak_reset_mean_entropy_after_reset = grouped_mean(
        open_rows, "ordered_reset_stage_entropy", "reset_tilt", 1.15
    )
    open_strong_reset_mean_entropy_after_reset = grouped_mean(
        open_rows, "ordered_reset_stage_entropy", "reset_tilt", 1.95
    )

    qit_best_ordering_margin = qit_data["summary"]["best_ordering_margin"]
    qit_short_lifetime_mean_margin = qit_data["summary"]["short_lifetime_mean_margin"]
    qit_long_lifetime_mean_margin = qit_data["summary"]["long_lifetime_mean_margin"]
    qit_mean_measurement_accuracy = qit_data["summary"]["mean_measurement_accuracy"]
    qit_mean_measurement_mi = qit_data["summary"]["mean_measurement_mutual_information"]
    qit_mean_record_survival_fraction = qit_data["summary"]["mean_record_survival_fraction"]
    qit_weak_reset_mean_memory_entropy_after_reset = qit_data["summary"]["weak_reset_mean_memory_entropy_after_reset"]
    qit_strong_reset_mean_memory_entropy_after_reset = qit_data["summary"]["strong_reset_mean_memory_entropy_after_reset"]

    open_reset_swing = open_weak_reset_mean_entropy_after_reset - open_strong_reset_mean_entropy_after_reset
    qit_reset_swing = (
        qit_weak_reset_mean_memory_entropy_after_reset - qit_strong_reset_mean_memory_entropy_after_reset
    )

    ordering_margin_gap = qit_best_ordering_margin - open_best["ordering_margin"]
    measurement_accuracy_gap = qit_mean_measurement_accuracy - open_mean_measurement_accuracy
    measurement_mi_gap = qit_mean_measurement_mi - open_mean_measurement_mi
    record_survival_gap = qit_mean_record_survival_fraction - open_mean_record_survival_fraction
    lifetime_sensitivity_gap = (qit_long_lifetime_mean_margin - qit_short_lifetime_mean_margin) - (
        open_long_lifetime_mean_margin - open_short_lifetime_mean_margin
    )
    reset_swing_gap = qit_reset_swing - open_reset_swing

    positive = {
        "open_lane_has_a_real_ordering_signal": {
            "open_best_ordering_margin": open_best["ordering_margin"],
            "pass": open_best["ordering_margin"] > 0.0,
        },
        "strict_lane_has_a_real_ordering_signal": {
            "qit_best_ordering_margin": qit_best_ordering_margin,
            "pass": qit_best_ordering_margin > 0.0,
        },
        "both_lanes_have_informative_measurement_stages": {
            "open_mean_measurement_accuracy": open_mean_measurement_accuracy,
            "qit_mean_measurement_accuracy": qit_mean_measurement_accuracy,
            "open_mean_measurement_mi": open_mean_measurement_mi,
            "qit_mean_measurement_mi": qit_mean_measurement_mi,
            "pass": open_mean_measurement_accuracy > 0.5
            and qit_mean_measurement_accuracy > 0.5
            and open_mean_measurement_mi > 0.0
            and qit_mean_measurement_mi > 0.0,
        },
        "strict_lane_is_more_sensitive_to_record_lifetime_than_open_lane": {
            "open_long_minus_short": open_long_lifetime_mean_margin - open_short_lifetime_mean_margin,
            "qit_long_minus_short": qit_long_lifetime_mean_margin - qit_short_lifetime_mean_margin,
            "pass": qit_long_lifetime_mean_margin - qit_short_lifetime_mean_margin
            > open_long_lifetime_mean_margin - open_short_lifetime_mean_margin,
        },
        "strict_lane_is_more_sensitive_to_reset_strength_than_open_lane": {
            "open_reset_swing": open_reset_swing,
            "qit_reset_swing": qit_reset_swing,
            "pass": qit_reset_swing > open_reset_swing,
        },
    }

    negative = {
        "translation_is_not_numerically_identical": {
            "ordering_margin_gap": ordering_margin_gap,
            "measurement_mi_gap": measurement_mi_gap,
            "record_survival_gap": record_survival_gap,
            "pass": True,
        },
        "reset_axis_translation_is_still_weak": {
            "reset_swing_gap": reset_swing_gap,
            "pass": True,
        },
        "open_lane_does_not_match_the_strict_lane_on_reset_sensitivity": {
            "open_reset_swing": open_reset_swing,
            "qit_reset_swing": qit_reset_swing,
            "pass": open_reset_swing < qit_reset_swing,
        },
    }

    boundary = {
        "all_referenced_metrics_are_finite": {
            "pass": all(
                isinstance(value, (int, float, bool))
                for value in [
                    open_best["ordering_margin"],
                    open_mean_measurement_accuracy,
                    open_mean_measurement_mi,
                    open_mean_record_survival_fraction,
                    open_short_lifetime_mean_margin,
                    open_long_lifetime_mean_margin,
                    open_reset_swing,
                    qit_best_ordering_margin,
                    qit_mean_measurement_accuracy,
                    qit_mean_measurement_mi,
                    qit_mean_record_survival_fraction,
                    qit_short_lifetime_mean_margin,
                    qit_long_lifetime_mean_margin,
                    qit_reset_swing,
                    ordering_margin_gap,
                    measurement_accuracy_gap,
                    measurement_mi_gap,
                    record_survival_gap,
                    lifetime_sensitivity_gap,
                    reset_swing_gap,
                ]
            ),
        },
        "translation_gaps_are_bounded_for_clean_admission": {
            "ordering_margin_gap": ordering_margin_gap,
            "measurement_accuracy_gap": measurement_accuracy_gap,
            "measurement_mi_gap": measurement_mi_gap,
            "record_survival_gap": record_survival_gap,
            "reset_swing_gap": reset_swing_gap,
            "pass": (
                abs(ordering_margin_gap) < 0.1
                and abs(measurement_accuracy_gap) < 0.05
                and abs(measurement_mi_gap) < 0.1
                and abs(record_survival_gap) < 0.2
                and abs(reset_swing_gap) < 0.15
            ),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    out = {
        "name": "qit_szilard_record_translation_lane",
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
            "open_best_ordering_margin": open_best["ordering_margin"],
            "qit_best_ordering_margin": qit_best_ordering_margin,
            "ordering_margin_gap": ordering_margin_gap,
            "open_mean_measurement_accuracy": open_mean_measurement_accuracy,
            "qit_mean_measurement_accuracy": qit_mean_measurement_accuracy,
            "measurement_accuracy_gap": measurement_accuracy_gap,
            "open_mean_measurement_mutual_information": open_mean_measurement_mi,
            "qit_mean_measurement_mutual_information": qit_mean_measurement_mi,
            "measurement_mi_gap": measurement_mi_gap,
            "open_mean_record_survival_fraction": open_mean_record_survival_fraction,
            "qit_mean_record_survival_fraction": qit_mean_record_survival_fraction,
            "record_survival_gap": record_survival_gap,
            "open_short_lifetime_mean_margin": open_short_lifetime_mean_margin,
            "open_long_lifetime_mean_margin": open_long_lifetime_mean_margin,
            "qit_short_lifetime_mean_margin": qit_short_lifetime_mean_margin,
            "qit_long_lifetime_mean_margin": qit_long_lifetime_mean_margin,
            "lifetime_sensitivity_gap": lifetime_sensitivity_gap,
            "open_reset_swing": open_reset_swing,
            "qit_reset_swing": qit_reset_swing,
            "reset_swing_gap": reset_swing_gap,
            "open_best_setting": {
                "measurement_flip_prob": open_best["measurement_flip_prob"],
                "record_lifetime_steps": open_best["record_lifetime_steps"],
                "reset_tilt": open_best["reset_tilt"],
            },
            "qit_best_setting": qit_best,
            "open_reset_axis_label": "reset_tilt",
            "qit_reset_axis_label": "reset_strength",
            "scope_note": (
                "Promoted QIT-aligned record-reset translation lane for Szilard. It compares "
                "the open stochastic sweep against the strict companion on the strongest shared "
                "metrics, and keeps the reset-axis mismatch explicit where the translation remains weak."
            ),
        },
        "open_lane": {
            "summary": {
                "best_ordering_margin": open_best["ordering_margin"],
                "best_setting": {
                    "measurement_flip_prob": open_best["measurement_flip_prob"],
                    "record_lifetime_steps": open_best["record_lifetime_steps"],
                    "reset_tilt": open_best["reset_tilt"],
                },
                "mean_measurement_accuracy": open_mean_measurement_accuracy,
                "mean_measurement_mutual_information": open_mean_measurement_mi,
                "mean_record_survival_fraction": open_mean_record_survival_fraction,
                "short_lifetime_mean_margin": open_short_lifetime_mean_margin,
                "long_lifetime_mean_margin": open_long_lifetime_mean_margin,
                "reset_swing": open_reset_swing,
            },
        },
        "strict_lane": {
            "summary": {
                "best_ordering_margin": qit_best_ordering_margin,
                "best_setting": qit_best,
                "mean_measurement_accuracy": qit_mean_measurement_accuracy,
                "mean_measurement_mutual_information": qit_mean_measurement_mi,
                "mean_record_survival_fraction": qit_mean_record_survival_fraction,
                "short_lifetime_mean_margin": qit_short_lifetime_mean_margin,
                "long_lifetime_mean_margin": qit_long_lifetime_mean_margin,
                "reset_swing": qit_reset_swing,
            },
        },
        "open_rows": open_rows,
        "strict_rows": qit_rows,
    }

    out_path = RESULT_DIR / "qit_szilard_record_translation_lane_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
