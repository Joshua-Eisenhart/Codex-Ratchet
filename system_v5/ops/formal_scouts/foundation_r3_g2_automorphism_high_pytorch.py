#!/usr/bin/env python3
"""PyTorch differentiable support leg for foundation_r3_g2_automorphism_high."""

from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

import torch
from torch.func import jacrev


OBJECT_ID = "foundation_r3_g2_automorphism_high"
ENGINE = "pytorch"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_r3_g2_automorphism_high_pytorch.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_r3_g2_automorphism_high_pytorch_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
DTYPE = torch.float64
TOL = 1.0e-8


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
    table = torch.zeros((dim, dim, dim), dtype=DTYPE)
    for i in range(dim):
        for j in range(dim):
            table[:, i, j] = cd_pair_multiply(parent, basis(dim, i), basis(dim, j))
    return table


def build_tables() -> dict[str, torch.Tensor]:
    r = torch.ones((1, 1, 1), dtype=DTYPE)
    c = cd_double(r)
    h = cd_double(c)
    o = cd_double(h)
    h_embedded = torch.zeros_like(o)
    h_embedded[:4, :4, :4] = h
    return {
        "R": r,
        "C": c,
        "H": h,
        "O": o,
        "O_commutative_projection_control": 0.5 * (o + o.transpose(1, 2)),
        "O_to_H_embedded_erasure_control": h_embedded,
    }


def derivation_matrix(table: torch.Tensor) -> torch.Tensor:
    n = table.shape[0]
    rows = []
    for k in range(n):
        for a in range(n):
            for b in range(n):
                coeffs = []
                for s in range(n):
                    for r in range(n):
                        coeff = table.new_tensor(0.0)
                        if r == k:
                            coeff = coeff + table[s, a, b]
                        if s == a:
                            coeff = coeff - table[k, r, b]
                        if s == b:
                            coeff = coeff - table[k, a, r]
                        coeffs.append(coeff)
                rows.append(torch.stack(coeffs))
    return torch.stack(rows)


def analyze(name: str, table: torch.Tensor) -> dict[str, Any]:
    matrix = derivation_matrix(table)
    rank = int(torch.linalg.matrix_rank(matrix, tol=TOL).detach().cpu().item())
    variable_count = int(table.shape[0] ** 2)
    svals = torch.linalg.svdvals(matrix)
    return {
        "name": name,
        "algebra_dim": int(table.shape[0]),
        "probe_count": int(matrix.shape[0]),
        "variable_count": variable_count,
        "constraint_rank": rank,
        "derivation_dimension": variable_count - rank,
        "smallest_singular_values": [float(x) for x in svals[-5:].detach().cpu().tolist()],
    }


def nonzero_o_derivation_vector(o_table: torch.Tensor, control_table: torch.Tensor) -> torch.Tensor:
    matrix = derivation_matrix(o_table)
    control_matrix = derivation_matrix(control_table)
    _, _, vh = torch.linalg.svd(matrix, full_matrices=True)
    nullity = int(o_table.shape[0] ** 2 - torch.linalg.matrix_rank(matrix, tol=TOL).detach().cpu().item())
    candidates = vh[-nullity:, :]
    residuals = torch.linalg.vector_norm(control_matrix @ candidates.T, dim=0)
    candidate = candidates[int(torch.argmax(residuals).detach().cpu().item()), :]
    return candidate / torch.linalg.vector_norm(candidate)


