"""QUARANTINE_EXPLORATORY: NumPy oracle substrate for qit_live_loop_3q_v1.

classification='scratch_diagnostic'; promotion_allowed=false.

Precomputes all 16 stage superoperators once using oracle_targets_3q.py's
generator/op functions and scipy.linalg.expm.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.linalg import expm

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from common_3q import ENGINES_DIR, load_module, run_substrate_cli, super_from_density_map


def build_stage_supers() -> list[np.ndarray]:
    oracle = load_module("cr_oracle_targets_3q_numpy_loop", ENGINES_DIR / "oracle_targets_3q.py")
    stages = []
    for t in range(8):
        terrain = expm(oracle.T_FLOW * super_from_density_map(oracle.gen(t)))
        for op_name in oracle.NATIVE[t]:
            op_super = super_from_density_map(oracle.op(op_name))
            stages.append((op_super @ terrain).astype(np.complex128))
    return stages


if __name__ == "__main__":
    run_substrate_cli("numpy_oracle_loop", build_stage_supers)
