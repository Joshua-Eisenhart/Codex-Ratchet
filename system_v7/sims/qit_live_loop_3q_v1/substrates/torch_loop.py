"""QUARANTINE_EXPLORATORY: PyTorch substrate for qit_live_loop_3q_v1.

classification='scratch_diagnostic'; promotion_allowed=false.

Precomputes all 16 stage superoperators once using torch_engine_3q.py's
terrain_super/op_super and torch.linalg.matrix_exp in complex128.
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
    torch_engine = load_module("cr_torch_engine_3q_loop", ENGINES_DIR / "torch_engine_3q.py")
    torch = torch_engine.torch
    stages = []
    for t in range(8):
        terrain = torch.linalg.matrix_exp(torch_engine.T_FLOW * torch_engine.terrain_super(t))
        for op_name in torch_engine.NATIVE[t]:
            stage = torch_engine.op_super(op_name) @ terrain
            stages.append(stage.detach().cpu().numpy().astype(np.complex128))
    return stages


if __name__ == "__main__":
    run_substrate_cli("torch_loop", build_stage_supers)
