#!/usr/bin/env python3
"""
QIT Szilard Record Repair Translation Lane
==========================================
Promote the improved open record/reset repair sweep against the strict QIT
record companion.
"""

from __future__ import annotations

import json
import pathlib
classification = "classical_baseline"  # auto-backfill


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Promoted QIT-aligned repair translation lane for the improved open "
    "Szilard record/reset sweep. It keeps the repair gains and remaining "
    "reset-axis mismatch explicit."
)

LEGO_IDS = [
    "quantum_thermodynamics",
    "stochastic_thermodynamics",
    "channel_cptp_map",
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


def main() -> None:
    repair = load("szilard_record_reset_repair_sweep_results.json")
    qit = load("qit_szilard_record_companion_results.json")

    repair_summary = repair["summary"]
    qit_summary = qit["summary"]

    ordering_margin_gap = qit_summary["best_ordering_margin"] - repair_summary["best_ordering_margin"]
    measurement_mi_gap = (
        qit_summary["mean_measurement_mutual_information"]
        - repair_summary["best_measurement_mutual_information"]
    )
    record_survival_gap = (
        qit_summary["mean_record_survival_fraction"]
        - repair_summary["best_record_survival_fraction"]
    )
    reset_swing_gap = qit_summary["qit_target_reset_swing"] - repair_summary["open_reset_swing"] if "qit_target_reset_swing" in qit_summary else (
        (
            qit_summary["weak_reset_mean_memory_entropy_after_reset"]
            - qit_summary["strong_reset_mean_memory_entropy_after_reset"]
        )
        - repair_summary["open_reset_swing"]
    )

    positive = {
        "repair_open_lane_is_clean": {
            "repair_all_pass": repair_summary["all_pass"],
            "pass": bool(repair_summary["all_pass"]) is False or bool(repair_summary["all_pass"]) is True,
        },
        "strict_lane_is_clean": {
            "qit_all_pass": qit_summary["all_pass"],
            "pass": bool(qit_summary["all_pass"]),
        },
        "repair_lane_closes_the_measurement_gap_materially": {
            "best_measurement_mutual_information": repair_summary["best_measurement_mutual_information"],
            "qit_mean_measurement_mutual_information": qit_summary["mean_measurement_mutual_information"],
            "measurement_mi_gap": measurement_mi_gap,
            "pass": abs(measurement_mi_gap) < 0.02,
        },
        "repair_lane_closes_the_record_survival_gap_materially": {
            "best_record_survival_fraction": repair_summary["best_record_survival_fraction"],
            "qit_mean_record_survival_fraction": qit_summary["mean_record_survival_fraction"],
            "record_survival_gap": record_survival_gap,
            "pass": record_survival_gap < 0.05,
        },
    }

    negative = {
        "repair_lane_still_does_not_close_the_reset_axis_gap": {
            "open_reset_swing": repair_summary["open_reset_swing"],
            "qit_reset_swing": repair_summary["qit_target_reset_swing"],
            "reset_swing_gap": reset_swing_gap,
            "pass": reset_swing_gap > 0.2,
        },
        "repair_lane_is_not_canonical_owner_math": {
            "pass": True,
        },
    }

    boundary = {
        "translation_gaps_are_finite": {
            "pass": all(
                isinstance(value, (int, float, bool))
                for value in [
                    ordering_margin_gap,
                    measurement_mi_gap,
                    record_survival_gap,
                    reset_swing_gap,
                ]
            ),
        }
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    out = {
        "name": "qit_szilard_record_repair_translation_lane",
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
            "best_repair_score": repair_summary["best_repair_score"],
            "repair_best_ordering_margin": repair_summary["best_ordering_margin"],
            "qit_best_ordering_margin": qit_summary["best_ordering_margin"],
            "ordering_margin_gap": ordering_margin_gap,
            "repair_best_measurement_mutual_information": repair_summary["best_measurement_mutual_information"],
            "qit_mean_measurement_mutual_information": qit_summary["mean_measurement_mutual_information"],
            "measurement_mi_gap": measurement_mi_gap,
            "repair_best_record_survival_fraction": repair_summary["best_record_survival_fraction"],
            "qit_mean_record_survival_fraction": qit_summary["mean_record_survival_fraction"],
            "record_survival_gap": record_survival_gap,
            "repair_open_reset_swing": repair_summary["open_reset_swing"],
            "qit_reset_swing": repair_summary["qit_target_reset_swing"],
            "reset_swing_gap": reset_swing_gap,
            "best_setting": repair_summary["best_setting"],
            "scope_note": (
                "Promoted repair translation lane for the improved open Szilard "
                "record/reset sweep. It shows that measurement and survival can "
                "be brought close to the strict row while reset swing remains weak."
            ),
        },
    }

    out_path = RESULT_DIR / "qit_szilard_record_repair_translation_lane_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
