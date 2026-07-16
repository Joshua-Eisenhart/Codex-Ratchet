#!/usr/bin/env python3
"""J3(O) Bloch-body entropy pawl probe.

Scratch diagnostic only. This file reuses the verified Fano convention and
flow pattern from jordan_octonion_entropy_pawl_sim.py, but runs on the full
Albert algebra J3(O): 3 real diagonal coordinates and three octonion
off-diagonal coordinates.

Installed test:
- spectral data come from the cubic characteristic polynomial
  lambda^3 - tr(X) lambda^2 + sigma2(X) lambda - det(X);
- density elements are trace-one positive-spectrum Albert elements;
- the dissipative step uses only the Jordan quadratic representation
  U_a(b)=2 a.(a.b)-(a.a).b, trace-normalized and convexly damped;
- the pawl observable is EJA relative entropy to an epsilon full-rank shadow of
  the primitive idempotent target.
"""

from __future__ import annotations

import datetime as dt
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


SIM_DIR = Path(__file__).resolve().parent
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = SIM_DIR / "j3o_bloch_body_entropy_pawl_sim_results.json"
J2_SOURCE_PATH = SIM_DIR / "jordan_octonion_entropy_pawl_sim.py"
J2_RESULT_PATH = SIM_DIR / "jordan_octonion_entropy_pawl_sim_results.json"

SIM_ID = "j3o_bloch_body_entropy_pawl"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
SEED = 0
TOL = 1.0e-9
FLOW_ETA = 0.08
FLOW_STEPS = 44
RELATIVE_EPSILON = 1.0e-6

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
        "reason": "load-bearing Fano octonion table, Albert cubic invariants, seeded state grid, and Jordan quadratic-representation flow sweep",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive timestamps, paths, scalar math, and JSON serialization",
    },
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing", "python_stdlib": "supportive"}


def basis(dim: int, idx: int) -> np.ndarray:
    out = np.zeros(dim, dtype=float)
    out[idx] = 1.0
    return out


def setprod(table: np.ndarray, a: int, b: int, c: int, s: float) -> None:
    table[c, a, b] = s


def add_identity(table: np.ndarray) -> None:
    for a in range(table.shape[0]):
        setprod(table, 0, a, a, 1.0)
        setprod(table, a, 0, a, 1.0)


def octonion_table() -> np.ndarray:
    table = np.zeros((8, 8, 8), dtype=float)
    add_identity(table)
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


def associator(table: np.ndarray, x: np.ndarray, y: np.ndarray, z: np.ndarray) -> np.ndarray:
    return multiply(table, multiply(table, x, y), z) - multiply(table, x, multiply(table, y, z))


def cayley_dickson_double(parent: np.ndarray) -> np.ndarray:
    n = parent.shape[0]
    dim = 2 * n
    table = np.zeros((dim, dim, dim), dtype=float)
    eye = np.eye(dim, dtype=float)
    for i in range(dim):
        for j in range(dim):
            x = eye[i]
            y = eye[j]
            a, b = x[:n], x[n:]
            c, d = y[:n], y[n:]
            first = multiply(parent, a, c) - multiply(parent, conjugate(d), b)
            second = multiply(parent, d, a) + multiply(parent, b, conjugate(c))
            table[:, i, j] = np.concatenate([first, second])
    return table


def vector_terms(v: np.ndarray) -> list[dict[str, Any]]:
    return [
        {"basis_index": int(idx), "label": f"e{idx}", "coefficient": float(value)}
        for idx, value in enumerate(v)
        if abs(float(value)) > 1.0e-10
    ]


def pair_vector(dim: int, i: int, j: int, si: float = 1.0, sj: float = 1.0) -> np.ndarray:
    out = np.zeros(dim, dtype=float)
    out[i] = si
    out[j] = sj
    return out


def zero_divisor_search(table: np.ndarray) -> dict[str, Any]:
    dim = table.shape[0]
    pairs = [(i, j) for i in range(1, dim) for j in range(i + 1, dim)]
    best_norm = float("inf")
    best = None
    for i, j in pairs:
        for k, ell in pairs:
            for si in (-1.0, 1.0):
                for sj in (-1.0, 1.0):
                    for sk in (-1.0, 1.0):
                        for sl in (-1.0, 1.0):
                            left = pair_vector(dim, i, j, si, sj)
                            right = pair_vector(dim, k, ell, sk, sl)
                            product = multiply(table, left, right)
                            product_norm = float(np.linalg.norm(product))
                            if product_norm < best_norm:
                                best_norm = product_norm
                                best = (left, right, product)
                            if product_norm < 1.0e-10:
                                return {
                                    "found": True,
                                    "product_norm": product_norm,
                                    "left_norm": float(np.linalg.norm(left)),
                                    "right_norm": float(np.linalg.norm(right)),
                                    "norm_multiplicativity_residual": float(
                                        abs(product_norm - np.linalg.norm(left) * np.linalg.norm(right))
                                    ),
                                    "left_terms": vector_terms(left),
                                    "right_terms": vector_terms(right),
                                    "product_terms": vector_terms(product),
                                }
    assert best is not None
    left, right, product = best
    return {
        "found": False,
        "best_product_norm": best_norm,
        "left_norm": float(np.linalg.norm(left)),
        "right_norm": float(np.linalg.norm(right)),
        "left_terms": vector_terms(left),
        "right_terms": vector_terms(right),
        "product_terms": vector_terms(product),
    }


