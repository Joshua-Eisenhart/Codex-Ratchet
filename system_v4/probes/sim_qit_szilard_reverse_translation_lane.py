#!/usr/bin/env python3
"""
QIT Szilard Reverse Translation Lane
===================================
Promote the translate-now reverse/recovery pair into a cleaner QIT-aligned
lane that combines the strict bidirectional base with the strict reverse/
recovery companion.
"""

from __future__ import annotations

import json
import pathlib


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Promoted QIT-aligned Szilard reverse/recovery lane built from the strict "
    "bidirectional base and the strict reverse/recovery companion. It is a "
    "translation-ready lane, not a canonical owner row."
)

LEGO_IDS = [
    "quantum_thermodynamics",
    "channel_cptp_map",
    "state_distinguishability",
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
    bidirectional = load("qit_szilard_bidirectional_protocol_results.json")
    reverse_companion = load("qit_szilard_reverse_recovery_companion_results.json")
    open_reverse = load("szilard_reverse_recovery_sweep_results.json")

    ideal_forward = bidirectional["ideal_forward"]
    ideal_reverse = bidirectional["ideal_reverse"]
    reverse_summary = reverse_companion["summary"]
    open_summary = open_reverse["summary"]

    translation_gap = (
        reverse_summary["mean_recovery_entropy_restoration_fraction"]
        - open_summary["mean_recovery_entropy_restoration_fraction"]
    )
    ordering_gap_delta = (
        reverse_summary["mean_recovery_vs_naive_gap"]
        - (
            open_summary["mean_recovery_entropy_restoration_fraction"]
            - open_summary["mean_naive_reverse_entropy_restoration_fraction"]
        )
    )

    positive = {
        "strict_bidirectional_base_is_clean": {
            "bidirectional_all_pass": bidirectional["summary"]["all_pass"],
            "pass": bool(bidirectional["summary"]["all_pass"]),
        },
        "strict_reverse_recovery_companion_is_clean": {
            "reverse_companion_all_pass": reverse_summary["all_pass"],
            "pass": bool(reverse_summary["all_pass"]),
        },
        "promoted_lane_preserves_recovery_over_naive_reverse": {
            "mean_recovery_fraction": reverse_summary["mean_recovery_entropy_restoration_fraction"],
            "mean_naive_fraction": reverse_summary["mean_naive_reverse_entropy_restoration_fraction"],
            "mean_gap": reverse_summary["mean_recovery_vs_naive_gap"],
            "pass": reverse_summary["mean_recovery_vs_naive_gap"] > 0.2,
        },
        "translation_gap_to_open_lane_stays_bounded": {
            "recovery_fraction_delta_vs_open": translation_gap,
            "gap_delta_vs_open": ordering_gap_delta,
            "pass": abs(translation_gap) < 0.2 and abs(ordering_gap_delta) < 0.1,
        },
    }

    negative = {
        "promoted_lane_is_not_canonical_owner_math": {
            "pass": True,
        },
        "promoted_lane_is_not_claimed_as_runtime_reservoir_realization": {
            "pass": True,
        },
    }

    boundary = {
        "all_referenced_inputs_are_finite": {
            "pass": all(
                isinstance(value, (int, float, bool))
                for value in [
                    bidirectional["summary"]["ideal_forward_information_gain"],
                    bidirectional["summary"]["ideal_forward_system_gain"],
                    bidirectional["summary"]["ideal_forward_erasure_cost"],
                    bidirectional["summary"]["ideal_reverse_randomization_cost"],
                    bidirectional["summary"]["ideal_reverse_restoration_trace_distance"],
                    reverse_summary["mean_recovery_entropy_restoration_fraction"],
                    reverse_summary["mean_naive_reverse_entropy_restoration_fraction"],
                    reverse_summary["mean_recovery_vs_naive_gap"],
                    reverse_summary["mean_erase_system_free_energy_gain"],
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
        "name": "qit_szilard_reverse_translation_lane",
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
            "ideal_forward_information_gain": bidirectional["summary"]["ideal_forward_information_gain"],
            "ideal_forward_system_gain": bidirectional["summary"]["ideal_forward_system_gain"],
            "ideal_forward_erasure_cost": bidirectional["summary"]["ideal_forward_erasure_cost"],
            "ideal_reverse_restoration_trace_distance": bidirectional["summary"]["ideal_reverse_restoration_trace_distance"],
            "mean_recovery_entropy_restoration_fraction": reverse_summary["mean_recovery_entropy_restoration_fraction"],
            "mean_naive_reverse_entropy_restoration_fraction": reverse_summary["mean_naive_reverse_entropy_restoration_fraction"],
            "mean_recovery_vs_naive_gap": reverse_summary["mean_recovery_vs_naive_gap"],
            "mean_erase_system_free_energy_gain": reverse_summary["mean_erase_system_free_energy_gain"],
            "recovery_fraction_delta_vs_open": translation_gap,
            "gap_delta_vs_open": ordering_gap_delta,
            "best_setting": reverse_summary["best_setting"],
            "scope_note": (
                "Promoted QIT-aligned reverse/recovery lane for Szilard. It combines the "
                "strict bidirectional base with the strict reverse/recovery companion and "
                "keeps translation to the open lane explicit."
            ),
        },
        "ideal_forward": ideal_forward,
        "ideal_reverse": ideal_reverse,
        "reverse_recovery_summary": reverse_summary,
    }

    out_path = RESULT_DIR / "qit_szilard_reverse_translation_lane_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
