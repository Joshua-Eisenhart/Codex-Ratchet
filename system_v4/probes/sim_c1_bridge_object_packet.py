#!/usr/bin/env python3
"""
sim_c1_bridge_object_packet.py
==============================

Package the current C1 bridge object into a stable downstream-facing surface.

This surface is intentionally narrow:
  - it packages the current admitted bridge object for downstream readout use,
  - it binds that object to the existing signed-honesty and handoff evidence,
  - it keeps every owner-law question explicitly open.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from axis0_bridge_owner_alignment_contract import (
    build_non_owner_reservation,
    build_signed_bridge_handoff,
    c1_bridge_object_read,
    c1_signed_bridge_handoff_read,
    current_bridge_gate_name,
    current_bridge_gate_status,
    current_bridge_object_status,
)

classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical packaging baseline: this packages the current C1 bridge object for downstream readout, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "python_stdlib": {"tried": True, "used": True, "reason": "JSON packet assembly from prior result artifacts"},
}
TOOL_INTEGRATION_DEPTH = {"python_stdlib": "supportive"}


ROOT = Path(__file__).resolve().parent
SIM_RESULTS = ROOT / "a2_state" / "sim_results"
OUTPUT_PATH = SIM_RESULTS / "c1_bridge_object_packet_results.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    search = load_json(SIM_RESULTS / "c1_signed_bridge_candidate_search_results.json")
    search_validation = load_json(SIM_RESULTS / "c1_signed_bridge_candidate_search_validation.json")
    carrier_selection = load_json(SIM_RESULTS / "carrier_selection_packet_validation.json")
    pre_entropy = load_json(SIM_RESULTS / "pre_entropy_packet_validation.json")
    entropy_readout = load_json(SIM_RESULTS / "entropy_readout_packet_validation.json")

    candidate = search["candidate_object"]
    counterfeit = search["negative_family"]["history_mispair_counterfeit"]
    carrier_selection_handoff = carrier_selection["signed_bridge_candidate_handoff"]
    handoff = search.get("downstream_handoff") or build_signed_bridge_handoff(
        bridge_owner_alignment=search["support_chain"]["bridge_owner_alignment"],
        extra_fields={
            "object": "c1_signed_bridge_candidate_handoff",
            "origin_surface": "sim_c1_signed_bridge_candidate_search",
            "support_chain_gate": "C1S3_support_chain_is_closed_before_candidate_packaging",
            "signed_metric": "I_c",
            "read": c1_signed_bridge_handoff_read(),
        },
    )
    current_mapping = pre_entropy["pre_axis_admission_schema"]["current_mapping"]
    placement_relations = pre_entropy["pre_axis_admission_schema"]["placement_relations"]
    axis_internal_readout = pre_entropy["owner_worthiness_map"]["axis_internal_readout"]

    payload = {
        "name": "c1_bridge_object_packet",
        "timestamp": datetime.now(UTC).isoformat(),
        "bridge_object": {
            "name": "Xi_chiral_entangle",
            "status": current_bridge_object_status(),
            "keep": True,
            "scope": "downstream_readout_only",
            "consumer_status": handoff["consumer_status"],
            "read": c1_bridge_object_read(),
            "evidence": {
                "bridge_winner": candidate["evidence"]["bridge_winner"],
                "winner_mean_mi": candidate["evidence"]["winner_mean_mi"],
                "winner_mean_i_c": candidate["evidence"]["winner_mean_i_c"],
                "runner_up": candidate["evidence"]["runner_up"],
                "runner_up_mean_mi": candidate["evidence"]["runner_up_mean_mi"],
                "runner_up_mean_i_c": candidate["evidence"]["runner_up_mean_i_c"],
                "lr_direct_mean_mi": candidate["evidence"]["lr_direct_mean_mi"],
                "counterfeit_status": counterfeit["status"],
                "counterfeit_mean_live_I_c": counterfeit["evidence"]["mean_live_I_c"],
                "counterfeit_mean_counterfeit_I_c": counterfeit["evidence"]["mean_counterfeit_I_c"],
                "counterfeit_mean_I_c_gap": counterfeit["evidence"]["mean_I_c_gap"],
            },
        },
        "support_contract": {
            "c1_search_closed": search_validation["passed_gates"] == search_validation["total_gates"],
            "bridge_owner_alignment": search["support_chain"]["bridge_owner_alignment"],
            "carrier_handoff": handoff,
            "carrier_selection_handoff_matches_search": all(
                carrier_selection_handoff.get(key) == handoff.get(key)
                for key in (
                    "candidate",
                    "status",
                    "placement_contract",
                    "owner_dependency",
                    "forbidden_reclassification",
                    "consumer_status",
                )
            ),
            "pre_entropy_mapping": current_mapping["Xi_chiral_entangle"],
            "pre_entropy_relation": axis_internal_readout["Xi_chiral_entangle_relation"],
            "pre_entropy_placement": placement_relations["Xi_chiral_entangle"],
            "entropy_gate_name": current_bridge_gate_name(),
            "entropy_gate_status": current_bridge_gate_status(),
        },
        "non_claims": build_non_owner_reservation(),
    }

    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
