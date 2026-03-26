#!/usr/bin/env python3
"""
Negative: Stage Native-Only Collapse
====================================
Proves that the engine does NOT just apply the 'native operator' 4 times.
All 4 operators (Ti, Fe, Te, Fi) must be executed in sequence for the
stage to run correctly. Repeating the native operator collapses the state.

KILL token: K_NEG_STAGE_NATIVE_ONLY
"""

import json
import os
import numpy as np
from datetime import datetime, UTC

from stage_matrix_helpers import (
    init_stage, run_program_variant, compare_variants,
    OPERATORS,
)
from type2_engine_sim import TYPE1_STAGES, TYPE2_STAGES
from proto_ratchet_sim_runner import EvidenceToken

RESULT_NAME = "neg_stage_native_only_results.json"
N_TRIALS = 4

def run():
    type_tables = {1: TYPE1_STAGES, 2: TYPE2_STAGES}
    records = []

    print("=" * 80)
    print("NEGATIVE: NATIVE-ONLY COLLAPSE")
    print("=" * 80)

    for engine_type, table in type_tables.items():
        for row in table:
            stage_num = row[0]
            native_op = row[2]
            axis6_up = row[4]
            for t in range(N_TRIALS):
                seed = 4000 + engine_type * 100 + stage_num * 10 + t
                engine, state0, meta = init_stage(engine_type, row, seed)

                base = run_program_variant(
                    engine_type, row, seed,
                    operator_order=list(OPERATORS),
                    lever_program=[axis6_up] * 4,
                )

                alt = run_program_variant(
                    engine_type, row, seed,
                    operator_order=[native_op] * 4,
                    lever_program=[axis6_up] * 4,
                )
                records.append(compare_variants(base, alt))

    mean_d = float(np.mean([r["d_L"] + r["d_R"] for r in records]))
    
    print(f"  native-only collapse D(L)+D(R): {mean_d:.4f}")
    kill_pass = "KILL" if mean_d > 0.10 else "PASS"
    print(f"  → {kill_pass} (native-only repeat destroys the state)")

    tokens = [
        EvidenceToken(
            "K_NEG_STAGE_NATIVE_ONLY",
            "S_SIM_NEG_STAGE_NATIVE",
            kill_pass,
            mean_d,
        )
    ]

    payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "mean_total_d": mean_d,
        "evidence_ledger": [t.__dict__ for t in tokens],
    }
    
    outpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results", RESULT_NAME)
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w") as f:
        json.dump(payload, f, indent=2)

    return tokens

if __name__ == "__main__":
    run()
