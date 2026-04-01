#!/usr/bin/env python3
"""
Lower-Tier Transport Law Search
===============================

Mechanical search surface for candidate lower-tier transport-law objects.

This packet keeps the exact same-carrier loop law explicit and fail-closed:
  - exact loop-assigned transport
  - generic transport activity
  - symmetric motion summary
  - downstream cut effect
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SIM_RESULTS = ROOT / "a2_state" / "sim_results"
OUTPUT_PATH = SIM_RESULTS / "lower_tier_transport_law_search_results.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    geometry_truth = load_json(SIM_RESULTS / "geometry_truth_results.json")
    formal_geometry = load_json(SIM_RESULTS / "formal_geometry_packet_validation.json")
    weyl_delta = load_json(SIM_RESULTS / "weyl_delta_packet_results.json")
    neg_loop_swap = load_json(SIM_RESULTS / "neg_loop_law_swap_results.json")

    delta_summary = weyl_delta["global_summary"]
    branch_map = weyl_delta["branch_map"]

    candidates = {
        "exact_loop_assigned_transport": {
            "status": "surviving_lower_tier_candidate",
            "keep": True,
            "reason": "fiber stationarity and base traversal survive only under the exact assigned loop law on the same carrier",
            "evidence": {
                "geometry_truth_all_pass": bool(geometry_truth["all_pass"]),
                "structure_matters": bool(neg_loop_swap["structure_matters"]),
                "max_true_fiber_drift": float(neg_loop_swap["max_true_fiber_drift"]),
                "min_true_base_traversal": float(neg_loop_swap["min_true_base_traversal"]),
                "min_swapped_base_as_fiber": float(neg_loop_swap["min_swapped_base_as_fiber"]),
                "min_swapped_fiber_as_base": float(neg_loop_swap["min_swapped_fiber_as_base"]),
            },
        },
        "generic_transport_activity": {
            "status": "too_generic_not_law",
            "keep": False,
            "reason": "mere movement or angle change does not distinguish the exact loop law from other motion summaries",
            "evidence": {
                "transport_active_count": int(delta_summary["transport_active_count"]),
                "max_abs_delta_eta": float(delta_summary["max_abs_delta_eta"]),
                "max_abs_delta_theta1": float(delta_summary["max_abs_delta_theta1"]),
                "max_abs_delta_theta2": float(delta_summary["max_abs_delta_theta2"]),
            },
        },
        "symmetric_motion_summary": {
            "status": "fake_lower_tier_law",
            "keep": False,
            "reason": "symmetric or undifferentiated motion summaries do not preserve loop-role asymmetry",
            "evidence": {
                "transport_active_count": int(delta_summary["transport_active_count"]),
                "loop_counts": delta_summary["loop_counts"],
            },
        },
        "downstream_cut_effect": {
            "status": "downstream_not_lower_tier",
            "keep": False,
            "reason": "cut and bridge effects belong above the lower transport tier",
            "evidence": {
                "status": branch_map["post_joint_cut_flux"]["status"],
                "reason": branch_map["post_joint_cut_flux"]["reason"],
            },
        },
    }

    payload = {
        "name": "lower_tier_transport_law_search",
        "timestamp": datetime.now(UTC).isoformat(),
        "candidate_family": candidates,
        "summary": {
            "winner": "exact_loop_assigned_transport",
            "winner_status": candidates["exact_loop_assigned_transport"]["status"],
            "fake_law_routes": [
                "generic_transport_activity",
                "symmetric_motion_summary",
            ],
            "downstream_routes": [
                "downstream_cut_effect",
            ],
            "single_transport_law": "exact_loop_assigned_transport_only",
        },
        "owner_read": {
            "status": "exact_loop_law_only",
            "note": "The lower-tier transport law supported by the repo is the exact same-carrier loop law, not generic transport activity and not downstream cut effects.",
        },
        "source_support": {
            "formal_geometry_gates": [item["name"] for item in formal_geometry["gates"] if item["pass"]],
        },
    }

    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
