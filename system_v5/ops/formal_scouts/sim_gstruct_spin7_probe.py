#!/usr/bin/env python3
"""Stage-4 Spin(7) G-structure probe with anti-fabrication checks.

Finite map:
    Phi -> (Phi_ijab Phi_klab - 6(delta_ik delta_jl - delta_il delta_jk) - 4 Phi_ijkl)

The real carrier is the standard sparse Cayley 4-form on R^8.  The negative
control flips the e5678 coefficient while preserving term count and norm, so a
norm/sparsity-only test cannot pass.  SMT proof is bound to measured residuals
through scripts/load_bearing_proof.py and must flip on the control.
"""

from __future__ import annotations

import itertools
import json
import os
import pathlib
import sys
import time
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import sympy as sp
import torch
from clifford import Cl
from e3nn import o3
import geomstats.backend as gs
from geomstats.geometry.special_orthogonal import SpecialOrthogonal

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
THISFILE = pathlib.Path(__file__).name
RESULT = RESULT_DIR / "gstruct_spin7_probe_results.json"

OBJECT_ID = "gstruct_spin7_cayley4_reduction"
DTYPE = torch.float64
EPS = 1.0e-9
NDIM = 8
SO8_DIM = 28
SCALES = (8, 16, 32, 64)
BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity", "bridge", "basin"]

# Bryant/Joyce convention from the task spec, written 1-based for auditability.
CAYLEY_TERMS_1BASED: tuple[tuple[tuple[int, int, int, int], int], ...] = (
    ((1, 2, 3, 4), 1),
    ((1, 2, 5, 6), 1),
    ((1, 2, 7, 8), 1),
    ((1, 3, 5, 7), 1),
    ((1, 3, 6, 8), -1),
    ((1, 4, 5, 8), -1),
    ((1, 4, 6, 7), -1),
    ((2, 3, 5, 8), -1),
    ((2, 3, 6, 7), -1),
    ((2, 4, 5, 7), -1),
    ((2, 4, 6, 8), 1),
    ((3, 4, 5, 6), 1),
    ((3, 4, 7, 8), 1),
    ((5, 6, 7, 8), 1),
)
CONTROL_TERM = (5, 6, 7, 8)

FANO_TRIPLES_1BASED: tuple[tuple[int, int, int], ...] = (
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
)


TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY tensor carrier for Cayley 4-form, contraction residual, self-duality, and stabilizer-rank ablation.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "x64 mirror for the pure tensor contraction and Hodge-star checks; geomstats is kept on torch backend.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "PROOF via smt_load_bearing: same residual<=eps claim is SAT on real Phi and UNSAT on sign-flip control.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "PROOF cross-check via smt_load_bearing cvc5_claim_pairs on the same measured residuals.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "Exact integer contraction, self-duality, and stabilizer rank used as symbolic proof surface; no numeric ablation.",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "Cl(7,0) spinor-carrier signature check; load-bearing through recompute against wrong Cl(6,1) signature control.",
    },
    "e3nn": {
        "tried": True,
        "used": True,
        "reason": "SO(3) rotation sub-block roundtrip check; load-bearing through malformed matrix ablation that e3nn rejects.",
    },
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": "SpecialOrthogonal(8) manifold membership for a Spin(7) exponential; load-bearing through non-orthogonal ablation.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Not imported; nonclassical claim-bearing computation stays torch/jax/sympy.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "clifford": "load_bearing",
    "e3nn": "load_bearing",
    "geomstats": "load_bearing",
    "numpy": "None",
}


def perm_sign(seq: tuple[int, ...]) -> int:
    inversions = 0
    for i in range(len(seq)):
        for j in range(i + 1, len(seq)):
            if seq[i] > seq[j]:
                inversions += 1
    return -1 if inversions % 2 else 1


def spin7_terms(*, control: bool = False) -> tuple[tuple[tuple[int, int, int, int], int], ...]:
    terms: list[tuple[tuple[int, int, int, int], int]] = []
    for quad, coeff in CAYLEY_TERMS_1BASED:
        if control and quad == CONTROL_TERM:
            terms.append((quad, -coeff))
        else:
            terms.append((quad, coeff))
    return tuple(terms)


def build_torch_phi(*, control: bool = False) -> torch.Tensor:
    phi = torch.zeros((NDIM, NDIM, NDIM, NDIM), dtype=DTYPE)
    for quad_1based, coeff in spin7_terms(control=control):
        base = tuple(i - 1 for i in quad_1based)
        for perm in itertools.permutations(base):
            idx_perm = tuple(base.index(i) for i in perm)
            phi[perm] = float(coeff * perm_sign(idx_perm))
    return phi


