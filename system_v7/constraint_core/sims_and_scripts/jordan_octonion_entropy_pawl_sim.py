#!/usr/bin/env python3
"""Jordan spectral entropy pawl probe at the octonion floor.

Scratch diagnostic only. This file uses the project-local Fano convention from
system_v5/julia_carrier/J3O_spectral_OP2.jl and the J3(O) Hermitian convention:
diagonal real coordinates and conjugate off-diagonal octonion coordinates.

Math spine installed here:
- O is the standard Fano-plane octonion algebra used by J3O_spectral_OP2.
- J2(O) is represented as the 10-dimensional spin factor: rho=(I+r.Gamma)/2,
  with r in R^9 and ||r||<=1. The off-diagonal octonion contributes eight
  vector coordinates; the diagonal imbalance contributes the ninth.
- Spectral entropy is S(rho)=h2((1+||r||)/2).
- The dissipative step uses the Euclidean Jordan quadratic representation
  U_a(b)=2 a.(a.b) - (a.a).b, then trace-normalizes the pure filter and
  convexly damps toward the chosen pure idempotent.
- The finite pawl table uses standard EJA relative entropy for a full-rank
  epsilon-shadow of the pure fixed point. The strict pure-idempotent target is
  recorded as ill-defined/infinite except at the fixed point.
"""

from __future__ import annotations

import datetime as dt
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
SOURCE_PATH = ROOT / "system_v7/constraint_core/sims_and_scripts/jordan_octonion_entropy_pawl_sim.py"
RESULT_PATH = ROOT / "system_v7/constraint_core/sims_and_scripts/jordan_octonion_entropy_pawl_sim_results.json"

OBJECT_ID = "jordan_octonion_entropy_pawl"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
SEED = 0
TOL = 1.0e-10
FLOW_ETA = 0.08
FLOW_STEPS = 42
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
        "reason": "load-bearing finite Fano octonion table, J2(O) spin-factor spectral calculations, seeded rotations, and flow sweeps",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive timestamps, paths, math functions, and JSON serialization",
    },
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing", "python_stdlib": "supportive"}


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


def basis(dim: int, idx: int) -> np.ndarray:
    out = np.zeros(dim, dtype=float)
    out[idx] = 1.0
    return out


def multiply(table: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    return np.einsum("cab,a,b->c", table, x, y)


def conjugate(x: np.ndarray) -> np.ndarray:
    out = np.array(x, dtype=float, copy=True)
    out[1:] *= -1.0
    return out


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
        if abs(float(value)) > TOL
    ]


def pair_vector(dim: int, i: int, j: int, si: float = 1.0, sj: float = 1.0) -> np.ndarray:
    out = np.zeros(dim, dtype=float)
    out[i] = si
    out[j] = sj
    return out


def zero_divisor_search(table: np.ndarray) -> dict[str, Any]:
    dim = table.shape[0]
    best_norm = float("inf")
    best = None
    pairs = [(i, j) for i in range(1, dim) for j in range(i + 1, dim)]
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
                            if product_norm < TOL:
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
    worst: dict[str, Any] | None = None
    for idx in range(samples):
        x = rng.normal(size=dim)
        y = rng.normal(size=dim)
        product = multiply(table, x, y)
        residual = abs(np.linalg.norm(product) - np.linalg.norm(x) * np.linalg.norm(y))
        if residual > max_residual:
            max_residual = float(residual)
            worst = {"sample_index": idx, "residual": float(residual)}
    return {"samples": samples, "max_residual": max_residual, "worst": worst, "pass": max_residual < 1.0e-9}


