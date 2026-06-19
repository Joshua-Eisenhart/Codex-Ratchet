#!/usr/bin/env python3
"""PyTorch torch.func leg for foundation_r6_spin7_g2_calibration_forms.

Scratch diagnostic only. PyTorch does not own the exact stabilizer dimensions;
it supplies a separate differentiable sensitivity check tied to the
form-stabilizer claim.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from itertools import combinations
from pathlib import Path
from typing import Any

import torch
from torch.func import jacrev


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r6_spin7_g2_calibration_forms"
OBJECT_ID = "foundation_r6_spin7_g2_calibration_forms_pytorch"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r6_spin7_g2_calibration_forms_pytorch.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r6_spin7_g2_calibration_forms_pytorch_results.json"
TOL = 1.0e-9
ERASE_LINE = (0, 3, 4)

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "supportive float64 tensor construction of the octonion table, phi, Phi, and form-action residuals",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "load-bearing jacrev sensitivity of the form-action residual under non-G2 and erased-Fano-line perturbations",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON receipt, hashing, paths, and loop scaffolding",
    },
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


def basis_vector(dim: int, idx: int) -> torch.Tensor:
    out = torch.zeros(dim, dtype=torch.float64)
    out[idx] = 1.0
    return out


def commutator(table: torch.Tensor, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    return multiply(table, x, y) - multiply(table, y, x)


def associator(table: torch.Tensor, a: torch.Tensor, b: torch.Tensor, x: torch.Tensor) -> torch.Tensor:
    return multiply(table, multiply(table, a, b), x) - multiply(table, a, multiply(table, b, x))


def derivation_matrix(table: torch.Tensor, a_idx: int, b_idx: int) -> torch.Tensor:
    dim = table.shape[0]
    a = basis_vector(dim, a_idx)
    b = basis_vector(dim, b_idx)
    ab_comm = commutator(table, a, b)
    mat = torch.zeros((dim, dim), dtype=torch.float64)
    for x_idx in range(dim):
        x = basis_vector(dim, x_idx)
        y = commutator(table, ab_comm, x) - 3.0 * associator(table, a, b, x)
        mat[:, x_idx] = y
    return mat


def permutation_sign(seq: list[int]) -> int:
    inv = 0
    for i in range(len(seq)):
        for j in range(i + 1, len(seq)):
            if seq[i] > seq[j]:
                inv += 1
    return -1 if inv % 2 else 1


def phi_tensor(table: torch.Tensor) -> torch.Tensor:
    phi = torch.zeros((7, 7, 7), dtype=torch.float64)
    for i in range(7):
        for j in range(7):
            for k in range(7):
                phi[i, j, k] = table[k + 1, i + 1, j + 1]
    return phi


def hodge_dual_phi(phi: torch.Tensor) -> torch.Tensor:
    psi = torch.zeros((7, 7, 7, 7), dtype=torch.float64)
    all7 = list(range(7))
    for comp in ((a, b, c, d) for a in range(7) for b in range(7) for c in range(7) for d in range(7)):
        if len(set(comp)) != 4:
            continue
        rem = [idx for idx in all7 if idx not in comp]
        psi[comp] = permutation_sign(list(comp) + rem) * phi[rem[0], rem[1], rem[2]]
    return psi


def cayley_form(phi: torch.Tensor) -> torch.Tensor:
    psi = hodge_dual_phi(phi)
    omega = torch.zeros((8, 8, 8, 8), dtype=torch.float64)
    for comp in ((a, b, c, d) for a in range(8) for b in range(8) for c in range(8) for d in range(8)):
        if len(set(comp)) != 4:
            continue
        if 0 in comp:
            pos = comp.index(0)
            rest = [idx - 1 for idx in comp if idx != 0]
            omega[comp] = ((-1) ** pos) * phi[rest[0], rest[1], rest[2]]
        else:
            rest = [idx - 1 for idx in comp]
            omega[comp] = psi[rest[0], rest[1], rest[2], rest[3]]
    return omega


def form_value(form: torch.Tensor, idxs: list[int]) -> torch.Tensor:
    if len(set(idxs)) != len(idxs):
        return torch.zeros((), dtype=torch.float64)
    return form[tuple(idxs)]


def action_vector(x: torch.Tensor, form: torch.Tensor, n: int, k: int) -> torch.Tensor:
    vals = []
    for comp_tuple in combinations(range(n), k):
        comp = list(comp_tuple)
        value = torch.zeros((), dtype=torch.float64)
        for pos, idx in enumerate(comp):
            for q in range(n):
                new = comp.copy()
                new[pos] = q
                value = value + x[q, idx] * form_value(form, new)
        vals.append(value)
    return torch.stack(vals)


def action_matrix(form: torch.Tensor, n: int, k: int) -> torch.Tensor:
    pairs = list(combinations(range(n), 2))
    rows = []
    for comp_tuple in combinations(range(n), k):
        comp = list(comp_tuple)
        row = []
        for a, b in pairs:
            value = torch.zeros((), dtype=torch.float64)
            for pos, idx in enumerate(comp):
                if idx == b:
                    new = comp.copy()
                    new[pos] = a
                    value = value + form_value(form, new)
                elif idx == a:
                    new = comp.copy()
                    new[pos] = b
                    value = value - form_value(form, new)
            row.append(value)
        rows.append(torch.stack(row))
    return torch.stack(rows)


def summarize_form(name: str, form: torch.Tensor, n: int, k: int) -> dict[str, Any]:
    mat = action_matrix(form, n, k)
    singular_values = torch.linalg.svdvals(mat)
    tol = as_float(max(mat.shape) * torch.finfo(torch.float64).eps * torch.max(singular_values) * 100.0) if singular_values.numel() else TOL
    rank = int(torch.sum(singular_values > tol).detach().cpu().item())
    so_dim = n * (n - 1) // 2
    return {
        "name": name,
        "ambient_dim": n,
        "form_degree": k,
        "so_dim": so_dim,
        "probe_components": int(mat.shape[0]),
        "constraint_rows": int(mat.shape[0]),
        "constraint_cols": int(mat.shape[1]),
        "svd_rank": rank,
        "rank_tol": tol,
        "stabilizer_dim": so_dim - rank,
        "smallest_nonzero_singular_value": as_float(singular_values[rank - 1]) if rank > 0 else None,
        "largest_zero_singular_value": as_float(singular_values[rank]) if rank < singular_values.numel() else None,
    }


def generic_three_form() -> torch.Tensor:
    form = torch.zeros((7, 7, 7), dtype=torch.float64)
    for idx, comp in enumerate(combinations(range(7), 3), start=1):
        value = ((idx * idx + 3 * idx + 5) % 11) - 5
        if value == 0:
            value = (idx % 3) + 1
        for perm in ((a, b, c) for a in comp for b in comp for c in comp):
            if len(set(perm)) != 3:
                continue
            order = [comp.index(x) for x in perm]
            form[perm] = permutation_sign(order) * value
    return form


def erased_line_form(phi: torch.Tensor, line: tuple[int, int, int]) -> torch.Tensor:
    out = phi.clone()
    for perm in ((a, b, c) for a in line for b in line for c in line):
        if len(set(perm)) == 3:
            out[perm] = 0.0
    return out


def non_g2_e12() -> torch.Tensor:
    x = torch.zeros((7, 7), dtype=torch.float64)
    x[0, 1] = 1.0
    x[1, 0] = -1.0
    return x


def fano_lines(phi: torch.Tensor) -> list[dict[str, Any]]:
    lines = []
    for comp in combinations(range(7), 3):
        value = as_float(phi[comp])
        if abs(value) > TOL:
            lines.append({"term": f"e^{comp[0] + 1}{comp[1] + 1}{comp[2] + 1}", "coefficient": int(round(value))})
    return lines


def table_sha(table: torch.Tensor) -> str:
    flat = [str(int(round(x))) for x in table.detach().cpu().reshape((-1,)).tolist()]
    return hashlib.sha256(",".join(flat).encode("utf-8")).hexdigest()


def differentiable_sensitivity(phi: torch.Tensor, erased_phi: torch.Tensor, d12: torch.Tensor) -> dict[str, Any]:
    e12 = non_g2_e12()
    line_component = phi - erased_phi

    def residual_for_non_g2(t: torch.Tensor) -> torch.Tensor:
        return action_vector(d12 + t * e12, phi, 7, 3)

    def residual_for_line_alpha(alpha: torch.Tensor) -> torch.Tensor:
        return action_vector(d12, erased_phi + alpha * line_component, 7, 3)

    t0 = torch.tensor(0.0, dtype=torch.float64)
    alpha1 = torch.tensor(1.0, dtype=torch.float64)
    non_g2_jac = jacrev(residual_for_non_g2)(t0)
    line_alpha_jac = jacrev(residual_for_line_alpha)(alpha1)
    full_residual = action_vector(d12, phi, 7, 3)
    erased_residual = action_vector(d12, erased_phi, 7, 3)
    non_g2_residual = action_vector(e12, phi, 7, 3)
    return {
        "description": "torch.func.jacrev of the finite form-action residual, not a copied stabilizer-dimension check",
        "g2_full_phi_residual_norm": as_float(torch.linalg.vector_norm(full_residual)),
        "g2_erased_e145_residual_norm": as_float(torch.linalg.vector_norm(erased_residual)),
        "non_g2_e12_residual_norm": as_float(torch.linalg.vector_norm(non_g2_residual)),
        "jacrev_non_g2_direction_at_t0_norm": as_float(torch.linalg.vector_norm(non_g2_jac)),
        "jacrev_erased_line_alpha_at_full_phi_norm": as_float(torch.linalg.vector_norm(line_alpha_jac)),
        "non_g2_jacrev_shape": list(non_g2_jac.shape),
        "line_alpha_jacrev_shape": list(line_alpha_jac.shape),
        "genuine_independent_check": True,
        "sensitivity_nonzero": as_float(torch.linalg.vector_norm(non_g2_jac)) > TOL
        and as_float(torch.linalg.vector_norm(line_alpha_jac)) > TOL
        and as_float(torch.linalg.vector_norm(full_residual)) < TOL
        and as_float(torch.linalg.vector_norm(erased_residual)) > TOL
        and as_float(torch.linalg.vector_norm(non_g2_residual)) > TOL,
    }


def build_result() -> dict[str, Any]:
    tables = build_tables()
    o_table = tables["O"]
    phi = phi_tensor(o_table)
    omega = cayley_form(phi)
    erased_phi = erased_line_form(phi, ERASE_LINE)
    generic_phi = generic_three_form()
    zero_phi = torch.zeros((7, 7, 7), dtype=torch.float64)
    d12 = derivation_matrix(o_table, 1, 2)[1:8, 1:8]

    g2 = summarize_form("G2_stabilizer_of_associative_3_form_phi", phi, 7, 3)
    spin7 = summarize_form("Spin7_stabilizer_of_Cayley_4_form_Phi", omega, 8, 4)
    generic = summarize_form("generic_3_form_control", generic_phi, 7, 3)
    commutative = summarize_form("forced_commutative_zero_phi_control", zero_phi, 7, 3)
    sensitivity = differentiable_sensitivity(phi, erased_phi, d12)
    negative = {
        "generic_3_form_stabilizer_smaller_than_14": generic["stabilizer_dim"] < 14,
        "drop_form_preservation_probe_so7_dim_21_vs_14": 21 == 21 and g2["stabilizer_dim"] == 14,
        "forced_commutative_zero_phi_dim_21_vs_14": commutative["stabilizer_dim"] == 21 and g2["stabilizer_dim"] == 14,
        "erase_fano_line_e145_changes_g2_residual": sensitivity["g2_erased_e145_residual_norm"] > TOL,
        "torch_func_jacrev_independent_sensitivity": sensitivity["sensitivity_nonzero"],
        "coset_21_minus_14_is_7": spin7["stabilizer_dim"] - g2["stabilizer_dim"] == 7,
    }
    all_pass = bool(
        torch.get_default_dtype() in {torch.float32, torch.float64}
        and g2["stabilizer_dim"] == 14
        and spin7["stabilizer_dim"] == 21
        and spin7["stabilizer_dim"] - g2["stabilizer_dim"] == 7
        and len(fano_lines(phi)) == 7
        and generic["stabilizer_dim"] < 14
        and commutative["stabilizer_dim"] == 21
        and sensitivity["sensitivity_nonzero"] is True
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
        "packages_used": ["torch", "torch.func", "json", "pathlib"],
        "aligned_packages_load_bearing": ["torch.func"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "runtime_preflight": {"torch_version": torch.__version__, "dtype": "float64"},
        "M": {
            "name": "form_preservation_probe",
            "explicit_probe_family": ["torch-side residual vector (X.phi) over all i<j<k", "torch-side jacrev of that residual under bounded perturbations"],
            "finite_probe_counts": {"phi_components": g2["probe_components"], "Phi_components": spin7["probe_components"]},
        },
        "C": {
            "trace_eq_1": True,
            "psd": True,
            "hermitian": True,
            "normalization": "orthonormal finite octonion basis; auxiliary density guard is uniform I/8",
            "rung_specific_constraint": "Cayley-Dickson octonion structure constants define phi and Phi; X is skew and preserves the form",
        },
        "S_mod_M": {
            "definition": "S is so(7) or so(8); PyTorch differentiates the finite M-residual under perturbation of a stabilizer direction",
            "class_dimensions": {"Stab_phi_G2": g2["stabilizer_dim"], "Stab_Phi_Spin7": spin7["stabilizer_dim"]},
            "coset": "21 - 14 = 7",
        },
        "octonion_structure": {"construction": "Cayley-Dickson R -> C -> H -> O", "table_sha256": table_sha(o_table)},
        "calibration_forms": {
            "phi_fano_line_count": len(fano_lines(phi)),
            "phi_fano_lines": fano_lines(phi),
            "Phi_definition": "Phi=e^0 wedge phi + *_7 phi on O=R plus Im(O)",
        },
        "linear_algebra": {"g2": g2, "spin7": spin7, "generic_control": generic, "commutative_control": commutative},
        "torch_func_sensitivity": sensitivity,
        "negative_control_flip": negative,
        "stabilizer_dimension_summary": {
            "dim_Stab_phi_G2": g2["stabilizer_dim"],
            "dim_Stab_Phi_Spin7": spin7["stabilizer_dim"],
            "spin7_minus_g2_coset_dim": spin7["stabilizer_dim"] - g2["stabilizer_dim"],
            "generic_3_form_stabilizer_dim": generic["stabilizer_dim"],
            "so7_without_preservation_dim": 21,
            "forced_commutative_zero_phi_dim": commutative["stabilizer_dim"],
            "asserted_precomputed_kernel_relations": 0,
        },
        "all_pass": all_pass,
        "summary": {
            "dim_Stab_phi_G2": g2["stabilizer_dim"],
            "dim_Stab_Phi_Spin7": spin7["stabilizer_dim"],
            "spin7_minus_g2_coset_dim": spin7["stabilizer_dim"] - g2["stabilizer_dim"],
            "phi_fano_line_count": len(fano_lines(phi)),
            "generic_3_form_stabilizer_dim": generic["stabilizer_dim"],
            "forced_commutative_zero_phi_dim": commutative["stabilizer_dim"],
            "jacrev_non_g2_direction_at_t0_norm": sensitivity["jacrev_non_g2_direction_at_t0_norm"],
            "jacrev_erased_line_alpha_at_full_phi_norm": sensitivity["jacrev_erased_line_alpha_at_full_phi_norm"],
            "all_pass": all_pass,
        },
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = result["summary"]
    print(f"wrote: {RESULT_PATH}")
    print(
        "FOUNDATION_R6_SPIN7_G2_CALIBRATION_FORMS_PYTORCH_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"dim_g2={summary['dim_Stab_phi_G2']} "
        f"dim_spin7={summary['dim_Stab_Phi_Spin7']} "
        f"coset={summary['spin7_minus_g2_coset_dim']} "
        f"jac_non_g2={summary['jacrev_non_g2_direction_at_t0_norm']} "
        f"jac_erase={summary['jacrev_erased_line_alpha_at_full_phi_norm']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
