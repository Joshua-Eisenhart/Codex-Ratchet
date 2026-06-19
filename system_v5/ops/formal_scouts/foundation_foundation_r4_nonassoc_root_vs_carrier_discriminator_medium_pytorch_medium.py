#!/usr/bin/env python3
"""PyTorch torch.func sensitivity leg for the R4 nonassoc root/carrier discriminator."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

import torch
from torch.func import jacrev


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r4_nonassoc_root_vs_carrier_discriminator_medium"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_medium_pytorch_medium.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_medium_pytorch_medium_results.json"
TOL = 1.0e-10


def multiply(table: torch.Tensor, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    return torch.einsum("kij,i,j->k", table, x, y)


def cd_conj(x: torch.Tensor) -> torch.Tensor:
    signs = torch.ones(x.shape[0], dtype=torch.float64)
    signs[1:] = -1.0
    return x * signs


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


def build_tables() -> dict[str, torch.Tensor]:
    r = torch.zeros((1, 1, 1), dtype=torch.float64)
    r[0, 0, 0] = 1.0
    c = cd_double(r)
    h = cd_double(c)
    o = cd_double(h)
    h8 = torch.zeros_like(o)
    h8[:4, :4, :4] = h
    return {"R": r, "C": c, "H": h, "O": o, "H8": h8}


def basis(dim: int, idx: int) -> torch.Tensor:
    out = torch.zeros(dim, dtype=torch.float64)
    out[idx] = 1.0
    return out


def commutator(table: torch.Tensor, i: int, j: int) -> torch.Tensor:
    return table[:, i, j] - table[:, j, i]


def anticommutator(table: torch.Tensor, i: int, j: int) -> torch.Tensor:
    return table[:, i, j] + table[:, j, i]


def commutator_norm(table: torch.Tensor, i: int, j: int) -> torch.Tensor:
    return torch.linalg.vector_norm(commutator(table, i, j))


def cl6_deficit_penalty(table: torch.Tensor, units: list[int]) -> torch.Tensor:
    terms = []
    for pos, left in enumerate(units):
        square = table[:, left, left]
        target = torch.zeros(table.shape[0], dtype=torch.float64)
        target[0] = -1.0
        terms.append(torch.linalg.vector_norm(square - target))
        for right in units[pos + 1 :]:
            terms.append(torch.linalg.vector_norm(anticommutator(table, left, right)))
    if len(units) < 7:
        terms.append(torch.tensor(float(7 - len(units)), dtype=torch.float64))
    return torch.stack(terms).sum()


def main() -> int:
    torch.set_default_dtype(torch.float64)
    tables = build_tables()
    h8 = tables["H8"]
    o = tables["O"]
    h_units = [1, 2, 3]
    o_units = [1, 2, 3, 4, 5, 6, 7]

    def selector_commutator_norm(alpha: torch.Tensor) -> torch.Tensor:
        table = h8 + alpha * (o - h8)
        return commutator_norm(table, 1, 2)

    def selector_cl6_penalty(alpha: torch.Tensor) -> torch.Tensor:
        table = h8 + alpha * (o - h8)
        return cl6_deficit_penalty(table, o_units)

    alpha_h = torch.tensor(0.0, dtype=torch.float64)
    alpha_mid = torch.tensor(0.5, dtype=torch.float64)
    alpha_o = torch.tensor(1.0, dtype=torch.float64)

    h_comm = selector_commutator_norm(alpha_h)
    o_comm = selector_commutator_norm(alpha_o)
    h_cl6_penalty = cl6_deficit_penalty(tables["H"], h_units)
    h8_cl6_penalty = selector_cl6_penalty(alpha_h)
    o_cl6_penalty = selector_cl6_penalty(alpha_o)
    comm_jac_h = jacrev(selector_commutator_norm)(alpha_h)
    cl6_jac_mid = jacrev(selector_cl6_penalty)(alpha_mid)
    cl6_jac_o = jacrev(selector_cl6_penalty)(alpha_o)

    all_pass = bool(
        float(h_comm.item()) > TOL
        and float(o_comm.item()) > TOL
        and abs(float(o_comm.item()) - float(h_comm.item())) <= TOL
        and float(h_cl6_penalty.item()) >= 4.0
        and float(h8_cl6_penalty.item()) > TOL
        and float(o_cl6_penalty.item()) <= TOL
        and abs(float(cl6_jac_mid.item())) > TOL
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
        "M": {
            "finite_probe_family": "differentiable probes: ||[e1,e2]|| and Cl6 seven-unit penalty under H8-to-O selector",
            "probe_indices_zero_based": [1, 2, 3, 4, 5, 6, 7],
        },
        "C": {
            "normalization": "basis units are torch float64 coordinate units",
            "rung_specific_constraint": "bare-root noncommutation remains nonzero while Cl6 seven-unit penalty flips from positive to zero",
        },
        "S_quotient_under_M": {
            "relation": "selector alpha=0 is H embedded in O coordinates; alpha=1 is O",
            "bare_noncommutation_probe": "H and O are indistinguishable by ||[e1,e2]||",
            "Cl6_probe": "H8 and O are distinguishable by seven-unit penalty",
        },
        "values": {
            "H_commutator_norm_e1_e2": float(h_comm.item()),
            "O_commutator_norm_e1_e2": float(o_comm.item()),
            "H_three_unit_cl6_deficit_penalty": float(h_cl6_penalty.item()),
            "H8_seven_unit_penalty_alpha_0": float(h8_cl6_penalty.item()),
            "O_seven_unit_penalty_alpha_1": float(o_cl6_penalty.item()),
            "jacrev_commutator_alpha_0": float(comm_jac_h.item()),
            "jacrev_cl6_penalty_alpha_0_5": float(cl6_jac_mid.item()),
            "jacrev_cl6_penalty_alpha_1": float(cl6_jac_o.item()),
        },
        "negative_control": {
            "bare_root_noncommutation_survives_H": float(h_comm.item()) > TOL,
            "force_Cl6_constraint_excludes_H8": float(h8_cl6_penalty.item()) > TOL,
            "restore_O_satisfies_Cl6_constraint": float(o_cl6_penalty.item()) <= TOL,
            "selector_sensitivity_nonzero": abs(float(cl6_jac_mid.item())) > TOL,
            "flips": float(h8_cl6_penalty.item()) > TOL and float(o_cl6_penalty.item()) <= TOL,
        },
        "torch_leg_independence": {
            "genuine_independent_check": True,
            "role": "torch.func.jacrev differentiates the H8-to-O Cl6 constraint penalty; this is a sensitivity check, not a solver mirror",
        },
        "all_pass": all_pass,
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(f"SCOUT_DONE H_comm={float(h_comm.item())} H8_cl6_penalty={float(h8_cl6_penalty.item())} O_cl6_penalty={float(o_cl6_penalty.item())} jac_mid={float(cl6_jac_mid.item())} all_pass={all_pass}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
