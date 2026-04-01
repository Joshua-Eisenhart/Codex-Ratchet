#!/usr/bin/env python3
"""
validate_transport_embargo_packet.py
====================================

Mechanical validator for the post-readiness transport embargo family.

This packet does not try to promote transport into owner doctrine.
It makes the current state explicit:
  - raw Weyl transport deltas are live,
  - lower-tier transport law is narrower than generic transport,
  - the surviving compound transport/chirality branch has nonproxy support,
  - the whole branch remains embargoed from owner promotion.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SIM_RESULTS = ROOT / "a2_state" / "sim_results"
OUTPUT_PATH = SIM_RESULTS / "transport_embargo_packet_validation.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(ok: bool, name: str, detail: dict) -> dict:
    return {"name": name, "pass": bool(ok), "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    weyl_delta = load_json(SIM_RESULTS / "weyl_delta_packet_validation.json")
    lower_transport = load_json(SIM_RESULTS / "lower_tier_transport_law_search_validation.json")
    pre_entropy = load_json(SIM_RESULTS / "pre_entropy_packet_validation.json")
    joint_ablation = load_json(SIM_RESULTS / "neg_transport_delta_joint_ablation_results.json")

    weyl_gate_map = {item["name"]: item for item in weyl_delta["gates"]}
    transport_gate_map = {item["name"]: item for item in lower_transport["gates"]}
    pre_gate_map = {item["name"]: item for item in pre_entropy["gates"]}

    weyl_delta_results = load_json(SIM_RESULTS / "weyl_delta_packet_results.json")
    transport_embargo_boundary = weyl_delta_results["transport_embargo_boundary"]
    owner_map = pre_entropy["owner_worthiness_map"]
    admission_schema = pre_entropy["pre_axis_admission_schema"]
    necessity = pre_entropy["joint_necessity_witness"]
    joint_summary = joint_ablation["summary"]
    joint_owner_read = joint_ablation["owner_read"]

    gates = [
        gate(
            weyl_gate_map["W5_branch_map_keeps_flux_placement_open"]["pass"]
            and weyl_gate_map["W6_flux_family_is_explicit_without_canonizing_flux"]["pass"]
            and weyl_gate_map["W7_branch_map_preserves_skeptical_flux_read"]["pass"]
            and weyl_gate_map["W8_pre_axis_object_inventory_is_explicit"]["pass"]
            and weyl_gate_map["W9_transport_embargo_boundary_is_explicit"]["pass"]
            and transport_embargo_boundary["status"] == "candidate_pre_axis_law_not_owner_promoted"
            and transport_embargo_boundary["surviving_candidate"] == "chirality_separated_transport_deltas"
            and transport_embargo_boundary["lower_tier_law"] == "exact_loop_assigned_transport_only"
            and transport_embargo_boundary["blocked_flux"] == "entropic_left_right_flux"
            and transport_embargo_boundary["unsupported_single_flux"] == "single_weyl_flux_object"
            and transport_embargo_boundary["downstream_branch"] == "post_joint_cut_flux"
            and transport_embargo_boundary["promotion_boundary"] == "awaiting_owner_promotion_decision_after_nonproxy_support",
            "TE1_weyl_delta_transport_family_is_live_but_fail_closed",
            {
                "w5_pass": weyl_gate_map["W5_branch_map_keeps_flux_placement_open"]["pass"],
                "w6_pass": weyl_gate_map["W6_flux_family_is_explicit_without_canonizing_flux"]["pass"],
                "w7_pass": weyl_gate_map["W7_branch_map_preserves_skeptical_flux_read"]["pass"],
                "w8_pass": weyl_gate_map["W8_pre_axis_object_inventory_is_explicit"]["pass"],
                "w9_pass": weyl_gate_map["W9_transport_embargo_boundary_is_explicit"]["pass"],
                "transport_embargo_boundary": transport_embargo_boundary,
            },
        ),
        gate(
            transport_gate_map["T1_exact_same_carrier_loop_law_survives_search"]["pass"]
            and transport_gate_map["T2_generic_transport_activity_is_not_promoted_to_law"]["pass"]
            and transport_gate_map["T3_symmetric_motion_summary_is_killed_as_fake_transport_law"]["pass"]
            and transport_gate_map["T4_downstream_cut_effect_is_fenced_off_from_lower_transport_law"]["pass"],
            "TE2_lower_tier_transport_law_stays_narrow_and_non_generic",
            {
                "t1_pass": transport_gate_map["T1_exact_same_carrier_loop_law_survives_search"]["pass"],
                "t2_pass": transport_gate_map["T2_generic_transport_activity_is_not_promoted_to_law"]["pass"],
                "t3_pass": transport_gate_map["T3_symmetric_motion_summary_is_killed_as_fake_transport_law"]["pass"],
                "t4_pass": transport_gate_map["T4_downstream_cut_effect_is_fenced_off_from_lower_transport_law"]["pass"],
            },
        ),
        gate(
            pre_gate_map["P16_transport_delta_branch_survives_but_is_not_owner_law_yet"]["pass"]
            and pre_gate_map["P17_transport_delta_branch_now_has_nonproxy_joint_necessity_support"]["pass"]
            and pre_gate_map["P18_joint_same_carrier_ablation_keeps_proxy_screen_closed"]["pass"]
            and pre_gate_map["P19_transport_gap_scalar_is_live_and_joint_ablation_collapses_it"]["pass"]
            and pre_gate_map["P20_joint_same_carrier_nonproxy_runtime_witness_is_explicit"]["pass"]
            and pre_gate_map["P21_pre_axis_admission_schema_is_explicit_and_axis_embargoed"]["pass"],
            "TE3_transport_embargo_branch_is_explicitly_supported_but_not_promoted",
            {
                "p16_pass": pre_gate_map["P16_transport_delta_branch_survives_but_is_not_owner_law_yet"]["pass"],
                "p17_pass": pre_gate_map["P17_transport_delta_branch_now_has_nonproxy_joint_necessity_support"]["pass"],
                "p18_pass": pre_gate_map["P18_joint_same_carrier_ablation_keeps_proxy_screen_closed"]["pass"],
                "p19_pass": pre_gate_map["P19_transport_gap_scalar_is_live_and_joint_ablation_collapses_it"]["pass"],
                "p20_pass": pre_gate_map["P20_joint_same_carrier_nonproxy_runtime_witness_is_explicit"]["pass"],
                "p21_pass": pre_gate_map["P21_pre_axis_admission_schema_is_explicit_and_axis_embargoed"]["pass"],
            },
        ),
        gate(
            joint_owner_read["status"] == "nonproxy_runtime_support"
            and joint_summary["live_min_transport_gap"] > 0.10
            and joint_summary["combined_gap_retention"] < 0.25
            and joint_summary["live_min_sheet_split"] > 0.1
            and joint_summary["combined_max_sheet_split"] < 1e-12
            and necessity["combined_same_carrier_ablation"]["status"] == "nonproxy_runtime_support"
            and owner_map["pre_axis_law"]["chirality_separated_transport_deltas"] == "candidate"
            and owner_map["pre_axis_law"]["chirality_separated_transport_deltas_blocker"]
            == "awaiting_owner_promotion_decision_after_nonproxy_support"
            and admission_schema["axis_embargo"]["currently_embargoed"]["chirality_separated_transport_deltas"]
            == "candidate_pending_owner_promotion_after_nonproxy_support",
            "TE4_nonproxy_support_and_embargo_blocker_are_bound_together",
            {
                "owner_read": joint_owner_read,
                "live_min_transport_gap": joint_summary["live_min_transport_gap"],
                "combined_gap_retention": joint_summary["combined_gap_retention"],
                "live_min_sheet_split": joint_summary["live_min_sheet_split"],
                "combined_max_sheet_split": joint_summary["combined_max_sheet_split"],
                "owner_worthiness_pre_axis": owner_map["pre_axis_law"],
                "axis_embargo": admission_schema["axis_embargo"]["currently_embargoed"],
            },
        ),
    ]

    passed = sum(1 for item in gates if item["pass"])
    payload = {
        "name": "transport_embargo_packet_validation",
        "timestamp": datetime.now(UTC).isoformat(),
        "passed_gates": passed,
        "total_gates": len(gates),
        "score": passed / len(gates) if gates else 0.0,
        "transport_embargo_contract": {
            "candidate_branch": "chirality-separated loop-sensitive transport deltas",
            "status": "supported_but_embargoed",
            "lower_tier_law": "exact_loop_assigned_transport_only",
            "promotion_blocker": owner_map["pre_axis_law"]["chirality_separated_transport_deltas_blocker"],
            "nonproxy_support": joint_owner_read["status"],
            "diagnostic_only": {
                "raw_delta_packet": owner_map["diagnostic_only"]["raw_delta_packet"],
                "single_weyl_flux_object": admission_schema["axis_embargo"]["currently_embargoed"]["single_weyl_flux_object"],
                "entropic_left_right_flux": owner_map["diagnostic_only"]["entropic_left_right_flux"],
                "post_joint_cut_flux": owner_map["diagnostic_only"]["post_joint_cut_flux"],
            },
        },
        "gates": gates,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if args.pretty:
        print("=" * 72)
        print("TRANSPORT EMBARGO PACKET VALIDATION")
        print("=" * 72)
        for item in gates:
            status = "PASS" if item["pass"] else "FAIL"
            print(f"{status:>4}  {item['name']}")
        print(f"\npassed_gates: {passed}/{len(gates)}")
        print(f"score: {payload['score']:.6f}")
        print(f"validation_results: {OUTPUT_PATH}")
    else:
        print(json.dumps(payload, indent=2))

    return 0 if passed == len(gates) else 1


if __name__ == "__main__":
    raise SystemExit(main())
