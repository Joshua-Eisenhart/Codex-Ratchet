#!/usr/bin/env python3
"""
Lower-Tier Chiral Law Search
============================

Mechanical search surface for candidate lower-tier chiral-law objects.

This packet does not promote a law. It compares the live candidates already
present in the repo and keeps the fake routes explicit:
  - GA3 chirality readout
  - symmetric dphi bookkeeping
  - raw delta-chirality signal
  - chirality-separated loop-sensitive transport deltas
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
classification = "classical_baseline"  # auto-backfill


ROOT = Path(__file__).resolve().parent
SIM_RESULTS = ROOT / "a2_state" / "sim_results"
OUTPUT_PATH = SIM_RESULTS / "lower_tier_chiral_law_search_results.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    formal_geometry = load_json(SIM_RESULTS / "formal_geometry_packet_validation.json")
    no_chirality_search = load_json(SIM_RESULTS / "no_chirality_search_validation.json")
    weyl_delta = load_json(SIM_RESULTS / "weyl_delta_packet_results.json")
    weyl_delta_validation = load_json(SIM_RESULTS / "weyl_delta_packet_validation.json")
    chirality = load_json(SIM_RESULTS / "L4_engine_chirality_results.json")
    neg_no_chirality = load_json(SIM_RESULTS / "neg_no_chirality_results.json")
    joint_ablation = load_json(SIM_RESULTS / "neg_transport_delta_joint_ablation_results.json")

    formal_embargo = formal_geometry["chiral_law_embargo"]
    delta_summary = weyl_delta["global_summary"]
    branch_map = weyl_delta["branch_map"]
    chirality_results = chirality["results"]
    joint_summary = joint_ablation["summary"]

    candidates = {
        "ga3_chirality_readout": {
            "status": "readout_only",
            "keep": False,
            "reason": formal_embargo["ga3_chirality"]["reason"],
            "evidence": {
                "avg_left_sheet_distance": float(chirality_results["avg_left_sheet_distance"]),
                "avg_right_sheet_distance": float(chirality_results["avg_right_sheet_distance"]),
            },
        },
        "symmetric_dphi_bookkeeping": {
            "status": "bookkeeping_only",
            "keep": False,
            "reason": formal_embargo["symmetric_dphi_bookkeeping"]["reason"],
            "evidence": {
                "max_abs_compat_dphi_gap": float(delta_summary["max_abs_compat_dphi_gap"]),
                "type1_total_dphi_L": float(chirality_results["type1_total_dphi_L"]),
                "type1_total_dphi_R": float(chirality_results["type1_total_dphi_R"]),
                "type2_total_dphi_L": float(chirality_results["type2_total_dphi_L"]),
                "type2_total_dphi_R": float(chirality_results["type2_total_dphi_R"]),
            },
        },
        "delta_chirality_signal": {
            "status": "real_signal_not_law",
            "keep": False,
            "reason": "delta trace_distance(rho_L, rho_R) is mechanically active but does not yet survive as a separate lower-tier owner law",
            "evidence": {
                "chirality_active_count": int(delta_summary["chirality_active_count"]),
                "mean_abs_delta_chirality": float(delta_summary["mean_abs_delta_chirality"]),
                "chirality_retention_ratio": float(neg_no_chirality["d_flat"] / neg_no_chirality["d_chiral"]),
            },
        },
        "chirality_separated_transport_deltas": {
            "status": "surviving_compound_candidate",
            "keep": True,
            "reason": branch_map["chirality_separated_transport_deltas"]["reason"],
            "evidence": {
                "transport_active_count": int(delta_summary["transport_active_count"]),
                "lr_bloch_asymmetry_count": int(delta_summary["lr_bloch_asymmetry_count"]),
                "nonproxy_runtime_support": joint_ablation["owner_read"]["status"],
                "live_min_direct_min_traversal": float(joint_summary["live_min_direct_min_traversal"]),
                "live_min_sheet_split": float(joint_summary["live_min_sheet_split"]),
            },
        },
    }

    payload = {
        "name": "lower_tier_chiral_law_search",
        "timestamp": datetime.now(UTC).isoformat(),
        "candidate_family": candidates,
        "summary": {
            "winner": "chirality_separated_transport_deltas",
            "winner_status": candidates["chirality_separated_transport_deltas"]["status"],
            "fake_law_routes": [
                "ga3_chirality_readout",
                "symmetric_dphi_bookkeeping",
            ],
            "signal_only_routes": [
                "delta_chirality_signal",
            ],
            "single_lower_tier_chiral_law": "not_supported_yet",
        },
        "owner_read": {
            "status": "compound_candidate_only",
            "note": "No single lower-tier chiral law is admitted; the best surviving branch remains the compound transport/chirality candidate.",
        },
        "source_support": {
            "formal_geometry_gates": [item["name"] for item in formal_geometry["gates"] if item["pass"]],
            "no_chirality_gates": [item["name"] for item in no_chirality_search["gates"] if item["pass"]],
            "weyl_delta_gates": [item["name"] for item in weyl_delta_validation["gates"] if item["pass"]],
        },
    }

    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
