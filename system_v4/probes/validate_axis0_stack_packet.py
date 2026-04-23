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

from axis0_bridge_owner_alignment_contract import (
    axis_internal_mapping_ok,
    axis_internal_placement_ok,
    axis_internal_readout_ok,
    current_bridge_gate_name,
    current_bridge_gate_status,
)
from axis0_constraint_types import build_constraint_family_profile
from axis0_result_loader import load_axis0_result
from axis0_xi_law_fingerprint import (
    carrier_law_fingerprint,
    carrier_matches_law,
    entropy_law_fingerprint,
    pre_entropy_law_fingerprint,
    runner_law_fingerprints_consistent,
    strict_law_fingerprint,
)


ROOT = Path(__file__).resolve().parent
SIM_RESULTS = ROOT / "a2_state" / "sim_results"
OUTPUT_PATH = SIM_RESULTS / "axis0_stack_packet_validation.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(ok: bool, name: str, detail: dict) -> dict:
    return {"name": name, "pass": bool(ok), "detail": detail}


def _mean_profile(*profiles: dict[str, float]) -> dict[str, float]:
    keys = (
        "observational",
        "admissible",
        "stable",
        "entropy_conditioned",
        "topology_conditioned",
    )
    present = [profile for profile in profiles if profile]
    if not present:
        return build_constraint_family_profile()
    return build_constraint_family_profile(
        **{
            key: sum(float(profile.get(key, 0.0)) for profile in present) / len(present)
            for key in keys
        }
    )


