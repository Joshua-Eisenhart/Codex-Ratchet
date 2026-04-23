#!/usr/bin/env python3
"""
Negative witness: stage-level shared Axis 6 matters.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, UTC

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from proto_ratchet_sim_runner import EvidenceToken
from stage_matrix_neg_lib import (
    BASELINE_ORDER, MIXED_AXIS6_VARIANTS, all_stage_rows, init_stage,
    baseline_controls, run_program_variant, run_engine_baseline, compare_variants,
    mean_metric,
)
from geometric_operators import trace_distance_2x2


RESULT_NAME = "neg_axis6_shared_stage_matrix_results.json"
N_TRIALS = 4


def run():
    control_equivalence = []
    mixed_records = {name: [] for name in MIXED_AXIS6_VARIANTS}

    for engine_type, row in all_stage_rows():
        for t in range(N_TRIALS):
            seed = 5000 + engine_type * 100 + row[0] * 10 + t
            engine, state0, engine_state, meta = run_engine_baseline(engine_type, row, seed)
            base = run_program_variant(
                engine_type, row, seed,
                operator_order=list(BASELINE_ORDER),
                lever_program=[meta["axis6_up"]] * len(BASELINE_ORDER),
            )
            control_equivalence.append({
                "d_L": float(trace_distance_2x2(engine_state.rho_L, base["final_state"].rho_L)),
                "d_R": float(trace_distance_2x2(engine_state.rho_R, base["final_state"].rho_R)),
            })

            for name, canonical_pattern in MIXED_AXIS6_VARIANTS.items():
                lever_program = [meta["axis6_up"] if bit else (not meta["axis6_up"]) for bit in canonical_pattern]
                alt = run_program_variant(
                    engine_type, row, seed,
                    operator_order=list(BASELINE_ORDER),
                    lever_program=lever_program,
                )
                mixed_records[name].append(compare_variants(base, alt))

    control_mean = {
        "d_L": mean_metric(control_equivalence, "d_L"),
        "d_R": mean_metric(control_equivalence, "d_R"),
    }
    sweep = {
        name: {
            "mean_d_L": mean_metric(records, "d_L"),
            "mean_d_R": mean_metric(records, "d_R"),
            "mean_total_d": float(sum(r["d_L"] + r["d_R"] for r in records) / len(records)),
            "mean_axis_diff_count": float(sum(r["n_axis_diff"] for r in records) / len(records)),
        }
        for name, records in mixed_records.items()
    }
    closest = min(sweep.items(), key=lambda kv: kv[1]["mean_total_d"])
    top3 = sorted(sweep.items(), key=lambda kv: kv[1]["mean_total_d"])[:3]

    tokens = [
        EvidenceToken(
            "E_NEG_STAGE_AXIS6_CONTROL_EQUIV",
            "S_SIM_NEG_STAGE_AXIS6_CONTROL_V1",
            "PASS" if max(control_mean["d_L"], control_mean["d_R"]) < 1e-9 else "KILL",
            float(max(control_mean["d_L"], control_mean["d_R"])),
        ),
        EvidenceToken(
            "K_NEG_STAGE_AXIS6_SHARED_V1",
            "S_SIM_NEG_STAGE_AXIS6_SHARED_V1",
            "KILL" if closest[1]["mean_total_d"] > 0.05 else "PASS",
            float(closest[1]["mean_total_d"]),
        ),
    ]

    payload = {
        "schema": "SIM_EVIDENCE_v1",
        "file": "neg_axis6_shared_stage_matrix_sim.py",
        "timestamp": datetime.now(UTC).isoformat(),
        "trial_count_per_stage": N_TRIALS,
        "control_equivalence": control_mean,
        "mixed_axis6_sweep": sweep,
        "closest_mixed_axis6": {"name": closest[0], **closest[1]},
        "top3_mixed_axis6": [{"name": name, **summary} for name, summary in top3],
        "evidence_ledger": [t.__dict__ for t in tokens],
    }

    outpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results", RESULT_NAME)
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"closest mixed axis6: {closest[0]} totalD={closest[1]['mean_total_d']:.4f}")
    print(f"saved: {outpath}")
    return tokens


if __name__ == "__main__":
    run()
