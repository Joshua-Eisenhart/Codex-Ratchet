#!/usr/bin/env python3
"""
validate_c1_signed_bridge_candidate_search.py
=============================================

Mechanical validator for the standalone C1 signed bridge candidate search.
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
    non_owner_reservation_ok,
    owner_read_ok,
)

ROOT = Path(__file__).resolve().parent
SIM_RESULTS = ROOT / "a2_state" / "sim_results"
OUTPUT_PATH = SIM_RESULTS / "c1_signed_bridge_candidate_search_validation.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(ok: bool, name: str, detail: dict) -> dict:
    return {"name": name, "pass": bool(ok), "detail": detail}


def _packet_constraint_family_profile(gate_map: dict[str, dict]) -> dict[str, float]:
    observational_names = (
        "C1S1_current_signed_bridge_candidate_is_explicit",
        "C1S4_candidate_stays_provisional_and_does_not_overpromote",
    )
    admissible_names = (
        "C1S3_support_chain_is_closed_before_candidate_packaging",
        "C1S4_candidate_stays_provisional_and_does_not_overpromote",
    )
    stable_names = (
        "C1S1_current_signed_bridge_candidate_is_explicit",
        "C1S2_counterfeit_pressure_keeps_signed_honesty_load_bearing",
        "C1S3_support_chain_is_closed_before_candidate_packaging",
    )
    entropy_names = (
        "C1S2_counterfeit_pressure_keeps_signed_honesty_load_bearing",
        "C1S3_support_chain_is_closed_before_candidate_packaging",
    )
    topology_names = (
        "C1S3_support_chain_is_closed_before_candidate_packaging",
        "C1S4_candidate_stays_provisional_and_does_not_overpromote",
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

    search = load_json(SIM_RESULTS / "c1_signed_bridge_candidate_search_results.json")
    candidate = search["candidate_object"]
    counterfeit = search["negative_family"]["history_mispair_counterfeit"]
    support = search["support_chain"]
    unresolved = search["unresolved"]
    bridge_alignment = support["bridge_owner_alignment"]

    gates = [
        gate(
            candidate["status"] == "provisional_signed_bridge_candidate"
            and candidate["keep"]
            and candidate["evidence"]["bridge_winner"] == "Xi_chiral_entangle"
            and candidate["evidence"]["winner_mean_mi"] > 0.5
            and candidate["evidence"]["winner_mean_i_c"] > 0.02
            and candidate["evidence"]["runner_up"] == "Xi_chiral_hist_entangle"
            and candidate["evidence"]["runner_up_mean_i_c"] < 0.0
            and candidate["evidence"]["winner_mean_i_c"] > candidate["evidence"]["runner_up_mean_i_c"]
            and candidate["evidence"]["lr_direct_mean_mi"] < 1e-12,
            "C1S1_current_signed_bridge_candidate_is_explicit",
            candidate,
        ),
        gate(
            counterfeit["status"] == "counterfeit_beats_mi_but_loses_signed_honesty"
            and counterfeit["keep"]
            and counterfeit["evidence"]["mean_counterfeit_I_AB"] > 0.9 * counterfeit["evidence"]["mean_live_I_AB"]
            and counterfeit["evidence"]["mean_live_I_c"] > counterfeit["evidence"]["mean_counterfeit_I_c"]
            and counterfeit["evidence"]["mean_I_c_gap"] > 0.05,
            "C1S2_counterfeit_pressure_keeps_signed_honesty_load_bearing",
            counterfeit,
        ),
        gate(
            bridge_owner_alignment_ok(bridge_alignment)
            and
            support["matched_marginal_closed"]
            and support["matched_marginal_contract_scope"] == "xi_downstream_handoff_and_honesty_layer"
            and "M8_matched_marginal_layer_preserves_xi_downstream_handoff_contract"
            in support["matched_marginal_required_gates"]
            and "M9_matched_marginal_stays_subordinate_to_xi_downstream_mapping"
            in support["matched_marginal_required_gates"]
            and all(support["matched_marginal_required_passes"].values())
            and support["matched_marginal_required_passes"][
                "M8_matched_marginal_layer_preserves_xi_downstream_handoff_contract"
            ]
            and support["matched_marginal_required_passes"][
                "M9_matched_marginal_stays_subordinate_to_xi_downstream_mapping"
            ]
            and support["pre_entropy_mapping"] == axis_internal_candidate_status()
            and support["pre_entropy_relation"] == axis_internal_candidate_relation()
            and support["pre_entropy_placement"] == axis_internal_candidate_placement()
            and support["entropy_readout_current_bridge_gate"] == current_bridge_gate_name(),
            "C1S3_support_chain_is_closed_before_candidate_packaging",
            {**support, "bridge_owner_alignment": bridge_alignment},
        ),
        gate(
            non_owner_reservation_ok(unresolved)
            and owner_read_ok(search["owner_read"]),
            "C1S4_candidate_stays_provisional_and_does_not_overpromote",
            {
                "unresolved": unresolved,
                "owner_read": search["owner_read"],
            },
        ),
    ]

    passed = sum(1 for item in gates if item["pass"])
    gate_map = {item["name"]: item for item in gates}
    payload = {
        "name": "c1_signed_bridge_candidate_search_validation",
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
        print("C1 SIGNED BRIDGE CANDIDATE SEARCH VALIDATION")
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