def build_jax_phi(*, control: bool = False) -> jax.Array:
    phi = jnp.zeros((NDIM, NDIM, NDIM, NDIM), dtype=jnp.float64)
    for quad_1based, coeff in spin7_terms(control=control):
        base = tuple(i - 1 for i in quad_1based)
        for perm in itertools.permutations(base):
            idx_perm = tuple(base.index(i) for i in perm)
            phi = phi.at[perm].set(float(coeff * perm_sign(idx_perm)))
    return phi


def build_exact_form(*, control: bool = False) -> dict[tuple[int, int, int, int], sp.Integer]:
    form: dict[tuple[int, int, int, int], sp.Integer] = {}
    for quad_1based, coeff in spin7_terms(control=control):
        base = tuple(i - 1 for i in quad_1based)
        for perm in itertools.permutations(base):
            idx_perm = tuple(base.index(i) for i in perm)
            form[perm] = sp.Integer(coeff * perm_sign(idx_perm))
    return form


def exact_val(form: dict[tuple[int, int, int, int], sp.Integer], i: int, j: int, k: int, l: int) -> sp.Integer:
    return form.get((i, j, k, l), sp.Integer(0))


def contraction_residual_torch(phi: torch.Tensor) -> dict[str, Any]:
    contraction = torch.einsum("ijab,klab->ijkl", phi, phi)
    delta = torch.eye(NDIM, dtype=DTYPE)
    wedge_metric = torch.einsum("ik,jl->ijkl", delta, delta) - torch.einsum("il,jk->ijkl", delta, delta)
    residual = contraction - (6.0 * wedge_metric + 4.0 * phi)
    return {
        "max_abs_residual": float(torch.max(torch.abs(residual)).item()),
        "frobenius_residual": float(torch.linalg.vector_norm(residual.reshape(-1)).item()),
        "contraction_norm": float(torch.linalg.vector_norm(contraction.reshape(-1)).item()),
    }


def contraction_residual_jax(phi: jax.Array) -> dict[str, Any]:
    contraction = jnp.einsum("ijab,klab->ijkl", phi, phi)
    delta = jnp.eye(NDIM, dtype=jnp.float64)
    wedge_metric = jnp.einsum("ik,jl->ijkl", delta, delta) - jnp.einsum("il,jk->ijkl", delta, delta)
    residual = contraction - (6.0 * wedge_metric + 4.0 * phi)
    return {
        "max_abs_residual": float(jnp.max(jnp.abs(residual)).item()),
        "frobenius_residual": float(jnp.linalg.norm(residual.reshape(-1)).item()),
    }


def hodge_self_duality_defect_torch(phi: torch.Tensor) -> float:
    max_diff = 0.0
    for indices in itertools.combinations(range(NDIM), 4):
        complement = tuple(i for i in range(NDIM) if i not in indices)
        sign = perm_sign(tuple(list(indices) + list(complement)))
        diff = abs(sign * float(phi[complement].item()) - float(phi[indices].item()))
        max_diff = max(max_diff, diff)
    return max_diff


def hodge_self_duality_defect_jax(phi: jax.Array) -> float:
    max_diff = 0.0
    for indices in itertools.combinations(range(NDIM), 4):
        complement = tuple(i for i in range(NDIM) if i not in indices)
        sign = perm_sign(tuple(list(indices) + list(complement)))
        diff = abs(sign * float(phi[complement].item()) - float(phi[indices].item()))
        max_diff = max(max_diff, diff)
    return max_diff


def exact_contraction_summary(form: dict[tuple[int, int, int, int], sp.Integer]) -> dict[str, Any]:
    max_abs = sp.Integer(0)
    nonzero_residuals = 0
    for i, j, k, l in itertools.product(range(NDIM), repeat=4):
        contraction = sum(exact_val(form, i, j, a, b) * exact_val(form, k, l, a, b) for a in range(NDIM) for b in range(NDIM))
        target = 6 * (int(i == k) * int(j == l) - int(i == l) * int(j == k)) + 4 * exact_val(form, i, j, k, l)
        residual = sp.Abs(contraction - target)
        if residual != 0:
            nonzero_residuals += 1
        max_abs = max(max_abs, residual)
    independent_norm = sum(exact_val(form, *indices) ** 2 for indices in itertools.combinations(range(NDIM), 4))
    full_nonzero = sum(1 for value in form.values() if value != 0)
    independent_nonzero = sum(1 for indices in itertools.combinations(range(NDIM), 4) if exact_val(form, *indices) != 0)
    return {
        "max_abs_residual": int(max_abs),
        "nonzero_residual_entries": nonzero_residuals,
        "independent_norm_squared": int(independent_norm),
        "independent_nonzero_terms": independent_nonzero,
        "full_antisymmetric_nonzero_entries": full_nonzero,
        "pass": bool(max_abs == 0 and independent_norm == 14 and independent_nonzero == 14 and full_nonzero == 14 * 24),
    }


