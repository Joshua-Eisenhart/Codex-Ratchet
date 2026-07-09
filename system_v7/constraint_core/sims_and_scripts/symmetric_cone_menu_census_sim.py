#!/usr/bin/env python3
"""Symmetric-cone menu census for small Koecher-Vinberg carriers.

Scratch diagnostic only.  This script applies the same finite gate battery to
the small menu named in the build card:

* classical R^3 simplex cone;
* spin factors J2(R), J2(C), J2(H), J2(O);
* rank-3 PSD cones over R, C, H;
* the exceptional Albert cone H3(O).

The common channel is a state-independent linear positive trace-preserving map

    Phi(x) = alpha*x + (1-alpha)*(eta*Pinch(x) + (1-eta)*tr(x)*sigma),

where Pinch is the Peirce/frame diagonal projection and sigma is a full-rank
fixed point in that same frame.  The reset term makes the fixed point unique
enough for a wrong-sigma control to have teeth; the pinch term keeps the v3
Peirce architecture load-bearing and is tested by a 1e-14 superposition gate.
"""

from __future__ import annotations

import datetime as dt
import json
import math
from pathlib import Path
from typing import Any, Callable

import numpy as np
from scipy.linalg import expm, logm


HERE = Path(__file__).resolve().parent
SOURCE_PATH = HERE / "symmetric_cone_menu_census_sim.py"
RESULT_PATH = HERE / "symmetric_cone_menu_census_sim_results.json"

SIM_ID = "symmetric_cone_menu_census_sim"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
SEED = 0

ALPHA = 0.83
ETA_PINCH = 0.41
STATE_COUNT = 20
FLOW_STEPS = 4
SUPERPOSITION_TOL = 1.0e-14
TRACE_TOL = 1.0e-11
POSITIVITY_TOL = 1.0e-9
DPI_TOL = 1.0e-10
S_INVARIANCE_TOL = 2.0e-10
REGRESSION_TOL = 2.0e-10
OCTONION_ASSOCIATOR_FLOOR = 1.0e-3

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite cone coordinates, spectra, seeded state grids, linearity gates, and DPI sweeps",
    },
    "scipy.linalg.expm": {
        "tried": True,
        "used": True,
        "reason": "load-bearing automorphism samples for H3(O) via exp([L_a,L_b]) and compact matrix-cone conjugations",
    },
    "scipy.linalg.logm": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent Umegaki regression check for the complex PSD cone",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive paths, timestamps, scalar math, and JSON serialization",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "scipy.linalg.expm": "load_bearing",
    "scipy.linalg.logm": "load_bearing",
    "python_stdlib": "supportive",
}


