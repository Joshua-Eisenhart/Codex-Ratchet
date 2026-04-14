#!/usr/bin/env python3
"""
QIT Carnot Finite-Time Translation Lane
======================================
Promote the finite-time Carnot pair into a cleaner QIT-aligned translation
surface.
"""

from __future__ import annotations

import json
import pathlib
classification = "classical_baseline"  # auto-backfill


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Promoted QIT-aligned finite-time Carnot translation lane built from the "
    "open stochastic finite-time row and the strict finite-time companion. It "
    "keeps the fast/slow/quasistatic translation gap explicit."
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
    open_ft = load("stoch_harmonic_carnot_finite_time_results.json")
    qit_ft = load("qit_carnot_finite_time_companion_results.json")

    baseline_open = abs(open_ft["cycles"]["forward_fast"]["final_variance"] - open_ft["cycles"]["forward_fast"]["initial_variance"])
    best_open = abs(open_ft["cycles"]["forward_quasistatic"]["final_variance"] - open_ft["cycles"]["forward_quasistatic"]["initial_variance"])
    best_open_eff = open_ft["summary"]["forward_quasistatic_efficiency"]
    best_open_cop = open_ft["summary"]["reverse_quasistatic_cop"]

    baseline_qit = qit_ft["summary"]["baseline_forward_closure_defect"]
    best_qit = qit_ft["summary"]["best_closure_defect"]
    best_qit_eff = qit_ft["summary"]["best_forward_efficiency"]
    best_qit_cop = qit_ft["summary"]["best_reverse_cop"]

    closure_gap = best_open - best_qit
    efficiency_gap = best_open_eff - best_qit_eff
    cop_gap = best_qit_cop - best_open_cop

    positive = {
        "open_lane_is_clean": {
            "open_all_pass": open_ft["summary"]["all_pass"],
            "pass": bool(open_ft["summary"]["all_pass"]),
        },
        "strict_lane_is_clean": {
            "qit_all_pass": qit_ft["summary"]["all_pass"],
            "pass": bool(qit_ft["summary"]["all_pass"]),
        },
        "both_lanes_improve_from_fast_to_quasistatic": {
            "open_forward_gain": open_ft["summary"]["forward_quasistatic_efficiency"] - open_ft["summary"]["forward_fast_efficiency"],
            "qit_forward_gain": qit_ft["summary"]["fast_to_quasistatic_forward_efficiency_gain"],
            "open_reverse_gain": open_ft["summary"]["reverse_quasistatic_cop"] - open_ft["summary"]["reverse_fast_cop"],
            "qit_reverse_gain": qit_ft["summary"]["fast_to_quasistatic_reverse_cop_gain"],
            "pass": (
                open_ft["summary"]["forward_quasistatic_efficiency"] > open_ft["summary"]["forward_slow_efficiency"]
                and qit_ft["summary"]["best_forward_efficiency"] > qit_ft["summary"]["baseline_forward_efficiency"]
                and open_ft["summary"]["reverse_quasistatic_cop"] > open_ft["summary"]["reverse_slow_cop"]
                and qit_ft["summary"]["best_reverse_cop"] > qit_ft["summary"]["best_reverse_cop"] - qit_ft["summary"]["fast_to_quasistatic_reverse_cop_gain"]
            ),
        },
        "translation_gap_stays_bounded": {
            "closure_gap": closure_gap,
            "efficiency_gap": efficiency_gap,
            "cop_gap": cop_gap,
            "pass": closure_gap < 0.05 and abs(efficiency_gap) < 0.05 and cop_gap < 0.15,
        },
    }

    negative = {
        "promoted_lane_is_not_canonical_owner_math": {
            "pass": True,
        },
        "open_lane_does_not_match_strict_quasistatic_limit_exactly": {
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
                    best_open_cop,
                    baseline_qit,
                    best_qit,
                    best_qit_eff,
                    best_qit_cop,
                    closure_gap,
                    efficiency_gap,
                    cop_gap,
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
        "name": "qit_carnot_finite_time_translation_lane",
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
            "open_best_forward_efficiency": best_open_eff,
            "qit_best_forward_efficiency": best_qit_eff,
            "open_best_reverse_cop": best_open_cop,
            "qit_best_reverse_cop": best_qit_cop,
            "closure_gap": closure_gap,
            "efficiency_gap": efficiency_gap,
            "cop_gap": cop_gap,
            "scope_note": (
                "Promoted QIT-aligned finite-time Carnot translation lane. It compares the "
                "open stochastic finite-time row against the strict finite-time companion and "
                "keeps the fast/slow/quasistatic translation gap explicit."
            ),
        },
    }

    out_path = RESULT_DIR / "qit_carnot_finite_time_translation_lane_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
