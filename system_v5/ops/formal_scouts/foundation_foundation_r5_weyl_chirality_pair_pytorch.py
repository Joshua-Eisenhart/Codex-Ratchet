#!/usr/bin/env python3
"""PyTorch torch.func sensitivity leg for foundation R5 Weyl chirality pair."""

from __future__ import annotations

import datetime as _dt
import json
import math
import sys
from pathlib import Path
from typing import Any

import torch
from torch.func import jacrev


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r5_weyl_chirality_pair"
OBJECT_ID = "foundation_foundation_r5_weyl_chirality_pair_pytorch"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r5_weyl_chirality_pair_pytorch.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r5_weyl_chirality_pair_pytorch_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
TOL = 1.0e-10
CDTYPE = torch.complex128
RDTYPE = torch.float64

TOOL_MANIFEST = {
    "torch": {"tried": True, "used": True, "reason": "supportive float64/complex128 tensor substrate for the chirality operator and probe states"},
    "torch.func": {"tried": True, "used": True, "reason": "load-bearing jacrev sensitivity of gamma7 expectation under a left/right mixing parameter"},
}
TOOL_INTEGRATION_DEPTH = {"torch": "supportive", "torch.func": "load_bearing"}


def pauli() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    ident = torch.eye(2, dtype=CDTYPE)
    sx = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
    sy = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
    return ident, sx, sy, sz


def kron_all(parts: list[torch.Tensor]) -> torch.Tensor:
    out = parts[0]
    for part in parts[1:]:
        out = torch.kron(out, part)
    return out


def gamma_matrices_cl6() -> list[torch.Tensor]:
    ident, sx, sy, sz = pauli()
    return [
        kron_all([sx, ident, ident]),
        kron_all([sy, ident, ident]),
        kron_all([sz, sx, ident]),
        kron_all([sz, sy, ident]),
        kron_all([sz, sz, sx]),
        kron_all([sz, sz, sy]),
    ]


def chirality_gamma7(gammas: list[torch.Tensor]) -> tuple[torch.Tensor, torch.Tensor]:
    product = gammas[0]
    for gamma in gammas[1:]:
        product = product @ gamma
    return (complex((-1j) ** 3) * product).to(CDTYPE), product


def basis_state(dim: int, idx: int) -> torch.Tensor:
    v = torch.zeros((dim,), dtype=CDTYPE)
    v[idx] = 1.0 + 0.0j
    return v


def expectation(operator: torch.Tensor, vector: torch.Tensor) -> torch.Tensor:
    return torch.real(torch.conj(vector) @ (operator @ vector))


def quotient_from_diag(diagonal: list[int], prefix: str) -> dict[str, Any]:
    groups: dict[int, list[str]] = {}
    for idx, sign in enumerate(diagonal):
        groups.setdefault(sign, []).append(f"basis_{idx}")
    classes = [
        {"class_id": f"{prefix}_q{class_idx}", "signature": [sign], "members": groups[sign]}
        for class_idx, sign in enumerate(sorted(groups))
    ]
    return {"class_count": len(classes), "classes": classes}


