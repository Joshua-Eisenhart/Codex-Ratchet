#!/usr/bin/env python3
"""PyTorch torch.func leg for foundation_r3_associator_xhigh.

Scratch diagnostic only. This is a differentiable sensitivity check: it scans
the octonion witness, embeds H in the O carrier dimension, interpolates the
multiplication table from H-embedded to O, and jacrev differentiates the
associator energy along that selector.
"""

from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

import torch
from torch.func import jacrev


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r3_associator_xhigh"
CANONICAL_RUNG_ID = "foundation_r3_associator"
OBJECT_ID = "foundation_r3_associator_xhigh_pytorch"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_r3_associator_xhigh_pytorch.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_r3_associator_xhigh_pytorch_results.json"
TOL = 1.0e-12
NONZERO_TOL = 1.0e-9

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
        "reason": "supportive float64 tensor substrate for differentiable finite table arithmetic",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "load-bearing jacrev sensitivity of associator energy along the algebra-selector interpolation",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON receipt, path, and timestamp handling",
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
    h_embedded = torch.zeros_like(octonion)
    h_embedded[:4, :4, :4] = quaternion
    return {"H": quaternion, "H_embedded_in_O": h_embedded, "O": octonion}


def associator_vector(table: torch.Tensor, x: torch.Tensor, y: torch.Tensor, z: torch.Tensor) -> torch.Tensor:
    return multiply(table, multiply(table, x, y), z) - multiply(table, x, multiply(table, y, z))


def associator_scan(table: torch.Tensor) -> dict[str, Any]:
    dim = table.shape[0]
    max_norm = 0.0
    witness = [0, 0, 0]
    witness_vec = torch.zeros(dim, dtype=torch.float64)
    nonzero_count = 0
    for a in range(dim):
        ea = basis_vector(dim, a)
        for b in range(dim):
            eb = basis_vector(dim, b)
            for c in range(dim):
                ec = basis_vector(dim, c)
                assoc = associator_vector(table, ea, eb, ec)
                residual = as_float(torch.linalg.vector_norm(assoc))
                if residual > NONZERO_TOL:
                    nonzero_count += 1
                if residual > max_norm:
                    max_norm = residual
                    witness = [a, b, c]
                    witness_vec = assoc.detach().clone()
    return {
        "dim": dim,
        "max_norm": max_norm,
        "associative": max_norm <= TOL,
        "nonzero_basis_triple_count": nonzero_count,
        "witness_basis_indices": witness,
        "witness_expression_ids": [f"(e{witness[0]}*e{witness[1]})*e{witness[2]}", f"e{witness[0]}*(e{witness[1]}*e{witness[2]})"],
        "witness_vector": [as_float(x) for x in witness_vec],
    }


def state_constraint_checks(dim: int) -> dict[str, Any]:
    eye = torch.eye(dim, dtype=torch.float64)
    projectors = eye[:, :, None] * eye[:, None, :]
    traces = torch.diagonal(projectors, dim1=1, dim2=2).sum(dim=1)
    hermitian_residual = torch.max(torch.abs(projectors - projectors.transpose(1, 2)))
    eigvals = torch.linalg.eigvalsh(projectors)
    norms = torch.linalg.vector_norm(eye, dim=1)
    return {
        "basis_projector_count": dim,
        "trace_one_max_residual": as_float(torch.max(torch.abs(traces - 1.0))),
        "hermiticity_max_residual": as_float(hermitian_residual),
        "psd_min_eigenvalue": as_float(torch.min(eigvals)),
        "normalization_max_residual": as_float(torch.max(torch.abs(norms - 1.0))),
    }


def selector_table(alpha: torch.Tensor, h_embedded: torch.Tensor, octonion: torch.Tensor) -> torch.Tensor:
    return (1.0 - alpha) * h_embedded + alpha * octonion


