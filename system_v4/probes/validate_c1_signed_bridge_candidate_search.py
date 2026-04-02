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


ROOT = Path(__file__).resolve().parent
SIM_RESULTS = ROOT / "a2_state" / "sim_results"
OUTPUT_PATH = SIM_RESULTS / "c1_signed_bridge_candidate_search_validation.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(ok: bool, name: str, detail: dict) -> dict:
    return {"name": name, "pass": bool(ok), "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    search = load_json(SIM_RESULTS / "c1_signed_bridge_candidate_search_results.json")
    candidate = search["candidate_object"]
    counterfeit = search["negative_family"]["history_mispair_counterfeit"]
    support = search["support_chain"]
    unresolved = search["unresolved"]

    gates = [
        gate(
            candidate["status"] == "provisional_signed_bridge_candidate"
            and candidate["keep"]
            and candidate["evidence"]["bridge_winner"] == "Xi_chiral_entangle"
            and candidate["evidence"]["winner_mean_mi"] > 0.5
            and candidate["evidence"]["winner_mean_i_c"] > 0.05
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
            and counterfeit["evidence"]["mean_counterfeit_I_AB"] > counterfeit["evidence"]["mean_live_I_AB"]
            and counterfeit["evidence"]["mean_live_I_c"] > counterfeit["evidence"]["mean_counterfeit_I_c"]
            and counterfeit["evidence"]["mean_I_c_gap"] > 0.05,
            "C1S2_counterfeit_pressure_keeps_signed_honesty_load_bearing",
            counterfeit,
        ),
        gate(
            support["matched_marginal_closed"]
            and support["pre_entropy_mapping"] == "axis_internal_candidate_not_final_owner_law"
            and support["pre_entropy_relation"] == "downstream_of_xi_hist_signed_law_not_alternate_owner_law"
            and support["pre_entropy_placement"] == "downstream_axis_internal_bridge_candidate_derived_from_xi_hist_signed_law"
            and support["entropy_readout_current_bridge_gate"] == "E10_current_bridge_candidate_is_explicit_and_provisional",
            "C1S3_support_chain_is_closed_before_candidate_packaging",
            support,
        ),
        gate(
            unresolved["status"] == "explicit_non_owner_reservation"
            and unresolved["final_xi_owner_law"] == "reserved_for_future_owner_doctrine_not_claimed_by_c1"
            and unresolved["shell_doctrine"] == "reserved_for_future_shell_doctrine_not_claimed_by_c1"
            and unresolved["history_law_replacement"] == "reserved_for_future_history_law_replacement_not_claimed_by_c1"
            and unresolved["entropy_family_owner_doctrine"] == "reserved_for_future_entropy_owner_doctrine_not_claimed_by_c1"
            and unresolved["owner_dependency"] == "must_bind_under_xi_hist_signed_law"
            and unresolved["consumer_scope"] == "downstream_readout_only"
            and search["owner_read"]["status"] == "admitted_executable_candidate_not_final_owner_law",
            "C1S4_candidate_stays_provisional_and_does_not_overpromote",
            {
                "unresolved": unresolved,
                "owner_read": search["owner_read"],
            },
        ),
    ]

    passed = sum(1 for item in gates if item["pass"])
    payload = {
        "name": "c1_signed_bridge_candidate_search_validation",
        "timestamp": datetime.now(UTC).isoformat(),
        "passed_gates": passed,
        "total_gates": len(gates),
        "score": passed / len(gates) if gates else 0.0,
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