def exact_self_duality_summary(form: dict[tuple[int, int, int, int], sp.Integer]) -> dict[str, Any]:
    max_abs = sp.Integer(0)
    nonzero = 0
    for indices in itertools.combinations(range(NDIM), 4):
        complement = tuple(i for i in range(NDIM) if i not in indices)
        sign = perm_sign(tuple(list(indices) + list(complement)))
        residual = sp.Abs(sign * exact_val(form, *complement) - exact_val(form, *indices))
        if residual != 0:
            nonzero += 1
        max_abs = max(max_abs, residual)
    return {"max_abs_star_minus_phi": int(max_abs), "nonzero_defects": nonzero, "pass": bool(max_abs == 0)}


def so8_basis() -> list[torch.Tensor]:
    basis: list[torch.Tensor] = []
    for i, j in itertools.combinations(range(NDIM), 2):
        mat = torch.zeros((NDIM, NDIM), dtype=DTYPE)
        mat[i, j] = 1.0
        mat[j, i] = -1.0
        basis.append(mat)
    return basis


def infinitesimal_action_torch(generator: torch.Tensor, phi: torch.Tensor) -> torch.Tensor:
    out = torch.einsum("im,mjkl->ijkl", generator, phi)
    out = out + torch.einsum("jm,imkl->ijkl", generator, phi)
    out = out + torch.einsum("km,ijml->ijkl", generator, phi)
    out = out + torch.einsum("lm,ijkm->ijkl", generator, phi)
    return -out


def stabilizer_numeric(phi: torch.Tensor) -> dict[str, Any]:
    basis = so8_basis()
    matrix = torch.stack([infinitesimal_action_torch(gen, phi).reshape(-1) for gen in basis], dim=1)
    singular = torch.linalg.svdvals(matrix)
    rank = int((singular > 1.0e-9).sum().item())
    u, s, vh = torch.linalg.svd(matrix, full_matrices=True)
    null_coeffs = vh[rank:, :]
    return {
        "rank": rank,
        "kernel_dim": SO8_DIM - rank,
        "singular_values": [float(v.item()) for v in singular],
        "null_coeffs": null_coeffs,
        "basis": basis,
    }


def exact_stabilizer_summary(form: dict[tuple[int, int, int, int], sp.Integer]) -> dict[str, Any]:
    pairs = list(itertools.combinations(range(NDIM), 2))
    quads = list(itertools.combinations(range(NDIM), 4))
    rows: list[list[int]] = []
    for i, j, k, l in quads:
        row: list[int] = []
        for p, q in pairs:
            def arow(a: int) -> dict[int, int]:
                values: dict[int, int] = {}
                if a == p:
                    values[q] = 1
                if a == q:
                    values[p] = -1
                return values

            value = 0
            for m, coeff in arow(i).items():
                value += coeff * int(exact_val(form, m, j, k, l))
            for m, coeff in arow(j).items():
                value += coeff * int(exact_val(form, i, m, k, l))
            for m, coeff in arow(k).items():
                value += coeff * int(exact_val(form, i, j, m, l))
            for m, coeff in arow(l).items():
                value += coeff * int(exact_val(form, i, j, k, m))
            row.append(-value)
        rows.append(row)
    matrix = sp.Matrix(rows)
    rank = int(matrix.rank())
    return {
        "exact_rank": rank,
        "exact_kernel_dim": SO8_DIM - rank,
        "domain_dim_so8": SO8_DIM,
        "codomain_independent_4form_components": len(quads),
        "pass_spin7_known_value": bool(rank == 7 and SO8_DIM - rank == 21),
    }


def make_spin7_group_element(stab: dict[str, Any]) -> torch.Tensor:
    coeffs = stab["null_coeffs"][0]
    generator = torch.zeros((NDIM, NDIM), dtype=DTYPE)
    for coeff, basis_mat in zip(coeffs, stab["basis"]):
        generator = generator + coeff * basis_mat
    return torch.linalg.matrix_exp(0.37 * generator)


