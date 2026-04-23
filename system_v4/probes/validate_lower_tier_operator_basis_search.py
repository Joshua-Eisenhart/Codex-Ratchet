#!/usr/bin/env python3
"""
validate_lower_tier_operator_basis_search.py
============================================

Mechanical validator for the lower-tier operator/basis search packet.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SIM_RESULTS = ROOT / "a2_state" / "sim_results"
OUTPUT_PATH = SIM_RESULTS / "lower_tier_operator_basis_search_validation.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(ok: bool, name: str, detail: dict) -> dict:
    return {"name": name, "pass": bool(ok), "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    search = load_json(SIM_RESULTS / "lower_tier_operator_basis_search_results.json")
    summary = search["summary"]
    candidates = search["candidate_family"]

    gates = [
        gate(
            search["B3.1_basis_remap_search"] == "PASS (Killed)"
            and summary["remap_kills"] > 0
            and candidates["noncommuting_basis_split"]["status"] == "surviving_lower_tier_candidate"
            and candidates["noncommuting_basis_split"]["keep"],
            "O1_fixed_carrier_basis_remap_shows_load_bearing_sensitivity",
            candidates["noncommuting_basis_split"],
        ),
        gate(
            search["B3.2_coordinate_change_control"] == "PASS (Invariant)"
            and summary["coord_invariant_count"] == summary["total_stages"]
            and candidates["global_coordinate_choice"]["status"] == "representation_only"
            and not candidates["global_coordinate_choice"]["keep"],
            "O2_global_coordinate_change_is_not_mistaken_for_substrate_failure",
            candidates["global_coordinate_choice"],
        ),
        gate(
            search["B3.3_noncommutation_ablation"] == "PASS (Killed)"
            and summary["ablation_kills"] > 0
            and candidates["noncommuting_basis_split"]["evidence"]["ablation_kills"] > 0,
            "O3_commuting_collapse_degrades_the_local_operator_response",
            candidates["noncommuting_basis_split"],
        ),
        gate(
            search["B3.4_representation_demotion"] == "LOCAL_UNITARY_PAIR_NOT_PROVEN_LOAD_BEARING_IN_LOCAL_TEST"
            and candidates["local_unitary_pair_Fe_Fi"]["status"] == "not_proven_load_bearing_in_local_test"
            and not candidates["local_unitary_pair_Fe_Fi"]["keep"]
            and search["owner_read"]["status"] == "lower_tier_noncommuting_basis_split_survives_local_search",
            "O4_local_unitary_pair_is_not_demoted_by_this_narrow_local_test",
            {
                "local_unitary_pair_Fe_Fi": candidates["local_unitary_pair_Fe_Fi"],
                "owner_read": search["owner_read"],
            },
        ),
    ]

    passed = sum(1 for item in gates if item["pass"])
    payload = {
        "name": "lower_tier_operator_basis_search_validation",
        "timestamp": datetime.now(UTC).isoformat(),
        "passed_gates": passed,
        "total_gates": len(gates),
        "score": passed / len(gates) if gates else 0.0,
        "gates": gates,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if args.pretty:
        print("=" * 72)
        print("LOWER-TIER OPERATOR BASIS SEARCH VALIDATION")
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