def build_result() -> dict[str, Any]:
    torch.set_default_dtype(DTYPE)
    tables = build_tables()
    values = {name: analyze(name, table) for name, table in tables.items()}
    ladder = {name: values[name]["derivation_dimension"] for name in ("R", "C", "H", "O")}
    expected_ladder = {"R": 0, "C": 0, "H": 3, "O": 14}
    control_dim = values["O_commutative_projection_control"]["derivation_dimension"]
    d_vec = nonzero_o_derivation_vector(tables["O"], tables["O_to_H_embedded_erasure_control"]).detach()

    def residual_sqnorm(theta: torch.Tensor) -> torch.Tensor:
        table = tables["O"] + theta * (tables["O_to_H_embedded_erasure_control"] - tables["O"])
        matrix = derivation_matrix(table)
        residual = matrix @ d_vec
        return torch.dot(residual, residual)

    theta_0 = torch.tensor(0.0, dtype=DTYPE)
    theta_mid = torch.tensor(0.5, dtype=DTYPE)
    theta_1 = torch.tensor(1.0, dtype=DTYPE)
    value_0 = residual_sqnorm(theta_0)
    value_mid = residual_sqnorm(theta_mid)
    value_1 = residual_sqnorm(theta_1)
    jac_0 = jacrev(residual_sqnorm)(theta_0)
    jac_mid = jacrev(residual_sqnorm)(theta_mid)
    jac_1 = jacrev(residual_sqnorm)(theta_1)
    genuine_independent_check = bool(
        abs(float(value_0.detach().cpu().item())) <= TOL
        and float(value_mid.detach().cpu().item()) > TOL
        and float(value_1.detach().cpu().item()) > float(value_mid.detach().cpu().item())
        and float(jac_mid.detach().cpu().item()) > TOL
        and float(jac_1.detach().cpu().item()) > TOL
    )
    all_pass = bool(
        ladder == expected_ladder
        and control_dim != ladder["O"]
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
            "id": "torch_derivation_defect_residual",
            "observable": "||M_table(D)||^2 for a torch-computed O derivation vector under table perturbation",
            "finite_family": {"O_basis_pair_coordinate_probes": 512},
        },
        "C_constraints": {
            "trace": "trace-one finite probe weighting recorded at envelope level",
            "PSD": "squared residual is a PSD Gram norm of derivation-defect probes",
            "Hermiticity": "real coordinate residual observables are self-adjoint",
            "normalization": "torch.float64 Cayley-Dickson basis normalization",
            "rung_specific": "D must remain a derivation after the multiplication table is perturbed",
        },
        "quotient": {
            "S": "End_R(A)",
            "equivalence": "torch residual zero means D remains in the derivation kernel for the chosen table",
            "class_dimensions": ladder,
        },
        "values": values,
        "differentiable_check": {
            "kind": "torch.func.jacrev_derivation_residual_under_commutative_projection",
            "theta_O": float(theta_0.detach().cpu().item()),
            "theta_mid": float(theta_mid.detach().cpu().item()),
            "theta_erased_H_control": float(theta_1.detach().cpu().item()),
            "value_O": float(value_0.detach().cpu().item()),
            "value_mid": float(value_mid.detach().cpu().item()),
            "value_erased_H_control": float(value_1.detach().cpu().item()),
            "jacrev_O": float(jac_0.detach().cpu().item()),
            "jacrev_mid": float(jac_mid.detach().cpu().item()),
            "jacrev_erased_H_control": float(jac_1.detach().cpu().item()),
            "genuine_independent_check": genuine_independent_check,
            "honesty_note": "This is not the SMT proof and not Julia authority; it is a torch.func sensitivity check that an O derivation is broken by erasing O multiplication outside the H subalgebra.",
        },
        "negative_control": {
            "division_algebra_ladder_flip": {"pass": ladder == expected_ladder, "dimensions": ladder},
            "force_commutativity_flip": {
                "pass": control_dim != ladder["O"],
                "O_derivation_dimension": ladder["O"],
                "commutative_projection_derivation_dimension": control_dim,
            },
            "residual_sensitivity_flip": {
                "pass": genuine_independent_check,
                "O_residual_sqnorm": float(value_0.detach().cpu().item()),
                "erased_H_control_residual_sqnorm": float(value_1.detach().cpu().item()),
            },
        },
        "packages_used": ["torch", "torch.func", "json"],
        "aligned_packages_load_bearing": ["torch.func"],
        "TOOL_MANIFEST": {
            "torch": {"tried": True, "used": True, "reason": "supportive float64 tensor construction of derivation matrices"},
            "torch.func": {"tried": True, "used": True, "reason": "load-bearing jacrev sensitivity of the derivation residual under a structural control"},
        },
        "TOOL_INTEGRATION_DEPTH": {"torch": "supportive", "torch.func": "load_bearing"},
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    dims = result["quotient"]["class_dimensions"]
    diff = result["differentiable_check"]
    print(
        "SCOUT_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"dims_R_C_H_O={dims['R']}/{dims['C']}/{dims['H']}/{dims['O']} "
        f"value_O={diff['value_O']} value_control={diff['value_erased_H_control']} "
        f"jac_mid={diff['jacrev_mid']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
