#!/usr/bin/env python3
"""
Exploratory ranking of all 24 operator orders for the 16x4 stage matrix.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, UTC
from itertools import permutations

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from proto_ratchet_sim_runner import EvidenceToken
from stage_matrix_neg_lib import (
    BASELINE_ORDER, all_stage_rows, run_program_variant,
    compare_variants_rich, mean_metric,
)


RESULT_NAME = "stage_order_identifiability_results.json"
N_TRIALS = 4
ORDERS = [tuple(order) for order in permutations(BASELINE_ORDER)]
NEAR_EQUIV_THRESHOLD = 0.03
WEAK_FAIL_THRESHOLD = 0.08


def classify(total_d: float) -> str:
    if total_d < NEAR_EQUIV_THRESHOLD:
        return "near_equivalent"
    if total_d < WEAK_FAIL_THRESHOLD:
        return "weakly_separated"
    return "strongly_separated"


def summarize(records: list[dict]) -> dict:
    return {
        "mean_d_L": mean_metric(records, "d_L"),
        "mean_d_R": mean_metric(records, "d_R"),
        "mean_total_d": float(sum(r["d_L"] + r["d_R"] for r in records) / len(records)),
        "mean_axis_diff_count": float(sum(r["n_axis_diff"] for r in records) / len(records)),
        "mean_abs_dphi_gap": mean_metric(records, "abs_dphi_gap"),
        "mean_abs_ga5_gap": float(sum(abs(r["ga5_gap"]) for r in records) / len(records)),
        "mean_abs_ga3_gap": float(sum(abs(r["ga3_gap"]) for r in records) / len(records)),
    }


def run():
    order_records = {order: [] for order in ORDERS if order != BASELINE_ORDER}

    for engine_type, row in all_stage_rows():
        axis6_up = bool(row[4])
        for t in range(N_TRIALS):
            seed = 9000 + engine_type * 100 + row[0] * 10 + t
            base = run_program_variant(
                engine_type, row, seed,
                operator_order=list(BASELINE_ORDER),
                lever_program=[axis6_up] * len(BASELINE_ORDER),
            )
            for order in order_records:
                alt = run_program_variant(
                    engine_type, row, seed,
                    operator_order=list(order),
                    lever_program=[axis6_up] * len(order),
                )
                order_records[order].append(compare_variants_rich(base, alt))

    summaries = []
    for order, records in order_records.items():
        summary = summarize(records)
        summary["order"] = list(order)
        summary["name"] = "_".join(order)
        summary["assessment"] = classify(summary["mean_total_d"])
        summaries.append(summary)

    summaries.sort(key=lambda item: item["mean_total_d"])
    nearest = summaries[:5]
    strongest = summaries[-5:][::-1]

    tokens = [
        EvidenceToken(
            "E_STAGE_ORDER_IDENTIFIABILITY_V1",
            "S_SIM_STAGE_ORDER_IDENTIFIABILITY_V1",
            "PASS",
            float(nearest[0]["mean_total_d"]),
        ),
    ]

    payload = {
        "schema": "SIM_EVIDENCE_v1",
        "file": "sim_stage_order_identifiability.py",
        "timestamp": datetime.now(UTC).isoformat(),
        "trial_count_per_stage": N_TRIALS,
        "baseline_order": list(BASELINE_ORDER),
        "near_equiv_threshold": NEAR_EQUIV_THRESHOLD,
        "weak_fail_threshold": WEAK_FAIL_THRESHOLD,
        "nearest_orders": nearest,
        "strongest_separated_orders": strongest,
        "all_orders": summaries,
        "evidence_ledger": [t.__dict__ for t in tokens],
    }

    outpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results", RESULT_NAME)
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"nearest order: {nearest[0]['name']} totalD={nearest[0]['mean_total_d']:.4f} {nearest[0]['assessment']}")
    print(f"strongest separated: {strongest[0]['name']} totalD={strongest[0]['mean_total_d']:.4f}")
    print(f"saved: {outpath}")
    return tokens


if __name__ == "__main__":
    run()
