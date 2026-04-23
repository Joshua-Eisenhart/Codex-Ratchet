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

from axis0_bridge_owner_alignment_contract import (
    build_non_owner_reservation,
    build_owner_read,
    build_signed_bridge_handoff,
    c1_signed_bridge_handoff_read,
    c1_signed_candidate_owner_note,
    current_bridge_gate_name,
)

classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical packaging baseline: this packages the current signed C1 bridge candidate for downstream readout, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "python_stdlib": {"tried": True, "used": True, "reason": "JSON packet assembly from prior result artifacts"},
}
TOOL_INTEGRATION_DEPTH = {"python_stdlib": "supportive"}


ROOT = Path(__file__).resolve().parent
SIM_RESULTS = ROOT / "a2_state" / "sim_results"
OUTPUT_PATH = SIM_RESULTS / "c1_signed_bridge_candidate_search_results.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    bridge_search = load_json(SIM_RESULTS / "axis0_bridge_search_results.json")
    mispair = load_json(SIM_RESULTS / "history_mispair_counterfeit_results.json")
    matched_marginal = load_json(SIM_RESULTS / "matched_marginal_packet_validation.json")
    pre_entropy = load_json(SIM_RESULTS / "pre_entropy_packet_validation.json")
    entropy_readout = load_json(SIM_RESULTS / "entropy_readout_packet_validation.json")

    mean_mi = bridge_search["mean_mi_by_candidate"]
    mean_ic = bridge_search["mean_ic_by_candidate"]
    ranking = bridge_search["ranking"]
    bridge_alignment = bridge_search["xi_hist_owner_alignment"]
    mispair_summary = mispair["summary"]
    matched_gate_map = {item["name"]: item for item in matched_marginal["gates"]}
    matched_marginal_required_gates = [
        "M1_phase4_and_phase5a_execute_cleanly",
        "M2_phase4_winner_fails_matched_marginal_filter",
        "M3_phase5a_certifies_marginal_preserving_family",
        "M4_preserving_mi_collapses_while_chiral_mi_stays_large",
        "M5_optimizer_finds_no_nonproduct_preserving_advantage",
        "M6_exact_preserving_point_reference_stays_discriminator_only",
        "M8_matched_marginal_layer_preserves_xi_downstream_handoff_contract",
        "M9_matched_marginal_stays_subordinate_to_xi_downstream_mapping",
    ]
    matched_marginal_required_passes = {
        gate_name: bool(matched_gate_map[gate_name]["pass"]) for gate_name in matched_marginal_required_gates
    }
    mapping = pre_entropy["pre_axis_admission_schema"]["current_mapping"]
    placement_relations = pre_entropy["pre_axis_admission_schema"]["placement_relations"]
    axis_internal_readout = pre_entropy["owner_worthiness_map"]["axis_internal_readout"]
    downstream_handoff = build_signed_bridge_handoff(
        bridge_owner_alignment=bridge_alignment,
        extra_fields={
            "object": "c1_signed_bridge_candidate_handoff",
            "origin_surface": "sim_c1_signed_bridge_candidate_search",
            "support_chain_gate": "C1S3_support_chain_is_closed_before_candidate_packaging",
            "signed_metric": "I_c",
            "read": c1_signed_bridge_handoff_read(),
        },
    )

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
            "bridge_owner_alignment": bridge_alignment,
            "carrier_handoff": downstream_handoff,
            "matched_marginal_closed": all(matched_marginal_required_passes.values()),
            "matched_marginal_contract_scope": "xi_downstream_handoff_and_honesty_layer",
            "matched_marginal_required_gates": matched_marginal_required_gates,
            "matched_marginal_required_passes": matched_marginal_required_passes,
            "matched_marginal_excluded_failures": [
                item["name"]
                for item in matched_marginal["gates"]
                if not item["pass"] and item["name"] not in matched_marginal_required_gates
            ],
            "pre_entropy_mapping": mapping["Xi_chiral_entangle"],
            "pre_entropy_relation": axis_internal_readout["Xi_chiral_entangle_relation"],
            "pre_entropy_placement": placement_relations["Xi_chiral_entangle"],
            "entropy_readout_current_bridge_gate": current_bridge_gate_name(),
        },
        "downstream_handoff": downstream_handoff,
        "unresolved": build_non_owner_reservation(),
        "owner_read": build_owner_read(note=c1_signed_candidate_owner_note()),
    }

    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
