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


ROOT = Path(__file__).resolve().parent
SIM_RESULTS = ROOT / "a2_state" / "sim_results"
LEGACY_RESULTS = ROOT.parent / "a2_state" / "sim_results"
OUTPUT_PATH = SIM_RESULTS / "root_emergence_packet_validation.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(ok: bool, name: str, detail: dict) -> dict:
    return {"name": name, "pass": bool(ok), "detail": detail}


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
    bridge_search = load_json(SIM_RESULTS / "axis0_bridge_search_results.json")
    carrier_rank = load_json(SIM_RESULTS / "root_constraint_carrier_rank_results.json")
    mispair = load_json(SIM_RESULTS / "history_mispair_counterfeit_results.json")
    coarising = load_json(SIM_RESULTS / "axis0_coarising_stress_test_results.json")
    attractor_basin = load_json(SIM_RESULTS / "axis0_attractor_basin_boundary_results.json")
    c1_bridge_object = load_json(SIM_RESULTS / "c1_bridge_object_packet_validation.json")

    steps = packet_run["steps"]
    formal_gate_map = {item["name"]: item for item in formal_geometry["gates"]}
    level1 = coarising["level1_lr_asym"]
    level2 = coarising["level2_bridge_mi"]
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
    live_carrier = carrier_rank["carrier_best"]["carrier_live_hopf_weyl"]
    live_honesty = carrier_rank["carrier_honesty_best"]["carrier_live_hopf_weyl"]
    mispair_summary = mispair["summary"]
    c1_gate_map = {item["name"]: item for item in c1_bridge_object["gates"]}
    signed_bridge_handoff = c1_gate_map["C1B3_bridge_object_is_bound_to_the_existing_support_contract"]["detail"]["carrier_handoff"]

    gates = [
        gate(
            formal_gate_map["G1_exact_hopf_geometry_truth"]["pass"]
            and formal_gate_map["G3_ambient_vs_engine_overlay"]["pass"]
            and formal_gate_map["G6_torus_negative_is_load_bearing"]["pass"]
            and formal_gate_map["G8_exact_loop_law_swap_negative"]["pass"]
            and formal_gate_map["G10_lower_tier_carrier_admission_and_classical_leakage_guards_are_explicit"]["pass"]
            and formal_gate_map["G11_chiral_readout_and_symmetric_bookkeeping_are_embargoed_from_law_promotion"]["pass"]
            and formal_gate_map["G14_lower_tier_operator_basis_search_is_explicit_and_fail_closed"]["pass"],
            "R1_formal_geometry_prerequisite_is_closed",
            {
                "formal_g1_pass": formal_gate_map["G1_exact_hopf_geometry_truth"]["pass"],
                "formal_g3_pass": formal_gate_map["G3_ambient_vs_engine_overlay"]["pass"],
                "formal_g6_pass": formal_gate_map["G6_torus_negative_is_load_bearing"]["pass"],
                "formal_g8_pass": formal_gate_map["G8_exact_loop_law_swap_negative"]["pass"],
                "formal_g10_pass": formal_gate_map["G10_lower_tier_carrier_admission_and_classical_leakage_guards_are_explicit"]["pass"],
                "formal_g11_pass": formal_gate_map["G11_chiral_readout_and_symmetric_bookkeeping_are_embargoed_from_law_promotion"]["pass"],
                "formal_g14_pass": formal_gate_map["G14_lower_tier_operator_basis_search_is_explicit_and_fail_closed"]["pass"],
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
            missing_axis["best_residual"] > 0.85
            and missing_axis["best_candidate"] in {"A: measurement_basis", "G: squeezing"}
            and missing_axis["candidates"]["C: coherence_class"]["residual"] < 1e-10,
            "R3_missing_axis_search_finds_uncaptured_structure",
            {
                "best_candidate": missing_axis["best_candidate"],
                "best_residual": missing_axis["best_residual"],
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
            and carrier_rank["best_root_rank_margin"] > 0.5,
            "R5_small_carrier_family_selects_live_hopf_weyl",
            {
                "live_best_candidate": live_carrier["best_candidate"],
                "live_best_mean_mi": live_carrier["best_mean_mi"],
                "best_control_mean_mi": carrier_rank["best_control_mean_mi"],
                "best_root_rank_margin": carrier_rank["best_root_rank_margin"],
            },
        ),
        gate(
            step_ok(steps, "carrier_rank")
            and live_honesty["best_candidate"] == "Xi_chiral_entangle"
            and live_honesty["best_mean_i_c"] > 0.05
            and carrier_rank["best_control_honesty_score"] == 0.0
            and carrier_rank["best_honesty_margin"] > 0.05,
            "R6_live_carrier_keeps_unique_positive_honesty_signal",
            {
                "live_honesty_candidate": live_honesty["best_candidate"],
                "live_honesty_mean_i_c": live_honesty["best_mean_i_c"],
                "live_honesty_mean_mi": live_honesty["best_mean_mi"],
                "best_control_honesty_score": carrier_rank["best_control_honesty_score"],
                "best_honesty_margin": carrier_rank["best_honesty_margin"],
            },
        ),
        gate(
            step_ok(steps, "history_mispair_counterfeit")
            and mispair_summary["mean_counterfeit_I_AB"] > mispair_summary["mean_live_I_AB"]
            and mispair_summary["mean_live_I_c"] > mispair_summary["mean_counterfeit_I_c"]
            and mispair_summary["mean_I_c_gap"] > 0.05
            and mispair_summary["counterfeit_beats_live_on_I_AB_count"] >= 4
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
            and coarising["level3_geometry"]["total_trials"] == 0,
            "R9_root_emergence_remains_open_without_smuggling",
            {
                "all_ok": packet_run["all_ok"],
                "all_level1_universal": all(result["universal"] for result in level1.values()),
                "all_level2_universal": all(result["universal"] for result in level2.values()),
                "level3_total_trials": coarising["level3_geometry"]["total_trials"],
            },
        ),
        gate(
            step_ok(steps, "attractor_basin_boundary")
            and q3_basin["threshold_accuracy"] > 0.9
            and ti_failure_threshold <= 0.05
            and min_trajectory_lr_asym > 0.3
            and ti_boundary_gap > 0.25,
            "R10A_attractor_basin_keeps_trajectory_far_from_ti_failure_boundary",
            {
                "threshold_accuracy": q3_basin["threshold_accuracy"],
                "ti_failure_threshold": ti_failure_threshold,
                "min_trajectory_lr_asym": min_trajectory_lr_asym,
                "ti_boundary_gap": ti_boundary_gap,
            },
        ),
        gate(
            step_ok(steps, "attractor_basin_boundary")
            and all(config["n_te_steps"] == 2 for config in q4_basin)
            and max_q4_norm_cyz <= -0.99
            and min_q4_lr_asym > 0.9,
            "R10B_te_steps_stay_on_antiparallel_yz_band_on_attractor",
            {
                "config_count": len(q4_basin),
                "max_q4_norm_cyz": max_q4_norm_cyz,
                "min_q4_norm_cyz": min_q4_norm_cyz,
                "min_q4_lr_asym": min_q4_lr_asym,
            },
        ),
        gate(
            bridge_search["winner"] == "Xi_chiral_entangle"
            and live_carrier["best_candidate"] == "Xi_chiral_entangle"
            and live_honesty["best_candidate"] == "Xi_chiral_entangle"
            and signed_bridge_handoff["candidate"] == "Xi_chiral_entangle"
            and signed_bridge_handoff["status"] == "provisional_handoff_ready"
            and signed_bridge_handoff["placement_contract"] == "downstream_axis_internal_bridge_candidate_only"
            and signed_bridge_handoff["owner_dependency"] == "must_bind_under_xi_hist_signed_law"
            and signed_bridge_handoff["forbidden_reclassification"] == "not_owner_derived_not_final_owner_xi"
            and signed_bridge_handoff["consumer_status"] == "allowed_for_entropy_readout_not_final_owner_xi",
            "R10_root_emergence_bridge_winner_respects_xi_handoff_contract",
            {
                "bridge_winner": bridge_search["winner"],
                "live_carrier_best_candidate": live_carrier["best_candidate"],
                "live_honesty_best_candidate": live_honesty["best_candidate"],
                "signed_bridge_handoff": signed_bridge_handoff,
            },
        ),
    ]

    passed = sum(1 for item in gates if item["pass"])
    payload = {
        "name": "root_emergence_packet_validation",
        "timestamp": datetime.now(UTC).isoformat(),
        "passed_gates": passed,
        "total_gates": len(gates),
        "score": passed / len(gates) if gates else 0.0,
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