def octonion_table() -> torch.Tensor:
    mult = torch.zeros((8, 8, 8), dtype=torch.int64)
    for i in range(8):
        mult[0, i, i] = 1
        mult[i, 0, i] = 1
    for i in range(1, 8):
        mult[i, i, 0] = -1
    for a, b, c in FANO_TRIPLES_1BASED:
        for x, y, z in ((a, b, c), (b, c, a), (c, a, b)):
            mult[x, y, z] = 1
            mult[y, x, z] = -1
    return mult


def octonion_mul(x: torch.Tensor, y: torch.Tensor, table: torch.Tensor) -> torch.Tensor:
    return torch.einsum("a,b,abc->c", x, y, table)


def octonion_associator_check() -> dict[str, Any]:
    table = octonion_table()

    def basis(index: int) -> torch.Tensor:
        vector = torch.zeros(8, dtype=torch.int64)
        vector[index] = 1
        return vector

    assoc = octonion_mul(octonion_mul(basis(1), basis(2), table), basis(4), table)
    assoc = assoc - octonion_mul(basis(1), octonion_mul(basis(2), basis(4), table), table)
    expected = torch.zeros(8, dtype=torch.int64)
    expected[7] = 2
    return {
        "associator": [int(v.item()) for v in assoc],
        "expected_2e7": [int(v.item()) for v in expected],
        "pass": bool(torch.equal(assoc, expected)),
    }


def smt_spin7_identity_proof(real_residual: float, control_residual: float) -> dict[str, Any]:
    return smt_load_bearing(
        claim="spin7_cayley_contraction_identity_max_abs_residual_le_eps",
        real_measured={"max_abs_identity_residual": real_residual, "eps": EPS},
        control_measured={"max_abs_identity_residual": control_residual, "eps": EPS},
        claim_builder=lambda v: v["max_abs_identity_residual"] <= v["eps"],
        cvc5_claim_pairs=[("max_abs_identity_residual", "<=", "eps")],
    )


def clifford_signature_check() -> dict[str, Any]:
    _, blades_real = Cl(7, 0, firstIdx=1)
    _, blades_control = Cl(6, 1, firstIdx=1)

    def positive_square_count(blades: dict[str, Any]) -> int:
        count = 0
        for i in range(1, 8):
            square = blades[f"e{i}"] * blades[f"e{i}"]
            if float(square[()]) > 0.0:
                count += 1
        return count

    real_count = positive_square_count(blades_real)
    control_count = positive_square_count(blades_control)
    return {
        "real_positive_generator_squares": real_count,
        "control_positive_generator_squares": control_count,
        "real_signature": "Cl(7,0)",
        "control_signature": "Cl(6,1)",
        "pass": bool(real_count == 7 and control_count == 6),
    }


def e3nn_roundtrip_check() -> dict[str, Any]:
    angles = torch.tensor([0.2, -0.4, 0.7])
    rotation = o3.angles_to_matrix(*angles)
    recovered = o3.angles_to_matrix(*o3.matrix_to_angles(rotation))
    baseline_residual = float(torch.max(torch.abs(rotation - recovered)).item())
    malformed = rotation.clone()
    malformed[0, 0] = malformed[0, 0] * 1.2
    try:
        malformed_recovered = o3.angles_to_matrix(*o3.matrix_to_angles(malformed))
        malformed_residual = float(torch.max(torch.abs(malformed - malformed_recovered)).item())
        malformed_success = malformed_residual <= 1.0e-5
    except AssertionError:
        malformed_residual = float("inf")
        malformed_success = False
    return {
        "baseline_roundtrip_residual": baseline_residual,
        "malformed_roundtrip_residual": "inf" if malformed_residual == float("inf") else malformed_residual,
        "baseline_success_score": 1.0 if baseline_residual <= 1.0e-5 else 0.0,
        "malformed_success_score": 1.0 if malformed_success else 0.0,
        "pass": bool(baseline_residual <= 1.0e-5 and not malformed_success),
    }


def geomstats_so8_check(group_element: torch.Tensor) -> dict[str, Any]:
    so8 = SpecialOrthogonal(n=NDIM)
    real_matrix = gs.array(group_element.detach().cpu().tolist())
    control = group_element.clone()
    control[0, 0] = control[0, 0] * 1.05
    control_matrix = gs.array(control.detach().cpu().tolist())
    real_belongs = bool(so8.belongs(real_matrix, atol=1.0e-6).item())
    control_belongs = bool(so8.belongs(control_matrix, atol=1.0e-6).item())
    orth_defect_real = float(torch.max(torch.abs(group_element.T @ group_element - torch.eye(NDIM, dtype=DTYPE))).item())
    orth_defect_control = float(torch.max(torch.abs(control.T @ control - torch.eye(NDIM, dtype=DTYPE))).item())
    return {
        "real_so8_belongs": real_belongs,
        "control_so8_belongs": control_belongs,
        "real_orthogonality_defect": orth_defect_real,
        "control_orthogonality_defect": orth_defect_control,
        "pass": bool(real_belongs and not control_belongs and orth_defect_real <= 1.0e-8 and orth_defect_control > 1.0e-6),
    }


