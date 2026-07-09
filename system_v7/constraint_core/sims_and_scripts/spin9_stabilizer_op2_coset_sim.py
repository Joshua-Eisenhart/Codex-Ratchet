#!/usr/bin/env python3
"""Spin(9) stabilizer and OP2 coset from the Albert/F4 derivation space.

Scratch diagnostic, promotion_allowed=false.

This extends exceptional_lie_ratchet_sim one rung by recomputing F4 as the
derivation algebra of J3(O), then imposing the linear stabilizer condition
D(e)=0 for a primitive idempotent e=diag(1,0,0). The target measurement is:

    dim Der(J3(O)) = 52
    dim {D in f4 | D(e)=0} = 36
    coset dimension = 52 - 36 = 16

The 16 is reported as the computed OP2 tangent/coset dimension, not as a
citation. Controls include a generic non-idempotent stabilizer, the rank-2
complement idempotent, and a one-sign corrupted Fano table upstream break.
"""

from __future__ import annotations

import datetime as dt
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
SOURCE_PATH = ROOT / "system_v7/constraint_core/sims_and_scripts/spin9_stabilizer_op2_coset_sim.py"
RESULT_PATH = ROOT / "system_v7/constraint_core/sims_and_scripts/spin9_stabilizer_op2_coset_sim_results.json"
UPSTREAM_SOURCE = ROOT / "system_v7/constraint_core/sims_and_scripts/exceptional_lie_ratchet_sim.py"
J3O_GATE_SOURCE = ROOT / "system_v7/constraint_core/sims_and_scripts/j3o_bloch_body_entropy_pawl_sim.py"

SIM_ID = "spin9_stabilizer_op2_coset"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
SEED = 108
SVD_THRESHOLD = 1.0e-8

FANO = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
]

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Fano octonion table, Albert product structure constants, SVD nullspaces, and stabilizer rank counts",
    },
    "scipy": {
        "tried": True,
        "used": True,
        "reason": "supportive pivoted-QR minor selection for the optional z3 nonzero-minor certificate",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive lower-bound nonzero-minor check on the measured primitive stabilizer action rank when available",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive paths, timestamps, JSON serialization, and report formatting",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "scipy": "supportive",
    "z3": "supportive",
    "python_stdlib": "supportive",
}


def basis(dim: int, idx: int) -> np.ndarray:
    out = np.zeros(dim, dtype=float)
    out[idx] = 1.0
    return out


def setprod(table: np.ndarray, a: int, b: int, c: int, s: float) -> None:
    table[c, a, b] = s


def octonion_table(*, corrupt_one_sign: bool = False) -> np.ndarray:
    table = np.zeros((8, 8, 8), dtype=float)
    for a in range(8):
        setprod(table, 0, a, a, 1.0)
        setprod(table, a, 0, a, 1.0)
    for a in range(1, 8):
        setprod(table, a, a, 0, -1.0)
    for i, j, k in FANO:
        for a, b, c, s in (
            (i, j, k, 1.0),
            (j, k, i, 1.0),
            (k, i, j, 1.0),
            (j, i, k, -1.0),
            (k, j, i, -1.0),
            (i, k, j, -1.0),
        ):
            setprod(table, a, b, c, s)
    if corrupt_one_sign:
        table[3, 1, 2] *= -1.0
    return table


