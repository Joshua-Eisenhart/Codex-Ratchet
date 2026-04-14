#!/usr/bin/env python3
"""
Engine Lab Repair Priority
==========================
Rank repairable open-lab rows by how close they already are to a usable
strict-side translation.
"""

from __future__ import annotations

import json
import pathlib


CLASSIFICATION = "exploratory"
CLASSIFICATION_NOTE = (
    "Controller ranking surface over repairable engine-lab rows. It combines "
    "route class, direct open-vs-QIT pair data, and clean-run status to produce "
    "the next strict-alignment queue."
)

LEGO_IDS = [
    "quantum_thermodynamics",
    "stochastic_thermodynamics",
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


def ratio(a: float, b: float) -> float:
    if b == 0.0:
        return 0.0
    return max(0.0, min(1.0, float(a / b)))


def closeness_score(pair: dict) -> float:
    pair_id = pair["pair_id"]
    if pair_id == "szilard_substep_pair":
        return (
            ratio(pair["open_metrics"]["ordering_margin"], pair["qit_metrics"]["best_ordering_margin"]) * 0.5
            + ratio(pair["open_metrics"]["measurement_mutual_information"], pair["qit_metrics"]["mean_measurement_mutual_information"]) * 0.25
            + ratio(pair["open_metrics"]["reset_penalty"], pair["qit_metrics"]["reset_memory_entropy_drop"]) * 0.25
        )
    if pair_id == "szilard_record_reset_pair":
        return (
            ratio(pair["open_metrics"]["best_ordering_margin"], pair["qit_metrics"]["best_ordering_margin"]) * 0.4
            + ratio(pair["open_metrics"]["long_minus_short_margin"], pair["qit_metrics"]["long_minus_short_margin"]) * 0.3
            + ratio(pair["open_metrics"]["reset_entropy_drop"], pair["qit_metrics"]["reset_entropy_drop"]) * 0.3
        )
    if pair_id == "szilard_record_reset_repair_pair":
        return (
            ratio(pair["open_metrics"]["best_ordering_margin"], pair["qit_metrics"]["best_ordering_margin"]) * 0.3
            + ratio(pair["open_metrics"]["mean_measurement_mutual_information"], pair["qit_metrics"]["mean_measurement_mutual_information"]) * 0.25
            + ratio(pair["open_metrics"]["mean_record_survival_fraction"], pair["qit_metrics"]["mean_record_survival_fraction"]) * 0.3
            + ratio(pair["open_metrics"]["reset_entropy_drop"], pair["qit_metrics"]["reset_entropy_drop"]) * 0.15
        )
    if pair_id == "szilard_record_hard_reset_pair":
        return (
            ratio(pair["open_metrics"]["best_ordering_margin"], pair["qit_metrics"]["best_ordering_margin"]) * 0.25
            + ratio(pair["open_metrics"]["mean_measurement_mutual_information"], pair["qit_metrics"]["mean_measurement_mutual_information"]) * 0.25
            + ratio(pair["open_metrics"]["mean_record_survival_fraction"], pair["qit_metrics"]["mean_record_survival_fraction"]) * 0.25
            + ratio(pair["qit_metrics"]["residual_reset_entropy"], pair["open_metrics"]["residual_reset_entropy"]) * 0.25
        )
    if pair_id == "szilard_record_ordering_pair":
        return (
            ratio(pair["open_metrics"]["best_ordering_margin"], pair["qit_metrics"]["best_ordering_margin"]) * 0.4
            + ratio(pair["open_metrics"]["mean_measurement_mutual_information"], pair["qit_metrics"]["mean_measurement_mutual_information"]) * 0.2
            + ratio(pair["open_metrics"]["mean_record_survival_fraction"], pair["qit_metrics"]["mean_record_survival_fraction"]) * 0.2
            + ratio(pair["qit_metrics"]["residual_reset_entropy"], pair["open_metrics"]["residual_reset_entropy"]) * 0.2
        )
    if pair_id == "szilard_record_ordering_refinement_pair":
        return (
            ratio(pair["open_metrics"]["best_ordering_margin"], pair["qit_metrics"]["best_ordering_margin"]) * 0.45
            + ratio(pair["open_metrics"]["mean_measurement_mutual_information"], pair["qit_metrics"]["mean_measurement_mutual_information"]) * 0.2
            + ratio(pair["open_metrics"]["mean_record_survival_fraction"], pair["qit_metrics"]["mean_record_survival_fraction"]) * 0.2
            + ratio(pair["qit_metrics"]["residual_reset_entropy"], pair["open_metrics"]["residual_reset_entropy"]) * 0.15
        )
    if pair_id == "szilard_reverse_recovery_pair":
        return (
            ratio(pair["open_metrics"]["mean_recovery_entropy_restoration_fraction"], pair["qit_metrics"]["mean_recovery_entropy_restoration_fraction"]) * 0.35
            + ratio(pair["open_metrics"]["mean_recovery_vs_naive_gap"], pair["qit_metrics"]["mean_recovery_vs_naive_gap"]) * 0.4
            + ratio(pair["open_metrics"]["mean_naive_reverse_entropy_restoration_fraction"], pair["qit_metrics"]["mean_naive_reverse_entropy_restoration_fraction"]) * 0.25
        )
    if pair_id == "carnot_finite_time_pair":
        return (
            ratio(pair["qit_metrics"]["baseline_closure"], pair["open_metrics"]["baseline_closure"]) * 0.25
            + ratio(pair["qit_metrics"]["best_closure"], pair["open_metrics"]["best_closure"]) * 0.25
            + ratio(pair["qit_metrics"]["best_forward_efficiency"], pair["open_metrics"]["best_forward_efficiency"]) * 0.25
            + ratio(pair["open_metrics"]["best_reverse_cop"], pair["qit_metrics"]["best_reverse_cop"]) * 0.25
        )
    if pair_id == "carnot_irreversibility_pair":
        return (
            ratio(pair["qit_metrics"]["best_forward_distance_to_carnot"], pair["open_metrics"]["best_forward_distance_to_carnot"]) * 0.3
            + ratio(pair["qit_metrics"]["best_reverse_distance_to_carnot_cop"], pair["open_metrics"]["best_reverse_distance_to_carnot_cop"]) * 0.3
            + ratio(pair["qit_metrics"]["best_forward_efficiency"], pair["open_metrics"]["best_forward_efficiency"]) * 0.2
            + ratio(pair["open_metrics"]["best_reverse_cop"], pair["qit_metrics"]["best_reverse_cop"]) * 0.2
        )
    if pair_id == "carnot_closure_pair":
        return (
            ratio(pair["qit_metrics"]["best_closure_defect"], pair["open_metrics"]["best_closure_defect"]) * 0.7
            + pair["delta"]["dominant_leg_matches"] * 0.3
        )
    if pair_id == "carnot_hold_policy_pair":
        return (
            ratio(pair["qit_metrics"]["baseline_closure"], pair["open_metrics"]["baseline_closure"]) * 0.25
            + ratio(pair["qit_metrics"]["best_closure"], pair["open_metrics"]["best_closure"]) * 0.35
            + ratio(pair["qit_metrics"]["best_efficiency"], pair["open_metrics"]["best_efficiency"]) * 0.4
        )
    return 0.0


def main() -> None:
    audit = load("engine_lab_constraint_audit_results.json")
    compare = load("qit_repair_comparison_surface_results.json")

    pair_by_open = {row["open_row_id"]: row for row in compare["rows"]}
    rows = []

    for audit_row in audit["rows"]:
        if audit_row["route"] not in {"repair_toward_qit_alignment", "keep_as_open_lab_sidecar"}:
            continue
        pair = pair_by_open.get(audit_row["row_id"])
        score = closeness_score(pair) if pair is not None else 0.0
        if pair is not None and score >= 0.75:
            bucket = "p0_translate_now"
        elif pair is not None and score >= 0.45:
            bucket = "p1_good_candidate"
        elif audit_row["route"] == "repair_toward_qit_alignment":
            bucket = "p2_needs_new_companion_or_metric"
        else:
            bucket = "p3_keep_open_sidecar"
        rows.append(
            {
                "row_id": audit_row["row_id"],
                "family": audit_row["family"],
                "route": audit_row["route"],
                "clean_run": audit_row["clean_run"],
                "closest_strict_anchor": audit_row["closest_strict_anchor"],
                "has_direct_qit_pair": pair is not None,
                "pair_id": pair["pair_id"] if pair is not None else None,
                "translation_closeness_score": float(score),
                "priority_bucket": bucket,
                "headline_metrics": audit_row["headline_metrics"],
            }
        )

    rows.sort(key=lambda row: (-row["translation_closeness_score"], row["row_id"]))
    buckets = sorted({row["priority_bucket"] for row in rows})
    priority_counts = {
        bucket: sum(row["priority_bucket"] == bucket for row in rows)
        for bucket in buckets
    }

    out = {
        "name": "engine_lab_repair_priority",
        "classification": CLASSIFICATION,
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": True,
            "ranked_rows": len(rows),
            "paired_rows": sum(row["has_direct_qit_pair"] for row in rows),
            "priority_counts": priority_counts,
            "top_row_id": rows[0]["row_id"] if rows else None,
            "top_row_score": rows[0]["translation_closeness_score"] if rows else None,
            "scope_note": (
                "Priority ranking over repairable engine-lab rows. Higher score means the "
                "open row already translates more cleanly into a strict companion."
            ),
        },
        "rows": rows,
    }

    out_path = RESULT_DIR / "engine_lab_repair_priority_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
