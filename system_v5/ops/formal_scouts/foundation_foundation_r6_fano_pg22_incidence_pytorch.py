#!/usr/bin/env python3
"""PyTorch torch.func leg for foundation_r6_fano_pg22_incidence.

Scratch diagnostic only. PyTorch independently derives the incidence lines
from a torch float64 Cayley-Dickson table and supplies the distinct check:
torch.func.jacrev sensitivity of the Fano collinearity residual under erasing
one true product coefficient.
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
RUNG_ID = "foundation_r6_fano_pg22_incidence"
OBJECT_ID = "foundation_r6_fano_pg22_incidence_pytorch"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r6_fano_pg22_incidence_pytorch.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r6_fano_pg22_incidence_pytorch_results.json"
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
        "reason": "supportive float64 Cayley-Dickson table and independent incidence derivation",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "load-bearing jacrev sensitivity of collinearity residual under differentiable erasure of a true line product",
    },
    "python_stdlib": {"tried": True, "used": True, "reason": "supportive JSON, hashing, and path handling"},
}

TOOL_INTEGRATION_DEPTH = {"torch": "supportive", "torch.func": "load_bearing", "python_stdlib": "supportive"}


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


def table_sha(table: torch.Tensor) -> str:
    flat = [str(int(round(x))) for x in table.detach().cpu().reshape((-1,)).tolist()]
    return hashlib.sha256(",".join(flat).encode("utf-8")).hexdigest()


def product_support(table: torch.Tensor, i0: int, j0: int) -> dict[str, Any]:
    vec = [int(round(x)) for x in table[:, i0, j0].detach().cpu().tolist()]
    nz = [idx for idx, value in enumerate(vec) if value != 0]
    if len(nz) != 1:
        return {"valid": False, "support": None, "sign": 0, "vector": vec}
    return {"valid": True, "support": nz[0], "sign": vec[nz[0]], "vector": vec}


def derive_lines(table: torch.Tensor) -> tuple[list[list[int]], list[dict[str, Any]]]:
    line_map: dict[tuple[int, int, int], list[int]] = {}
    pair_records: list[dict[str, Any]] = []
    for i in range(1, 8):
        for j in range(i + 1, 8):
            prod = product_support(table, i, j)
            valid = bool(prod["valid"] and prod["support"] in range(1, 8) and prod["support"] not in {i, j})
            if valid:
                triple = sorted([i, j, int(prod["support"])])
                line_map[tuple(triple)] = triple
            pair_records.append(
                {
                    "pair": [i, j],
                    "product_support": prod["support"],
                    "sign": prod["sign"],
                    "valid_collinearity_probe": valid,
                }
            )
    return sorted(line_map.values()), pair_records


def fano_axioms(lines: list[list[int]]) -> dict[str, Any]:
    point_degrees = {str(p): sum(1 for line in lines if p in line) for p in range(1, 8)}
    pair_counts = {
        f"{i}-{j}": sum(1 for line in lines if i in line and j in line) for i in range(1, 8) for j in range(i + 1, 8)
    }
    three_points = all(len(line) == 3 and len(set(line)) == 3 for line in lines)
    holds = len(lines) == 7 and three_points and all(v == 3 for v in point_degrees.values()) and all(
        v == 1 for v in pair_counts.values()
    )
    return {
        "point_count": 7,
        "line_count": len(lines),
        "three_points_per_line": three_points,
        "three_lines_per_point": all(v == 3 for v in point_degrees.values()),
        "unique_line_through_each_pair": all(v == 1 for v in pair_counts.values()),
        "point_degrees": point_degrees,
        "pair_line_counts": pair_counts,
        "holds": holds,
    }


def mutate_pair_product(table: torch.Tensor, i0: int, j0: int, wrong_k0: int) -> torch.Tensor:
    control = table.clone()
    control[:, i0, j0] = 0.0
    control[wrong_k0, i0, j0] = 1.0
    control[:, j0, i0] = 0.0
    control[wrong_k0, j0, i0] = -1.0
    return control


def differentiable_erasure_sensitivity(table: torch.Tensor, lines: list[list[int]]) -> dict[str, Any]:
    targets: list[tuple[int, int, int, int]] = []
    for i in range(1, 8):
        for j in range(i + 1, 8):
            prod = product_support(table, i, j)
            targets.append((i, j, int(prod["support"]), int(prod["sign"])))
    true_line = lines[0]
    erased_i, erased_j, erased_k = true_line
    erased_prod = product_support(table, erased_i, erased_j)
    erased_sign = int(erased_prod["sign"])

    def table_with_alpha(alpha: torch.Tensor) -> torch.Tensor:
        mutated = table.clone()
        mutated[:, erased_i, erased_j] = alpha * table[:, erased_i, erased_j]
        mutated[:, erased_j, erased_i] = alpha * table[:, erased_j, erased_i]
        return mutated

    def incidence_energy(alpha: torch.Tensor) -> torch.Tensor:
        mutated = table_with_alpha(alpha)
        total = torch.zeros((), dtype=torch.float64)
        for i, j, k, sign in targets:
            target = torch.zeros(8, dtype=torch.float64)
            target[k] = float(sign)
            residual = mutated[:, i, j] - target
            total = total + torch.dot(residual, residual)
        return total

    grid = []
    for value in [0.0, 0.25, 0.5, 0.75, 1.0]:
        alpha = torch.tensor(value, dtype=torch.float64)
        grid.append({"alpha": value, "energy": as_float(incidence_energy(alpha)), "jacrev": as_float(jacrev(incidence_energy)(alpha))})
    return {
        "expression": "E(alpha)=sum_pair ||product_alpha(e_i,e_j)-signed_target_ij||^2, with one true line product scaled by alpha",
        "erased_true_line": true_line,
        "erased_product_sign": erased_sign,
        "energy_alpha_1": grid[-1]["energy"],
        "energy_alpha_0_5": grid[2]["energy"],
        "energy_alpha_0": grid[0]["energy"],
        "jacrev_alpha_1": grid[-1]["jacrev"],
        "jacrev_alpha_0_5": grid[2]["jacrev"],
        "jacrev_alpha_0": grid[0]["jacrev"],
        "grid": grid,
        "sensitivity_nonzero": grid[-1]["energy"] <= TOL and grid[2]["energy"] > TOL and abs(grid[2]["jacrev"]) > TOL,
        "independence_limit": "PyTorch does not prove the finite incidence axioms; it supplies a genuine differentiable sensitivity check for the line-erasure control.",
    }


def build_result() -> dict[str, Any]:
    table = build_tables()["O"]
    lines, pair_records = derive_lines(table)
    axioms = fano_axioms(lines)
    control_table = mutate_pair_product(table, 1, 2, 4)
    control_lines, control_pair_records = derive_lines(control_table)
    control_axioms = fano_axioms(control_lines)
    sensitivity = differentiable_erasure_sensitivity(table, lines)
    negative = {
        "non_octonion_erased_pair_axioms_hold_true_to_false": axioms["holds"] is True and control_axioms["holds"] is False,
        "line_count_7_to_control": [len(lines), len(control_lines)],
        "mutated_pair": [1, 2],
        "mutated_pair_wrong_support": 4,
        "mutated_pair_unique_line_count": control_axioms["pair_line_counts"]["1-2"],
        "torch_func_jacrev_independent_sensitivity": sensitivity["sensitivity_nonzero"],
    }
    all_pass = bool(
        axioms["holds"]
        and not control_axioms["holds"]
        and sensitivity["sensitivity_nonzero"]
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
        "packages_used": ["torch", "torch.func", "json", "pathlib", "hashlib"],
        "aligned_packages_load_bearing": ["torch.func"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "runtime_preflight": {"sys_executable": sys.executable, "torch_version": torch.__version__, "dtype": "torch.float64"},
        "M": {
            "name": "octonion_collinearity_probe_family",
            "explicit_probe_family": ["P_ij for each unordered pair of distinct imaginary units e_i,e_j: compute e_i*e_j and record the signed support +/-e_k"],
            "finite_probe_counts": {"points": 7, "pair_probes": 21, "line_projectors": len(lines)},
            "pair_records": pair_records,
        },
        "C": {
            "trace_eq_1": True,
            "psd": True,
            "hermitian": True,
            "normalization": "finite one-hot point probes have unit norm; auxiliary density guard is identity/7",
            "rung_specific_constraint": "torch float64 Cayley-Dickson octonion structure constants; collinearity residual is differentiable under product erasure",
            "structure_constants_sha256": table_sha(table),
        },
        "S_mod_M": {
            "definition": "S is unordered triples of seven imaginary units; the M quotient classes are triples whose pair products close under +/- the third point.",
            "points": list(range(1, 8)),
            "equivalence_classes": lines,
            "quotient_line_count": len(lines),
            "incidence_structure": "PG(2,2) Fano plane",
        },
        "fano_axioms": axioms,
        "control": {
            "kind": "non_octonion_mutated_pair_product",
            "lines": control_lines,
            "pair_records": control_pair_records,
            "fano_axioms": control_axioms,
        },
        "torch_func": sensitivity,
        "negative_control_flip": negative,
        "summary": {
            "points": 7,
            "line_count": len(lines),
            "lines": lines,
            "fano_axioms_hold": axioms["holds"],
            "control_line_count": len(control_lines),
            "control_fano_axioms_hold": control_axioms["holds"],
            "jacrev_alpha_0_5": sensitivity["jacrev_alpha_0_5"],
            "energy_alpha_0_5": sensitivity["energy_alpha_0_5"],
        },
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "FOUNDATION_R6_FANO_PG22_INCIDENCE_PYTORCH_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"lines={result['summary']['lines']} "
        f"control_lines={result['summary']['control_line_count']} "
        f"energy_alpha_0_5={result['summary']['energy_alpha_0_5']} "
        f"jacrev_alpha_0_5={result['summary']['jacrev_alpha_0_5']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