def build_result() -> dict[str, Any]:
    torch.set_default_dtype(torch.float64)
    tables = build_tables()
    h_scan = associator_scan(tables["H"])
    o_scan = associator_scan(tables["O"])
    witness = o_scan["witness_basis_indices"]
    dim = tables["O"].shape[0]
    ea, eb, ec = [basis_vector(dim, idx) for idx in witness]

    def associator_energy(alpha: torch.Tensor) -> torch.Tensor:
        table = selector_table(alpha, tables["H_embedded_in_O"], tables["O"])
        assoc = associator_vector(table, ea, eb, ec)
        return torch.dot(assoc, assoc)

    alpha_h = torch.tensor(0.0, dtype=torch.float64)
    alpha_mid = torch.tensor(0.5, dtype=torch.float64)
    alpha_o = torch.tensor(1.0, dtype=torch.float64)
    energy_h = associator_energy(alpha_h)
    energy_mid = associator_energy(alpha_mid)
    energy_o = associator_energy(alpha_o)
    jac_h = jacrev(associator_energy)(alpha_h)
    jac_mid = jacrev(associator_energy)(alpha_mid)
    jac_o = jacrev(associator_energy)(alpha_o)

    grid_alphas = [0.0, 0.25, 0.5, 0.75, 1.0]
    grid = []
    for value in grid_alphas:
        alpha = torch.tensor(value, dtype=torch.float64)
        energy = associator_energy(alpha)
        grid.append(
            {
                "alpha": value,
                "associator_energy": as_float(energy),
                "associator_norm": as_float(torch.sqrt(torch.clamp(energy, min=0.0))),
            }
        )
    monotone_grid = all(grid[idx]["associator_energy"] <= grid[idx + 1]["associator_energy"] + TOL for idx in range(len(grid) - 1))

    h_norm = float(h_scan["max_norm"])
    o_norm = float(o_scan["max_norm"])
    gradient_check = {
        "expression": "E(alpha)=||[(e_a,e_b,e_c)]_{(1-alpha)H_embedded + alpha O}||^2 at the computed O witness triple",
        "witness_basis_indices": witness,
        "energy_alpha_0": as_float(energy_h),
        "energy_alpha_0_5": as_float(energy_mid),
        "energy_alpha_1": as_float(energy_o),
        "jacrev_alpha_0": as_float(jac_h),
        "jacrev_alpha_0_5": as_float(jac_mid),
        "jacrev_alpha_1": as_float(jac_o),
        "norm_grid": grid,
        "monotone_energy_grid": monotone_grid,
    }
    genuine_independent_check = bool(
        gradient_check["energy_alpha_0"] <= TOL
        and gradient_check["energy_alpha_1"] > NONZERO_TOL
        and abs(gradient_check["jacrev_alpha_0"]) <= TOL
        and gradient_check["jacrev_alpha_1"] > NONZERO_TOL
        and monotone_grid
    )
    all_pass = bool(
        h_norm <= TOL
        and o_norm > NONZERO_TOL
        and genuine_independent_check
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
        and reads_peer_result is False
    )

    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "rung_id": RUNG_ID,
        "canonical_rung_id": CANONICAL_RUNG_ID,
        "hardening_variant": "xhigh_v3_solver_derived_associator",
        "object_id": OBJECT_ID,
        "engine": "pytorch",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "packages_used": ["torch", "torch.func", "json", "pathlib"],
        "aligned_packages_load_bearing": ["torch.func"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "runtime_preflight": {
            "sys_executable": sys.executable,
            "torch_version": torch.__version__,
            "torch_default_dtype": str(torch.get_default_dtype()),
        },
        "M": {
            "name": "bracketing_distinguishability_probe",
            "probe_family": ["associator[A,B,C] = (AB)C - A(BC)"],
            "differentiated_probe": "associator energy at the computed O witness triple",
        },
        "C": {
            "trace_one": "basis probes are represented as rank-one coordinate projectors rho=|e_i><e_i| with trace 1",
            "psd": "rank-one coordinate projectors are positive semidefinite",
            "hermitian": "rank-one coordinate projectors are real symmetric/Hermitian",
            "normalization": "basis probes have unit Euclidean norm",
            "rung_specific_constraint": "Cayley-Dickson H/O multiplication tables, with H embedded in O dimension for a differentiable algebra selector",
            "dtype": "torch.float64",
            "finite_projector_checks": {"H": state_constraint_checks(4), "O": state_constraint_checks(8)},
        },
        "S_mod_M": {
            "definition": "(AB)C ~_M A(BC) iff the associator vector is zero",
            "H_bracketing_classes_under_M": 1 if h_norm <= TOL else 2,
            "O_witness_bracketing_classes_under_M": 2 if o_norm > NONZERO_TOL else 1,
            "drop_M_bracketing_classes": 1,
        },
        "summaries": {"H": h_scan, "O": o_scan},
        "differentiable_associator_selector": gradient_check,
        "negative_control_flip": {
            "H_to_O_flip": h_norm <= TOL and o_norm > NONZERO_TOL,
            "drop_M_coarsens_O_witness_quotient": o_norm > NONZERO_TOL,
            "torch_func_jacrev_independent_sensitivity": genuine_independent_check,
        },
        "summary": {
            "H_associator_max_norm": h_norm,
            "O_associator_max_norm": o_norm,
            "O_witness_basis_indices": witness,
            "O_witness_vector": o_scan["witness_vector"],
            "jacrev_alpha_0": gradient_check["jacrev_alpha_0"],
            "jacrev_alpha_1": gradient_check["jacrev_alpha_1"],
        },
        "torch_leg_genuine_independent_check": genuine_independent_check,
        "torch_leg_limit": "PyTorch is not exact algebra authority here; it supplies a float64 torch.func.jacrev sensitivity check tied to the associator claim.",
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "FOUNDATION_R3_ASSOCIATOR_XHIGH_PYTORCH_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"H_norm={result['summary']['H_associator_max_norm']} "
        f"O_norm={result['summary']['O_associator_max_norm']} "
        f"O_witness={result['summary']['O_witness_basis_indices']} "
        f"jac0={result['summary']['jacrev_alpha_0']} "
        f"jac1={result['summary']['jacrev_alpha_1']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
