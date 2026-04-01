#!/usr/bin/env python3
"""
validate_attractor_basin_boundary_search.py
===========================================

Mechanical validator for the narrow attractor-basin search surface.

This is intentionally not a packet-level admission. It only captures the
cleanest basin subclaim currently supported by the existing probe:
Ti failure sits behind a low-lr_asym boundary, while live trajectory states
stay well above that boundary.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SIM_RESULTS = ROOT / "a2_state" / "sim_results"
OUTPUT_PATH = SIM_RESULTS / "attractor_basin_boundary_search_validation.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(ok: bool, name: str, detail: dict) -> dict:
    return {"name": name, "pass": bool(ok), "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    basin = load_json(SIM_RESULTS / "axis0_attractor_basin_boundary_results.json")

    q1 = basin["q1_trajectory_lr_asym"]
    q3 = basin["q3_ti_boundary"]

    threshold = q3["best_lr_asym_before_threshold"]
    trajectory_floor = min(cfg["lr_asym_min"] for cfg in q1["configs"])
    trajectory_margin = trajectory_floor - threshold

    gates = [
        gate(
            q3["n_failures"] > 0
            and q3["n_successes"] > 0
            and threshold == 0.05
            and q3["threshold_accuracy"] > 0.9,
            "AB1_ti_failure_boundary_is_mechanical",
            {
                "n_failures": q3["n_failures"],
                "n_successes": q3["n_successes"],
                "best_lr_asym_before_threshold": threshold,
                "threshold_accuracy": q3["threshold_accuracy"],
            },
        ),
        gate(
            trajectory_floor > threshold + 0.5
            and trajectory_margin > 0.5,
            "AB2_live_trajectory_stays_far_above_ti_failure_boundary",
            {
                "trajectory_lr_asym_floor": trajectory_floor,
                "ti_failure_threshold": threshold,
                "trajectory_margin": trajectory_margin,
            },
        ),
        gate(
            q3["failure_asym_before_mean"] < q3["success_asym_before_mean"]
            and q3["failure_z_diff_mean"] < q3["success_z_diff_mean"],
            "AB3_ti_failure_population_is_separable_from_success_population",
            {
                "failure_asym_before_mean": q3["failure_asym_before_mean"],
                "success_asym_before_mean": q3["success_asym_before_mean"],
                "failure_z_diff_mean": q3["failure_z_diff_mean"],
                "success_z_diff_mean": q3["success_z_diff_mean"],
            },
        ),
    ]

    passed = sum(1 for item in gates if item["pass"])
    payload = {
        "name": "attractor_basin_boundary_search_validation",
        "timestamp": datetime.now(UTC).isoformat(),
        "passed_gates": passed,
        "total_gates": len(gates),
        "score": passed / len(gates) if gates else 0.0,
        "status": "search_surface_only_not_packet_admission",
        "gates": gates,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if args.pretty:
        print("=" * 72)
        print("ATTRACTOR BASIN BOUNDARY SEARCH VALIDATION")
        print("=" * 72)
        for item in gates:
            print(f"{'PASS' if item['pass'] else 'FAIL'}  {item['name']}")
        print()
        print(f"passed_gates: {passed}/{len(gates)}")
        print(f"score: {payload['score']:.6f}")
        print(f"validation_results: {OUTPUT_PATH}")

    return 0 if passed == len(gates) else 1


if __name__ == "__main__":
    raise SystemExit(main())
