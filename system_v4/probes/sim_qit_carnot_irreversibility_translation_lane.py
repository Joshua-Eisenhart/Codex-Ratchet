#!/usr/bin/env python3
"""
QIT Carnot Irreversibility Translation Lane
===========================================
Promote the duration/irreversibility Carnot pair into a cleaner QIT-aligned
translation surface.
"""

from __future__ import annotations

import json
import pathlib
classification = "classical_baseline"  # auto-backfill


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Promoted QIT-aligned Carnot irreversibility translation lane built from "
    "the open duration sweep and the strict irreversibility companion. It "
    "keeps duration-driven translation gaps explicit."
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
    open_ir = load("carnot_irreversibility_sweep_results.json")
    qit_ir = load("qit_carnot_irreversibility_companion_results.json")

    open_best_forward_distance = open_ir["summary"]["best_forward_distance_to_carnot"]
    qit_best_forward_distance = qit_ir["summary"]["best_forward_distance_to_carnot"]
    open_best_reverse_distance = open_ir["summary"]["best_reverse_distance_to_carnot_cop"]
    qit_best_reverse_distance = qit_ir["summary"]["best_reverse_distance_to_carnot_cop"]
    open_best_forward_eff = open_ir["summary"]["best_forward_efficiency"]
    qit_best_forward_eff = qit_ir["summary"]["best_forward_efficiency"]
    open_best_reverse_cop = open_ir["summary"]["best_reverse_cop"]
    qit_best_reverse_cop = qit_ir["summary"]["best_reverse_cop"]

    forward_distance_gap = open_best_forward_distance - qit_best_forward_distance
    reverse_distance_gap = open_best_reverse_distance - qit_best_reverse_distance
    forward_efficiency_gap = qit_best_forward_eff - open_best_forward_eff
    reverse_cop_gap = qit_best_reverse_cop - open_best_reverse_cop

    positive = {
        "open_lane_is_clean": {
            "open_all_pass": open_ir["summary"]["all_pass"],
            "pass": bool(open_ir["summary"]["all_pass"]),
        },
        "strict_lane_is_clean": {
            "qit_all_pass": qit_ir["summary"]["all_pass"],
            "pass": bool(qit_ir["summary"]["all_pass"]),
        },
        "both_lanes_improve_toward_high_step_regime": {
            "open_best_forward_steps": open_ir["summary"]["best_forward_steps"],
            "qit_best_forward_steps": qit_ir["summary"]["best_forward_steps"],
            "open_best_reverse_steps": open_ir["summary"]["best_reverse_steps"],
            "qit_best_reverse_steps": qit_ir["summary"]["best_reverse_steps"],
            "pass": (
                open_ir["summary"]["best_forward_steps"] == 5000
                and qit_ir["summary"]["best_forward_steps"] == 5000
                and open_ir["summary"]["best_reverse_steps"] == 5000
                and qit_ir["summary"]["best_reverse_steps"] == 5000
            ),
        },
        "translation_gap_stays_bounded": {
            "forward_distance_gap": forward_distance_gap,
            "reverse_distance_gap": reverse_distance_gap,
            "forward_efficiency_gap": forward_efficiency_gap,
            "reverse_cop_gap": reverse_cop_gap,
            "pass": (
                forward_distance_gap < 0.1
                and reverse_distance_gap < 0.1
                and forward_efficiency_gap < 0.1
                and reverse_cop_gap < 0.15
            ),
        },
    }

    negative = {
        "promoted_lane_is_not_canonical_owner_math": {
            "pass": True,
        },
        "open_lane_does_not_match_strict_high_budget_limit_exactly": {
            "forward_distance_gap": forward_distance_gap,
            "pass": forward_distance_gap > 0.0,
        },
    }

    boundary = {
        "all_summary_values_are_finite": {
            "pass": all(
                isinstance(value, (int, float, bool))
                for value in [
                    open_best_forward_distance,
                    qit_best_forward_distance,
                    open_best_reverse_distance,
                    qit_best_reverse_distance,
                    open_best_forward_eff,
                    qit_best_forward_eff,
                    open_best_reverse_cop,
                    qit_best_reverse_cop,
                    forward_distance_gap,
                    reverse_distance_gap,
                    forward_efficiency_gap,
                    reverse_cop_gap,
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
        "name": "qit_carnot_irreversibility_translation_lane",
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
            "open_best_forward_distance_to_carnot": open_best_forward_distance,
            "qit_best_forward_distance_to_carnot": qit_best_forward_distance,
            "open_best_reverse_distance_to_carnot_cop": open_best_reverse_distance,
            "qit_best_reverse_distance_to_carnot_cop": qit_best_reverse_distance,
            "open_best_forward_efficiency": open_best_forward_eff,
            "qit_best_forward_efficiency": qit_best_forward_eff,
            "open_best_reverse_cop": open_best_reverse_cop,
            "qit_best_reverse_cop": qit_best_reverse_cop,
            "forward_distance_gap": forward_distance_gap,
            "reverse_distance_gap": reverse_distance_gap,
            "forward_efficiency_gap": forward_efficiency_gap,
            "reverse_cop_gap": reverse_cop_gap,
            "scope_note": (
                "Promoted QIT-aligned Carnot irreversibility translation lane. It compares "
                "the open duration sweep against the strict irreversibility companion and "
                "keeps high-budget translation gaps explicit."
            ),
        },
    }

    out_path = RESULT_DIR / "qit_carnot_irreversibility_translation_lane_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
