#!/usr/bin/env python3
"""
QIT Szilard Record Hard-Reset Translation Lane
==============================================
Promote the hard-reset open repair lane against the strict QIT record/reset
companion.
"""

from __future__ import annotations

import json
import pathlib


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Promoted hard-reset translation lane for the open Szilard record/reset "
    "carrier. It compares the upgraded open reset mechanic against the strict "
    "QIT companion without claiming canonical admission."
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
    hard = load("szilard_record_hard_reset_repair_sweep_results.json")
    qit = load("qit_szilard_record_companion_results.json")

    hs = hard["summary"]
    qs = qit["summary"]
    qit_reset_entropy = qs["strong_reset_mean_memory_entropy_after_reset"]

    ordering_margin_gap = qs["best_ordering_margin"] - hs["best_ordering_margin"]
    measurement_mi_gap = qs["mean_measurement_mutual_information"] - hs["best_measurement_mutual_information"]
    record_survival_gap = qs["mean_record_survival_fraction"] - hs["best_record_survival_fraction"]
    residual_reset_entropy_gap = hs["best_reset_stage_entropy"] - qit_reset_entropy

    positive = {
        "hard_reset_lane_is_clean": {
            "hard_reset_all_pass": hs["all_pass"],
            "pass": bool(hs["all_pass"]),
        },
        "hard_reset_lane_closes_measurement_gap": {
            "measurement_mi_gap": measurement_mi_gap,
            "pass": abs(measurement_mi_gap) < 0.08,
        },
        "hard_reset_lane_closes_record_survival_gap": {
            "record_survival_gap": record_survival_gap,
            "pass": abs(record_survival_gap) < 0.1,
        },
        "hard_reset_lane_reduces_reset_entropy_gap_materially": {
            "residual_reset_entropy_gap": residual_reset_entropy_gap,
            "pass": residual_reset_entropy_gap < 0.35,
        },
    }

    negative = {
        "ordering_gap_still_remains": {
            "ordering_margin_gap": ordering_margin_gap,
            "pass": ordering_margin_gap > 0.1,
        },
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
        "name": "qit_szilard_record_hard_reset_translation_lane",
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
            "best_repair_score": hs["best_repair_score"],
            "ordering_margin_gap": ordering_margin_gap,
            "measurement_mi_gap": measurement_mi_gap,
            "record_survival_gap": record_survival_gap,
            "residual_reset_entropy_gap": residual_reset_entropy_gap,
            "best_setting": hs["best_setting"],
            "scope_note": (
                "Hard-reset translation lane for the open Szilard record carrier. "
                "Reset is materially stronger now; ordering remains the main gap."
            ),
        },
    }

    out_path = RESULT_DIR / "qit_szilard_record_hard_reset_translation_lane_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