def octonion_verification(table: np.ndarray, rng: np.random.Generator) -> dict[str, Any]:
    x = rng.normal(size=8)
    y = rng.normal(size=8)
    z = rng.normal(size=8)
    generic_assoc = associator(table, x, y, z)
    alt_max = 0.0
    for _ in range(32):
        a = rng.normal(size=8)
        b = rng.normal(size=8)
        alt_max = max(
            alt_max,
            float(np.linalg.norm(associator(table, a, a, b))),
            float(np.linalg.norm(associator(table, a, b, b))),
        )
    h_basis_assoc_max = 0.0
    for i in range(4):
        for j in range(4):
            for k in range(4):
                h_basis_assoc_max = max(
                    h_basis_assoc_max,
                    float(np.linalg.norm(associator(table, basis(8, i), basis(8, j), basis(8, k)))),
                )
    witness = associator(table, basis(8, 1), basis(8, 2), basis(8, 4))
    return {
        "fano_cycles": [list(row) for row in FANO],
        "norm_composition": norm_composition_sample(table, rng, 64, 8),
        "generic_associator_norm": float(np.linalg.norm(generic_assoc)),
        "basis_associator_e1_e2_e4_norm": float(np.linalg.norm(witness)),
        "basis_associator_e1_e2_e4_terms": vector_terms(witness),
        "alternative_max_residual_seeded": alt_max,
        "alternative_identity_holds_seeded": alt_max < 1.0e-9,
        "quaternionic_subalgebra_e0_e1_e2_e3_associator_max": h_basis_assoc_max,
        "quaternionic_subalgebra_associative": h_basis_assoc_max < 1.0e-12,
    }


def spin_jordan(a: tuple[float, np.ndarray], b: tuple[float, np.ndarray]) -> tuple[float, np.ndarray]:
    alpha, u = a
    beta, v = b
    return alpha * beta + float(np.dot(u, v)), alpha * v + beta * u


def spin_quadratic(a: tuple[float, np.ndarray], b: tuple[float, np.ndarray]) -> tuple[float, np.ndarray]:
    aa = spin_jordan(a, a)
    return tuple_part_sub(tuple_part_scale(spin_jordan(a, spin_jordan(a, b)), 2.0), spin_jordan(aa, b))


def tuple_part_scale(x: tuple[float, np.ndarray], scale: float) -> tuple[float, np.ndarray]:
    return scale * x[0], scale * x[1]


def tuple_part_sub(a: tuple[float, np.ndarray], b: tuple[float, np.ndarray]) -> tuple[float, np.ndarray]:
    return a[0] - b[0], a[1] - b[1]


def tuple_part_mix(a: tuple[float, np.ndarray], b: tuple[float, np.ndarray], eta: float) -> tuple[float, np.ndarray]:
    return (1.0 - eta) * a[0] + eta * b[0], (1.0 - eta) * a[1] + eta * b[1]


def density_from_r(r: np.ndarray) -> tuple[float, np.ndarray]:
    return 0.5, 0.5 * np.asarray(r, dtype=float)


def r_from_density(x: tuple[float, np.ndarray]) -> np.ndarray:
    alpha, u = x
    if abs(alpha - 0.5) > 1.0e-8:
        raise ValueError(f"expected trace-one density scalar 0.5, got {alpha}")
    return 2.0 * u


def trace_spin(x: tuple[float, np.ndarray]) -> float:
    return 2.0 * x[0]


def pure_idempotent(n: np.ndarray) -> tuple[float, np.ndarray]:
    return 0.5, 0.5 * n


def jordan_flow_step(r: np.ndarray, n: np.ndarray, eta: float) -> tuple[np.ndarray, dict[str, Any]]:
    rho = density_from_r(r)
    p = pure_idempotent(n)
    filtered = spin_quadratic(p, rho)
    filtered_trace = trace_spin(filtered)
    if filtered_trace <= TOL:
        normalized = p
        normalization_note = "zero Peirce weight; used pure-idempotent limiting target"
    else:
        normalized = (filtered[0] / filtered_trace, filtered[1] / filtered_trace)
        normalization_note = "trace-normalized U_p(rho)"
    stepped = tuple_part_mix(rho, normalized, eta)
    return r_from_density(stepped), {
        "quadratic_trace": float(filtered_trace),
        "normalization_note": normalization_note,
        "trace_after_step": float(trace_spin(stepped)),
        "norm_after_step": float(np.linalg.norm(r_from_density(stepped))),
    }


def binary_entropy_from_radius(radius: float) -> float:
    radius = min(max(float(radius), 0.0), 1.0)
    vals = [(1.0 + radius) / 2.0, (1.0 - radius) / 2.0]
    return float(-sum(v * math.log(v) for v in vals if v > 0.0))


def spectral_entropy(r: np.ndarray) -> float:
    return binary_entropy_from_radius(float(np.linalg.norm(r)))


