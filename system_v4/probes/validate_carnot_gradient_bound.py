#!/usr/bin/env python3
"""
validate_carnot_gradient_bound.py
=================================

Mechanical validator for the exploratory Carnot-style runtime probe.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROBE_RESULTS = ROOT.parent / "a2_state" / "sim_results"
OUTPUT_PATH = ROOT / "a2_state" / "sim_results" / "carnot_gradient_bound_validation.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(ok: bool, name: str, detail: dict) -> dict:
    return {"name": name, "pass": bool(ok), "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    probe = load_json(PROBE_RESULTS / "carnot_gradient_bound.json")
    summary = probe["summary"]
    points = probe["operating_points"]

    by_torus: dict[str, list[dict]] = defaultdict(list)
    by_engine: dict[int, list[dict]] = defaultdict(list)
    for point in points:
        by_torus[point["torus_name"]].append(point)
        by_engine[point["engine_type"]].append(point)

    mean_work_by_torus = {
        torus: sum(point["total_work"] for point in rows) / len(rows)
        for torus, rows in by_torus.items()
    }
    mean_eta_delta_by_torus = {
        torus: sum(point["eta_delta"] for point in rows) / len(rows)
        for torus, rows in by_torus.items()
    }
    mean_ga5_delta_by_engine = {
        engine: sum(point["GA5_after"] - point["GA5_before"] for point in rows) / len(rows)
        for engine, rows in by_engine.items()
    }

    gates = [
        gate(
            len(points) == 54
            and set(by_torus) == {"inner", "clifford", "outer"}
            and set(by_engine) == {1, 2},
            "CB1_carnot_probe_surface_is_complete_and_structured",
            {
                "n_points": len(points),
                "torus_names": sorted(by_torus),
                "engine_types": sorted(by_engine),
            },
        ),
        gate(
            abs(summary["r_ga0_work"]) < 0.05
            and summary["r_curve_work"] < -0.9
            and summary["efficiency_mean"] > 10.0
            and summary["efficiency_cv"] > 0.9,
            "CB2_work_tracks_curvature_much_more_than_ga0_and_has_no_stable_carnot_bound",
            {
                "r_ga0_work": summary["r_ga0_work"],
                "r_curve_work": summary["r_curve_work"],
                "efficiency_mean": summary["efficiency_mean"],
                "efficiency_cv": summary["efficiency_cv"],
            },
        ),
        gate(
            mean_work_by_torus["inner"] > mean_work_by_torus["clifford"]
            and mean_work_by_torus["outer"] > mean_work_by_torus["clifford"]
            and mean_eta_delta_by_torus["clifford"] < 1e-12
            and mean_eta_delta_by_torus["inner"] > 0.15
            and mean_eta_delta_by_torus["outer"] > 0.15
            and summary["r_ax0_ax5"] < -0.4
            and mean_ga5_delta_by_engine[1] < 0.0
            and mean_ga5_delta_by_engine[2] < 0.0,
            "CB3_inner_outer_runtime_work_beats_clifford_while_ax0_ax5_stay_coupled",
            {
                "mean_work_by_torus": mean_work_by_torus,
                "mean_eta_delta_by_torus": mean_eta_delta_by_torus,
                "r_ax0_ax5": summary["r_ax0_ax5"],
                "mean_ga5_delta_by_engine": mean_ga5_delta_by_engine,
            },
        ),
    ]

    passed = sum(1 for item in gates if item["pass"])
    payload = {
        "name": "carnot_gradient_bound_validation",
        "timestamp": datetime.now(UTC).isoformat(),
        "passed_gates": passed,
        "total_gates": len(gates),
        "score": passed / len(gates) if gates else 0.0,
        "gates": gates,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    if args.pretty:
        print("=" * 72)
        print("CARNOT GRADIENT BOUND VALIDATION")
        print("=" * 72)
        for item in gates:
            status = "PASS" if item["pass"] else "FAIL"
            print(f"{status:<5} {item['name']}")
        print()
        print(f"passed_gates: {passed}/{len(gates)}")
        print(f"score: {payload['score']:.6f}")
        print(f"validation_results: {OUTPUT_PATH}")
    else:
        print(json.dumps(payload, indent=2))

    return 0 if passed == len(gates) else 1


if __name__ == "__main__":
    raise SystemExit(main())