def _profile_meets(profile: dict[str, float], **minimums: float) -> bool:
    return all(float(profile.get(key, 0.0)) >= threshold for key, threshold in minimums.items())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    run_packet = load_axis0_result(SIM_RESULTS, "axis0_stack_packet_run_results.json")
    xi_strict = load_axis0_result(SIM_RESULTS, "axis0_xi_strict_bakeoff_results.json")
    formal_geometry = load_json(SIM_RESULTS / "formal_geometry_packet_validation.json")
    root_emergence = load_json(SIM_RESULTS / "root_emergence_packet_validation.json")
    carrier_selection = load_json(SIM_RESULTS / "carrier_selection_packet_validation.json")
    pre_entropy = load_json(SIM_RESULTS / "pre_entropy_packet_validation.json")
    c1_bridge_object = load_json(SIM_RESULTS / "c1_bridge_object_packet_validation.json")
    matched_marginal = load_json(SIM_RESULTS / "matched_marginal_packet_validation.json")
    entropy_readout = load_json(SIM_RESULTS / "entropy_readout_packet_validation.json")
    root_gate_map = {item["name"]: item for item in root_emergence["gates"]}
    carrier_gate_map = {item["name"]: item for item in carrier_selection["gates"]}
    pre_entropy_gate_map = {item["name"]: item for item in pre_entropy["gates"]}
    c1_bridge_gate_map = {item["name"]: item for item in c1_bridge_object["gates"]}
    matched_gate_map = {item["name"]: item for item in matched_marginal["gates"]}
    entropy_gate_map = {item["name"]: item for item in entropy_readout["gates"]}
    strict_xi_law = strict_law_fingerprint(xi_strict)
    carrier_xi_semantics = carrier_selection.get(
        "xi_hist_carrier_semantics",
        carrier_law_fingerprint(carrier_selection),
    )
    pre_entropy_xi_law = pre_entropy.get(
        "xi_hist_law_fingerprint",
        pre_entropy_law_fingerprint(pre_entropy),
    )
    entropy_xi_law = entropy_readout.get(
        "xi_hist_law_fingerprint",
        entropy_law_fingerprint(entropy_readout),
    )
    root_constraint_profile = root_emergence.get("constraint_family_profile", {})
    carrier_constraint_profile = carrier_selection.get("constraint_family_profile", {})
    pre_entropy_constraint_profile = pre_entropy.get("constraint_family_profile", {})
    matched_constraint_profile = matched_marginal.get("constraint_family_profile", {})
    entropy_constraint_profile = entropy_readout.get("constraint_family_profile", {})
    carrier_constraint_profile = carrier_selection.get("constraint_family_profile", {})
    pre_entropy_constraint_profile = pre_entropy.get("constraint_family_profile", {})

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
            root_gate_map["R1_formal_geometry_prerequisite_is_closed"]["pass"]
            and root_emergence["score"] == 1.0
            and carrier_gate_map["C3_live_carrier_wins_and_honesty_signal_stays_unique"]["pass"]
            and carrier_gate_map["C4_bridge_search_separates_winning_bridges_from_controls"]["pass"]
            and carrier_gate_map["C6_direct_lr_stays_ranked_as_control_not_winner"]["pass"]
            and carrier_gate_map["C7_counterfeit_history_games_mi_but_not_coherent_info"]["pass"]
            and carrier_gate_map["C8_provisional_signed_bridge_candidate_handoff_is_explicit"]["pass"]
            and carrier_gate_map["C9_handoff_contract_freezes_downstream_only_placement"]["pass"]
            and _profile_meets(
                root_constraint_profile,
                observational=1.0,
                admissible=1.0,
                stable=1.0,
                topology_conditioned=1.0,
            )
            and _profile_meets(
                carrier_constraint_profile,
                observational=1.0,
                admissible=1.0,
                stable=1.0,
                entropy_conditioned=1.0,
                topology_conditioned=1.0,
            ),
            "S3_lower_ladder_is_coherent",
            {
                "formal_geometry_score": formal_geometry["score"],
                "root_r1_pass": root_gate_map["R1_formal_geometry_prerequisite_is_closed"]["pass"],
                "root_emergence_score": root_emergence["score"],
                "root_constraint_profile": root_constraint_profile,
                "carrier_selection_score": carrier_selection["score"],
                "carrier_constraint_profile": carrier_constraint_profile,
                "carrier_c3_pass": carrier_gate_map["C3_live_carrier_wins_and_honesty_signal_stays_unique"]["pass"],
                "carrier_c4_pass": carrier_gate_map["C4_bridge_search_separates_winning_bridges_from_controls"]["pass"],
                "carrier_c6_pass": carrier_gate_map["C6_direct_lr_stays_ranked_as_control_not_winner"]["pass"],
                "carrier_c7_pass": carrier_gate_map["C7_counterfeit_history_games_mi_but_not_coherent_info"]["pass"],
                "carrier_c8_pass": carrier_gate_map["C8_provisional_signed_bridge_candidate_handoff_is_explicit"]["pass"],
                "carrier_c9_pass": carrier_gate_map["C9_handoff_contract_freezes_downstream_only_placement"]["pass"],
            },
        ),
        gate(
            pre_entropy["score"] == 1.0
            and c1_bridge_object["score"] == 1.0
            and matched_marginal["score"] == 1.0
            and entropy_readout["score"] == 1.0
            and _profile_meets(
                pre_entropy_constraint_profile,
                observational=1.0,
                admissible=1.0,
                stable=1.0,
                entropy_conditioned=1.0,
                topology_conditioned=1.0,
            )
            and _profile_meets(
                matched_constraint_profile,
                observational=1.0,
                admissible=1.0,
                stable=1.0,
                entropy_conditioned=1.0,
                topology_conditioned=1.0,
            )
            and _profile_meets(
                entropy_constraint_profile,
                observational=1.0,
                admissible=1.0,
                stable=1.0,
                entropy_conditioned=1.0,
                topology_conditioned=1.0,
            ),
            "S4_upper_ladder_is_coherent",
            {
                "pre_entropy_score": pre_entropy["score"],
                "pre_entropy_constraint_profile": pre_entropy_constraint_profile,
                "c1_bridge_object_score": c1_bridge_object["score"],
                "matched_marginal_score": matched_marginal["score"],
                "matched_constraint_profile": matched_constraint_profile,
                "entropy_readout_score": entropy_readout["score"],
                "entropy_constraint_profile": entropy_constraint_profile,
            },
        ),
        gate(
            root_emergence["score"] == 1.0
            and c1_bridge_object["score"] == 1.0
            and pre_entropy_gate_map["P22_c1_signed_bridge_candidate_is_explicit_and_provisional"]["pass"]
            and pre_entropy_gate_map["P23_xi_chiral_entangle_remains_downstream_of_xi_hist_signed_law"]["pass"]
            and pre_entropy_gate_map["P24_carrier_handoff_matches_pre_entropy_downstream_mapping"]["pass"]
            and pre_entropy_gate_map["P25_standalone_c1_bridge_object_matches_pre_entropy_contract"]["pass"]
            and entropy_gate_map[current_bridge_gate_name()]["pass"]
            and entropy_gate_map["E11_xi_chiral_entangle_signed_honesty_beats_mispair_counterfeit"]["pass"]
            and _profile_meets(
                root_constraint_profile,
                observational=1.0,
                admissible=1.0,
                stable=1.0,
                topology_conditioned=1.0,
            )
            and _profile_meets(
                pre_entropy_constraint_profile,
                observational=1.0,
                admissible=1.0,
                stable=1.0,
                entropy_conditioned=1.0,
                topology_conditioned=1.0,
            )
            and _profile_meets(
                entropy_constraint_profile,
                observational=1.0,
                admissible=1.0,
                stable=1.0,
                entropy_conditioned=1.0,
                topology_conditioned=1.0,
            ),
            "S5_axis0_ladder_is_mechanically_traversable",
            {
                "root_emergence_score": root_emergence["score"],
                "root_constraint_profile": root_constraint_profile,
                "pre_entropy_score": pre_entropy["score"],
                "pre_entropy_constraint_profile": pre_entropy_constraint_profile,
                "c1_bridge_object_score": c1_bridge_object["score"],
                "entropy_readout_score": entropy_readout["score"],
                "entropy_constraint_profile": entropy_constraint_profile,
                "pre_entropy_p22_pass": pre_entropy_gate_map["P22_c1_signed_bridge_candidate_is_explicit_and_provisional"]["pass"],
                "pre_entropy_p23_pass": pre_entropy_gate_map["P23_xi_chiral_entangle_remains_downstream_of_xi_hist_signed_law"]["pass"],
                "pre_entropy_p24_pass": pre_entropy_gate_map["P24_carrier_handoff_matches_pre_entropy_downstream_mapping"]["pass"],
                "pre_entropy_p25_pass": pre_entropy_gate_map["P25_standalone_c1_bridge_object_matches_pre_entropy_contract"]["pass"],
                "entropy_e10_pass": entropy_gate_map[current_bridge_gate_name()]["pass"],
                "entropy_e11_pass": entropy_gate_map["E11_xi_chiral_entangle_signed_honesty_beats_mispair_counterfeit"]["pass"],
            },
        ),
        gate(
            c1_bridge_gate_map["C1B1_bridge_object_is_explicit_and_downstream_only"]["pass"]
            and c1_bridge_gate_map["C1B3_bridge_object_is_bound_to_the_existing_support_contract"]["pass"]
            and c1_bridge_gate_map["C1B4_bridge_object_keeps_owner_doctrine_questions_open"]["pass"]
            and entropy_gate_map[current_bridge_gate_name()]["pass"]
            and entropy_gate_map[current_bridge_gate_name()]["detail"]["status"]
            == current_bridge_gate_status()
            and axis_internal_readout_ok(pre_entropy["owner_worthiness_map"]["axis_internal_readout"])
            and pre_entropy["owner_worthiness_map"]["owner_derived"]["xi_hist_signed_law"] == "admitted"
            and axis_internal_mapping_ok(pre_entropy["pre_axis_admission_schema"]["current_mapping"])
            and axis_internal_placement_ok(pre_entropy["pre_axis_admission_schema"]["placement_relations"]),
            "S6_xi_chiral_entangle_remains_axis_internal_and_not_owner_law",
            {
                "c1b1_pass": c1_bridge_gate_map["C1B1_bridge_object_is_explicit_and_downstream_only"]["pass"],
                "c1b3_pass": c1_bridge_gate_map["C1B3_bridge_object_is_bound_to_the_existing_support_contract"]["pass"],
                "c1b4_pass": c1_bridge_gate_map["C1B4_bridge_object_keeps_owner_doctrine_questions_open"]["pass"],
                "entropy_e10_status": entropy_gate_map[current_bridge_gate_name()]["detail"]["status"],
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
            and entropy_gate_map[current_bridge_gate_name()]["pass"]
            and _profile_meets(
                root_constraint_profile,
                admissible=1.0,
                stable=1.0,
                topology_conditioned=1.0,
            )
            and _profile_meets(
                pre_entropy_constraint_profile,
                admissible=1.0,
                stable=1.0,
                entropy_conditioned=1.0,
                topology_conditioned=1.0,
            )
            and _profile_meets(
                matched_constraint_profile,
                admissible=1.0,
                stable=1.0,
                entropy_conditioned=1.0,
                topology_conditioned=1.0,
            )
            and _profile_meets(
                entropy_constraint_profile,
                admissible=1.0,
                stable=1.0,
                entropy_conditioned=1.0,
                topology_conditioned=1.0,
            ),
            "S7_axis0_stack_explicitly_consumes_named_contract_gates",
            {
                "root_r10_pass": root_gate_map["R10_root_emergence_bridge_winner_respects_xi_handoff_contract"]["pass"],
                "root_constraint_profile": root_constraint_profile,
                "c1b3_pass": c1_bridge_gate_map["C1B3_bridge_object_is_bound_to_the_existing_support_contract"]["pass"],
                "pre_entropy_p24_pass": pre_entropy_gate_map["P24_carrier_handoff_matches_pre_entropy_downstream_mapping"]["pass"],
                "pre_entropy_constraint_profile": pre_entropy_constraint_profile,
                "matched_m9_pass": matched_gate_map["M9_matched_marginal_stays_subordinate_to_xi_downstream_mapping"]["pass"],
                "matched_constraint_profile": matched_constraint_profile,
                "entropy_e10_pass": entropy_gate_map[current_bridge_gate_name()]["pass"],
                "entropy_e12_pass": entropy_gate_map["E12_xi_hist_law_summary_binds_pre_entropy_to_readout"]["pass"],
                "entropy_constraint_profile": entropy_constraint_profile,
            },
        ),
        gate(
            runner_law_fingerprints_consistent(run_packet)
            and strict_xi_law == pre_entropy_xi_law
            and strict_xi_law == entropy_xi_law
            and carrier_matches_law(carrier_xi_semantics, strict_xi_law),
            "S8_xi_hist_law_is_semantically_consistent_across_stack",
            {
                "runner_fingerprints_consistent": runner_law_fingerprints_consistent(run_packet),
                "strict_vs_pre_entropy_match": strict_xi_law == pre_entropy_xi_law,
                "strict_vs_entropy_readout_match": strict_xi_law == entropy_xi_law,
                "carrier_matches_strict_law": carrier_matches_law(carrier_xi_semantics, strict_xi_law),
                "strict_xi_law": strict_xi_law,
                "carrier_xi_semantics": carrier_xi_semantics,
                "pre_entropy_xi_law": pre_entropy_xi_law,
                "entropy_readout_xi_law": entropy_xi_law,
                "run_packet_xi_hist_law_fingerprints": run_packet.get("xi_hist_law_fingerprints", {}),
            },
        ),
        gate(
            c1_bridge_gate_map["C1B1_bridge_object_is_explicit_and_downstream_only"]["pass"]
            and c1_bridge_gate_map["C1B2_counterfeit_pressure_remains_bound_to_the_bridge_object"]["pass"]
            and c1_bridge_gate_map["C1B3_bridge_object_is_bound_to_the_existing_support_contract"]["pass"]
            and c1_bridge_gate_map["C1B4_bridge_object_keeps_owner_doctrine_questions_open"]["pass"]
            and entropy_gate_map[current_bridge_gate_name()]["pass"]
            and _profile_meets(
                entropy_constraint_profile,
                observational=1.0,
                admissible=1.0,
                stable=1.0,
                entropy_conditioned=1.0,
                topology_conditioned=1.0,
            ),
            "S9_axis0_stack_consumes_standalone_c1_bridge_object_contract",
            {
                "c1b1_pass": c1_bridge_gate_map["C1B1_bridge_object_is_explicit_and_downstream_only"]["pass"],
                "c1b2_pass": c1_bridge_gate_map["C1B2_counterfeit_pressure_remains_bound_to_the_bridge_object"]["pass"],
                "c1b3_pass": c1_bridge_gate_map["C1B3_bridge_object_is_bound_to_the_existing_support_contract"]["pass"],
                "c1b4_pass": c1_bridge_gate_map["C1B4_bridge_object_keeps_owner_doctrine_questions_open"]["pass"],
                "entropy_e10_pass": entropy_gate_map[current_bridge_gate_name()]["pass"],
                "entropy_e12_pass": entropy_gate_map["E12_xi_hist_law_summary_binds_pre_entropy_to_readout"]["pass"],
                "entropy_constraint_profile": entropy_constraint_profile,
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
        "constraint_family_profile": _mean_profile(
            formal_geometry.get("constraint_family_profile", {}),
            c1_bridge_object.get("constraint_family_profile", {}),
            root_constraint_profile,
            carrier_constraint_profile,
            pre_entropy_constraint_profile,
            matched_constraint_profile,
            entropy_constraint_profile,
        ),
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
