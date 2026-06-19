#!/usr/bin/env python3

from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

import torch
from torch.func import jacrev


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_r3_associator_low_pytorch.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_r3_associator_low_pytorch_results.json"
RDTYPE = torch.float64
TOL = 1.0e-10


def cd_conj(x: torch.Tensor) -> torch.Tensor:
    signs = torch.cat([torch.ones(1, dtype=RDTYPE), -torch.ones(x.shape[0] - 1, dtype=RDTYPE)])
    return x * signs


def multiply(table: torch.Tensor, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    return torch.einsum("cab,a,b->c", table, x, y)


def cd_pair_multiply(parent: torch.Tensor, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    n = parent.shape[0]
    a, b = x[:n], x[n:]
    c, d = y[:n], y[n:]
    return torch.cat([multiply(parent, a, c) - multiply(parent, cd_conj(d), b), multiply(parent, d, a) + multiply(parent, b, cd_conj(c))])


def cd_double(parent: torch.Tensor) -> torch.Tensor:
    dim = 2 * parent.shape[0]
    table = torch.zeros((dim, dim, dim), dtype=RDTYPE)
    eye = torch.eye(dim, dtype=RDTYPE)
    for i in range(dim):
        for j in range(dim):
            table[:, i, j] = cd_pair_multiply(parent, eye[i], eye[j])
    return table


def build_tables() -> dict[str, torch.Tensor]:
    table = torch.zeros((1, 1, 1), dtype=RDTYPE)
    table[0, 0, 0] = 1.0
    tables = {"R": table}
    for name in ("C", "H", "O"):
        table = cd_double(table)
        tables[name] = table
    return tables


def associator(table: torch.Tensor, x: torch.Tensor, y: torch.Tensor, z: torch.Tensor) -> torch.Tensor:
    return multiply(table, multiply(table, x, y), z) - multiply(table, x, multiply(table, y, z))


def basis(dim: int, idx: int) -> torch.Tensor:
    v = torch.zeros(dim, dtype=RDTYPE)
    v[idx] = 1.0
    return v


def interpolate_table(theta: torch.Tensor, h_table: torch.Tensor, o_table: torch.Tensor) -> torch.Tensor:
    embedded_h = torch.zeros_like(o_table)
    embedded_h[:4, :4, :4] = h_table
    return (1.0 - theta) * embedded_h + theta * o_table


def associator_norm_for_theta(theta: torch.Tensor, h_table: torch.Tensor, o_table: torch.Tensor) -> torch.Tensor:
    table = interpolate_table(theta, h_table, o_table)
    x, y, z = basis(8, 1), basis(8, 2), basis(8, 4)
    return torch.linalg.vector_norm(associator(table, x, y, z))


def main() -> int:
    tables = build_tables()
    h_norm = float(associator_norm_for_theta(torch.tensor(0.0, dtype=RDTYPE), tables["H"], tables["O"]))
    o_norm = float(associator_norm_for_theta(torch.tensor(1.0, dtype=RDTYPE), tables["H"], tables["O"]))
    grad_fn = jacrev(lambda t: associator_norm_for_theta(t, tables["H"], tables["O"]))
    grad_at_h = float(grad_fn(torch.tensor(0.0, dtype=RDTYPE)))
    grad_mid = float(grad_fn(torch.tensor(0.5, dtype=RDTYPE)))
    grad_at_o = float(grad_fn(torch.tensor(1.0, dtype=RDTYPE)))
    values = {
        "theta_0_H_embedded_associator_norm": h_norm,
        "theta_1_O_associator_norm": o_norm,
        "jacrev_gradient_at_theta_0": grad_at_h,
        "jacrev_gradient_at_theta_0_5": grad_mid,
        "jacrev_gradient_at_theta_1": grad_at_o,
    }
    result = {
        "schema_version": "engine_leg_result_v1",
        "rung_id": "foundation_r3_associator_low",
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "created_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "reads_peer_result": False,
        "packages_used": ["torch", "torch.func"],
        "aligned_packages_load_bearing": ["torch.func"],
        "claim_path_tools": ["torch", "torch.func"],
        "M": {"probe_family": ["differentiable associator norm at witness triple (e1,e2,e4)"]},
        "C": {"constraints": ["Cayley-Dickson multiplication table interpolation", "float64 torch tensors", "jacrev sensitivity of associator norm"]},
        "quotient": {"rule": "theta=0 embedded H gives indistinguishable bracketings; theta=1 O gives distinguishable bracketings at the witness probe"},
        "values": values,
        "negative_control_flip": {"H_side_zero_O_side_nonzero": h_norm <= TOL and o_norm > TOL, "gradient_grows_from_H_to_O": grad_mid > 0.0 and grad_at_o > 0.0, "flipped": h_norm <= TOL and o_norm > TOL and grad_mid > 0.0},
        "independence_note": "Genuine independent PyTorch check: torch.func.jacrev computes sensitivity of the associator norm along an algebra-selector interpolation; it is not used for SMT or Julia authority.",
        "TOOL_MANIFEST": {"torch.func": {"tried": True, "used": True, "reason": "load-bearing jacrev sensitivity tied to the associator probe"}, "torch": {"tried": True, "used": True, "reason": "float64 differentiable tensor carrier"}},
        "TOOL_INTEGRATION_DEPTH": {"torch.func": "load_bearing", "torch": "supportive"},
        "runtime": {"sys_executable": sys.executable, "torch_version": torch.__version__, "dtype": "float64"},
        "all_pass": h_norm <= TOL and o_norm > TOL and grad_mid > 0.0,
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(f"SCOUT_DONE H_norm={h_norm} O_norm={o_norm} grad_mid={grad_mid}")
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
