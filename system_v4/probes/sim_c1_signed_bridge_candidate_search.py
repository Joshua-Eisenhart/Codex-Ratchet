#!/usr/bin/env python3
"""
sim_c1_signed_bridge_candidate_search.py
========================================

Standalone C1 search surface for the current signed bridge candidate.

This surface is intentionally narrow:
  - it packages the current live bridge winner,
  - it requires counterfeit-resistant signed honesty,
  - it keeps final Xi doctrine, shell doctrine, and history-law replacement open.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SIM_RESULTS = ROOT / "a2_state" / "sim_results"
OUTPUT_PATH = SIM_RESULTS / "c1_signed_bridge_candidate_search_results.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    bridge_search = load_json(SIM_RESULTS / "axis0_bridge_search_results.json")
    mispair = load_json(SIM_RESULTS / "history_mispair_counterfeit_results.json")
    carrier_selection = load_json(SIM_RESULTS / "carrier_selection_packet_validation.json")
    matched_marginal = load_json(SIM_RESULTS / "matched_marginal_packet_validation.json")
    pre_entropy = load_json(SIM_RESULTS / "pre_entropy_packet_validation.json")
    entropy_readout = load_json(SIM_RESULTS / "entropy_readout_packet_validation.json")

    mean_mi = bridge_search["mean_mi_by_candidate"]
    mean_ic = bridge_search["mean_ic_by_candidate"]
    ranking = bridge_search["ranking"]
    mispair_summary = mispair["summary"]
    mapping = pre_entropy["pre_axis_admission_schema"]["current_mapping"]

    payload = {
        "name": "c1_signed_bridge_candidate_search",
        "timestamp": datetime.now(UTC).isoformat(),
        "candidate_object": {
            "name": "Xi_chiral_entangle",
            "status": "provisional_signed_bridge_candidate",
            "keep": True,
            "reason": "Xi_chiral_entangle is the current live bridge winner on the admitted carrier and survives counterfeit pressure only when signed honesty is enforced.",
            "evidence": {
                "bridge_winner": bridge_search["winner"],
                "ranking_head": ranking[:3],
                "winner_mean_mi": float(mean_mi["Xi_chiral_entangle"]),
                "winner_mean_i_c": float(mean_ic["Xi_chiral_entangle"]),
                "lr_direct_mean_mi": float(mean_mi["Xi_LR_direct"]),
                "runner_up": "Xi_chiral_hist_entangle",
                "runner_up_mean_mi": float(mean_mi["Xi_chiral_hist_entangle"]),
                "runner_up_mean_i_c": float(mean_ic["Xi_chiral_hist_entangle"]),
            },
        },
        "negative_family": {
            "history_mispair_counterfeit": {
                "status": "counterfeit_beats_mi_but_loses_signed_honesty",
                "keep": True,
                "reason": "The counterfeit history construction can inflate raw mutual information while still losing on signed coherent-information honesty.",
                "evidence": {
                    "mean_live_I_AB": float(mispair_summary["mean_live_I_AB"]),
                    "mean_counterfeit_I_AB": float(mispair_summary["mean_counterfeit_I_AB"]),
                    "mean_live_I_c": float(mispair_summary["mean_live_I_c"]),
                    "mean_counterfeit_I_c": float(mispair_summary["mean_counterfeit_I_c"]),
                    "mean_I_c_gap": float(mispair_summary["mean_I_c_gap"]),
                    "counterfeit_beats_live_on_I_AB_count": int(mispair_summary["counterfeit_beats_live_on_I_AB_count"]),
                    "live_beats_counterfeit_on_I_c_count": int(mispair_summary["live_beats_counterfeit_on_I_c_count"]),
                },
            },
        },
        "support_chain": {
            "carrier_selection_closed": carrier_selection["passed_gates"] == carrier_selection["total_gates"],
            "matched_marginal_closed": matched_marginal["passed_gates"] == matched_marginal["total_gates"],
            "pre_entropy_mapping": mapping["Xi_chiral_entangle"],
            "entropy_readout_current_bridge_gate": entropy_readout["gates"][9]["name"],
        },
        "unresolved": {
            "final_xi_owner_law": "open",
            "shell_doctrine": "open",
            "history_law_replacement": "open",
            "entropy_family_owner_doctrine": "open",
        },
        "owner_read": {
            "status": "admitted_executable_candidate_not_final_owner_law",
            "note": "This C1 surface packages the current signed bridge candidate without replacing xi_hist signed law or promoting Xi_chiral_entangle to final owner doctrine.",
        },
    }

    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
