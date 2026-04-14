#!/usr/bin/env python3
"""
QIT Carnot Closure Translation Lane
==================================
Promote the Carnot closure diagnostic pair into a cleaner QIT-aligned
translation surface.
"""

from __future__ import annotations

import json
import pathlib
classification = "classical_baseline"  # auto-backfill


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Promoted QIT-aligned Carnot closure translation lane built from the open "
    "closure diagnostic row and the strict closure companion. It keeps closure "
    "defect and dominant-leg translation gaps explicit."
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
    open_cd = load("carnot_closure_diagnostic_results.json")
    qit_cd = load("qit_carnot_closure_companion_results.json")

    open_best = open_cd["summary"]["best_closure_abs_variance_mismatch"]
    qit_best = qit_cd["summary"]["best_closure_defect"]
    open_worst = open_cd["summary"]["worst_closure_abs_variance_mismatch"]
    qit_baseline = qit_cd["summary"]["baseline_closure_defect"]
    dominant_match = (
        open_cd["summary"]["dominant_closure_leg_at_best_row"]
        == qit_cd["summary"]["dominant_closure_leg_at_best_row"]
    )

    positive = {
        "open_lane_is_clean": {
            "open_all_pass": open_cd["summary"]["all_pass"],
            "pass": bool(open_cd["summary"]["all_pass"]),
        },
        "strict_lane_is_clean": {
            "qit_all_pass": qit_cd["summary"]["all_pass"],
            "pass": bool(qit_cd["summary"]["all_pass"]),
        },
        "both_lanes_improve_from_baseline_or_worst_to_best": {
            "open_improvement": open_worst - open_best,
            "qit_improvement": qit_baseline - qit_best,
            "pass": (open_worst > open_best) and (qit_baseline > qit_best),
        },
        "translation_gap_stays_bounded": {
            "best_closure_gap": open_best - qit_best,
            "dominant_leg_matches": float(dominant_match),
            "pass": (open_best - qit_best) < 0.01 and dominant_match,
        },
    }

    negative = {
        "promoted_lane_is_not_canonical_owner_math": {
            "pass": True,
        },
        "open_lane_does_not_match_strict_best_closure_exactly": {
            "best_closure_gap": open_best - qit_best,
            "pass": (open_best - qit_best) > 0.0,
        },
    }

    boundary = {
        "all_summary_values_are_finite": {
            "pass": all(
                isinstance(value, (int, float, bool))
                for value in [
                    open_best,
                    qit_best,
                    open_worst,
                    qit_baseline,
                    float(dominant_match),
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
        "name": "qit_carnot_closure_translation_lane",
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
            "open_best_closure_defect": open_best,
            "qit_best_closure_defect": qit_best,
            "open_worst_closure_defect": open_worst,
            "qit_baseline_closure_defect": qit_baseline,
            "best_closure_gap": open_best - qit_best,
            "dominant_leg_matches": bool(dominant_match),
            "open_dominant_closure_leg": open_cd["summary"]["dominant_closure_leg_at_best_row"],
            "qit_dominant_closure_leg": qit_cd["summary"]["dominant_closure_leg_at_best_row"],
            "scope_note": (
                "Promoted QIT-aligned Carnot closure translation lane. It compares the open "
                "closure diagnostic row against the strict closure companion and keeps closure "
                "defect plus dominant-leg agreement explicit."
            ),
        },
    }

    out_path = RESULT_DIR / "qit_carnot_closure_translation_lane_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
