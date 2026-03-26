#!/usr/bin/env python3
"""
Negative: Stage Drop Single Subordinate Operator
================================================
Proves that every single one of the 4 operators (Ti, Fe, Te, Fi)
is load-bearing in the macro-stage subcycle. Dropping exactly ONE
subordinate (non-native) operator causes trace divergence, proving
the stage relies on the complete 4-part process cycle, not just
the native operator.

KILL token: K_NEG_STAGE_DROP_ONE
"""

import json
import os
from collections import defaultdict
from datetime import datetime, UTC

from stage_matrix_helpers import (
    init_stage, run_program_variant, compare_variants,
    summarize_family, OPERATORS,
)
from type2_engine_sim import TYPE1_STAGES, TYPE2_STAGES
from proto_ratchet_sim_runner import EvidenceToken

RESULT_NAME = "neg_stage_drop_one_results.json"
N_TRIALS = 4

def run():
    type_tables = {1: TYPE1_STAGES, 2: TYPE2_STAGES}
    drop_sweep = defaultdict(list)

    print("=" * 80)
    print("NEGATIVE: DROP SINGLE SUBORDINATE OPERATOR")
    print("=" * 80)

    for engine_type, table in type_tables.items():
        for row in table:
            stage_num = row[0]
            native_op = row[2]
            axis6_up = row[4]
            for t in range(N_TRIALS):
                seed = 4000 + engine_type * 100 + stage_num * 10 + t
                engine, state0, meta = init_stage(engine_type, row, seed)

                # Baseline (all 4 operators)
                base = run_program_variant(
                    engine_type, row, seed,
                    operator_order=list(OPERATORS),
                    lever_program=[axis6_up] * 4,
                )

                # Sweep: Drop exactly one operator
                for op_to_drop in OPERATORS:
                    # Actually, the requirement was "drop exactly one subordinate operator"
                    # But if we drop the native operator, obviously that diverges too.
                    # This sweep drops each operator individually and records the diverge.
                    dropped_order = [op for op in OPERATORS if op != op_to_drop]
                    alt = run_program_variant(
                        engine_type, row, seed,
                        operator_order=dropped_order,
                        lever_program=[axis6_up] * 3,
                    )
                    
                    variant_name = f"drop_{op_to_drop}"
                    drop_sweep[variant_name].append(compare_variants(base, alt))

    drop_summary = summarize_family(drop_sweep)
    
    # We find the *least damaging* single dropout to prove that even
    # the least important operator is still fully load-bearing.
    closest_drop = min(drop_summary.items(), key=lambda kv: kv[1]["mean_total_d"])
    
    print(f"  least damaging dropout: {closest_drop[0]}")
    print(f"  total divergence D(L)+D(R): {closest_drop[1]['mean_total_d']:.4f}")
    kill_pass = "KILL" if closest_drop[1]["mean_total_d"] > 0.05 else "PASS"
    print(f"  → {kill_pass} (every individual operator is load-bearing)")

    tokens = [
        EvidenceToken(
            "K_NEG_STAGE_DROP_ONE",
            "S_SIM_NEG_STAGE_DROP_ONE",
            kill_pass,
            float(closest_drop[1]["mean_total_d"]),
        )
    ]

    payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "least_damaging_dropout": {"name": closest_drop[0], **closest_drop[1]},
        "evidence_ledger": [t.__dict__ for t in tokens],
    }
    
    outpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results", RESULT_NAME)
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w") as f:
        json.dump(payload, f, indent=2)

    return tokens

if __name__ == "__main__":
    run()
