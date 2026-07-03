"""QUARANTINE_EXPLORATORY: NumPy substrate for qit_dual_engine_live_v0.

classification='scratch_diagnostic'; promotion_allowed=false.

Builds the pinned eps-sheet direct/conjugated stages from oracle_targets_3q.py
generator/operator functions, then runs the same shared-world dual-engine loop.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.linalg import expm

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from common_dual_engine import ENGINES_DIR, SHEET_STAGE_DEFS, load_module, run_substrate_cli, super_from_density_map


def build_sheet_stage_supers() -> dict[str, list[np.ndarray]]:
    oracle = load_module("cr_oracle_targets_3q_dual_numpy_loop", ENGINES_DIR / "oracle_targets_3q.py")
    out: dict[str, list[np.ndarray]] = {"D": [], "C": []}
    for engine_id, stage_defs in SHEET_STAGE_DEFS.items():
        for stage in stage_defs:
            terrain = expm(oracle.T_FLOW * super_from_density_map(oracle.gen(stage["terrain"])))
            op_super = super_from_density_map(oracle.op(stage["op"]))
            out[engine_id].append((op_super @ terrain).astype(np.complex128))
    return out


if __name__ == "__main__":
    run_substrate_cli("numpy_oracle_loop", build_sheet_stage_supers)