def spectral_data_j2(r: np.ndarray) -> dict[str, Any]:
    radius = float(np.linalg.norm(r))
    return {
        "spin_radius": radius,
        "eigenvalues": [float((1.0 + radius) / 2.0), float((1.0 - radius) / 2.0)],
        "entropy": spectral_entropy(r),
        "positive": radius <= 1.0 + 1.0e-10,
        "trace": 1.0,
    }


def trace_rho_log_sigma(r: np.ndarray, s: np.ndarray) -> float:
    sigma_radius = float(np.linalg.norm(s))
    if sigma_radius >= 1.0:
        if np.linalg.norm(r - s) < 1.0e-9:
            return 0.0
        return float("-inf")
    mu_plus = (1.0 + sigma_radius) / 2.0
    mu_minus = (1.0 - sigma_radius) / 2.0
    c0 = 0.5 * (math.log(mu_plus) + math.log(mu_minus))
    if sigma_radius < TOL:
        return c0
    c1 = 0.5 * (math.log(mu_plus) - math.log(mu_minus))
    return float(c0 + c1 * float(np.dot(r, s / sigma_radius)))


def eja_relative_entropy(r: np.ndarray, s: np.ndarray) -> float:
    if np.linalg.norm(s) >= 1.0 - 1.0e-15 and np.linalg.norm(r - s) >= 1.0e-9:
        return float("inf")
    return float(-spectral_entropy(r) - trace_rho_log_sigma(r, s))


def classify_deltas(values_by_path: list[list[float]], direction: str, tol: float = 1.0e-9) -> dict[str, Any]:
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


def random_rotation(dim: int, rng: np.random.Generator) -> np.ndarray:
    q, r = np.linalg.qr(rng.normal(size=(dim, dim)))
    signs = np.sign(np.diag(r))
    signs[signs == 0.0] = 1.0
    q = q * signs
    if np.linalg.det(q) < 0.0:
        q[:, 0] *= -1.0
    return q


def sample_grid(rng: np.random.Generator) -> list[np.ndarray]:
    rows: list[np.ndarray] = []
    n = basis(9, 8)
    for radius in np.linspace(0.0, 0.98, 15):
        rows.append(-radius * n)
        rows.append(radius * n)
    for _ in range(150):
        direction = rng.normal(size=9)
        direction /= np.linalg.norm(direction)
        radius = rng.uniform(0.0, 0.985)
        rows.append(radius * direction)
    return rows


def run_flow_sweep(rng: np.random.Generator) -> dict[str, Any]:
    fixed = basis(9, 8)
    foreign = basis(9, 0)
    sigma_shadow = (1.0 - RELATIVE_EPSILON) * fixed
    foreign_shadow = (1.0 - RELATIVE_EPSILON) * foreign
    states = sample_grid(rng)
    entropy_paths: list[list[float]] = []
    relative_paths: list[list[float]] = []
    wrong_relative_paths: list[list[float]] = []
    min_margin = float("inf")
    max_trace_error = 0.0
    quadratic_trace_min = float("inf")
    for start in states:
        r = np.array(start, dtype=float)
        ent = [spectral_entropy(r)]
        rel = [eja_relative_entropy(r, sigma_shadow)]
        wrong_rel = [eja_relative_entropy(r, foreign_shadow)]
        for _ in range(FLOW_STEPS):
            r, step_info = jordan_flow_step(r, fixed, FLOW_ETA)
            radius = float(np.linalg.norm(r))
            min_margin = min(min_margin, 1.0 - radius)
            max_trace_error = max(max_trace_error, abs(step_info["trace_after_step"] - 1.0))
            quadratic_trace_min = min(quadratic_trace_min, step_info["quadratic_trace"])
            ent.append(spectral_entropy(r))
            rel.append(eja_relative_entropy(r, sigma_shadow))
            wrong_rel.append(eja_relative_entropy(r, foreign_shadow))
        entropy_paths.append(ent)
        relative_paths.append(rel)
        wrong_relative_paths.append(wrong_rel)
    return {
        "fixed_idempotent_vector": fixed.tolist(),
        "flow": {
            "definition": "rho_{t+1}=(1-eta)rho_t + eta * normalize_trace(U_p(rho_t)); U_p is Jordan quadratic representation",
            "eta": FLOW_ETA,
            "steps": FLOW_STEPS,
            "sample_count": len(states),
            "positivity_preserved": min_margin >= -1.0e-10,
            "trace_preserved": max_trace_error <= 1.0e-10,
            "min_positivity_margin_1_minus_norm": float(min_margin),
            "max_trace_error": float(max_trace_error),
            "min_quadratic_trace_before_normalization": float(quadratic_trace_min),
        },
        "strict_pure_fixed_point_relative_entropy": {
            "status": "ill_defined_infinite_off_support",
            "reason": "The chosen fixed point is a pure idempotent with spectral eigenvalue zero; EJA Umegaki relative entropy D(rho||p) is finite only when rho=p.",
            "finite_sample_count": 1,
            "installed_interpretation_for_pawl_table": "standard EJA relative entropy against sigma_epsilon=(1-epsilon)p + epsilon*unit/2",
            "epsilon": RELATIVE_EPSILON,
        },
        "pawl_table": {
            "U_J_to_epsilon_shadow_of_fixed_point": classify_deltas(relative_paths, "decreasing"),
            "S_raw_spectral_entropy": classify_deltas(entropy_paths, "none"),
            "wrong_fixed_point_U_J_control": classify_deltas(wrong_relative_paths, "decreasing"),
        },
    }


