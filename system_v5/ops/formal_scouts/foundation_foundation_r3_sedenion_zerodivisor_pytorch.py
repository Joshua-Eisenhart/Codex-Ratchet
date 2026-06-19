#!/usr/bin/env python3
"""PyTorch jacrev leg for the sedenion norm-multiplicativity defect."""

from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

import torch
from torch.func import jacrev


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r3_sedenion_zerodivisor"
OBJECT_ID = "foundation_foundation_r3_sedenion_zerodivisor_pytorch"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r3_sedenion_zerodivisor_pytorch.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r3_sedenion_zerodivisor_pytorch_results.json"
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


def basis(dim: int, idx: int) -> torch.Tensor:
    return torch.eye(dim, dtype=torch.float64)[idx]


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


def normsq(v: torch.Tensor) -> torch.Tensor:
    return torch.sum(v * v)


def vector_terms(v: torch.Tensor) -> list[dict[str, Any]]:
    terms: list[dict[str, Any]] = []
    for idx, coeff in enumerate(v.detach().cpu().tolist()):
        if abs(float(coeff)) > 0.0:
            terms.append({"basis_index": idx, "label": f"e{idx}", "coefficient": float(coeff)})
    return terms


def sedenion_witness_vectors(theta: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    left = torch.zeros(16, dtype=torch.float64)
    right = torch.zeros(16, dtype=torch.float64)
    left[1] = theta[0]
    left[10] = theta[1]
    right[5] = theta[2]
    right[14] = theta[3]
    return left, right


def defect(table: torch.Tensor, left: torch.Tensor, right: torch.Tensor) -> torch.Tensor:
    product = multiply(table, left, right)
    return normsq(product) - normsq(left) * normsq(right)


def fixed_product_record(table: torch.Tensor, left: torch.Tensor, right: torch.Tensor, claim: str) -> dict[str, Any]:
    product = multiply(table, left, right)
    defect_value = defect(table, left, right)
    return {
        "claim": claim,
        "left_components": [float(x) for x in left.detach().cpu().tolist()],
        "right_components": [float(x) for x in right.detach().cpu().tolist()],
        "left_terms": vector_terms(left),
        "right_terms": vector_terms(right),
        "product_components": [float(x) for x in product.detach().cpu().tolist()],
        "product_terms": vector_terms(product),
        "left_normsq": float(normsq(left).item()),
        "right_normsq": float(normsq(right).item()),
        "product_normsq": float(normsq(product).item()),
        "norm_multiplicativity_defect": float(defect_value.item()),
    }


def main() -> int:
    torch.set_default_dtype(torch.float64)
    tables = cd_tables()
    o_table = tables["O"]
    s_table = tables["S"]

    theta = torch.tensor([1.0, 1.0, 1.0, 1.0], dtype=torch.float64)
    left, right = sedenion_witness_vectors(theta)
    s_record = fixed_product_record(s_table, left, right, "(e1 + e10) * (e5 + e14) = 0 in S")

    def witness_defect(params: torch.Tensor) -> torch.Tensor:
        lvec, rvec = sedenion_witness_vectors(params)
        return defect(s_table, lvec, rvec)

    jac = jacrev(witness_defect)(theta)
    plus_step = witness_defect(theta + torch.tensor([0.01, 0.0, 0.0, 0.0], dtype=torch.float64))
    minus_step = witness_defect(theta - torch.tensor([0.01, 0.0, 0.0, 0.0], dtype=torch.float64))
    central_fd = (plus_step - minus_step) / 0.02

    o_left = basis(8, 1) + basis(8, 2)
    o_right = basis(8, 3) + basis(8, 4)
    o_control = fixed_product_record(o_table, o_left, o_right, "(e1 + e2) * (e3 + e4) != 0 in O")
    jac_values = [float(x) for x in jac.detach().cpu().tolist()]
    s_record.update(
        {
            "jacrev_defect_gradient": jac_values,
            "finite_difference_dtheta0": float(central_fd.item()),
            "jacrev_vs_fd_abs_error_dtheta0": abs(jac_values[0] - float(central_fd.item())),
        }
    )
    all_pass = (
        s_record["product_normsq"] == 0.0
        and s_record["left_normsq"] > 0.0
        and s_record["right_normsq"] > 0.0
        and s_record["norm_multiplicativity_defect"] < 0.0
        and max(abs(x) for x in jac_values) > 0.0
        and s_record["jacrev_vs_fd_abs_error_dtheta0"] < 1.0e-10
        and o_control["product_normsq"] > 0.0
        and abs(o_control["norm_multiplicativity_defect"]) < 1.0e-12
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
        "packages_used": ["torch", "torch.func"],
        "aligned_packages_load_bearing": ["torch.func"],
        "claim_path_tools": ["torch", "torch.func"],
        "torch_version": torch.__version__,
        "torch_dtype": str(torch.get_default_dtype()),
        "TOOL_MANIFEST": {
            "torch": {"tried": True, "used": True, "reason": "torch-native float64 Cayley-Dickson tensor arithmetic for differentiable defect evaluation"},
            "torch.func": {"tried": True, "used": True, "reason": "load-bearing jacrev sensitivity of the S norm-multiplicativity defect"},
        },
        "TOOL_INTEGRATION_DEPTH": {"torch": "supportive", "torch.func": "load_bearing"},
        "M": {
            "name": "norm-multiplicativity defect sensitivity at fixed O/S two-term probes",
            "observables": ["defect value", "jacrev gradient of defect at S annihilator", "O defect control"],
        },
        "C": {
            "trace_equals_one": "not a density-state rung; finite unital real algebra carrier",
            "psd": "not a density-state rung; nonzero norm of fixed factors is the positivity/normalization check",
            "hermiticity": "not a density-state rung; Cayley-Dickson conjugation is encoded in the table construction",
            "normalization": "theta=(1,1,1,1) gives nonzero two-term S factors",
            "rung_specific_constraint": "S table constructed inside PyTorch leg; jacrev differentiates the norm-multiplicativity defect",
        },
        "S_quotient_under_M": {
            "O_control": "zero norm defect at sampled O pair",
            "S_witness": "negative norm defect and nonzero jacrev sensitivity at S annihilator",
        },
        "octonion_control": o_control,
        "sedenion_witness": s_record,
        "negative_control": {
            "O_to_S_defect_flip": {
                "O_defect": o_control["norm_multiplicativity_defect"],
                "S_defect": s_record["norm_multiplicativity_defect"],
                "flips": abs(o_control["norm_multiplicativity_defect"]) < 1.0e-12 and s_record["norm_multiplicativity_defect"] < 0.0,
            }
        },
        "independent_check_note": "Genuine PyTorch-side differentiable check: torch.func.jacrev computes sensitivity of the S norm-multiplicativity defect; it is not a parity-only mirror.",
        "all_pass": all_pass,
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "SCOUT_DONE "
        f"all_pass={str(all_pass).lower()} "
        f"S_product_normsq={s_record['product_normsq']} "
        f"S_defect={s_record['norm_multiplicativity_defect']} "
        f"jacrev={jac_values} "
        f"O_product_normsq={o_control['product_normsq']} "
        f"O_defect={o_control['norm_multiplicativity_defect']}"
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
