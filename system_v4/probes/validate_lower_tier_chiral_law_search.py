#!/usr/bin/env python3
"""
validate_lower_tier_chiral_law_search.py
========================================

Mechanical validator for the lower-tier chiral-law search packet.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SIM_RESULTS = ROOT / "a2_state" / "sim_results"
OUTPUT_PATH = SIM_RESULTS / "lower_tier_chiral_law_search_validation.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(ok: bool, name: str, detail: dict) -> dict:
    return {"name": name, "pass": bool(ok), "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    search = load_json(SIM_RESULTS / "lower_tier_chiral_law_search_results.json")
    candidates = search["candidate_family"]
    summary = search["summary"]
    owner_read = search["owner_read"]
    source_support = search["source_support"]

    gates = [
        gate(
            candidates["ga3_chirality_readout"]["status"] == "readout_only"
            and not candidates["ga3_chirality_readout"]["keep"]
            and candidates["symmetric_dphi_bookkeeping"]["status"] == "bookkeeping_only"
            and not candidates["symmetric_dphi_bookkeeping"]["keep"],
            "L1_fake_lower_tier_chiral_law_routes_are_killed",
            {
                "ga3_chirality_readout": candidates["ga3_chirality_readout"],
                "symmetric_dphi_bookkeeping": candidates["symmetric_dphi_bookkeeping"],
            },
        ),
        gate(
            candidates["delta_chirality_signal"]["status"] == "real_signal_not_law"
            and not candidates["delta_chirality_signal"]["keep"]
            and candidates["delta_chirality_signal"]["evidence"]["chirality_active_count"] > 0,
            "L2_delta_chirality_is_real_signal_but_not_owner_law",
            {
                "delta_chirality_signal": candidates["delta_chirality_signal"],
            },
        ),
        gate(
            candidates["chirality_separated_transport_deltas"]["status"] == "surviving_compound_candidate"
            and candidates["chirality_separated_transport_deltas"]["keep"]
            and candidates["chirality_separated_transport_deltas"]["evidence"]["nonproxy_runtime_support"] == "nonproxy_runtime_support"
            and candidates["chirality_separated_transport_deltas"]["evidence"]["transport_active_count"] == 48
            and candidates["chirality_separated_transport_deltas"]["evidence"]["lr_bloch_asymmetry_count"] == 48
            and candidates["chirality_separated_transport_deltas"]["evidence"]["live_min_direct_min_traversal"] > 0.1
            and candidates["chirality_separated_transport_deltas"]["evidence"]["live_min_sheet_split"] > 1.4,
            "L3_compound_transport_chirality_branch_survives_search",
            {
                "chirality_separated_transport_deltas": candidates["chirality_separated_transport_deltas"],
            },
        ),
        gate(
            summary["winner"] == "chirality_separated_transport_deltas"
            and summary["winner_status"] == "surviving_compound_candidate"
            and summary["fake_law_routes"] == ["ga3_chirality_readout", "symmetric_dphi_bookkeeping"]
            and summary["signal_only_routes"] == ["delta_chirality_signal"]
            and summary["single_lower_tier_chiral_law"] == "not_supported_yet"
            and owner_read["status"] == "compound_candidate_only"
            and "No single lower-tier chiral law is admitted" in owner_read["note"]
            and "G11_chiral_readout_and_symmetric_bookkeeping_are_embargoed_from_law_promotion"
            in source_support["formal_geometry_gates"]
            and "N1_no_chirality_kill_is_real_but_not_total" in source_support["no_chirality_gates"]
            and "N2_no_chirality_residual_is_explicitly_nontrivial" in source_support["no_chirality_gates"]
            and "N3_chiral_run_keeps_stronger_sheet_split_than_flattened_run" in source_support["no_chirality_gates"]
            and "W5_branch_map_keeps_flux_placement_open" in source_support["weyl_delta_gates"]
            and "W7_branch_map_preserves_skeptical_flux_read" in source_support["weyl_delta_gates"]
            and "W8_pre_axis_object_inventory_is_explicit" in source_support["weyl_delta_gates"],
            "L4_search_keeps_single_lower_tier_chiral_law_open_but_unadmitted",
            {
                "summary": summary,
                "owner_read": owner_read,
                "source_support": source_support,
            },
        ),
    ]

    passed = sum(1 for item in gates if item["pass"])
    payload = {
        "name": "lower_tier_chiral_law_search_validation",
        "timestamp": datetime.now(UTC).isoformat(),
        "passed_gates": passed,
        "total_gates": len(gates),
        "score": passed / len(gates) if gates else 0.0,
        "gates": gates,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if args.pretty:
        print("=" * 72)
        print("LOWER-TIER CHIRAL LAW SEARCH VALIDATION")
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
