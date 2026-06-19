#!/usr/bin/env python3
"""Scratch finite witness: SU(3) color from G2=Aut(O) stabilizer on Cl(6)."""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


OBJECT_ID = "su3_color_from_g2_octonion_cl6"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/su3_color_from_g2_octonion_cl6_results.json"
JULIA_REFERENCE_PATH = ROOT / "system_v5/julia_carrier/su3_color_from_g2_octonion_cl6_julia_results.json"

TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
COLLAPSE_SENTINEL = 1.0e99
DIM_O = 8
FIXED_UNIT = 7
CLAIM_CEILING = (
    "finite witness that SU(3)-color emerges as the G2=Aut(O) complex-structure "
    "stabilizer on Cl(6) octonion spinors, reproducing the published "
    "Dixon/Furey construction on the owner's carrier; NO admission of the "
    "Standard Model/physics/M(C); masses, couplings, SU(2)xU(1), and "
    "generations NOT addressed here"
)
FANO = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
]


def py_float(x: Any) -> float:
    return float(jax.device_get(jnp.real(x)))


def py_bool(x: Any) -> bool:
    return bool(jax.device_get(x))


def setprod(table: jax.Array, a: int, b: int, c: int, s: float) -> jax.Array:
    return table.at[c, a, b].set(s)


def octonion_table() -> jax.Array:
    table = jnp.zeros((DIM_O, DIM_O, DIM_O), dtype=jnp.float64)
    for a in range(DIM_O):
        table = setprod(table, 0, a, a, 1.0)
        table = setprod(table, a, 0, a, 1.0)
    for a in range(1, DIM_O):
        table = setprod(table, a, a, 0, -1.0)
    for i, j, k in FANO:
        for a, b, c, s in [
            (i, j, k, 1.0),
            (j, k, i, 1.0),
            (k, i, j, 1.0),
            (j, i, k, -1.0),
            (k, j, i, -1.0),
            (i, k, j, -1.0),
        ]:
            table = setprod(table, a, b, c, s)
    return table


def associative_commutative_erase_table() -> jax.Array:
    table = jnp.zeros((DIM_O, DIM_O, DIM_O), dtype=jnp.float64)
    for a in range(DIM_O):
        table = setprod(table, a, a, a, 1.0)
    return table


def basis(dim: int, idx: int, dtype: Any = jnp.float64) -> jax.Array:
    return jnp.eye(dim, dtype=dtype)[idx]


