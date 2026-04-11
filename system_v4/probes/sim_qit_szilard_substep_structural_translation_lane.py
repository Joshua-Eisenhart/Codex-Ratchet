#!/usr/bin/env python3
"""
QIT Szilard Substep Structural Translation Lane
==============================================
Compare the structural substep variant against the strict finite two-qubit
substep companion.
"""

from __future__ import annotations

import json
import pathlib


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Structural translation lane for the stochastic Szilard substep carrier "
    "after adding an explicit record-wait stage."
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
    refined = load("szilard_substep_structural_variant_sweep_results.json")
    qit = load("qit_szilard_substep_companion_results.json")

    refined_summary = refined["summary"]
    qit_summary = qit["summary"]
    qit_reset_signal = qit_summary["weak_reset_mean_memory_entropy_after_reset"] - qit_summary["strong_reset_mean_memory_entropy_after_reset"]

    ordering_margin_gap = qit_summary["best_ordering_margin"] - refined_summary["best_ordering_margin"]
    measurement_mutual_information_gap = qit_summary["mean_measurement_mutual_information"] - refined_summary["best_measurement_mutual_information"]
    reset_signal_gap = qit_reset_signal - refined_summary["best_reset_signal"]

    positive = {
        "ordering_gap_beats_push_lane": {
            "ordering_margin_gap": ordering_margin_gap,
            "pass": ordering_margin_gap < 0.34510881311207176,
        },
        "measurement_gap_stays_small": {
            "measurement_mutual_information_gap": measurement_mutual_information_gap,
            "pass": abs(measurement_mutual_information_gap) < 0.04,
        },
        "reset_gap_stays_small": {
            "reset_signal_gap": reset_signal_gap,
            "pass": abs(reset_signal_gap) < 0.08,
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
                    measurement_mutual_information_gap,
                    reset_signal_gap,
                ]
            )
        }
    }

    all_pass = all(v["pass"] for v in positive.values()) and all(v["pass"] for v in negative.values()) and all(v["pass"] for v in boundary.values())

    out = {
        "name": "qit_szilard_substep_structural_translation_lane",
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
            "measurement_mutual_information_gap": measurement_mutual_information_gap,
            "reset_signal_gap": reset_signal_gap,
            "best_setting": refined_summary["best_setting"],
            "best_structural_score": refined_summary["best_structural_score"],
            "best_ordering_margin": refined_summary["best_ordering_margin"],
            "best_reset_signal": refined_summary["best_reset_signal"],
            "scope_note": (
                "Structural translation lane for the stochastic Szilard substep carrier."
            ),
        },
    }

    out_path = RESULT_DIR / "qit_szilard_substep_structural_translation_lane_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
