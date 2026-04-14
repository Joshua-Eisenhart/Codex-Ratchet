#!/usr/bin/env python3
"""
Mass inside-geometry sweep for the live engine.

This stays in the runtime-native microstep space:
- eta/theta/phase movement
- transport activation
- q-level displacement
- branch separation / negentropy deltas

It does not attempt a structural hexagram decode.
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from datetime import UTC, datetime

import numpy as np
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sim_engine_inside_trace import trace_one_cycle  # noqa: E402


def _mean(xs):
    if not xs:
        return 0.0
    return float(sum(xs) / len(xs))


def _norm_delta(a, b):
    va = np.asarray(a, dtype=float)
    vb = np.asarray(b, dtype=float)
    return float(np.linalg.norm(vb - va))


def main():
    seeds = list(range(24))
    programs = ["default", "inner_outer_wave"]
    engine_types = [1, 2]

    grouped = defaultdict(list)
    terrain_grouped = defaultdict(list)
    operator_grouped = defaultdict(list)

    for seed in seeds:
        for engine_type in engine_types:
            for program in programs:
                trace = trace_one_cycle(engine_type=engine_type, seed=seed, program=program)
                for step in trace["microsteps"]:
                    dtrace = (
                        step["pair_after"]["trace_distance_LR"]
                        - step["pair_before"]["trace_distance_LR"]
                    )
                    dneg = (
                        step["pair_after"]["avg_negentropy"]
                        - step["pair_before"]["avg_negentropy"]
                    )
                    dchi = (
                        (step["left_after"]["pop_gap"] - step["right_after"]["pop_gap"])
                        - (step["left_before"]["pop_gap"] - step["right_before"]["pop_gap"])
                    )
                    record = {
                        "abs_deta": abs(step["deta"]),
                        "abs_dtheta1": abs(step["dtheta1"]),
                        "abs_dtheta2": abs(step["dtheta2"]),
                        "abs_dphase": abs(step["dphase"]),
                        "axis0_blend": step["axis0_blend"],
                        "axis0_injection_norm": step["axis0_injection_norm"],
                        "axis0_effective_gain": step["axis0_effective_gain"],
                        "transport_alpha": step["transport_alpha"],
                        "transport_triggered": 1.0 if step["transport_triggered"] else 0.0,
                        "q_transport_move": _norm_delta(step["q_before"], step["q_after_transport"]),
                        "q_total_move": _norm_delta(step["q_before"], step["q_after"]),
                        "dtrace": dtrace,
                        "abs_dtrace": abs(dtrace),
                        "dneg": dneg,
                        "abs_dneg": abs(dneg),
                        "dchi": dchi,
                        "abs_dchi": abs(dchi),
                        "strength": step["strength"],
                        "ga0_delta": step["ga0_after"] - step["ga0_before"],
                        "ga0_after": step["ga0_after"],
                    }
                    grouped[(program, engine_type)].append(record)
                    terrain_grouped[(program, engine_type, step["terrain"])].append(record)
                    operator_grouped[(program, engine_type, step["operator"])].append(record)

    def summarize(bucket):
        keys = [
            "abs_deta",
            "abs_dtheta1",
            "abs_dtheta2",
            "abs_dphase",
            "axis0_blend",
            "axis0_injection_norm",
            "axis0_effective_gain",
            "transport_alpha",
            "transport_triggered",
            "q_transport_move",
            "q_total_move",
            "dtrace",
            "abs_dtrace",
            "dneg",
            "abs_dneg",
            "dchi",
            "abs_dchi",
            "strength",
            "ga0_delta",
            "ga0_after",
        ]
        return {k: _mean([r[k] for r in bucket]) for k in keys}

    overall = []
    terrain_summary = []
    operator_summary = []

    for key, bucket in sorted(grouped.items()):
        program, engine_type = key
        row = {"program": program, "engine_type": engine_type, "count": len(bucket)}
        row.update(summarize(bucket))
        overall.append(row)

    for key, bucket in sorted(terrain_grouped.items()):
        program, engine_type, terrain = key
        row = {
            "program": program,
            "engine_type": engine_type,
            "terrain": terrain,
            "count": len(bucket),
        }
        row.update(summarize(bucket))
        terrain_summary.append(row)

    for key, bucket in sorted(operator_grouped.items()):
        program, engine_type, operator = key
        row = {
            "program": program,
            "engine_type": engine_type,
            "operator": operator,
            "count": len(bucket),
        }
        row.update(summarize(bucket))
        operator_summary.append(row)

    def top(rows, field, n=8):
        return sorted(rows, key=lambda r: abs(r[field]), reverse=True)[:n]

    out = {
        "schema": "SIM_EVIDENCE_v1",
        "file": os.path.basename(__file__),
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "seeds": seeds,
        "programs": programs,
        "engine_types": engine_types,
        "overall": overall,
        "terrain_summary": terrain_summary,
        "operator_summary": operator_summary,
        "tops": {
            "terrain_by_abs_dphase": top(terrain_summary, "abs_dphase"),
            "terrain_by_transport_alpha": top(terrain_summary, "transport_alpha"),
            "terrain_by_abs_dtrace": top(terrain_summary, "abs_dtrace"),
            "operator_by_abs_dphase": top(operator_summary, "abs_dphase"),
            "operator_by_transport_alpha": top(operator_summary, "transport_alpha"),
            "operator_by_abs_dtrace": top(operator_summary, "abs_dtrace"),
        },
    }

    out_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "a2_state",
        "sim_results",
        "engine_inside_mass_sweep.json",
    )
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print("=" * 72)
    print("ENGINE INSIDE MASS SWEEP")
    print("=" * 72)
    for row in overall:
        print(
            f"type {row['engine_type']} [{row['program']}]: "
            f"transport={row['transport_alpha']:.4f}, "
            f"|dphase|={row['abs_dphase']:.4f}, "
            f"|dtrace|={row['abs_dtrace']:.4f}, "
            f"|dchi|={row['abs_dchi']:.4f}, "
            f"ga0_delta={row['ga0_delta']:.4f}"
        )
    print(f"\nResults written to {out_file}")


if __name__ == "__main__":
    main()
