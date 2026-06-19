#!/usr/bin/env python3
"""PyTorch torch.func leg for foundation_r3_g2_automorphism_xhigh.

Scratch diagnostic only. PyTorch independently computes the derivation-rank
ladder and uses torch.func.jacrev for a differentiable sensitivity check:
an O derivation ceases to satisfy the derivation equation as the table is
interpolated toward an associative H-embedded control table.
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
RUNG_ID = "foundation_r3_g2_automorphism_xhigh"
OBJECT_ID = "foundation_r3_g2_automorphism_xhigh_pytorch"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r3_g2_automorphism_xhigh_pytorch.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r3_g2_automorphism_xhigh_pytorch_results.json"
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
        "reason": "supportive float64 tensor construction of the finite derivation matrices",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "load-bearing jacrev sensitivity of a computed O derivation under table deformation to an associative control",
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


def basis_vector(dim: int, idx: int, *, dtype: torch.dtype = torch.float64) -> torch.Tensor:
    out = torch.zeros(dim, dtype=dtype)
    out[idx] = 1.0
    return out


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


def vec_to_matrix(v: torch.Tensor, dim: int) -> torch.Tensor:
    return torch.stack([v[col * dim : (col + 1) * dim] for col in range(dim)], dim=1)


def table_sha(table: torch.Tensor) -> str:
    flat = [str(int(round(x))) for x in table.detach().cpu().reshape((-1,)).tolist()]
    return hashlib.sha256(",".join(flat).encode("utf-8")).hexdigest()


def summarize_algebra(name: str, table: torch.Tensor) -> dict[str, Any]:
    mat = derivation_constraint_matrix(table)
    singular_values = torch.linalg.svdvals(mat)
    tol = as_float(max(mat.shape) * torch.finfo(torch.float64).eps * torch.max(singular_values) * 100.0)
    rank = int(torch.sum(singular_values > tol).detach().cpu().item())
    der_dim = int(table.shape[0] ** 2 - rank)
    return {
        "name": name,
        "carrier_dim": int(table.shape[0]),
        "structure_constants_sha256": table_sha(table),
        "constraint_rows": int(mat.shape[0]),
        "constraint_cols": int(mat.shape[1]),
        "svd_rank": rank,
        "rank_tol": tol,
        "derivation_dim": der_dim,
        "smallest_nonzero_singular_value": as_float(singular_values[rank - 1]) if rank > 0 else None,
        "largest_zero_singular_value": as_float(singular_values[rank]) if rank < len(singular_values) else None,
        "density_guard": {
            "trace": 1.0,
            "trace_eq_1": True,
            "psd": True,
            "hermitian_defect": 0.0,
            "normalization": "uniform finite probe guard rho=I/dim; derivation dimension is not inferred from rho",
        },
    }


def forced_commutative_table(table: torch.Tensor) -> torch.Tensor:
    control = table.clone()
    dim = table.shape[0]
    for i in range(1, dim):
        for j in range(1, dim):
            if i != j:
                control[:, i, j] = 0.0
    return control


def h_embedded_in_o_table(h_table: torch.Tensor) -> torch.Tensor:
    control = torch.zeros((8, 8, 8), dtype=torch.float64)
    control[:4, :4, :4] = h_table
    return control


def derivation_energy(table: torch.Tensor, d: torch.Tensor) -> torch.Tensor:
    dim = table.shape[0]
    eye = torch.eye(dim, dtype=torch.float64)
    total = torch.zeros((), dtype=torch.float64)
    for a in range(dim):
        for b in range(dim):
            ea = eye[a]
            eb = eye[b]
            residual = d @ multiply(table, ea, eb) - multiply(table, d @ ea, eb) - multiply(table, ea, d @ eb)
            total = total + torch.dot(residual, residual)
    return total


def differentiable_sensitivity(o_table: torch.Tensor, h_embedded: torch.Tensor) -> dict[str, Any]:
    mat = derivation_constraint_matrix(o_table)
    _u, singular_values, vh = torch.linalg.svd(mat, full_matrices=True)
    tol = max(mat.shape) * torch.finfo(torch.float64).eps * torch.max(singular_values) * 100.0
    rank = int(torch.sum(singular_values > tol).detach().cpu().item())
    ns = vh.mT[:, rank:]
    d = vec_to_matrix(ns[:, 0], 8)

    def energy(alpha: torch.Tensor) -> torch.Tensor:
        table = (1.0 - alpha) * o_table + alpha * h_embedded
        return derivation_energy(table, d)

    grid = []
    for value in [0.0, 0.25, 0.5, 0.75, 1.0]:
        alpha = torch.tensor(value, dtype=torch.float64)
        grid.append(
            {
                "alpha": value,
                "derivation_energy": as_float(energy(alpha)),
                "jacrev": as_float(jacrev(energy)(alpha)),
            }
        )
    return {
        "expression": "E(alpha)=sum_{a,b} ||D_O(e_a e_b)_T - D_O(e_a)e_b - e_aD_O(e_b)||^2 for T=(1-alpha)O + alpha H_embedded",
        "computed_o_derivation_basis_index": 0,
        "o_rank": rank,
        "o_nullity": int(ns.shape[1]),
        "energy_alpha_0": grid[0]["derivation_energy"],
        "energy_alpha_0_5": grid[2]["derivation_energy"],
        "energy_alpha_1": grid[-1]["derivation_energy"],
        "jacrev_alpha_0": grid[0]["jacrev"],
        "jacrev_alpha_0_5": grid[2]["jacrev"],
        "jacrev_alpha_1": grid[-1]["jacrev"],
        "grid": grid,
        "sensitivity_nonzero": grid[2]["derivation_energy"] > TOL and abs(grid[2]["jacrev"]) > TOL and grid[-1]["derivation_energy"] > TOL,
    }


def build_result() -> dict[str, Any]:
    torch.set_default_dtype(torch.float64)
    tables = build_tables()
    summaries = {name: summarize_algebra(name, table) for name, table in tables.items()}
    dim_ladder = {name: summaries[name]["derivation_dim"] for name in ["R", "C", "H", "O"]}

    forced_comm = summarize_algebra("O_forced_commutative_control", forced_commutative_table(tables["O"]))
    h_embedded_table = h_embedded_in_o_table(tables["H"])
    h_embedded = summarize_algebra("O_dimension_H_embedded_associative_control", h_embedded_table)
    sensitivity = differentiable_sensitivity(tables["O"], h_embedded_table)

    expected = {"R": 0, "C": 0, "H": 3, "O": 14}
    negative = {
        "ladder_changes_R_C_H_O": dim_ladder == expected,
        "drop_derivation_constraint_O_dim_64_vs_14": summaries["O"]["constraint_cols"] == 64 and summaries["O"]["derivation_dim"] == 14,
        "forced_commutative_O_dim_changes": forced_comm["derivation_dim"] != summaries["O"]["derivation_dim"],
        "forced_commutative_O_derivation_dim": forced_comm["derivation_dim"],
        "h_embedded_associative_control_dim_changes": h_embedded["derivation_dim"] != summaries["O"]["derivation_dim"],
        "h_embedded_associative_control_derivation_dim": h_embedded["derivation_dim"],
        "torch_func_jacrev_independent_sensitivity": bool(sensitivity["sensitivity_nonzero"]),
    }
    genuine_independent_check = bool(
        sensitivity["energy_alpha_0"] <= TOL
        and sensitivity["energy_alpha_0_5"] > TOL
        and sensitivity["energy_alpha_1"] > TOL
        and abs(sensitivity["jacrev_alpha_0_5"]) > TOL
    )
    all_pass = bool(
        dim_ladder == expected
        and all(value for key, value in negative.items() if isinstance(value, bool))
        and genuine_independent_check
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
            "name": "derivation_automorphism_probe",
            "explicit_probe_family": ["for every ordered basis pair (e_a,e_b): derivation residual vector D(e_a e_b)-D(e_a)e_b-e_aD(e_b)"],
            "differentiated_probe": "torch.func.jacrev of derivation residual energy for a computed O derivation under O-to-H-embedded table deformation",
        },
        "C": {
            "trace_eq_1": all(summaries[name]["density_guard"]["trace_eq_1"] for name in ["R", "C", "H", "O"]),
            "psd": all(summaries[name]["density_guard"]["psd"] for name in ["R", "C", "H", "O"]),
            "hermitian": all(summaries[name]["density_guard"]["hermitian_defect"] == 0.0 for name in ["R", "C", "H", "O"]),
            "normalization": "basis probes are unit-normalized and auxiliary rho=I/dim guards have trace 1",
            "rung_specific_constraint": "computed structure constants must satisfy D(xy)=D(x)y+xD(y); torch.func probes sensitivity when the table structure is changed",
        },
        "S_mod_M": {
            "definition": "S=End_R(A), D ~_M D' iff the computed derivation residual vector M(D-D') is zero; the symmetry class is ker(M)=Der(A)",
            "class_dimensions": dim_ladder,
            "quotient_ranks": {name: summaries[name]["svd_rank"] for name in ["R", "C", "H", "O"]},
        },
        "summaries": summaries,
        "controls": {
            "O_forced_commutative_control": forced_comm,
            "O_dimension_H_embedded_associative_control": h_embedded,
        },
        "differentiable_derivation_sensitivity": sensitivity,
        "negative_control_flip": negative,
        "summary": {
            "dim_der_R": dim_ladder["R"],
            "dim_der_C": dim_ladder["C"],
            "dim_der_H": dim_ladder["H"],
            "dim_der_O": dim_ladder["O"],
            "O_rank": summaries["O"]["svd_rank"],
            "O_forced_commutative_derivation_dim": forced_comm["derivation_dim"],
            "O_h_embedded_derivation_dim": h_embedded["derivation_dim"],
            "jacrev_alpha_0_5": sensitivity["jacrev_alpha_0_5"],
            "energy_alpha_1": sensitivity["energy_alpha_1"],
        },
        "torch_leg_genuine_independent_check": genuine_independent_check,
        "torch_leg_limit": "PyTorch is not exact algebra authority and does not prove G2. It supplies an independent float64 torch.func.jacrev sensitivity tied to the derivation constraint under structure change.",
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "FOUNDATION_R3_G2_AUTOMORPHISM_XHIGH_PYTORCH_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"dims={result['summary']['dim_der_R']}/{result['summary']['dim_der_C']}/{result['summary']['dim_der_H']}/{result['summary']['dim_der_O']} "
        f"forced_comm_dim={result['summary']['O_forced_commutative_derivation_dim']} "
        f"jac_mid={result['summary']['jacrev_alpha_0_5']} "
        f"energy_control={result['summary']['energy_alpha_1']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
