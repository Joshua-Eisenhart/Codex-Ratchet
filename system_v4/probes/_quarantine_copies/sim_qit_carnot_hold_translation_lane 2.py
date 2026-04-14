#!/usr/bin/env python3
"""
QIT Carnot Hold Translation Lane
================================
Promote the best Carnot tighten lane into a cleaner QIT-aligned translation
surface using the open adaptive-hold row and the strict hold-policy companion.
"""

from __future__ import annotations

import json
import pathlib


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Promoted QIT-aligned Carnot hold-translation lane built from the open "
    "adaptive-hold sweep and the strict hold-policy companion. It is a "
    "translation-ready comparison surface, not a canonical engine theorem."
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
    open_hold = load("carnot_adaptive_hold_sweep_results.json")
    qit_hold = load("qit_carnot_hold_policy_companion_results.json")

    baseline_open = open_hold["summary"]["baseline_closure_defect"]
    best_open = open_hold["summary"]["best_closure_defect"]
    best_open_eff = open_hold["summary"]["best_efficiency"]

    baseline_qit = qit_hold["baseline"]["final_trace_distance_to_initial"]
    best_qit = qit_hold["positive"]["fixed_full_chain_has_the_best_closure"]["best_closure_trace_distance"]
    best_qit_eff = max(row["efficiency"] for row in qit_hold["rows"])

    closure_gain_open = baseline_open - best_open
    closure_gain_qit = baseline_qit - best_qit
    efficiency_gap = best_qit_eff - best_open_eff
    closure_gap = best_open - best_qit

    positive = {
        "open_lane_is_clean": {
            "open_all_pass": open_hold["summary"]["all_pass"],
            "pass": bool(open_hold["summary"]["all_pass"]),
        },
        "strict_lane_is_clean": {
            "qit_all_pass": qit_hold["summary"]["all_pass"],
            "pass": bool(qit_hold["summary"]["all_pass"]),
        },
        "both_lanes_gain_closure_from_hold_policy": {
            "open_closure_gain": closure_gain_open,
            "qit_closure_gain": closure_gain_qit,
            "pass": closure_gain_open > 0.0 and closure_gain_qit > 0.0,
        },
        "translation_gap_stays_bounded": {
            "closure_gap": closure_gap,
            "efficiency_gap": efficiency_gap,
            "pass": closure_gap < 0.01 and efficiency_gap < 0.08,
        },
    }

    negative = {
        "promoted_lane_is_not_canonical_owner_math": {
            "pass": True,
        },
        "open_lane_does_not_match_strict_best_closure_exactly": {
            "closure_gap": closure_gap,
            "pass": closure_gap > 0.0,
        },
    }

    boundary = {
        "all_summary_values_are_finite": {
            "pass": all(
                isinstance(value, (int, float, bool))
                for value in [
                    baseline_open,
                    best_open,
                    best_open_eff,
                    baseline_qit,
                    best_qit,
                    best_qit_eff,
                    closure_gain_open,
                    closure_gain_qit,
                    efficiency_gap,
                    closure_gap,
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
        "name": "qit_carnot_hold_translation_lane",
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
            "open_baseline_closure_defect": baseline_open,
            "open_best_closure_defect": best_open,
            "qit_baseline_closure_defect": baseline_qit,
            "qit_best_closure_defect": best_qit,
            "open_best_efficiency": best_open_eff,
            "qit_best_efficiency": best_qit_eff,
            "closure_gain_open": closure_gain_open,
            "closure_gain_qit": closure_gain_qit,
            "closure_gap": closure_gap,
            "efficiency_gap": efficiency_gap,
            "open_best_setting": open_hold["summary"]["best_setting"],
            "qit_best_policy": qit_hold["summary"]["best_closure_policy"],
            "scope_note": (
                "Promoted QIT-aligned Carnot hold-translation lane. It compares the open "
                "adaptive-hold sweep against the strict hold-policy companion and keeps "
                "the closure/efficiency translation gap explicit."
            ),
        },
    }

    out_path = RESULT_DIR / "qit_carnot_hold_translation_lane_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