def norm_composition_sample(table: np.ndarray, rng: np.random.Generator, samples: int, dim: int) -> dict[str, Any]:
    max_residual = 0.0
    worst = None
    for idx in range(samples):
        x = rng.normal(size=dim)
        y = rng.normal(size=dim)
        product = multiply(table, x, y)
        residual = abs(np.linalg.norm(product) - np.linalg.norm(x) * np.linalg.norm(y))
        if residual > max_residual:
            max_residual = float(residual)
            worst = {"sample_index": idx, "residual": float(residual)}
    return {"samples": samples, "max_residual": max_residual, "worst": worst, "pass": max_residual < 1.0e-9}


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


def j3_unit() -> np.ndarray:
    return j3_from_parts(np.ones(3), np.zeros(8), np.zeros(8), np.zeros(8))


def j3_diag(values: tuple[float, float, float] | list[float] | np.ndarray) -> np.ndarray:
    return j3_from_parts(np.asarray(values, dtype=float), np.zeros(8), np.zeros(8), np.zeros(8))


def j3_add(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return a + b


def j3_sub(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return a - b


def j3_scale(a: np.ndarray, scalar: float) -> np.ndarray:
    return scalar * a


def j3_trace(a: np.ndarray) -> float:
    return float(a[0, 0, 0] + a[1, 1, 0] + a[2, 2, 0])


def hermitian_residual(a: np.ndarray) -> float:
    max_res = 0.0
    for i in range(3):
        imag_diag = float(np.linalg.norm(a[i, i, 1:]))
        max_res = max(max_res, imag_diag)
        for j in range(i + 1, 3):
            max_res = max(max_res, float(np.linalg.norm(a[j, i, :] - conjugate(a[i, j, :]))))
    return max_res


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


def jordan_square(table: np.ndarray, a: np.ndarray) -> np.ndarray:
    return jordan(table, a, a)


def jordan_quadratic(table: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    aa = jordan_square(table, a)
    return j3_sub(j3_scale(jordan(table, a, jordan(table, a, b)), 2.0), jordan(table, aa, b))


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


def cubic_eigenvalues(trace: float, sigma2: float, determinant: float) -> np.ndarray:
    p = sigma2 - trace * trace / 3.0
    q = -2.0 * trace * trace * trace / 27.0 + trace * sigma2 / 3.0 - determinant
    if abs(p) < 1.0e-15:
        roots = np.array([trace / 3.0, trace / 3.0, trace / 3.0], dtype=float)
    else:
        arg = (3.0 * q / (2.0 * p)) * math.sqrt(max(0.0, -3.0 / p))
        arg = min(1.0, max(-1.0, arg))
        radius = 2.0 * math.sqrt(max(0.0, -p / 3.0))
        roots = np.array(
            [trace / 3.0 + radius * math.cos(math.acos(arg) / 3.0 - 2.0 * math.pi * k / 3.0) for k in range(3)],
            dtype=float,
        )
    roots.sort()
    return roots[::-1]


def spectral_data(a: np.ndarray, table: np.ndarray) -> dict[str, Any]:
    tr = j3_trace(a)
    sig = sigma2_j3(a)
    det = det_j3(table, a)
    eigs = cubic_eigenvalues(tr, sig, det)
    reconstructed = {
        "trace": float(np.sum(eigs)),
        "sigma2": float(eigs[0] * eigs[1] + eigs[0] * eigs[2] + eigs[1] * eigs[2]),
        "det": float(np.prod(eigs)),
    }
    return {
        "trace": tr,
        "sigma2": sig,
        "det": det,
        "eigenvalues": [float(x) for x in eigs],
        "positive": bool(float(np.min(eigs)) >= -1.0e-9),
        "min_eigenvalue": float(np.min(eigs)),
        "max_invariant_reconstruction_error": float(
            max(abs(reconstructed["trace"] - tr), abs(reconstructed["sigma2"] - sig), abs(reconstructed["det"] - det))
        ),
    }


def spectral_entropy(a: np.ndarray, table: np.ndarray) -> float:
    eigs = cubic_eigenvalues(j3_trace(a), sigma2_j3(a), det_j3(table, a))
    clipped = np.clip(eigs, 0.0, 1.0)
    return float(-sum(float(x) * math.log(float(x)) for x in clipped if x > 0.0))


def primitive_idempotent_gate(a: np.ndarray, table: np.ndarray) -> dict[str, Any]:
    square = jordan_square(table, a)
    tr = j3_trace(a)
    sig = sigma2_j3(a)
    det = det_j3(table, a)
    return {
        "trace": tr,
        "sigma2": sig,
        "det": det,
        "idempotent_residual": float(np.linalg.norm(square - a)),
        "pass": bool(abs(tr - 1.0) < 1.0e-12 and abs(sig) < 1.0e-12 and abs(det) < 1.0e-12 and np.linalg.norm(square - a) < 1.0e-12),
    }


def rank2_idempotent_gate(a: np.ndarray, table: np.ndarray) -> dict[str, Any]:
    square = jordan_square(table, a)
    tr = j3_trace(a)
    sig = sigma2_j3(a)
    det = det_j3(table, a)
    return {
        "trace": tr,
        "sigma2": sig,
        "det": det,
        "idempotent_residual": float(np.linalg.norm(square - a)),
        "primitive_gate_pass": bool(abs(tr - 1.0) < 1.0e-12 and abs(sig) < 1.0e-12 and abs(det) < 1.0e-12),
        "rank2_idempotent_signature": bool(abs(tr - 2.0) < 1.0e-12 and abs(sig - 1.0) < 1.0e-12 and abs(det) < 1.0e-12 and np.linalg.norm(square - a) < 1.0e-12),
    }


def trace_rho_log_diagonal_shadow(rho: np.ndarray, log_diag: np.ndarray) -> float:
    return float(rho[0, 0, 0] * log_diag[0] + rho[1, 1, 0] * log_diag[1] + rho[2, 2, 0] * log_diag[2])


def primitive_shadow_log_diag(target_index: int) -> np.ndarray:
    diag = np.full(3, RELATIVE_EPSILON / 3.0, dtype=float)
    diag[target_index] = 1.0 - RELATIVE_EPSILON + RELATIVE_EPSILON / 3.0
    return np.log(diag)


def rank2_shadow_log_diag(excluded_index: int) -> np.ndarray:
    diag = np.full(3, RELATIVE_EPSILON / 3.0, dtype=float)
    for i in range(3):
        if i != excluded_index:
            diag[i] = 0.5 * (1.0 - RELATIVE_EPSILON) + RELATIVE_EPSILON / 3.0
    return np.log(diag)


def eja_relative_entropy_to_diag_shadow(rho: np.ndarray, table: np.ndarray, log_diag: np.ndarray) -> float:
    return float(-spectral_entropy(rho, table) - trace_rho_log_diagonal_shadow(rho, log_diag))


def normalize_density(a: np.ndarray) -> np.ndarray:
    tr = j3_trace(a)
    if abs(tr) < 1.0e-15:
        raise ValueError("cannot trace-normalize an element with near-zero trace")
    return a / tr


def jordan_flow_step(rho: np.ndarray, target: np.ndarray, table: np.ndarray, fallback_density: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
    filtered = jordan_quadratic(table, target, rho)
    filtered_trace = j3_trace(filtered)
    if filtered_trace <= 1.0e-14:
        normalized = np.array(fallback_density, dtype=float, copy=True)
        note = "zero Peirce weight; used target-face limiting density"
    else:
        normalized = normalize_density(filtered)
        note = "trace-normalized U_a(rho)"
    stepped = (1.0 - FLOW_ETA) * rho + FLOW_ETA * normalized
    return stepped, {
        "quadratic_trace": float(filtered_trace),
        "normalization_note": note,
        "trace_after_step": j3_trace(stepped),
        "hermitian_residual_after_step": hermitian_residual(stepped),
    }


def classify_deltas(values_by_path: list[list[float]], direction: str, tol: float = TOL) -> dict[str, Any]:
    max_increase = 0.0
    max_decrease = 0.0
    worst_increase = None
    worst_decrease = None
    start_end = []
    for state_index, values in enumerate(values_by_path):
        start_end.append(float(values[-1] - values[0]))
        for step, (a, b) in enumerate(zip(values, values[1:])):
            delta = float(b - a)
            if delta > max_increase:
                max_increase = delta
                worst_increase = {"state_index": state_index, "step": step, "delta": delta}
            if -delta > max_decrease:
                max_decrease = -delta
                worst_decrease = {"state_index": state_index, "step": step, "delta": delta}
    if direction == "decreasing":
        pawl = max_increase <= tol
    elif direction == "increasing":
        pawl = max_decrease <= tol
    else:
        pawl = max_increase <= tol or max_decrease <= tol
    if max_increase <= tol and max_decrease <= tol:
        classification = "hold"
    elif max_increase <= tol:
        classification = "monotone-decreasing"
    elif max_decrease <= tol:
        classification = "monotone-increasing"
    else:
        classification = "non-monotone"
    return {
        "direction_tested": direction,
        "classification": classification,
        "pawl": bool(pawl),
        "max_increase": max_increase,
        "max_decrease": max_decrease,
        "worst_increase": worst_increase,
        "worst_decrease": worst_decrease,
        "net_delta_min": float(min(start_end)),
        "net_delta_max": float(max(start_end)),
    }


def coordinate_basis_perturbation(coord: int, amplitude: float) -> np.ndarray:
    diag = np.array([1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0], dtype=float)
    zeros = np.zeros(8, dtype=float)
    if coord == 0:
        diag += amplitude * np.array([1.0, -1.0, 0.0])
        return j3_from_parts(diag, zeros, zeros, zeros)
    if coord == 1:
        diag += amplitude * np.array([1.0, 1.0, -2.0]) / math.sqrt(3.0)
        return j3_from_parts(diag, zeros, zeros, zeros)
    off_index = coord - 2
    slot = off_index // 8
    unit = off_index % 8
    x01 = np.zeros(8, dtype=float)
    x02 = np.zeros(8, dtype=float)
    x12 = np.zeros(8, dtype=float)
    if slot == 0:
        x01[unit] = amplitude
    elif slot == 1:
        x02[unit] = amplitude
    else:
        x12[unit] = amplitude
    return j3_from_parts(diag, x01, x02, x12)


def random_density_candidate(rng: np.random.Generator, scale: float) -> np.ndarray:
    diag_delta = rng.normal(size=3)
    diag_delta -= float(np.mean(diag_delta))
    diag = np.full(3, 1.0 / 3.0, dtype=float) + scale * diag_delta
    x01 = rng.normal(scale=scale, size=8)
    x02 = rng.normal(scale=scale, size=8)
    x12 = rng.normal(scale=scale, size=8)
    return j3_from_parts(diag, x01, x02, x12)


def is_density(a: np.ndarray, table: np.ndarray, margin: float = -1.0e-10) -> bool:
    data = spectral_data(a, table)
    return bool(abs(data["trace"] - 1.0) < 1.0e-9 and data["min_eigenvalue"] >= margin and hermitian_residual(a) < 1.0e-10)


def sample_state_grid(rng: np.random.Generator, table: np.ndarray) -> tuple[list[np.ndarray], dict[str, Any]]:
    states: list[np.ndarray] = []
    amplitudes = [0.02, -0.02, 0.055, -0.055]
    for coord in range(26):
        for amp in amplitudes:
            candidate = coordinate_basis_perturbation(coord, amp)
            if is_density(candidate, table):
                states.append(candidate)
    primitive = [j3_diag([1.0, 0.0, 0.0]), j3_diag([0.0, 1.0, 0.0]), j3_diag([0.0, 0.0, 1.0])]
    mixed = j3_unit() / 3.0
    for idx in range(3):
        for alpha in (0.015, 0.04, 0.09, 0.18, 0.35, 0.6):
            states.append((1.0 - alpha) * primitive[idx] + alpha * mixed)
    accepted_random = 0
    attempts = 0
    scales = [0.018, 0.028, 0.04, 0.055, 0.07]
    while accepted_random < 168 and attempts < 5000:
        scale = scales[attempts % len(scales)]
        candidate = random_density_candidate(rng, scale)
        attempts += 1
        if is_density(candidate, table, margin=1.0e-6):
            states.append(candidate)
            accepted_random += 1
    min_eig = min(spectral_data(state, table)["min_eigenvalue"] for state in states)
    return states, {
        "trace_one_body_dimension": 26,
        "ambient_albert_dimension": 27,
        "coordinate_basis_states": 26 * len(amplitudes),
        "near_frame_primitive_states": 18,
        "accepted_random_states": accepted_random,
        "random_attempts": attempts,
        "sample_count": len(states),
        "min_initial_eigenvalue": float(min_eig),
    }


def frame_automorphism(a: np.ndarray, perm: np.ndarray, signs: np.ndarray) -> np.ndarray:
    out = j3_zero()
    for i in range(3):
        for j in range(3):
            out[i, j, :] = signs[i] * signs[j] * a[int(perm[i]), int(perm[j]), :]
    for i in range(3):
        out[i, i, 1:] = 0.0
    return out


def entropy_invariance(table: np.ndarray, rng: np.random.Generator, states: list[np.ndarray]) -> dict[str, Any]:
    max_diff = 0.0
    max_invariant_error = 0.0
    rows = []
    for idx, state in enumerate(states[:64]):
        perm = rng.permutation(3)
        signs = rng.choice(np.array([-1.0, 1.0]), size=3)
        moved = frame_automorphism(state, perm, signs)
        before = spectral_entropy(state, table)
        after = spectral_entropy(moved, table)
        diff = abs(after - before)
        max_diff = max(max_diff, float(diff))
        before_data = spectral_data(state, table)
        after_data = spectral_data(moved, table)
        inv_error = max(
            abs(before_data["trace"] - after_data["trace"]),
            abs(before_data["sigma2"] - after_data["sigma2"]),
            abs(before_data["det"] - after_data["det"]),
        )
        max_invariant_error = max(max_invariant_error, float(inv_error))
        if idx < 6:
            rows.append(
                {
                    "sample": idx,
                    "perm": [int(x) for x in perm],
                    "signs": [float(x) for x in signs],
                    "before": before,
                    "after": after,
                    "abs_diff": diff,
                    "invariant_error": inv_error,
                }
            )
    return {
        "group_action": "seeded Albert-frame permutation plus Peirce sign flips, an F4-contained automorphism sample surface",
        "sample_count": min(64, len(states)),
        "max_abs_entropy_diff": max_diff,
        "max_invariant_error": max_invariant_error,
        "pass": bool(max_diff < 1.0e-10 and max_invariant_error < 1.0e-10),
        "sample_rows": rows,
    }


def run_primitive_flow_sweep(table: np.ndarray, states: list[np.ndarray]) -> dict[str, Any]:
    target = j3_diag([1.0, 0.0, 0.0])
    fallback = target
    fixed_log = primitive_shadow_log_diag(0)
    wrong_log = primitive_shadow_log_diag(1)
    entropy_paths: list[list[float]] = []
    relative_paths: list[list[float]] = []
    wrong_relative_paths: list[list[float]] = []
    min_eig = float("inf")
    max_trace_error = 0.0
    max_hermitian_residual = 0.0
    min_quad_trace = float("inf")
    fallback_count = 0
    for start in states:
        rho = np.array(start, dtype=float, copy=True)
        ent = [spectral_entropy(rho, table)]
        rel = [eja_relative_entropy_to_diag_shadow(rho, table, fixed_log)]
        wrong = [eja_relative_entropy_to_diag_shadow(rho, table, wrong_log)]
        for _ in range(FLOW_STEPS):
            rho, step = jordan_flow_step(rho, target, table, fallback)
            if step["normalization_note"].startswith("zero"):
                fallback_count += 1
            data = spectral_data(rho, table)
            min_eig = min(min_eig, data["min_eigenvalue"])
            max_trace_error = max(max_trace_error, abs(data["trace"] - 1.0), abs(step["trace_after_step"] - 1.0))
            max_hermitian_residual = max(max_hermitian_residual, step["hermitian_residual_after_step"])
            min_quad_trace = min(min_quad_trace, step["quadratic_trace"])
            ent.append(spectral_entropy(rho, table))
            rel.append(eja_relative_entropy_to_diag_shadow(rho, table, fixed_log))
            wrong.append(eja_relative_entropy_to_diag_shadow(rho, table, wrong_log))
        entropy_paths.append(ent)
        relative_paths.append(rel)
        wrong_relative_paths.append(wrong)
    return {
        "target": "primitive idempotent diag(1,0,0), an OP2 frame point",
        "target_gate": primitive_idempotent_gate(target, table),
        "flow": {
            "definition": "rho_{t+1}=(1-eta)rho_t + eta*normalize_trace(U_p(rho_t)); U_p(b)=2p.(p.b)-(p.p).b",
            "eta": FLOW_ETA,
            "steps": FLOW_STEPS,
            "sample_count": len(states),
            "positivity_preserved": bool(min_eig >= -1.0e-9),
            "trace_preserved": bool(max_trace_error <= 1.0e-9),
            "hermitian_preserved": bool(max_hermitian_residual <= 1.0e-10),
            "min_eigenvalue_along_paths": float(min_eig),
            "max_trace_error": float(max_trace_error),
            "max_hermitian_residual": float(max_hermitian_residual),
            "min_quadratic_trace_before_normalization": float(min_quad_trace),
            "zero_peirce_fallback_count": int(fallback_count),
        },
        "strict_pure_fixed_point_relative_entropy": {
            "status": "ill_defined_infinite_off_support",
            "reason": "The primitive idempotent has two zero spectral eigenvalues; D_EJA(rho||p) is finite only on p's support.",
            "installed_interpretation_for_pawl_table": "D_EJA(rho||sigma_epsilon), sigma_epsilon=(1-epsilon)p + epsilon*unit/3",
            "epsilon": RELATIVE_EPSILON,
        },
        "pawl_table": {
            "U_J_to_epsilon_shadow_of_fixed_primitive": classify_deltas(relative_paths, "decreasing"),
            "S_raw_spectral_entropy": classify_deltas(entropy_paths, "none"),
            "wrong_fixed_point_U_J_control": classify_deltas(wrong_relative_paths, "decreasing"),
        },
    }


def run_rank2_control(table: np.ndarray, states: list[np.ndarray]) -> dict[str, Any]:
    target = j3_diag([0.0, 1.0, 1.0])
    fallback = target / j3_trace(target)
    log_shadow = rank2_shadow_log_diag(0)
    paths: list[list[float]] = []
    terminal_d01 = []
    terminal_d02 = []
    terminal_entropy = []
    min_eig = float("inf")
    max_trace_error = 0.0
    for start in states:
        rho = np.array(start, dtype=float, copy=True)
        path = [eja_relative_entropy_to_diag_shadow(rho, table, log_shadow)]
        for _ in range(FLOW_STEPS):
            rho, _ = jordan_flow_step(rho, target, table, fallback)
            data = spectral_data(rho, table)
            min_eig = min(min_eig, data["min_eigenvalue"])
            max_trace_error = max(max_trace_error, abs(data["trace"] - 1.0))
            path.append(eja_relative_entropy_to_diag_shadow(rho, table, log_shadow))
        paths.append(path)
        terminal_d01.append(float(rho[1, 1, 0]))
        terminal_d02.append(float(rho[2, 2, 0]))
        terminal_entropy.append(spectral_entropy(rho, table))
    deltas = classify_deltas(paths, "decreasing")
    return {
        "attempted_target": "rank-2 idempotent diag(0,1,1), not an OP2 primitive point",
        "target_gate": rank2_idempotent_gate(target, table),
        "flow_note": "U_q is defined, but trace-normalized U_q(rho) attracts to a rank-2 face rather than a primitive point; terminal face coordinates retain initial-state dependence.",
        "relative_entropy_to_rank2_shadow": deltas,
        "positivity_preserved": bool(min_eig >= -1.0e-9),
        "trace_preserved": bool(max_trace_error <= 1.0e-9),
        "terminal_face_coordinate_spread": {
            "diag_1_min": float(min(terminal_d01)),
            "diag_1_max": float(max(terminal_d01)),
            "diag_2_min": float(min(terminal_d02)),
            "diag_2_max": float(max(terminal_d02)),
            "entropy_min": float(min(terminal_entropy)),
            "entropy_max": float(max(terminal_entropy)),
        },
        "misbehavior": "primitive-idempotent gate fails; the flow has a target face, not a unique OP2 point, and the rank-2 shadow pawl is not the requested fixed-point-point construction",
    }


def octonion_verification(table: np.ndarray, rng: np.random.Generator) -> dict[str, Any]:
    alt_max = 0.0
    for _ in range(32):
        a = rng.normal(size=8)
        b = rng.normal(size=8)
        alt_max = max(
            alt_max,
            float(np.linalg.norm(associator(table, a, a, b))),
            float(np.linalg.norm(associator(table, a, b, b))),
        )
    witness = associator(table, basis(8, 1), basis(8, 2), basis(8, 4))
    return {
        "fano_cycles": [list(row) for row in FANO],
        "norm_composition": norm_composition_sample(table, rng, 64, 8),
        "basis_associator_e1_e2_e4_norm": float(np.linalg.norm(witness)),
        "basis_associator_e1_e2_e4_terms": vector_terms(witness),
        "alternative_max_residual_seeded": alt_max,
        "alternative_identity_holds_seeded": bool(alt_max < 1.0e-9),
    }


def sedenion_kill_control(o_table: np.ndarray) -> dict[str, Any]:
    s_table = cayley_dickson_double(o_table)
    zero = zero_divisor_search(s_table)
    norm = norm_composition_sample(s_table, np.random.default_rng(SEED + 99), 64, 16)
    alt_max = 0.0
    rng = np.random.default_rng(SEED + 101)
    for _ in range(32):
        x = rng.normal(size=16)
        y = rng.normal(size=16)
        alt_max = max(alt_max, float(np.linalg.norm(associator(s_table, x, x, y))))
    return {
        "attempted_object": "J3(S) Hermitian-like Albert analogue one Cayley-Dickson rung past O",
        "break_status": "construction_breaks",
        "reason": "Sedenion zero divisors and norm-composition failure remove the positive spectral/Jordan spine required for the Albert density construction.",
        "zero_divisor_witness": zero,
        "norm_composition_sample": norm,
        "alternative_max_residual_seeded": alt_max,
        "entropy_construction_allowed": False,
    }


def representative_full_state(table: np.ndarray) -> dict[str, Any]:
    state = j3_from_parts(
        np.array([0.36, 0.33, 0.31], dtype=float),
        np.array([0.025, -0.01, 0.0, 0.008, 0.004, 0.0, -0.006, 0.003], dtype=float),
        np.array([-0.018, 0.006, 0.011, 0.0, -0.004, 0.005, 0.0, -0.002], dtype=float),
        np.array([0.014, 0.0, -0.009, 0.004, 0.0, -0.003, 0.007, 0.0], dtype=float),
    )
    data = spectral_data(state, table)
    data["entropy"] = spectral_entropy(state, table)
    data["hermitian_residual"] = hermitian_residual(state)
    return data


def build_result() -> dict[str, Any]:
    rng = np.random.default_rng(SEED)
    table = octonion_table()
    oct_checks = octonion_verification(table, rng)
    states, grid = sample_state_grid(rng, table)
    invariance = entropy_invariance(table, rng, states)
    primitive_flow = run_primitive_flow_sweep(table, states)
    rank2 = run_rank2_control(table, states)
    sedenion = sedenion_kill_control(table)

    pawl = primitive_flow["pawl_table"]["U_J_to_epsilon_shadow_of_fixed_primitive"]
    raw_s = primitive_flow["pawl_table"]["S_raw_spectral_entropy"]
    wrong = primitive_flow["pawl_table"]["wrong_fixed_point_U_J_control"]
    rank2_deltas = rank2["relative_entropy_to_rank2_shadow"]
    construction_well_defined = bool(
        oct_checks["norm_composition"]["pass"]
        and oct_checks["alternative_identity_holds_seeded"]
        and primitive_flow["target_gate"]["pass"]
        and primitive_flow["flow"]["positivity_preserved"]
        and primitive_flow["flow"]["trace_preserved"]
        and primitive_flow["flow"]["hermitian_preserved"]
        and invariance["pass"]
    )
    controls_flip = bool(
        raw_s["classification"] == "non-monotone"
        and not wrong["pawl"]
        and rank2["target_gate"]["rank2_idempotent_signature"]
        and not rank2["target_gate"]["primitive_gate_pass"]
        and sedenion["break_status"] == "construction_breaks"
        and sedenion["zero_divisor_witness"]["found"]
    )
    if not construction_well_defined:
        verdict = "construction_ill_defined"
    elif pawl["pawl"] and controls_flip:
        verdict = "pawl_lifts_to_J3O"
    else:
        verdict = "pawl_fails"

    all_pass = bool(verdict == "pawl_lifts_to_J3O")
    return {
        "schema": "codex_ratchet.j3o_bloch_body_entropy_pawl_result.v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "sim_execution_kind": "classical",
        "sim_class": "jordan_spectral_entropy_probe",
        "seed": SEED,
        "tol": TOL,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_conventions_reused": {
            "J2O_source_path": str(J2_SOURCE_PATH),
            "J2O_result_path": str(J2_RESULT_PATH),
            "FANO": [list(row) for row in FANO],
            "flow_pattern": "trace-normalized Jordan quadratic representation followed by convex damping, matching the J2(O) pawl sim pattern",
        },
        "installed_interpretation": {
            "primary_carrier": "J3(O), the 27-dimensional Albert algebra; trace-one density body has 26 affine dimensions",
            "spectral_decomposition": "cubic Albert spectrum from trace, sigma2, and cubic norm determinant",
            "finite_pawl_measure": "D_EJA(rho || sigma_epsilon), sigma_epsilon=(1-epsilon)p + epsilon*unit/3",
            "strict_relative_entropy_gap": primitive_flow["strict_pure_fixed_point_relative_entropy"]["status"],
        },
        "claim_ceiling": (
            "Scratch diagnostic: finite seeded J3(O) Albert spectral entropy and epsilon-shadow relative-entropy pawl probe. "
            "No formal proof, Axis0 closure, bridge, manifold, or admission claim."
        ),
        "octonion_verification": oct_checks,
        "spectral_entropy_well_defined": {
            "J3O_dimension": 27,
            "trace_one_body_dimension": 26,
            "density_condition": "cubic-spectrum eigenvalues nonnegative and trace one",
            "representative_full_density": representative_full_state(table),
            "basis_independence": invariance,
        },
        "state_grid": grid,
        "jordan_flow": primitive_flow,
        "controls": {
            "wrong_fixed_point": wrong,
            "rank2_idempotent_target": rank2,
            "sedenion_kill": sedenion,
        },
        "divergence_log": [
            {
                "surface": "raw_spectral_entropy",
                "expected": "non-monotone under primitive U_p damp flow",
                "observed": raw_s["classification"],
                "reason": "Raw spectral entropy is not the fixed-point-shadow pawl even though it is computed from the same Albert spectrum.",
            },
            {
                "surface": "wrong_fixed_point_relative_entropy",
                "expected": "control should lose monotonicity",
                "observed": wrong["classification"],
                "reason": "The pawl is tied to the flow's primitive fixed idempotent, not an arbitrary foreign idempotent.",
            },
            {
                "surface": "rank2_idempotent_target",
                "expected": "not a primitive OP2 point",
                "observed": rank2["misbehavior"],
                "relative_entropy_classification": rank2_deltas["classification"],
                "reason": "A rank-2 idempotent passes idempotency but fails det=0, sigma2=0, trace=1 primitive gating.",
            },
            {
                "surface": "sedenion_kill",
                "expected": "construction breaks past octonions",
                "observed": sedenion["break_status"],
                "reason": "Zero divisors and norm-composition failure remove the division-algebra positivity spine.",
            },
        ],
        "construction_well_defined": construction_well_defined,
        "controls_flip": controls_flip,
        "verdict": verdict,
        "all_pass": all_pass,
        "promotion_status": "diagnostic_only",
        "eligible_consumers": [],
        "blocked_consumers": [
            "formal monotonicity theorem",
            "Axis0 closure",
            "bridge or manifold admission",
            "canonical-by-process promotion",
        ],
        "blocked_downstream_consumers": [
            "formal monotonicity theorem",
            "Axis0 closure",
            "bridge or manifold admission",
            "canonical-by-process promotion",
        ],
    }


def print_summary(result: dict[str, Any]) -> None:
    octv = result["octonion_verification"]
    inv = result["spectral_entropy_well_defined"]["basis_independence"]
    flow = result["jordan_flow"]["flow"]
    pawl_table = result["jordan_flow"]["pawl_table"]
    rank2 = result["controls"]["rank2_idempotent_target"]
    sed = result["controls"]["sedenion_kill"]

    print("J3O_BLOCH_BODY_ENTROPY_PAWL_SIM")
    print(f"seed={SEED} classification={CLASSIFICATION} promotion_allowed={PROMOTION_ALLOWED}")
    print(
        "octonion verification: "
        f"norm_comp_pass={octv['norm_composition']['pass']} "
        f"norm_max_residual={octv['norm_composition']['max_residual']:.3e} "
        f"basis_assoc_e1_e2_e4={octv['basis_associator_e1_e2_e4_norm']:.6f} "
        f"alternative_max={octv['alternative_max_residual_seeded']:.3e}"
    )
    print(
        "state grid: "
        f"samples={result['state_grid']['sample_count']} "
        f"trace_one_dim={result['state_grid']['trace_one_body_dimension']} "
        f"min_initial_eig={result['state_grid']['min_initial_eigenvalue']:.6e}"
    )
    print(
        "spectral entropy invariance: "
        f"F4ish_samples={inv['sample_count']} "
        f"max_abs_diff={inv['max_abs_entropy_diff']:.3e} "
        f"max_invariant_error={inv['max_invariant_error']:.3e} "
        f"pass={inv['pass']}"
    )
    print(
        "primitive flow preservation: "
        f"trace_preserved={flow['trace_preserved']} "
        f"positivity_preserved={flow['positivity_preserved']} "
        f"min_eig={flow['min_eigenvalue_along_paths']:.6e} "
        f"zero_peirce_fallback_count={flow['zero_peirce_fallback_count']}"
    )
    print("pawl table:")
    for key, row in pawl_table.items():
        print(
            "  "
            f"{key}: classification={row['classification']} pawl={row['pawl']} "
            f"max_increase={row['max_increase']:.6e} max_decrease={row['max_decrease']:.6e} "
            f"net_delta_min={row['net_delta_min']:.6e} net_delta_max={row['net_delta_max']:.6e}"
        )
    print(
        "rank2 control: "
        f"primitive_gate_pass={rank2['target_gate']['primitive_gate_pass']} "
        f"rank2_signature={rank2['target_gate']['rank2_idempotent_signature']} "
        f"rel_entropy_classification={rank2['relative_entropy_to_rank2_shadow']['classification']} "
        f"terminal_entropy_spread=[{rank2['terminal_face_coordinate_spread']['entropy_min']:.6e}, "
        f"{rank2['terminal_face_coordinate_spread']['entropy_max']:.6e}]"
    )
    print(
        "sedenion kill control: "
        f"zero_divisor_found={sed['zero_divisor_witness']['found']} "
        f"product_norm={sed['zero_divisor_witness'].get('product_norm')} "
        f"norm_residual={sed['zero_divisor_witness'].get('norm_multiplicativity_residual')} "
        f"entropy_allowed={sed['entropy_construction_allowed']}"
    )
    print(
        f"verdict={result['verdict']} "
        f"construction_well_defined={result['construction_well_defined']} "
        f"controls_flip={result['controls_flip']} "
        f"all_pass={result['all_pass']}"
    )
    print(f"wrote: {RESULT_PATH}")


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print_summary(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
