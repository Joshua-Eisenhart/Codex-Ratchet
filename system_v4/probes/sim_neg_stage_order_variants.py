#!/usr/bin/env python3
"""
Negative: Stage Operator Order Scrambled
========================================
Proves that the operator internal subcycle order (Ti->Fe->Te->Fi)
is NOT completely arbitrary. Scrambling the operators diverges the
macro-stage trace and axis trajectories from the baseline.

KILL token: K_NEG_STAGE_ORDER_SCRAMBLED
"""

import json
import os
from collections import defaultdict
from datetime import datetime, UTC
from itertools import permutations

from stage_matrix_helpers import (
    init_stage, run_program_variant, compare_variants,
    summarize_family, OPERATORS,
)
from type2_engine_sim import TYPE1_STAGES, TYPE2_STAGES
from proto_ratchet_sim_runner import EvidenceToken

RESULT_NAME = "neg_stage_order_variants_results.json"
N_TRIALS = 4
BASELINE_ORDER = tuple(OPERATORS)
ORDER_VARIANTS = {
    "_".join(order): list(order)
    for order in permutations(OPERATORS)
    if tuple(order) != BASELINE_ORDER
}

def run():
    type_tables = {1: TYPE1_STAGES, 2: TYPE2_STAGES}
    order_sweep = defaultdict(list)

    print("=" * 80)
    print("NEGATIVE: STAGE OPERATOR SCRAMBLED")
    print("=" * 80)

    for engine_type, table in type_tables.items():
        for row in table:
            stage_num = row[0]
            axis6_up = row[4]
            for t in range(N_TRIALS):
                seed = 4000 + engine_type * 100 + stage_num * 10 + t
                engine, state0, meta = init_stage(engine_type, row, seed)

                # Baseline
                base = run_program_variant(
                    engine_type, row, seed,
                    operator_order=list(OPERATORS),
                    lever_program=[axis6_up] * 4,
                )

                # Sweeps
                for variant_name, order in ORDER_VARIANTS.items():
                    alt = run_program_variant(
                        engine_type, row, seed,
                        operator_order=order,
                        lever_program=[axis6_up] * 4,
                    )
                    order_sweep[variant_name].append(compare_variants(base, alt))

    order_summary = summarize_family(order_sweep)
    closest_wrong_order = min(order_summary.items(), key=lambda kv: kv[1]["mean_total_d"])
    
    print(f"  closest wrong order: {closest_wrong_order[0]}")
    print(f"  total divergence D(L)+D(R): {closest_wrong_order[1]['mean_total_d']:.4f}")
    kill_pass = "KILL" if closest_wrong_order[1]["mean_total_d"] > 0.015 else "PASS"
    print(f"  → {kill_pass} (scrambled order diverges from baseline)")

    tokens = [
        EvidenceToken(
            "K_NEG_STAGE_ORDER_SCRAMBLED",
            "S_SIM_NEG_STAGE_ORDER",
            kill_pass,
            float(closest_wrong_order[1]["mean_total_d"]),
        )
    ]

    payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "closest_wrong_order": {"name": closest_wrong_order[0], **closest_wrong_order[1]},
        "evidence_ledger": [t.__dict__ for t in tokens],
    }
    
    outpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results", RESULT_NAME)
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w") as f:
        json.dump(payload, f, indent=2)

    return tokens

if __name__ == "__main__":
    run()
