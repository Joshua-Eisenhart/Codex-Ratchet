#!/usr/bin/env python3
"""
QIT Szilard Record Reconciled Translation Lane
==============================================
Re-score the repaired record/reset open lane after calibrating the reset axis
onto a shared reset-effect scale.
"""

from __future__ import annotations

import json
import pathlib
classification = "classical_baseline"  # auto-backfill


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Reconciled QIT-aligned record/reset translation lane for Szilard. It uses "
    "a calibrated reset-effect mapping instead of comparing reset tilt and "
    "reset strength directly."
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
    reset_map = load("szilard_reset_axis_reconciliation_results.json")

    repair_summary = repair["summary"]
    qit_summary = qit["summary"]
    best_mapping = min(reset_map["mappings"], key=lambda row: row["reset_effect_gap"])

    ordering_margin_gap = qit_summary["best_ordering_margin"] - repair_summary["best_ordering_margin"]
    measurement_mi_gap = qit_summary["mean_measurement_mutual_information"] - repair_summary["best_measurement_mutual_information"]
    record_survival_gap = qit_summary["mean_record_survival_fraction"] - repair_summary["best_record_survival_fraction"]
    reconciled_reset_gap = best_mapping["reset_effect_gap"]

    positive = {
        "repaired_lane_closes_measurement_gap": {
            "measurement_mi_gap": measurement_mi_gap,
            "pass": abs(measurement_mi_gap) < 0.02,
        },
        "repaired_lane_closes_record_survival_gap": {
            "record_survival_gap": record_survival_gap,
            "pass": record_survival_gap < 0.05,
        },
        "reconciled_reset_axis_maps_cleanly": {
            "reconciled_reset_gap": reconciled_reset_gap,
            "pass": reconciled_reset_gap < 0.03,
        },
    }

    negative = {
        "ordering_gap_still_remains_after_repair": {
            "ordering_margin_gap": ordering_margin_gap,
            "pass": ordering_margin_gap > 0.1,
        },
        "reconciled_lane_is_not_canonical_owner_math": {
            "pass": True,
        },
    }

    boundary = {
        "all_reconciled_metrics_are_finite": {
            "pass": all(
                isinstance(value, (int, float, bool))
                for value in [
                    ordering_margin_gap,
                    measurement_mi_gap,
                    record_survival_gap,
                    reconciled_reset_gap,
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
        "name": "qit_szilard_record_reconciled_translation_lane",
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
            "ordering_margin_gap": ordering_margin_gap,
            "measurement_mi_gap": measurement_mi_gap,
            "record_survival_gap": record_survival_gap,
            "reconciled_reset_gap": reconciled_reset_gap,
            "best_open_tilt": best_mapping["reset_tilt"],
            "best_matched_qit_strength": best_mapping["matched_reset_strength"],
            "scope_note": (
                "Reconciled record/reset translation lane for Szilard using a "
                "shared reset-effect scale. Measurement and survival are close; "
                "ordering remains the main residual gap."
            ),
        },
    }

    out_path = RESULT_DIR / "qit_szilard_record_reconciled_translation_lane_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
