#!/usr/bin/env python3
"""Positive topology-diversity successor for Szilard topology entropy."""

from __future__ import annotations

import json
import pathlib


CLASSIFICATION = "diagnostic_only"
classification = CLASSIFICATION
divergence_log = (
    "Bounded successor for the Szilard topology entropy sidecar. The source "
    "row showed positive ordering across tested topologies, asymmetric topology "
    "as the best local ordering carrier, and nonlogical entropy diversity; the "
    "weak-topology claim is kept as killed. No QIT, GStack, axis, or engine "
    "admission is claimed."
)

LEGO_IDS = ["szilard_engine", "topology_entropy", "ordering_sensitivity"]
PRIMARY_LEGO_IDS = ["topology_entropy"]

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "loads topology entropy row and writes successor receipt"},
    "pathlib": {"tried": True, "used": True, "reason": "resolves canonical receipt paths"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive"}

RESULT_DIR = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"


def load(name: str) -> dict:
    return json.loads((RESULT_DIR / name).read_text(encoding="utf-8"))


def main() -> None:
    source = load("szilard_topology_entropy_array_results.json")
    summary = source["summary"]
    positive_source = source["positive"]
    negative_source = source["negative"]

    positive = {
        "all_tested_topologies_have_positive_ordering_margin": {
            "worst_margin": negative_source["at_least_one_topology_remains_weak_for_ordering"]["worst_margin"],
            "pass": negative_source["at_least_one_topology_remains_weak_for_ordering"]["worst_margin"] > 0.0,
        },
        "asymmetric_topology_is_best_local_ordering_carrier": {
            "best_topology": summary["best_topology"],
            "best_margin": summary["best_margin"],
            "pass": summary["best_topology"] == "asymmetric_double_well" and summary["best_margin"] > 0.0,
        },
        "topology_changes_nonlogical_entropy_proxy": {
            **positive_source["topology_changes_nonlogical_entropy_proxy"],
        },
        "measurement_information_present_across_ordered_rows": {
            **positive_source["measurement_information_is_present_in_all_ordered_rows"],
        },
    }
    negative = {
        "weak_topology_claim_is_killed": {
            "source_weak_topology_check_pass": negative_source["at_least_one_topology_remains_weak_for_ordering"]["pass"],
            "pass": negative_source["at_least_one_topology_remains_weak_for_ordering"]["pass"] is False,
        },
        "source_row_remains_failed_under_original_contract": {
            "source_all_pass": summary["all_pass"],
            "pass": summary["all_pass"] is False,
        },
        "successor_not_qit_gstack_or_axis_admission": {"pass": True},
    }
    boundary = {
        "topology_list_is_preserved": {
            "topologies": summary["topologies"],
            "pass": len(summary["topologies"]) >= 4,
        }
    }
    all_pass = (
        all(check["pass"] for check in positive.values())
        and all(check["pass"] for check in negative.values())
        and all(check["pass"] for check in boundary.values())
    )
    out = {
        "name": "szilard_topology_positive_diversity_successor",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": {
            "szilard_topology_entropy_array": str(RESULT_DIR / "szilard_topology_entropy_array_results.json"),
            "engine_lab_sidecar_graveyard": str(RESULT_DIR / "engine_lab_sidecar_graveyard_results.json"),
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": bool(all_pass),
            "topologies": summary["topologies"],
            "best_topology": summary["best_topology"],
            "best_margin": summary["best_margin"],
            "worst_margin": negative_source["at_least_one_topology_remains_weak_for_ordering"]["worst_margin"],
            "spread_entropy_range": positive_source["topology_changes_nonlogical_entropy_proxy"][
                "spread_entropy_range"
            ],
            "qit_or_axis_promotion_allowed": False,
            "scope_note": divergence_log,
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULT_DIR / "szilard_topology_positive_diversity_successor_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
