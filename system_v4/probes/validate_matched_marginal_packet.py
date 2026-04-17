#!/usr/bin/env python3
"""
validate_matched_marginal_packet.py
===================================

Mechanical validator for the matched-marginal honesty layer.

This packet sits between bridge search and entropy readout:
  - Phase 4: strongest unconstrained bridge winner
  - Phase 5A: best marginal-preserving bridge family
  - Phase 6: exact-preserving point-reference honesty check
  - FE-indexed history refinement control
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
    signed_bridge_handoff_ok,
)
from axis0_constraint_types import build_constraint_family_profile
from axis0_result_loader import load_axis0_result


ROOT = Path(__file__).resolve().parent
SIM_RESULTS = ROOT / "a2_state" / "sim_results"
OUTPUT_PATH = SIM_RESULTS / "matched_marginal_packet_validation.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(ok: bool, name: str, detail: dict) -> dict:
    return {"name": name, "pass": bool(ok), "detail": detail}


def _packet_constraint_family_profile(gate_map: dict[str, dict]) -> dict[str, float]:
    observational_names = (
        "M1_phase4_and_phase5a_execute_cleanly",
        "M2_phase4_winner_fails_matched_marginal_filter",
    )
    admissible_names = (
        "M8_matched_marginal_layer_preserves_xi_downstream_handoff_contract",
        "M9_matched_marginal_stays_subordinate_to_xi_downstream_mapping",
    )
    stable_names = (
        "M3_phase5a_certifies_marginal_preserving_family",
        "M4_preserving_mi_collapses_while_chiral_mi_stays_large",
        "M5_optimizer_finds_no_nonproduct_preserving_advantage",
    )
    entropy_names = (
        "M6_exact_preserving_point_reference_stays_discriminator_only",
        "M7_fe_indexed_pairs_remain_the_strongest_structured_refinement_candidate",
    )
    topology_names = (
        "M3_phase5a_certifies_marginal_preserving_family",
        "M6_exact_preserving_point_reference_stays_discriminator_only",
        "M7_fe_indexed_pairs_remain_the_strongest_structured_refinement_candidate",
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    run_packet = load_json(SIM_RESULTS / "matched_marginal_packet_run_results.json")
    phase4 = load_axis0_result(SIM_RESULTS, "axis0_phase4_results.json")
    phase5a = load_axis0_result(SIM_RESULTS, "axis0_phase5a_results.json")
    phase6 = load_axis0_result(SIM_RESULTS, "axis0_phase6_point_reference_results.json")
    fe_indexed = load_axis0_result(SIM_RESULTS, "axis0_fe_indexed_xi_hist_results.json")
    pre_entropy = load_json(SIM_RESULTS / "pre_entropy_packet_validation.json")
    c1_bridge_object = load_json(SIM_RESULTS / "c1_bridge_object_packet_validation.json")

    phase5a_rows = phase5a["results"]
    final_rows = [row["final_state"] for row in phase5a_rows]
    hist_rows = [row["history_averaged"] for row in phase5a_rows]
    final_checks = [row["final_state"]["marginal_check"] for row in phase5a_rows]
    hist_checks = [row["history_averaged"]["marginal_check"] for row in phase5a_rows]
    phase6_verdict = phase6["verdict"]
    fe_summary = fe_indexed["summary"]
    fe_rows = fe_indexed["results"]
    fe_pairs_only_beats_phase4_on_ic_count = sum(
        1
        for row in fe_rows
        if row["bridges"]["C_fe_pairs_only"]["ic"] > row["bridges"]["A_phase4_winner"]["ic"]
    )
    c1_gate_map = {item["name"]: item for item in c1_bridge_object["gates"]}
    signed_bridge_handoff = c1_gate_map["C1B3_bridge_object_is_bound_to_the_existing_support_contract"]["detail"]["carrier_handoff"]

    gates = [
        gate(
            run_packet["all_ok"],
            "M1_phase4_and_phase5a_execute_cleanly",
            {
                "all_ok": run_packet["all_ok"],
                "steps": [{k: step[k] for k in ("label", "ok", "returncode")} for step in run_packet["steps"]],
            },
        ),
        gate(
            not phase4["winner_preserves_marginals"]
            and phase4["matched_marginal_winner"] is None
            and phase4["matched_marginal_tolerance"] == 1e-3,
            "M2_phase4_winner_fails_matched_marginal_filter",
            {
                "winner": phase4["winner"],
                "winner_preserves_marginals": phase4["winner_preserves_marginals"],
                "matched_marginal_winner": phase4["matched_marginal_winner"],
                "matched_marginal_tolerance": phase4["matched_marginal_tolerance"],
            },
        ),
        gate(
            phase5a["certified_blocks"] == phase5a["total_blocks"]
            and phase5a["failed_blocks"] == 0
            and all(check["preserves_marginals_within_tol"] for check in final_checks + hist_checks),
            "M3_phase5a_certifies_marginal_preserving_family",
            {
                "certified_blocks": phase5a["certified_blocks"],
                "total_blocks": phase5a["total_blocks"],
                "failed_blocks": phase5a["failed_blocks"],
                "max_final_dev_A": max(check["dev_A"] for check in final_checks),
                "max_final_dev_B": max(check["dev_B"] for check in final_checks),
                "max_hist_dev_A": max(check["dev_A"] for check in hist_checks),
                "max_hist_dev_B": max(check["dev_B"] for check in hist_checks),
            },
        ),
        gate(
            phase5a["mean_preserving"] < 1e-12
            and phase5a["mean_chiral"] > 1.0
            and max(row["ratio_preserving_to_chiral"] for row in final_rows + hist_rows) < 1e-12,
            "M4_preserving_mi_collapses_while_chiral_mi_stays_large",
            {
                "mean_preserving": phase5a["mean_preserving"],
                "mean_chiral": phase5a["mean_chiral"],
                "max_ratio_preserving_to_chiral": max(row["ratio_preserving_to_chiral"] for row in final_rows + hist_rows),
            },
        ),
        gate(
            all(row["best_source"] == "product_seed" for row in final_checks + hist_checks)
            and max(row["max_preserving_MI"] for row in final_rows + hist_rows) < 1e-12,
            "M5_optimizer_finds_no_nonproduct_preserving_advantage",
            {
                "best_sources": sorted(set(row["best_source"] for row in final_checks + hist_checks)),
                "max_preserving_MI": max(row["max_preserving_MI"] for row in final_rows + hist_rows),
            },
        ),
        gate(
            not phase6_verdict["point_reference_earned_bridge_survives"]
            and phase6_verdict["mean_best_exact_I_AB"] < 1e-12
            and phase6_verdict["base_exact_nontrivial_count"] == 0
            and phase6_verdict["fiber_exact_nontrivial_count"] == 0,
            "M6_exact_preserving_point_reference_stays_discriminator_only",
            {
                "mean_best_exact_I_AB": phase6_verdict["mean_best_exact_I_AB"],
                "mean_best_tol_1e3_I_AB": phase6_verdict["mean_best_tol_1e3_I_AB"],
                "base_exact_nontrivial_count": phase6_verdict["base_exact_nontrivial_count"],
                "fiber_exact_nontrivial_count": phase6_verdict["fiber_exact_nontrivial_count"],
                "controller_read": phase6_verdict["controller_read"],
            },
        ),
        gate(
            fe_summary["best_new_bridge"] == "C_fe_pairs_only"
            and fe_summary["best_gain"] < 0.0
            and fe_summary["best_gain"] > -0.1
            and fe_summary["mean_fe_advantage"] > 0.1
            and fe_summary["winner_counts"]["A_phase4_winner"] == len(fe_rows)
            and fe_summary["winner_counts"]["B_fe_indexed"] == 0
            and fe_summary["winner_counts"]["C_fe_pairs_only"] == 0
            and fe_summary["winner_counts"]["D_lag7_pairs"] == 0
            and fe_summary["mean_mi"]["A_phase4_winner"] > fe_summary["mean_mi"]["C_fe_pairs_only"]
            and fe_summary["mean_ic"]["A_phase4_winner"] > fe_summary["mean_ic"]["C_fe_pairs_only"]
            and fe_summary["mean_mi"]["C_fe_pairs_only"] > fe_summary["mean_mi"]["B_fe_indexed"]
            and fe_summary["mean_mi"]["C_fe_pairs_only"] > fe_summary["mean_mi"]["D_lag7_pairs"]
            and fe_summary["mean_ic"]["C_fe_pairs_only"] > fe_summary["mean_ic"]["B_fe_indexed"]
            and fe_summary["mean_ic"]["C_fe_pairs_only"] > fe_summary["mean_ic"]["D_lag7_pairs"]
            and fe_pairs_only_beats_phase4_on_ic_count == 0,
            "M7_fe_indexed_pairs_remain_the_strongest_structured_refinement_candidate",
            {
                "best_new_bridge": fe_summary["best_new_bridge"],
                "best_gain": fe_summary["best_gain"],
                "mean_fe_advantage": fe_summary["mean_fe_advantage"],
                "mean_mi": fe_summary["mean_mi"],
                "mean_ic": fe_summary["mean_ic"],
                "winner_counts": fe_summary["winner_counts"],
                "fe_pairs_only_beats_phase4_on_ic_count": fe_pairs_only_beats_phase4_on_ic_count,
            },
        ),
        gate(
            signed_bridge_handoff_ok(signed_bridge_handoff)
            and not phase4["winner_preserves_marginals"]
            and phase4["matched_marginal_winner"] is None
            and not phase6_verdict["point_reference_earned_bridge_survives"]
            and phase6_verdict["point_reference_discriminator_survives"],
            "M8_matched_marginal_layer_preserves_xi_downstream_handoff_contract",
            {
                "signed_bridge_handoff": signed_bridge_handoff,
                "phase4_winner": phase4["winner"],
                "phase4_winner_preserves_marginals": phase4["winner_preserves_marginals"],
                "phase4_matched_marginal_winner": phase4["matched_marginal_winner"],
                "phase6_point_reference_earned_bridge_survives": phase6_verdict["point_reference_earned_bridge_survives"],
                "phase6_point_reference_discriminator_survives": phase6_verdict["point_reference_discriminator_survives"],
            },
        ),
        gate(
            pre_entropy["owner_worthiness_map"]["owner_derived"]["xi_hist_signed_law"] == "admitted"
            and axis_internal_readout_ok(pre_entropy["owner_worthiness_map"]["axis_internal_readout"])
            and axis_internal_mapping_ok(pre_entropy["pre_axis_admission_schema"]["current_mapping"])
            and axis_internal_placement_ok(pre_entropy["pre_axis_admission_schema"]["placement_relations"])
            and pre_entropy["pre_axis_admission_schema"]["placement_relations"]["xi_hist_signed_law"]
            == "owner_derived_law_that_binds_bridge_handoff"
            and signed_bridge_handoff_ok(signed_bridge_handoff)
            and not phase4["winner_preserves_marginals"]
            and phase4["matched_marginal_winner"] is None
            and not phase6_verdict["point_reference_earned_bridge_survives"]
            and phase6_verdict["point_reference_discriminator_survives"],
            "M9_matched_marginal_stays_subordinate_to_xi_downstream_mapping",
            {
                "signed_bridge_handoff": signed_bridge_handoff,
                "pre_entropy_axis_internal_readout": pre_entropy["owner_worthiness_map"]["axis_internal_readout"],
                "pre_entropy_current_mapping": pre_entropy["pre_axis_admission_schema"]["current_mapping"],
                "pre_entropy_placement_relations": pre_entropy["pre_axis_admission_schema"]["placement_relations"],
                "phase4_winner_preserves_marginals": phase4["winner_preserves_marginals"],
                "phase4_matched_marginal_winner": phase4["matched_marginal_winner"],
                "phase6_point_reference_earned_bridge_survives": phase6_verdict["point_reference_earned_bridge_survives"],
                "phase6_point_reference_discriminator_survives": phase6_verdict["point_reference_discriminator_survives"],
            },
        ),
    ]

    passed = sum(1 for item in gates if item["pass"])
    gate_map = {item["name"]: item for item in gates}
    payload = {
        "name": "matched_marginal_packet_validation",
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
        print("MATCHED MARGINAL PACKET VALIDATION")
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
