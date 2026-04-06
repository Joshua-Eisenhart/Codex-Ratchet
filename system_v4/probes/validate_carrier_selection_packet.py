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


ROOT = Path(__file__).resolve().parent
SIM_RESULTS = ROOT / "a2_state" / "sim_results"
LEGACY_RESULTS = ROOT.parent / "a2_state" / "sim_results"
OUTPUT_PATH = SIM_RESULTS / "carrier_selection_packet_validation.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(ok: bool, name: str, detail: dict) -> dict:
    return {"name": name, "pass": bool(ok), "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    run_packet = load_json(SIM_RESULTS / "carrier_selection_packet_run_results.json")
    missing_axis = load_json(LEGACY_RESULTS / "missing_axis_search_results.json")
    bridge_search = load_json(SIM_RESULTS / "axis0_bridge_search_results.json")
    xi_strict = load_json(SIM_RESULTS / "axis0_xi_strict_bakeoff_results.json")
    carrier_rank = load_json(SIM_RESULTS / "root_constraint_carrier_rank_results.json")
    mispair = load_json(SIM_RESULTS / "history_mispair_counterfeit_results.json")

    discriminators = xi_strict["verdict"]["discriminators"]
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
    signed_bridge_candidate_handoff = {
        "object": "c1_signed_bridge_candidate_handoff",
        "candidate": "Xi_chiral_entangle",
        "status": "provisional_handoff_ready",
        "placement_contract": "downstream_axis_internal_bridge_candidate_only",
        "owner_dependency": "must_bind_under_xi_hist_signed_law",
        "forbidden_reclassification": "not_owner_derived_not_final_owner_xi",
        "positive_witness_gate": "C3_live_carrier_wins_and_honesty_signal_stays_unique",
        "bridge_separation_gate": "C4_bridge_search_separates_winning_bridges_from_controls",
        "counterfeit_guard_gate": "C7_counterfeit_history_games_mi_but_not_coherent_info",
        "signed_metric": "I_c",
        "consumer_status": "allowed_for_entropy_readout_not_final_owner_xi",
        "read": "Xi_chiral_entangle is the current signed bridge candidate handoff object for downstream readout use, but it is not a final owner law.",
    }

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
            and live_honesty["best_mean_i_c"] > 0.05
            and carrier_rank["best_control_mean_mi"] < 1e-3
            and carrier_rank["best_root_rank_margin"] > 0.5
            and carrier_rank["best_control_honesty_score"] == 0.0
            and carrier_rank["best_honesty_margin"] > 0.05
            and all(row["best_ic"] == "Xi_chiral_entangle" for row in live_row_best_iab)
            and sum(row["best_iab"] == "Xi_chiral_entangle" for row in live_row_best_iab) == 4
            and sum(row["best_iab"] == "Xi_chiral_hist_entangle" for row in live_row_best_iab) == 2
            and all(
                row["best_iab"] == "Xi_chiral_hist_entangle"
                for row in live_row_best_iab
                if row["engine_type"] == 1 and row["torus"] in {"inner", "outer"}
            )
            and all(
                row["best_iab"] == "Xi_chiral_entangle"
                for row in live_row_best_iab
                if not (row["engine_type"] == 1 and row["torus"] in {"inner", "outer"})
            ),
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
            discriminators["hist_outer_minus_lr_mi"] > 0.005
            and discriminators["hist_cycle_minus_lr_mi"] > 0.005
            and discriminators["history_nontrivial_while_shell_flat"]
            and discriminators["point_ref_minus_shell_base_std"] > 0.1,
            "C5_strict_bakeoff_confirms_history_over_direct_lr",
            {
                "hist_outer_minus_lr_mi": discriminators["hist_outer_minus_lr_mi"],
                "hist_cycle_minus_lr_mi": discriminators["hist_cycle_minus_lr_mi"],
                "history_nontrivial_while_shell_flat": discriminators["history_nontrivial_while_shell_flat"],
                "point_ref_minus_shell_base_std": discriminators["point_ref_minus_shell_base_std"],
            },
        ),
        gate(
            bridge_search["winner"] == ranking[0]
            and "Xi_LR_direct" in ranking[-3:]
            and not xi_strict["verdict"]["means"]["xi_lr_direct_MI"] > 0.3,
            "C6_direct_lr_stays_ranked_as_control_not_winner",
            {
                "winner": bridge_search["winner"],
                "tail_ranking": ranking[-3:],
                "xi_lr_direct_MI": xi_strict["verdict"]["means"]["xi_lr_direct_MI"],
            },
        ),
        gate(
            run_packet["all_ok"]
            and mispair_summary["mean_counterfeit_I_AB"] > mispair_summary["mean_live_I_AB"]
            and mispair_summary["mean_live_I_c"] > mispair_summary["mean_counterfeit_I_c"]
            and mispair_summary["mean_I_c_gap"] > 0.05
            and mispair_summary["counterfeit_beats_live_on_I_AB_count"] >= 4
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
            signed_bridge_candidate_handoff["candidate"] == "Xi_chiral_entangle"
            and signed_bridge_candidate_handoff["status"] == "provisional_handoff_ready"
            and signed_bridge_candidate_handoff["consumer_status"] == "allowed_for_entropy_readout_not_final_owner_xi"
            and bridge_search["winner"] == "Xi_chiral_entangle"
            and live_honesty["best_candidate"] == "Xi_chiral_entangle"
            and live_honesty["best_mean_i_c"] > 0.05
            and mean_mi["Xi_LR_direct"] < 1e-12
            and mispair_summary["mean_live_I_c"] > mispair_summary["mean_counterfeit_I_c"],
            "C8_provisional_signed_bridge_candidate_handoff_is_explicit",
            {
                "signed_bridge_candidate_handoff": signed_bridge_candidate_handoff,
                "bridge_winner": bridge_search["winner"],
                "live_honesty_candidate": live_honesty["best_candidate"],
                "live_honesty_mean_i_c": live_honesty["best_mean_i_c"],
                "lr_direct_mean_mi": mean_mi["Xi_LR_direct"],
                "mean_live_I_c": mispair_summary["mean_live_I_c"],
                "mean_counterfeit_I_c": mispair_summary["mean_counterfeit_I_c"],
            },
        ),
        gate(
            signed_bridge_candidate_handoff["candidate"] == "Xi_chiral_entangle"
            and signed_bridge_candidate_handoff["status"] == "provisional_handoff_ready"
            and signed_bridge_candidate_handoff["placement_contract"] == "downstream_axis_internal_bridge_candidate_only"
            and signed_bridge_candidate_handoff["owner_dependency"] == "must_bind_under_xi_hist_signed_law"
            and signed_bridge_candidate_handoff["forbidden_reclassification"] == "not_owner_derived_not_final_owner_xi"
            and signed_bridge_candidate_handoff["consumer_status"] == "allowed_for_entropy_readout_not_final_owner_xi",
            "C9_handoff_contract_freezes_downstream_only_placement",
            {
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
    payload = {
        "name": "carrier_selection_packet_validation",
        "timestamp": datetime.now(UTC).isoformat(),
        "passed_gates": passed,
        "total_gates": len(gates),
        "score": passed / len(gates) if gates else 0.0,
        "signed_bridge_candidate_handoff": signed_bridge_candidate_handoff,
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
