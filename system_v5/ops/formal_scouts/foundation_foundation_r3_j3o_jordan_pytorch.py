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
RUNG_ID = "foundation_r3_j3o_jordan"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r3_j3o_jordan_pytorch.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r3_j3o_jordan_pytorch_results.json"
RDTYPE = torch.float64
TOL = 1.0e-10
OFFDIAG_PAIRS = [(0, 1), (0, 2), (1, 2)]


def cd_conj(x: torch.Tensor) -> torch.Tensor:
    signs = torch.cat([torch.ones(1, dtype=RDTYPE), -torch.ones(x.shape[0] - 1, dtype=RDTYPE)])
    return x * signs


def multiply(table: torch.Tensor, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    return torch.einsum("cab,a,b->c", table, x, y)


def cd_pair_multiply(parent: torch.Tensor, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    n = parent.shape[0]
    a, b = x[:n], x[n:]
    c, d = y[:n], y[n:]
    return torch.cat(
        [
            multiply(parent, a, c) - multiply(parent, cd_conj(d), b),
            multiply(parent, d, a) + multiply(parent, b, cd_conj(c)),
        ]
    )


def cd_double(parent: torch.Tensor) -> torch.Tensor:
    dim = 2 * parent.shape[0]
    table = torch.zeros((dim, dim, dim), dtype=RDTYPE)
    eye = torch.eye(dim, dtype=RDTYPE)
    for i in range(dim):
        for j in range(dim):
            table[:, i, j] = cd_pair_multiply(parent, eye[i], eye[j])
    return table


def octonion_table() -> torch.Tensor:
    table = torch.ones((1, 1, 1), dtype=RDTYPE)
    for _ in range(3):
        table = cd_double(table)
    return table


def j3_zero() -> torch.Tensor:
    return torch.zeros((3, 3, 8), dtype=RDTYPE)


def j3_from_parts(diag: list[float], offdiag: list[list[float]]) -> torch.Tensor:
    matrix = j3_zero()
    for i, d in enumerate(diag):
        matrix[i, i, 0] = float(d)
    for (i, j), values in zip(OFFDIAG_PAIRS, offdiag, strict=True):
        vector = torch.tensor(values, dtype=RDTYPE)
        matrix[i, j, :] = vector
        matrix[j, i, :] = cd_conj(vector)
    return matrix


def j3_probe_a() -> torch.Tensor:
    return j3_from_parts(
        [2.0, -1.0, 0.0],
        [
            [0.0, 1.0, 2.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
        ],
    )


def j3_probe_b() -> torch.Tensor:
    return j3_from_parts(
        [0.0, 1.0, -2.0],
        [
            [0.0, 0.0, 1.0, 0.0, 0.0, -1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
            [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
        ],
    )


def j3_matmul(table: torch.Tensor, a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    out = j3_zero()
    for i in range(3):
        for k in range(3):
            acc = torch.zeros(8, dtype=RDTYPE)
            for j in range(3):
                acc = acc + multiply(table, a[i, j], b[j, k])
            out[i, k, :] = acc
    return out


def jordan(table: torch.Tensor, a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    return 0.5 * (j3_matmul(table, a, b) + j3_matmul(table, b, a))


def raw_product(table: torch.Tensor, a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    return j3_matmul(table, a, b)


def deformed_product(theta: torch.Tensor, table: torch.Tensor, a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    return (1.0 - theta) * jordan(table, a, b) + theta * raw_product(table, a, b)


def deformed_identity_residual(theta: torch.Tensor, table: torch.Tensor, a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    aa = deformed_product(theta, table, a, a)
    ab = deformed_product(theta, table, a, b)
    return deformed_product(theta, table, ab, aa) - deformed_product(theta, table, a, deformed_product(theta, table, b, aa))


def residual_squared(theta: torch.Tensor, table: torch.Tensor, a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    residual = deformed_identity_residual(theta, table, a, b)
    return torch.sum(residual * residual)


def main() -> int:
    table = octonion_table()
    a = j3_probe_a()
    b = j3_probe_b()
    scalar = lambda theta: residual_squared(theta, table, a, b)
    grad_fn = jacrev(scalar)

    theta_zero = torch.tensor(0.0, dtype=RDTYPE)
    theta_half = torch.tensor(0.5, dtype=RDTYPE)
    theta_one = torch.tensor(1.0, dtype=RDTYPE)
    jordan_sq = float(scalar(theta_zero))
    half_sq = float(scalar(theta_half))
    raw_sq = float(scalar(theta_one))
    grad_zero = float(grad_fn(theta_zero))
    grad_half = float(grad_fn(theta_half))
    grad_one = float(grad_fn(theta_one))

    values = {
        "theta_0_jordan_identity_residual_squared": jordan_sq,
        "theta_0_5_deformed_identity_residual_squared": half_sq,
        "theta_1_raw_identity_residual_squared": raw_sq,
        "jacrev_gradient_at_theta_0": grad_zero,
        "jacrev_gradient_at_theta_0_5": grad_half,
        "jacrev_gradient_at_theta_1": grad_one,
    }
    negative = {
        "jordan_to_raw_residual_flip": jordan_sq <= TOL and raw_sq > TOL,
        "jacrev_mid_sensitivity_nonzero": abs(grad_half) > TOL,
    }
    negative["flipped"] = all(negative.values())
    result = {
        "schema_version": "engine_leg_result_v1",
        "rebuild_version": "v2",
        "rung_id": RUNG_ID,
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
        "M": {
            "name": "differentiable Jordan-product deformation probe",
            "finite_probe_family": [
                "same explicit A,B Hermitian J3(O) probes",
                "theta=0 Jordan product, theta=1 raw non-Jordan product",
                "torch.func.jacrev sensitivity of the identity residual squared",
            ],
        },
        "C": {
            "constraints": [
                "float64 torch tensors",
                "fixed Hermitian A,B probes",
                "rung-specific product deformation between Jordan and non-Jordan products",
                "genuine jacrev derivative of a computed residual, not a peer-result mirror",
            ]
        },
        "quotient": {
            "symbol": "S/~_M",
            "rule": "the torch check separates the Jordan and raw-product classes by differentiable sensitivity of the identity residual",
        },
        "values": values,
        "negative_control_flip": negative,
        "independence_note": "Genuine independent PyTorch check: torch.func.jacrev computes sensitivity of the J3(O) Jordan-identity residual under a product-deformation parameter. It does not read Julia/JAX results and it does not provide the SMT proof.",
        "claim_limit": "PyTorch supplies only the differentiable sensitivity leg. It is not the authoritative J3(O) arithmetic leg and not the z3/cvc5 structural proof.",
        "TOOL_MANIFEST": {
            "torch.func": {"tried": True, "used": True, "reason": "load-bearing jacrev sensitivity tied to the Jordan-vs-raw product flip"},
            "torch": {"tried": True, "used": True, "reason": "float64 differentiable tensor carrier"},
        },
        "TOOL_INTEGRATION_DEPTH": {"torch.func": "load_bearing", "torch": "supportive"},
        "runtime": {"sys_executable": sys.executable, "torch_version": torch.__version__, "dtype": "float64"},
        "all_pass": bool(jordan_sq <= TOL and raw_sq > TOL and abs(grad_half) > TOL),
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "SCOUT_DONE "
        f"rung={RUNG_ID} "
        f"jordan_sq={jordan_sq} raw_sq={raw_sq} "
        f"grad_mid={grad_half} negative_flip={negative['flipped']}"
    )
    print(f"wrote: {RESULT_PATH}")
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