def clean(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return clean(obj.tolist())
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        obj = float(obj)
    if isinstance(obj, complex):
        return {"real": clean(obj.real), "imag": clean(obj.imag)}
    if isinstance(obj, float):
        if math.isfinite(obj):
            return obj
        if math.isnan(obj):
            return "NaN"
        return "Infinity" if obj > 0.0 else "-Infinity"
    return obj


def entropy_from_eigs(eigs: np.ndarray) -> float:
    vals = np.clip(np.asarray(eigs, dtype=float), 0.0, None)
    return float(-sum(float(x) * math.log(float(x)) for x in vals if x > 0.0))


def random_orthogonal(rng: np.random.Generator, n: int) -> np.ndarray:
    q, r = np.linalg.qr(rng.normal(size=(n, n)))
    signs = np.sign(np.diag(r))
    signs[signs == 0.0] = 1.0
    return q @ np.diag(signs)


def random_unitary(rng: np.random.Generator, n: int) -> np.ndarray:
    z = rng.normal(size=(n, n)) + 1j * rng.normal(size=(n, n))
    q, r = np.linalg.qr(z)
    phases = np.diag(r)
    phases = phases / np.maximum(np.abs(phases), 1.0e-15)
    return q @ np.diag(np.conj(phases))


def matrix_log_psd(a: np.ndarray) -> np.ndarray:
    vals, vecs = np.linalg.eigh(0.5 * (a + a.conj().T))
    if float(np.min(vals.real)) <= 0.0:
        raise ValueError("matrix log requires a positive definite state")
    return vecs @ np.diag(np.log(vals.real)) @ vecs.conj().T


def matrix_entropy(a: np.ndarray, trace_factor: float = 1.0) -> float:
    vals = np.linalg.eigvalsh(0.5 * (a + a.conj().T)).real
    if trace_factor != 1.0:
        vals = vals[::2]
    return entropy_from_eigs(vals)


def matrix_relative_entropy(rho: np.ndarray, sigma: np.ndarray, trace_factor: float = 1.0) -> float:
    log_rho = matrix_log_psd(rho)
    log_sigma = matrix_log_psd(sigma)
    val = np.trace(rho @ (log_rho - log_sigma))
    return float((trace_factor * np.real_if_close(val, tol=1000)).real)


def random_density_matrix(
    rng: np.random.Generator,
    n: int,
    kind: str,
    eps: float = 0.10,
) -> np.ndarray:
    if kind == "real":
        a = rng.normal(size=(n, n))
        h = a @ a.T + eps * np.eye(n)
        return h / float(np.trace(h))
    if kind == "complex":
        a = rng.normal(size=(n, n)) + 1j * rng.normal(size=(n, n))
        h = a @ a.conj().T + eps * np.eye(n)
        return h / float(np.trace(h).real)
    raise ValueError(kind)


def hermitian_part(a: np.ndarray) -> np.ndarray:
    return 0.5 * (a + a.conj().T)


def quat_rep(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Complex 2n x 2n representation of A + B*j."""
    return np.block([[a, b], [-b.conj(), a.conj()]])


def random_quaternionic_matrix_rep(rng: np.random.Generator, n: int) -> np.ndarray:
    a = rng.normal(size=(n, n)) + 1j * rng.normal(size=(n, n))
    b = rng.normal(size=(n, n)) + 1j * rng.normal(size=(n, n))
    return quat_rep(a, b)


def random_quaternionic_density_rep(rng: np.random.Generator, n: int) -> np.ndarray:
    q = random_quaternionic_matrix_rep(rng, n)
    h = q @ q.conj().T + 0.10 * np.eye(2 * n)
    return h / (0.5 * float(np.trace(h).real))


def quaternionic_diag_state(probs: np.ndarray) -> np.ndarray:
    vals = np.asarray(probs, dtype=float)
    return np.diag(np.concatenate([vals, vals])).astype(complex)


def quaternionic_pinch(a: np.ndarray) -> np.ndarray:
    n = a.shape[0] // 2
    diag = []
    for i in range(n):
        diag.append(0.5 * float((a[i, i] + a[i + n, i + n]).real))
    return quaternionic_diag_state(np.asarray(diag, dtype=float))


def random_quaternionic_unitary_rep(rng: np.random.Generator, n: int) -> np.ndarray:
    x = random_quaternionic_matrix_rep(rng, n)
    k = x - x.conj().T
    return expm(0.17 * k)


FANO = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
]


def setprod(table: np.ndarray, a: int, b: int, c: int, s: float) -> None:
    table[c, a, b] = s


def octonion_table(corrupt: bool = False) -> np.ndarray:
    table = np.zeros((8, 8, 8), dtype=float)
    for a in range(8):
        setprod(table, 0, a, a, 1.0)
        setprod(table, a, 0, a, 1.0)
    for a in range(1, 8):
        setprod(table, a, a, 0, -1.0)
    for row_idx, (i, j, k) in enumerate(FANO):
        sign = -1.0 if corrupt and row_idx == 0 else 1.0
        for a, b, c, s in (
            (i, j, k, sign),
            (j, k, i, 1.0),
            (k, i, j, 1.0),
            (j, i, k, -1.0),
            (k, j, i, -1.0),
            (i, k, j, -1.0),
        ):
            setprod(table, a, b, c, s)
    return table


def omul(table: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    return np.einsum("cab,a,b->c", table, x, y)


def oconj(x: np.ndarray) -> np.ndarray:
    out = np.array(x, dtype=float, copy=True)
    out[1:] *= -1.0
    return out


def oassoc(table: np.ndarray, x: np.ndarray, y: np.ndarray, z: np.ndarray) -> np.ndarray:
    return omul(table, omul(table, x, y), z) - omul(table, x, omul(table, y, z))


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


def j3_unit() -> np.ndarray:
    return j3_from_parts(np.ones(3), np.zeros(8), np.zeros(8), np.zeros(8))


def j3_diag(values: np.ndarray | list[float]) -> np.ndarray:
    return j3_from_parts(np.asarray(values, dtype=float), np.zeros(8), np.zeros(8), np.zeros(8))


def j3_trace(a: np.ndarray) -> float:
    return float(a[0, 0, 0] + a[1, 1, 0] + a[2, 2, 0])


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


def j3_norm2(x: np.ndarray) -> float:
    return float(np.dot(x, x))


def j3_sigma2(a: np.ndarray) -> float:
    d0, d1, d2 = float(a[0, 0, 0]), float(a[1, 1, 0]), float(a[2, 2, 0])
    return float(d0 * d1 + d0 * d2 + d1 * d2 - j3_norm2(a[0, 1, :]) - j3_norm2(a[0, 2, :]) - j3_norm2(a[1, 2, :]))


def j3_det(table: np.ndarray, a: np.ndarray) -> float:
    d0, d1, d2 = float(a[0, 0, 0]), float(a[1, 1, 0]), float(a[2, 2, 0])
    x01, x02, x12 = a[0, 1, :], a[0, 2, :], a[1, 2, :]
    triple = float(omul(table, omul(table, x01, x12), oconj(x02))[0])
    return float(d0 * d1 * d2 + 2.0 * triple - d0 * j3_norm2(x12) - d1 * j3_norm2(x02) - d2 * j3_norm2(x01))


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


def j3_eigs(table: np.ndarray, a: np.ndarray) -> np.ndarray:
    return cubic_eigenvalues(j3_trace(a), j3_sigma2(a), j3_det(table, a))


def j3_log_from_projectors(table: np.ndarray, sigma: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
    eigs = j3_eigs(table, sigma)
    if float(np.min(eigs)) <= 0.0:
        raise ValueError("J3(O) log requires full-rank sigma")
    unit = j3_unit()
    projectors = []
    for i, lam in enumerate(eigs):
        others = [float(eigs[j]) for j in range(3) if j != i]
        numerator = j3_jordan(table, sigma - others[0] * unit, sigma - others[1] * unit)
        denom = (float(lam) - others[0]) * (float(lam) - others[1])
        projectors.append(numerator / denom)
    log_sigma = sum(math.log(float(lam)) * p for lam, p in zip(eigs, projectors))
    recon = sum(float(lam) * p for lam, p in zip(eigs, projectors))
    return log_sigma, {
        "method": "full Lagrange spectral-projector log on cubic eigenvalues",
        "eigenvalues": [float(x) for x in eigs],
        "reconstruction_error": float(np.linalg.norm(recon - sigma)),
    }


def j3_entropy(table: np.ndarray, rho: np.ndarray) -> float:
    return entropy_from_eigs(j3_eigs(table, rho))


def j3_relative_entropy(table: np.ndarray, rho: np.ndarray, sigma: np.ndarray) -> float:
    log_rho, _ = j3_log_from_projectors(table, rho)
    log_sigma, _ = j3_log_from_projectors(table, sigma)
    return float(j3_trace(j3_jordan(table, rho, log_rho - log_sigma)))


def j3_pinch(rho: np.ndarray) -> np.ndarray:
    return j3_diag([rho[0, 0, 0], rho[1, 1, 0], rho[2, 2, 0]])


def j3_random_density(rng: np.random.Generator, table: np.ndarray, require_assoc: bool = True) -> np.ndarray:
    for _ in range(20000):
        diag_delta = rng.normal(size=3)
        diag_delta -= float(np.mean(diag_delta))
        diag = np.array([0.50, 0.30, 0.20], dtype=float) + 0.035 * diag_delta
        x01 = rng.normal(scale=0.028, size=8)
        x02 = rng.normal(scale=0.028, size=8)
        x12 = rng.normal(scale=0.028, size=8)
        cand = j3_from_parts(diag, x01, x02, x12)
        eigs = j3_eigs(table, cand)
        assoc = float(np.linalg.norm(oassoc(table, x01, x02, x12)))
        if abs(j3_trace(cand) - 1.0) < 1.0e-9 and float(np.min(eigs)) > 1.0e-5:
            if not require_assoc or assoc > OCTONION_ASSOCIATOR_FLOOR:
                return cand
    raise RuntimeError("could not sample H3(O) density")


def j3_vec_from_elem(x: np.ndarray) -> np.ndarray:
    out = np.zeros(27, dtype=float)
    out[0:3] = [x[0, 0, 0], x[1, 1, 0], x[2, 2, 0]]
    out[3:11] = x[0, 1, :]
    out[11:19] = x[0, 2, :]
    out[19:27] = x[1, 2, :]
    return out


def j3_elem_from_vec(v: np.ndarray) -> np.ndarray:
    return j3_from_parts(np.asarray(v[0:3]), np.asarray(v[3:11]), np.asarray(v[11:19]), np.asarray(v[19:27]))


def j3_left_matrix(table: np.ndarray, a: np.ndarray) -> np.ndarray:
    cols = []
    for idx in range(27):
        e = np.zeros(27, dtype=float)
        e[idx] = 1.0
        cols.append(j3_vec_from_elem(j3_jordan(table, a, j3_elem_from_vec(e))))
    return np.column_stack(cols)


def j3_automorphism(table: np.ndarray) -> np.ndarray:
    a = j3_from_parts(np.zeros(3), np.array([0.0, 1.0, 0, 0, 0, 0, 0, 0]), np.zeros(8), np.zeros(8))
    b = j3_diag([1.0, -1.0, 0.0])
    d = j3_left_matrix(table, a) @ j3_left_matrix(table, b) - j3_left_matrix(table, b) @ j3_left_matrix(table, a)
    return expm(0.11 * d)


def spin_state(v: np.ndarray) -> tuple[float, np.ndarray]:
    return 0.5, np.asarray(v, dtype=float)


def spin_eigs(x: tuple[float, np.ndarray]) -> np.ndarray:
    alpha, v = x
    r = float(np.linalg.norm(v))
    return np.array([alpha + r, alpha - r], dtype=float)


def spin_entropy(x: tuple[float, np.ndarray]) -> float:
    return entropy_from_eigs(spin_eigs(x))


def spin_jordan(a: tuple[float, np.ndarray], b: tuple[float, np.ndarray]) -> tuple[float, np.ndarray]:
    aa, av = a
    ba, bv = b
    return aa * ba + float(np.dot(av, bv)), aa * bv + ba * av


def spin_relative_entropy(rho: tuple[float, np.ndarray], sigma: tuple[float, np.ndarray]) -> float:
    rho_eigs = spin_eigs(rho)
    sigma_alpha, sigma_v = sigma
    sigma_norm = float(np.linalg.norm(sigma_v))
    if sigma_norm <= 1.0e-15:
        log_sigma = (math.log(sigma_alpha), np.zeros_like(sigma_v))
    else:
        u = sigma_v / sigma_norm
        lp = math.log(sigma_alpha + sigma_norm)
        lm = math.log(sigma_alpha - sigma_norm)
        log_sigma = (0.5 * (lp + lm), 0.5 * (lp - lm) * u)
    log_rho_trace = sum(float(x) * math.log(float(x)) for x in rho_eigs if x > 0.0)
    trace_rho_log_sigma = 2.0 * spin_jordan(rho, log_sigma)[0]
    return float(log_rho_trace - trace_rho_log_sigma)


def spin_pinch(axis: np.ndarray, x: tuple[float, np.ndarray]) -> tuple[float, np.ndarray]:
    alpha, v = x
    return alpha, float(np.dot(v, axis)) * axis


def spin_add(a: tuple[float, np.ndarray], b: tuple[float, np.ndarray]) -> tuple[float, np.ndarray]:
    return a[0] + b[0], a[1] + b[1]


def spin_scale(c: float, a: tuple[float, np.ndarray]) -> tuple[float, np.ndarray]:
    return c * a[0], c * a[1]


def spin_norm(a: tuple[float, np.ndarray]) -> float:
    return float(math.sqrt(a[0] * a[0] + np.dot(a[1], a[1])))


def phi_generic(x: Any, sigma: Any, trace_fn: Callable[[Any], float], pinch_fn: Callable[[Any], Any], add_fn: Callable[[Any, Any], Any], scale_fn: Callable[[float, Any], Any]) -> Any:
    pinched = pinch_fn(x)
    reset = scale_fn(trace_fn(x), sigma)
    mix = add_fn(scale_fn(ETA_PINCH, pinched), scale_fn(1.0 - ETA_PINCH, reset))
    return add_fn(scale_fn(ALPHA, x), scale_fn(1.0 - ALPHA, mix))


def vector_add(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return a + b


def vector_scale(c: float, a: np.ndarray) -> np.ndarray:
    return c * a


def matrix_add(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return a + b


def matrix_scale(c: float, a: np.ndarray) -> np.ndarray:
    return c * a


def j3_add(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return a + b


def j3_scale(c: float, a: np.ndarray) -> np.ndarray:
    return c * a


def run_linearity_gate(
    states: list[Any],
    phi: Callable[[Any], Any],
    add_fn: Callable[[Any, Any], Any],
    scale_fn: Callable[[float, Any], Any],
    norm_fn: Callable[[Any], float],
    rng: np.random.Generator,
) -> dict[str, Any]:
    max_err = 0.0
    rows = []
    for idx in range(12):
        x = states[idx % len(states)]
        y = states[-(idx % len(states) + 1)]
        a = float(rng.normal())
        b = float(rng.normal())
        lhs = phi(add_fn(scale_fn(a, x), scale_fn(b, y)))
        rhs = add_fn(scale_fn(a, phi(x)), scale_fn(b, phi(y)))
        err = norm_fn(add_fn(lhs, scale_fn(-1.0, rhs)))
        max_err = max(max_err, err)
        if idx < 3:
            rows.append({"sample": idx, "a": a, "b": b, "superposition_error": err})
    return {
        "samples": 12,
        "max_superposition_error": max_err,
        "tolerance": SUPERPOSITION_TOL,
        "pass": bool(max_err <= SUPERPOSITION_TOL),
        "sample_rows": rows,
    }


def dpi_sweep(states: list[Any], phi: Callable[[Any], Any], rel: Callable[[Any, Any], float], sigma: Any) -> dict[str, Any]:
    violations = []
    max_increase = -float("inf")
    min_delta = float("inf")
    rows = []
    for state_idx, start in enumerate(states):
        current = start
        d_prev = rel(current, sigma)
        for step in range(FLOW_STEPS):
            nxt = phi(current)
            d_next = rel(nxt, sigma)
            delta = float(d_next - d_prev)
            max_increase = max(max_increase, delta)
            min_delta = min(min_delta, delta)
            if delta > DPI_TOL:
                violations.append({"state_index": state_idx, "step": step, "delta": delta, "before": d_prev, "after": d_next})
            if state_idx < 4 and step in {0, FLOW_STEPS - 1}:
                rows.append({"state_index": state_idx, "step": step, "before": d_prev, "after": d_next, "delta": delta})
            current, d_prev = nxt, d_next
    return {
        "states": len(states),
        "steps_per_state": FLOW_STEPS,
        "violation_count": len(violations),
        "max_increase": float(max_increase),
        "most_negative_delta": float(min_delta),
        "dpi_holds_on_grid": bool(len(violations) == 0),
        "tolerance": DPI_TOL,
        "sample_rows": rows,
        "violations": violations[:6],
    }


def wrong_sigma_control(states: list[Any], phi: Callable[[Any], Any], rel: Callable[[Any, Any], float], wrong_sigma: Any, norm_fn: Callable[[Any], float], sub_fn: Callable[[Any, Any], Any]) -> dict[str, Any]:
    rows = []
    violation_count = 0
    max_increase = -float("inf")
    for idx, rho in enumerate([wrong_sigma] + states[:8]):
        before = rel(rho, wrong_sigma)
        after_state = phi(rho)
        after = rel(after_state, wrong_sigma)
        delta = float(after - before)
        max_increase = max(max_increase, delta)
        if delta > DPI_TOL:
            violation_count += 1
        if idx < 5:
            rows.append({"sample": idx, "delta": delta, "before": before, "after": after})
    return {
        "meaning": "Uses a sigma that is not fixed by Phi; D(wrong_sigma||wrong_sigma)=0 should move upward after Phi.",
        "phi_wrong_sigma_distance": norm_fn(sub_fn(phi(wrong_sigma), wrong_sigma)),
        "violation_count": violation_count,
        "max_increase": float(max_increase),
        "breaks": bool(violation_count > 0),
        "sample_rows": rows,
    }


def classical_cone(rng: np.random.Generator) -> dict[str, Any]:
    sigma = np.array([0.50, 0.30, 0.20], dtype=float)
    wrong = np.array([0.25, 0.25, 0.50], dtype=float)
    states = [rng.dirichlet(np.array([1.4, 1.8, 2.2])) for _ in range(STATE_COUNT)]

    def rel(p: np.ndarray, q: np.ndarray) -> float:
        return float(sum(float(pi) * (math.log(float(pi)) - math.log(float(qi))) for pi, qi in zip(p, q) if pi > 0.0))

    phi = lambda x: phi_generic(x, sigma, lambda y: float(np.sum(y)), lambda y: y, vector_add, vector_scale)
    perms = [np.array([1, 2, 0]), np.array([2, 0, 1]), np.array([0, 2, 1])]
    max_s_diff = max(abs(entropy_from_eigs(p[perm]) - entropy_from_eigs(p)) for p in states[:8] for perm in perms)
    fixed_error = float(np.linalg.norm(phi(sigma) - sigma))
    positivity_min = min(float(np.min(phi(p))) for p in states)
    return finish_cone(
        name="classical_R3",
        family="classical simplex",
        dimension=3,
        spectral_method="component KL on the R^3 simplex",
        states=states,
        sigma=sigma,
        wrong_sigma=wrong,
        phi=phi,
        entropy=lambda x: entropy_from_eigs(x),
        rel=rel,
        trace_fn=lambda x: float(np.sum(x)),
        add_fn=vector_add,
        scale_fn=vector_scale,
        norm_fn=lambda x: float(np.linalg.norm(x)),
        sub_fn=lambda a, b: a - b,
        s_invariance={"automorphism_sample": "simplex vertex permutations", "max_abs_entropy_diff": float(max_s_diff), "pass": bool(max_s_diff <= S_INVARIANCE_TOL)},
        fixed_error=fixed_error,
        positivity_min=positivity_min,
        rng=rng,
        expected_zero_violations=True,
    )


def spin_cone(label: str, dim: int, rng: np.random.Generator) -> dict[str, Any]:
    axis = np.zeros(dim - 1, dtype=float)
    axis[0] = 1.0
    sigma = spin_state(0.10 * axis)
    wrong_axis = np.zeros(dim - 1, dtype=float)
    wrong_axis[-1] = 1.0
    wrong = spin_state(0.16 * wrong_axis)
    states = []
    for _ in range(STATE_COUNT):
        v = rng.normal(size=dim - 1)
        v /= max(np.linalg.norm(v), 1.0e-15)
        v *= float(rng.uniform(0.02, 0.43))
        states.append(spin_state(v))
    phi = lambda x: phi_generic(x, sigma, lambda y: 2.0 * y[0], lambda y: spin_pinch(axis, y), spin_add, spin_scale)
    max_s_diff = 0.0
    for rho in states[:8]:
        q = random_orthogonal(rng, dim - 1)
        moved = (rho[0], q @ rho[1])
        max_s_diff = max(max_s_diff, abs(spin_entropy(moved) - spin_entropy(rho)))
    fixed_error = spin_norm(spin_add(phi(sigma), spin_scale(-1.0, sigma)))
    positivity_min = min(float(np.min(spin_eigs(phi(rho)))) for rho in states)
    result = finish_cone(
        name=label,
        family="spin factor",
        dimension=dim,
        spectral_method="rank-2 quadratic spectrum alpha +/- ||v|| with Peirce projectors p_pm",
        states=states,
        sigma=sigma,
        wrong_sigma=wrong,
        phi=phi,
        entropy=spin_entropy,
        rel=spin_relative_entropy,
        trace_fn=lambda x: 2.0 * x[0],
        add_fn=spin_add,
        scale_fn=spin_scale,
        norm_fn=spin_norm,
        sub_fn=lambda a, b: spin_add(a, spin_scale(-1.0, b)),
        s_invariance={"automorphism_sample": f"O({dim - 1}) vector rotations", "max_abs_entropy_diff": float(max_s_diff), "pass": bool(max_s_diff <= S_INVARIANCE_TOL)},
        fixed_error=fixed_error,
        positivity_min=positivity_min,
        rng=rng,
        expected_zero_violations=True,
    )
    if label == "spin_J2O":
        table = octonion_table(False)
        result["octonion_content_gate"] = octonion_content_gate(table, corrupt_table=octonion_table(True), rng=rng, h3_states=None)
    return result


def psd_cone(field: str, rng: np.random.Generator) -> dict[str, Any]:
    probs = np.array([0.50, 0.30, 0.20], dtype=float)
    wrong_probs = np.array([0.20, 0.50, 0.30], dtype=float)
    if field == "R":
        sigma = np.diag(probs)
        wrong = np.diag(wrong_probs)
        states = [random_density_matrix(rng, 3, "real") for _ in range(STATE_COUNT)]
        pinch = lambda x: np.diag(np.diag(x))
        trace_fn = lambda x: float(np.trace(x).real)
        rel = lambda a, b: matrix_relative_entropy(a.astype(complex), b.astype(complex))
        entropy = lambda x: matrix_entropy(x.astype(complex))
        def conj(x: np.ndarray) -> np.ndarray:
            q = random_orthogonal(rng, 3)
            return q @ x @ q.T

        auto_name = "orthogonal conjugation"
        name, dimension = "PSD_Sym3R", 6
    elif field == "C":
        sigma = np.diag(probs).astype(complex)
        wrong = np.diag(wrong_probs).astype(complex)
        states = [random_density_matrix(rng, 3, "complex") for _ in range(STATE_COUNT)]
        pinch = lambda x: np.diag(np.diag(x))
        trace_fn = lambda x: float(np.trace(x).real)
        rel = matrix_relative_entropy
        entropy = matrix_entropy
        auto_name = "unitary conjugation"

        def conj(x: np.ndarray) -> np.ndarray:
            u = random_unitary(rng, 3)
            return u @ x @ u.conj().T

        name, dimension = "PSD_Herm3C", 9
    elif field == "H":
        sigma = quaternionic_diag_state(probs)
        wrong = quaternionic_diag_state(wrong_probs)
        states = [random_quaternionic_density_rep(rng, 3) for _ in range(STATE_COUNT)]
        pinch = quaternionic_pinch
        trace_fn = lambda x: 0.5 * float(np.trace(x).real)
        rel = lambda a, b: matrix_relative_entropy(a, b, trace_factor=0.5)
        entropy = lambda x: matrix_entropy(x, trace_factor=0.5)
        auto_name = "compact symplectic/quaternionic-unitary conjugation"

        def conj(x: np.ndarray) -> np.ndarray:
            u = random_quaternionic_unitary_rep(rng, 3)
            return u @ x @ u.conj().T

        name, dimension = "PSD_Herm3H", 15
    else:
        raise ValueError(field)
    phi = lambda x: phi_generic(x, sigma, trace_fn, pinch, matrix_add, matrix_scale)
    max_s_diff = max(abs(entropy(conj(rho)) - entropy(rho)) for rho in states[:8])
    fixed_error = float(np.linalg.norm(phi(sigma) - sigma))
    positivity_min = min(float(np.min(np.linalg.eigvalsh(hermitian_part(phi(rho))).real)) for rho in states)
    result = finish_cone(
        name=name,
        family=f"rank-3 PSD over {field}",
        dimension=dimension,
        spectral_method="full matrix spectral-projector log; quaternionic trace is half the complex representation trace" if field == "H" else "full matrix spectral-projector log",
        states=states,
        sigma=sigma,
        wrong_sigma=wrong,
        phi=phi,
        entropy=entropy,
        rel=rel,
        trace_fn=trace_fn,
        add_fn=matrix_add,
        scale_fn=matrix_scale,
        norm_fn=lambda x: float(np.linalg.norm(x)),
        sub_fn=lambda a, b: a - b,
        s_invariance={"automorphism_sample": auto_name, "max_abs_entropy_diff": float(max_s_diff), "pass": bool(max_s_diff <= S_INVARIANCE_TOL)},
        fixed_error=fixed_error,
        positivity_min=positivity_min,
        rng=rng,
        expected_zero_violations=True,
    )
    if field == "C":
        rows = []
        max_diff = 0.0
        for idx, rho in enumerate(states[:8]):
            spectral = rel(rho, sigma)
            direct = float(np.trace(rho @ (logm(rho) - logm(sigma))).real)
            diff = abs(spectral - direct)
            max_diff = max(max_diff, diff)
            if idx < 3:
                rows.append({"sample": idx, "spectral_projector": spectral, "numpy_umegaki_logm": direct, "abs_diff": diff})
        result["known_value_regression"] = {
            "target": "Herm3(C) Umegaki relative entropy",
            "max_abs_diff": float(max_diff),
            "tolerance": REGRESSION_TOL,
            "pass": bool(max_diff <= REGRESSION_TOL),
            "sample_rows": rows,
        }
    return result


def h3o_cone(rng: np.random.Generator) -> dict[str, Any]:
    table = octonion_table(False)
    sigma = j3_diag([0.50, 0.30, 0.20])
    wrong = j3_diag([0.20, 0.50, 0.30])
    states = [j3_random_density(rng, table, require_assoc=True) for _ in range(STATE_COUNT)]
    phi = lambda x: phi_generic(x, sigma, j3_trace, j3_pinch, j3_add, j3_scale)
    auto = j3_automorphism(table)
    max_s_diff = 0.0
    for rho in states[:8]:
        moved = j3_elem_from_vec(auto @ j3_vec_from_elem(rho))
        max_s_diff = max(max_s_diff, abs(j3_entropy(table, moved) - j3_entropy(table, rho)))
    fixed_error = float(np.linalg.norm(phi(sigma) - sigma))
    positivity_min = min(float(np.min(j3_eigs(table, phi(rho)))) for rho in states)
    result = finish_cone(
        name="H3O_exceptional",
        family="exceptional Albert cone",
        dimension=27,
        spectral_method="full Lagrange spectral-projector log on cubic Albert spectrum",
        states=states,
        sigma=sigma,
        wrong_sigma=wrong,
        phi=phi,
        entropy=lambda x: j3_entropy(table, x),
        rel=lambda a, b: j3_relative_entropy(table, a, b),
        trace_fn=j3_trace,
        add_fn=j3_add,
        scale_fn=j3_scale,
        norm_fn=lambda x: float(np.linalg.norm(x)),
        sub_fn=lambda a, b: a - b,
        s_invariance={"automorphism_sample": "exp(t[L_a,L_b]) Jordan derivation", "max_abs_entropy_diff": float(max_s_diff), "pass": bool(max_s_diff <= S_INVARIANCE_TOL)},
        fixed_error=fixed_error,
        positivity_min=positivity_min,
        rng=rng,
        expected_zero_violations=False,
    )
    result["octonion_content_gate"] = octonion_content_gate(table, corrupt_table=octonion_table(True), rng=rng, h3_states=states)
    _, log_report = j3_log_from_projectors(table, sigma)
    result["spectral_log_sigma"] = log_report
    return result


def octonion_content_gate(
    table: np.ndarray,
    corrupt_table: np.ndarray,
    rng: np.random.Generator,
    h3_states: list[np.ndarray] | None,
) -> dict[str, Any]:
    triples = []
    assoc_values = []
    if h3_states is not None:
        for rho in h3_states:
            assoc_values.append(float(np.linalg.norm(oassoc(table, rho[0, 1, :], rho[0, 2, :], rho[1, 2, :]))))
    else:
        for _ in range(STATE_COUNT):
            a = rng.normal(size=8)
            b = rng.normal(size=8)
            c = rng.normal(size=8)
            assoc_values.append(float(np.linalg.norm(oassoc(table, a, b, c))))
    for idx, val in enumerate(assoc_values[:4]):
        triples.append({"sample": idx, "associator_norm": val})

    alt_max = 0.0
    corrupt_alt_max = 0.0
    norm_residual = 0.0
    corrupt_norm_residual = 0.0
    for _ in range(32):
        a = rng.normal(size=8)
        b = rng.normal(size=8)
        alt_max = max(alt_max, float(np.linalg.norm(oassoc(table, a, a, b))), float(np.linalg.norm(oassoc(table, a, b, b))))
        corrupt_alt_max = max(
            corrupt_alt_max,
            float(np.linalg.norm(oassoc(corrupt_table, a, a, b))),
            float(np.linalg.norm(oassoc(corrupt_table, a, b, b))),
        )
        prod = omul(table, a, b)
        bad_prod = omul(corrupt_table, a, b)
        norm_residual = max(norm_residual, abs(float(np.dot(prod, prod)) - float(np.dot(a, a) * np.dot(b, b))))
        corrupt_norm_residual = max(
            corrupt_norm_residual,
            abs(float(np.dot(bad_prod, bad_prod)) - float(np.dot(a, a) * np.dot(b, b))),
        )
    fraction = float(sum(v > OCTONION_ASSOCIATOR_FLOOR for v in assoc_values) / len(assoc_values))
    return {
        "meaning": "Grok-injection guard: nonzero octonion associator content prevents C-slice escape; corrupted Fano table must fail upstream algebra checks.",
        "samples": len(assoc_values),
        "associator_floor": OCTONION_ASSOCIATOR_FLOOR,
        "fraction_above_floor": fraction,
        "associator_min": float(min(assoc_values)),
        "associator_median": float(np.median(assoc_values)),
        "associator_max": float(max(assoc_values)),
        "sample_rows": triples,
        "alternative_identity_max_residual": float(alt_max),
        "norm_composition_max_residual": float(norm_residual),
        "corrupted_table_alternative_residual": float(corrupt_alt_max),
        "corrupted_table_norm_residual": float(corrupt_norm_residual),
        "pass": bool(fraction >= 0.80 and alt_max <= 1.0e-9 and norm_residual <= 1.0e-8),
        "corrupted_table_breaks": bool(corrupt_alt_max > 1.0e-8 or corrupt_norm_residual > 1.0e-8),
    }


def finish_cone(
    name: str,
    family: str,
    dimension: int,
    spectral_method: str,
    states: list[Any],
    sigma: Any,
    wrong_sigma: Any,
    phi: Callable[[Any], Any],
    entropy: Callable[[Any], float],
    rel: Callable[[Any, Any], float],
    trace_fn: Callable[[Any], float],
    add_fn: Callable[[Any, Any], Any],
    scale_fn: Callable[[float, Any], Any],
    norm_fn: Callable[[Any], float],
    sub_fn: Callable[[Any, Any], Any],
    s_invariance: dict[str, Any],
    fixed_error: float,
    positivity_min: float,
    rng: np.random.Generator,
    expected_zero_violations: bool,
) -> dict[str, Any]:
    line = run_linearity_gate(states, phi, add_fn, scale_fn, norm_fn, rng)
    dpi = dpi_sweep(states, phi, rel, sigma)
    wrong = wrong_sigma_control(states, phi, rel, wrong_sigma, norm_fn, sub_fn)
    trace_errors = [abs(trace_fn(phi(rho)) - 1.0) for rho in states]
    verdict = "dpi_holds_on_grid" if dpi["violation_count"] == 0 else "dpi_violated_on_grid"
    construction_pass = bool(
        s_invariance["pass"]
        and line["pass"]
        and fixed_error <= SUPERPOSITION_TOL
        and max(trace_errors) <= TRACE_TOL
        and positivity_min >= -POSITIVITY_TOL
        and wrong["breaks"]
    )
    theorem_cell_pass = bool((not expected_zero_violations) or dpi["violation_count"] == 0)
    return {
        "cone": name,
        "family": family,
        "dimension": dimension,
        "spectral_method": spectral_method,
        "state_grid": {"seeded_states": len(states), "trajectory_steps": FLOW_STEPS},
        "gates": {
            "S_invariance": s_invariance,
            "linearity_superposition": line,
            "fixed_point": {"phi_sigma_distance": float(fixed_error), "tolerance": SUPERPOSITION_TOL, "pass": bool(fixed_error <= SUPERPOSITION_TOL)},
            "trace_positivity": {
                "max_trace_error": float(max(trace_errors)),
                "min_post_phi_eigenvalue_or_component": float(positivity_min),
                "trace_pass": bool(max(trace_errors) <= TRACE_TOL),
                "positivity_pass": bool(positivity_min >= -POSITIVITY_TOL),
            },
        },
        "dpi_table": dpi,
        "controls": {"wrong_sigma": wrong},
        "expected_zero_violations": expected_zero_violations,
        "dpi_verdict": verdict,
        "construction_pass": construction_pass,
        "theorem_cell_pass": theorem_cell_pass,
        "honest_cell_pass": bool(construction_pass and theorem_cell_pass),
    }


def build_result() -> dict[str, Any]:
    rng = np.random.default_rng(SEED)
    cones = [
        classical_cone(rng),
        spin_cone("spin_J2R", 3, rng),
        spin_cone("spin_J2C", 4, rng),
        spin_cone("spin_J2H", 6, rng),
        spin_cone("spin_J2O", 10, rng),
        psd_cone("R", rng),
        psd_cone("C", rng),
        psd_cone("H", rng),
        h3o_cone(rng),
    ]
    menu_rows = []
    for cone in cones:
        oct_gate = cone.get("octonion_content_gate")
        menu_rows.append(
            {
                "cone": cone["cone"],
                "dim": cone["dimension"],
                "S_invariance": cone["gates"]["S_invariance"]["pass"],
                "DPI_verdict": cone["dpi_verdict"],
                "violations": cone["dpi_table"]["violation_count"],
                "max_increase": cone["dpi_table"]["max_increase"],
                "wrong_sigma_breaks": cone["controls"]["wrong_sigma"]["breaks"],
                "octonion_content": None if oct_gate is None else oct_gate["pass"],
                "honest_cell_pass": cone["honest_cell_pass"] and (oct_gate is None or (oct_gate["pass"] and oct_gate["corrupted_table_breaks"])),
            }
        )
    theorem_zero_cells_ok = all(row["violations"] == 0 for row in menu_rows if row["cone"] != "H3O_exceptional")
    o_controls_ok = all(
        (cone.get("octonion_content_gate") is None)
        or (cone["octonion_content_gate"]["pass"] and cone["octonion_content_gate"]["corrupted_table_breaks"])
        for cone in cones
    )
    complex_regression = next(cone["known_value_regression"] for cone in cones if cone["cone"] == "PSD_Herm3C")
    all_pass = bool(
        all(row["honest_cell_pass"] for row in menu_rows)
        and theorem_zero_cells_ok
        and o_controls_ok
        and complex_regression["pass"]
    )
    pawl_change = [
        row for row in menu_rows if row["violations"] > 0 or (row["cone"] == "H3O_exceptional" and row["DPI_verdict"] == "dpi_violated_on_grid")
    ]
    return {
        "schema": "codex_ratchet.symmetric_cone_menu_census_result.v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "sim_execution_kind": "classical",
        "sim_class": "symmetric_cone_menu_comparative_dpi_probe",
        "seed": SEED,
        "rng": "numpy.default_rng(0)",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "claim_ceiling": "Scratch diagnostic finite-grid comparison over the named symmetric-cone menu; no theorem, no canonical admission, no bridge/Axis/manifold claim.",
        "map": {
            "formula": "Phi(x)=alpha*x+(1-alpha)*(eta*Pinch(x)+(1-eta)*tr(x)*sigma)",
            "alpha": ALPHA,
            "eta_pinch": ETA_PINCH,
            "linear": True,
            "state_dependent_normalization": False,
            "computed_fixed_point": "sigma in the standard Jordan frame for each cone",
        },
        "banned_modes_guard": {
            "state_dependent_normalization_in_phi": False,
            "conditioned_single_branch_map": False,
            "diagonal_shadow_relative_entropy_for_main_claim": False,
            "hardcoded_dpi_verdict": False,
            "promotion_claim": False,
        },
        "comparative_menu_table": menu_rows,
        "cones": cones,
        "controls": {
            "wrong_sigma_breaks_all_cones": all(row["wrong_sigma_breaks"] for row in menu_rows),
            "corrupted_octonion_table_breaks_o_cells_upstream": o_controls_ok,
            "complex_psd_numpy_umegaki_regression": complex_regression,
        },
        "comparative_verdict": {
            "theorem_expected_zero_cells_ok": theorem_zero_cells_ok,
            "H3O_question_cell": next(row for row in menu_rows if row["cone"] == "H3O_exceptional"),
            "sampled_pawl_change_cells": pawl_change,
            "summary": "No sampled pawl-structure change in this finite grid." if not pawl_change else "Sampled DPI increase found in the listed cell(s); see violations.",
        },
        "all_pass": all_pass,
        "promotion_status": "diagnostic_only",
        "eligible_consumers": [],
        "blocked_consumers": [
            "formal symmetric-cone DPI theorem",
            "canonical-by-process promotion",
            "Axis0, bridge, manifold, or physics admission",
        ],
    }


def print_summary(result: dict[str, Any]) -> None:
    print("SYMMETRIC_CONE_MENU_CENSUS_SIM")
    print(f"seed={SEED} classification={CLASSIFICATION} promotion_allowed={PROMOTION_ALLOWED}")
    print("linear v3 map: Phi=alpha*id+(1-alpha)*(eta*Pinch+(1-eta)*trace-reset-to-sigma)")
    print(f"alpha={ALPHA} eta_pinch={ETA_PINCH} superposition_tol={SUPERPOSITION_TOL:.1e}")
    print("")
    print("MENU TABLE")
    print("cone              dim  S-inv  DPI verdict           viol  max_increase       wrong-sigma  O-content")
    for row in result["comparative_menu_table"]:
        octo = "-" if row["octonion_content"] is None else str(row["octonion_content"])
        print(
            f"{row['cone']:<17} {row['dim']:>3}  {str(row['S_invariance']):<5}  "
            f"{row['DPI_verdict']:<20} {row['violations']:>4}  {row['max_increase']:> .6e}  "
            f"{str(row['wrong_sigma_breaks']):<11} {octo}"
        )
    print("")
    print("CONTROLS")
    print(f"wrong_sigma_breaks_all_cones={result['controls']['wrong_sigma_breaks_all_cones']}")
    print(f"corrupted_octonion_table_breaks_o_cells_upstream={result['controls']['corrupted_octonion_table_breaks_o_cells_upstream']}")
    reg = result["controls"]["complex_psd_numpy_umegaki_regression"]
    print(f"Herm3(C) numpy/logm Umegaki regression pass={reg['pass']} max_abs_diff={reg['max_abs_diff']:.3e}")
    verdict = result["comparative_verdict"]
    print("")
    print("COMPARATIVE VERDICT")
    print(f"theorem_expected_zero_cells_ok={verdict['theorem_expected_zero_cells_ok']}")
    print(f"H3O_question_cell={verdict['H3O_question_cell']}")
    print(verdict["summary"])
    print(f"all_pass={result['all_pass']}")
    print(f"wrote: {RESULT_PATH}")


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(clean(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print_summary(result)
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