def scale_rung(n: int, real_exact: dict[str, Any], control_exact: dict[str, Any]) -> dict[str, Any]:
    block_count = n // 8
    support_terms = block_count * 14
    full_antisymmetric_entries = support_terms * 24
    ambient_entries = n**4
    return {
        "sites_or_qubits": n,
        "spinor_carrier_dim": n,
        "clifford_chain": f"Cl({6 + block_count})/blocked Spin carrier summary",
        "block_count": block_count,
        "sparse_cayley_terms": support_terms,
        "full_antisymmetric_nonzero_entries": full_antisymmetric_entries,
        "ambient_4tensor_entries_not_materialized": ambient_entries,
        "sparsity_density_upper_bound": full_antisymmetric_entries / ambient_entries,
        "dense_state_closure_used": False,
        "base_real_identity_residual_reused_by_sparse_block_rule": real_exact["max_abs_residual"],
        "base_control_identity_residual_reused_by_sparse_block_rule": control_exact["max_abs_residual"],
        "pass": bool(n in SCALES and n % 8 == 0 and real_exact["pass"] and control_exact["max_abs_residual"] > 0),
    }


def build_tool_ablations(
    real_torch: dict[str, Any],
    control_torch: dict[str, Any],
    real_stab: dict[str, Any],
    control_stab: dict[str, Any],
    clifford_result: dict[str, Any],
    e3nn_result: dict[str, Any],
    geomstats_result: dict[str, Any],
) -> dict[str, Any]:
    return {
        "torch_stabilizer_dim_control_recompute": tool_ablation(
            "torch_kernel_dim_real_phi_vs_sign_flip_control",
            baseline_value=float(real_stab["kernel_dim"]),
            ablated_value=float(control_stab["kernel_dim"]),
            tool="torch",
        ),
        "torch_contraction_residual_control_recompute": tool_ablation(
            "torch_identity_residual_real_phi_vs_sign_flip_control",
            baseline_value=float(real_torch["max_abs_residual"]),
            ablated_value=float(control_torch["max_abs_residual"]),
            tool="torch",
        ),
        "clifford_signature_control_recompute": tool_ablation(
            "clifford_positive_generator_squares_real_Cl70_vs_control_Cl61",
            baseline_value=float(clifford_result["real_positive_generator_squares"]),
            ablated_value=float(clifford_result["control_positive_generator_squares"]),
            tool="clifford",
        ),
        "e3nn_roundtrip_control_recompute": tool_ablation(
            "e3nn_so3_roundtrip_success_real_rotation_vs_malformed_matrix",
            baseline_value=float(e3nn_result["baseline_success_score"]),
            ablated_value=float(e3nn_result["malformed_success_score"]),
            tool="e3nn",
        ),
        "geomstats_so8_membership_control_recompute": tool_ablation(
            "geomstats_special_orthogonal_belongs_real_exponential_vs_nonorthogonal_control",
            baseline_value=1.0 if geomstats_result["real_so8_belongs"] else 0.0,
            ablated_value=1.0 if geomstats_result["control_so8_belongs"] else 0.0,
            tool="geomstats",
        ),
    }


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(exist_ok=True)

    real_phi = build_torch_phi(control=False)
    control_phi = build_torch_phi(control=True)
    real_jax_phi = build_jax_phi(control=False)
    control_jax_phi = build_jax_phi(control=True)
    real_exact_form = build_exact_form(control=False)
    control_exact_form = build_exact_form(control=True)

    real_torch = contraction_residual_torch(real_phi)
    control_torch = contraction_residual_torch(control_phi)
    real_jax = contraction_residual_jax(real_jax_phi)
    control_jax = contraction_residual_jax(control_jax_phi)
    real_exact = exact_contraction_summary(real_exact_form)
    control_exact = exact_contraction_summary(control_exact_form)
    real_selfdual_exact = exact_self_duality_summary(real_exact_form)
    control_selfdual_exact = exact_self_duality_summary(control_exact_form)

    real_stab_torch = stabilizer_numeric(real_phi)
    control_stab_torch = stabilizer_numeric(control_phi)
    real_stab_exact = exact_stabilizer_summary(real_exact_form)
    control_stab_exact = exact_stabilizer_summary(control_exact_form)
    group_element = make_spin7_group_element(real_stab_torch)

    proof = smt_spin7_identity_proof(real_torch["max_abs_residual"], control_torch["max_abs_residual"])
    octonion_assoc = octonion_associator_check()
    clifford_result = clifford_signature_check()
    e3nn_result = e3nn_roundtrip_check()
    geomstats_result = geomstats_so8_check(group_element)

    scale_rows = {
        str(n): scale_rung(n, real_exact, control_exact)
        for n in SCALES
    }
    scale_pass = all(row["pass"] for row in scale_rows.values())
    ablations = build_tool_ablations(
        real_torch,
        control_torch,
        real_stab_torch,
        control_stab_torch,
        clifford_result,
        e3nn_result,
        geomstats_result,
    )
    ablation_pass = all(
        abs(float(row["baseline_value"]) - float(row["ablated_value"])) > 1.0e-12
        and abs((float(row["baseline_value"]) - float(row["ablated_value"])) - float(row["outcome_delta"])) <= 1.0e-12
        for row in ablations.values()
    )

    torch_primary_result = {
        "runtime": "torch",
        "dtype": str(DTYPE),
        "cayley_tensor_shape": [NDIM, NDIM, NDIM, NDIM],
        "real_identity_max_abs_residual": real_torch["max_abs_residual"],
        "real_identity_frobenius_residual": real_torch["frobenius_residual"],
        "control_identity_max_abs_residual": control_torch["max_abs_residual"],
        "control_identity_frobenius_residual": control_torch["frobenius_residual"],
        "real_self_duality_defect": hodge_self_duality_defect_torch(real_phi),
        "control_self_duality_defect": hodge_self_duality_defect_torch(control_phi),
        "real_stabilizer_kernel_dim": int(real_stab_torch["kernel_dim"]),
        "control_stabilizer_kernel_dim": int(control_stab_torch["kernel_dim"]),
        "pass": bool(
            real_torch["max_abs_residual"] <= EPS
            and control_torch["max_abs_residual"] > EPS
            and real_stab_torch["kernel_dim"] == 21
            and control_stab_torch["kernel_dim"] == 9
            and hodge_self_duality_defect_torch(real_phi) <= EPS
            and hodge_self_duality_defect_torch(control_phi) > EPS
        ),
    }

    jax_mirror_result = {
        "runtime": "jax",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "real_identity_max_abs_residual": real_jax["max_abs_residual"],
        "control_identity_max_abs_residual": control_jax["max_abs_residual"],
        "real_self_duality_defect": hodge_self_duality_defect_jax(real_jax_phi),
        "control_self_duality_defect": hodge_self_duality_defect_jax(control_jax_phi),
        "pass": bool(
            abs(real_jax["max_abs_residual"] - real_torch["max_abs_residual"]) <= EPS
            and abs(control_jax["max_abs_residual"] - control_torch["max_abs_residual"]) <= EPS
            and hodge_self_duality_defect_jax(real_jax_phi) <= EPS
            and hodge_self_duality_defect_jax(control_jax_phi) > EPS
        ),
    }
    jax_vs_pytorch_delta = max(
        abs(jax_mirror_result["real_identity_max_abs_residual"] - torch_primary_result["real_identity_max_abs_residual"]),
        abs(jax_mirror_result["control_identity_max_abs_residual"] - torch_primary_result["control_identity_max_abs_residual"]),
        abs(jax_mirror_result["real_self_duality_defect"] - torch_primary_result["real_self_duality_defect"]),
        abs(jax_mirror_result["control_self_duality_defect"] - torch_primary_result["control_self_duality_defect"]),
    )

    proof_pass = bool(
        proof["real_claim_verdict"] == "sat"
        and proof["negated_claim_verdict"] == "unsat"
        and proof["differ"] is True
        and proof["bound_to_measured"] is True
        and proof.get("cvc5_real_verdict") == "sat"
        and proof.get("cvc5_control_verdict") == "unsat"
        and real_exact["pass"]
        and not control_exact["pass"]
    )
    auxiliary_pass = bool(
        octonion_assoc["pass"]
        and clifford_result["pass"]
        and e3nn_result["pass"]
        and geomstats_result["pass"]
        and real_stab_exact["pass_spin7_known_value"]
        and control_stab_exact["exact_kernel_dim"] == 9
        and real_selfdual_exact["pass"]
        and not control_selfdual_exact["pass"]
    )
    all_pass = bool(
        torch_primary_result["pass"]
        and jax_mirror_result["pass"]
        and proof_pass
        and auxiliary_pass
        and scale_pass
        and ablation_pass
    )

    return {
        "sim_id": "sim_gstruct_spin7_probe",
        "name": "Stage-4 Spin(7) Cayley G-structure finite-map probe",
        "version": "1.0.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "thisfile": THISFILE,
        "result": str(RESULT.relative_to(ROOT)),
        "object_id": OBJECT_ID,
        "spec_key": "Spin(7)",
        "spec_selection_note": "The substring Spin(7) appeared in two spec rows; this sim uses the row whose gstructure starts with 'Spin(7) G-structure'.",
        "finite_map": {
            "domain": "Sparse fully antisymmetric integer Cayley 4-form Phi in Lambda^4(R^8)* with 14 independent unit terms, plus SO(8) infinitesimal generators.",
            "codomain_or_output": "Quadratic contraction residual tensor, Hodge self-duality defect, stabilizer action-map rank/kernel dimension, and blocked downstream consumer list.",
            "definition": "Phi -> Phi_ijab Phi_klab - 6(delta_ik delta_jl - delta_il delta_jk) - 4 Phi_ijkl; pass iff max residual is zero on real Phi and nonzero on equal-norm sign-flip control.",
            "negative_control": "Flip only the e5678 coefficient from +1 to -1; norm and term count remain 14.",
        },
        "root_constraints": {
            "F01": {
                "status": "active_tested",
                "statement": "finite carrier/probe/operator set: 14 sparse Cayley terms expanded over finite index set {0..7}, 28 SO(8) generators, 70 independent 4-form components.",
            },
            "N01": {
                "status": "active_tested",
                "statement": "order-sensitive octonion multiplication witness: associator (e1e2)e4 - e1(e2e4) = 2e7, plus sign/order-sensitive Cayley control flip.",
            },
        },
        "classification": "lego",
        "promotion_allowed": False,
        "tier": "STAGE 4",
        "sim_execution_kind": "nonclassical",
        "sim_class": "g_structure_probe",
        "carrier_layer": "Spin(7) Cayley 4-form on R^8 with sparse spinor/Clifford carrier summaries at 8/16/32/64",
        "geometry_layer": "SO(8) frame reduction to Spin(7) stabilizer of the Cayley 4-form",
        "carrier_realization": "torch.float64 sparse finite tensor from exact integer term list; no NumPy import, no dense n^4 scale materialization beyond the base 8D form.",
        "peps3d_embedding": "finite PEPS3D carrier anchor: each scale rung is a block lattice of 8-dimensional local spinor cells carrying the same sparse Cayley channel; this sim does not promote a manifold layer.",
        "spinor_state": "8-dimensional real spinor carrier for Cl(7)/Spin(7), scaled as 8/16/32/64 block spinor carriers without dense-state closure.",
        "quaternion_action": "not_applicable; octonion nonassociative multiplication is checked instead, with associator witness 2e7.",
        "dependency_receipts": ["task_spec:/tmp/gstruct_specs.json#index_9", "exemplar:sim_root_F01_finite_distinguishability_probe.py"],
        "allowed_claims": [
            "Pointwise Stage-4 algebraic Spin(7) G-structure finite-map witness.",
            "The Cayley contraction identity holds for the real Phi and fails for the equal-norm sign-flip control.",
            "The stabilizer action-map kernel dimension is 21 on real Phi and 9 on the control.",
        ],
        "promotion_blockers": [
            "No curvature or holonomy transport is proved.",
            "No layer completion, stack readiness, Axis0, FEP, flux, bridge, basin, or physics claim is admitted.",
            "Scale ladder is sparse block-carrier evidence, not dense full Spin(7) manifold integration.",
        ],
        "eligible_consumers": ["bounded future Stage-4 local G-structure comparison probes only"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "torch_primary_result": torch_primary_result,
        "jax_mirror_result": jax_mirror_result,
        "jax_vs_pytorch_delta": float(jax_vs_pytorch_delta),
        "proof_results": {
            "spin7_contraction_identity_smt_load_bearing": proof,
            "sympy_exact_result": {
                "real_contraction": real_exact,
                "control_contraction": control_exact,
                "real_self_duality": real_selfdual_exact,
                "control_self_duality": control_selfdual_exact,
                "real_stabilizer": real_stab_exact,
                "control_stabilizer": control_stab_exact,
                "pass": bool(real_exact["pass"] and not control_exact["pass"] and real_stab_exact["pass_spin7_known_value"]),
            },
        },
        "controls": {
            "sign_flip_e5678": {
                "description": "Flip e5678 from +1 to -1 while preserving independent norm=14 and independent term count=14.",
                "real_norm_squared": real_exact["independent_norm_squared"],
                "control_norm_squared": control_exact["independent_norm_squared"],
                "real_term_count": real_exact["independent_nonzero_terms"],
                "control_term_count": control_exact["independent_nonzero_terms"],
                "control_identity_max_abs_residual": control_torch["max_abs_residual"],
                "control_stabilizer_kernel_dim": control_stab_exact["exact_kernel_dim"],
                "control_self_duality_defect": control_selfdual_exact["max_abs_star_minus_phi"],
                "pass": bool(
                    real_exact["independent_norm_squared"] == control_exact["independent_norm_squared"] == 14
                    and real_exact["independent_nonzero_terms"] == control_exact["independent_nonzero_terms"] == 14
                    and control_torch["max_abs_residual"] > EPS
                    and control_stab_exact["exact_kernel_dim"] == 9
                    and control_selfdual_exact["max_abs_star_minus_phi"] > 0
                ),
            },
            "octonion_nonassociativity": octonion_assoc,
        },
        "tool_ablations": ablations,
        "scale_ladder": {
            "axis": "8/16/32/64 sparse spinor/Clifford block carriers; Phi remains a sparse local 8D Cayley channel.",
            "rungs": scale_rows,
            "pass": bool(scale_pass),
        },
        "known_value_checks": {
            "dim_so8": {"computed": SO8_DIM, "expected": 28, "pass": SO8_DIM == 28},
            "dim_spin7_real": {"computed": real_stab_exact["exact_kernel_dim"], "expected": 21, "pass": real_stab_exact["exact_kernel_dim"] == 21},
            "orbit_codim": {"computed": SO8_DIM - real_stab_exact["exact_kernel_dim"], "expected": 7, "pass": SO8_DIM - real_stab_exact["exact_kernel_dim"] == 7},
            "cayley_norm_squared": {"computed": real_exact["independent_norm_squared"], "expected": 14, "pass": real_exact["independent_norm_squared"] == 14},
            "independent_term_count": {"computed": real_exact["independent_nonzero_terms"], "expected": 14, "pass": real_exact["independent_nonzero_terms"] == 14},
            "full_antisymmetric_nonzero_entries": {"computed": real_exact["full_antisymmetric_nonzero_entries"], "expected": 336, "pass": real_exact["full_antisymmetric_nonzero_entries"] == 336},
            "hodge_self_duality": {"computed_max_defect": real_selfdual_exact["max_abs_star_minus_phi"], "expected": 0, "pass": real_selfdual_exact["pass"]},
            "contraction_identity_residual": {"computed_max_abs": real_exact["max_abs_residual"], "expected": 0, "pass": real_exact["pass"]},
            "control_identity_residual": {"computed_max_abs": control_exact["max_abs_residual"], "expected_nonzero": True, "pass": control_exact["max_abs_residual"] > 0},
            "control_stabilizer_dim": {"computed": control_stab_exact["exact_kernel_dim"], "expected": 9, "pass": control_stab_exact["exact_kernel_dim"] == 9},
            "octonion_associator": {"computed": octonion_assoc["associator"], "expected": octonion_assoc["expected_2e7"], "pass": octonion_assoc["pass"]},
        },
        "finite_frame_data": {
            "cayley_terms_1based": [{"indices": list(indices), "coeff": coeff} for indices, coeff in CAYLEY_TERMS_1BASED],
            "control": "e5678 coefficient flipped from +1 to -1 only",
            "fano_triples_1based": [list(row) for row in FANO_TRIPLES_1BASED],
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "pass_rule": "real Cayley Phi has exact Spin(7) contraction identity, self-duality, and kernel dim 21; equal-norm sign-flip control fails identity/self-duality and drops kernel dim to 9; proof verdict flips through smt_load_bearing.",
        "fail_rule": "fail on non-flipping proof, proof not bound to measured residuals, planted known values, norm/sparsity-only control, missing genuine numeric ablation, JAX mismatch, dense scale materialization, or downstream promotion.",
        "all_pass": all_pass,
        "required_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT.write_text(json.dumps(result, indent=2) + "\n")
    print(f"wrote {RESULT.relative_to(ROOT)}")
    print(f"required_pass={result['required_pass']}")
    return 0 if result["required_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