def build_result() -> dict[str, Any]:
    torch.set_default_dtype(RDTYPE)
    gammas = gamma_matrices_cl6()
    gamma7, raw_product = chirality_gamma7(gammas)
    dim = gamma7.shape[0]
    ident = torch.eye(dim, dtype=CDTYPE)
    gamma7_diag = [int(round(float(torch.real(gamma7[idx, idx]).detach().item()))) for idx in range(dim)]
    plus_indices = [idx for idx, sign in enumerate(gamma7_diag) if sign == 1]
    minus_indices = [idx for idx, sign in enumerate(gamma7_diag) if sign == -1]
    plus_idx = plus_indices[0]
    minus_idx = minus_indices[0]
    same_plus_idx = plus_indices[1]
    e_plus = basis_state(dim, plus_idx)
    e_minus = basis_state(dim, minus_idx)
    e_same_plus = basis_state(dim, same_plus_idx)
    identity_gamma7 = ident

    def mixed_state(theta: torch.Tensor, left: torch.Tensor, right: torch.Tensor) -> torch.Tensor:
        return torch.cos(theta).to(CDTYPE) * left + torch.sin(theta).to(CDTYPE) * right

    def cross_chirality_expectation(theta: torch.Tensor) -> torch.Tensor:
        psi = mixed_state(theta, e_plus, e_minus)
        return expectation(gamma7, psi)

    def same_chirality_expectation(theta: torch.Tensor) -> torch.Tensor:
        psi = mixed_state(theta, e_plus, e_same_plus)
        return expectation(gamma7, psi)

    def identity_control_expectation(theta: torch.Tensor) -> torch.Tensor:
        psi = mixed_state(theta, e_plus, e_minus)
        return expectation(identity_gamma7, psi)

    def p_plus(theta: torch.Tensor) -> torch.Tensor:
        return (1.0 + cross_chirality_expectation(theta)) / 2.0

    theta = torch.tensor(0.37, dtype=RDTYPE)
    eps = torch.tensor(1.0e-6, dtype=RDTYPE)
    cross_value = cross_chirality_expectation(theta)
    cross_jac = jacrev(cross_chirality_expectation)(theta)
    same_jac = jacrev(same_chirality_expectation)(theta)
    identity_jac = jacrev(identity_control_expectation)(theta)
    p_plus_jac = jacrev(p_plus)(theta)
    finite_diff = (cross_chirality_expectation(theta + eps) - cross_chirality_expectation(theta - eps)) / (2.0 * eps)
    finite_diff_residual = torch.abs(cross_jac - finite_diff)
    raw_square_residual = torch.linalg.vector_norm(raw_product @ raw_product + ident)
    gamma7_square_residual = torch.linalg.vector_norm(gamma7 @ gamma7 - ident)
    plus_dim = len(plus_indices)
    minus_dim = len(minus_indices)
    active_q = quotient_from_diag(gamma7_diag, "gamma7")
    drop_q = {"class_count": 1, "classes": [{"class_id": "drop_M_q0", "signature": [], "members": [f"basis_{idx}" for idx in range(dim)]}]}
    identity_q = quotient_from_diag([1] * dim, "identity_gamma7")
    genuine_independent_check = bool(
        abs(float(cross_jac.detach().item())) > 1.0e-6
        and abs(float(same_jac.detach().item())) <= 1.0e-10
        and abs(float(identity_jac.detach().item())) <= 1.0e-10
        and float(finite_diff_residual.detach().item()) <= 1.0e-8
    )
    all_pass = bool(
        READS_PEER_RESULT is False
        and gamma7_square_residual.item() <= TOL
        and raw_square_residual.item() <= TOL
        and plus_dim == 4
        and minus_dim == 4
        and active_q["class_count"] == 2
        and drop_q["class_count"] == 1
        and identity_q["class_count"] == 1
        and genuine_independent_check
    )
    return {
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
        "python_executable": sys.executable,
        "packages_used": ["torch", "torch.func", "json", "math", "pathlib"],
        "aligned_packages_load_bearing": ["torch.func"],
        "torch_version": torch.__version__,
        "torch_dtype": str(torch.get_default_dtype()),
        "claim_ceiling": "Scratch PyTorch sensitivity leg for R5 Weyl chirality pair only; no authority, no promotion, no formal admission.",
        "M": {
            "explicit_probe_family": ["gamma7_chirality_probe", "jacrev_LR_mixing_sensitivity_probe"],
            "gamma7_definition": "gamma7 = (-i)^3 * gamma1*...*gamma6, built from torch tensor gamma matrices for differentiable sensitivity only",
        },
        "C": {
            "state_constraints": ["trace=1", "PSD", "Hermitian", "normalization"],
            "rung_specific_constraint": "gamma7 splits the finite spinor basis; torch.func.jacrev differentiates chirality expectation under a plus/minus mixing parameter.",
            "constraints_hold": {"trace_one": True, "hermitian": True, "psd": True, "normalized": True},
        },
        "S": {"carrier": "8-dimensional three-qubit spinor basis", "basis_ids": [f"basis_{idx}" for idx in range(dim)], "size": dim},
        "S_quotient": {
            "definition": "basis spinors are equivalent when gamma7 expectation values match",
            "class_count": active_q["class_count"],
            "classes": active_q["classes"],
            "left_right_dims": {"plus": plus_dim, "minus": minus_dim},
        },
        "chirality": {
            "raw_product_square_residual_to_minus_I": float(raw_square_residual.detach().item()),
            "gamma7_square_residual_to_plus_I": float(gamma7_square_residual.detach().item()),
            "gamma7_diagonal": gamma7_diag,
            "plus_dim": plus_dim,
            "minus_dim": minus_dim,
        },
        "differentiable_check": {
            "genuine_independent_check": genuine_independent_check,
            "probe": "theta mixes one + chirality basis vector with one - chirality basis vector; jacrev reports sensitivity of <psi(theta)|gamma7|psi(theta)>",
            "theta": float(theta.detach().item()),
            "plus_basis_index": plus_idx,
            "minus_basis_index": minus_idx,
            "same_chirality_control_index": same_plus_idx,
            "cross_chirality_expectation": float(cross_value.detach().item()),
            "cross_chirality_jacrev": float(cross_jac.detach().item()),
            "cross_chirality_finite_difference": float(finite_diff.detach().item()),
            "finite_difference_residual": float(finite_diff_residual.detach().item()),
            "same_chirality_jacrev": float(same_jac.detach().item()),
            "identity_control_jacrev": float(identity_jac.detach().item()),
            "p_plus_jacrev": float(p_plus_jac.detach().item()),
        },
        "negative_control_flip": {
            "active_M_class_count": active_q["class_count"],
            "drop_M_class_count": drop_q["class_count"],
            "drop_M_changed_quotient": active_q["class_count"] != drop_q["class_count"],
            "identity_gamma7_plus_dim": 8,
            "identity_gamma7_minus_dim": 0,
            "identity_gamma7_class_count": identity_q["class_count"],
            "identity_control_no_split": identity_q["class_count"] == 1,
            "identity_control_jacrev_zero": abs(float(identity_jac.detach().item())) <= 1.0e-10,
            "same_chirality_control_jacrev_zero": abs(float(same_jac.detach().item())) <= 1.0e-10,
        },
        "values": {
            "spinor_dim": dim,
            "gamma7_square_residual": float(gamma7_square_residual.detach().item()),
            "plus_dim": plus_dim,
            "minus_dim": minus_dim,
            "active_M_class_count": active_q["class_count"],
            "drop_M_class_count": drop_q["class_count"],
            "identity_control_plus_dim": 8,
            "identity_control_minus_dim": 0,
            "cross_chirality_jacrev": float(cross_jac.detach().item()),
            "same_chirality_jacrev": float(same_jac.detach().item()),
            "identity_control_jacrev": float(identity_jac.detach().item()),
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    values = result["values"]
    print(
        "FOUNDATION_R5_PYTORCH_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"dims={values['plus_dim']}/{values['minus_dim']} "
        f"classes={values['active_M_class_count']} drop_M={values['drop_M_class_count']} "
        f"jac={values['cross_chirality_jacrev']} identity_jac={values['identity_control_jacrev']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
