#!/usr/bin/env python3
"""
validate_carrier_selection_packet.py
====================================

Mechanical validator for the current carrier-selection witness packet.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from axis0_bridge_owner_alignment_contract import (
    build_signed_bridge_handoff,
    bridge_owner_alignment_ok,
    signed_bridge_handoff_ok,
)
from axis0_constraint_types import build_constraint_family_profile
from axis0_result_loader import load_axis0_result
from axis0_xi_law_fingerprint import carrier_law_fingerprint


ROOT = Path(__file__).resolve().parent
SIM_RESULTS = ROOT / "a2_state" / "sim_results"
LEGACY_RESULTS = ROOT.parent / "a2_state" / "sim_results"
OUTPUT_PATH = SIM_RESULTS / "carrier_selection_packet_validation.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(ok: bool, name: str, detail: dict) -> dict:
    return {"name": name, "pass": bool(ok), "detail": detail}


def _packet_constraint_family_profile(gate_map: dict[str, dict]) -> dict[str, float]:
    observational_names = (
        "C1_search_and_bridge_surfaces_execute_cleanly",
        "C2_missing_axis_search_finds_uncaptured_candidate",
    )
    admissible_names = (
        "C8_provisional_signed_bridge_candidate_handoff_is_explicit",
        "C9_handoff_contract_freezes_downstream_only_placement",
    )
    stable_names = (
        "C3_live_carrier_wins_and_honesty_signal_stays_unique",
        "C4_bridge_search_separates_winning_bridges_from_controls",
        "C6_direct_lr_stays_ranked_as_control_not_winner",
    )
    entropy_names = (
        "C5_strict_bakeoff_confirms_structured_history_without_shell_shortcut",
        "C7_counterfeit_history_games_mi_but_not_coherent_info",
    )
    topology_names = (
        "C4_bridge_search_separates_winning_bridges_from_controls",
        "C5_strict_bakeoff_confirms_structured_history_without_shell_shortcut",
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

    run_packet = load_json(SIM_RESULTS / "carrier_selection_packet_run_results.json")
    missing_axis = load_json(LEGACY_RESULTS / "missing_axis_search_results.json")
    bridge_search = load_axis0_result(SIM_RESULTS, "axis0_bridge_search_results.json")
    xi_strict = load_axis0_result(SIM_RESULTS, "axis0_xi_strict_bakeoff_results.json")
    carrier_rank = load_json(SIM_RESULTS / "root_constraint_carrier_rank_results.json")
    mispair = load_json(SIM_RESULTS / "history_mispair_counterfeit_results.json")

    discriminators = xi_strict["verdict"]["discriminators"]
    history_window_sweep = xi_strict["verdict"]["history_window_sweep_summary"]
    placement_profile = xi_strict["verdict"]["history_window_placement_summary"]
    prefix_drop_profile = xi_strict["verdict"]["history_prefix_drop_summary"]
    bridge_alignment = bridge_search["xi_hist_owner_alignment"]
    ranking = bridge_search["ranking"]
    mean_mi = bridge_search["mean_mi_by_candidate"]
    carrier_best = carrier_rank["carrier_best"]
    carrier_honesty_best = carrier_rank["carrier_honesty_best"]
    live_carrier = carrier_best["carrier_live_hopf_weyl"]
    live_honesty = carrier_honesty_best["carrier_live_hopf_weyl"]
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
    dechiralized_control = carrier_best["carrier_dechiralized_history"]
    cartesian_control = carrier_best["carrier_cartesian_nohistory"]
    mispair_summary = mispair["summary"]
    signed_bridge_candidate_handoff = build_signed_bridge_handoff(
        bridge_owner_alignment=bridge_alignment,
        extra_fields={
            "object": "c1_signed_bridge_candidate_handoff",
            "positive_witness_gate": "C3_live_carrier_wins_and_honesty_signal_stays_unique",
            "bridge_separation_gate": "C4_bridge_search_separates_winning_bridges_from_controls",
            "counterfeit_guard_gate": "C7_counterfeit_history_games_mi_but_not_coherent_info",
            "signed_metric": "I_c",
            "read": (
                "Xi_chiral_entangle is the current signed bridge candidate handoff object "
                "for downstream readout use, but it is not a final owner law."
            ),
        },
    )

    gates = [
        gate(
            run_packet["all_ok"],
            "C1_search_and_bridge_surfaces_execute_cleanly",
            {
                "all_ok": run_packet["all_ok"],
                "steps": [{k: step[k] for k in ("label", "ok", "returncode")} for step in run_packet["steps"]],
            },
        ),
        gate(
            missing_axis["best_residual"] > 0.85
            and missing_axis["best_candidate"] == "A: measurement_basis"
            and missing_axis["candidates"]["C: coherence_class"]["residual"] < 1e-10,
            "C2_missing_axis_search_finds_uncaptured_candidate",
            {
                "best_candidate": missing_axis["best_candidate"],
                "best_residual": missing_axis["best_residual"],
                "coherence_class_residual": missing_axis["candidates"]["C: coherence_class"]["residual"],
            },
        ),
        gate(
            live_carrier["best_candidate"] == "Xi_chiral_entangle"
            and live_carrier["best_mean_mi"] > 0.5
            and live_honesty["best_candidate"] == "Xi_chiral_entangle"
            and live_honesty["best_mean_i_c"] > 0.02
            and carrier_rank["best_control_mean_mi"] < 1e-3
            and carrier_rank["best_root_rank_margin"] > 0.5
            and carrier_rank["best_control_honesty_score"] == 0.0
            and carrier_rank["best_honesty_margin"] > 0.02
            and all(row["best_ic"] == "Xi_chiral_entangle" for row in live_row_best_iab)
            and all(row["best_iab"] == "Xi_chiral_entangle" for row in live_row_best_iab),
            "C3_live_carrier_wins_and_honesty_signal_stays_unique",
            {
                "live_best_candidate": live_carrier["best_candidate"],
                "live_best_mean_mi": live_carrier["best_mean_mi"],
                "live_honesty_candidate": live_honesty["best_candidate"],
                "live_honesty_mean_i_c": live_honesty["best_mean_i_c"],
                "dechiralized_best_candidate": dechiralized_control["best_candidate"],
                "dechiralized_best_mean_mi": dechiralized_control["best_mean_mi"],
                "cartesian_best_candidate": cartesian_control["best_candidate"],
                "cartesian_best_mean_mi": cartesian_control["best_mean_mi"],
                "best_control_mean_mi": carrier_rank["best_control_mean_mi"],
                "best_root_rank_margin": carrier_rank["best_root_rank_margin"],
                "best_control_honesty_score": carrier_rank["best_control_honesty_score"],
                "best_honesty_margin": carrier_rank["best_honesty_margin"],
                "live_row_best_iab": live_row_best_iab,
            },
        ),
        gate(
            bridge_search["winner"] in {"Xi_chiral_entangle", "Xi_chiral_hist_entangle"}
            and mean_mi["Xi_LR_direct"] < 1e-12
            and mean_mi[ranking[0]] > 0.4
            and mean_mi[ranking[1]] > 0.4
            and mean_mi[ranking[2]] < 0.02,
            "C4_bridge_search_separates_winning_bridges_from_controls",
            {
                "winner": bridge_search["winner"],
                "top3": [(name, mean_mi[name]) for name in ranking[:3]],
                "lr_direct_mean_mi": mean_mi["Xi_LR_direct"],
            },
        ),
        gate(
            discriminators["history_nontrivial_while_shell_flat"]
            and discriminators["point_ref_minus_shell_base_std"] > 0.1
            and history_window_sweep["best_window_by_mi_counts"]["0_7"] == history_window_sweep["total_rows"]
            and placement_profile["best_placement_by_mi_counts"]["8_23"] == placement_profile["total_rows"]
            and placement_profile["early_window_beats_shifted_count"] == 0
            and prefix_drop_profile["best_prefix_drop_by_mi_counts"]["8_15"] == prefix_drop_profile["total_rows"],
            "C5_strict_bakeoff_confirms_structured_history_without_shell_shortcut",
            {
                "xi_lr_direct_mean_mi": xi_strict["verdict"]["means"]["xi_lr_direct_MI"],
                "hist_outer_minus_lr_mi": discriminators["hist_outer_minus_lr_mi"],
                "hist_cycle_minus_lr_mi": discriminators["hist_cycle_minus_lr_mi"],
                "history_nontrivial_while_shell_flat": discriminators["history_nontrivial_while_shell_flat"],
                "point_ref_minus_shell_base_std": discriminators["point_ref_minus_shell_base_std"],
                "best_window_by_mi_counts": history_window_sweep["best_window_by_mi_counts"],
                "best_placement_by_mi_counts": placement_profile["best_placement_by_mi_counts"],
                "early_window_beats_shifted_count": placement_profile["early_window_beats_shifted_count"],
                "best_prefix_drop_by_mi_counts": prefix_drop_profile["best_prefix_drop_by_mi_counts"],
            },
        ),
        gate(
            bridge_search["winner"] == ranking[0]
            and "Xi_LR_direct" in ranking[-3:]
            and mean_mi["Xi_LR_direct"] < 1e-12,
            "C6_direct_lr_stays_ranked_as_control_not_winner",
            {
                "winner": bridge_search["winner"],
                "tail_ranking": ranking[-3:],
                "xi_lr_direct_MI": xi_strict["verdict"]["means"]["xi_lr_direct_MI"],
            },
        ),
        gate(
            run_packet["all_ok"]
            and mispair_summary["mean_counterfeit_I_AB"] > 0.9 * mispair_summary["mean_live_I_AB"]
            and mispair_summary["mean_live_I_c"] > mispair_summary["mean_counterfeit_I_c"]
            and mispair_summary["mean_I_c_gap"] > 0.05
            and mispair_summary["live_beats_counterfeit_on_I_c_count"] >= 4,
            "C7_counterfeit_history_games_mi_but_not_coherent_info",
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
            bridge_owner_alignment_ok(bridge_alignment)
            and signed_bridge_handoff_ok(signed_bridge_candidate_handoff)
            and bridge_search["winner"] == "Xi_chiral_entangle"
            and live_honesty["best_candidate"] == "Xi_chiral_entangle"
            and live_honesty["best_mean_i_c"] > 0.02
            and mean_mi["Xi_LR_direct"] < 1e-12
            and mispair_summary["mean_live_I_c"] > mispair_summary["mean_counterfeit_I_c"],
            "C8_provisional_signed_bridge_candidate_handoff_is_explicit",
            {
                "signed_bridge_candidate_handoff": signed_bridge_candidate_handoff,
                "bridge_owner_alignment": bridge_alignment,
                "bridge_winner": bridge_search["winner"],
                "live_honesty_candidate": live_honesty["best_candidate"],
                "live_honesty_mean_i_c": live_honesty["best_mean_i_c"],
                "lr_direct_mean_mi": mean_mi["Xi_LR_direct"],
                "mean_live_I_c": mispair_summary["mean_live_I_c"],
                "mean_counterfeit_I_c": mispair_summary["mean_counterfeit_I_c"],
            },
        ),
        gate(
            bridge_owner_alignment_ok(bridge_alignment)
            and signed_bridge_handoff_ok(signed_bridge_candidate_handoff),
            "C9_handoff_contract_freezes_downstream_only_placement",
            {
                "bridge_owner_alignment": bridge_alignment,
                "candidate": signed_bridge_candidate_handoff["candidate"],
                "status": signed_bridge_candidate_handoff["status"],
                "placement_contract": signed_bridge_candidate_handoff["placement_contract"],
                "owner_dependency": signed_bridge_candidate_handoff["owner_dependency"],
                "forbidden_reclassification": signed_bridge_candidate_handoff["forbidden_reclassification"],
                "consumer_status": signed_bridge_candidate_handoff["consumer_status"],
            },
        ),
    ]

    passed = sum(1 for item in gates if item["pass"])
    gate_map = {item["name"]: item for item in gates}
    payload = {
        "name": "carrier_selection_packet_validation",
        "timestamp": datetime.now(UTC).isoformat(),
        "passed_gates": passed,
        "total_gates": len(gates),
        "score": passed / len(gates) if gates else 0.0,
        "signed_bridge_candidate_handoff": signed_bridge_candidate_handoff,
        "xi_hist_carrier_semantics": carrier_law_fingerprint({"gates": gates}),
        "constraint_family_profile": _packet_constraint_family_profile(gate_map),
        "gates": gates,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if args.pretty:
        print("=" * 72)
        print("CARRIER SELECTION PACKET VALIDATION")
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