def multiply(table: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    return np.einsum("cab,a,b->c", table, x, y)


def conjugate(x: np.ndarray) -> np.ndarray:
    out = np.array(x, dtype=float, copy=True)
    out[1:] *= -1.0
    return out


def norm2(x: np.ndarray) -> float:
    return float(np.dot(x, x))


def real_part(x: np.ndarray) -> float:
    return float(x[0])


def j3_zero() -> np.ndarray:
    return np.zeros((3, 3, 8), dtype=float)


def j3_from_parts(diag: np.ndarray, x01: np.ndarray, x02: np.ndarray, x12: np.ndarray) -> np.ndarray:
    m = j3_zero()
    for i in range(3):
        m[i, i, 0] = float(diag[i])
    m[0, 1, :] = x01
    m[1, 0, :] = conjugate(x01)
    m[0, 2, :] = x02
    m[2, 0, :] = conjugate(x02)
    m[1, 2, :] = x12
    m[2, 1, :] = conjugate(x12)
    return m


def j3_diag(values: list[float] | tuple[float, float, float] | np.ndarray) -> np.ndarray:
    z = np.zeros(8, dtype=float)
    return j3_from_parts(np.asarray(values, dtype=float), z, z, z)


def j3_trace(a: np.ndarray) -> float:
    return float(a[0, 0, 0] + a[1, 1, 0] + a[2, 2, 0])


def j3_matmul(table: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    out = j3_zero()
    for i in range(3):
        for k in range(3):
            acc = np.zeros(8, dtype=float)
            for j in range(3):
                acc += multiply(table, a[i, j, :], b[j, k, :])
            out[i, k, :] = acc
    return out


def jordan(table: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return 0.5 * (j3_matmul(table, a, b) + j3_matmul(table, b, a))


def sigma2_j3(a: np.ndarray) -> float:
    d0 = float(a[0, 0, 0])
    d1 = float(a[1, 1, 0])
    d2 = float(a[2, 2, 0])
    return float(d0 * d1 + d0 * d2 + d1 * d2 - norm2(a[0, 1, :]) - norm2(a[0, 2, :]) - norm2(a[1, 2, :]))


def det_j3(table: np.ndarray, a: np.ndarray) -> float:
    d0 = float(a[0, 0, 0])
    d1 = float(a[1, 1, 0])
    d2 = float(a[2, 2, 0])
    x01 = a[0, 1, :]
    x02 = a[0, 2, :]
    x12 = a[1, 2, :]
    triple = real_part(multiply(table, multiply(table, x01, x12), conjugate(x02)))
    return float(d0 * d1 * d2 + 2.0 * triple - d0 * norm2(x12) - d1 * norm2(x02) - d2 * norm2(x01))


def albert_basis() -> list[np.ndarray]:
    items: list[np.ndarray] = []
    for i in range(3):
        m = j3_zero()
        m[i, i, 0] = 1.0
        items.append(m)
    for i, j in ((0, 1), (0, 2), (1, 2)):
        for a in range(8):
            m = j3_zero()
            e = basis(8, a)
            m[i, j, :] = e
            m[j, i, :] = conjugate(e)
            items.append(m)
    return items


def structure_consts(table: np.ndarray, items: list[np.ndarray]) -> np.ndarray:
    n = len(items)
    bmat = np.array([b.flatten() for b in items]).T
    consts = np.zeros((n, n, n), dtype=float)
    for i in range(n):
        for j in range(n):
            x, *_ = np.linalg.lstsq(bmat, jordan(table, items[i], items[j]).flatten(), rcond=None)
            consts[:, i, j] = x
    return consts


def derivation_constraint_matrix(consts: np.ndarray) -> np.ndarray:
    n = consts.shape[0]
    rows: list[np.ndarray] = []
    for i in range(n):
        for j in range(i, n):
            for k in range(n):
                row = np.zeros((n, n), dtype=float)
                for a in range(n):
                    row[a, i] += consts[k, a, j]
                    row[a, j] += consts[k, i, a]
                for b in range(n):
                    row[k, b] -= consts[b, i, j]
                rows.append(row.flatten())
    return np.array(rows, dtype=float)


def svd_rank(matrix: np.ndarray, threshold: float = SVD_THRESHOLD) -> tuple[int, np.ndarray]:
    singular_values = np.linalg.svd(matrix, compute_uv=False)
    return int(np.sum(singular_values > threshold)), singular_values


def svd_report(singular_values: np.ndarray, rank: int) -> dict[str, Any]:
    return {
        "threshold": SVD_THRESHOLD,
        "rank": int(rank),
        "largest_singular_value": float(singular_values[0]) if len(singular_values) else 0.0,
        "smallest_singular_value": float(singular_values[-1]) if len(singular_values) else 0.0,
        "last_counted_singular_value": float(singular_values[rank - 1]) if rank > 0 and rank <= len(singular_values) else None,
        "first_uncounted_singular_value": float(singular_values[rank]) if rank < len(singular_values) else None,
    }


def f4_derivation_space(table: np.ndarray) -> dict[str, Any]:
    items = albert_basis()
    consts = structure_consts(table, items)
    constraints = derivation_constraint_matrix(consts)
    u, singular_values, vt = np.linalg.svd(constraints, full_matrices=True)
    del u
    rank = int(np.sum(singular_values > SVD_THRESHOLD))
    nullspace = vt[rank:, :]
    return {
        "basis": items,
        "structure_constants": consts,
        "constraints": constraints,
        "constraint_rank": rank,
        "constraint_singular_values": singular_values,
        "nullspace": nullspace,
        "dimension": int(nullspace.shape[0]),
    }


def coords_from_element(items: list[np.ndarray], element: np.ndarray) -> np.ndarray:
    bmat = np.array([b.flatten() for b in items]).T
    coords, *_ = np.linalg.lstsq(bmat, element.flatten(), rcond=None)
    return coords


def element_from_coords(items: list[np.ndarray], coords: np.ndarray) -> np.ndarray:
    out = j3_zero()
    for coeff, item in zip(coords, items):
        out = out + float(coeff) * item
    return out


def primitive_idempotent_gate(table: np.ndarray, element: np.ndarray) -> dict[str, Any]:
    square = jordan(table, element, element)
    trace = j3_trace(element)
    sig = sigma2_j3(element)
    det = det_j3(table, element)
    residual = float(np.linalg.norm(square - element))
    return {
        "trace": trace,
        "sigma2": sig,
        "det": det,
        "idempotent_residual": residual,
        "pass": bool(abs(trace - 1.0) < 1.0e-12 and abs(sig) < 1.0e-12 and abs(det) < 1.0e-12 and residual < 1.0e-12),
    }


def rank2_idempotent_gate(table: np.ndarray, element: np.ndarray) -> dict[str, Any]:
    square = jordan(table, element, element)
    trace = j3_trace(element)
    sig = sigma2_j3(element)
    det = det_j3(table, element)
    residual = float(np.linalg.norm(square - element))
    return {
        "trace": trace,
        "sigma2": sig,
        "det": det,
        "idempotent_residual": residual,
        "primitive_gate_pass": bool(abs(trace - 1.0) < 1.0e-12 and abs(sig) < 1.0e-12 and abs(det) < 1.0e-12),
        "rank2_idempotent_signature": bool(abs(trace - 2.0) < 1.0e-12 and abs(sig - 1.0) < 1.0e-12 and abs(det) < 1.0e-12 and residual < 1.0e-12),
    }


def condition_matrix_from_vectors(nullspace: np.ndarray, vectors: list[np.ndarray]) -> np.ndarray:
    n = vectors[0].shape[0]
    blocks = []
    for vector in vectors:
        block = np.stack([der.reshape(n, n) @ vector for der in nullspace], axis=1)
        blocks.append(block)
    return np.vstack(blocks)


def direct_stabilizer_rows(vectors: list[np.ndarray]) -> np.ndarray:
    n = vectors[0].shape[0]
    rows = []
    for vector in vectors:
        for out_idx in range(n):
            row = np.zeros((n, n), dtype=float)
            row[out_idx, :] = vector
            rows.append(row.flatten())
    return np.array(rows, dtype=float)


def z3_nonzero_minor_certificate(matrix: np.ndarray, rank: int) -> dict[str, Any]:
    if rank <= 0:
        return {"attempted": False, "reason": "rank is zero"}
    try:
        from scipy.linalg import qr
        from z3 import RealVal, Solver, unsat
    except Exception as exc:  # pragma: no cover - depends on optional packages
        return {"attempted": True, "available": False, "reason": repr(exc)}

    try:
        _, _, col_pivots = qr(matrix, pivoting=True, mode="economic")
        cols = [int(x) for x in col_pivots[:rank]]
        selected_cols = matrix[:, cols]
        _, _, row_pivots = qr(selected_cols.T, pivoting=True, mode="economic")
        rows = [int(x) for x in row_pivots[:rank]]
        minor = selected_cols[rows, :]
        det_value = float(np.linalg.det(minor))
        solver = Solver()
        det_const = RealVal(format(det_value, ".17e"))
        solver.add(det_const == 0)
        check = solver.check()
        return {
            "attempted": True,
            "available": True,
            "scope": "supportive lower-bound certificate for rank >= measured_rank on the floating SVD-basis action matrix",
            "rank_lower_bound": int(rank),
            "minor_shape": [int(rank), int(rank)],
            "selected_rows": rows,
            "selected_columns": cols,
            "determinant_decimal": det_value,
            "z3_check_det_equals_zero": str(check),
            "nonzero_minor_certified": bool(check == unsat),
            "limitation": "This is not an exact rational certificate for the original 729-variable derivation matrix; the integer rank verdict remains SVD-threshold based.",
        }
    except Exception as exc:  # pragma: no cover - defensive report path
        return {"attempted": True, "available": True, "error": repr(exc)}


def stabilizer_measure(space: dict[str, Any], vectors: list[np.ndarray], label: str, *, direct_augmented: bool = False) -> dict[str, Any]:
    nullspace = space["nullspace"]
    f4_dim = int(space["dimension"])
    cond = condition_matrix_from_vectors(nullspace, vectors)
    action_rank, action_singular_values = svd_rank(cond)
    stabilizer_dim = f4_dim - action_rank
    out = {
        "label": label,
        "vectors_fixed": len(vectors),
        "condition_matrix_shape": [int(x) for x in cond.shape],
        "action_rank_on_f4": int(action_rank),
        "stabilizer_dimension": int(stabilizer_dim),
        "coset_or_orbit_dimension": int(f4_dim - stabilizer_dim),
        "svd": svd_report(action_singular_values, action_rank),
    }
    if direct_augmented:
        direct_rows = direct_stabilizer_rows(vectors)
        augmented = np.vstack([space["constraints"], direct_rows])
        direct_rank, direct_singular_values = svd_rank(augmented)
        out["direct_729_variable_augmented_check"] = {
            "augmented_matrix_shape": [int(x) for x in augmented.shape],
            "augmented_rank": int(direct_rank),
            "augmented_nullity": int(augmented.shape[1] - direct_rank),
            "rank_added_over_f4_constraints": int(direct_rank - space["constraint_rank"]),
            "svd": svd_report(direct_singular_values, direct_rank),
        }
    return out


def complex_subalgebra_preservation_matrix(nullspace: np.ndarray) -> np.ndarray:
    n = 27
    complex_j3_indices = [0, 1, 2]
    for start in (3, 11, 19):
        complex_j3_indices.extend([start, start + 1])
    pin = np.zeros((n, n), dtype=float)
    pout = np.eye(n, dtype=float)
    for idx in complex_j3_indices:
        pin[idx, idx] = 1.0
        pout[idx, idx] = 0.0
    return np.stack([(pout @ der.reshape(n, n) @ pin).flatten() for der in nullspace], axis=1)


def left_complex_structure_centralizer_matrix(table: np.ndarray, nullspace: np.ndarray) -> np.ndarray:
    n = 27
    unit_i = basis(8, 1)
    left_i = np.zeros((8, 8), dtype=float)
    for col in range(8):
        left_i[:, col] = multiply(table, unit_i, basis(8, col))
    j = np.zeros((n, n), dtype=float)
    for start in (3, 11, 19):
        j[start : start + 8, start : start + 8] = left_i
    return np.stack([(der.reshape(n, n) @ j - j @ der.reshape(n, n)).flatten() for der in nullspace], axis=1)


def matrix_nullity_report(matrix: np.ndarray, ambient_dim: int, label: str) -> dict[str, Any]:
    rank, singular_values = svd_rank(matrix)
    return {
        "label": label,
        "condition_matrix_shape": [int(x) for x in matrix.shape],
        "condition_rank": int(rank),
        "stabilizer_dimension": int(ambient_dim - rank),
        "svd": svd_report(singular_values, rank),
    }


def compute_corrupted_f4_dimension() -> dict[str, Any]:
    corrupt_table = octonion_table(corrupt_one_sign=True)
    corrupt_space = f4_derivation_space(corrupt_table)
    dim = int(corrupt_space["dimension"])
    rank = int(corrupt_space["constraint_rank"])
    return {
        "corruption": "single upstream sign flip: e1*e2 coefficient of e3 multiplied by -1",
        "f4_dimension_after_corruption": dim,
        "constraint_rank_after_corruption": rank,
        "breaks_52_gate": bool(dim != 52),
        "svd": svd_report(corrupt_space["constraint_singular_values"], rank),
    }


def build_result() -> dict[str, Any]:
    rng = np.random.default_rng(SEED)
    table = octonion_table()
    space = f4_derivation_space(table)
    items = space["basis"]

    primitive_element = j3_diag([1.0, 0.0, 0.0])
    rank2_element = j3_diag([0.0, 1.0, 1.0])
    generic_diag_element = j3_diag([1.0, 2.0, 3.0])
    generic_full_coords = rng.normal(size=27)
    generic_full_element = element_from_coords(items, generic_full_coords)

    primitive = coords_from_element(items, primitive_element)
    rank2 = coords_from_element(items, rank2_element)
    generic_diag = coords_from_element(items, generic_diag_element)

    primitive_stabilizer = stabilizer_measure(space, [primitive], "primitive_idempotent_diag_100", direct_augmented=True)
    rank2_stabilizer = stabilizer_measure(space, [rank2], "rank2_idempotent_diag_011_complement_control")
    generic_diag_stabilizer = stabilizer_measure(space, [generic_diag], "generic_distinct_diagonal_non_idempotent_control")
    generic_full_stabilizer = stabilizer_measure(space, [generic_full_coords], "seeded_generic_full_non_idempotent_control")

    peirce_x01_real = basis(27, 3)
    peirce_x02_real = basis(27, 11)
    spin7_probe = stabilizer_measure(space, [primitive, peirce_x01_real], "stretch_point_plus_one_peirce_spinor")
    g2_probe = stabilizer_measure(
        space,
        [primitive, peirce_x01_real, peirce_x02_real],
        "stretch_point_plus_two_compatible_peirce_spinors",
    )

    complex_preservation = matrix_nullity_report(
        complex_subalgebra_preservation_matrix(space["nullspace"]),
        int(space["dimension"]),
        "stretch_preserve_embedded_J3C_subalgebra",
    )
    left_complex_centralizer = matrix_nullity_report(
        left_complex_structure_centralizer_matrix(table, space["nullspace"]),
        int(space["dimension"]),
        "diagnostic_left_multiplication_i_centralizer_not_SU3xSU3_target",
    )

    corrupted = compute_corrupted_f4_dimension()
    f4_dim = int(space["dimension"])
    spin9_dim = int(primitive_stabilizer["stabilizer_dimension"])
    coset_dim = int(f4_dim - spin9_dim)
    primitive_gate = primitive_idempotent_gate(table, primitive_element)
    rank2_gate = rank2_idempotent_gate(table, rank2_element)

    main_dims_on_nose = bool(f4_dim == 52 and spin9_dim == 36 and coset_dim == 16 and primitive_gate["pass"])
    generic_control_flips = bool(
        generic_diag_stabilizer["stabilizer_dimension"] != spin9_dim
        and generic_full_stabilizer["stabilizer_dimension"] != spin9_dim
    )
    rank2_same_is_expected = bool(
        rank2_gate["rank2_idempotent_signature"] and rank2_stabilizer["stabilizer_dimension"] == spin9_dim
    )
    stretch_dims = {
        "spin7_probe_dim_21": bool(spin7_probe["stabilizer_dimension"] == 21),
        "g2_probe_dim_14": bool(g2_probe["stabilizer_dimension"] == 14),
        "J3C_preservation_dim_16": bool(complex_preservation["stabilizer_dimension"] == 16),
    }

    if f4_dim != 52 or not corrupted["breaks_52_gate"]:
        verdict = "upstream_broken"
    elif not main_dims_on_nose:
        verdict = "dimension_mismatch"
    else:
        verdict = "rung_derived"

    primitive_stabilizer["z3_certificate"] = z3_nonzero_minor_certificate(
        condition_matrix_from_vectors(space["nullspace"], [primitive]),
        primitive_stabilizer["action_rank_on_f4"],
    )

    return {
        "schema": "codex_ratchet.spin9_stabilizer_op2_coset_result.v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "upstream_source_path": str(UPSTREAM_SOURCE),
        "primitive_gate_source_path": str(J3O_GATE_SOURCE),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "sim_execution_kind": "classical",
        "sim_class": "exceptional_jordan_stabilizer_rank_probe",
        "seed": SEED,
        "svd_threshold": SVD_THRESHOLD,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_conventions_reused": {
            "FANO": [list(x) for x in FANO],
            "albert_basis_order": "3 diagonal basis elements, then octonion coordinates for slots (0,1), (0,2), (1,2)",
            "f4_derivation_method": "linear nullspace of D(x.y)=D(x).y+x.D(y) over the 27-dimensional Albert coordinate basis",
            "primitive_idempotent_gate": "trace=1, sigma2=0, det=0, and Jordan-square residual zero",
        },
        "f4_from_scratch": {
            "ambient_endomorphism_dimension": 729,
            "derivation_constraint_matrix_shape": [int(x) for x in space["constraints"].shape],
            "constraint_rank": int(space["constraint_rank"]),
            "f4_dimension": f4_dim,
            "svd": svd_report(space["constraint_singular_values"], int(space["constraint_rank"])),
        },
        "primary_rung": {
            "question": "Is F4 > Spin(9) computable as the stabilizer subalgebra of f4 fixing one primitive idempotent of J3(O), with OP2 coset dimension 16?",
            "primitive_idempotent": {
                "description": "e=diag(1,0,0)",
                "gate": primitive_gate,
            },
            "spin9_stabilizer": primitive_stabilizer,
            "computed_coset": {
                "formula": "dim(F4)-dim(stabilizer)",
                "f4_dimension": f4_dim,
                "stabilizer_dimension": spin9_dim,
                "coset_dimension": coset_dim,
                "matches_dim_OP2": bool(coset_dim == 16),
                "interpretation": "The 16-dimensional Cayley-plane tangent/coset dimension is computed from the stabilizer rank, not cited as an input.",
            },
        },
        "controls": {
            "rank2_idempotent_complement": {
                "gate": rank2_gate,
                "stabilizer": rank2_stabilizer,
                "flips_from_primitive": bool(rank2_stabilizer["stabilizer_dimension"] != spin9_dim),
                "honest_note": "This rank-2 idempotent is 1-e for a primitive e. Since derivations kill the Jordan unit, fixing 1-e is equivalent to fixing e, so this control does not flip and should not be used as a negative for the Spin(9) rung.",
            },
            "generic_distinct_diagonal_non_idempotent": {
                "stabilizer": generic_diag_stabilizer,
                "flips_from_primitive": bool(generic_diag_stabilizer["stabilizer_dimension"] != spin9_dim),
            },
            "seeded_generic_full_non_idempotent": {
                "coordinate_seed": SEED,
                "trace": j3_trace(generic_full_element),
                "sigma2": sigma2_j3(generic_full_element),
                "det": det_j3(table, generic_full_element),
                "idempotent_residual": float(np.linalg.norm(jordan(table, generic_full_element, generic_full_element) - generic_full_element)),
                "stabilizer": generic_full_stabilizer,
                "flips_from_primitive": bool(generic_full_stabilizer["stabilizer_dimension"] != spin9_dim),
            },
            "corrupted_fano_upstream": corrupted,
        },
        "stretch_attempts": {
            "spin7_from_point_plus_peirce_spinor": {
                "status": "measured",
                "stabilizer": spin7_probe,
                "target_dimension": 21,
                "dimension_match": bool(spin7_probe["stabilizer_dimension"] == 21),
            },
            "g2_from_point_plus_two_compatible_peirce_spinors": {
                "status": "measured",
                "stabilizer": g2_probe,
                "target_dimension": 14,
                "dimension_match": bool(g2_probe["stabilizer_dimension"] == 14),
            },
            "su3_su3_via_complex_subalgebra_preservation": {
                "status": "measured",
                "stabilizer": complex_preservation,
                "target_dimension": 16,
                "dimension_match": bool(complex_preservation["stabilizer_dimension"] == 16),
                "boundary": "This measures the f4 stabilizer of the embedded J3(C) coordinate subalgebra C=span(1,e1) inside each off-diagonal octonion slot.",
            },
            "left_complex_structure_centralizer_control": {
                "status": "measured_not_target",
                "stabilizer": left_complex_centralizer,
                "reason": "Commuting with left multiplication by e1 on all octonion slots gives dimension 10 here, so the SU(3)xSU(3) stretch claim is tied to preserving the embedded complex J3(C) subalgebra, not to this stricter centralizer.",
            },
        },
        "gates": {
            "dims_on_the_nose": main_dims_on_nose,
            "generic_controls_flip": generic_control_flips,
            "rank2_complement_same_expected": rank2_same_is_expected,
            "corrupted_fano_breaks_upstream_52": bool(corrupted["breaks_52_gate"]),
            "stretch_dimension_matches": stretch_dims,
        },
        "verdict": verdict,
        "all_pass": bool(verdict == "rung_derived"),
        "promotion_status": "diagnostic_only",
        "claim_ceiling": "Scratch diagnostic local rank computation only: derives F4, the primitive-idempotent stabilizer dimension, and the 16-dimensional OP2 coset from linear algebra over the constructed Albert product. No formal admission, no bridge, no Axis0, no canonical-by-process claim.",
        "eligible_consumers": [],
        "blocked_consumers": [
            "formal Lie algebra identification proof beyond dimension",
            "canonical-by-process promotion",
            "bridge, manifold, or Axis0 claims",
        ],
        "blocked_downstream_consumers": [
            "formal Lie algebra identification proof beyond dimension",
            "canonical-by-process promotion",
            "bridge, manifold, or Axis0 claims",
        ],
        "divergence_log": [
            {
                "surface": "generic_non_idempotent_stabilizer",
                "expected": "different dimension from primitive-idempotent stabilizer",
                "observed": {
                    "generic_distinct_diagonal_dim": generic_diag_stabilizer["stabilizer_dimension"],
                    "generic_full_dim": generic_full_stabilizer["stabilizer_dimension"],
                },
                "pass": generic_control_flips,
            },
            {
                "surface": "rank2_idempotent_complement",
                "expected_from_prompt": "different dimension",
                "observed": rank2_stabilizer["stabilizer_dimension"],
                "pass": rank2_same_is_expected,
                "reason": "The measured rank-2 idempotent is the complement of a primitive idempotent, so equality is the mathematically honest control outcome.",
            },
            {
                "surface": "corrupted_fano_table",
                "expected": "upstream f4 dimension not 52",
                "observed": corrupted["f4_dimension_after_corruption"],
                "pass": bool(corrupted["breaks_52_gate"]),
            },
        ],
    }


def print_summary(result: dict[str, Any]) -> None:
    f4 = result["f4_from_scratch"]
    primary = result["primary_rung"]
    controls = result["controls"]
    stretch = result["stretch_attempts"]

    print("SPIN9_STABILIZER_OP2_COSET_SIM")
    print(f"seed={SEED} classification={CLASSIFICATION} promotion_allowed={PROMOTION_ALLOWED}")
    print(f"svd_threshold={SVD_THRESHOLD:.1e}")
    print("")
    print("stabilizer dimension table:")
    print(
        "  F4 derivations of J3(O): "
        f"constraint_rank={f4['constraint_rank']} dim={f4['f4_dimension']} "
        f"matrix_shape={f4['derivation_constraint_matrix_shape']}"
    )
    spin9 = primary["spin9_stabilizer"]
    coset = primary["computed_coset"]
    print(
        "  fix primitive idempotent diag(1,0,0): "
        f"action_rank={spin9['action_rank_on_f4']} stabilizer_dim={spin9['stabilizer_dimension']} "
        f"coset_dim={coset['coset_dimension']} target=Spin(9):36 OP2:16"
    )
    print(
        "  direct augmented check: "
        f"rank={spin9['direct_729_variable_augmented_check']['augmented_rank']} "
        f"nullity={spin9['direct_729_variable_augmented_check']['augmented_nullity']} "
        f"rank_added={spin9['direct_729_variable_augmented_check']['rank_added_over_f4_constraints']}"
    )
    rank2 = controls["rank2_idempotent_complement"]["stabilizer"]
    print(
        "  rank2 complement diag(0,1,1): "
        f"action_rank={rank2['action_rank_on_f4']} stabilizer_dim={rank2['stabilizer_dimension']} "
        f"flip={controls['rank2_idempotent_complement']['flips_from_primitive']} "
        "note=complement_same_expected"
    )
    gdiag = controls["generic_distinct_diagonal_non_idempotent"]["stabilizer"]
    gfull = controls["seeded_generic_full_non_idempotent"]["stabilizer"]
    print(
        "  generic non-idempotent controls: "
        f"diag_distinct_dim={gdiag['stabilizer_dimension']} "
        f"seeded_full_dim={gfull['stabilizer_dimension']} "
        f"flip={result['gates']['generic_controls_flip']}"
    )
    corrupt = controls["corrupted_fano_upstream"]
    print(
        "  corrupted Fano upstream: "
        f"f4_dim={corrupt['f4_dimension_after_corruption']} breaks_52={corrupt['breaks_52_gate']}"
    )
    print("")
    print("stretch dimension probes:")
    print(
        "  point + one Peirce spinor: "
        f"dim={stretch['spin7_from_point_plus_peirce_spinor']['stabilizer']['stabilizer_dimension']} target=Spin(7):21"
    )
    print(
        "  point + two compatible Peirce spinors: "
        f"dim={stretch['g2_from_point_plus_two_compatible_peirce_spinors']['stabilizer']['stabilizer_dimension']} target=G2:14"
    )
    print(
        "  preserve embedded J3(C): "
        f"dim={stretch['su3_su3_via_complex_subalgebra_preservation']['stabilizer']['stabilizer_dimension']} target=SU(3)xSU(3):16"
    )
    print(
        "  left-complex-structure centralizer control: "
        f"dim={stretch['left_complex_structure_centralizer_control']['stabilizer']['stabilizer_dimension']} target=not_used"
    )
    z3cert = spin9["z3_certificate"]
    print("")
    print(
        "z3 rank certificate: "
        f"attempted={z3cert.get('attempted')} "
        f"nonzero_minor_certified={z3cert.get('nonzero_minor_certified')} "
        f"scope={z3cert.get('scope', z3cert.get('reason', z3cert.get('error')))}"
    )
    print("")
    print(
        f"verdict={result['verdict']} "
        f"dims_on_the_nose={result['gates']['dims_on_the_nose']} "
        f"generic_controls_flip={result['gates']['generic_controls_flip']} "
        f"corrupted_fano_breaks={result['gates']['corrupted_fano_breaks_upstream_52']}"
    )
    print(f"wrote: {RESULT_PATH}")


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print_summary(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
