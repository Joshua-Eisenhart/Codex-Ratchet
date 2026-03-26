#!/usr/bin/env python3
"""
Negative: Stage Axis-6 Mixed
============================
Proves that the shared Axis-6 lever strictly controls the macro-stage.
Mixing the Up/Down polarities inside the 4-operator subcycle causes
the trace distance to strongly diverge.

KILL token: K_NEG_STAGE_AXIS6_MIXED
"""

import json
import os
from collections import defaultdict
from datetime import datetime, UTC
from itertools import product

from stage_matrix_helpers import (
    init_stage, run_program_variant, compare_variants,
    summarize_family, OPERATORS,
)
from type2_engine_sim import TYPE1_STAGES, TYPE2_STAGES
from proto_ratchet_sim_runner import EvidenceToken

RESULT_NAME = "neg_stage_axis6_mix_results.json"
N_TRIALS = 4
AXIS6_VARIANTS = {
    "".join("U" if bit else "D" for bit in pattern): list(pattern)
    for pattern in product([False, True], repeat=4)
    if tuple(pattern) not in ((False, False, False, False), (True, True, True, True))
}

def run():
    type_tables = {1: TYPE1_STAGES, 2: TYPE2_STAGES}
    axis6_sweep = defaultdict(list)

    print("=" * 80)
    print("NEGATIVE: MIXED AXIS-6 POLARITY")
    print("=" * 80)

    for engine_type, table in type_tables.items():
        for row in table:
            stage_num = row[0]
            axis6_up = row[4]
            for t in range(N_TRIALS):
                seed = 4000 + engine_type * 100 + stage_num * 10 + t
                engine, state0, meta = init_stage(engine_type, row, seed)

                base = run_program_variant(
                    engine_type, row, seed,
                    operator_order=list(OPERATORS),
                    lever_program=[axis6_up] * 4,
                )

                for variant_name, canonical_pattern in AXIS6_VARIANTS.items():
                    lever_program = [
                        axis6_up if bit else (not axis6_up)
                        for bit in canonical_pattern
                    ]
                    alt = run_program_variant(
                        engine_type, row, seed,
                        operator_order=list(OPERATORS),
                        lever_program=lever_program,
                    )
                    axis6_sweep[variant_name].append(compare_variants(base, alt))

    axis6_summary = summarize_family(axis6_sweep)
    closest_wrong_axis6 = min(axis6_summary.items(), key=lambda kv: kv[1]["mean_total_d"])
    
    print(f"  closest mixed axis6: {closest_wrong_axis6[0]}")
    print(f"  total divergence D(L)+D(R): {closest_wrong_axis6[1]['mean_total_d']:.4f}")
    kill_pass = "KILL" if closest_wrong_axis6[1]["mean_total_d"] > 0.03 else "PASS"
    print(f"  → {kill_pass} (mixed axis-6 diverges from shared baseline)")

    tokens = [
        EvidenceToken(
            "K_NEG_STAGE_AXIS6_MIXED",
            "S_SIM_NEG_STAGE_AXIS6",
            kill_pass,
            float(closest_wrong_axis6[1]["mean_total_d"]),
        )
    ]

    payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "closest_mixed_axis6": {"name": closest_wrong_axis6[0], **closest_wrong_axis6[1]},
        "evidence_ledger": [t.__dict__ for t in tokens],
    }
    
    outpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results", RESULT_NAME)
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w") as f:
        json.dump(payload, f, indent=2)

    return tokens

if __name__ == "__main__":
    run()
