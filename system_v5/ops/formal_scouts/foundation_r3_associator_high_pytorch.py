#!/usr/bin/env python3
"""PyTorch differentiable leg for foundation_r3_associator_high.

This is a genuine support check: it differentiates an associator squared norm
through a torch-native Cayley-Dickson algebra-selector interpolation. It does
not read Julia or JAX receipts.
"""

from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

import torch
from torch.func import jacrev


OBJECT_ID = "foundation_r3_associator_high"
ENGINE = "pytorch"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_r3_associator_high_pytorch.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_r3_associator_high_pytorch_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
DTYPE = torch.float64
TOL = 1.0e-10


def basis(dim: int, idx: int) -> torch.Tensor:
    return torch.eye(dim, dtype=DTYPE)[idx]


def cd_conj(x: torch.Tensor) -> torch.Tensor:
    signs = torch.cat([torch.ones(1, dtype=DTYPE), -torch.ones(x.shape[0] - 1, dtype=DTYPE)])
    return x * signs


def multiply(table: torch.Tensor, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    return torch.einsum("cab,a,b->c", table, x, y)


def cd_pair_multiply(parent: torch.Tensor, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    n = parent.shape[0]
    a, b = x[:n], x[n:]
    c, d = y[:n], y[n:]
    first = multiply(parent, a, c) - multiply(parent, cd_conj(d), b)
    second = multiply(parent, d, a) + multiply(parent, b, cd_conj(c))
    return torch.cat([first, second])


def cd_double(parent: torch.Tensor) -> torch.Tensor:
    dim = parent.shape[0] * 2
    rows = []
    for i in range(dim):
        cols = []
        for j in range(dim):
            cols.append(cd_pair_multiply(parent, basis(dim, i), basis(dim, j)))
        rows.append(torch.stack(cols, dim=1))
    return torch.stack(rows, dim=1)


def build_tables() -> dict[str, torch.Tensor]:
    r = torch.ones((1, 1, 1), dtype=DTYPE)
    c = cd_double(r)
    h = cd_double(c)
    o = cd_double(h)
    h_embedded = torch.zeros_like(o)
    h_embedded[:4, :4, :4] = h
    return {"H": h, "O": o, "H_embedded_in_O": h_embedded}


def associator(table: torch.Tensor, x: torch.Tensor, y: torch.Tensor, z: torch.Tensor) -> torch.Tensor:
    return multiply(table, multiply(table, x, y), z) - multiply(table, x, multiply(table, y, z))


def associator_max(table: torch.Tensor) -> tuple[float, list[int], torch.Tensor]:
    dim = table.shape[0]
    best_norm = torch.tensor(-1.0, dtype=DTYPE)
    best = [0, 0, 0]
    best_vec = torch.zeros(dim, dtype=DTYPE)
    for a in range(dim):
        for b in range(dim):
            for c in range(dim):
                vec = associator(table, basis(dim, a), basis(dim, b), basis(dim, c))
                nrm = torch.linalg.vector_norm(vec)
                if bool(nrm > best_norm):
                    best_norm = nrm
                    best = [a, b, c]
                    best_vec = vec
    return float(best_norm.detach().cpu().item()), best, best_vec


def build_result() -> dict[str, Any]:
    torch.set_default_dtype(DTYPE)
    tables = build_tables()
    h_norm, h_witness, h_vec = associator_max(tables["H"])
    o_norm, o_witness, o_vec = associator_max(tables["O"])
    x = basis(8, o_witness[0])
    y = basis(8, o_witness[1])
    z = basis(8, o_witness[2])

    def selector_assoc_sqnorm(theta: torch.Tensor) -> torch.Tensor:
        table = tables["H_embedded_in_O"] + theta * (tables["O"] - tables["H_embedded_in_O"])
        vec = associator(table, x, y, z)
        return torch.dot(vec, vec)

    theta_h = torch.tensor(0.0, dtype=DTYPE)
    theta_mid = torch.tensor(0.5, dtype=DTYPE)
    theta_o = torch.tensor(1.0, dtype=DTYPE)
    value_h = selector_assoc_sqnorm(theta_h)
    value_mid = selector_assoc_sqnorm(theta_mid)
    value_o = selector_assoc_sqnorm(theta_o)
    jac_h = jacrev(selector_assoc_sqnorm)(theta_h)
    jac_mid = jacrev(selector_assoc_sqnorm)(theta_mid)
    jac_o = jacrev(selector_assoc_sqnorm)(theta_o)

    genuine_independent_check = bool(
        abs(float(value_h.detach().cpu().item())) <= TOL
        and float(value_mid.detach().cpu().item()) > TOL
        and float(value_o.detach().cpu().item()) > float(value_mid.detach().cpu().item())
        and abs(float(jac_h.detach().cpu().item())) <= TOL
        and float(jac_mid.detach().cpu().item()) > TOL
        and float(jac_o.detach().cpu().item()) > TOL
    )
    all_pass = bool(
        h_norm <= TOL
        and o_norm > TOL
        and genuine_independent_check
        and CLASSIFICATION == "scratch_diagnostic"
        and PROMOTION_ALLOWED is False
        and FORMAL_ADMISSION_ALLOWED is False
        and READS_PEER_RESULT is False
    )

    return {
        "object_id": OBJECT_ID,
        "engine": ENGINE,
        "created_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "sys_executable": sys.executable,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "torch_version": torch.__version__,
        "torch_dtype": str(torch.get_default_dtype()),
        "M_probe_family": {
            "id": "torch_basis_triple_associator_squared_norm",
            "observable": "||[A,B,C]||^2 along H-embedded-to-O algebra selector",
            "witness_triple": [f"e{i}" for i in o_witness],
        },
        "C_constraints": {
            "domain": "finite Cayley-Dickson structure constants in torch.float64",
            "rung_specific": "differentiable selector scales the O structure added beyond embedded H",
        },
        "quotient": {
            "definition": "(AB)C ~ A(BC) iff torch associator squared norm is zero",
            "H_quotient_class_count": 1 if h_norm <= TOL else 2,
            "O_quotient_class_count": 2 if o_norm > TOL else 1,
        },
        "values": {
            "H": {"associator_max_norm": h_norm, "witness": {"basis_indices_zero_based": h_witness, "components": [float(v) for v in h_vec.detach().cpu().tolist()]}},
            "O": {"associator_max_norm": o_norm, "witness": {"basis_indices_zero_based": o_witness, "basis_labels": [f"e{i}" for i in o_witness], "components": [float(v) for v in o_vec.detach().cpu().tolist()]}},
        },
        "differentiable_check": {
            "kind": "torch.func.jacrev_algebra_selector_associator_sqnorm",
            "theta_H": float(theta_h.detach().cpu().item()),
            "theta_mid": float(theta_mid.detach().cpu().item()),
            "theta_O": float(theta_o.detach().cpu().item()),
            "value_H": float(value_h.detach().cpu().item()),
            "value_mid": float(value_mid.detach().cpu().item()),
            "value_O": float(value_o.detach().cpu().item()),
            "jacrev_H": float(jac_h.detach().cpu().item()),
            "jacrev_mid": float(jac_mid.detach().cpu().item()),
            "jacrev_O": float(jac_o.detach().cpu().item()),
            "genuine_independent_check": genuine_independent_check,
            "honesty_note": "This is not SMT or Julia authority; it is the requested differentiable sensitivity leg.",
        },
        "negative_control": {
            "H_to_O_structure_flip": {"pass": h_norm <= TOL and o_norm > TOL, "H_associator_max_norm": h_norm, "O_associator_max_norm": o_norm},
            "selector_erasure_flip": {"pass": genuine_independent_check, "theta_0_value": float(value_h.detach().cpu().item()), "theta_1_value": float(value_o.detach().cpu().item())},
        },
        "packages_used": ["torch", "torch.func", "json"],
        "aligned_packages_load_bearing": ["torch.func"],
        "TOOL_MANIFEST": {
            "torch": {"tried": True, "used": True, "reason": "supportive float64 tensor algebra substrate"},
            "torch.func": {"tried": True, "used": True, "reason": "load-bearing jacrev sensitivity through the associator observable"},
        },
        "TOOL_INTEGRATION_DEPTH": {"torch": "supportive", "torch.func": "load_bearing"},
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "SCOUT_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"H_assoc={result['values']['H']['associator_max_norm']} "
        f"O_assoc={result['values']['O']['associator_max_norm']} "
        f"jac_H={result['differentiable_check']['jacrev_H']} "
        f"jac_O={result['differentiable_check']['jacrev_O']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
