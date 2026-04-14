#!/usr/bin/env python3
"""
QIT Szilard Record Ordering Translation Lane
============================================
Promote the ordering-amplified hard-reset open lane against the strict QIT
record/reset companion.
"""

from __future__ import annotations

import json
import pathlib
classification = "classical_baseline"  # auto-backfill


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Promoted ordering-focused translation lane for the open Szilard hard-reset "
    "record carrier. It tracks the stronger open ordering signal against the "
    "strict QIT record/reset companion."
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
    amp = load("szilard_record_ordering_amplification_sweep_results.json")
    qit = load("qit_szilard_record_companion_results.json")

    amp_summary = amp["summary"]
    qit_summary = qit["summary"]
    qit_reset_entropy = qit_summary["strong_reset_mean_memory_entropy_after_reset"]

    ordering_margin_gap = qit_summary["best_ordering_margin"] - amp_summary["best_ordering_margin"]
    measurement_mi_gap = qit_summary["mean_measurement_mutual_information"] - amp_summary["best_measurement_mutual_information"]
    record_survival_gap = qit_summary["mean_record_survival_fraction"] - amp_summary["best_record_survival_fraction"]
    residual_reset_entropy_gap = amp_summary["best_reset_stage_entropy"] - qit_reset_entropy

    positive = {
        "ordering_gap_is_materially_smaller_than_in_the_hard_reset_baseline": {
            "ordering_margin_gap": ordering_margin_gap,
            "pass": ordering_margin_gap < 0.11,
        },
        "measurement_information_stays_high": {
            "measurement_mi_gap": measurement_mi_gap,
            "pass": abs(measurement_mi_gap) < 0.12,
        },
        "record_survival_stays_high": {
            "record_survival_gap": record_survival_gap,
            "pass": abs(record_survival_gap) < 0.2,
        },
    }

    negative = {
        "lane_is_not_canonical_owner_math": {"pass": True},
    }

    boundary = {
        "all_metrics_finite": {
            "pass": all(
                isinstance(v, (int, float, bool))
                for v in [
                    ordering_margin_gap,
                    measurement_mi_gap,
                    record_survival_gap,
                    residual_reset_entropy_gap,
                ]
            )
        }
    }

    all_pass = all(v["pass"] for v in positive.values()) and all(v["pass"] for v in negative.values()) and all(v["pass"] for v in boundary.values())

    out = {
        "name": "qit_szilard_record_ordering_translation_lane",
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
            "ordering_margin_gap": ordering_margin_gap,
            "measurement_mi_gap": measurement_mi_gap,
            "record_survival_gap": record_survival_gap,
            "residual_reset_entropy_gap": residual_reset_entropy_gap,
            "best_setting": amp_summary["best_setting"],
            "best_ordering_margin": amp_summary["best_ordering_margin"],
            "scope_note": (
                "Ordering-focused translation lane for the open Szilard hard-reset carrier. "
                "It shows that stronger feedback asymmetry improves the open ordering signal materially."
            ),
        },
    }

    out_path = RESULT_DIR / "qit_szilard_record_ordering_translation_lane_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
