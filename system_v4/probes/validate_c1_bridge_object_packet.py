#!/usr/bin/env python3
"""
validate_c1_bridge_object_packet.py
===================================

Mechanical validator for the standalone C1 bridge-object packet.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SIM_RESULTS = ROOT / "a2_state" / "sim_results"
OUTPUT_PATH = SIM_RESULTS / "c1_bridge_object_packet_validation.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(ok: bool, name: str, detail: dict) -> dict:
    return {"name": name, "pass": bool(ok), "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    packet = load_json(SIM_RESULTS / "c1_bridge_object_packet_results.json")
    bridge_object = packet["bridge_object"]
    support = packet["support_contract"]
    non_claims = packet["non_claims"]

    gates = [
        gate(
            bridge_object["name"] == "Xi_chiral_entangle"
            and bridge_object["status"] == "admitted_bridge_object_for_downstream_readout_not_final_owner_law"
            and bridge_object["scope"] == "downstream_readout_only"
            and bridge_object["consumer_status"] == "allowed_for_entropy_readout_not_final_owner_xi"
            and bridge_object["evidence"]["bridge_winner"] == "Xi_chiral_entangle"
            and bridge_object["evidence"]["winner_mean_mi"] > 0.5
            and bridge_object["evidence"]["winner_mean_i_c"] > 0.05
            and bridge_object["evidence"]["runner_up"] == "Xi_chiral_hist_entangle"
            and bridge_object["evidence"]["runner_up_mean_i_c"] < 0.0
            and bridge_object["evidence"]["winner_mean_i_c"] > bridge_object["evidence"]["runner_up_mean_i_c"]
            and bridge_object["evidence"]["lr_direct_mean_mi"] < 1e-12,
            "C1B1_bridge_object_is_explicit_and_downstream_only",
            bridge_object,
        ),
        gate(
            bridge_object["evidence"]["counterfeit_status"] == "counterfeit_beats_mi_but_loses_signed_honesty"
            and bridge_object["evidence"]["counterfeit_mean_live_I_c"] > bridge_object["evidence"]["counterfeit_mean_counterfeit_I_c"]
            and bridge_object["evidence"]["counterfeit_mean_I_c_gap"] > 0.05,
            "C1B2_counterfeit_pressure_remains_bound_to_the_bridge_object",
            bridge_object["evidence"],
        ),
        gate(
            support["c1_search_closed"]
            and support["carrier_handoff"]["candidate"] == "Xi_chiral_entangle"
            and support["carrier_handoff"]["placement_contract"] == "downstream_axis_internal_bridge_candidate_only"
            and support["carrier_handoff"]["owner_dependency"] == "must_bind_under_xi_hist_signed_law"
            and support["carrier_handoff"]["forbidden_reclassification"] == "not_owner_derived_not_final_owner_xi"
            and support["pre_entropy_mapping"] == "axis_internal_candidate_not_final_owner_law"
            and support["pre_entropy_relation"] == "downstream_of_xi_hist_signed_law_not_alternate_owner_law"
            and support["pre_entropy_placement"] == "downstream_axis_internal_bridge_candidate_derived_from_xi_hist_signed_law"
            and support["entropy_gate_name"] == "E10_current_bridge_candidate_is_explicit_and_provisional"
            and support["entropy_gate_status"] == "admitted_executable_candidate_not_final_owner_law",
            "C1B3_bridge_object_is_bound_to_the_existing_support_contract",
            support,
        ),
        gate(
            non_claims["final_xi_owner_law"] == "open"
            and non_claims["shell_doctrine"] == "open"
            and non_claims["history_law_replacement"] == "open"
            and non_claims["entropy_family_owner_doctrine"] == "open",
            "C1B4_bridge_object_keeps_owner_doctrine_questions_open",
            non_claims,
        ),
    ]

    passed = sum(1 for item in gates if item["pass"])
    payload = {
        "name": "c1_bridge_object_packet_validation",
        "timestamp": datetime.now(UTC).isoformat(),
        "passed_gates": passed,
        "total_gates": len(gates),
        "score": passed / len(gates) if gates else 0.0,
        "gates": gates,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if args.pretty:
        print("=" * 72)
        print("C1 BRIDGE OBJECT PACKET VALIDATION")
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
