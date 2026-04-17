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

from axis0_constraint_types import build_constraint_family_profile
from axis0_bridge_owner_alignment_contract import (
    axis_internal_candidate_placement,
    axis_internal_candidate_relation,
    axis_internal_candidate_status,
    bridge_owner_alignment_ok,
    current_bridge_gate_name,
    current_bridge_gate_status,
    current_bridge_object_status,
    non_owner_reservation_ok,
    signed_bridge_handoff_ok,
)

ROOT = Path(__file__).resolve().parent
SIM_RESULTS = ROOT / "a2_state" / "sim_results"
OUTPUT_PATH = SIM_RESULTS / "c1_bridge_object_packet_validation.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(ok: bool, name: str, detail: dict) -> dict:
    return {"name": name, "pass": bool(ok), "detail": detail}


def _packet_constraint_family_profile(gate_map: dict[str, dict]) -> dict[str, float]:
    observational_names = (
        "C1B1_bridge_object_is_explicit_and_downstream_only",
        "C1B4_bridge_object_keeps_owner_doctrine_questions_open",
    )
    admissible_names = (
        "C1B3_bridge_object_is_bound_to_the_existing_support_contract",
        "C1B4_bridge_object_keeps_owner_doctrine_questions_open",
    )
    stable_names = (
        "C1B1_bridge_object_is_explicit_and_downstream_only",
        "C1B2_counterfeit_pressure_remains_bound_to_the_bridge_object",
        "C1B3_bridge_object_is_bound_to_the_existing_support_contract",
    )
    entropy_names = (
        "C1B2_counterfeit_pressure_remains_bound_to_the_bridge_object",
        "C1B3_bridge_object_is_bound_to_the_existing_support_contract",
    )
    topology_names = (
        "C1B3_bridge_object_is_bound_to_the_existing_support_contract",
        "C1B4_bridge_object_keeps_owner_doctrine_questions_open",
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

    packet = load_json(SIM_RESULTS / "c1_bridge_object_packet_results.json")
    bridge_object = packet["bridge_object"]
    support = packet["support_contract"]
    non_claims = packet["non_claims"]
    bridge_alignment = support["bridge_owner_alignment"]

    gates = [
        gate(
            bridge_object["name"] == "Xi_chiral_entangle"
            and bridge_object["status"] == current_bridge_object_status()
            and bridge_object["scope"] == "downstream_readout_only"
            and bridge_object["consumer_status"] == "allowed_for_entropy_readout_not_final_owner_xi"
            and bridge_object["evidence"]["bridge_winner"] == "Xi_chiral_entangle"
            and bridge_object["evidence"]["winner_mean_mi"] > 0.5
            and bridge_object["evidence"]["winner_mean_i_c"] > 0.02
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
            bridge_owner_alignment_ok(bridge_alignment)
            and signed_bridge_handoff_ok(support["carrier_handoff"])
            and support["carrier_selection_handoff_matches_search"]
            and support["pre_entropy_mapping"] == axis_internal_candidate_status()
            and support["pre_entropy_relation"] == axis_internal_candidate_relation()
            and support["pre_entropy_placement"] == axis_internal_candidate_placement()
            and support["entropy_gate_name"] == current_bridge_gate_name()
            and support["entropy_gate_status"] == current_bridge_gate_status(),
            "C1B3_bridge_object_is_bound_to_the_existing_support_contract",
            {**support, "bridge_owner_alignment": bridge_alignment},
        ),
        gate(
            non_owner_reservation_ok(non_claims),
            "C1B4_bridge_object_keeps_owner_doctrine_questions_open",
            non_claims,
        ),
    ]

    passed = sum(1 for item in gates if item["pass"])
    gate_map = {item["name"]: item for item in gates}
    payload = {
        "name": "c1_bridge_object_packet_validation",
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
