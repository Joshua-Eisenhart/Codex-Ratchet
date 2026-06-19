#!/usr/bin/env python3
"""PyTorch torch.func sensitivity leg for foundation_r4_nonassoc_root_vs_carrier_discriminator_low."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

import torch
from torch.func import jacrev


OBJECT_ID = "foundation_r4_nonassoc_root_vs_carrier_discriminator_low"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_r4_nonassoc_root_vs_carrier_discriminator_low_pytorch.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_r4_nonassoc_root_vs_carrier_discriminator_low_pytorch_results.json"
DTYPE = torch.float64


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cd_conj(x: torch.Tensor) -> torch.Tensor:
    if x.numel() == 1:
        return x
    return torch.cat([x[:1], -x[1:]])


def cd_mul(x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    n = x.numel()
    if n == 1:
        return x * y
    h = n // 2
    a, b = x[:h], x[h:]
    c, d = y[:h], y[h:]
    return torch.cat([cd_mul(a, c) - cd_mul(cd_conj(d), b), cd_mul(d, a) + cd_mul(b, cd_conj(c))])


def basis(dim: int, idx: int) -> torch.Tensor:
    return torch.eye(dim, dtype=DTYPE)[idx]


def table(dim: int) -> torch.Tensor:
    rows = []
    for i in range(dim):
        row = []
        for j in range(dim):
            row.append(cd_mul(basis(dim, i), basis(dim, j)))
        rows.append(torch.stack(row))
    return torch.stack(rows)


def unit_score_from_table(tbl: torch.Tensor) -> torch.Tensor:
    dim = tbl.shape[0]
    scores = []
    for i in range(1, dim):
        square_target = torch.zeros(dim, dtype=DTYPE)
        square_target[0] = -1.0
        square_res = torch.sum((tbl[i, i] - square_target) ** 2)
        pair_res = torch.zeros((), dtype=DTYPE)
        for j in range(1, dim):
            if i != j:
                pair_res = pair_res + torch.sum((tbl[i, j] + tbl[j, i]) ** 2)
        scores.append(1.0 / (1.0 + square_res + pair_res))
    return torch.sum(torch.stack(scores)) if scores else torch.zeros((), dtype=DTYPE)


def differentiable_gap(scale: torch.Tensor) -> torch.Tensor:
    h_tbl = table(4) * scale[0]
    o_tbl = table(8) * scale[1]
    return unit_score_from_table(o_tbl) - unit_score_from_table(h_tbl)


def main() -> int:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    baseline_scale = torch.tensor([1.0, 1.0], dtype=DTYPE)
    sensitivity_scale = torch.tensor([0.97, 1.03], dtype=DTYPE)
    gap = differentiable_gap(baseline_scale)
    sensitivity_gap = differentiable_gap(sensitivity_scale)
    jac = jacrev(differentiable_gap)(sensitivity_scale)
    h_score = unit_score_from_table(table(4)).item()
    o_score = unit_score_from_table(table(8)).item()
    result = {
        "schema_version": "three_engine_leg_result_v1",
        "object_id": OBJECT_ID,
        "sim_id": OBJECT_ID,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "reads_peer_result": False,
        "packages_used": ["torch", "torch.func", "json", "hashlib", "pathlib"],
        "aligned_packages_load_bearing": ["torch.func"],
        "claim_path_tools": ["torch.func"],
        "M": {"probes": ["differentiable relaxed anticommuting-unit score for H and O Cayley-Dickson tables"]},
        "C": {"rung_specific_constraint": "sensitivity of Cl6/>=7 unit gap under multiplication-table scale perturbation"},
        "summary": {
            "H_relaxed_unit_score": h_score,
            "O_relaxed_unit_score": o_score,
            "relaxed_gap_O_minus_H": gap.item(),
            "sensitivity_probe_scale_H": sensitivity_scale[0].item(),
            "sensitivity_probe_scale_O": sensitivity_scale[1].item(),
            "sensitivity_probe_gap_O_minus_H": sensitivity_gap.item(),
            "jacobian_d_gap_d_H_scale": jac[0].item(),
            "jacobian_d_gap_d_O_scale": jac[1].item(),
            "jacobian_l2_norm": torch.linalg.vector_norm(jac).item(),
            "genuine_independent_check": True,
            "independence_note": "torch.func.jacrev computes sensitivity of a smooth anticommutator-based gap; it is not the SMT SAT/UNSAT proof or a peer-result mirror.",
        },
        "all_pass": abs(h_score - 3.0) < 1.0e-9 and abs(o_score - 7.0) < 1.0e-9 and torch.linalg.vector_norm(jac).item() > 0.0,
        "source_sha256": sha256_file(SOURCE_PATH),
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"FOUNDATION_R4_NONASSOC_ROOT_VS_CARRIER_DISCRIMINATOR_LOW_PYTORCH_DONE {RESULT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
