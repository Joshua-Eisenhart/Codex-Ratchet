#!/usr/bin/env python3
"""Finite Alfsen-Shultz dynamical-correspondence probe.

Scratch diagnostic, promotion_allowed=false.

This script contrasts special matrix Jordan algebras, where observables carry a
Hamiltonian order-derivation correspondence, with the exceptional Albert
algebra H3(O), where the same single-observable commutator mechanism is absent.

The finite test is deliberately modest:
- Herm2(C) demonstrates the concrete qubit flow x -> exp(i t a) x exp(-i t a).
- Herm3(C) is the positive dynamical-correspondence control using
  D_a = (i/2)[a,.], the normalization satisfying [D_a,D_b]=-[L_a,L_b].
- H3(O) recomputes the 52-dimensional f4 derivation algebra from the Albert
  product, then runs deterministic finite linear feasibility constraints for a
  map from 26 traceless observables into those derivations.

The H3(O) verdict is a finite sampled obstruction, not a theorem proof.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
SOURCE_PATH = ROOT / "system_v7/constraint_core/sims_and_scripts/alfsen_shultz_correspondence_probe_sim.py"
RESULT_PATH = ROOT / "system_v7/constraint_core/sims_and_scripts/alfsen_shultz_correspondence_probe_sim_results.json"
SPIN9_SOURCE = ROOT / "system_v7/constraint_core/sims_and_scripts/spin9_stabilizer_op2_coset_sim.py"

SIM_ID = "alfsen_shultz_correspondence_probe"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
SEED = 20260708
TOL = 1.0e-8
RANK_TOL = 1.0e-8

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite matrix/Jordan products, Albert structure constants, derivation bases, QR/SVD rank checks, and sampled feasibility residuals",
    },
    "scipy": {
        "tried": True,
        "used": False,
        "reason": "optional rank backend; numpy QR/SVD path is sufficient when scipy is unavailable",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic paths, hashing, timestamps, and JSON emission",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "scipy": "supportive",
    "python_stdlib": "supportive",
}

FANO = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rank_report(matrix: np.ndarray, tol: float = RANK_TOL) -> dict[str, Any]:
    """Rank report using pivoted QR when available, with SVD extrema for small surfaces."""
    try:
        from scipy.linalg import qr  # type: ignore

        _, r, pivots = qr(matrix, pivoting=True, mode="economic")
        diag = np.abs(np.diag(r))
        rank = int(np.sum(diag > tol))
        return {
            "method": "scipy.linalg.qr_pivoted",
            "shape": [int(x) for x in matrix.shape],
            "rank": rank,
            "nullity": int(matrix.shape[1] - rank),
            "tol": tol,
            "last_counted_diag": float(diag[rank - 1]) if rank else None,
            "first_uncounted_diag": float(diag[rank]) if rank < len(diag) else None,
            "pivot_prefix": [int(x) for x in pivots[: min(12, len(pivots))]],
        }
    except Exception as exc:
        singular_values = np.linalg.svd(matrix, compute_uv=False)
        rank = int(np.sum(singular_values > tol))
        return {
            "method": "numpy.linalg.svd",
            "fallback_reason": repr(exc),
            "shape": [int(x) for x in matrix.shape],
            "rank": rank,
            "nullity": int(matrix.shape[1] - rank),
            "tol": tol,
            "largest_singular_value": float(singular_values[0]) if len(singular_values) else 0.0,
            "last_counted_singular_value": float(singular_values[rank - 1]) if rank else None,
            "first_uncounted_singular_value": float(singular_values[rank]) if rank < len(singular_values) else None,
        }


def matrix_rank(matrix: np.ndarray, tol: float = RANK_TOL) -> int:
    return int(rank_report(matrix, tol)["rank"])


def basis_vec(dim: int, idx: int) -> np.ndarray:
    out = np.zeros(dim, dtype=float)
    out[idx] = 1.0
    return out


def hermitian_basis(n: int) -> list[np.ndarray]:
    items: list[np.ndarray] = []
    for i in range(n):
        m = np.zeros((n, n), dtype=complex)
        m[i, i] = 1.0
        items.append(m)
    for i in range(n):
        for j in range(i + 1, n):
            real = np.zeros((n, n), dtype=complex)
            real[i, j] = 1.0
            real[j, i] = 1.0
            items.append(real)
            imag = np.zeros((n, n), dtype=complex)
            imag[i, j] = -1.0j
            imag[j, i] = 1.0j
            items.append(imag)
    return items


def hermitian_flat(m: np.ndarray) -> np.ndarray:
    return np.concatenate([m.real.reshape(-1), m.imag.reshape(-1)])


def coords_in_hermitian_basis(items: list[np.ndarray], m: np.ndarray) -> np.ndarray:
    bmat = np.array([hermitian_flat(x) for x in items]).T
    coords, *_ = np.linalg.lstsq(bmat, hermitian_flat(m), rcond=None)
    return coords


def hermitian_from_coords(items: list[np.ndarray], coords: np.ndarray) -> np.ndarray:
    out = np.zeros_like(items[0])
    for coeff, item in zip(coords, items):
        out = out + float(coeff) * item
    return out


def matrix_jordan(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return 0.5 * (a @ b + b @ a)


def left_multiplication_from_product(
    product,
    basis_items: list[Any],
    coord_fn,
    element_from_coords_fn,
    coords: np.ndarray,
) -> np.ndarray:
    n = len(basis_items)
    a = element_from_coords_fn(basis_items, coords)
    out = np.zeros((n, n), dtype=float)
    for j, b in enumerate(basis_items):
        out[:, j] = coord_fn(basis_items, product(a, b))
    return out


def hermitian_left_mats(n: int) -> dict[str, Any]:
    items = hermitian_basis(n)
    dim = len(items)
    all_coords = np.eye(dim)
    left_mats = [
        left_multiplication_from_product(matrix_jordan, items, coords_in_hermitian_basis, hermitian_from_coords, c)
        for c in all_coords
    ]
    if n == 2:
        traceless = [
            np.array([1.0, -1.0, 0.0, 0.0]),
            np.array([0.0, 0.0, 1.0, 0.0]),
            np.array([0.0, 0.0, 0.0, 1.0]),
        ]
    elif n == 3:
        traceless = [
            np.array([1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
            np.array([0.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        ]
        for idx in range(3, 9):
            traceless.append(basis_vec(9, idx))
    else:  # pragma: no cover - only n=2,3 are used
        raise ValueError(n)
    traceless = [np.asarray(x, dtype=float) for x in traceless]
    obs_left = [
        left_multiplication_from_product(matrix_jordan, items, coords_in_hermitian_basis, hermitian_from_coords, c)
        for c in traceless
    ]
    return {"items": items, "all_left": left_mats, "obs_coords": traceless, "obs_left": obs_left}


def commutator_derivation_matrix(items: list[np.ndarray], a: np.ndarray, scale: float) -> np.ndarray:
    dim = len(items)
    out = np.zeros((dim, dim), dtype=float)
    for j, x in enumerate(items):
        dx = scale * 1.0j * (a @ x - x @ a)
        out[:, j] = coords_in_hermitian_basis(items, dx)
    return out


def hermitian_derivation_basis(n: int, normalized: bool = True) -> dict[str, Any]:
    data = hermitian_left_mats(n)
    items = data["items"]
    scale = 0.5 if normalized else 1.0
    derivs = [
        commutator_derivation_matrix(items, hermitian_from_coords(items, coords), scale)
        for coords in data["obs_coords"]
    ]
    return {**data, "derivations": derivs, "scale": scale}


def density_entropy(rho: np.ndarray) -> float:
    vals = np.linalg.eigvalsh(rho)
    vals = np.clip(vals.real, 1.0e-15, None)
    return float(-np.sum(vals * np.log(vals)))


def expm_hermitian_flow(a: np.ndarray, t: float) -> np.ndarray:
    vals, vecs = np.linalg.eigh(a)
    return vecs @ np.diag(np.exp(1.0j * t * vals)) @ vecs.conj().T


def herm2_special_demo() -> dict[str, Any]:
    data = hermitian_left_mats(2)
    items = data["items"]
    a = np.array([[0.7, 0.2 - 0.35j], [0.2 + 0.35j, -0.4]], dtype=complex)
    b = np.array([[0.1, -0.3 + 0.15j], [-0.3 - 0.15j, 0.8]], dtype=complex)
    rho = np.array([[0.63, 0.18 - 0.11j], [0.18 + 0.11j, 0.37]], dtype=complex)
    rho = rho / np.trace(rho)
    t = 0.73
    u = expm_hermitian_flow(a, t)
    flow = lambda x: u @ x @ u.conj().T
    jordan_defect = np.linalg.norm(flow(matrix_jordan(b, rho)) - matrix_jordan(flow(b), flow(rho)))
    rho_flow = flow(rho)
    eig_before = np.linalg.eigvalsh(rho).real
    eig_after = np.linalg.eigvalsh(rho_flow).real

    full_basis_derivs = [
        commutator_derivation_matrix(items, item, 1.0).reshape(-1)
        for item in items
    ]
    full_map = np.array(full_basis_derivs).T
    traceless_derivs = [
        commutator_derivation_matrix(items, hermitian_from_coords(items, c), 1.0).reshape(-1)
        for c in data["obs_coords"]
    ]
    traceless_map = np.array(traceless_derivs).T

    # Finite-difference derivative check for the user-facing i[a,.] generator.
    eps = 1.0e-6
    finite_diff = (expm_hermitian_flow(a, eps) @ b @ expm_hermitian_flow(a, eps).conj().T - b) / eps
    generator = 1.0j * (a @ b - b @ a)
    return {
        "observable": [[float(x.real), float(x.imag)] for x in a.reshape(-1)],
        "time": t,
        "jordan_product_preservation_defect": float(jordan_defect),
        "state_trace_after": float(np.trace(rho_flow).real),
        "state_min_eigenvalue_before": float(np.min(eig_before)),
        "state_min_eigenvalue_after": float(np.min(eig_after)),
        "state_spectrum_shift_norm": float(np.linalg.norm(np.sort(eig_before) - np.sort(eig_after))),
        "entropy_before": density_entropy(rho),
        "entropy_after": density_entropy(rho_flow),
        "entropy_shift_abs": abs(density_entropy(rho) - density_entropy(rho_flow)),
        "physical_generator_i_commutator_finite_difference_defect": float(np.linalg.norm(finite_diff - generator)),
        "observable_to_delta_full_rank": matrix_rank(full_map),
        "observable_to_delta_full_kernel_dim": int(4 - matrix_rank(full_map)),
        "observable_to_delta_traceless_rank": matrix_rank(traceless_map),
        "injective_up_to_center": bool(matrix_rank(full_map) == 3 and matrix_rank(traceless_map) == 3),
        "center_kernel_note": "The identity observable maps to zero; the three traceless Pauli directions map injectively to rotations.",
    }


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


def omul(table: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    return np.einsum("cab,a,b->c", table, x, y)


def oconj(x: np.ndarray) -> np.ndarray:
    out = np.array(x, dtype=float, copy=True)
    out[1:] *= -1.0
    return out


def j3_zero() -> np.ndarray:
    return np.zeros((3, 3, 8), dtype=float)


def j3_from_parts(diag: np.ndarray, x01: np.ndarray, x02: np.ndarray, x12: np.ndarray) -> np.ndarray:
    m = j3_zero()
    for i in range(3):
        m[i, i, 0] = float(diag[i])
    m[0, 1, :] = x01
    m[1, 0, :] = oconj(x01)
    m[0, 2, :] = x02
    m[2, 0, :] = oconj(x02)
    m[1, 2, :] = x12
    m[2, 1, :] = oconj(x12)
    return m


def j3_diag(values: list[float] | tuple[float, float, float] | np.ndarray) -> np.ndarray:
    z = np.zeros(8, dtype=float)
    return j3_from_parts(np.asarray(values, dtype=float), z, z, z)


def j3_matmul(table: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    out = j3_zero()
    for i in range(3):
        for k in range(3):
            acc = np.zeros(8, dtype=float)
            for j in range(3):
                acc += omul(table, a[i, j, :], b[j, k, :])
            out[i, k, :] = acc
    return out


def j3_jordan(table: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return 0.5 * (j3_matmul(table, a, b) + j3_matmul(table, b, a))


def albert_basis() -> list[np.ndarray]:
    items: list[np.ndarray] = []
    for i in range(3):
        m = j3_zero()
        m[i, i, 0] = 1.0
        items.append(m)
    for i, j in ((0, 1), (0, 2), (1, 2)):
        for a in range(8):
            m = j3_zero()
            e = basis_vec(8, a)
            m[i, j, :] = e
            m[j, i, :] = oconj(e)
            items.append(m)
    return items


def albert_coords(items: list[np.ndarray], element: np.ndarray) -> np.ndarray:
    bmat = np.array([b.flatten() for b in items]).T
    coords, *_ = np.linalg.lstsq(bmat, element.flatten(), rcond=None)
    return coords


def albert_from_coords(items: list[np.ndarray], coords: np.ndarray) -> np.ndarray:
    out = j3_zero()
    for coeff, item in zip(coords, items):
        out = out + float(coeff) * item
    return out


def structure_consts_albert(table: np.ndarray, items: list[np.ndarray]) -> np.ndarray:
    n = len(items)
    bmat = np.array([b.flatten() for b in items]).T
    consts = np.zeros((n, n, n), dtype=float)
    for i in range(n):
        for j in range(n):
            x, *_ = np.linalg.lstsq(bmat, j3_jordan(table, items[i], items[j]).flatten(), rcond=None)
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


def nullspace_svd(matrix: np.ndarray, tol: float = RANK_TOL) -> tuple[np.ndarray, np.ndarray, int]:
    _, singular_values, vt = np.linalg.svd(matrix, full_matrices=True)
    rank = int(np.sum(singular_values > tol))
    return vt[rank:, :], singular_values, rank


def f4_derivation_space(table: np.ndarray) -> dict[str, Any]:
    items = albert_basis()
    consts = structure_consts_albert(table, items)
    constraints = derivation_constraint_matrix(consts)
    nullspace, singular_values, rank = nullspace_svd(constraints, RANK_TOL)
    return {
        "items": items,
        "structure_constants": consts,
        "constraints": constraints,
        "nullspace": nullspace,
        "constraint_rank": rank,
        "singular_values": singular_values,
        "dimension": int(nullspace.shape[0]),
    }


def left_mats_from_structure(consts: np.ndarray, obs_coords: list[np.ndarray]) -> list[np.ndarray]:
    n = consts.shape[0]
    mats = []
    for coords in obs_coords:
        mat = np.zeros((n, n), dtype=float)
        nz = np.nonzero(np.abs(coords) > 1.0e-12)[0]
        for j in range(n):
            acc = np.zeros(n)
            for i in nz:
                acc += coords[i] * consts[:, i, j]
            mat[:, j] = acc
        mats.append(mat)
    return mats


def albert_traceless_observable_coords(items: list[np.ndarray]) -> list[np.ndarray]:
    coords: list[np.ndarray] = []
    coords.append(albert_coords(items, j3_diag([1.0, -1.0, 0.0])))
    coords.append(albert_coords(items, j3_diag([0.0, 1.0, -1.0])))
    for idx in range(3, 27):
        coords.append(basis_vec(27, idx))
    return coords


def assemble_linear_feasibility_matrix(
    obs_coords: list[np.ndarray],
    obs_left: list[np.ndarray],
    derivations: list[np.ndarray],
    *,
    seed: int,
    covariance_pair_limit: int | None,
    vector_limit: int,
) -> tuple[np.ndarray, dict[str, Any]]:
    rng = np.random.default_rng(seed)
    p_dim = len(obs_coords)
    d_dim = len(derivations)
    n_dim = obs_left[0].shape[0]
    unknowns = p_dim * d_dim

    deriv_action = np.zeros((d_dim, p_dim, n_dim), dtype=float)
    for r, dmat in enumerate(derivations):
        for q, coord in enumerate(obs_coords):
            deriv_action[r, q, :] = dmat @ coord

    rows: list[np.ndarray] = []
    for p in range(p_dim):
        for q in range(p, p_dim):
            block = np.zeros((n_dim, unknowns), dtype=float)
            block[:, p * d_dim : (p + 1) * d_dim] += deriv_action[:, q, :].T
            block[:, q * d_dim : (q + 1) * d_dim] += deriv_action[:, p, :].T
            rows.append(block)

    pairs = [(i, j) for i in range(p_dim) for j in range(p_dim)]
    rng.shuffle(pairs)
    if covariance_pair_limit is not None:
        pairs = pairs[:covariance_pair_limit]
    vector_grid = [np.asarray(v, dtype=float) for v in obs_coords[: min(vector_limit, p_dim)]]
    while len(vector_grid) < vector_limit:
        vector_grid.append(rng.normal(size=n_dim))

    # Precompute the two commutator families used by [D_a,L_b]=[L_a,D_b].
    d_l_minus_l_d = np.zeros((d_dim, p_dim, n_dim, n_dim), dtype=float)
    l_d_minus_d_l = np.zeros((p_dim, d_dim, n_dim, n_dim), dtype=float)
    for r, dmat in enumerate(derivations):
        for q, lq in enumerate(obs_left):
            d_l_minus_l_d[r, q, :, :] = dmat @ lq - lq @ dmat
    for p, lp in enumerate(obs_left):
        for r, dmat in enumerate(derivations):
            l_d_minus_d_l[p, r, :, :] = lp @ dmat - dmat @ lp

    for p, q in pairs:
        for vector in vector_grid:
            block = np.zeros((n_dim, unknowns), dtype=float)
            block[:, p * d_dim : (p + 1) * d_dim] += np.einsum("rnk,k->nr", d_l_minus_l_d[:, q, :, :], vector)
            block[:, q * d_dim : (q + 1) * d_dim] -= np.einsum("rnk,k->nr", l_d_minus_d_l[p, :, :, :], vector)
            rows.append(block)

    matrix = np.vstack(rows)
    metadata = {
        "unknown_matrix_shape_observables_x_derivations": [p_dim, d_dim],
        "unknown_count": unknowns,
        "self_annihilation_polarized_pairs": int(p_dim * (p_dim + 1) / 2),
        "covariance_pairs_sampled": len(pairs),
        "state_grid_vectors_per_pair": len(vector_grid),
        "state_grid_policy": f"first {min(vector_limit, p_dim)} observable basis vectors, then seeded Gaussian fillers if needed",
    }
    return matrix, metadata


def commutator_axiom_residual(obs_left: list[np.ndarray], candidate_derivs: list[np.ndarray]) -> dict[str, Any]:
    max_residual = 0.0
    sum_residual = 0.0
    count = 0
    worst_pair = [0, 0]
    for i, di in enumerate(candidate_derivs):
        for j, dj in enumerate(candidate_derivs):
            target = -(obs_left[i] @ obs_left[j] - obs_left[j] @ obs_left[i])
            got = di @ dj - dj @ di
            residual = float(np.linalg.norm(got - target))
            sum_residual += residual
            count += 1
            if residual > max_residual:
                max_residual = residual
                worst_pair = [i, j]
    return {
        "pair_count": count,
        "max_residual": max_residual,
        "mean_residual": float(sum_residual / max(count, 1)),
        "worst_pair": worst_pair,
        "passes": bool(max_residual < 1.0e-7),
    }


def wrong_sign_commutator_residual(obs_left: list[np.ndarray], candidate_derivs: list[np.ndarray]) -> dict[str, Any]:
    max_residual = 0.0
    count = 0
    for i, di in enumerate(candidate_derivs):
        for j, dj in enumerate(candidate_derivs):
            wrong_target = obs_left[i] @ obs_left[j] - obs_left[j] @ obs_left[i]
            got = di @ dj - dj @ di
            max_residual = max(max_residual, float(np.linalg.norm(got - wrong_target)))
            count += 1
    return {"pair_count": count, "max_residual": max_residual, "passes": bool(max_residual < 1.0e-7)}


def linear_feasibility_report(
    label: str,
    obs_coords: list[np.ndarray],
    obs_left: list[np.ndarray],
    derivations: list[np.ndarray],
    *,
    seed: int,
    covariance_pair_limit: int | None,
    vector_limit: int,
) -> dict[str, Any]:
    matrix, metadata = assemble_linear_feasibility_matrix(
        obs_coords,
        obs_left,
        derivations,
        seed=seed,
        covariance_pair_limit=covariance_pair_limit,
        vector_limit=vector_limit,
    )
    ranks = rank_report(matrix)
    return {
        "label": label,
        "linear_axioms": [
            "polarized self-annihilation: D_a(b)+D_b(a)=0, implying D_a(a)=0",
            "linear covariance identity: [D_a,L_b]=[L_a,D_b]",
        ],
        "sampling": metadata,
        "rank_report": ranks,
        "linear_solution_dimension": int(ranks["nullity"]),
        "feasible_nonzero_linear_surface": bool(ranks["nullity"] > 0),
    }


def herm3c_control() -> dict[str, Any]:
    data = hermitian_derivation_basis(3, normalized=True)
    derivs = data["derivations"]
    obs_left = data["obs_left"]
    obs_coords = data["obs_coords"]
    feasibility = linear_feasibility_report(
        "Herm3(C)_positive_control",
        obs_coords,
        obs_left,
        derivs,
        seed=SEED + 3,
        covariance_pair_limit=None,
        vector_limit=9,
    )
    map_rank = matrix_rank(np.array([d.reshape(-1) for d in derivs]).T)
    residual = commutator_axiom_residual(obs_left, derivs)
    corrupted = wrong_sign_commutator_residual(obs_left, derivs)
    return {
        "observable_dimension": 9,
        "traceless_observable_dimension": 8,
        "derivation_dimension": len(derivs),
        "correspondence_normalization": "D_a=(i/2)[a,.]",
        "correspondence_map_rank": map_rank,
        "expected_rank": 8,
        "linear_feasibility": feasibility,
        "commutator_axiom": residual,
        "corrupted_axiom_wrong_sign_control": corrupted,
        "control_succeeds": bool(map_rank == 8 and residual["passes"] and not corrupted["passes"]),
    }


def h3o_exceptional_probe() -> dict[str, Any]:
    table = octonion_table()
    space = f4_derivation_space(table)
    items = space["items"]
    obs_coords = albert_traceless_observable_coords(items)
    obs_left = left_mats_from_structure(space["structure_constants"], obs_coords)
    derivs = [row.reshape(27, 27) for row in space["nullspace"]]

    feasibility = linear_feasibility_report(
        "H3(O)_exceptional_branch",
        obs_coords,
        obs_left,
        derivs,
        seed=SEED + 27,
        covariance_pair_limit=36,
        vector_limit=8,
    )

    target_inner = []
    for i in range(len(obs_left)):
        for j in range(i + 1, len(obs_left)):
            target_inner.append(obs_left[i] @ obs_left[j] - obs_left[j] @ obs_left[i])
    target_matrix = np.array([x.reshape(-1) for x in target_inner]).T
    inner_span_rank = matrix_rank(target_matrix)
    zero_candidate_residual = commutator_axiom_residual(obs_left, [np.zeros((27, 27)) for _ in obs_left])

    corrupt_space = f4_derivation_space(octonion_table(corrupt_one_sign=True))

    return {
        "observable_dimension": 27,
        "traceless_observable_dimension": 26,
        "available_skew_order_derivations": "inner derivations [L_a,L_b] recomputed as Der(H3(O))",
        "f4_derivation_dimension": int(space["dimension"]),
        "f4_constraint_rank": int(space["constraint_rank"]),
        "ambient_endomorphism_dimension": 729,
        "derivation_constraint_matrix_shape": [int(x) for x in space["constraints"].shape],
        "upstream_52_dim_gate_pass": bool(space["dimension"] == 52),
        "inner_derivation_pair_span_rank": inner_span_rank,
        "linear_feasibility": feasibility,
        "zero_candidate_bilinear_residual": zero_candidate_residual,
        "single_observable_candidate_status": (
            "degenerate_or_empty"
            if feasibility["linear_solution_dimension"] == 0
            else "nonzero_linear_surface_requires_bilinear_audit"
        ),
        "corrupted_fano_control": {
            "corruption": "single upstream sign flip in the Fano table",
            "f4_dimension_after_corruption": int(corrupt_space["dimension"]),
            "breaks_52_gate": bool(corrupt_space["dimension"] != 52),
        },
    }


def build_result() -> dict[str, Any]:
    herm2 = herm2_special_demo()
    herm3 = herm3c_control()
    h3o = h3o_exceptional_probe()

    h3o_linear_dim = h3o["linear_feasibility"]["linear_solution_dimension"]
    h3o_rank = h3o["linear_feasibility"]["rank_report"]["rank"]
    h3o_unknowns = h3o["linear_feasibility"]["sampling"]["unknown_count"]
    h3o_deficit = 26 - (0 if h3o_linear_dim == 0 else min(26, h3o_linear_dim))

    if not h3o["upstream_52_dim_gate_pass"] or not herm3["control_succeeds"]:
        verdict = "setup_failed"
    elif h3o_linear_dim == 0 and h3o["zero_candidate_bilinear_residual"]["max_residual"] > 1.0:
        verdict = "deficit_demonstrated"
    else:
        verdict = "correspondence_unexpectedly_found"

    return {
        "schema": "codex_ratchet.alfsen_shultz_correspondence_probe_result.v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "generated_at": utc_now(),
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "spin9_derivation_machinery_source": str(SPIN9_SOURCE),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "sim_execution_kind": "classical",
        "sim_class": "finite_jordan_dynamical_correspondence_probe",
        "seed": SEED,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "claim_ceiling": "scratch_diagnostic only; finite sampled obstruction/control evidence, not theorem admission",
        "question": "What does the exceptional H3(O) branch give up relative to special C*-state spaces with a dynamical correspondence?",
        "special_case_Herm2C": herm2,
        "control_Herm3C": herm3,
        "exceptional_H3O": h3o,
        "deficit_measure": {
            "Herm3C_correspondence_rank": herm3["correspondence_map_rank"],
            "Herm3C_expected_traceless_rank": 8,
            "H3O_unknown_matrix_shape": [26, 52],
            "H3O_feasibility_rank": h3o_rank,
            "H3O_unknown_count": h3o_unknowns,
            "H3O_linear_solution_dimension": h3o_linear_dim,
            "H3O_measured_single_observable_rank": 0 if h3o_linear_dim == 0 else None,
            "H3O_traceless_observable_dimension": 26,
            "rank_deficit_vs_full_traceless_observables": h3o_deficit,
            "operational_meaning": "The finite H3(O) search finds no nonzero sampled linear single-observable correspondence into f4, while inner derivations [L_a,L_b] still span f4. Operationally the exceptional cone keeps two-observable symmetry generators but loses the C*-style assignment of each observable to its own Hamiltonian flow.",
        },
        "controls": {
            "Herm3C_positive_control_must_succeed": herm3["control_succeeds"],
            "Herm3C_corrupted_wrong_sign_axiom_breaks": not herm3["corrupted_axiom_wrong_sign_control"]["passes"],
            "H3O_f4_upstream_still_52_dim": h3o["upstream_52_dim_gate_pass"],
            "H3O_corrupted_fano_breaks_52_gate": h3o["corrupted_fano_control"]["breaks_52_gate"],
        },
        "verdict": verdict,
        "allowed_claims": [
            "Herm2(C) and Herm3(C) finite special controls realize the normalized dynamical correspondence.",
            "H3(O) finite sampled search demonstrates a single-observable correspondence deficit while preserving f4 inner derivations.",
        ],
        "blocked_consumers": [
            "formal theorem proof",
            "runtime admission",
            "axis or bridge claim",
            "claim that sampled feasibility exhausts all nonlinear H3(O) possibilities without external proof",
        ],
    }


def main() -> None:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    herm3 = result["control_Herm3C"]
    h3o = result["exceptional_H3O"]
    deficit = result["deficit_measure"]
    print("Alfsen-Shultz dynamical-correspondence finite probe")
    print(f"  result_path: {RESULT_PATH}")
    print(
        "  Herm2(C): product_defect={:.3e} entropy_shift={:.3e} map_rank_full={} traceless_rank={}".format(
            result["special_case_Herm2C"]["jordan_product_preservation_defect"],
            result["special_case_Herm2C"]["entropy_shift_abs"],
            result["special_case_Herm2C"]["observable_to_delta_full_rank"],
            result["special_case_Herm2C"]["observable_to_delta_traceless_rank"],
        )
    )
    print(
        "  Herm3(C) feasibility: rank={}/{} nullity={} correspondence_rank={} comm_residual={:.3e}".format(
            herm3["linear_feasibility"]["rank_report"]["rank"],
            herm3["linear_feasibility"]["sampling"]["unknown_count"],
            herm3["linear_feasibility"]["linear_solution_dimension"],
            herm3["correspondence_map_rank"],
            herm3["commutator_axiom"]["max_residual"],
        )
    )
    print(
        "  Herm3(C) corrupted wrong-sign residual: {:.3e} passes={}".format(
            herm3["corrupted_axiom_wrong_sign_control"]["max_residual"],
            herm3["corrupted_axiom_wrong_sign_control"]["passes"],
        )
    )
    print(
        "  H3(O) upstream: Der(H3(O)) dimension={} inner_pair_span_rank={} corrupted_fano_dim={}".format(
            h3o["f4_derivation_dimension"],
            h3o["inner_derivation_pair_span_rank"],
            h3o["corrupted_fano_control"]["f4_dimension_after_corruption"],
        )
    )
    print(
        "  H3(O) feasibility: rank={}/{} nullity={} sampled_single_observable_rank={}".format(
            h3o["linear_feasibility"]["rank_report"]["rank"],
            h3o["linear_feasibility"]["sampling"]["unknown_count"],
            h3o["linear_feasibility"]["linear_solution_dimension"],
            deficit["H3O_measured_single_observable_rank"],
        )
    )
    print(
        "  DEFICIT: H3(O) traceless observables={} vs measured single-observable correspondence rank={} -> deficit={}".format(
            deficit["H3O_traceless_observable_dimension"],
            deficit["H3O_measured_single_observable_rank"],
            deficit["rank_deficit_vs_full_traceless_observables"],
        )
    )
    print(f"  VERDICT: {result['verdict']}")


if __name__ == "__main__":
    main()
