"""QUARANTINE_EXPLORATORY: JAX substrate for qit_live_loop_3q_v1.

classification='scratch_diagnostic'; promotion_allowed=false.

Precomputes all 16 stage superoperators once using jax_engine_3q.py's
gen_super/op_map and jax.scipy.linalg.expm with x64 enabled by that source.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from common_3q import ENGINES_DIR, load_module, run_substrate_cli


def build_stage_supers() -> list[np.ndarray]:
    jax_engine = load_module("cr_jax_engine_3q_loop", ENGINES_DIR / "jax_engine_3q.py")
    stages = []
    for t in range(8):
        terrain = jax_engine.expm(jax_engine.T_FLOW * jax_engine.gen_super(t))
        for op_name in jax_engine.NATIVE[t]:
            stages.append(np.asarray(jax_engine.op_map(op_name) @ terrain, dtype=np.complex128))
    return stages


if __name__ == "__main__":
    run_substrate_cli("jax_loop", build_stage_supers)
