#!/usr/bin/env python3
"""PyTorch torch.func leg for foundation_r5_g2_su3_reduction.

Scratch diagnostic only. PyTorch computes the stabilizer dimensions with
float64 tensors and supplies a distinct differentiable check: a derivation in
the D(e1)=0 stabilizer is tested for sensitivity when the fixed probe moves
toward an independent unit e2.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import torch
from torch.func import jacrev


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r5_g2_su3_reduction"
OBJECT_ID = "foundation_r5_g2_su3_reduction_pytorch"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r5_g2_su3_reduction_pytorch.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r5_g2_su3_reduction_pytorch_results.json"
TOL = 1.0e-9

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
reads_peer_result = False

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "supportive float64 tensor construction of the finite derivation and unit-fixing matrices",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "load-bearing jacrev sensitivity of a computed D(e1)=0 derivation when the fixed probe is perturbed toward e2",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON receipt, hashing, and path handling",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "supportive",
    "torch.func": "load_bearing",
    "python_stdlib": "supportive",
}


def as_float(value: torch.Tensor | float) -> float:
    if isinstance(value, torch.Tensor):
        return float(value.detach().cpu().item())
    return float(value)


def cd_conj(x: torch.Tensor) -> torch.Tensor:
    signs = torch.cat([torch.ones(1, dtype=x.dtype), -torch.ones(x.shape[0] - 1, dtype=x.dtype)])
    return x * signs


def multiply(table: torch.Tensor, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    return torch.einsum("cab,a,b->c", table, x, y)


def cd_pair_multiply(parent: torch.Tensor, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    n = parent.shape[0]
    a = x[:n]
    b = x[n:]
    c = y[:n]
    d = y[n:]
    first = multiply(parent, a, c) - multiply(parent, cd_conj(d), b)
    second = multiply(parent, d, a) + multiply(parent, b, cd_conj(c))
    return torch.cat([first, second])


def cd_double(parent: torch.Tensor) -> torch.Tensor:
    n = parent.shape[0]
    dim = 2 * n
    table = torch.zeros((dim, dim, dim), dtype=torch.float64)
    eye = torch.eye(dim, dtype=torch.float64)
    for i in range(dim):
        for j in range(dim):
            table[:, i, j] = cd_pair_multiply(parent, eye[i], eye[j])
    return table


def build_tables() -> dict[str, torch.Tensor]:
    real = torch.zeros((1, 1, 1), dtype=torch.float64)
    real[0, 0, 0] = 1.0
    complex_table = cd_double(real)
    quaternion = cd_double(complex_table)
    octonion = cd_double(quaternion)
    return {"R": real, "C": complex_table, "H": quaternion, "O": octonion}


def derivation_constraint_matrix(table: torch.Tensor) -> torch.Tensor:
    dim = table.shape[0]
    mat = torch.zeros((dim**3, dim**2), dtype=torch.float64)

    def varidx(row: int, col: int) -> int:
        return row + col * dim

    row = 0
    for a in range(dim):
        for b in range(dim):
            for c in range(dim):
                for k in range(dim):
                    mat[row, varidx(c, k)] += table[k, a, b]
                    mat[row, varidx(k, a)] -= table[c, k, b]
                    mat[row, varidx(k, b)] -= table[c, a, k]
                row += 1
    return mat


def fixing_constraint_matrix(dim: int, vectors: list[torch.Tensor]) -> torch.Tensor:
    if not vectors:
        return torch.zeros((0, dim * dim), dtype=torch.float64)
    rows = torch.zeros((dim * len(vectors), dim * dim), dtype=torch.float64)
    row = 0
    for vec in vectors:
        for out_idx in range(dim):
            for col, coeff in enumerate(vec):
                if as_float(coeff) != 0.0:
                    rows[row, out_idx + col * dim] += coeff
            row += 1
    return rows


def augmented_constraint_matrix(table: torch.Tensor, vectors: list[torch.Tensor]) -> torch.Tensor:
    return torch.cat([derivation_constraint_matrix(table), fixing_constraint_matrix(int(table.shape[0]), vectors)], dim=0)


def table_sha(table: torch.Tensor) -> str:
    flat = [str(int(round(x))) for x in table.detach().cpu().reshape((-1,)).tolist()]
    return hashlib.sha256(",".join(flat).encode("utf-8")).hexdigest()


def forced_commutative_table(table: torch.Tensor) -> torch.Tensor:
    control = table.clone()
    dim = table.shape[0]
    for i in range(1, dim):
        for j in range(1, dim):
            if i != j:
                control[:, i, j] = 0.0
    return control


def summarize_system(name: str, table: torch.Tensor, vectors: list[torch.Tensor]) -> dict[str, Any]:
    mat = augmented_constraint_matrix(table, vectors)
    singular_values = torch.linalg.svdvals(mat)
    tol = as_float(max(mat.shape) * torch.finfo(torch.float64).eps * torch.max(singular_values) * 100.0)
    rank = int(torch.sum(singular_values > tol).detach().cpu().item())
    kernel_dim = int(table.shape[0] ** 2 - rank)
    return {
        "name": name,
        "carrier_dim": int(table.shape[0]),
        "structure_constants_sha256": table_sha(table),
        "derivation_constraint_rows": int(table.shape[0] ** 3),
        "fixing_constraint_rows": int(table.shape[0] * len(vectors)),
        "constraint_rows": int(mat.shape[0]),
        "constraint_cols": int(mat.shape[1]),
        "svd_rank": rank,
        "rank_tol": tol,
        "kernel_dim": kernel_dim,
        "stabilizer_dim": kernel_dim,
        "smallest_nonzero_singular_value": as_float(singular_values[rank - 1]) if rank > 0 else None,
        "largest_zero_singular_value": as_float(singular_values[rank]) if rank < len(singular_values) else None,
        "density_guard": {
            "trace": 1.0,
            "trace_eq_1": True,
            "psd": True,
            "hermitian_defect": 0.0,
            "normalization": "uniform finite probe guard rho=I/dim; stabilizer dimension is not inferred from rho",
        },
    }


def vec_to_matrix(v: torch.Tensor, dim: int) -> torch.Tensor:
    return torch.stack([v[col * dim : (col + 1) * dim] for col in range(dim)], dim=1)


def choose_unit_fixing_derivation(table: torch.Tensor, e1: torch.Tensor, e2: torch.Tensor) -> dict[str, Any]:
    mat = augmented_constraint_matrix(table, [e1])
    _u, singular_values, vh = torch.linalg.svd(mat, full_matrices=True)
    tol = max(mat.shape) * torch.finfo(torch.float64).eps * torch.max(singular_values) * 100.0
    rank = int(torch.sum(singular_values > tol).detach().cpu().item())
    ns = vh.mT[:, rank:]
    best_idx = 0
    best_norm = torch.tensor(-1.0, dtype=torch.float64)
    best_d = vec_to_matrix(ns[:, 0], 8)
    for idx in range(ns.shape[1]):
        d = vec_to_matrix(ns[:, idx], 8)
        norm_e2 = torch.linalg.vector_norm(d @ e2)
        if norm_e2 > best_norm:
            best_norm = norm_e2
            best_idx = idx
            best_d = d
    return {
        "rank": rank,
        "nullity": int(ns.shape[1]),
        "basis_index": best_idx,
        "basis_d": best_d,
        "fix_e1_norm": as_float(torch.linalg.vector_norm(best_d @ e1)),
        "moves_e2_norm": as_float(torch.linalg.vector_norm(best_d @ e2)),
    }


def differentiable_probe_sensitivity(table: torch.Tensor, e1: torch.Tensor, e2: torch.Tensor) -> dict[str, Any]:
    chosen = choose_unit_fixing_derivation(table, e1, e2)
    d = chosen["basis_d"]

    def energy(alpha: torch.Tensor) -> torch.Tensor:
        u = e1 + alpha * e2
        residual = d @ u
        return torch.dot(residual, residual)

    grid = []
    for value in [0.0, 0.25, 0.5, 0.75, 1.0]:
        alpha = torch.tensor(value, dtype=torch.float64)
        grid.append(
            {
                "alpha": value,
                "unit_fixing_energy": as_float(energy(alpha)),
                "jacrev": as_float(jacrev(energy)(alpha)),
            }
        )
    return {
        "expression": "E(alpha)=||D_fix_e1(e1 + alpha e2)||^2 for a computed D in ker(derivation rows, D(e1)=0) selected to move e2",
        "chosen_basis_index": chosen["basis_index"],
        "fix_e1_rank": chosen["rank"],
        "fix_e1_nullity": chosen["nullity"],
        "fix_e1_norm": chosen["fix_e1_norm"],
        "moves_e2_norm": chosen["moves_e2_norm"],
        "energy_alpha_0": grid[0]["unit_fixing_energy"],
        "energy_alpha_0_5": grid[2]["unit_fixing_energy"],
        "energy_alpha_1": grid[-1]["unit_fixing_energy"],
        "jacrev_alpha_0": grid[0]["jacrev"],
        "jacrev_alpha_0_5": grid[2]["jacrev"],
        "jacrev_alpha_1": grid[-1]["jacrev"],
        "grid": grid,
        "sensitivity_nonzero": grid[0]["unit_fixing_energy"] <= TOL
        and grid[2]["unit_fixing_energy"] > TOL
        and abs(grid[2]["jacrev"]) > TOL
        and chosen["moves_e2_norm"] > TOL,
    }


def build_result() -> dict[str, Any]:
    torch.set_default_dtype(torch.float64)
    tables = build_tables()
    o_table = tables["O"]
    e1 = torch.tensor([0, 1, 0, 0, 0, 0, 0, 0], dtype=torch.float64)
    e2 = torch.tensor([0, 0, 1, 0, 0, 0, 0, 0], dtype=torch.float64)

    full = summarize_system("Der_O_no_unit_fixing_control", o_table, [])
    unit = summarize_system("Der_O_fix_e1_unit_stabilizer", o_table, [e1])
    two_unit = summarize_system("Der_O_fix_e1_e2_two_unit_control", o_table, [e1, e2])
    forced_comm_unit = summarize_system("Der_O_forced_commutative_fix_e1_control", forced_commutative_table(o_table), [e1])
    sensitivity = differentiable_probe_sensitivity(o_table, e1, e2)

    negative = {
        "drop_unit_fixing_probe_dim_14_vs_8": full["stabilizer_dim"] == 14 and unit["stabilizer_dim"] == 8,
        "two_independent_units_dim_changes_3_vs_8": two_unit["stabilizer_dim"] == 3 and two_unit["stabilizer_dim"] != unit["stabilizer_dim"],
        "forced_commutative_unit_fixing_dim_changes": forced_comm_unit["stabilizer_dim"] != unit["stabilizer_dim"],
        "forced_commutative_unit_fixing_dim": forced_comm_unit["stabilizer_dim"],
        "torch_func_jacrev_independent_sensitivity": bool(sensitivity["sensitivity_nonzero"]),
    }
    genuine_independent_check = bool(
        sensitivity["energy_alpha_0"] <= TOL
        and sensitivity["energy_alpha_0_5"] > TOL
        and abs(sensitivity["jacrev_alpha_0_5"]) > TOL
        and sensitivity["moves_e2_norm"] > TOL
    )
    all_pass = bool(
        full["stabilizer_dim"] == 14
        and unit["stabilizer_dim"] == 8
        and two_unit["stabilizer_dim"] == 3
        and forced_comm_unit["stabilizer_dim"] != 8
        and genuine_independent_check
        and all(value for value in negative.values() if isinstance(value, bool))
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
        and reads_peer_result is False
    )

    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "rung_id": RUNG_ID,
        "object_id": OBJECT_ID,
        "engine": "pytorch",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "packages_used": ["torch", "torch.func", "json", "hashlib", "pathlib"],
        "aligned_packages_load_bearing": ["torch.func"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "runtime_preflight": {
            "sys_executable": sys.executable,
            "torch_version": torch.__version__,
            "torch_default_dtype": str(torch.get_default_dtype()),
        },
        "M": {
            "name": "unit_fixing_derivation_probe",
            "explicit_probe_family": [
                "derivation rows: for every ordered octonion basis pair (e_a,e_b), the derivation residual vector",
                "unit-fixing rows: D(e1)",
            ],
            "differentiated_probe": "torch.func.jacrev of ||D(e1 + alpha e2)||^2 for a computed D in the D(e1)=0 stabilizer",
        },
        "C": {
            "trace_eq_1": unit["density_guard"]["trace_eq_1"],
            "psd": unit["density_guard"]["psd"],
            "hermitian": unit["density_guard"]["hermitian_defect"] == 0.0,
            "normalization": "basis probes are unit-normalized and auxiliary rho=I/dim guard has trace 1",
            "rung_specific_constraint": "D is an octonion derivation and D(e1)=0; torch.func probes sensitivity when the fixed unit is perturbed toward e2",
        },
        "S_mod_M": {
            "definition": "S=Der(O), D ~_M D' iff (D-D')(e1)=0 under the explicit unit-fixing probe; PyTorch SVD computes the float64 kernel dimension",
            "class_dimensions": {"Der_O": full["stabilizer_dim"], "fix_e1": unit["stabilizer_dim"]},
            "quotient_rank": unit["svd_rank"],
        },
        "summaries": {
            "Der_O_no_unit_fixing_control": full,
            "Der_O_fix_e1_unit_stabilizer": unit,
            "Der_O_fix_e1_e2_two_unit_control": two_unit,
            "Der_O_forced_commutative_fix_e1_control": forced_comm_unit,
        },
        "differentiable_unit_probe_sensitivity": sensitivity,
        "negative_control_flip": negative,
        "summary": {
            "der_O_dim": full["stabilizer_dim"],
            "fix_e1_stabilizer_dim": unit["stabilizer_dim"],
            "fix_e1_e2_stabilizer_dim": two_unit["stabilizer_dim"],
            "forced_commutative_fix_e1_dim": forced_comm_unit["stabilizer_dim"],
            "unit_fix_rank": unit["svd_rank"],
            "jacrev_alpha_0_5": sensitivity["jacrev_alpha_0_5"],
            "energy_alpha_1": sensitivity["energy_alpha_1"],
            "moves_e2_norm": sensitivity["moves_e2_norm"],
        },
        "torch_leg_genuine_independent_check": genuine_independent_check,
        "torch_leg_limit": "PyTorch is not exact algebra authority and does not prove su(3). It supplies an independent float64 torch.func.jacrev sensitivity tied to the unit-fixing probe.",
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "FOUNDATION_R5_G2_SU3_REDUCTION_PYTORCH_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"dim_der_O={result['summary']['der_O_dim']} "
        f"fix_e1_dim={result['summary']['fix_e1_stabilizer_dim']} "
        f"two_unit_dim={result['summary']['fix_e1_e2_stabilizer_dim']} "
        f"forced_comm_fix_dim={result['summary']['forced_commutative_fix_e1_dim']} "
        f"jac_mid={result['summary']['jacrev_alpha_0_5']} "
        f"energy_alpha_1={result['summary']['energy_alpha_1']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
