#!/usr/bin/env python3
"""
validate_axis0_attractor_basin_boundary_search.py
=================================================

Mechanical validator for the bounded attractor-basin boundary search.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SIM_RESULTS = ROOT / "a2_state" / "sim_results"
OUTPUT_PATH = SIM_RESULTS / "axis0_attractor_basin_boundary_search_validation.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(ok: bool, name: str, detail: dict) -> dict:
    return {"name": name, "pass": bool(ok), "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    search = load_json(SIM_RESULTS / "axis0_attractor_basin_boundary_results.json")
    q1_configs = search["q1_trajectory_lr_asym"]["configs"]
    q3 = search["q3_ti_boundary"]

    threshold = q3["best_lr_asym_before_threshold"]
    q1_min_floor = min(config["lr_asym_min"] for config in q1_configs)
    q1_mean_floor = min(config["lr_asym_mean"] for config in q1_configs)
    q1_peak = max(config["lr_asym_max"] for config in q1_configs)

    gates = [
        gate(
            len(q1_configs) >= 8
            and all(not config["constant_at_1"] for config in q1_configs)
            and q1_mean_floor > 0.88
            and q1_peak > 0.99,
            "AB1_trajectory_lr_asym_surface_is_explicit_and_nontrivial",
            {
                "config_count": len(q1_configs),
                "all_nonconstant": all(not config["constant_at_1"] for config in q1_configs),
                "q1_mean_floor": q1_mean_floor,
                "q1_peak": q1_peak,
            },
        ),
        gate(
            threshold == 0.05
            and q3["threshold_accuracy"] > 0.93
            and q3["n_successes"] > q3["n_failures"]
            and q3["failure_asym_before_mean"] < q3["success_asym_before_mean"],
            "AB2_ti_failure_boundary_is_explicit_and_predictive",
            {
                "threshold": threshold,
                "threshold_accuracy": q3["threshold_accuracy"],
                "n_successes": q3["n_successes"],
                "n_failures": q3["n_failures"],
                "failure_asym_before_mean": q3["failure_asym_before_mean"],
                "success_asym_before_mean": q3["success_asym_before_mean"],
            },
        ),
        gate(
            q1_min_floor > threshold + 0.25
            and q1_mean_floor > q3["success_asym_before_mean"],
            "AB3_observed_trajectory_stays_clear_of_the_ti_failure_regime",
            {
                "q1_min_floor": q1_min_floor,
                "q1_mean_floor": q1_mean_floor,
                "threshold": threshold,
                "success_asym_before_mean": q3["success_asym_before_mean"],
            },
        ),
    ]

    passed = sum(1 for item in gates if item["pass"])
    payload = {
        "name": "axis0_attractor_basin_boundary_search_validation",
        "timestamp": datetime.now(UTC).isoformat(),
        "passed_gates": passed,
        "total_gates": len(gates),
        "score": passed / len(gates) if gates else 0.0,
        "gates": gates,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if args.pretty:
        print("=" * 72)
        print("AXIS0 ATTRACTOR BASIN BOUNDARY SEARCH VALIDATION")
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
