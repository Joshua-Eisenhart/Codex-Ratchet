#!/usr/bin/env python3
"""
Negative witness: flattening type-specific weighting changes the stage matrix materially.
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


RESULT_NAME = "neg_type_flatten_stage_matrix_results.json"
N_TRIALS = 4


def run():
    records = []
    for engine_type, row in all_stage_rows():
        axis6_up = bool(row[4])
        for t in range(N_TRIALS):
            seed = 7000 + engine_type * 100 + row[0] * 10 + t
            base = run_program_variant(
                engine_type, row, seed,
                operator_order=list(BASELINE_ORDER),
                lever_program=[axis6_up] * len(BASELINE_ORDER),
            )
            alt = run_program_variant(
                engine_type, row, seed,
                operator_order=list(BASELINE_ORDER),
                lever_program=[axis6_up] * len(BASELINE_ORDER),
                flatten_type_weighting=True,
            )
            records.append(compare_variants(base, alt))

    summary = {
        "mean_d_L": mean_metric(records, "d_L"),
        "mean_d_R": mean_metric(records, "d_R"),
        "mean_total_d": float(sum(r["d_L"] + r["d_R"] for r in records) / len(records)),
        "mean_axis_diff_count": float(sum(r["n_axis_diff"] for r in records) / len(records)),
    }

    tokens = [
        EvidenceToken(
            "K_NEG_STAGE_TYPE_FLAT_V1",
            "S_SIM_NEG_STAGE_TYPE_FLAT_V1",
            "KILL" if summary["mean_total_d"] > 0.05 else "PASS",
            float(summary["mean_total_d"]),
        ),
    ]

    payload = {
        "schema": "SIM_EVIDENCE_v1",
        "file": "neg_type_flatten_stage_matrix_sim.py",
        "timestamp": datetime.now(UTC).isoformat(),
        "trial_count_per_stage": N_TRIALS,
        "flat_type_weighting": summary,
        "evidence_ledger": [t.__dict__ for t in tokens],
    }

    outpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results", RESULT_NAME)
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"flat-type totalD={summary['mean_total_d']:.4f}")
    print(f"saved: {outpath}")
    return tokens


if __name__ == "__main__":
    run()
