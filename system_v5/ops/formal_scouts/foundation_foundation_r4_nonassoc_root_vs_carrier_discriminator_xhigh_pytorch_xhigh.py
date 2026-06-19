#!/usr/bin/env python3
"""PyTorch torch.func sensitivity leg for foundation R4 nonassoc root-vs-carrier discriminator."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any

import torch
from torch.func import jacrev


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r4_nonassoc_root_vs_carrier_discriminator_xhigh"
OBJECT_ID = RUNG_ID
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_xhigh_pytorch_xhigh.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_xhigh_pytorch_xhigh_results.json"
DTYPE = torch.float64
TOL = 1.0e-9

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing differentiable Cayley-Dickson tensor and matrix probes in float64",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "load-bearing jacrev sensitivity of the H noncommutator and O Cl(0,6) anticommutator residuals",
    },
}

TOOL_INTEGRATION_DEPTH = {"torch": "load_bearing", "torch.func": "load_bearing"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def py_float(value: torch.Tensor) -> float:
    return float(value.detach().cpu().item())


def cd_conj(x: torch.Tensor) -> torch.Tensor:
    if x.shape[0] == 1:
        return x
    signs = torch.cat([torch.ones(1, dtype=DTYPE), -torch.ones(x.shape[0] - 1, dtype=DTYPE)])
    return x * signs


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


def multiplication_table(dim: int) -> torch.Tensor:
    table = torch.zeros((dim, dim, dim), dtype=DTYPE)
    for i in range(dim):
        for j in range(dim):
            table[:, i, j] = cd_mul(basis(dim, i), basis(dim, j))
    return table


def left_matrix(table: torch.Tensor, unit_idx: int) -> torch.Tensor:
    dim = int(table.shape[0])
    mat = torch.zeros((dim, dim), dtype=DTYPE)
    for col in range(dim):
        mat[:, col] = table[:, unit_idx, col]
    return mat


def left_matrices(table: torch.Tensor) -> list[torch.Tensor]:
    return [left_matrix(table, idx) for idx in range(1, int(table.shape[0]))]


def square_minus_one(table: torch.Tensor, idx: int) -> bool:
    dim = int(table.shape[0])
    return abs(py_float(table[0, idx, idx]) + 1.0) <= TOL and all(abs(py_float(table[k, idx, idx])) <= TOL for k in range(1, dim))


def anticommutes(table: torch.Tensor, i: int, j: int) -> bool:
    return py_float(torch.linalg.norm(table[:, i, j] + table[:, j, i])) <= TOL


def carrier_numeric_summary(name: str, dim: int) -> dict[str, Any]:
    table = multiplication_table(dim)
    imaginary = list(range(1, dim))
    valid = [idx for idx in imaginary if square_minus_one(table, idx)]
    pair_failures = [(i, j) for i in valid for j in valid if i < j and not anticommutes(table, i, j)]
    max_comm = 0.0
    witness = None
    for i in imaginary:
        for j in imaginary:
            if i >= j:
                continue
            comm = table[:, i, j] - table[:, j, i]
            norm_value = py_float(torch.linalg.norm(comm))
            if norm_value > max_comm:
                max_comm = norm_value
                witness = {"i": i, "j": j, "commutator_norm": norm_value}
    count = len(valid) if not pair_failures else 0
    return {
        "name": name,
        "real_dimension": dim,
        "finite": True,
        "imaginary_unit_count": count,
        "valid_imaginary_indices": valid,
        "pair_failures": pair_failures,
        "noncommutation": {"max_norm": max_comm, "witness": witness, "noncommutative": max_comm > TOL},
        "bare_root_admissible": dim >= 4 and max_comm > TOL,
        "cl6_7unit_admissible": count >= 7,
    }


def h_noncommutator_vector(scales: torch.Tensor, h_table: torch.Tensor) -> torch.Tensor:
    # [s1*e1, s2*e2] in H, expressed by structure constants.
    e1_e2 = h_table[:, 1, 2]
    e2_e1 = h_table[:, 2, 1]
    return scales[0] * scales[1] * (e1_e2 - e2_e1)


def o_cl6_anticommutator_residual(scales: torch.Tensor, o_mats: tuple[torch.Tensor, ...]) -> torch.Tensor:
    mats = [scales[idx] * o_mats[idx] for idx in range(7)]
    dim = int(mats[0].shape[0])
    rows: list[torch.Tensor] = []
    for i, left in enumerate(mats):
        for j, right in enumerate(mats):
            target = -2.0 * torch.eye(dim, dtype=DTYPE) if i == j else torch.zeros((dim, dim), dtype=DTYPE)
            rows.append((left @ right + right @ left - target).reshape(-1))
    return torch.cat(rows)


def jacrev_sensitivity() -> dict[str, Any]:
    h_table = multiplication_table(4)
    o_table = multiplication_table(8)
    o_mats = tuple(left_matrices(o_table))

    h_scales = torch.ones(2, dtype=DTYPE)
    h_value = h_noncommutator_vector(h_scales, h_table)
    h_jac = jacrev(lambda scales: h_noncommutator_vector(scales, h_table))(h_scales)
    h_eps = torch.tensor(1.0e-5, dtype=DTYPE)
    h_perturbed = h_scales.clone()
    h_perturbed[0] = h_perturbed[0] + h_eps
    h_fd = (h_noncommutator_vector(h_perturbed, h_table) - h_value) / h_eps
    h_fd_residual = py_float(torch.linalg.norm(h_fd - h_jac[:, 0]))

    o_scales = torch.ones(7, dtype=DTYPE)
    o_value = o_cl6_anticommutator_residual(o_scales, o_mats)
    o_jac = jacrev(lambda scales: o_cl6_anticommutator_residual(scales, o_mats))(o_scales)

    def residual_index(i: int, j: int, row: int, col: int) -> int:
        return (((i * 7 + j) * 8 + row) * 8) + col

    o_self_diag = [py_float(o_jac[residual_index(i, i, 0, 0), i]) for i in range(7)]
    o_eps = torch.tensor(1.0e-5, dtype=DTYPE)
    o_perturbed = o_scales.clone()
    o_perturbed[0] = o_perturbed[0] + o_eps
    o_fd = (o_cl6_anticommutator_residual(o_perturbed, o_mats)[residual_index(0, 0, 0, 0)] - o_value[residual_index(0, 0, 0, 0)]) / o_eps
    o_fd_residual = abs(py_float(o_fd) - o_self_diag[0])

    return {
        "tool": "torch.func.jacrev",
        "genuine_independent_check": True,
        "honest_limit": "The discrete >=7-unit SAT/UNSAT exclusion is not differentiable; PyTorch independently checks sensitivity of the H bare-root noncommutator and O Cl(0,6) anticommutator equations.",
        "H_bare_noncommutator": {
            "observable": "[s1*e1, s2*e2] in H from structure constants",
            "value_norm": py_float(torch.linalg.norm(h_value)),
            "jacobian_shape": list(h_jac.shape),
            "jacobian_frobenius_norm": py_float(torch.linalg.norm(h_jac)),
            "finite_difference_vs_jacrev_residual": h_fd_residual,
            "pass": py_float(torch.linalg.norm(h_value)) > 0.0 and py_float(torch.linalg.norm(h_jac)) > 0.0 and h_fd_residual <= 1.0e-8,
        },
        "O_cl6_anticommutator": {
            "observable": "Jacobian of all seven O left-action anticommutator residuals with respect to generator scales",
            "residual_vector_length": int(o_value.numel()),
            "base_residual_max_abs": py_float(torch.max(torch.abs(o_value))),
            "jacobian_shape": list(o_jac.shape),
            "jacobian_frobenius_norm": py_float(torch.linalg.norm(o_jac)),
            "self_diagonal_sensitivities": o_self_diag,
            "expected_self_diagonal_sensitivity": -4.0,
            "finite_difference_sensitivity_L1": py_float(o_fd),
            "finite_difference_vs_jacrev_abs_residual": o_fd_residual,
            "pass": py_float(torch.max(torch.abs(o_value))) <= TOL
            and py_float(torch.linalg.norm(o_jac)) > 0.0
            and all(abs(value + 4.0) <= 1.0e-9 for value in o_self_diag)
            and o_fd_residual <= 1.0e-3,
        },
    }


def quotient_summary(carriers: dict[str, dict[str, Any]]) -> dict[str, Any]:
    names = ["R", "C", "H", "O"]
    full_signatures = {
        name: (
            f"finite={row['finite']};noncomm={row['noncommutation']['noncommutative']};"
            f"dim={row['real_dimension']};imaginary_units={row['imaginary_unit_count']};cl6={row['cl6_7unit_admissible']}"
        )
        for name, row in carriers.items()
    }
    coarse_signatures = {name: f"finite={row['finite']};noncomm={row['noncommutation']['noncommutative']}" for name, row in carriers.items()}
    return {
        "S": names,
        "equivalence_relation": "a ~_M b iff finite root probe signatures match",
        "bare_root_admitted_carriers": [name for name in names if carriers[name]["bare_root_admissible"]],
        "strong_cl6_7unit_admitted_carriers": [name for name in names if carriers[name]["cl6_7unit_admissible"]],
        "full_probe_signatures": full_signatures,
        "coarse_signatures_after_dropping_dimension_unit_and_cl6_probes": coarse_signatures,
        "full_probe_class_count": len(set(full_signatures.values())),
        "coarse_probe_class_count": len(set(coarse_signatures.values())),
        "drop_probe_coarsening_flip": {
            "dropped_probes": ["carrier_dimension", "imaginary_unit_count", "cl6_7unit_capacity"],
            "before_class_count": len(set(full_signatures.values())),
            "after_class_count": len(set(coarse_signatures.values())),
            "flips": len(set(full_signatures.values())) != len(set(coarse_signatures.values())),
        },
    }


def build_result() -> dict[str, Any]:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    torch.set_default_dtype(DTYPE)
    carriers = {
        "R": carrier_numeric_summary("R", 1),
        "C": carrier_numeric_summary("C", 2),
        "H": carrier_numeric_summary("H", 4),
        "O": carrier_numeric_summary("O", 8),
    }
    unit_counts = {name: carriers[name]["imaginary_unit_count"] for name in ["R", "C", "H", "O"]}
    quotient = quotient_summary(carriers)
    sensitivity = jacrev_sensitivity()
    h_bare = carriers["H"]["bare_root_admissible"]
    h_cl6 = carriers["H"]["cl6_7unit_admissible"]
    o_cl6 = carriers["O"]["cl6_7unit_admissible"]
    all_pass = bool(
        unit_counts == {"R": 0, "C": 1, "H": 3, "O": 7}
        and h_bare
        and not h_cl6
        and o_cl6
        and quotient["drop_probe_coarsening_flip"]["flips"]
        and sensitivity["H_bare_noncommutator"]["pass"]
        and sensitivity["O_cl6_anticommutator"]["pass"]
    )
    return {
        "schema": "codex_ratchet.engine_leg.v1",
        "object_id": OBJECT_ID,
        "rung_id": RUNG_ID,
        "engine": "pytorch",
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "ran": True,
        "standalone": True,
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "torch_version": torch.__version__,
        "dtype": str(DTYPE),
        "claim_ceiling": "Scratch PyTorch torch.func sensitivity leg only; discrete forced-vs-installed verdict remains Julia/JAX-SMT bounded.",
        "M": {
            "name": "finite differentiable probes over H noncommutator and O Cl(0,6) anticommutator residuals",
            "probe_family": ["[s1*e1,s2*e2] in H", "O left-action anticommutator residual vector under generator scaling"],
        },
        "C": {
            "state_constraints": ["trace(rho)=1", "rho PSD", "rho Hermitian", "normalization"],
            "bare_root_constraints": ["finite table", "noncommuting [Z,X]-analog exists", "finite M quotient"],
            "rung_specific_stronger_constraint": ">=7 mutually anticommuting imaginary units / Cl(0,6) / 3-qubit Weyl floor",
        },
        "carriers": carriers,
        "quotient": quotient,
        "unit_counts": unit_counts,
        "torch_func_sensitivity": sensitivity,
        "negative_control_flip": {
            "drop_stronger_cl6_7unit_constraint": {
                "H_under_bare_root": "admitted",
                "H_under_cl6_7unit_constraint": "excluded",
                "flips": h_bare and not h_cl6,
            },
            "drop_probe_coarsening": quotient["drop_probe_coarsening_flip"],
        },
        "decision": {
            "H_bare_root_admissible": h_bare,
            "H_cl6_7unit_admissible": h_cl6,
            "O_cl6_7unit_admissible": o_cl6,
            "nonassoc_forced_by_bare_root": False,
            "nonassoc_installed_by_constraint": "Cl(0,6)/>=7 mutually anticommuting imaginary units/3-qubit Weyl floor",
            "forced_vs_installed_verdict": "INSTALLED_NOT_FORCED",
        },
        "summary": {
            "all_pass": all_pass,
            "unit_counts_R_C_H_O": [unit_counts["R"], unit_counts["C"], unit_counts["H"], unit_counts["O"]],
            "H_bare_root_admissible": h_bare,
            "H_cl6_7unit_admissible": h_cl6,
            "O_cl6_7unit_admissible": o_cl6,
            "H_noncommutator_jacobian_norm": sensitivity["H_bare_noncommutator"]["jacobian_frobenius_norm"],
            "O_cl6_jacobian_norm": sensitivity["O_cl6_anticommutator"]["jacobian_frobenius_norm"],
            "torch_check_genuine_independent": sensitivity["genuine_independent_check"],
            "torch_check_honest_limit": sensitivity["honest_limit"],
            "forced_vs_installed_verdict": "INSTALLED_NOT_FORCED",
        },
        "all_pass": all_pass,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    s = result["summary"]
    print(f"wrote: {RESULT_PATH}")
    print(
        "PYTORCH_DONE "
        f"all_pass={str(s['all_pass']).lower()} "
        f"unit_counts={s['unit_counts_R_C_H_O']} "
        f"H_bare={str(s['H_bare_root_admissible']).lower()} "
        f"H_cl6={str(s['H_cl6_7unit_admissible']).lower()} "
        f"O_cl6={str(s['O_cl6_7unit_admissible']).lower()} "
        f"H_jac_norm={s['H_noncommutator_jacobian_norm']:.6g} "
        f"O_jac_norm={s['O_cl6_jacobian_norm']:.6g} "
        f"verdict={s['forced_vs_installed_verdict']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
