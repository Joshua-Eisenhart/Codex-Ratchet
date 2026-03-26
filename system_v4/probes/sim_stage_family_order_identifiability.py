#!/usr/bin/env python3
"""
Family-specific order identifiability for the 16x4 stage matrix.

Ranks all 24 operator orders separately by loop family and engine type.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime, UTC
from itertools import permutations

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from proto_ratchet_sim_runner import EvidenceToken
from stage_matrix_neg_lib import (
    BASELINE_ORDER, all_stage_rows, run_program_variant,
    compare_variants_rich,
)


RESULT_NAME = "stage_family_order_identifiability_results.json"
N_TRIALS = 4
ORDERS = [tuple(order) for order in permutations(BASELINE_ORDER) if tuple(order) != BASELINE_ORDER]
NEAR_EQUIV_THRESHOLD = 0.03
WEAK_FAIL_THRESHOLD = 0.08


def classify(total_d: float) -> str:
    if total_d < NEAR_EQUIV_THRESHOLD:
        return "near_equivalent"
    if total_d < WEAK_FAIL_THRESHOLD:
        return "weakly_separated"
    return "strongly_separated"


def summarize(records: list[dict]) -> dict:
    n = len(records)
    return {
        "mean_d_L": float(sum(r["d_L"] for r in records) / n),
        "mean_d_R": float(sum(r["d_R"] for r in records) / n),
        "mean_total_d": float(sum(r["d_L"] + r["d_R"] for r in records) / n),
        "mean_axis_diff_count": float(sum(r["n_axis_diff"] for r in records) / n),
        "mean_abs_dphi_gap": float(sum(abs(r["abs_dphi_gap"]) for r in records) / n),
        "mean_abs_ga5_gap": float(sum(abs(r["ga5_gap"]) for r in records) / n),
        "mean_abs_ga3_gap": float(sum(abs(r["ga3_gap"]) for r in records) / n),
    }


def rank_family(records_by_order: dict[tuple[str, ...], list[dict]]) -> dict:
    summaries = []
    for order, records in records_by_order.items():
        s = summarize(records)
        s["order"] = list(order)
        s["name"] = "_".join(order)
        s["assessment"] = classify(s["mean_total_d"])
        summaries.append(s)
    summaries.sort(key=lambda item: item["mean_total_d"])
    return {
        "nearest_orders": summaries[:5],
        "strongest_separated_orders": summaries[-5:][::-1],
    }


def run():
    by_loop_role = defaultdict(lambda: defaultdict(list))
    by_engine_type = defaultdict(lambda: defaultdict(list))

    for engine_type, row in all_stage_rows():
        loop_role = row[5]
        axis6_up = bool(row[4])
        for t in range(N_TRIALS):
            seed = 11000 + engine_type * 100 + row[0] * 10 + t
            base = run_program_variant(
                engine_type, row, seed,
                operator_order=list(BASELINE_ORDER),
                lever_program=[axis6_up] * len(BASELINE_ORDER),
            )
            for order in ORDERS:
                alt = run_program_variant(
                    engine_type, row, seed,
                    operator_order=list(order),
                    lever_program=[axis6_up] * len(order),
                )
                comp = compare_variants_rich(base, alt)
                by_loop_role[loop_role][order].append(comp)
                by_engine_type[str(engine_type)][order].append(comp)

    loop_rankings = {
        loop_role: rank_family(records_by_order)
        for loop_role, records_by_order in by_loop_role.items()
    }
    engine_rankings = {
        engine_type: rank_family(records_by_order)
        for engine_type, records_by_order in by_engine_type.items()
    }

    payload = {
        "schema": "SIM_EVIDENCE_v1",
        "file": "sim_stage_family_order_identifiability.py",
        "timestamp": datetime.now(UTC).isoformat(),
        "trial_count_per_stage": N_TRIALS,
        "baseline_order": list(BASELINE_ORDER),
        "near_equiv_threshold": NEAR_EQUIV_THRESHOLD,
        "weak_fail_threshold": WEAK_FAIL_THRESHOLD,
        "by_loop_role": loop_rankings,
        "by_engine_type": engine_rankings,
        "evidence_ledger": [
            EvidenceToken(
                "E_STAGE_FAMILY_ORDER_IDENTIFIABILITY_V1",
                "S_SIM_STAGE_FAMILY_ORDER_IDENTIFIABILITY_V1",
                "PASS",
                0.0,
            ).__dict__
        ],
    }

    outpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results", RESULT_NAME)
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w") as f:
        json.dump(payload, f, indent=2)

    for loop_role, ranking in loop_rankings.items():
        best = ranking["nearest_orders"][0]
        print(f"{loop_role}: nearest {best['name']} totalD={best['mean_total_d']:.4f} {best['assessment']}")
    print(f"saved: {outpath}")


if __name__ == "__main__":
    run()
