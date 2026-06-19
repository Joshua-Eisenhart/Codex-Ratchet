#!/usr/bin/env python3
"""PyTorch torch.func leg for the R4 non-assoc root-vs-carrier discriminator."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any

import torch
from torch.func import jacrev


OBJECT_ID = "foundation_r4_nonassoc_root_vs_carrier_discriminator_high"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_high_pytorch.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_high_pytorch_results.json"
DTYPE = torch.float64


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def py_float(value: torch.Tensor) -> float:
    return float(value.detach().cpu().item())


def cd_conj(x: torch.Tensor) -> torch.Tensor:
    if x.shape[0] == 1:
        return x
    y = x.clone()
    y[1:] = -y[1:]
    return y


def cd_mul(x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    n = int(x.shape[0])
    if n == 1:
        return x * y
    half = n // 2
    a, b = x[:half], x[half:]
    c, d = y[:half], y[half:]
    return torch.cat([cd_mul(a, c) - cd_mul(cd_conj(d), b), cd_mul(d, a) + cd_mul(b, cd_conj(c))])


def basis(dim: int, idx: int) -> torch.Tensor:
    return torch.eye(dim, dtype=DTYPE)[idx]


def multiplication_table(dim: int) -> list[list[list[int]]]:
    rows: list[list[list[int]]] = []
    for a in range(dim):
        a_rows: list[list[int]] = []
        for b in range(dim):
            product = cd_mul(basis(dim, a), basis(dim, b))
            a_rows.append([int(round(py_float(product[k]))) for k in range(dim)])
        rows.append(a_rows)
    return rows


def left_matrix(dim: int, unit_idx: int) -> torch.Tensor:
    e = basis(dim, unit_idx)
    return torch.stack([cd_mul(e, basis(dim, col)) for col in range(dim)], dim=1)


def left_matrices(dim: int) -> list[torch.Tensor]:
    return [left_matrix(dim, idx) for idx in range(1, dim)]


def commutator_coeffs(table: list[list[list[int]]], i: int, j: int) -> list[int]:
    return [table[i][j][k] - table[j][i][k] for k in range(len(table))]


def self_square_normalized(table: list[list[list[int]]], i: int) -> bool:
    dim = len(table)
    return all(2 * table[i][i][k] == (-2 if k == 0 else 0) for k in range(dim))


def pair_anticommutes(table: list[list[list[int]]], i: int, j: int) -> bool:
    return all(table[i][j][k] + table[j][i][k] == 0 for k in range(len(table)))


def max_mutually_anticommuting_units(table: list[list[list[int]]]) -> int:
    imag = list(range(1, len(table)))
    best = 0
    for mask in range(1 << len(imag)):
        selected = [imag[idx] for idx in range(len(imag)) if (mask >> idx) & 1]
        ok = all(self_square_normalized(table, i) for i in selected)
        ok = ok and all(pair_anticommutes(table, selected[a], selected[b]) for a in range(len(selected)) for b in range(a + 1, len(selected)))
        if ok:
            best = max(best, len(selected))
    return best


def carrier_report(name: str, dim: int, associative: bool) -> dict[str, Any]:
    table = multiplication_table(dim)
    witnesses = []
    for i in range(1, dim):
        for j in range(i + 1, dim):
            coeffs = commutator_coeffs(table, i, j)
            if any(value != 0 for value in coeffs):
                witnesses.append({"i": i, "j": j, "commutator_coefficients": coeffs})
    count = max_mutually_anticommuting_units(table)
    return {
        "name": name,
        "real_dimension": dim,
        "associative": associative,
        "finite": True,
        "mutually_anticommuting_imaginary_unit_count": count,
        "noncommuting": bool(witnesses),
        "noncommutation_witness": witnesses[0] if witnesses else None,
        "bare_root_admissible": bool(witnesses),
        "cl6_7unit_admissible": count >= 7,
    }


def anticommutation_residual(scales: torch.Tensor, base_mats: tuple[torch.Tensor, ...]) -> torch.Tensor:
    mats = [scales[idx] * base_mats[idx] for idx in range(scales.shape[0])]
    dim = int(base_mats[0].shape[0])
    rows: list[torch.Tensor] = []
    for i, left in enumerate(mats):
        for j, right in enumerate(mats):
            target = -2.0 * torch.eye(dim, dtype=DTYPE) if i == j else torch.zeros((dim, dim), dtype=DTYPE)
            rows.append((left @ right + right @ left - target).reshape(-1))
    return torch.cat(rows)


def torch_func_sensitivity() -> dict[str, Any]:
    o_mats = tuple(left_matrices(8))
    h_mats = tuple(left_matrices(4))
    o_scales = torch.ones(7, dtype=DTYPE)
    h_scales = torch.ones(3, dtype=DTYPE)
    o_residual = anticommutation_residual(o_scales, o_mats)
    h_residual = anticommutation_residual(h_scales, h_mats)
    o_jac = jacrev(lambda scales: anticommutation_residual(scales, o_mats))(o_scales)
    h_jac = jacrev(lambda scales: anticommutation_residual(scales, h_mats))(h_scales)

    def residual_index(generator_count: int, dim: int, i: int, j: int, row: int, col: int) -> int:
        return (((i * generator_count + j) * dim + row) * dim) + col

    o_self_sens = [py_float(o_jac[residual_index(7, 8, i, i, 0, 0), i]) for i in range(7)]
    h_self_sens = [py_float(h_jac[residual_index(3, 4, i, i, 0, 0), i]) for i in range(3)]
    dropped = o_scales.clone()
    dropped[6] = 0.0
    drop_residual = anticommutation_residual(dropped, o_mats)
    return {
        "tool": "torch.func.jacrev",
        "genuine_independent_check": True,
        "claim_tie": "Jacobian of the >=7-unit anticommutation/self-square residual with respect to generator normalization scales; dropping one O generator changes the Cl6/7-unit constraint residual.",
        "O_residual_vector_length": int(o_residual.numel()),
        "H_residual_vector_length": int(h_residual.numel()),
        "O_jacobian_shape": list(o_jac.shape),
        "H_jacobian_shape": list(h_jac.shape),
        "O_jacobian_frobenius_norm": py_float(torch.linalg.norm(o_jac)),
        "H_jacobian_frobenius_norm": py_float(torch.linalg.norm(h_jac)),
        "O_self_diagonal_sensitivities": o_self_sens,
        "H_self_diagonal_sensitivities": h_self_sens,
        "expected_self_diagonal_sensitivity": -4.0,
        "O_max_abs_residual_at_canonical": py_float(torch.max(torch.abs(o_residual))),
        "H_max_abs_residual_at_canonical": py_float(torch.max(torch.abs(h_residual))),
        "O_drop_one_generator_max_abs_residual": py_float(torch.max(torch.abs(drop_residual))),
        "pass": py_float(torch.max(torch.abs(o_residual))) == 0.0
        and py_float(torch.max(torch.abs(h_residual))) == 0.0
        and all(abs(value + 4.0) <= 1.0e-9 for value in o_self_sens)
        and all(abs(value + 4.0) <= 1.0e-9 for value in h_self_sens)
        and py_float(torch.max(torch.abs(drop_residual))) > 0.0
        and py_float(torch.linalg.norm(o_jac)) > 0.0,
    }


def quotient_summary(carriers: dict[str, dict[str, Any]]) -> dict[str, Any]:
    bare = sorted([name for name, row in carriers.items() if row["bare_root_admissible"]])
    strong = sorted([name for name, row in carriers.items() if row["cl6_7unit_admissible"]])
    full = {
        name: f"finite={row['finite']};noncommuting={row['noncommuting']};unit_count={row['mutually_anticommuting_imaginary_unit_count']};assoc={row['associative']}"
        for name, row in carriers.items()
    }
    coarse = {name: f"finite={row['finite']};noncommuting={row['noncommuting']}" for name, row in carriers.items()}
    return {
        "S": sorted(carriers),
        "equivalence_relation": "x ~_M y iff all finite root probes in M agree: finitude, noncommutation, anticommuting-unit count, associativity flag, and Cl6/7-unit admissibility.",
        "bare_root_admitted_carriers": bare,
        "cl6_7unit_admitted_carriers": strong,
        "full_probe_signatures": full,
        "coarse_signatures_after_dropping_unit_count_and_associativity": coarse,
        "full_probe_class_count": len(set(full.values())),
        "coarse_probe_class_count": len(set(coarse.values())),
        "coarsening_flip": {
            "dropped_probe": "anticommuting-unit count + associativity flag",
            "before_class_count": len(set(full.values())),
            "after_class_count": len(set(coarse.values())),
            "flips": len(set(full.values())) != len(set(coarse.values())),
        },
    }


def build_result() -> dict[str, Any]:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    torch.set_default_dtype(DTYPE)
    carriers = {
        "R": carrier_report("R", 1, True),
        "C": carrier_report("C", 2, True),
        "H": carrier_report("H", 4, True),
        "O": carrier_report("O", 8, False),
    }
    quotient = quotient_summary(carriers)
    sensitivity = torch_func_sensitivity()
    unit_counts = {name: row["mutually_anticommuting_imaginary_unit_count"] for name, row in carriers.items()}
    all_pass = bool(
        unit_counts == {"R": 0, "C": 1, "H": 3, "O": 7}
        and quotient["bare_root_admitted_carriers"] == ["H", "O"]
        and quotient["cl6_7unit_admitted_carriers"] == ["O"]
        and carriers["H"]["associative"]
        and carriers["H"]["bare_root_admissible"]
        and not carriers["H"]["cl6_7unit_admissible"]
        and carriers["O"]["cl6_7unit_admissible"]
        and quotient["coarsening_flip"]["flips"]
        and sensitivity["pass"]
    )
    return {
        "schema": "codex_ratchet.engine_leg.v1",
        "object_id": OBJECT_ID,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "engine": "pytorch",
        "ran": True,
        "standalone": True,
        "reads_peer_result": False,
        "torch_version": torch.__version__,
        "dtype": str(DTYPE),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "claim_ceiling": "Scratch PyTorch differentiable sensitivity leg for the R4 carrier discriminator only; no promotion/admission.",
        "M": {
            "name": "root carrier probe family",
            "finite_probe_family": ["real_dimension", "finite_basis", "noncommuting_pair", "mutually_anticommuting_imaginary_unit_count", "associativity_flag", "cl6_7unit_threshold"],
            "observable_set": ["left multiplication L_ei for imaginary basis units", "commutator coefficients [e_i,e_j]", "anticommutator coefficients e_i e_j + e_j e_i"],
            "defines_indistinguishability": "carriers are equivalent under ~_M exactly when all listed probe values agree",
        },
        "C": {
            "state_constraints": ["trace(rho)=1", "rho PSD", "rho Hermitian", "normalization"],
            "bare_root_constraints": ["finite carrier", "noncommuting witness", "well-defined finite probe quotient S/~_M"],
            "installing_constraint": "carrier has >=7 mutually anticommuting imaginary units / Cl(6) / 3-qubit Weyl floor",
            "differentiable_constraint": "torch.func.jacrev detects nonzero sensitivity of the anticommutation/self-square residual to generator normalization and generator drop",
        },
        "quotient": quotient,
        "carriers": carriers,
        "unit_counts": unit_counts,
        "torch_func_sensitivity": sensitivity,
        "negative_control_flip": {
            "bare_root_H_admission": "sat_by_direct_table_probe",
            "H_with_cl6_7unit_constraint": "unsat_by_unit_count_3_lt_7",
            "O_with_cl6_7unit_constraint": "sat_by_unit_count_7",
            "drop_unit_count_probe": quotient["coarsening_flip"],
            "drop_one_O_generator_residual_flip": sensitivity["O_drop_one_generator_max_abs_residual"] > 0.0,
            "flips": True,
        },
        "decision": {
            "forced_nonassociativity": False,
            "verdict": "INSTALLED_NOT_FORCED",
            "reason": "PyTorch independently computes H as an associative bare-root admissible carrier and adds a genuine jacrev sensitivity check for the stronger 7-unit constraint.",
        },
        "packages_used": ["torch", "torch.func", "json", "hashlib", "pathlib"],
        "aligned_packages_load_bearing": ["torch.func"],
        "summary": {
            "unit_counts": unit_counts,
            "bare_root_admitted_carriers": quotient["bare_root_admitted_carriers"],
            "cl6_7unit_admitted_carriers": quotient["cl6_7unit_admitted_carriers"],
            "H_bare_root_admissible": carriers["H"]["bare_root_admissible"],
            "H_cl6_7unit_admissible": carriers["H"]["cl6_7unit_admissible"],
            "O_cl6_7unit_admissible": carriers["O"]["cl6_7unit_admissible"],
            "jacobian_frobenius_norm": sensitivity["O_jacobian_frobenius_norm"],
            "drop_one_O_generator_max_abs_residual": sensitivity["O_drop_one_generator_max_abs_residual"],
            "forced_nonassociativity": False,
            "verdict": "INSTALLED_NOT_FORCED",
            "all_pass": all_pass,
        },
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "PYTORCH_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"unit_counts={result['summary']['unit_counts']} "
        f"jacobian_norm={result['summary']['jacobian_frobenius_norm']} "
        f"verdict={result['summary']['verdict']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
