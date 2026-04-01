#!/usr/bin/env python3
"""
validate_lower_tier_transport_law_search.py
===========================================

Mechanical validator for the lower-tier transport-law search packet.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SIM_RESULTS = ROOT / "a2_state" / "sim_results"
OUTPUT_PATH = SIM_RESULTS / "lower_tier_transport_law_search_validation.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(ok: bool, name: str, detail: dict) -> dict:
    return {"name": name, "pass": bool(ok), "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    search = load_json(SIM_RESULTS / "lower_tier_transport_law_search_results.json")
    candidates = search["candidate_family"]
    summary = search["summary"]

    gates = [
        gate(
            candidates["exact_loop_assigned_transport"]["status"] == "surviving_lower_tier_candidate"
            and candidates["exact_loop_assigned_transport"]["keep"]
            and candidates["exact_loop_assigned_transport"]["evidence"]["max_true_fiber_drift"] < 1e-12
            and candidates["exact_loop_assigned_transport"]["evidence"]["min_true_base_traversal"] > 0.1,
            "T1_exact_same_carrier_loop_law_survives_search",
            candidates["exact_loop_assigned_transport"],
        ),
        gate(
            candidates["generic_transport_activity"]["status"] == "too_generic_not_law"
            and not candidates["generic_transport_activity"]["keep"]
            and candidates["generic_transport_activity"]["evidence"]["transport_active_count"] > 0,
            "T2_generic_transport_activity_is_not_promoted_to_law",
            candidates["generic_transport_activity"],
        ),
        gate(
            candidates["symmetric_motion_summary"]["status"] == "fake_lower_tier_law"
            and not candidates["symmetric_motion_summary"]["keep"]
            and candidates["symmetric_motion_summary"]["evidence"]["loop_counts"]["fiber"] > 0
            and candidates["symmetric_motion_summary"]["evidence"]["loop_counts"]["base"] > 0,
            "T3_symmetric_motion_summary_is_killed_as_fake_transport_law",
            candidates["symmetric_motion_summary"],
        ),
        gate(
            candidates["downstream_cut_effect"]["status"] == "downstream_not_lower_tier"
            and not candidates["downstream_cut_effect"]["keep"]
            and summary["winner"] == "exact_loop_assigned_transport"
            and summary["single_transport_law"] == "exact_loop_assigned_transport_only",
            "T4_downstream_cut_effect_is_fenced_off_from_lower_transport_law",
            {
                "downstream_cut_effect": candidates["downstream_cut_effect"],
                "summary": summary,
            },
        ),
    ]

    passed = sum(1 for item in gates if item["pass"])
    payload = {
        "name": "lower_tier_transport_law_search_validation",
        "timestamp": datetime.now(UTC).isoformat(),
        "passed_gates": passed,
        "total_gates": len(gates),
        "score": passed / len(gates) if gates else 0.0,
        "gates": gates,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if args.pretty:
        print("=" * 72)
        print("LOWER-TIER TRANSPORT LAW SEARCH VALIDATION")
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
