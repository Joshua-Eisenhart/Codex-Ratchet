#!/usr/bin/env python3
"""
validate_root_emergence_packet.py
=================================

Mechanical validator for the executable root-emergence witness packet.

This packet sits below the pre-entropy ladder:
  - formal geometry as a prerequisite witness
  - nonclassical runtime guards
  - EC-3 boundary/identity witness
  - missing-axis residual search
  - bridge search ranking
  - co-arising stress as an explicit unresolved theorem surface
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from axis0_bridge_owner_alignment_contract import (
    bridge_owner_alignment_ok,
    signed_bridge_handoff_ok,
)
from axis0_constraint_types import build_constraint_family_profile
from axis0_result_loader import load_axis0_result


ROOT = Path(__file__).resolve().parent
SIM_RESULTS = ROOT / "a2_state" / "sim_results"
LEGACY_RESULTS = ROOT.parent / "a2_state" / "sim_results"
OUTPUT_PATH = SIM_RESULTS / "root_emergence_packet_validation.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(ok: bool, name: str, detail: dict) -> dict:
    return {"name": name, "pass": bool(ok), "detail": detail}


def _packet_constraint_family_profile(gate_map: dict[str, dict]) -> dict[str, float]:
    observational_names = (
        "R1_formal_geometry_prerequisite_is_closed",
        "R2_root_guards_and_ec3_execute_cleanly",
        "R3_missing_axis_search_finds_uncaptured_structure",
    )
    admissible_names = (
        "R4_bridge_search_rejects_direct_cartesian_carrier",
        "R10_root_emergence_bridge_winner_respects_xi_handoff_contract",
    )
    stable_names = (
        "R5_small_carrier_family_selects_live_hopf_weyl",
        "R6_live_carrier_keeps_unique_positive_honesty_signal",
        "R7_mispair_counterfeit_games_mi_but_not_coherent_info",
    )
    entropy_names = (
        "R8_coarising_is_attractor_specific_not_universal_algebra",
        "R9_root_emergence_remains_open_without_smuggling",
    )
    topology_names = (
        "R10A_attractor_basin_keeps_trajectory_far_from_ti_failure_boundary",
        "R10B_te_steps_stay_on_antiparallel_yz_band_on_attractor",
    )

    def _fraction(names: tuple[str, ...]) -> float:
        if not names:
            return 0.0
        return float(sum(1.0 if gate_map[name]["pass"] else 0.0 for name in names) / len(names))

    return build_constraint_family_profile(
        observational=_fraction(observational_names),
        admissible=_fraction(admissible_names),
        stable=_fraction(stable_names),
        entropy_conditioned=_fraction(entropy_names),
        topology_conditioned=_fraction(topology_names),
    )


def step_ok(steps: list[dict], label: str) -> bool:
    for step in steps:
        if step["label"] == label:
            return bool(step["ok"])
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    formal_geometry = load_json(SIM_RESULTS / "formal_geometry_packet_validation.json")
    packet_run = load_json(SIM_RESULTS / "root_emergence_packet_run_results.json")
    missing_axis = load_json(LEGACY_RESULTS / "missing_axis_search_results.json")
    bridge_search = load_axis0_result(SIM_RESULTS, "axis0_bridge_search_results.json")
    carrier_rank = load_json(SIM_RESULTS / "root_constraint_carrier_rank_results.json")
    mispair = load_json(SIM_RESULTS / "history_mispair_counterfeit_results.json")
    coarising = load_axis0_result(SIM_RESULTS, "axis0_coarising_stress_test_results.json")
    orbit_phase = load_axis0_result(SIM_RESULTS, "axis0_orbit_phase_alignment_results.json")
    attractor_basin = load_axis0_result(SIM_RESULTS, "axis0_attractor_basin_boundary_results.json")
    c1_bridge_object = load_json(SIM_RESULTS / "c1_bridge_object_packet_validation.json")
    formal_constraint_profile = formal_geometry.get("constraint_family_profile", {})
    attractor_constraint_profile = load_json(
        SIM_RESULTS / "axis0_attractor_basin_boundary_search_validation.json"
    ).get("constraint_family_profile", {})
    c1_constraint_profile = c1_bridge_object.get("constraint_family_profile", {})

    steps = packet_run["steps"]
    formal_gate_map = {item["name"]: item for item in formal_geometry["gates"]}
    g10_detail = formal_gate_map["G10_lower_tier_carrier_admission_and_classical_leakage_guards_are_explicit"]["detail"]
    g11_detail = formal_gate_map["G11_chiral_readout_and_symmetric_bookkeeping_are_embargoed_from_law_promotion"]["detail"]
    g12_detail = formal_gate_map["G12_lower_tier_chiral_law_search_is_explicit_and_fail_closed"]["detail"]
    g14_detail = formal_gate_map["G14_lower_tier_operator_basis_search_is_explicit_and_fail_closed"]["detail"]
    level1 = coarising["level1_lr_asym"]
    level2 = coarising["level2_bridge_mi"]
    orbit_phase_stats = orbit_phase["aggregate_phase"]
    orbit_half_stats = orbit_phase["aggregate_half"]
    q1_basin = attractor_basin["q1_trajectory_lr_asym"]["configs"]
    q3_basin = attractor_basin["q3_ti_boundary"]
    q4_basin = attractor_basin["q4_te_inversion"]["configs"]
    min_trajectory_lr_asym = min(config["lr_asym_min"] for config in q1_basin)
    ti_failure_threshold = q3_basin["best_lr_asym_before_threshold"]
    ti_boundary_gap = min_trajectory_lr_asym - ti_failure_threshold
    q4_te_steps = [step for config in q4_basin for step in config["te_step_details"]]
    min_q4_norm_cyz = min(step["norm_cyz"] for step in q4_te_steps)
    max_q4_norm_cyz = max(step["norm_cyz"] for step in q4_te_steps)
    min_q4_lr_asym = min(step["lr_asym"] for step in q4_te_steps)
    missing_axis_candidates = missing_axis["candidates"]
    measurement_basis_residual = missing_axis_candidates["A: measurement_basis"]["residual"]
    squeezing_residual = missing_axis_candidates["G: squeezing"]["residual"]
    coupling_strength_residual = missing_axis_candidates["B: coupling_strength"]["residual"]
    live_carrier = carrier_rank["carrier_best"]["carrier_live_hopf_weyl"]
    live_honesty = carrier_rank["carrier_honesty_best"]["carrier_live_hopf_weyl"]
    carrier_rank_rows = carrier_rank["rows"]
    live_row_best_iab = [
        {
            "engine_type": row["engine_type"],
            "torus": row["torus"],
            "best_iab": max(row["carriers"]["carrier_live_hopf_weyl"].items(), key=lambda item: item[1]["I_AB"])[0],
            "best_ic": max(row["carriers"]["carrier_live_hopf_weyl"].items(), key=lambda item: item[1]["I_c"])[0],
        }
        for row in carrier_rank_rows
    ]
    mispair_summary = mispair["summary"]
    c1_gate_map = {item["name"]: item for item in c1_bridge_object["gates"]}
    bridge_alignment = c1_gate_map["C1B3_bridge_object_is_bound_to_the_existing_support_contract"]["detail"]["bridge_owner_alignment"]
    signed_bridge_handoff = c1_gate_map["C1B3_bridge_object_is_bound_to_the_existing_support_contract"]["detail"]["carrier_handoff"]

    gates = [
        gate(
            formal_constraint_profile.get("observational", 0.0) >= 1.0
            and formal_constraint_profile.get("admissible", 0.0) >= 1.0
            and formal_constraint_profile.get("stable", 0.0) >= 1.0
            and formal_gate_map["G1_exact_hopf_geometry_truth"]["pass"]
            and formal_gate_map["G3_ambient_vs_engine_overlay"]["pass"]
            and formal_gate_map["G6_torus_negative_is_load_bearing"]["pass"]
            and formal_gate_map["G8_exact_loop_law_swap_negative"]["pass"]
            and formal_gate_map["G10_lower_tier_carrier_admission_and_classical_leakage_guards_are_explicit"]["pass"]
            and formal_gate_map["G11_chiral_readout_and_symmetric_bookkeeping_are_embargoed_from_law_promotion"]["pass"]
            and formal_gate_map["G12_lower_tier_chiral_law_search_is_explicit_and_fail_closed"]["pass"]
            and formal_gate_map["G14_lower_tier_operator_basis_search_is_explicit_and_fail_closed"]["pass"]
            and g10_detail["classical_leakage_guards"]["raw_lr_control_blocked"]["status"] == "control_only"
            and g10_detail["classical_leakage_guards"]["torus_scramble_kill"]["status"] == "KILL"
            and g10_detail["classical_leakage_guards"]["no_chirality_kill"]["status"] == "KILL"
            and g10_detail["classical_leakage_guards"]["loop_law_swap_kill"]["status"] == "KILL"
            and g11_detail["ga3_chirality"]["status"] == "readout_only"
            and g11_detail["symmetric_dphi_bookkeeping"]["status"] == "bookkeeping_only"
            and g11_detail["promotion_block"] == "awaiting_real_lower_tier_chiral_differential_law"
            and g12_detail["lower_tier_chiral_detail"]["summary"]["winner"] == "chirality_separated_transport_deltas"
            and g12_detail["lower_tier_chiral_detail"]["summary"]["winner_status"] == "surviving_compound_candidate"
            and g12_detail["lower_tier_chiral_detail"]["summary"]["single_lower_tier_chiral_law"] == "not_supported_yet"
            and g12_detail["lower_tier_chiral_detail"]["owner_read"]["status"] == "compound_candidate_only"
            and g14_detail["o4_detail"]["local_unitary_pair_Fe_Fi"]["status"] == "not_proven_load_bearing_in_local_test"
            and g14_detail["o4_detail"]["owner_read"]["status"] == "lower_tier_noncommuting_basis_split_survives_local_search",
            "R1_formal_geometry_prerequisite_is_closed",
            {
                "formal_constraint_profile": formal_constraint_profile,
                "formal_g1_pass": formal_gate_map["G1_exact_hopf_geometry_truth"]["pass"],
                "formal_g3_pass": formal_gate_map["G3_ambient_vs_engine_overlay"]["pass"],
                "formal_g6_pass": formal_gate_map["G6_torus_negative_is_load_bearing"]["pass"],
                "formal_g8_pass": formal_gate_map["G8_exact_loop_law_swap_negative"]["pass"],
                "formal_g10_pass": formal_gate_map["G10_lower_tier_carrier_admission_and_classical_leakage_guards_are_explicit"]["pass"],
                "formal_g11_pass": formal_gate_map["G11_chiral_readout_and_symmetric_bookkeeping_are_embargoed_from_law_promotion"]["pass"],
                "formal_g10_detail": g10_detail,
                "formal_g11_detail": g11_detail,
                "formal_g12_pass": formal_gate_map["G12_lower_tier_chiral_law_search_is_explicit_and_fail_closed"]["pass"],
                "formal_g12_detail": g12_detail["lower_tier_chiral_detail"],
                "formal_g14_pass": formal_gate_map["G14_lower_tier_operator_basis_search_is_explicit_and_fail_closed"]["pass"],
                "formal_g14_o4_detail": g14_detail["o4_detail"],
            },
        ),
        gate(
            step_ok(steps, "nonclassical_guard") and step_ok(steps, "ec3_identity"),
            "R2_root_guards_and_ec3_execute_cleanly",
            {
                "nonclassical_guard_ok": step_ok(steps, "nonclassical_guard"),
                "ec3_identity_ok": step_ok(steps, "ec3_identity"),
            },
        ),
        gate(
            step_ok(steps, "missing_axis_search")
            and missing_axis["best_residual"] > 0.85
            and missing_axis["best_candidate"] == "A: measurement_basis"
            and measurement_basis_residual > 0.85
            and squeezing_residual > 0.85
            and measurement_basis_residual > squeezing_residual > coupling_strength_residual
            and measurement_basis_residual - squeezing_residual > 0.05
            and squeezing_residual - coupling_strength_residual > 0.05
            and coupling_strength_residual < 0.85
            and missing_axis["candidates"]["C: coherence_class"]["residual"] < 1e-10,
            "R3_missing_axis_search_finds_uncaptured_structure",
            {
                "missing_axis_search_ok": step_ok(steps, "missing_axis_search"),
                "best_candidate": missing_axis["best_candidate"],
                "best_residual": missing_axis["best_residual"],
                "measurement_basis_residual": measurement_basis_residual,
                "squeezing_residual": squeezing_residual,
                "coupling_strength_residual": coupling_strength_residual,
                "measurement_basis_minus_squeezing": measurement_basis_residual - squeezing_residual,
                "squeezing_minus_coupling_strength": squeezing_residual - coupling_strength_residual,
                "coherence_class_residual": missing_axis["candidates"]["C: coherence_class"]["residual"],
            },
        ),
        gate(
            bridge_search["winner"] in {"Xi_chiral_entangle", "Xi_chiral_hist_entangle"}
            and bridge_search["mean_mi_by_candidate"]["Xi_LR_direct"] < 1e-12
            and bridge_search["mean_mi_by_candidate"][bridge_search["winner"]] > 0.4,
            "R4_bridge_search_rejects_direct_cartesian_carrier",
            {
                "winner": bridge_search["winner"],
                "winner_mean_mi": bridge_search["mean_mi_by_candidate"][bridge_search["winner"]],
                "lr_direct_mean_mi": bridge_search["mean_mi_by_candidate"]["Xi_LR_direct"],
            },
        ),
        gate(
            step_ok(steps, "carrier_rank")
            and live_carrier["best_candidate"] == "Xi_chiral_entangle"
            and live_carrier["best_mean_mi"] > 0.5
            and carrier_rank["best_control_mean_mi"] < 1e-3
            and carrier_rank["best_root_rank_margin"] > 0.5
            and all(row["best_ic"] == "Xi_chiral_entangle" for row in live_row_best_iab)
            and all(row["best_iab"] == "Xi_chiral_entangle" for row in live_row_best_iab),
            "R5_small_carrier_family_selects_live_hopf_weyl",
            {
                "live_best_candidate": live_carrier["best_candidate"],
                "live_best_mean_mi": live_carrier["best_mean_mi"],
                "best_control_mean_mi": carrier_rank["best_control_mean_mi"],
                "best_root_rank_margin": carrier_rank["best_root_rank_margin"],
                "live_row_best_iab": live_row_best_iab,
            },
        ),
        gate(
            step_ok(steps, "carrier_rank")
            and live_honesty["best_candidate"] == "Xi_chiral_entangle"
            and live_honesty["best_mean_i_c"] > 0.02
            and carrier_rank["best_control_honesty_score"] == 0.0
            and carrier_rank["best_honesty_margin"] > 0.02
            and all(row["best_ic"] == "Xi_chiral_entangle" for row in live_row_best_iab),
            "R6_live_carrier_keeps_unique_positive_honesty_signal",
            {
                "live_honesty_candidate": live_honesty["best_candidate"],
                "live_honesty_mean_i_c": live_honesty["best_mean_i_c"],
                "live_honesty_mean_mi": live_honesty["best_mean_mi"],
                "best_control_honesty_score": carrier_rank["best_control_honesty_score"],
                "best_honesty_margin": carrier_rank["best_honesty_margin"],
                "live_row_best_iab": live_row_best_iab,
            },
        ),
        gate(
            step_ok(steps, "history_mispair_counterfeit")
            and mispair_summary["mean_counterfeit_I_AB"] > 0.9 * mispair_summary["mean_live_I_AB"]
            and mispair_summary["mean_live_I_c"] > mispair_summary["mean_counterfeit_I_c"]
            and mispair_summary["mean_I_c_gap"] > 0.05
            and mispair_summary["live_beats_counterfeit_on_I_c_count"] >= 4,
            "R7_mispair_counterfeit_games_mi_but_not_coherent_info",
            {
                "mean_live_I_AB": mispair_summary["mean_live_I_AB"],
                "mean_counterfeit_I_AB": mispair_summary["mean_counterfeit_I_AB"],
                "mean_live_I_c": mispair_summary["mean_live_I_c"],
                "mean_counterfeit_I_c": mispair_summary["mean_counterfeit_I_c"],
                "mean_I_c_gap": mispair_summary["mean_I_c_gap"],
                "counterfeit_beats_live_on_I_AB_count": mispair_summary["counterfeit_beats_live_on_I_AB_count"],
                "live_beats_counterfeit_on_I_c_count": mispair_summary["live_beats_counterfeit_on_I_c_count"],
            },
        ),
        gate(
            not level1["Ti"]["universal"]
            and level1["Fi"]["universal"]
            and level2["Fi"]["universal"]
            and not level1["Fe"]["universal"]
            and not level1["Te"]["universal"]
            and not level2["Ti"]["universal"]
            and not level2["Fe"]["universal"]
            and not level2["Te"]["universal"]
            and coarising["algebraic_structure"].startswith("TRAJECTORY-SPECIFIC"),
            "R8_coarising_is_attractor_specific_not_universal_algebra",
            {
                "ti_level1_universal": level1["Ti"]["universal"],
                "fi_level1_universal": level1["Fi"]["universal"],
                "ti_level2_universal": level2["Ti"]["universal"],
                "fi_level2_universal": level2["Fi"]["universal"],
                "fe_level1_universal": level1["Fe"]["universal"],
                "te_level1_universal": level1["Te"]["universal"],
                "fe_level2_universal": level2["Fe"]["universal"],
                "te_level2_universal": level2["Te"]["universal"],
                "algebraic_structure": coarising["algebraic_structure"],
            },
        ),
        gate(
            packet_run["all_ok"]
            and not all(result["universal"] for result in level1.values())
            and not all(result["universal"] for result in level2.values())
            and coarising["level3_geometry"]["total_trials"] == 0
            and step_ok(steps, "orbit_phase_alignment")
            and orbit_phase["n_total_failures"] > 0
            and (
                orbit_phase["guard_event_count"] > 0
                or any(stats["fail"] > 0 for stats in orbit_phase_stats.values())
            )
            and any(stats["fail"] > 0 for stats in orbit_phase_stats.values()),
            "R9_root_emergence_remains_open_without_smuggling",
            {
                "all_ok": packet_run["all_ok"],
                "all_level1_universal": all(result["universal"] for result in level1.values()),
                "all_level2_universal": all(result["universal"] for result in level2.values()),
                "level3_total_trials": coarising["level3_geometry"]["total_trials"],
                "orbit_phase_alignment_ok": step_ok(steps, "orbit_phase_alignment"),
                "orbit_guard_event_count": orbit_phase["guard_event_count"],
                "orbit_total_failures": orbit_phase["n_total_failures"],
                "orbit_phase_stats": orbit_phase_stats,
                "orbit_half_stats": orbit_half_stats,
            },
        ),
        gate(
            attractor_constraint_profile.get("admissible", 0.0) >= 1.0
            and attractor_constraint_profile.get("entropy_conditioned", 0.0) >= 1.0
            and attractor_constraint_profile.get("topology_conditioned", 0.0) >= 1.0
            and step_ok(steps, "attractor_basin_boundary")
            and q3_basin["threshold_accuracy"] > 0.9
            and ti_failure_threshold <= 0.05
            and min_trajectory_lr_asym > 0.3
            and ti_boundary_gap > 0.25,
            "R10A_attractor_basin_keeps_trajectory_far_from_ti_failure_boundary",
            {
                "attractor_constraint_profile": attractor_constraint_profile,
                "threshold_accuracy": q3_basin["threshold_accuracy"],
                "ti_failure_threshold": ti_failure_threshold,
                "min_trajectory_lr_asym": min_trajectory_lr_asym,
                "ti_boundary_gap": ti_boundary_gap,
            },
        ),
        gate(
            attractor_constraint_profile.get("stable", 0.0) >= 1.0
            and attractor_constraint_profile.get("topology_conditioned", 0.0) >= 1.0
            and step_ok(steps, "attractor_basin_boundary")
            and all(config["n_te_steps"] == 2 for config in q4_basin)
            and max_q4_norm_cyz <= -0.99
            and min_q4_lr_asym > 0.9,
            "R10B_te_steps_stay_on_antiparallel_yz_band_on_attractor",
            {
                "attractor_constraint_profile": attractor_constraint_profile,
                "config_count": len(q4_basin),
                "max_q4_norm_cyz": max_q4_norm_cyz,
                "min_q4_norm_cyz": min_q4_norm_cyz,
                "min_q4_lr_asym": min_q4_lr_asym,
            },
        ),
        gate(
            c1_constraint_profile.get("admissible", 0.0) >= 1.0
            and c1_constraint_profile.get("topology_conditioned", 0.0) >= 1.0
            and bridge_owner_alignment_ok(bridge_alignment)
            and bridge_search["winner"] == "Xi_chiral_entangle"
            and live_carrier["best_candidate"] == "Xi_chiral_entangle"
            and live_honesty["best_candidate"] == "Xi_chiral_entangle"
            and signed_bridge_handoff_ok(signed_bridge_handoff),
            "R10_root_emergence_bridge_winner_respects_xi_handoff_contract",
            {
                "c1_constraint_profile": c1_constraint_profile,
                "bridge_owner_alignment": bridge_alignment,
                "bridge_winner": bridge_search["winner"],
                "live_carrier_best_candidate": live_carrier["best_candidate"],
                "live_honesty_best_candidate": live_honesty["best_candidate"],
                "signed_bridge_handoff": signed_bridge_handoff,
            },
        ),
    ]

    passed = sum(1 for item in gates if item["pass"])
    gate_map = {item["name"]: item for item in gates}
    payload = {
        "name": "root_emergence_packet_validation",
        "timestamp": datetime.now(UTC).isoformat(),
        "passed_gates": passed,
        "total_gates": len(gates),
        "score": passed / len(gates) if gates else 0.0,
        "constraint_family_profile": _packet_constraint_family_profile(gate_map),
        "gates": gates,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if args.pretty:
        print("=" * 72)
        print("ROOT EMERGENCE PACKET VALIDATION")
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
