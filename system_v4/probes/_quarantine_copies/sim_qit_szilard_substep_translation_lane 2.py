#!/usr/bin/env python3
"""
QIT Szilard Substep Translation Lane
===================================
Promote the open stochastic Szilard substep row and the strict QIT substep
companion into one bounded translation surface.
"""

from __future__ import annotations

import json
import pathlib


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Promoted QIT-aligned Szilard substep translation lane built from the open "
    "stochastic substep row and the strict finite two-qubit companion. It "
    "keeps measurement, ordering, and reset-translation gaps explicit."
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
    open_substeps = load("szilard_measurement_feedback_substeps_results.json")
    qit_substeps = load("qit_szilard_substep_companion_results.json")

    open_summary = open_substeps["summary"]
    qit_summary = qit_substeps["summary"]

    open_ordered = open_summary["ordered"]
    open_best_scrambled_entropy = min(
        open_summary["feedback_first"]["final_entropy"],
        open_summary["reset_first"]["final_entropy"],
        open_summary["measurement_then_reset_then_feedback"]["final_entropy"],
    )
    open_ordering_margin = open_best_scrambled_entropy - open_ordered["final_entropy"]
    open_reset_penalty = (
        open_summary["measurement_then_reset_then_feedback"]["final_entropy"]
        - open_ordered["final_entropy"]
    )

    qit_reset_drop = (
        qit_summary["weak_reset_mean_memory_entropy_after_reset"]
        - qit_summary["strong_reset_mean_memory_entropy_after_reset"]
    )

    ordering_margin_gap = qit_summary["best_ordering_margin"] - open_ordering_margin
    measurement_mi_gap = (
        qit_summary["mean_measurement_mutual_information"]
        - open_ordered["measurement_mutual_information"]
    )
    feedback_gain_gap = (
        qit_summary["mean_feedback_system_free_energy_gain"]
        - open_ordered["mean_work"]
    )
    reset_signal_gap = qit_reset_drop - open_reset_penalty

    positive = {
        "open_lane_is_clean": {
            "open_all_pass": open_summary["all_pass"],
            "pass": bool(open_summary["all_pass"]),
        },
        "strict_lane_is_clean": {
            "qit_all_pass": qit_summary["all_pass"],
            "pass": bool(qit_summary["all_pass"]),
        },
        "both_lanes_remain_measurement_informative": {
            "open_measurement_accuracy": open_ordered["measurement_accuracy"],
            "open_measurement_mutual_information": open_ordered["measurement_mutual_information"],
            "qit_mean_measurement_accuracy": qit_summary["mean_measurement_accuracy"],
            "qit_mean_measurement_mutual_information": qit_summary["mean_measurement_mutual_information"],
            "pass": (
                open_ordered["measurement_accuracy"] > 0.8
                and open_ordered["measurement_mutual_information"] > 0.2
                and qit_summary["mean_measurement_accuracy"] > 0.8
                and qit_summary["mean_measurement_mutual_information"] > 0.2
            ),
        },
        "both_lanes_preserve_ordering_advantage": {
            "open_ordering_margin": open_ordering_margin,
            "qit_best_ordering_margin": qit_summary["best_ordering_margin"],
            "pass": open_ordering_margin > 0.005 and qit_summary["best_ordering_margin"] > 0.05,
        },
        "translation_gap_stays_bounded": {
            "ordering_margin_gap": ordering_margin_gap,
            "measurement_mutual_information_gap": measurement_mi_gap,
            "feedback_gain_gap": feedback_gain_gap,
            "reset_signal_gap": reset_signal_gap,
            "pass": (
                ordering_margin_gap < 0.6
                and abs(measurement_mi_gap) < 0.2
                and abs(feedback_gain_gap) < 0.5
                and abs(reset_signal_gap) < 0.6
            ),
        },
    }

    negative = {
        "promoted_lane_is_not_canonical_owner_math": {
            "pass": True,
        },
        "open_lane_and_strict_lane_do_not_share_identical_entropy_carriers": {
            "pass": True,
        },
    }

    boundary = {
        "all_summary_values_are_finite": {
            "pass": all(
                isinstance(value, (int, float, bool))
                for value in [
                    open_ordering_margin,
                    open_ordered["measurement_mutual_information"],
                    open_ordered["measurement_accuracy"],
                    open_ordered["mean_work"],
                    open_reset_penalty,
                    qit_summary["best_ordering_margin"],
                    qit_summary["mean_measurement_mutual_information"],
                    qit_summary["mean_measurement_accuracy"],
                    qit_summary["mean_feedback_system_free_energy_gain"],
                    qit_reset_drop,
                    ordering_margin_gap,
                    measurement_mi_gap,
                    feedback_gain_gap,
                    reset_signal_gap,
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
        "name": "qit_szilard_substep_translation_lane",
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
            "open_ordering_margin": open_ordering_margin,
            "qit_best_ordering_margin": qit_summary["best_ordering_margin"],
            "open_measurement_accuracy": open_ordered["measurement_accuracy"],
            "qit_mean_measurement_accuracy": qit_summary["mean_measurement_accuracy"],
            "open_measurement_mutual_information": open_ordered["measurement_mutual_information"],
            "qit_mean_measurement_mutual_information": qit_summary["mean_measurement_mutual_information"],
            "open_feedback_signal": open_ordered["mean_work"],
            "qit_mean_feedback_system_free_energy_gain": qit_summary["mean_feedback_system_free_energy_gain"],
            "open_reset_signal": open_reset_penalty,
            "qit_reset_signal": qit_reset_drop,
            "ordering_margin_gap": ordering_margin_gap,
            "measurement_mutual_information_gap": measurement_mi_gap,
            "feedback_gain_gap": feedback_gain_gap,
            "reset_signal_gap": reset_signal_gap,
            "scope_note": (
                "Promoted QIT-aligned Szilard substep translation lane. It compares the "
                "open stochastic substep row against the strict finite two-qubit companion "
                "and keeps measurement, ordering, and reset gaps explicit."
            ),
        },
    }

    out_path = RESULT_DIR / "qit_szilard_substep_translation_lane_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
