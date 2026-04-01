#!/usr/bin/env python3
"""
validate_weyl_delta_packet.py
=============================

Mechanical validator for the raw pre-Axis Weyl delta packet.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SIM_RESULTS = ROOT / "a2_state" / "sim_results"
OUTPUT_PATH = SIM_RESULTS / "weyl_delta_packet_validation.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(ok: bool, name: str, detail: dict) -> dict:
    return {"name": name, "pass": bool(ok), "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    delta = load_json(SIM_RESULTS / "weyl_delta_packet_results.json")
    neg_no_chirality = load_json(SIM_RESULTS / "neg_no_chirality_results.json")

    summary = delta["global_summary"]
    placement = delta["placement_hints"]
    flux = delta["flux_candidate_status"]
    branches = delta["branch_map"]
    inventory = delta["pre_axis_object_inventory"]
    gates = [
        gate(
            summary["rows"] == 48
            and summary["transport_active_count"] == 48
            and summary["mean_delta_rho_L_frob"] > 0.1
            and summary["mean_delta_rho_R_frob"] > 0.1
            and summary["loop_counts"].get("base", 0) > 0
            and summary["loop_counts"].get("fiber", 0) > 0,
            "W1_stagewise_raw_delta_surfaces_exist",
            {
                "rows": summary["rows"],
                "transport_active_count": summary["transport_active_count"],
                "mean_delta_rho_L_frob": summary["mean_delta_rho_L_frob"],
                "mean_delta_rho_R_frob": summary["mean_delta_rho_R_frob"],
                "loop_counts": summary["loop_counts"],
            },
        ),
        gate(
            summary["max_abs_delta_eta"] > 0.1
            and summary["max_abs_delta_theta1"] > 0.1
            and summary["max_abs_delta_theta2"] > 0.05
            and len(summary["seat_transition_counts"]) >= 4,
            "W2_transport_geometry_is_mechanically_nontrivial",
            {
                "max_abs_delta_eta": summary["max_abs_delta_eta"],
                "max_abs_delta_theta1": summary["max_abs_delta_theta1"],
                "max_abs_delta_theta2": summary["max_abs_delta_theta2"],
                "seat_transition_counts": summary["seat_transition_counts"],
            },
        ),
        gate(
            summary["chirality_active_count"] >= 24
            and summary["mean_abs_delta_chirality"] > 1e-3
            and neg_no_chirality["chirality_matters"],
            "W3_chirality_differential_is_real_pre_axis_signal",
            {
                "chirality_active_count": summary["chirality_active_count"],
                "mean_abs_delta_chirality": summary["mean_abs_delta_chirality"],
                "neg_no_chirality_chirality_matters": neg_no_chirality["chirality_matters"],
                "d_chiral": neg_no_chirality["d_chiral"],
                "d_flat": neg_no_chirality["d_flat"],
            },
        ),
        gate(
            summary["lr_state_asymmetry_count"] >= 24
            and summary["lr_bloch_asymmetry_count"] >= 24
            and summary["max_abs_compat_dphi_gap"] < 1e-12
            and flux["entropic_left_right_flux"] == "blocked_by_symmetric_compat_shim",
            "W4_raw_lr_deltas_are_not_reducible_to_symmetric_dphi_shim",
            {
                "lr_state_asymmetry_count": summary["lr_state_asymmetry_count"],
                "lr_bloch_asymmetry_count": summary["lr_bloch_asymmetry_count"],
                "max_abs_compat_dphi_gap": summary["max_abs_compat_dphi_gap"],
                "entropic_left_right_flux": flux["entropic_left_right_flux"],
            },
        ),
        gate(
            placement["geometric_transport_delta"] == "pre-axis"
            and placement["chirality_differential_delta"] == "pre-axis"
            and placement["bloch_differential_delta"] == "pre-axis"
            and placement["entropic_left_right_flux"] == "unresolved_not_owner_worthy_yet"
            and placement["post_joint_cut_flux"] == "axis_internal_or_cross_axis",
            "W5_branch_map_keeps_flux_placement_open",
            {
                "placement_hints": placement,
            },
        ),
        gate(
            flux["geometric_transport_flux"] == "candidate_ready"
            and flux["bloch_current_flux"] == "candidate_ready"
            and flux["chirality_differential_flux"] == "candidate_ready"
            and flux["entropic_left_right_flux"] == "blocked_by_symmetric_compat_shim"
            and flux["post_joint_cut_flux"] == "downstream_existing_branch",
            "W6_flux_family_is_explicit_without_canonizing_flux",
            {
                "flux_candidate_status": flux,
            },
        ),
        gate(
            branches["single_weyl_flux_object"]["status"] == "not_supported_yet"
            and branches["chirality_separated_transport_deltas"]["status"] == "surviving_pre_axis_candidate"
            and branches["compound_owner_phrase_candidate"]["status"] == "survives_better_than_single_flux",
            "W7_branch_map_preserves_skeptical_flux_read",
            {
                "single_weyl_flux_object": branches["single_weyl_flux_object"],
                "chirality_separated_transport_deltas": branches["chirality_separated_transport_deltas"],
                "compound_owner_phrase_candidate": branches["compound_owner_phrase_candidate"],
            },
        ),
        gate(
            inventory["hopf_carrier_point"]["status"] == "live_pre_axis_geometry"
            and inventory["nested_torus_seat"]["status"] == "live_pre_axis_geometry"
            and inventory["weyl_sheet_pair"]["status"] == "live_pre_axis_refinement"
            and inventory["loop_sensitive_transport_surface"]["status"] == "live_pre_axis_candidate"
            and inventory["chirality_differential_surface"]["status"] == "live_pre_axis_candidate"
            and inventory["bloch_differential_surface"]["status"] == "live_pre_axis_candidate"
            and inventory["raw_delta_packet"]["status"] == "diagnostic_surface_not_final_owner_law"
            and inventory["bridge_ready_cut_object"]["status"] == "downstream_not_pre_axis",
            "W8_pre_axis_object_inventory_is_explicit",
            {
                "pre_axis_object_inventory": inventory,
            },
        ),
    ]

    passed = sum(1 for item in gates if item["pass"])
    payload = {
        "name": "weyl_delta_packet_validation",
        "timestamp": datetime.now(UTC).isoformat(),
        "passed_gates": passed,
        "total_gates": len(gates),
        "score": passed / len(gates) if gates else 0.0,
        "gates": gates,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if args.pretty:
        print("=" * 72)
        print("WEYL DELTA PACKET VALIDATION")
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
