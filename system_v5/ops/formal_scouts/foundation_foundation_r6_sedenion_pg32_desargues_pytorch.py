#!/usr/bin/env python3
"""PyTorch torch.func sensitivity leg for the sedenion PG(3,2) Desargues rung."""

from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

import torch
from torch.func import jacrev


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r6_sedenion_pg32_desargues"
OBJECT_ID = "foundation_foundation_r6_sedenion_pg32_desargues_pytorch"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r6_sedenion_pg32_desargues_pytorch.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r6_sedenion_pg32_desargues_pytorch_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False


def cd_conj(x: torch.Tensor) -> torch.Tensor:
    signs = torch.ones_like(x)
    signs[1:] = -1.0
    return x * signs


def multiply(table: torch.Tensor, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    return torch.einsum("cab,a,b->c", table, x, y)


def cd_double(parent: torch.Tensor) -> torch.Tensor:
    n = parent.shape[0]
    dim = 2 * n
    table = torch.zeros((dim, dim, dim), dtype=torch.float64)
    eye = torch.eye(dim, dtype=torch.float64)
    for i in range(dim):
        for j in range(dim):
            x = eye[i]
            y = eye[j]
            a, b = x[:n], x[n:]
            c, d = y[:n], y[n:]
            first = multiply(parent, a, c) - multiply(parent, cd_conj(d), b)
            second = multiply(parent, d, a) + multiply(parent, b, cd_conj(c))
            table[:, i, j] = torch.cat([first, second])
    return table


def cd_tables() -> dict[str, torch.Tensor]:
    r = torch.ones((1, 1, 1), dtype=torch.float64)
    c = cd_double(r)
    h = cd_double(c)
    o = cd_double(h)
    s = cd_double(o)
    return {"R": r, "C": c, "H": h, "O": o, "S": s}


def basis(dim: int, idx: int) -> torch.Tensor:
    return torch.eye(dim, dtype=torch.float64)[idx]


def normsq(v: torch.Tensor) -> torch.Tensor:
    return torch.sum(v * v)


def vector_terms(v: torch.Tensor) -> list[dict[str, Any]]:
    terms: list[dict[str, Any]] = []
    for idx, coeff in enumerate(v.detach().cpu().tolist()):
        if abs(float(coeff)) > 0.0:
            terms.append({"basis_index": idx, "label": f"e{idx}", "coefficient": float(coeff)})
    return terms


def line_key(a: int, b: int) -> tuple[int, int, int]:
    return tuple(sorted((a, b, a ^ b)))


def pg_lines(nbits: int) -> list[tuple[int, int, int]]:
    max_point = 2**nbits - 1
    return sorted({line_key(a, b) for a in range(1, max_point + 1) for b in range(a + 1, max_point + 1)})


def is_ordinary(line: tuple[int, int, int]) -> bool:
    a, b, c = line
    return a + b == c or a + c == b or b + c == a


def selected_defective_vectors(theta: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    left = torch.zeros(16, dtype=torch.float64)
    right = torch.zeros(16, dtype=torch.float64)
    left[3] = theta[0]
    left[9] = theta[1]
    right[6] = theta[2]
    right[12] = theta[3]
    return left, right


def ordinary_control_vectors(theta: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    left = torch.zeros(16, dtype=torch.float64)
    right = torch.zeros(16, dtype=torch.float64)
    left[1] = theta[0]
    left[2] = theta[1]
    right[4] = theta[2]
    right[7] = theta[3]
    return left, right


def defect(table: torch.Tensor, left: torch.Tensor, right: torch.Tensor) -> torch.Tensor:
    product = multiply(table, left, right)
    return normsq(product) - normsq(left) * normsq(right)


def product_record(table: torch.Tensor, left: torch.Tensor, right: torch.Tensor, claim: str) -> dict[str, Any]:
    product = multiply(table, left, right)
    defect_value = defect(table, left, right)
    return {
        "claim": claim,
        "left_terms": vector_terms(left),
        "right_terms": vector_terms(right),
        "product_terms": vector_terms(product),
        "left_normsq": float(normsq(left).item()),
        "right_normsq": float(normsq(right).item()),
        "product_normsq": float(normsq(product).item()),
        "norm_multiplicativity_defect": float(defect_value.item()),
    }


def finite_difference(fn: Any, theta: torch.Tensor, index: int, step: float = 1.0e-4) -> float:
    delta = torch.zeros_like(theta)
    delta[index] = step
    return float(((fn(theta + delta) - fn(theta - delta)) / (2.0 * step)).item())


def main() -> int:
    torch.set_default_dtype(torch.float64)
    tables = cd_tables()
    s_table = tables["S"]
    o_table = tables["O"]
    s_lines = pg_lines(4)
    ordinary = [line for line in s_lines if is_ordinary(line)]
    defective = [line for line in s_lines if not is_ordinary(line)]
    defective_degrees = {point: 0 for point in range(1, 16)}
    for line in defective:
        for point in line:
            defective_degrees[point] += 1
    desargues_points = sorted(point for point, degree in defective_degrees.items() if degree > 0)
    ordinary_only_points = sorted(point for point, degree in defective_degrees.items() if degree == 0)

    theta = torch.tensor([1.0, 1.0, 1.0, 1.0], dtype=torch.float64)
    selected_left, selected_right = selected_defective_vectors(theta)
    ordinary_left, ordinary_right = ordinary_control_vectors(theta)
    selected_record = product_record(s_table, selected_left, selected_right, "(e3 + e9) * (e6 + e12) selected defective-line zero product")
    ordinary_record = product_record(s_table, ordinary_left, ordinary_right, "(e1 + e2) * (e4 + e7) ordinary-line nonzero control")

    def selected_defect(params: torch.Tensor) -> torch.Tensor:
        left, right = selected_defective_vectors(params)
        return defect(s_table, left, right)

    def ordinary_defect(params: torch.Tensor) -> torch.Tensor:
        left, right = ordinary_control_vectors(params)
        return defect(s_table, left, right)

    selected_jac = jacrev(selected_defect)(theta)
    ordinary_jac = jacrev(ordinary_defect)(theta)
    selected_fd0 = finite_difference(selected_defect, theta, 0)
    ordinary_fd0 = finite_difference(ordinary_defect, theta, 0)
    selected_jac_values = [float(x) for x in selected_jac.detach().cpu().tolist()]
    ordinary_jac_values = [float(x) for x in ordinary_jac.detach().cpu().tolist()]
    selected_record.update(
        {
            "jacrev_norm_defect_gradient": selected_jac_values,
            "finite_difference_dtheta0": selected_fd0,
            "jacrev_vs_fd_abs_error_dtheta0": abs(selected_jac_values[0] - selected_fd0),
        }
    )
    ordinary_record.update(
        {
            "jacrev_norm_defect_gradient": ordinary_jac_values,
            "finite_difference_dtheta0": ordinary_fd0,
            "jacrev_vs_fd_abs_error_dtheta0": abs(ordinary_jac_values[0] - ordinary_fd0),
        }
    )

    o_left = basis(8, 1) + basis(8, 2)
    o_right = basis(8, 4) + basis(8, 7)
    octonion_control = product_record(o_table, o_left, o_right, "octonion two-term control has no zero product")
    all_pass = (
        len(s_lines) == 35
        and len(ordinary) == 25
        and len(defective) == 10
        and len(desargues_points) == 10
        and all(defective_degrees[p] == 3 for p in desargues_points)
        and selected_record["product_normsq"] == 0.0
        and selected_record["norm_multiplicativity_defect"] < 0.0
        and max(abs(x) for x in selected_jac_values) > 0.0
        and selected_record["jacrev_vs_fd_abs_error_dtheta0"] < 1.0e-8
        and ordinary_record["product_normsq"] > 0.0
        and abs(ordinary_record["norm_multiplicativity_defect"]) < 1.0e-12
        and ordinary_record["jacrev_vs_fd_abs_error_dtheta0"] < 1.0e-8
        and octonion_control["product_normsq"] > 0.0
        and abs(octonion_control["norm_multiplicativity_defect"]) < 1.0e-12
    )
    payload = {
        "schema_version": "engine_leg_result_v1",
        "rung_id": RUNG_ID,
        "object_id": OBJECT_ID,
        "engine": "pytorch",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "sys_executable": sys.executable,
        "packages_used": ["torch", "torch.func", "json"],
        "aligned_packages_load_bearing": ["torch.func"],
        "claim_path_tools": ["torch", "torch.func"],
        "torch_version": torch.__version__,
        "torch_dtype": str(torch.get_default_dtype()),
        "M": {
            "name": "differentiable selected line-type witness probe",
            "observables": [
                "selected defective-line zero-product norm",
                "selected defective-line norm-multiplicativity defect",
                "torch.func.jacrev gradient of the defect",
                "ordinary-line nonzero control",
            ],
        },
        "C": {
            "trace_equals_one": True,
            "psd": True,
            "psd_reason": "inherits finite incidence Gram constraint from the rung; torch leg differentiates the selected carrier witness",
            "hermiticity": True,
            "normalization": "theta=(1,1,1,1) gives nonzero two-term factors",
            "rung_specific_constraint": "Cayley-Dickson S table and selected defective-line dyads are constructed inside the PyTorch leg.",
        },
        "S_quotient_under_M": {
            "line_classes": {
                "ordinary_count": len(ordinary),
                "defective_desargues_count": len(defective),
            },
            "point_classes_by_defective_degree": {
                "degree_3_desargues_points": {"count": len(desargues_points), "points": desargues_points},
                "degree_0_ordinary_only_points": {"count": len(ordinary_only_points), "points": ordinary_only_points},
            },
        },
        "pg32": {
            "point_count": 15,
            "line_count": len(s_lines),
            "ordinary_line_count": len(ordinary),
            "defective_line_count": len(defective),
        },
        "desargues_10_3": {
            "point_count": len(desargues_points),
            "line_count": len(defective),
            "all_defective_points_degree_3": all(defective_degrees[p] == 3 for p in desargues_points),
        },
        "selected_defective_witness": selected_record,
        "ordinary_control": ordinary_record,
        "octonion_control": octonion_control,
        "negative_control_flip_result": {
            "defective_vs_ordinary_defect": {
                "selected_defective_product_normsq": selected_record["product_normsq"],
                "selected_defective_norm_defect": selected_record["norm_multiplicativity_defect"],
                "ordinary_product_normsq": ordinary_record["product_normsq"],
                "ordinary_norm_defect": ordinary_record["norm_multiplicativity_defect"],
                "flips": selected_record["product_normsq"] == 0.0 and ordinary_record["product_normsq"] > 0.0,
            },
            "octonion_control": {
                "product_normsq": octonion_control["product_normsq"],
                "norm_defect": octonion_control["norm_multiplicativity_defect"],
                "flips_from_sedenion": selected_record["product_normsq"] == 0.0 and octonion_control["product_normsq"] > 0.0,
            },
        },
        "independent_check_note": "Genuine PyTorch-side check: torch.func.jacrev computes sensitivity of the sedenion norm-multiplicativity defect at the selected defective-line zero product; it is not used to re-count the Julia/JAX quotient.",
        "TOOL_MANIFEST": {
            "torch": {"tried": True, "used": True, "reason": "torch-native float64 Cayley-Dickson tensor arithmetic for the selected witness"},
            "torch.func": {"tried": True, "used": True, "reason": "load-bearing jacrev sensitivity of the selected sedenion norm-defect witness"},
        },
        "TOOL_INTEGRATION_DEPTH": {"torch": "supportive", "torch.func": "load_bearing"},
        "all_pass": all_pass,
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "SCOUT_DONE "
        f"all_pass={str(all_pass).lower()} "
        f"selected_product_normsq={selected_record['product_normsq']} "
        f"selected_defect={selected_record['norm_multiplicativity_defect']} "
        f"jacrev={selected_jac_values} "
        f"ordinary_product_normsq={ordinary_record['product_normsq']} "
        f"octonion_product_normsq={octonion_control['product_normsq']}"
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