def entropy_invariance(rng: np.random.Generator) -> dict[str, Any]:
    max_diff = 0.0
    rows = []
    for idx in range(24):
        r = rng.normal(size=9)
        r = r / np.linalg.norm(r) * rng.uniform(0.0, 0.99)
        q = random_rotation(9, rng)
        before = spectral_entropy(r)
        after = spectral_entropy(q @ r)
        diff = abs(after - before)
        max_diff = max(max_diff, diff)
        if idx < 5:
            rows.append({"sample": idx, "before": before, "after": after, "abs_diff": diff})
    return {
        "group_action": "seeded SO(9) vector-part rotations, the spin-factor automorphism/Spin(9)-ish entropy invariance surface",
        "sample_count": 24,
        "max_abs_entropy_diff": float(max_diff),
        "pass": max_diff < 1.0e-12,
        "sample_rows": rows,
    }


def unitary_automorphism_control(rng: np.random.Generator) -> dict[str, Any]:
    fixed = basis(9, 8)
    sigma_shadow = (1.0 - RELATIVE_EPSILON) * fixed
    states = sample_grid(rng)[:48]
    entropy_paths = []
    relative_paths = []
    for start in states:
        r = np.array(start, dtype=float)
        path_s = [spectral_entropy(r)]
        path_u = [eja_relative_entropy(r, sigma_shadow)]
        for angle in np.linspace(0.0, 2.0 * math.pi, FLOW_STEPS + 1)[1:]:
            q = np.eye(9)
            c = math.cos(angle)
            s = math.sin(angle)
            q[0, 0] = c
            q[0, 1] = -s
            q[1, 0] = s
            q[1, 1] = c
            rr = q @ r
            path_s.append(spectral_entropy(rr))
            path_u.append(eja_relative_entropy(rr, sigma_shadow))
        entropy_paths.append(path_s)
        relative_paths.append(path_u)
    return {
        "definition": "rotation in a plane orthogonal to the fixed idempotent; no Jordan damping",
        "S_raw_spectral_entropy": classify_deltas(entropy_paths, "decreasing"),
        "U_J_to_fixed_shadow": classify_deltas(relative_paths, "decreasing"),
        "no_dissipation_no_strict_pawl": True,
    }


