#!/usr/bin/env python3
"""
Negative witness: dropping one operator from the 4-subcycle stage is not equivalent.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, UTC

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from proto_ratchet_sim_runner import EvidenceToken
from stage_matrix_neg_lib import (
    BASELINE_ORDER, all_stage_rows, run_program_variant, compare_variants, mean_metric,
)


RESULT_NAME = "neg_missing_operator_stage_matrix_results.json"
N_TRIALS = 4
EQUIVALENCE_FAIL_THRESHOLD = 0.05
STRONG_FAIL_THRESHOLD = 0.15


def run():
    records_by_missing = {op: [] for op in BASELINE_ORDER}

    for engine_type, row in all_stage_rows():
        axis6_up = bool(row[4])
        for t in range(N_TRIALS):
            seed = 8000 + engine_type * 100 + row[0] * 10 + t
            base = run_program_variant(
                engine_type, row, seed,
                operator_order=list(BASELINE_ORDER),
                lever_program=[axis6_up] * len(BASELINE_ORDER),
            )
            for missing_op in BASELINE_ORDER:
                order = [op for op in BASELINE_ORDER if op != missing_op]
                alt = run_program_variant(
                    engine_type, row, seed,
                    operator_order=order,
                    lever_program=[axis6_up] * len(order),
                )
                records_by_missing[missing_op].append(compare_variants(base, alt))

    def classify(mean_total_d: float) -> str:
        if mean_total_d >= STRONG_FAIL_THRESHOLD:
            return "strong_fail"
        if mean_total_d >= EQUIVALENCE_FAIL_THRESHOLD:
            return "weak_fail"
        return "near_equivalent"

    sweep = {
        missing_op: {
            "mean_d_L": mean_metric(records, "d_L"),
            "mean_d_R": mean_metric(records, "d_R"),
            "mean_total_d": float(sum(r["d_L"] + r["d_R"] for r in records) / len(records)),
            "mean_axis_diff_count": float(sum(r["n_axis_diff"] for r in records) / len(records)),
            "assessment": classify(float(sum(r["d_L"] + r["d_R"] for r in records) / len(records))),
        }
        for missing_op, records in records_by_missing.items()
    }
    closest = min(sweep.items(), key=lambda kv: kv[1]["mean_total_d"])

    tokens = [
        EvidenceToken(
            "K_NEG_STAGE_MISSING_OPERATOR_V1",
            "S_SIM_NEG_STAGE_MISSING_OPERATOR_V1",
            "KILL" if closest[1]["mean_total_d"] > EQUIVALENCE_FAIL_THRESHOLD else "PASS",
            float(closest[1]["mean_total_d"]),
        ),
    ]

    payload = {
        "schema": "SIM_EVIDENCE_v1",
        "file": "neg_missing_operator_stage_matrix_sim.py",
        "timestamp": datetime.now(UTC).isoformat(),
        "trial_count_per_stage": N_TRIALS,
        "equivalence_fail_threshold": EQUIVALENCE_FAIL_THRESHOLD,
        "strong_fail_threshold": STRONG_FAIL_THRESHOLD,
        "missing_operator_sweep": sweep,
        "closest_missing_operator": {"operator": closest[0], **closest[1]},
        "evidence_ledger": [t.__dict__ for t in tokens],
    }

    outpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results", RESULT_NAME)
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"closest missing op: {closest[0]} totalD={closest[1]['mean_total_d']:.4f}")
    print(f"saved: {outpath}")
    return tokens


if __name__ == "__main__":
    run()
