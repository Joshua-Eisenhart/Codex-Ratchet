#!/usr/bin/env python3
"""
Focused Fe-omission probe with richer metrics than final-state trace alone.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime, UTC

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from proto_ratchet_sim_runner import EvidenceToken
from stage_matrix_neg_lib import (
    BASELINE_ORDER, all_stage_rows, run_program_variant,
    compare_variants_rich, mean_metric,
)


RESULT_NAME = "neg_missing_fe_stage_matrix_results.json"
N_TRIALS = 4
TRACE_THRESHOLD = 0.05
DPHI_THRESHOLD = 0.10


def summarize(records: list[dict]) -> dict:
    return {
        "mean_d_L": mean_metric(records, "d_L"),
        "mean_d_R": mean_metric(records, "d_R"),
        "mean_total_d": float(sum(r["d_L"] + r["d_R"] for r in records) / len(records)),
        "mean_axis_diff_count": float(sum(r["n_axis_diff"] for r in records) / len(records)),
        "mean_abs_dphi_gap": float(sum(abs(r["abs_dphi_gap"]) for r in records) / len(records)),
        "mean_abs_ga5_gap": float(sum(abs(r["ga5_gap"]) for r in records) / len(records)),
        "mean_abs_ga3_gap": float(sum(abs(r["ga3_gap"]) for r in records) / len(records)),
        "mean_abs_ga1_gap": float(sum(abs(r["ga1_gap"]) for r in records) / len(records)),
    }


def run():
    all_records = []
    by_native = defaultdict(list)
    by_loop = defaultdict(list)
    by_engine = defaultdict(list)

    for engine_type, row in all_stage_rows():
        native_operator = row[2]
        loop_role = row[5]
        axis6_up = bool(row[4])
        for t in range(N_TRIALS):
            seed = 10000 + engine_type * 100 + row[0] * 10 + t
            base = run_program_variant(
                engine_type, row, seed,
                operator_order=list(BASELINE_ORDER),
                lever_program=[axis6_up] * len(BASELINE_ORDER),
            )
            alt = run_program_variant(
                engine_type, row, seed,
                operator_order=[op for op in BASELINE_ORDER if op != "Fe"],
                lever_program=[axis6_up] * 3,
            )
            comp = compare_variants_rich(base, alt)
            all_records.append(comp)
            by_native[native_operator].append(comp)
            by_loop[loop_role].append(comp)
            by_engine[str(engine_type)].append(comp)

    overall = summarize(all_records)
    native_breakdown = {key: summarize(records) for key, records in by_native.items()}
    loop_breakdown = {key: summarize(records) for key, records in by_loop.items()}
    engine_breakdown = {key: summarize(records) for key, records in by_engine.items()}

    trace_fail = overall["mean_total_d"] > TRACE_THRESHOLD
    dphi_fail = overall["mean_abs_dphi_gap"] > DPHI_THRESHOLD

    tokens = [
        EvidenceToken(
            "K_NEG_MISSING_FE_TRACE_V1",
            "S_SIM_NEG_MISSING_FE_TRACE_V1",
            "KILL" if trace_fail else "PASS",
            float(overall["mean_total_d"]),
        ),
        EvidenceToken(
            "K_NEG_MISSING_FE_DPHI_V1",
            "S_SIM_NEG_MISSING_FE_DPHI_V1",
            "KILL" if dphi_fail else "PASS",
            float(overall["mean_abs_dphi_gap"]),
        ),
    ]

    payload = {
        "schema": "SIM_EVIDENCE_v1",
        "file": "neg_missing_fe_stage_matrix_sim.py",
        "timestamp": datetime.now(UTC).isoformat(),
        "trial_count_per_stage": N_TRIALS,
        "trace_fail_threshold": TRACE_THRESHOLD,
        "abs_dphi_gap_threshold": DPHI_THRESHOLD,
        "overall": overall,
        "by_native_operator": native_breakdown,
        "by_loop_role": loop_breakdown,
        "by_engine_type": engine_breakdown,
        "evidence_ledger": [t.__dict__ for t in tokens],
    }

    outpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results", RESULT_NAME)
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"missing-Fe totalD={overall['mean_total_d']:.4f} abs|ΔΦ|gap={overall['mean_abs_dphi_gap']:.4f}")
    print(f"saved: {outpath}")
    return tokens


if __name__ == "__main__":
    run()
