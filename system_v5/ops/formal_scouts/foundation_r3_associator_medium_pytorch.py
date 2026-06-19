#!/usr/bin/env python3
"""PyTorch jacrev sensitivity leg for foundation_r3_associator_medium."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

import torch
from torch.func import jacrev


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_r3_associator_medium_pytorch.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_r3_associator_medium_pytorch_results.json"
RUNG_ID = "foundation_r3_associator_medium"
TOL = 1.0e-10


def cd_conj(x: torch.Tensor) -> torch.Tensor:
    signs = torch.ones(x.shape[0], dtype=torch.float64)
    signs[1:] = -1.0
    return x * signs


def multiply(table: torch.Tensor, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    return torch.einsum("cab,a,b->c", table, x, y)


def cd_double(parent: torch.Tensor) -> torch.Tensor:
    n = parent.shape[0]
    dim = 2 * n
    table = torch.zeros((dim, dim, dim), dtype=torch.float64)
    eye = torch.eye(dim, dtype=torch.float64)
    for i in range(dim):
        for j in range(dim):
            x, y = eye[i], eye[j]
            a, b = x[:n], x[n:]
            c, d = y[:n], y[n:]
            first = multiply(parent, a, c) - multiply(parent, cd_conj(d), b)
            second = multiply(parent, d, a) + multiply(parent, b, cd_conj(c))
            table[:, i, j] = torch.cat([first, second])
    return table


def build_tables() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    r = torch.zeros((1, 1, 1), dtype=torch.float64)
    r[0, 0, 0] = 1.0
    c = cd_double(r)
    h = cd_double(c)
    o = cd_double(h)
    h8 = torch.zeros_like(o)
    h8[:4, :4, :4] = h
    return h, h8, o


def basis(dim: int, idx: int) -> torch.Tensor:
    out = torch.zeros(dim, dtype=torch.float64)
    out[idx] = 1.0
    return out


def associator(table: torch.Tensor, a: torch.Tensor, b: torch.Tensor, c: torch.Tensor) -> torch.Tensor:
    return multiply(table, multiply(table, a, b), c) - multiply(table, a, multiply(table, b, c))


def max_associator_norm(table: torch.Tensor) -> tuple[float, list[int], torch.Tensor]:
    dim = table.shape[0]
    eye = torch.eye(dim, dtype=torch.float64)
    max_norm = -1.0
    witness = [0, 0, 0]
    witness_vec = torch.zeros(dim, dtype=torch.float64)
    for a in range(dim):
        for b in range(dim):
            for c in range(dim):
                vec = associator(table, eye[a], eye[b], eye[c])
                norm = float(torch.linalg.vector_norm(vec).item())
                if norm > max_norm:
                    max_norm = norm
                    witness = [a, b, c]
                    witness_vec = vec
    return max_norm, witness, witness_vec


def main() -> int:
    torch.set_default_dtype(torch.float64)
    h, h8, o = build_tables()
    h_norm, _h_witness, _h_vec = max_associator_norm(h)
    o_norm, witness, o_vec = max_associator_norm(o)
    a, b, c = [basis(8, idx) for idx in witness]

    def selector_associator_norm(alpha: torch.Tensor) -> torch.Tensor:
        table = h8 + alpha * (o - h8)
        vec = associator(table, a, b, c)
        return torch.linalg.vector_norm(vec)

    alpha_h = torch.tensor(0.0, dtype=torch.float64)
    alpha_o = torch.tensor(1.0, dtype=torch.float64)
    h_selector_norm = selector_associator_norm(alpha_h)
    o_selector_norm = selector_associator_norm(alpha_o)
    h_jacrev = jacrev(selector_associator_norm)(alpha_h)
    mid_jacrev = jacrev(selector_associator_norm)(torch.tensor(0.5, dtype=torch.float64))
    o_jacrev = jacrev(selector_associator_norm)(alpha_o)

    all_pass = bool(
        h_norm <= TOL
        and o_norm > TOL
        and float(h_selector_norm.item()) <= TOL
        and float(o_selector_norm.item()) > TOL
        and abs(float(h_jacrev.item())) <= TOL
        and abs(float(mid_jacrev.item())) > TOL
        and abs(float(o_jacrev.item())) > TOL
    )
    payload: dict[str, Any] = {
        "schema_version": "engine_leg_result_v1",
        "rung_id": RUNG_ID,
        "engine": "pytorch",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "reads_peer_result": False,
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "packages_used": ["torch", "torch.func"],
        "aligned_packages_load_bearing": ["torch.func"],
        "claim_path_tools": ["torch", "torch.func"],
        "M": {"probe": "[A,B,C] = (AB)C - A(BC)", "differentiated_probe": "norm of witness associator under H8->O algebra selector"},
        "C": {"rung_specific_constraint": "Cayley-Dickson table interpolation with alpha=0 H-embedded and alpha=1 O", "normalization": "unit basis witness"},
        "S_quotient_under_M": {"relation": "(AB)C ~ A(BC) iff differentiable associator norm is zero"},
        "values": {
            "H_max_associator_norm": h_norm,
            "O_max_associator_norm": o_norm,
            "witness_basis_indices_zero_based": witness,
            "witness_vector": [float(x) for x in o_vec.tolist()],
            "selector_norm_alpha_0": float(h_selector_norm.item()),
            "selector_norm_alpha_1": float(o_selector_norm.item()),
            "jacrev_alpha_0": float(h_jacrev.item()),
            "jacrev_alpha_0_5": float(mid_jacrev.item()),
            "jacrev_alpha_1": float(o_jacrev.item()),
        },
        "negative_control": {
            "force_H_embedding_alpha_0_erases_bracketing_gap": float(h_selector_norm.item()) <= TOL,
            "restore_O_alpha_1_recovers_bracketing_gap": float(o_selector_norm.item()) > TOL,
            "selector_sensitivity_nonzero": abs(float(mid_jacrev.item())) > TOL,
            "H_side_jacrev_flat": abs(float(h_jacrev.item())) <= TOL,
            "O_side_jacrev_nonzero": abs(float(o_jacrev.item())) > TOL,
            "flips": float(h_selector_norm.item()) <= TOL and float(o_selector_norm.item()) > TOL,
        },
        "torch_leg_independence": {
            "genuine_independent_check": True,
            "role": "differentiable sensitivity of the associator probe via torch.func.jacrev; not a solver proof and not the Julia authority path",
        },
        "all_pass": all_pass,
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(f"SCOUT_DONE H_norm={h_norm} O_norm={o_norm} witness={witness} jacrev_mid={float(mid_jacrev.item())} all_pass={all_pass}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
