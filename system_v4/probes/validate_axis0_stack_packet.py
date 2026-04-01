#!/usr/bin/env python3
"""
validate_axis0_stack_packet.py
==============================

Mechanical validator for the full Axis 0 packet ladder.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SIM_RESULTS = ROOT / "a2_state" / "sim_results"
OUTPUT_PATH = SIM_RESULTS / "axis0_stack_packet_validation.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(ok: bool, name: str, detail: dict) -> dict:
    return {"name": name, "pass": bool(ok), "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    run_packet = load_json(SIM_RESULTS / "axis0_stack_packet_run_results.json")
    formal_geometry = load_json(SIM_RESULTS / "formal_geometry_packet_validation.json")
    root_emergence = load_json(SIM_RESULTS / "root_emergence_packet_validation.json")
    carrier_selection = load_json(SIM_RESULTS / "carrier_selection_packet_validation.json")
    pre_entropy = load_json(SIM_RESULTS / "pre_entropy_packet_validation.json")
    c1_bridge_object = load_json(SIM_RESULTS / "c1_bridge_object_packet_validation.json")
    matched_marginal = load_json(SIM_RESULTS / "matched_marginal_packet_validation.json")
    entropy_readout = load_json(SIM_RESULTS / "entropy_readout_packet_validation.json")
    formal_gate_map = {item["name"]: item for item in formal_geometry["gates"]}
    root_gate_map = {item["name"]: item for item in root_emergence["gates"]}
    carrier_gate_map = {item["name"]: item for item in carrier_selection["gates"]}
    pre_entropy_gate_map = {item["name"]: item for item in pre_entropy["gates"]}
    c1_bridge_gate_map = {item["name"]: item for item in c1_bridge_object["gates"]}
    matched_gate_map = {item["name"]: item for item in matched_marginal["gates"]}
    entropy_gate_map = {item["name"]: item for item in entropy_readout["gates"]}

    packet_map = {
        "formal_geometry": formal_geometry,
        "root_emergence": root_emergence,
        "carrier_selection": carrier_selection,
        "pre_entropy": pre_entropy,
        "c1_bridge_object": c1_bridge_object,
        "matched_marginal": matched_marginal,
        "entropy_readout": entropy_readout,
    }

    gates = [
        gate(
            run_packet["all_ok"],
            "S1_all_packet_runners_execute_cleanly",
            {
                "all_ok": run_packet["all_ok"],
                "steps": [{k: step[k] for k in ("label", "ok", "returncode")} for step in run_packet["steps"]],
            },
        ),
        gate(
            all(packet["passed_gates"] == packet["total_gates"] for packet in packet_map.values()),
            "S2_all_component_packets_are_closed",
            {
                key: {
                    "passed_gates": packet["passed_gates"],
                    "total_gates": packet["total_gates"],
                    "score": packet["score"],
                }
                for key, packet in packet_map.items()
            },
        ),
        gate(
            formal_geometry["score"] == 1.0
            and root_emergence["score"] == 1.0
            and carrier_selection["score"] == 1.0,
            "S3_lower_ladder_is_coherent",
            {
                "formal_geometry_score": formal_geometry["score"],
                "root_emergence_score": root_emergence["score"],
                "carrier_selection_score": carrier_selection["score"],
            },
        ),
        gate(
            pre_entropy["score"] == 1.0
            and c1_bridge_object["score"] == 1.0
            and matched_marginal["score"] == 1.0
            and entropy_readout["score"] == 1.0,
            "S4_upper_ladder_is_coherent",
            {
                "pre_entropy_score": pre_entropy["score"],
                "c1_bridge_object_score": c1_bridge_object["score"],
                "matched_marginal_score": matched_marginal["score"],
                "entropy_readout_score": entropy_readout["score"],
            },
        ),
        gate(
            root_emergence["score"] == 1.0
            and pre_entropy["score"] == 1.0
            and c1_bridge_object["score"] == 1.0
            and entropy_readout["score"] == 1.0,
            "S5_axis0_ladder_is_mechanically_traversable",
            {
                "root_emergence_score": root_emergence["score"],
                "pre_entropy_score": pre_entropy["score"],
                "c1_bridge_object_score": c1_bridge_object["score"],
                "entropy_readout_score": entropy_readout["score"],
            },
        ),
        gate(
            c1_bridge_gate_map["C1B1_bridge_object_is_explicit_and_downstream_only"]["pass"]
            and c1_bridge_gate_map["C1B3_bridge_object_is_bound_to_the_existing_support_contract"]["pass"]
            and c1_bridge_gate_map["C1B4_bridge_object_keeps_owner_doctrine_questions_open"]["pass"]
            and entropy_gate_map["E10_current_bridge_candidate_is_explicit_and_provisional"]["pass"]
            and entropy_gate_map["E12_xi_hist_law_summary_binds_pre_entropy_to_readout"]["pass"]
            and entropy_gate_map["E10_current_bridge_candidate_is_explicit_and_provisional"]["detail"]["status"]
            == "admitted_executable_candidate_not_final_owner_law"
            and pre_entropy["owner_worthiness_map"]["axis_internal_readout"]["Xi_chiral_entangle"] == "current_bridge_candidate"
            and pre_entropy["owner_worthiness_map"]["owner_derived"]["xi_hist_signed_law"] == "admitted"
            and pre_entropy["pre_axis_admission_schema"]["current_mapping"]["Xi_chiral_entangle"]
            == "axis_internal_candidate_not_final_owner_law"
            and pre_entropy["pre_axis_admission_schema"]["placement_relations"]["Xi_chiral_entangle"]
            == "downstream_axis_internal_bridge_candidate_derived_from_xi_hist_signed_law",
            "S6_xi_chiral_entangle_remains_axis_internal_and_not_owner_law",
            {
                "c1b1_pass": c1_bridge_gate_map["C1B1_bridge_object_is_explicit_and_downstream_only"]["pass"],
                "c1b3_pass": c1_bridge_gate_map["C1B3_bridge_object_is_bound_to_the_existing_support_contract"]["pass"],
                "c1b4_pass": c1_bridge_gate_map["C1B4_bridge_object_keeps_owner_doctrine_questions_open"]["pass"],
                "entropy_e10_status": entropy_gate_map["E10_current_bridge_candidate_is_explicit_and_provisional"]["detail"]["status"],
                "entropy_e12_pass": entropy_gate_map["E12_xi_hist_law_summary_binds_pre_entropy_to_readout"]["pass"],
                "xi_axis_internal_status": pre_entropy["owner_worthiness_map"]["axis_internal_readout"]["Xi_chiral_entangle"],
                "xi_hist_owner_status": pre_entropy["owner_worthiness_map"]["owner_derived"]["xi_hist_signed_law"],
                "xi_current_mapping": pre_entropy["pre_axis_admission_schema"]["current_mapping"]["Xi_chiral_entangle"],
                "xi_placement_relation": pre_entropy["pre_axis_admission_schema"]["placement_relations"]["Xi_chiral_entangle"],
            },
        ),
        gate(
            root_gate_map["R10_root_emergence_bridge_winner_respects_xi_handoff_contract"]["pass"]
            and c1_bridge_gate_map["C1B3_bridge_object_is_bound_to_the_existing_support_contract"]["pass"]
            and pre_entropy_gate_map["P24_carrier_handoff_matches_pre_entropy_downstream_mapping"]["pass"]
            and matched_gate_map["M9_matched_marginal_stays_subordinate_to_xi_downstream_mapping"]["pass"]
            and entropy_gate_map["E10_current_bridge_candidate_is_explicit_and_provisional"]["pass"]
            and entropy_gate_map["E12_xi_hist_law_summary_binds_pre_entropy_to_readout"]["pass"],
            "S7_axis0_stack_explicitly_consumes_named_contract_gates",
            {
                "root_r10_pass": root_gate_map["R10_root_emergence_bridge_winner_respects_xi_handoff_contract"]["pass"],
                "c1b3_pass": c1_bridge_gate_map["C1B3_bridge_object_is_bound_to_the_existing_support_contract"]["pass"],
                "pre_entropy_p24_pass": pre_entropy_gate_map["P24_carrier_handoff_matches_pre_entropy_downstream_mapping"]["pass"],
                "matched_m9_pass": matched_gate_map["M9_matched_marginal_stays_subordinate_to_xi_downstream_mapping"]["pass"],
                "entropy_e10_pass": entropy_gate_map["E10_current_bridge_candidate_is_explicit_and_provisional"]["pass"],
                "entropy_e12_pass": entropy_gate_map["E12_xi_hist_law_summary_binds_pre_entropy_to_readout"]["pass"],
            },
        ),
        gate(
            formal_gate_map["G10_lower_tier_carrier_admission_and_classical_leakage_guards_are_explicit"]["pass"]
            and formal_gate_map["G11_chiral_readout_and_symmetric_bookkeeping_are_embargoed_from_law_promotion"]["pass"]
            and formal_gate_map["G12_lower_tier_chiral_law_search_is_explicit_and_fail_closed"]["pass"]
            and formal_gate_map["G13_lower_tier_transport_law_search_is_explicit_and_fail_closed"]["pass"]
            and formal_gate_map["G14_lower_tier_operator_basis_search_is_explicit_and_fail_closed"]["pass"]
            and root_gate_map["R1_formal_geometry_prerequisite_is_closed"]["pass"]
            and root_gate_map["R7_mispair_counterfeit_games_mi_but_not_coherent_info"]["pass"]
            and root_gate_map["R9_root_emergence_remains_open_without_smuggling"]["pass"]
            and matched_gate_map["M6_exact_preserving_point_reference_stays_discriminator_only"]["pass"]
            and matched_gate_map["M7_fe_indexed_pairs_remain_the_only_structured_refinement_winner"]["pass"]
            and entropy_gate_map["E2_shannon_diagonal_is_not_geometry_safe"]["pass"]
            and entropy_gate_map["E3_product_proxy_and_pure_fi_negatives_hold"]["pass"]
            and entropy_gate_map["E8_history_family_handoff_supports_signed_readout_on_same_objects"]["pass"]
            and entropy_gate_map["E9_fep_framing_shows_nonclassical_directionality"]["pass"]
            and entropy_gate_map["E12_xi_hist_law_summary_binds_pre_entropy_to_readout"]["pass"],
            "S8_axis0_stack_explicitly_consumes_named_foundation_gates",
            {
                "formal_g10_pass": formal_gate_map["G10_lower_tier_carrier_admission_and_classical_leakage_guards_are_explicit"]["pass"],
                "formal_g11_pass": formal_gate_map["G11_chiral_readout_and_symmetric_bookkeeping_are_embargoed_from_law_promotion"]["pass"],
                "formal_g12_pass": formal_gate_map["G12_lower_tier_chiral_law_search_is_explicit_and_fail_closed"]["pass"],
                "formal_g13_pass": formal_gate_map["G13_lower_tier_transport_law_search_is_explicit_and_fail_closed"]["pass"],
                "formal_g14_pass": formal_gate_map["G14_lower_tier_operator_basis_search_is_explicit_and_fail_closed"]["pass"],
                "root_r1_pass": root_gate_map["R1_formal_geometry_prerequisite_is_closed"]["pass"],
                "root_r7_pass": root_gate_map["R7_mispair_counterfeit_games_mi_but_not_coherent_info"]["pass"],
                "root_r9_pass": root_gate_map["R9_root_emergence_remains_open_without_smuggling"]["pass"],
                "matched_m6_pass": matched_gate_map["M6_exact_preserving_point_reference_stays_discriminator_only"]["pass"],
                "matched_m7_pass": matched_gate_map["M7_fe_indexed_pairs_remain_the_only_structured_refinement_winner"]["pass"],
                "entropy_e2_pass": entropy_gate_map["E2_shannon_diagonal_is_not_geometry_safe"]["pass"],
                "entropy_e3_pass": entropy_gate_map["E3_product_proxy_and_pure_fi_negatives_hold"]["pass"],
                "entropy_e8_pass": entropy_gate_map["E8_history_family_handoff_supports_signed_readout_on_same_objects"]["pass"],
                "entropy_e9_pass": entropy_gate_map["E9_fep_framing_shows_nonclassical_directionality"]["pass"],
                "entropy_e12_pass": entropy_gate_map["E12_xi_hist_law_summary_binds_pre_entropy_to_readout"]["pass"],
            },
        ),
        gate(
            c1_bridge_gate_map["C1B1_bridge_object_is_explicit_and_downstream_only"]["pass"]
            and c1_bridge_gate_map["C1B2_counterfeit_pressure_remains_bound_to_the_bridge_object"]["pass"]
            and c1_bridge_gate_map["C1B3_bridge_object_is_bound_to_the_existing_support_contract"]["pass"]
            and c1_bridge_gate_map["C1B4_bridge_object_keeps_owner_doctrine_questions_open"]["pass"]
            and entropy_gate_map["E10_current_bridge_candidate_is_explicit_and_provisional"]["pass"]
            and entropy_gate_map["E12_xi_hist_law_summary_binds_pre_entropy_to_readout"]["pass"],
            "S9_axis0_stack_consumes_standalone_c1_bridge_object_contract",
            {
                "c1b1_pass": c1_bridge_gate_map["C1B1_bridge_object_is_explicit_and_downstream_only"]["pass"],
                "c1b2_pass": c1_bridge_gate_map["C1B2_counterfeit_pressure_remains_bound_to_the_bridge_object"]["pass"],
                "c1b3_pass": c1_bridge_gate_map["C1B3_bridge_object_is_bound_to_the_existing_support_contract"]["pass"],
                "c1b4_pass": c1_bridge_gate_map["C1B4_bridge_object_keeps_owner_doctrine_questions_open"]["pass"],
                "entropy_e10_pass": entropy_gate_map["E10_current_bridge_candidate_is_explicit_and_provisional"]["pass"],
                "entropy_e12_pass": entropy_gate_map["E12_xi_hist_law_summary_binds_pre_entropy_to_readout"]["pass"],
            },
        ),
    ]

    passed = sum(1 for item in gates if item["pass"])
    payload = {
        "name": "axis0_stack_packet_validation",
        "timestamp": datetime.now(UTC).isoformat(),
        "passed_gates": passed,
        "total_gates": len(gates),
        "score": passed / len(gates) if gates else 0.0,
        "gates": gates,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if args.pretty:
        print("=" * 72)
        print("AXIS0 STACK PACKET VALIDATION")
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
