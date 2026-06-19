#!/usr/bin/env python3
"""PyTorch torch.func leg for octonion-left-action Cl(0,6) sensitivity."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any

import torch
from torch.func import jacrev


OBJECT_ID = "foundation_r3_octonion_cl6_link_xhigh"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_r3_octonion_cl6_link_xhigh_pytorch.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_r3_octonion_cl6_link_xhigh_pytorch_results.json"
DTYPE = torch.float64
TOL = 1.0e-9


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


def left_matrix(dim: int, unit_idx: int) -> torch.Tensor:
    e = basis(dim, unit_idx)
    return torch.stack([cd_mul(e, basis(dim, col)) for col in range(dim)], dim=1)


def left_matrices(dim: int) -> list[torch.Tensor]:
    return [left_matrix(dim, idx) for idx in range(1, dim)]


def rank_from_columns(cols: list[torch.Tensor]) -> dict[str, Any]:
    mat = torch.stack(cols, dim=1)
    singular = torch.linalg.svdvals(mat)
    max_s = py_float(torch.max(singular)) if singular.numel() else 0.0
    tol = max(mat.shape) * torch.finfo(DTYPE).eps * max_s * 100.0
    rank = int(torch.sum(singular > tol).item())
    return {"rank": rank, "rank_tol": float(tol)}


def generated_rank(mats: list[torch.Tensor], generator_count: int) -> dict[str, Any]:
    dim = int(mats[0].shape[0])
    cols: list[torch.Tensor] = []
    for mask in range(2**generator_count):
        acc = torch.eye(dim, dtype=DTYPE)
        for idx in range(generator_count):
            if (mask >> idx) & 1:
                acc = acc @ mats[idx]
        cols.append(acc.reshape(-1))
    report = rank_from_columns(cols)
    report.update({"generator_count": generator_count, "word_count": len(cols)})
    return report


def anticommutation_vector(mats: list[torch.Tensor]) -> torch.Tensor:
    dim = int(mats[0].shape[0])
    rows: list[torch.Tensor] = []
    for i, left in enumerate(mats):
        for j, right in enumerate(mats):
            target = -2.0 * torch.eye(dim, dtype=DTYPE) if i == j else torch.zeros((dim, dim), dtype=DTYPE)
            rows.append((left @ right + right @ left - target).reshape(-1))
    return torch.cat(rows)


def anticommutation_report(mats: list[torch.Tensor]) -> dict[str, Any]:
    residual = anticommutation_vector(mats)
    return {
        "relation": "L_i L_j + L_j L_i = -2 delta_ij I",
        "max_abs_residual": py_float(torch.max(torch.abs(residual))),
        "l2_residual": py_float(torch.linalg.norm(residual)),
        "entry_count": int(residual.numel()),
        "pass": py_float(torch.max(torch.abs(residual))) <= TOL,
    }


def skew_report(mats: list[torch.Tensor]) -> dict[str, Any]:
    residuals = [py_float(torch.linalg.norm(mat.T + mat)) for mat in mats]
    return {"max_residual": max(residuals), "per_generator_residuals": residuals, "pass": max(residuals) <= TOL}


def pseudoscalar_link_report(o_mats: list[torch.Tensor]) -> dict[str, Any]:
    product = torch.eye(8, dtype=DTYPE)
    for idx in range(6):
        product = product @ o_mats[idx]
    plus_residual = py_float(torch.linalg.norm(product - o_mats[6]))
    minus_residual = py_float(torch.linalg.norm(product + o_mats[6]))
    return {
        "relation": "L_e1 L_e2 L_e3 L_e4 L_e5 L_e6 = L_e7 under this Cayley-Dickson orientation",
        "plus_residual": plus_residual,
        "minus_residual": minus_residual,
        "pass": plus_residual <= TOL,
    }


def scaled_residual_vector(scales: torch.Tensor, base_mats: tuple[torch.Tensor, ...]) -> torch.Tensor:
    mats = [scales[idx] * base_mats[idx] for idx in range(scales.shape[0])]
    return anticommutation_vector(mats)


def torch_func_sensitivity(o_mats: list[torch.Tensor]) -> dict[str, Any]:
    base = tuple(mat.clone() for mat in o_mats[:6])
    scales0 = torch.ones(6, dtype=DTYPE)
    residual0 = scaled_residual_vector(scales0, base)
    jacobian = jacrev(lambda scales: scaled_residual_vector(scales, base))(scales0)
    dim = 8

    def residual_index(i: int, j: int, row: int, col: int) -> int:
        return (((i * 6 + j) * dim + row) * dim) + col

    self_diag_sensitivities = [py_float(jacobian[residual_index(i, i, 0, 0), i]) for i in range(6)]
    eps = torch.tensor(1.0e-4, dtype=DTYPE)
    perturbed = scales0.clone()
    perturbed[0] = perturbed[0] + eps
    finite_difference = (scaled_residual_vector(perturbed, base)[residual_index(0, 0, 0, 0)] - residual0[residual_index(0, 0, 0, 0)]) / eps
    fd_residual = abs(py_float(finite_difference) - self_diag_sensitivities[0])
    return {
        "tool": "torch.func.jacrev",
        "claim_tie": "Jacobian of the Cl(0,6) anticommutation residual with respect to generator normalization scales; nonzero derivative detects that the Clifford constraint is not a pinned scalar.",
        "residual_vector_length": int(residual0.numel()),
        "jacobian_shape": list(jacobian.shape),
        "jacobian_frobenius_norm": py_float(torch.linalg.norm(jacobian)),
        "self_diagonal_sensitivities": self_diag_sensitivities,
        "expected_self_diagonal_sensitivity": -4.0,
        "finite_difference_sensitivity_L1": py_float(finite_difference),
        "finite_difference_vs_jacrev_abs_residual": fd_residual,
        "pass": py_float(torch.linalg.norm(jacobian)) > 0.0
        and all(abs(value + 4.0) <= 1.0e-9 for value in self_diag_sensitivities)
        and fd_residual <= 1.0e-3,
    }


def quotient_report(o_rank: dict[str, Any], h_rank: dict[str, Any], o_anti: dict[str, Any], h_anti: dict[str, Any]) -> dict[str, Any]:
    full_signatures = {
        "octonion_left_action_on_O": f"O:generators=7;carrier_dim=8;rank={o_rank['rank']};spinor_dim=8;anticommutes={o_anti['pass']}",
        "quaternion_left_action_control_on_H": f"H:generators=3;carrier_dim=4;rank={h_rank['rank']};spinor_dim=2;anticommutes={h_anti['pass']}",
    }
    coarse_signatures = {
        "octonion_left_action_on_O": f"skew=True;anticommutes={o_anti['pass']}",
        "quaternion_left_action_control_on_H": f"skew=True;anticommutes={h_anti['pass']}",
    }
    full_count = len(set(full_signatures.values()))
    coarse_count = len(set(coarse_signatures.values()))
    return {
        "S": ["octonion_left_action_on_O", "quaternion_left_action_control_on_H"],
        "equivalence_relation": "x ~_M y iff all finite M probes match: generator count, carrier dimension, anticommutation signature, generated Clifford rank, and spinor dimension",
        "full_probe_signatures": full_signatures,
        "coarse_probe_signatures_after_dropping_dimension_and_rank": coarse_signatures,
        "full_probe_class_count": full_count,
        "drop_dimension_and_rank_probe_class_count": coarse_count,
        "octonion_class": {"label": "Cl(0,6)_spinor_from_O_left_multiplication", "generated_rank": o_rank["rank"], "spinor_dim": 8},
        "quaternion_control_class": {"label": "Cl(0,2)_control_from_H_left_multiplication", "generated_rank": h_rank["rank"], "spinor_dim": 2},
        "coarsening_flip": {
            "dropped_probe": "carrier dimension + generated Clifford rank",
            "before_class_count": full_count,
            "after_class_count": coarse_count,
            "flips": full_count != coarse_count,
        },
    }


def build_result() -> dict[str, Any]:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    torch.set_default_dtype(DTYPE)
    o_mats = left_matrices(8)
    h_mats = left_matrices(4)
    o_skew = skew_report(o_mats)
    h_skew = skew_report(h_mats)
    o_anti = anticommutation_report(o_mats)
    h_anti = anticommutation_report(h_mats)
    o_rank6 = generated_rank(o_mats, 6)
    o_rank7 = generated_rank(o_mats, 7)
    h_rank2 = generated_rank(h_mats, 2)
    h_rank3 = generated_rank(h_mats, 3)
    pseudoscalar_link = pseudoscalar_link_report(o_mats)
    sensitivity = torch_func_sensitivity(o_mats)
    quotient = quotient_report(o_rank6, h_rank2, o_anti, h_anti)

    all_pass = bool(
        o_skew["pass"]
        and h_skew["pass"]
        and o_anti["pass"]
        and h_anti["pass"]
        and o_rank6["rank"] == 64
        and o_rank7["rank"] == 64
        and h_rank2["rank"] == 4
        and h_rank3["rank"] == 4
        and pseudoscalar_link["pass"]
        and sensitivity["pass"]
        and quotient["coarsening_flip"]["flips"]
    )

    return {
        "schema": "codex_ratchet.engine_leg.v1",
        "object_id": OBJECT_ID,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "Scratch PyTorch torch.func differentiability leg for octonion left-action Cl(0,6) constraint sensitivity only; no promotion/admission.",
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
        "M": {
            "probe_family": "finite octonion left-multiplication observables and anticommutator matrix entries",
            "operators": [f"L_e{idx}" for idx in range(1, 8)],
            "probe_entries": "<basis_a | (L_ei L_ej + L_ej L_ei) | basis_b> for i,j=1..7 and a,b=1..8",
            "pair_probe_count": 49,
            "entry_probe_count": 49 * 8 * 8,
            "quotient_discriminators": ["generator_count", "carrier_dimension", "anticommutation_signature", "generated_clifford_rank", "spinor_dimension"],
        },
        "C": {
            "state_constraints": ["trace(rho)=1", "rho PSD", "rho Hermitian", "normalization"],
            "rung_specific_constraints": [
                "Cayley-Dickson octonion multiplication table",
                "L_ei^T = -L_ei",
                "L_ei L_ej + L_ej L_ei = -2 delta_ij I",
                "first six L_ei generate a 64-dimensional Cl(0,6) carrier on an 8-dimensional spinor",
                "torch.func.jacrev sensitivity of anticommutator residual to generator scaling is nonzero and equals -4 on self-diagonal probes",
            ],
        },
        "quotient": quotient,
        "octonion_left_action": {
            "carrier_real_dimension": 8,
            "generator_count": 7,
            "skew": o_skew,
            "anticommutation": o_anti,
            "generated_rank_first_six": o_rank6,
            "generated_rank_all_seven_matrix_image": o_rank7,
            "spinor_dim": 8,
            "pseudoscalar_link": pseudoscalar_link,
        },
        "quaternion_control": {
            "carrier_real_dimension": 4,
            "generator_count": 3,
            "skew": h_skew,
            "anticommutation": h_anti,
            "generated_rank_first_two": h_rank2,
            "generated_rank_all_three_matrix_image": h_rank3,
            "spinor_dim": 2,
            "control_result": "Cl(0,2) rank 4 / spinor 2, not Cl(0,6) rank 64 / spinor 8",
        },
        "torch_func_sensitivity": sensitivity,
        "negative_controls": {
            "quaternion_H_control": {
                "octonion_rank": o_rank6["rank"],
                "quaternion_rank": h_rank2["rank"],
                "octonion_spinor_dim": 8,
                "quaternion_spinor_dim": 2,
                "flips": o_rank6["rank"] != h_rank2["rank"],
            },
            "drop_dimension_and_rank_probe": quotient["coarsening_flip"],
            "normalization_sensitivity": {
                "jacobian_frobenius_norm": sensitivity["jacobian_frobenius_norm"],
                "self_diagonal_sensitivities": sensitivity["self_diagonal_sensitivities"],
                "flips_from_zero_sensitivity": sensitivity["jacobian_frobenius_norm"] > 0.0,
            },
        },
        "packages_used": ["torch", "torch.func", "json", "hashlib", "pathlib"],
        "aligned_packages_load_bearing": ["torch.func"],
        "TOOL_MANIFEST": {
            "torch.func": {"tried": True, "used": True, "reason": "load-bearing jacrev sensitivity of Clifford anticommutation residual to generator normalization"},
            "torch": {"tried": True, "used": True, "reason": "supportive float64 tensor substrate for finite Cayley-Dickson matrix construction"},
            "json": {"tried": True, "used": True, "reason": "supportive result serialization"},
            "hashlib": {"tried": True, "used": True, "reason": "supportive source hash"},
            "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic paths"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "torch.func": "load_bearing",
            "torch": "supportive",
            "json": "supportive",
            "hashlib": "supportive",
            "pathlib": "supportive",
        },
        "summary": {
            "octonion_cl6_rank": o_rank6["rank"],
            "octonion_all7_matrix_rank": o_rank7["rank"],
            "octonion_spinor_dim": 8,
            "quaternion_cl2_rank": h_rank2["rank"],
            "quaternion_all3_matrix_rank": h_rank3["rank"],
            "quaternion_spinor_dim": 2,
            "octonion_anticommutation_max_residual": o_anti["max_abs_residual"],
            "quaternion_anticommutation_max_residual": h_anti["max_abs_residual"],
            "pseudoscalar_link_plus_residual": pseudoscalar_link["plus_residual"],
            "full_quotient_class_count": quotient["full_probe_class_count"],
            "coarse_quotient_class_count": quotient["drop_dimension_and_rank_probe_class_count"],
            "jacobian_frobenius_norm": sensitivity["jacobian_frobenius_norm"],
            "self_diagonal_sensitivities": sensitivity["self_diagonal_sensitivities"],
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
        f"octonion_cl6_rank={result['summary']['octonion_cl6_rank']} "
        f"quaternion_cl2_rank={result['summary']['quaternion_cl2_rank']} "
        f"jacobian_norm={result['summary']['jacobian_frobenius_norm']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