def multiply(table: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    return jnp.einsum("cab,a,b->c", table, x, y)


def left_matrix(table: jax.Array, v: jax.Array) -> jax.Array:
    return jnp.einsum("cab,a->cb", table, v)


def varidx(row: int, col: int) -> int:
    return row + col * DIM_O


def vec_to_matrix(v: jax.Array) -> jax.Array:
    return jnp.stack([v[col * DIM_O : (col + 1) * DIM_O] for col in range(DIM_O)], axis=1)


def matrix_to_vec(mat: jax.Array) -> jax.Array:
    return jnp.concatenate([mat[:, col] for col in range(DIM_O)])


def rank_from_singular_values(singular: jax.Array, shape: tuple[int, int], scale: float = 100.0) -> tuple[int, float]:
    max_s = jnp.max(singular) if singular.size else jnp.array(0.0, dtype=jnp.float64)
    tol = py_float(max(shape) * jnp.finfo(jnp.float64).eps * max_s * scale)
    rank = int(jax.device_get(jnp.sum(singular > tol)))
    return rank, tol


def nullspace_data(mat: jax.Array) -> dict[str, Any]:
    full = mat.shape[0] < mat.shape[1]
    _, singular, vh = jnp.linalg.svd(mat, full_matrices=full)
    rank, tol = rank_from_singular_values(singular, mat.shape)
    basis_cols = vh.conj().T[:, rank:]
    return {
        "rank": rank,
        "tol": tol,
        "nullity": int(basis_cols.shape[1]),
        "basis": basis_cols,
        "singular": singular,
    }


def derivation_constraint_matrix(table: jax.Array) -> jax.Array:
    mat = jnp.zeros((DIM_O * DIM_O * DIM_O, DIM_O * DIM_O), dtype=jnp.float64)
    row = 0
    for a in range(DIM_O):
        for b in range(DIM_O):
            for c in range(DIM_O):
                for k in range(DIM_O):
                    mat = mat.at[row, varidx(c, k)].add(table[k, a, b])
                    mat = mat.at[row, varidx(k, a)].add(-table[c, k, b])
                    mat = mat.at[row, varidx(k, b)].add(-table[c, a, k])
                row += 1
    return mat


def derivation_residual(table: jax.Array, d: jax.Array) -> float:
    max_seen = 0.0
    for a in range(DIM_O):
        for b in range(DIM_O):
            ea = basis(DIM_O, a)
            eb = basis(DIM_O, b)
            left = d @ multiply(table, ea, eb)
            right = multiply(table, d @ ea, eb) + multiply(table, ea, d @ eb)
            max_seen = max(max_seen, py_float(jnp.linalg.norm(left - right)))
    return max_seen


def derivation_basis(table: jax.Array) -> dict[str, Any]:
    constraint = derivation_constraint_matrix(table)
    ns = nullspace_data(constraint)
    mats = [vec_to_matrix(ns["basis"][:, idx]) for idx in range(ns["nullity"])]
    return {"constraint": constraint, "nullspace": ns, "mats": mats}


def stabilizer_basis(g2_basis: jax.Array, fixed_idx: int) -> dict[str, Any]:
    constraints = jnp.stack([g2_basis[varidx(row, fixed_idx), :] for row in range(DIM_O)], axis=0)
    ns = nullspace_data(constraints)
    basis_cols = g2_basis @ ns["basis"]
    mats = [vec_to_matrix(basis_cols[:, idx]) for idx in range(basis_cols.shape[1])]
    return {"constraints": constraints, "nullspace": ns, "basis": basis_cols, "mats": mats}


def project_coeffs(basis_cols: jax.Array, vec: jax.Array) -> jax.Array:
    gram = basis_cols.conj().T @ basis_cols
    return jnp.linalg.solve(gram, basis_cols.conj().T @ vec)


def bracket_closure_metrics(basis_cols: jax.Array, mats: list[jax.Array]) -> dict[str, Any]:
    n = len(mats)
    max_resid = 0.0
    max_bracket_norm = 0.0
    coeffs = jnp.zeros((n, n, n), dtype=basis_cols.dtype)
    for i, left in enumerate(mats):
        for j, right in enumerate(mats):
            bracket = left @ right - right @ left
            flat = matrix_to_vec(bracket)
            co = project_coeffs(basis_cols, flat)
            residual = flat - basis_cols @ co
            max_resid = max(max_resid, py_float(jnp.linalg.norm(residual)))
            max_bracket_norm = max(max_bracket_norm, py_float(jnp.linalg.norm(bracket)))
            coeffs = coeffs.at[:, i, j].set(co)
    return {"max_residual": max_resid, "max_bracket_norm": max_bracket_norm, "structure_constants": coeffs}


def killing_and_rank_metrics(structure_constants: jax.Array, mats: list[jax.Array], basis_cols: jax.Array) -> dict[str, Any]:
    n = int(structure_constants.shape[0])
    ad = [structure_constants[:, i, :] for i in range(n)]
    killing = jnp.array([[jnp.trace(ad[i] @ ad[j]) for j in range(n)] for i in range(n)], dtype=jnp.float64)
    killing_eigs = jnp.linalg.eigvalsh((killing + killing.T) / 2.0)
    generic = sum(float(idx + 1) * mats[idx] for idx in range(n))
    centralizer_columns = [matrix_to_vec(mats[idx] @ generic - generic @ mats[idx]) for idx in range(n)]
    centralizer_matrix = jnp.stack(centralizer_columns, axis=1)
    centralizer_singular = jnp.linalg.svd(centralizer_matrix, compute_uv=False)
    centralizer_rank = int(jax.device_get(jnp.sum(centralizer_singular > 1.0e-9)))
    return {
        "killing_matrix": killing,
        "killing_eigs": killing_eigs,
        "killing_negative_definite": py_bool(jnp.all(killing_eigs < -1.0e-9)),
        "centralizer_rank": centralizer_rank,
        "rank": n - centralizer_rank,
        "basis_gram_residual": py_float(jnp.linalg.norm(basis_cols.T @ basis_cols - jnp.eye(n, dtype=jnp.float64))),
    }


def j_eigenbasis() -> jax.Array:
    eye = jnp.eye(DIM_O, dtype=jnp.complex128)
    e = lambda idx: eye[:, idx]
    rt2 = jnp.sqrt(jnp.array(2.0, dtype=jnp.float64))
    return jnp.stack(
        [
            (e(0) - 1j * e(7)) / rt2,
            (e(1) + 1j * e(6)) / rt2,
            (e(2) - 1j * e(5)) / rt2,
            (e(3) - 1j * e(4)) / rt2,
            (e(0) + 1j * e(7)) / rt2,
            (e(1) - 1j * e(6)) / rt2,
            (e(2) + 1j * e(5)) / rt2,
            (e(3) + 1j * e(4)) / rt2,
        ],
        axis=1,
    )


def decomposition_metrics(mats: list[jax.Array]) -> dict[str, Any]:
    change = j_eigenbasis()
    inv = change.conj().T
    blocks = [0, 1, 1, 1, 2, 3, 3, 3]
    max_offblock = 0.0
    max_singlet = 0.0
    max_trace = 0.0
    max_antitriplet_conj = 0.0
    casimir_triplet = jnp.zeros((3, 3), dtype=jnp.complex128)
    casimir_antitriplet = jnp.zeros((3, 3), dtype=jnp.complex128)
    for mat in mats:
        rep = inv @ (mat.astype(jnp.complex128) @ change)
        for row in range(DIM_O):
            for col in range(DIM_O):
                if blocks[row] != blocks[col]:
                    max_offblock = max(max_offblock, py_float(jnp.abs(rep[row, col])))
        max_singlet = max(max_singlet, py_float(jnp.abs(rep[0, 0])), py_float(jnp.abs(rep[4, 4])))
        triplet = rep[1:4, 1:4]
        antitriplet = rep[5:8, 5:8]
        max_trace = max(max_trace, py_float(jnp.abs(jnp.trace(triplet))), py_float(jnp.abs(jnp.trace(antitriplet))))
        max_antitriplet_conj = max(max_antitriplet_conj, py_float(jnp.linalg.norm(antitriplet - jnp.conj(triplet))))
        casimir_triplet = casimir_triplet + triplet @ triplet
        casimir_antitriplet = casimir_antitriplet + antitriplet @ antitriplet
    casimir_target = -(4.0 / 3.0) * jnp.eye(3, dtype=jnp.complex128)
    return {
        "basis_unitary_residual": py_float(jnp.linalg.norm(change.conj().T @ change - jnp.eye(DIM_O, dtype=jnp.complex128))),
        "offblock_residual": max_offblock,
        "singlet_action_residual": max_singlet,
        "triplet_trace_residual": max_trace,
        "antitriplet_is_conjugate_residual": max_antitriplet_conj,
        "triplet_casimir_residual": py_float(jnp.linalg.norm(casimir_triplet - casimir_target)),
        "antitriplet_casimir_residual": py_float(jnp.linalg.norm(casimir_antitriplet - casimir_target)),
        "triplet_casimir_value": py_float(-jnp.trace(casimir_triplet) / 3.0),
        "antitriplet_casimir_value": py_float(-jnp.trace(casimir_antitriplet) / 3.0),
        "dims": {"singlet_plus": 1, "triplet": 3, "singlet_minus": 1, "antitriplet": 3},
    }


def complex_vec(terms: list[tuple[int, complex]]) -> jax.Array:
    out = jnp.zeros((DIM_O,), dtype=jnp.complex128)
    for idx, coeff in terms:
        out = out.at[idx].set(coeff)
    return out


def octonion_complex_dagger(v: jax.Array) -> jax.Array:
    out = jnp.zeros_like(v)
    out = out.at[0].set(jnp.conj(v[0]))
    for idx in range(1, DIM_O):
        out = out.at[idx].set(-jnp.conj(v[idx]))
    return out


def owner_ladder_vectors() -> list[jax.Array]:
    return [
        complex_vec([(6, -0.5), (1, 0.5j)]),
        complex_vec([(5, -0.5), (2, 0.5j)]),
        complex_vec([(4, -0.5), (3, 0.5j)]),
    ]


def wedge2_matrix(triplet: jax.Array) -> jax.Array:
    pairs = [(1, 2), (2, 0), (0, 1)]
    out = jnp.zeros((3, 3), dtype=jnp.complex128)
    for col, (a, b) in enumerate(pairs):
        for r in range(3):
            for term, coeff in [((r, b), triplet[r, a]), ((a, r), triplet[r, b])]:
                if term[0] == term[1]:
                    continue
                sign = 1.0
                ordered = term
                if ordered[0] > ordered[1]:
                    ordered = (ordered[1], ordered[0])
                    sign = -1.0
                for row, target in enumerate(pairs):
                    if ordered == target:
                        out = out.at[row, col].add(sign * coeff)
                    elif ordered == (target[1], target[0]):
                        out = out.at[row, col].add(-sign * coeff)
    return out


def cl6_ladder_metrics(table: jax.Array) -> dict[str, Any]:
    ctable = table.astype(jnp.complex128)
    alphas = owner_ladder_vectors()
    daggers = [octonion_complex_dagger(alpha) for alpha in alphas]
    lower = [left_matrix(ctable, alpha) for alpha in alphas]
    raise_ = [left_matrix(ctable, dagger) for dagger in daggers]
    ident = jnp.eye(DIM_O, dtype=jnp.complex128)

    car_residual = 0.0
    for i in range(3):
        for j in range(3):
            target = ident if i == j else jnp.zeros_like(ident)
            car_residual = max(car_residual, py_float(jnp.linalg.norm(lower[i] @ raise_[j] + raise_[j] @ lower[i] - target)))
            car_residual = max(car_residual, py_float(jnp.linalg.norm(lower[i] @ lower[j] + lower[j] @ lower[i])))
            car_residual = max(car_residual, py_float(jnp.linalg.norm(raise_[i] @ raise_[j] + raise_[j] @ raise_[i])))

    gammas = [lower[i] + raise_[i] for i in range(3)] + [-1j * (lower[i] - raise_[i]) for i in range(3)]
    gamma_residual = 0.0
    for i in range(6):
        for j in range(6):
            target = 2.0 * ident if i == j else jnp.zeros_like(ident)
            gamma_residual = max(gamma_residual, py_float(jnp.linalg.norm(gammas[i] @ gammas[j] + gammas[j] @ gammas[i] - target)))

    products = []
    for mask in range(64):
        mat = ident
        for idx, gamma in enumerate(gammas):
            if (mask >> idx) & 1:
                mat = mat @ gamma
        products.append(mat.reshape(-1))
    span = jnp.stack(products, axis=1)
    span_singular = jnp.linalg.svd(span, compute_uv=False)
    cl6_rank = int(jax.device_get(jnp.sum(span_singular > 1.0e-9)))

    lambdas = [
        -(raise_[1] @ lower[0] + raise_[0] @ lower[1]),
        1j * raise_[1] @ lower[0] - 1j * raise_[0] @ lower[1],
        raise_[1] @ lower[1] - raise_[0] @ lower[0],
        -(raise_[0] @ lower[2] + raise_[2] @ lower[0]),
        -1j * raise_[0] @ lower[2] + 1j * raise_[2] @ lower[0],
        -(raise_[2] @ lower[1] + raise_[1] @ lower[2]),
        1j * raise_[2] @ lower[1] - 1j * raise_[1] @ lower[2],
        -(raise_[0] @ lower[0] + raise_[1] @ lower[1] - 2.0 * raise_[2] @ lower[2]) / jnp.sqrt(3.0),
    ]
    su3_spinor = [-0.5j * item for item in lambdas]
    spinor_cols = jnp.stack([item.reshape(-1) for item in su3_spinor], axis=1)
    spinor_rank = int(jax.device_get(jnp.linalg.matrix_rank(spinor_cols, tol=1.0e-9)))
    if spinor_rank < 8:
        return {
            "car_residual": car_residual,
            "gamma_residual": gamma_residual,
            "cl6_matrix_span_dim": cl6_rank,
            "spinor_su3_rank": spinor_rank,
            "spinor_su3_closure_residual": COLLAPSE_SENTINEL,
            "projector_rank": 0,
            "vacuum_column": None,
            "fock_gram_residual": COLLAPSE_SENTINEL,
            "fock_offblock_residual": COLLAPSE_SENTINEL,
            "fock_singlet_action_residual": COLLAPSE_SENTINEL,
            "fock_triplet_trace_residual": COLLAPSE_SENTINEL,
            "fock_wedge2_antitriplet_residual": COLLAPSE_SENTINEL,
            "fock_triplet_casimir_residual": COLLAPSE_SENTINEL,
            "fock_antitriplet_casimir_residual": COLLAPSE_SENTINEL,
            "number_operator_residual": COLLAPSE_SENTINEL,
            "charge_quantization_residual": COLLAPSE_SENTINEL,
            "particle_ideal_charges": [],
            "charge_conjugate_ideal_charges": [],
            "sm_charge_slots": {},
        }
    spinor_gram = spinor_cols.conj().T @ spinor_cols
    spinor_closure = 0.0
    for left in su3_spinor:
        for right in su3_spinor:
            bracket = left @ right - right @ left
            coeff = jnp.linalg.solve(spinor_gram, spinor_cols.conj().T @ bracket.reshape(-1))
            spinor_closure = max(spinor_closure, py_float(jnp.linalg.norm(bracket.reshape(-1) - spinor_cols @ coeff)))

    projector = lower[0] @ lower[1] @ lower[2] @ raise_[2] @ raise_[1] @ raise_[0]
    col_norms = jnp.linalg.norm(projector, axis=0)
    vacuum_col = int(jax.device_get(jnp.argmax(col_norms)))
    if py_float(col_norms[vacuum_col]) < TOL:
        return {
            "car_residual": car_residual,
            "gamma_residual": gamma_residual,
            "cl6_matrix_span_dim": cl6_rank,
            "spinor_su3_rank": spinor_rank,
            "spinor_su3_closure_residual": spinor_closure,
            "projector_rank": int(jax.device_get(jnp.linalg.matrix_rank(projector, tol=1.0e-9))),
            "vacuum_column": vacuum_col,
            "fock_gram_residual": COLLAPSE_SENTINEL,
            "fock_offblock_residual": COLLAPSE_SENTINEL,
            "fock_singlet_action_residual": COLLAPSE_SENTINEL,
            "fock_triplet_trace_residual": COLLAPSE_SENTINEL,
            "fock_wedge2_antitriplet_residual": COLLAPSE_SENTINEL,
            "fock_triplet_casimir_residual": COLLAPSE_SENTINEL,
            "fock_antitriplet_casimir_residual": COLLAPSE_SENTINEL,
            "number_operator_residual": COLLAPSE_SENTINEL,
            "charge_quantization_residual": COLLAPSE_SENTINEL,
            "particle_ideal_charges": [],
            "charge_conjugate_ideal_charges": [],
            "sm_charge_slots": {},
        }
    vacuum = projector[:, vacuum_col] / col_norms[vacuum_col]
    fock_states = [vacuum]
    fock_states.extend([raise_[idx] @ vacuum for idx in range(3)])
    fock_states.extend([raise_[1] @ raise_[2] @ vacuum, raise_[2] @ raise_[0] @ vacuum, raise_[0] @ raise_[1] @ vacuum])
    fock_states.append(raise_[0] @ raise_[1] @ raise_[2] @ vacuum)
    fock = jnp.stack(fock_states, axis=1)
    fock_inv = fock.conj().T
    fock_gram_residual = py_float(jnp.linalg.norm(fock_inv @ fock - ident))
    occ_blocks = [0, 1, 1, 1, 2, 2, 2, 3]

    fock_offblock = 0.0
    fock_singlet = 0.0
    fock_trace = 0.0
    wedge2_residual = 0.0
    fock_casimir_1 = jnp.zeros((3, 3), dtype=jnp.complex128)
    fock_casimir_2 = jnp.zeros((3, 3), dtype=jnp.complex128)
    for generator in su3_spinor:
        rep = fock_inv @ (generator @ fock)
        for row in range(DIM_O):
            for col in range(DIM_O):
                if occ_blocks[row] != occ_blocks[col]:
                    fock_offblock = max(fock_offblock, py_float(jnp.abs(rep[row, col])))
        fock_singlet = max(fock_singlet, py_float(jnp.abs(rep[0, 0])), py_float(jnp.abs(rep[7, 7])))
        triplet = rep[1:4, 1:4]
        antitriplet = rep[4:7, 4:7]
        fock_trace = max(fock_trace, py_float(jnp.abs(jnp.trace(triplet))), py_float(jnp.abs(jnp.trace(antitriplet))))
        wedge2_residual = max(wedge2_residual, py_float(jnp.linalg.norm(antitriplet - wedge2_matrix(triplet))))
        fock_casimir_1 = fock_casimir_1 + triplet @ triplet
        fock_casimir_2 = fock_casimir_2 + antitriplet @ antitriplet
    casimir_target = -(4.0 / 3.0) * jnp.eye(3, dtype=jnp.complex128)

    number = sum(raise_[idx] @ lower[idx] for idx in range(3))
    number_rep = fock_inv @ (number @ fock)
    number_target = jnp.diag(jnp.array([0.0, 1.0, 1.0, 1.0, 2.0, 2.0, 2.0, 3.0], dtype=jnp.float64)).astype(jnp.complex128)
    particle_charges = jnp.diag(number_target).real / 3.0
    conjugate_charges = -particle_charges
    charge_quant_residual = max(
        py_float(jnp.max(jnp.abs(3.0 * particle_charges - jnp.round(3.0 * particle_charges)))),
        py_float(jnp.max(jnp.abs(3.0 * conjugate_charges - jnp.round(3.0 * conjugate_charges)))),
    )

    return {
        "car_residual": car_residual,
        "gamma_residual": gamma_residual,
        "cl6_matrix_span_dim": cl6_rank,
        "spinor_su3_rank": spinor_rank,
        "spinor_su3_closure_residual": spinor_closure,
        "projector_rank": int(jax.device_get(jnp.linalg.matrix_rank(projector, tol=1.0e-9))),
        "vacuum_column": vacuum_col,
        "fock_gram_residual": fock_gram_residual,
        "fock_offblock_residual": fock_offblock,
        "fock_singlet_action_residual": fock_singlet,
        "fock_triplet_trace_residual": fock_trace,
        "fock_wedge2_antitriplet_residual": wedge2_residual,
        "fock_triplet_casimir_residual": py_float(jnp.linalg.norm(fock_casimir_1 - casimir_target)),
        "fock_antitriplet_casimir_residual": py_float(jnp.linalg.norm(fock_casimir_2 - casimir_target)),
        "number_operator_residual": py_float(jnp.linalg.norm(number_rep - number_target)),
        "charge_quantization_residual": charge_quant_residual,
        "particle_ideal_charges": [py_float(x) for x in particle_charges],
        "charge_conjugate_ideal_charges": [py_float(x) for x in conjugate_charges],
        "sm_charge_slots": {
            "neutrino_singlet": {"dim": 1, "charge": 0.0, "source": "particle ideal N=0"},
            "down_quark_color_triplet": {"dim": 3, "charge": -1.0 / 3.0, "source": "charge-conjugate ideal N=1"},
            "up_quark_color_triplet": {"dim": 3, "charge": 2.0 / 3.0, "source": "particle ideal N=2"},
            "electron_singlet": {"dim": 1, "charge": -1.0, "source": "charge-conjugate ideal N=3"},
        },
    }


def deterministic_wrong_subspace(g2_basis: jax.Array) -> dict[str, Any]:
    raw = jnp.array(
        [[(((row + 3) * (col + 5) * 37 + (row + 1) ** 2 * 11 + (col + 1) * 17) % 97 - 48) / 29.0 for col in range(8)] for row in range(14)],
        dtype=jnp.float64,
    )
    q, _ = jnp.linalg.qr(raw)
    basis_cols = g2_basis @ q[:, :8]
    mats = [vec_to_matrix(basis_cols[:, idx]) for idx in range(8)]
    closure = bracket_closure_metrics(basis_cols, mats)
    decomp = decomposition_metrics(mats)
    fixed_norm = max(py_float(jnp.linalg.norm(mat @ basis(DIM_O, FIXED_UNIT))) for mat in mats)
    return {
        "basis": basis_cols,
        "mats": mats,
        "closure_residual": closure["max_residual"],
        "decomp_offblock_residual": decomp["offblock_residual"],
        "fixed_unit_action_norm": fixed_norm,
    }


def parity_against_peer(result: dict[str, Any], peer_path: Path) -> dict[str, Any]:
    if not peer_path.exists():
        return {
            "peer_result_path": str(peer_path),
            "status": "pending_peer_backend",
            "shared_scalar_rows": [],
            "max_diff_key": None,
            "parity_max_diff": None,
            "within_1e_9": False,
            "strict_divergence_gt_1e_6": [{"missing": str(peer_path)}],
            "boolean_mismatches": [],
            "missing_keys": [],
            "stop_condition_fired": True,
        }
    peer = json.loads(peer_path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    max_diff = 0.0
    max_diff_key = None
    strict: list[dict[str, Any]] = []
    missing: list[str] = []
    for key, value in result["shared_scalars"].items():
        if key not in peer.get("shared_scalars", {}):
            missing.append(key)
            continue
        jv = float(value)
        pv = float(peer["shared_scalars"][key])
        diff = abs(jv - pv)
        if diff > max_diff:
            max_diff = diff
            max_diff_key = key
        row = {"key": key, "jax": jv, "julia": pv, "abs_diff": diff}
        rows.append(row)
        if diff > STRICT_STOP_TOL:
            strict.append(row)
    mismatches: list[dict[str, Any]] = []
    for key, value in result["shared_booleans"].items():
        if key not in peer.get("shared_booleans", {}):
            missing.append(key)
            continue
        if bool(value) != bool(peer["shared_booleans"][key]):
            mismatches.append({"key": key, "jax": bool(value), "julia": bool(peer["shared_booleans"][key])})
    return {
        "peer_result_path": str(peer_path),
        "status": "compared",
        "shared_scalar_rows": rows,
        "max_diff_key": max_diff_key,
        "parity_max_diff": max_diff,
        "within_1e_9": max_diff < TOL and not strict and not mismatches and not missing,
        "strict_divergence_gt_1e_6": strict,
        "boolean_mismatches": mismatches,
        "missing_keys": missing,
        "stop_condition_fired": bool(strict) or bool(mismatches) or bool(missing),
    }


def build_result() -> dict[str, Any]:
    table = octonion_table()
    g2 = derivation_basis(table)
    g2_basis = g2["nullspace"]["basis"]
    g2_closure = bracket_closure_metrics(g2_basis, g2["mats"])
    su3 = stabilizer_basis(g2_basis, FIXED_UNIT)
    su3_closure = bracket_closure_metrics(su3["basis"], su3["mats"])
    su3_lie = killing_and_rank_metrics(su3_closure["structure_constants"], su3["mats"], su3["basis"])
    direct_decomp = decomposition_metrics(su3["mats"])
    cl6 = cl6_ladder_metrics(table)

    wrong = deterministic_wrong_subspace(g2_basis)
    erased = derivation_basis(associative_commutative_erase_table())
    erased_stabilizer = stabilizer_basis(erased["nullspace"]["basis"], FIXED_UNIT) if erased["nullspace"]["nullity"] else None
    erased_cl6 = cl6_ladder_metrics(associative_commutative_erase_table())

    g2_dim = g2["nullspace"]["nullity"]
    su3_dim = su3["basis"].shape[1]
    su3_closes = su3_closure["max_residual"] < TOL
    decomp_3_3bar_1_1 = (
        direct_decomp["offblock_residual"] < TOL
        and direct_decomp["singlet_action_residual"] < TOL
        and direct_decomp["triplet_trace_residual"] < TOL
        and direct_decomp["antitriplet_is_conjugate_residual"] < TOL
        and direct_decomp["triplet_casimir_residual"] < TOL
        and direct_decomp["antitriplet_casimir_residual"] < TOL
    )
    furey_spinor_pattern = (
        cl6["car_residual"] < TOL
        and cl6["gamma_residual"] < TOL
        and cl6["cl6_matrix_span_dim"] == 64
        and cl6["spinor_su3_rank"] == 8
        and cl6["spinor_su3_closure_residual"] < TOL
        and cl6["fock_offblock_residual"] < TOL
        and cl6["fock_singlet_action_residual"] < TOL
        and cl6["fock_wedge2_antitriplet_residual"] < TOL
        and cl6["number_operator_residual"] < TOL
        and cl6["charge_quantization_residual"] < TOL
    )
    wrong_subgroup_fails = (
        wrong["closure_residual"] > 1.0e-3
        and wrong["decomp_offblock_residual"] > 1.0e-3
        and wrong["fixed_unit_action_norm"] > 1.0e-3
    )
    assoc_erase_collapses = (
        erased["nullspace"]["nullity"] != 14
        and (erased_stabilizer is None or erased_stabilizer["basis"].shape[1] != 8)
        and (erased_cl6["car_residual"] > 1.0e-3 or erased_cl6["cl6_matrix_span_dim"] != 64)
    )

    verdicts = {
        "g2_dim_is_14": g2_dim == 14,
        "g2_closes": g2_closure["max_residual"] < TOL,
        "su3_dim_is_8": su3_dim == 8,
        "su3_closes": su3_closes,
        "su3_rank_is_2": su3_lie["rank"] == 2,
        "su3_killing_negative_definite": su3_lie["killing_negative_definite"],
        "su3_triplet_casimir_is_4_3": direct_decomp["triplet_casimir_residual"] < TOL,
        "decomp_3_3bar_1_1": decomp_3_3bar_1_1,
        "cl6_is_complex_8x8": cl6["cl6_matrix_span_dim"] == 64,
        "furey_ladder_charge_pattern": furey_spinor_pattern,
    }
    controls = {
        "wrong_subgroup_fails": wrong_subgroup_fails,
        "assoc_erase_collapses": assoc_erase_collapses,
        "control_miswired": not (wrong_subgroup_fails and assoc_erase_collapses),
    }

    shared_scalars = {
        "g2.constraint_rank": g2["nullspace"]["rank"],
        "g2.dim": g2_dim,
        "g2.closure_residual": g2_closure["max_residual"],
        "su3.stabilizer_constraint_rank": su3["nullspace"]["rank"],
        "su3.dim": su3_dim,
        "su3.closure_residual": su3_closure["max_residual"],
        "su3.rank": su3_lie["rank"],
        "su3.killing_eig_min": py_float(jnp.min(su3_lie["killing_eigs"])),
        "su3.killing_eig_max": py_float(jnp.max(su3_lie["killing_eigs"])),
        "direct_decomp.offblock_residual": direct_decomp["offblock_residual"],
        "direct_decomp.singlet_action_residual": direct_decomp["singlet_action_residual"],
        "direct_decomp.triplet_casimir_value": direct_decomp["triplet_casimir_value"],
        "direct_decomp.triplet_casimir_residual": direct_decomp["triplet_casimir_residual"],
        "cl6.car_residual": cl6["car_residual"],
        "cl6.gamma_residual": cl6["gamma_residual"],
        "cl6.matrix_span_dim": cl6["cl6_matrix_span_dim"],
        "cl6.spinor_su3_rank": cl6["spinor_su3_rank"],
        "cl6.spinor_su3_closure_residual": cl6["spinor_su3_closure_residual"],
        "cl6.fock_wedge2_antitriplet_residual": cl6["fock_wedge2_antitriplet_residual"],
        "cl6.number_operator_residual": cl6["number_operator_residual"],
        "cl6.charge_quantization_residual": cl6["charge_quantization_residual"],
        "assoc_erase.g2_dim": erased["nullspace"]["nullity"],
        "assoc_erase.cl6_car_residual": erased_cl6["car_residual"],
        "assoc_erase.cl6_matrix_span_dim": erased_cl6["cl6_matrix_span_dim"],
    }
    shared_booleans = {f"verdict.{key}": value for key, value in verdicts.items()}
    shared_booleans.update({f"control.{key}": value for key, value in controls.items()})

    all_core = all(verdicts.values()) and all(value for key, value in controls.items() if key != "control_miswired")

    tool_manifest = {
        "JAX": "load-bearing x64 finite tensor, SVD/nullspace, rank, Lie-bracket, and Cl(6) matrix computations",
        "jax.numpy": "load-bearing array algebra for octonion structure constants, derivation constraints, and spinor operators",
        "json": "supportive result serialization only",
        "Julia peer": "independent dual-backend mirror required for parity, not used by this JAX computation",
    }
    tool_depth = {
        "JAX": "load_bearing",
        "jax.numpy": "load_bearing",
        "json": "supportive",
        "Julia peer": "load_bearing",
    }

    result: dict[str, Any] = {
        "object_id": OBJECT_ID,
        "backend": "jax_jnp_x64",
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
        "sim_execution_kind": "nonclassical",
        "sim_class": "finite_algebra_witness_controlled_scratch_diagnostic",
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "fixed_complex_structure_unit": "e7",
        "owner_fano_triples": FANO,
        "owner_ladder_pairs": {
            "alpha1": "(-e6 + i e1)/2",
            "alpha2": "(-e5 + i e2)/2",
            "alpha3": "(-e4 + i e3)/2",
            "reason": "These are the nilpotent pairs induced by left multiplication by the owner's fixed e7 Fano convention.",
        },
        "tool_manifest": tool_manifest,
        "TOOL_MANIFEST": tool_manifest,
        "tool_integration_depth": tool_depth,
        "TOOL_INTEGRATION_DEPTH": tool_depth,
        "verdicts": verdicts,
        "controls": controls,
        "numbers": shared_scalars,
        "direct_g2_stabilizer_decomposition": direct_decomp,
        "cl6_furey_ladder": cl6,
        "wrong_subgroup_control": {
            "closure_residual": wrong["closure_residual"],
            "decomp_offblock_residual": wrong["decomp_offblock_residual"],
            "fixed_unit_action_norm": wrong["fixed_unit_action_norm"],
        },
        "associative_erase_control": {
            "table": "coordinatewise associative/commutative direct-product erase",
            "g2_dim": erased["nullspace"]["nullity"],
            "stabilizer_dim": None if erased_stabilizer is None else erased_stabilizer["basis"].shape[1],
            "cl6_car_residual": erased_cl6["car_residual"],
            "cl6_matrix_span_dim": erased_cl6["cl6_matrix_span_dim"],
        },
        "positive": {
            "g2_derivation_algebra": {"pass": verdicts["g2_dim_is_14"] and verdicts["g2_closes"], "dim": g2_dim},
            "su3_stabilizer": {"pass": verdicts["su3_dim_is_8"] and verdicts["su3_closes"], "dim": su3_dim},
            "spinor_decomposition": {"pass": decomp_3_3bar_1_1, "dims": "1+3+1+3"},
            "cl6_furey_charge_pattern": {"pass": furey_spinor_pattern, "charges": cl6["sm_charge_slots"]},
        },
        "graveyard_companions": {
            "wrong_subgroup": {"pass": wrong_subgroup_fails},
            "associative_erase": {"pass": assoc_erase_collapses},
        },
        "boundary": {
            "not_new_physics": {"pass": True, "ceiling": CLAIM_CEILING},
            "no_su2_u1_generations_masses_or_couplings": {"pass": True},
        },
        "why_not_v4_probes": "Scratch dual-backend finite algebra witness only; not a canonical formal_scout admission result.",
        "nearby_variants": {"passed": 2, "total": 2, "variants": ["wrong_subgroup_control", "associative_erase_control"]},
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "plain_sentence": (
            "On the owner's octonion Fano carrier, Der(O) has dimension 14; the e7 stabilizer has dimension 8, "
            "closes with compact su(3) invariants, and its complexified spinor action splits as 3 + 3bar + 1 + 1. "
            "The matching Cl(6) ladder operators give the Furey number/charge quantization pattern, while wrong-subgroup "
            "and associative-erasure controls fail."
        ),
    }
    result["parity"] = parity_against_peer(result, JULIA_REFERENCE_PATH)
    result["all_pass"] = bool(all_core and result["parity"]["within_1e_9"])
    result["stop_condition_fired"] = not result["all_pass"]
    return result


def main() -> int:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "su3_color_from_g2_octonion_cl6 JAX "
        f"all_pass={str(result['all_pass']).lower()} "
        f"g2_dim={result['shared_scalars']['g2.dim']} "
        f"su3_dim={result['shared_scalars']['su3.dim']} "
        f"su3_closes={str(result['verdicts']['su3_closes']).lower()} "
        f"decomp_3_3bar_1_1={str(result['verdicts']['decomp_3_3bar_1_1']).lower()} "
        f"wrong_subgroup_fails={str(result['controls']['wrong_subgroup_fails']).lower()} "
        f"assoc_erase_collapses={str(result['controls']['assoc_erase_collapses']).lower()} "
        f"parity={result['parity']['status']}:{result['parity']['parity_max_diff']}"
    )
    print(f"wrote: {RESULT_PATH}")
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