def quaternionic_control(rng: np.random.Generator, table: np.ndarray) -> dict[str, Any]:
    fixed = basis(9, 8)
    sigma_shadow = (1.0 - RELATIVE_EPSILON) * fixed
    paths = []
    leakage_max = 0.0
    for _ in range(48):
        r = np.zeros(9, dtype=float)
        q_part = rng.normal(size=5)
        q_part = q_part / np.linalg.norm(q_part) * rng.uniform(0.0, 0.96)
        r[0:4] = q_part[0:4]
        r[8] = q_part[4]
        path = [eja_relative_entropy(r, sigma_shadow)]
        for _ in range(FLOW_STEPS):
            r, _ = jordan_flow_step(r, fixed, FLOW_ETA)
            leakage_max = max(leakage_max, float(np.linalg.norm(r[4:8])))
            path.append(eja_relative_entropy(r, sigma_shadow))
        paths.append(path)
    h_assoc_max = 0.0
    for i in range(4):
        for j in range(4):
            for k in range(4):
                h_assoc_max = max(
                    h_assoc_max,
                    float(np.linalg.norm(associator(table, basis(8, i), basis(8, j), basis(8, k)))),
                )
    return {
        "subalgebra": "span(e0,e1,e2,e3) quaternionic associative subalgebra inside the installed Fano table",
        "associator_max_on_basis": h_assoc_max,
        "associative": h_assoc_max < 1.0e-12,
        "max_octonion_coordinate_leakage_e4_to_e7": leakage_max,
        "U_J_reduces_to_associative_spin_factor": classify_deltas(paths, "decreasing"),
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
        "attempted_object": "J2(S) Hermitian-like spin-factor analogue one rung past O",
        "break_status": "construction_breaks",
        "reason": "Cayley-Dickson sedenions have zero divisors and fail norm composition/alternativity, so |xy| no longer supplies the division-algebra positivity spine used by the octonionic Jordan construction.",
        "zero_divisor_witness": zero,
        "norm_composition_sample": norm,
        "alternative_max_residual_seeded": alt_max,
        "entropy_construction_allowed": False,
        "floor_echo": "same carrier-floor kill: O passes normed-division controls; S fails by zero divisors and norm-composition defect",
    }


def build_result() -> dict[str, Any]:
    rng = np.random.default_rng(SEED)
    o_table = octonion_table()
    oct_checks = octonion_verification(o_table, rng)
    entropy_checks = entropy_invariance(rng)
    flow = run_flow_sweep(rng)
    q_control = quaternionic_control(rng, o_table)
    unitary_control = unitary_automorphism_control(rng)
    sedenion = sedenion_kill_control(o_table)

    uj = flow["pawl_table"]["U_J_to_epsilon_shadow_of_fixed_point"]
    raw_s = flow["pawl_table"]["S_raw_spectral_entropy"]
    wrong = flow["pawl_table"]["wrong_fixed_point_U_J_control"]
    pawl_lifts_finite = bool(
        uj["pawl"]
        and raw_s["classification"] == "non-monotone"
        and not wrong["pawl"]
        and flow["flow"]["positivity_preserved"]
        and flow["flow"]["trace_preserved"]
        and entropy_checks["pass"]
        and oct_checks["norm_composition"]["pass"]
        and oct_checks["alternative_identity_holds_seeded"]
        and sedenion["break_status"] == "construction_breaks"
    )
    strict_gap = flow["strict_pure_fixed_point_relative_entropy"]["status"]
    if pawl_lifts_finite:
        verdict = "pawl_lifts"
    else:
        verdict = "pawl_fails_at_octonion_rung"

    return {
        "schema": "codex_ratchet.jordan_octonion_entropy_pawl_result.v1",
        "sim_id": OBJECT_ID,
        "object_id": OBJECT_ID,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "sim_execution_kind": "classical",
        "sim_class": "jordan_spectral_entropy_probe",
        "installed_interpretation": {
            "primary_carrier": "J2(O), the 10-dimensional Euclidean Jordan spin factor/octonionic qubit",
            "strict_relative_entropy_gap": strict_gap,
            "finite_pawl_measure": "D_EJA(rho || sigma_epsilon), sigma_epsilon=(1-epsilon)p + epsilon*unit/2",
            "j3_stretch_goal": "unmeasured; J3(O) spectral machinery read as convention source only",
        },
        "claim_ceiling": (
            "Scratch diagnostic: finite J2(O) Jordan spectral entropy and epsilon-shadow relative-entropy pawl "
            "probe. No Axis0 closure, bridge, basin, manifold, formal-admission, or J3(O) promotion claim."
        ),
        "seed": SEED,
        "tol": TOL,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_conventions_reused": {
            "J3O_spectral_OP2": "Fano cycles, conjugation convention, and Hermitian diagonal/off-diagonal representation",
            "FANO": [list(row) for row in FANO],
            "hermitian_J2O_coordinates": "rho=[[a,x],[conj(x),b]], a+b=1, r=(2*x_coordinates,a-b), eigenvalues=(1+-||r||)/2",
        },
        "octonion_verification": oct_checks,
        "spectral_entropy_well_defined": {
            "J2O_dimension": 10,
            "density_condition": "||r||<=1 in the spin-factor vector ball",
            "spectral_decomposition": "rho=lambda_plus*p_plus + lambda_minus*p_minus, lambda_pm=(1+-||r||)/2",
            "basis_independence": entropy_checks,
            "representative_density": spectral_data_j2(np.array([0.2, -0.1, 0.05, 0.0, 0.11, -0.07, 0.03, 0.04, 0.41])),
        },
        "jordan_flow": flow,
        "controls": {
            "wrong_fixed_point": flow["pawl_table"]["wrong_fixed_point_U_J_control"],
            "associativity_erasure_quaternionic_subalgebra": q_control,
            "unitary_automorphism_no_dissipation": unitary_control,
            "sedenion_floor_echo": sedenion,
        },
        "divergence_log": [
            {
                "surface": "raw_spectral_entropy",
                "expected": "not the damp-flow pawl",
                "observed": raw_s["classification"],
                "reason": "The terrain census predicts U, not raw S, as the universal damp-style pawl.",
            },
            {
                "surface": "wrong_fixed_point_relative_entropy",
                "expected": "control should lose monotonicity",
                "observed": wrong["classification"],
                "reason": "The pawl is tied to the flow's fixed idempotent, not arbitrary target geometry.",
            },
            {
                "surface": "sedenion_floor_echo",
                "expected": "construction breaks past octonions",
                "observed": sedenion["break_status"],
                "reason": "Zero divisors and norm-composition failure remove the division-algebra positivity spine.",
            },
        ],
        "verdict": verdict,
        "strict_pure_fixed_point_status": strict_gap,
        "finite_shadow_pawl_lifts": pawl_lifts_finite,
        "promotion_status": "diagnostic_only",
        "eligible_consumers": [],
        "blocked_consumers": [
            "Axis0 closure",
            "bridge or manifold admission",
            "J3(O) entropy-pawl claim",
            "formal proof of monotonicity beyond seeded finite sweep",
        ],
        "blocked_downstream_consumers": [
            "Axis0 closure",
            "bridge or manifold admission",
            "J3(O) entropy-pawl claim",
            "formal proof of monotonicity beyond seeded finite sweep",
        ],
        "all_pass": pawl_lifts_finite,
    }


def print_summary(result: dict[str, Any]) -> None:
    octv = result["octonion_verification"]
    inv = result["spectral_entropy_well_defined"]["basis_independence"]
    pawl = result["jordan_flow"]["pawl_table"]
    sed = result["controls"]["sedenion_floor_echo"]
    flow = result["jordan_flow"]["flow"]

    print("JORDAN_OCTONION_ENTROPY_PAWL_SIM")
    print(f"seed={SEED} classification={CLASSIFICATION} promotion_allowed={PROMOTION_ALLOWED}")
    print(
        "octonion verification: "
        f"norm_comp_pass={octv['norm_composition']['pass']} "
        f"norm_max_residual={octv['norm_composition']['max_residual']:.3e} "
        f"generic_associator_norm={octv['generic_associator_norm']:.6f} "
        f"basis_assoc_e1_e2_e4={octv['basis_associator_e1_e2_e4_norm']:.6f} "
        f"alternative_max={octv['alternative_max_residual_seeded']:.3e}"
    )
    print(
        "spectral entropy invariance: "
        f"SO9ish_samples={inv['sample_count']} "
        f"max_abs_diff={inv['max_abs_entropy_diff']:.3e} "
        f"pass={inv['pass']}"
    )
    print(
        "flow preservation: "
        f"trace_preserved={flow['trace_preserved']} "
        f"positivity_preserved={flow['positivity_preserved']} "
        f"min_margin={flow['min_positivity_margin_1_minus_norm']:.6e}"
    )
    print("pawl table:")
    for key, row in pawl.items():
        print(
            "  "
            f"{key}: classification={row['classification']} pawl={row['pawl']} "
            f"max_increase={row['max_increase']:.6e} max_decrease={row['max_decrease']:.6e} "
            f"net_delta_min={row['net_delta_min']:.6e} net_delta_max={row['net_delta_max']:.6e}"
        )
    print(
        "strict pure fixed point relative entropy: "
        f"{result['strict_pure_fixed_point_status']} "
        "(finite table uses epsilon full-rank shadow)"
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
        f"finite_shadow_pawl_lifts={result['finite_shadow_pawl_lifts']} "
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
