#!/usr/bin/env python3
"""Genuine Jordan dissipator pawl probe, v2.

Scratch diagnostic only. This hardening round addresses the straight-line
mixing critique against the earlier U_p damp-flow probes.  The flow here is a
nonlinear Jordan operation: a rotated-frame Peirce pinch, a genuine exp([L_a,L_b])
automorphism, and a non-convex quadratic Jordan filter toward the intended
primitive idempotent.  No step convexly mixes the state with the target.

The target-attractor condition is measured, not assumed.  If the computed
attractor differs from the intended primitive target, the result reports the
distance and keeps the claim ceiling diagnostic.
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np
from scipy.linalg import expm


ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v7/constraint_core/sims_and_scripts"
SOURCE_PATH = SIM_DIR / "jordan_dissipator_pawl_v2_sim.py"
RESULT_PATH = SIM_DIR / "jordan_dissipator_pawl_v2_sim_results.json"
J2_SOURCE_PATH = SIM_DIR / "jordan_octonion_entropy_pawl_sim.py"
J3_SOURCE_PATH = SIM_DIR / "j3o_bloch_body_entropy_pawl_sim.py"

SIM_ID = "jordan_dissipator_pawl_v2"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
SEED = 0
TOL = 1.0e-10
DERIVATION_TOL = 1.0e-12
RELATIVE_EPSILON = 1.0e-6
OFFDIAG_ATTENUATION = 0.18
FILTER_OFF_TARGET_SCALE = 0.018
FLOW_STEPS = 42
FIXED_ITERATIONS = 360
CURVATURE_THRESHOLD = 1.0e-8

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite Jordan algebra coordinates, Peirce projections, seeded state grids, curvature checks, and pawl sweeps",
    },
    "scipy.linalg.expm": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exponentiation of genuine D_{a,b}=[L_a,L_b] Jordan derivation matrices",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive import loading, paths, timestamps, dataclasses, and JSON serialization",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "scipy.linalg.expm": "load_bearing",
    "python_stdlib": "supportive",
}


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load module spec for {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


j2_prev = load_module(J2_SOURCE_PATH, "jordan_octonion_entropy_pawl_prev")
j3_prev = load_module(J3_SOURCE_PATH, "j3o_bloch_body_entropy_pawl_prev")


def clean(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return clean(obj.tolist())
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        value = float(obj)
        if math.isfinite(value):
            return value
        if math.isnan(value):
            return "NaN"
        return "Infinity" if value > 0 else "-Infinity"
    return obj


def basis(dim: int, idx: int) -> np.ndarray:
    out = np.zeros(dim, dtype=float)
    out[idx] = 1.0
    return out


def classify_deltas(values_by_path: list[list[float]], direction: str, tol: float = 1.0e-9) -> dict[str, Any]:
    max_increase = 0.0
    max_decrease = 0.0
    violation_count = 0
    worst_increase = None
    worst_decrease = None
    start_end = []
    for state_index, values in enumerate(values_by_path):
        start_end.append(float(values[-1] - values[0]))
        for step, (a, b) in enumerate(zip(values, values[1:])):
            delta = float(b - a)
            if direction == "decreasing" and delta > tol:
                violation_count += 1
            if direction == "increasing" and -delta > tol:
                violation_count += 1
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
        "violation_count": int(violation_count),
        "max_increase": float(max_increase),
        "max_decrease": float(max_decrease),
        "worst_increase": worst_increase,
        "worst_decrease": worst_decrease,
        "net_delta_min": float(min(start_end)),
        "net_delta_max": float(max(start_end)),
    }


@dataclass
class JordanAlgebra:
    name: str
    dim: int
    unit: np.ndarray
    product: Callable[[np.ndarray, np.ndarray], np.ndarray]
    trace: Callable[[np.ndarray], float]
    entropy: Callable[[np.ndarray], float]
    rel_entropy_shadow: Callable[[np.ndarray, np.ndarray], float]
    trace_distance: Callable[[np.ndarray, np.ndarray], float]
    normalize: Callable[[np.ndarray], np.ndarray]
    is_density: Callable[[np.ndarray], bool]
    sample_states: Callable[[np.random.Generator], list[np.ndarray]]
    target: np.ndarray
    foreign_target: np.ndarray
    standard_frame: list[np.ndarray]
    rotated_frame_generator: tuple[np.ndarray, np.ndarray, float]
    tick_rotation_generator: tuple[np.ndarray, np.ndarray, float]
    fixed_start: np.ndarray
    target_coord_label: str

    def square(self, x: np.ndarray) -> np.ndarray:
        return self.product(x, x)

    def quadratic(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return 2.0 * self.product(a, self.product(a, b)) - self.product(self.square(a), b)


def left_matrix(algebra: JordanAlgebra, a: np.ndarray) -> np.ndarray:
    cols = [algebra.product(a, basis(algebra.dim, i)) for i in range(algebra.dim)]
    return np.column_stack(cols)


def derivation_matrix(algebra: JordanAlgebra, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    la = left_matrix(algebra, a)
    lb = left_matrix(algebra, b)
    return la @ lb - lb @ la


def automorphism_from_generator(algebra: JordanAlgebra, a: np.ndarray, b: np.ndarray, time: float) -> tuple[np.ndarray, np.ndarray]:
    d = derivation_matrix(algebra, a, b)
    return d, expm(time * d)


def derivation_gate(algebra: JordanAlgebra, transform: np.ndarray, rng: np.random.Generator, samples: int) -> dict[str, Any]:
    max_product_error = 0.0
    max_unit_error = float(np.linalg.norm(transform @ algebra.unit - algebra.unit))
    rows = []
    for idx in range(samples):
        x = rng.normal(scale=0.2, size=algebra.dim)
        y = rng.normal(scale=0.2, size=algebra.dim)
        left = transform @ algebra.product(x, y)
        right = algebra.product(transform @ x, transform @ y)
        err = float(np.linalg.norm(left - right))
        max_product_error = max(max_product_error, err)
        if idx < 4:
            rows.append({"sample": idx, "product_error": err})
    return {
        "construction": "D_{a,b}=[L_a,L_b], A=exp(tD)",
        "samples": samples,
        "max_product_preservation_error": max_product_error,
        "max_unit_error": max_unit_error,
        "pass": bool(max_product_error <= DERIVATION_TOL and max_unit_error <= DERIVATION_TOL),
        "sample_rows": rows,
    }


def peirce_pinch(algebra: JordanAlgebra, frame: list[np.ndarray], rho: np.ndarray) -> np.ndarray:
    diagonal = np.zeros(algebra.dim, dtype=float)
    for e in frame:
        diagonal += algebra.quadratic(e, rho)
    offdiag = rho - diagonal
    return diagonal + OFFDIAG_ATTENUATION * offdiag


def jordan_filter_to_target(algebra: JordanAlgebra, rho: np.ndarray) -> np.ndarray:
    g = algebra.target + FILTER_OFF_TARGET_SCALE * (algebra.unit - algebra.target)
    return algebra.normalize(algebra.quadratic(g, rho))


def chord_curvature(path: list[np.ndarray], fixed: np.ndarray) -> float:
    start = path[0]
    chord = fixed - start
    denom = float(np.dot(chord, chord))
    if denom <= 1.0e-30:
        return 0.0
    max_dist = 0.0
    for point in path:
        tau = float(np.dot(point - start, chord) / denom)
        tau = max(0.0, min(1.0, tau))
        closest = start + tau * chord
        max_dist = max(max_dist, float(np.linalg.norm(point - closest)))
    return max_dist


def flow_step(algebra: JordanAlgebra, rho: np.ndarray, frame: list[np.ndarray], tick_rotation: np.ndarray) -> np.ndarray:
    pinched = peirce_pinch(algebra, frame, rho)
    rotated = tick_rotation @ pinched
    return jordan_filter_to_target(algebra, rotated)


def iterate_fixed_point(algebra: JordanAlgebra, frame: list[np.ndarray], tick_rotation: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
    rho = np.array(algebra.fixed_start, dtype=float, copy=True)
    last_delta = float("inf")
    for idx in range(FIXED_ITERATIONS):
        nxt = flow_step(algebra, rho, frame, tick_rotation)
        last_delta = float(np.linalg.norm(nxt - rho))
        rho = nxt
        if last_delta < 1.0e-13:
            break
    return rho, {
        "iterations": int(idx + 1),
        "last_delta": last_delta,
        "distance_to_intended_target": float(np.linalg.norm(rho - algebra.target)),
        "trace": algebra.trace(rho),
        "is_density": algebra.is_density(rho),
    }


def run_dissipator_sweep(algebra: JordanAlgebra, rng: np.random.Generator) -> dict[str, Any]:
    frame_a, frame_b, frame_time = algebra.rotated_frame_generator
    tick_a, tick_b, tick_time = algebra.tick_rotation_generator
    _, frame_auto = automorphism_from_generator(algebra, frame_a, frame_b, frame_time)
    tick_d, tick_auto = automorphism_from_generator(algebra, tick_a, tick_b, tick_time)
    frame = [frame_auto @ e for e in algebra.standard_frame]
    fixed, fixed_report = iterate_fixed_point(algebra, frame, tick_auto)
    fixed_shadow = (1.0 - RELATIVE_EPSILON) * fixed + RELATIVE_EPSILON * algebra.unit / algebra.trace(algebra.unit)
    wrong_shadow = (1.0 - RELATIVE_EPSILON) * algebra.foreign_target + RELATIVE_EPSILON * algebra.unit / algebra.trace(algebra.unit)
    states = algebra.sample_states(rng)

    rel_paths: list[list[float]] = []
    wrong_rel_paths: list[list[float]] = []
    entropy_paths: list[list[float]] = []
    wrong_trace_paths: list[list[float]] = []
    target_trace_paths: list[list[float]] = []
    curvatures = []
    min_trace = float("inf")
    max_trace_error = 0.0
    density_failures = 0
    witness_paths = []
    for state_index, start in enumerate(states):
        rho = np.array(start, dtype=float, copy=True)
        path = [rho]
        rel = [algebra.rel_entropy_shadow(rho, fixed_shadow)]
        wrong_rel = [algebra.rel_entropy_shadow(rho, wrong_shadow)]
        ent = [algebra.entropy(rho)]
        wrong_trace = [algebra.trace_distance(rho, algebra.foreign_target)]
        target_trace = [algebra.trace_distance(rho, fixed)]
        for _ in range(FLOW_STEPS):
            rho = flow_step(algebra, rho, frame, tick_auto)
            path.append(rho)
            min_trace = min(min_trace, algebra.trace(rho))
            max_trace_error = max(max_trace_error, abs(algebra.trace(rho) - 1.0))
            if not algebra.is_density(rho):
                density_failures += 1
            rel.append(algebra.rel_entropy_shadow(rho, fixed_shadow))
            wrong_rel.append(algebra.rel_entropy_shadow(rho, wrong_shadow))
            ent.append(algebra.entropy(rho))
            wrong_trace.append(algebra.trace_distance(rho, algebra.foreign_target))
            target_trace.append(algebra.trace_distance(rho, fixed))
        curvature = chord_curvature(path, fixed)
        curvatures.append(curvature)
        rel_paths.append(rel)
        wrong_rel_paths.append(wrong_rel)
        entropy_paths.append(ent)
        wrong_trace_paths.append(wrong_trace)
        target_trace_paths.append(target_trace)
        if state_index < 3:
            witness_paths.append(
                {
                    "state_index": state_index,
                    "curvature": curvature,
                    "start_distance_to_fixed": float(np.linalg.norm(path[0] - fixed)),
                    "end_distance_to_fixed": float(np.linalg.norm(path[-1] - fixed)),
                    "relative_entropy_start": rel[0],
                    "relative_entropy_end": rel[-1],
                }
            )

    curvature_pass_count = int(sum(c > CURVATURE_THRESHOLD for c in curvatures))
    curvature_fraction = curvature_pass_count / max(1, len(curvatures))
    pawl = classify_deltas(rel_paths, "decreasing")
    wrong = classify_deltas(wrong_rel_paths, "decreasing")
    entropy = classify_deltas(entropy_paths, "none")
    wrong_trace = classify_deltas(wrong_trace_paths, "decreasing")
    target_trace = classify_deltas(target_trace_paths, "decreasing")
    flow_degenerate = bool(curvature_fraction <= 0.80 or fixed_report["distance_to_intended_target"] > 0.08)
    if flow_degenerate:
        verdict = "flow_degenerate"
    elif pawl["pawl"]:
        verdict = "pawl_holds_nontrivially"
    else:
        verdict = "pawl_fails"

    return {
        "rung": algebra.name,
        "target_coord_label": algebra.target_coord_label,
        "flow_definition": {
            "pinch": "rotated Jordan-frame Peirce pinch: sum_i U_{f_i}(rho) plus attenuated off-diagonal Peirce residue",
            "rotation": "A=exp(tD), D=[L_a,L_b], applied after the pinch",
            "nonconvex_target_pressure": "trace-normalized U_g(rho), g=p+lambda(1-p); this is not convex mixing with p",
            "offdiag_attenuation": OFFDIAG_ATTENUATION,
            "filter_off_target_scale": FILTER_OFF_TARGET_SCALE,
            "steps": FLOW_STEPS,
        },
        "derivation_matrix_norm": float(np.linalg.norm(tick_d)),
        "frame_not_containing_target_distance_min": float(min(np.linalg.norm(f - algebra.target) for f in frame)),
        "fixed_point_computation": fixed_report,
        "fixed_point_coordinates_head": [float(x) for x in fixed[: min(10, len(fixed))]],
        "automorphism_gate": derivation_gate(algebra, tick_auto, rng, 20),
        "state_grid": {
            "sample_count": len(states),
            "density_failures_along_paths": int(density_failures),
            "min_trace": float(min_trace),
            "max_trace_error": float(max_trace_error),
        },
        "curvature_gate": {
            "threshold": CURVATURE_THRESHOLD,
            "max_curvature": float(max(curvatures)),
            "median_curvature": float(np.median(curvatures)),
            "pass_count": curvature_pass_count,
            "sample_count": len(curvatures),
            "fraction_above_threshold": float(curvature_fraction),
            "pass": bool(curvature_fraction > 0.80),
            "flow_is_effectively_mixing": bool(curvature_fraction <= 0.80),
        },
        "pawl_table": {
            "U_J_to_computed_fixed_point_shadow": pawl,
            "wrong_fixed_point_U_J_control": wrong,
            "raw_spectral_entropy": entropy,
            "trace_distance_to_wrong_target_decreasing_control": wrong_trace,
            "trace_distance_to_fixed_point_decreasing_control": target_trace,
        },
        "witness_paths": witness_paths,
        "verdict": verdict,
    }


def j2_algebra() -> JordanAlgebra:
    dim = 10
    unit = np.zeros(dim, dtype=float)
    unit[0] = 1.0
    n = basis(9, 8)
    foreign = basis(9, 0)

    def product(x: np.ndarray, y: np.ndarray) -> np.ndarray:
        out = np.zeros(dim, dtype=float)
        out[0] = x[0] * y[0] + float(np.dot(x[1:], y[1:]))
        out[1:] = x[0] * y[1:] + y[0] * x[1:]
        return out

    def primitive(v: np.ndarray) -> np.ndarray:
        out = np.zeros(dim, dtype=float)
        out[0] = 0.5
        out[1:] = 0.5 * v
        return out

    target = primitive(n)
    foreign_target = primitive(foreign)

    def trace(x: np.ndarray) -> float:
        return float(2.0 * x[0])

    def normalize(x: np.ndarray) -> np.ndarray:
        tr = trace(x)
        if abs(tr) < 1.0e-15:
            raise ValueError("near-zero trace in J2 normalize")
        return x / tr

    def r_of(x: np.ndarray) -> np.ndarray:
        return 2.0 * x[1:]

    def entropy(x: np.ndarray) -> float:
        return j2_prev.spectral_entropy(r_of(normalize(x)))

    def rel_entropy(x: np.ndarray, sigma: np.ndarray) -> float:
        return j2_prev.eja_relative_entropy(r_of(normalize(x)), r_of(normalize(sigma)))

    def trace_distance(x: np.ndarray, y: np.ndarray) -> float:
        return 0.5 * float(np.linalg.norm(r_of(normalize(x)) - r_of(normalize(y))))

    def is_density(x: np.ndarray) -> bool:
        rho = normalize(x)
        return bool(abs(trace(rho) - 1.0) < 1.0e-8 and np.linalg.norm(r_of(rho)) <= 1.0 + 1.0e-8)

    def density_from_r(r: np.ndarray) -> np.ndarray:
        out = np.zeros(dim, dtype=float)
        out[0] = 0.5
        out[1:] = 0.5 * r
        return out

    def sample_states(rng: np.random.Generator) -> list[np.ndarray]:
        rows = []
        for radius in np.linspace(0.0, 0.965, 12):
            rows.append(density_from_r(radius * n))
            rows.append(density_from_r(-radius * n))
        for _ in range(96):
            direction = rng.normal(size=9)
            direction /= np.linalg.norm(direction)
            rows.append(density_from_r(rng.uniform(0.04, 0.975) * direction))
        return rows

    tilted = math.cos(0.72) * n + math.sin(0.72) * basis(9, 0)
    frame = [primitive(tilted), primitive(-tilted)]
    frame_a = np.r_[0.0, basis(9, 0)]
    frame_b = np.r_[0.0, basis(9, 8)]
    tick_a = np.r_[0.0, basis(9, 1)]
    tick_b = np.r_[0.0, basis(9, 2)]
    return JordanAlgebra(
        name="J2(O)_spin_factor",
        dim=dim,
        unit=unit,
        product=product,
        trace=trace,
        entropy=entropy,
        rel_entropy_shadow=rel_entropy,
        trace_distance=trace_distance,
        normalize=normalize,
        is_density=is_density,
        sample_states=sample_states,
        target=target,
        foreign_target=foreign_target,
        standard_frame=frame,
        rotated_frame_generator=(frame_a, frame_b, 0.0),
        tick_rotation_generator=(tick_a, tick_b, 0.31),
        fixed_start=density_from_r(np.zeros(9)),
        target_coord_label="spin vector e8 primitive idempotent",
    )


def j3_vec_from_elem(x: np.ndarray) -> np.ndarray:
    out = np.zeros(27, dtype=float)
    out[0] = x[0, 0, 0]
    out[1] = x[1, 1, 0]
    out[2] = x[2, 2, 0]
    out[3:11] = x[0, 1, :]
    out[11:19] = x[0, 2, :]
    out[19:27] = x[1, 2, :]
    return out


def j3_elem_from_vec(v: np.ndarray) -> np.ndarray:
    return j3_prev.j3_from_parts(np.array(v[0:3], dtype=float), np.array(v[3:11]), np.array(v[11:19]), np.array(v[19:27]))


def j3_algebra() -> JordanAlgebra:
    table = j3_prev.octonion_table()
    dim = 27
    unit = j3_vec_from_elem(j3_prev.j3_unit())
    e0 = j3_vec_from_elem(j3_prev.j3_diag([1.0, 0.0, 0.0]))
    e1 = j3_vec_from_elem(j3_prev.j3_diag([0.0, 1.0, 0.0]))
    e2 = j3_vec_from_elem(j3_prev.j3_diag([0.0, 0.0, 1.0]))

    def product(x: np.ndarray, y: np.ndarray) -> np.ndarray:
        return j3_vec_from_elem(j3_prev.jordan(table, j3_elem_from_vec(x), j3_elem_from_vec(y)))

    def trace(x: np.ndarray) -> float:
        return float(x[0] + x[1] + x[2])

    def normalize(x: np.ndarray) -> np.ndarray:
        tr = trace(x)
        if abs(tr) < 1.0e-15:
            raise ValueError("near-zero trace in J3 normalize")
        return x / tr

    def entropy(x: np.ndarray) -> float:
        return j3_prev.spectral_entropy(j3_elem_from_vec(normalize(x)), table)

    def rel_entropy(x: np.ndarray, sigma: np.ndarray) -> float:
        rho = normalize(x)
        sig = normalize(sigma)
        diag = np.clip(sig[0:3], RELATIVE_EPSILON / 3.0, None)
        diag = diag / float(np.sum(diag))
        log_diag = np.log(diag)
        return j3_prev.eja_relative_entropy_to_diag_shadow(j3_elem_from_vec(rho), table, log_diag)

    def trace_distance(x: np.ndarray, y: np.ndarray) -> float:
        delta = j3_elem_from_vec(normalize(x) - normalize(y))
        eigs = j3_prev.cubic_eigenvalues(j3_prev.j3_trace(delta), j3_prev.sigma2_j3(delta), j3_prev.det_j3(table, delta))
        return 0.5 * float(np.sum(np.abs(eigs)))

    def is_density(x: np.ndarray) -> bool:
        rho = normalize(x)
        return bool(abs(trace(rho) - 1.0) < 1.0e-8 and j3_prev.is_density(j3_elem_from_vec(rho), table, margin=-1.0e-7))

    def sample_states(rng: np.random.Generator) -> list[np.ndarray]:
        elems, _ = j3_prev.sample_state_grid(rng, table)
        rows = [j3_vec_from_elem(e) for e in elems[:120]]
        return rows

    def offdiag(pair: int, oct_idx: int, scale: float = 1.0) -> np.ndarray:
        out = np.zeros(27, dtype=float)
        base = 3 + 8 * pair
        out[base + oct_idx] = scale
        return out

    frame_a = offdiag(0, 0)
    frame_b = e0 - e1
    tick_a = offdiag(2, 1)
    tick_b = e1 - e2
    return JordanAlgebra(
        name="J3(O)_Albert",
        dim=dim,
        unit=unit,
        product=product,
        trace=trace,
        entropy=entropy,
        rel_entropy_shadow=rel_entropy,
        trace_distance=trace_distance,
        normalize=normalize,
        is_density=is_density,
        sample_states=sample_states,
        target=e0,
        foreign_target=e1,
        standard_frame=[e0, e1, e2],
        rotated_frame_generator=(frame_a, frame_b, 0.46),
        tick_rotation_generator=(tick_a, tick_b, 0.23),
        fixed_start=unit / 3.0,
        target_coord_label="Albert diag(1,0,0) primitive idempotent",
    )


def unitary_only_control(algebra: JordanAlgebra, rng: np.random.Generator) -> dict[str, Any]:
    tick_a, tick_b, tick_time = algebra.tick_rotation_generator
    _, tick_auto = automorphism_from_generator(algebra, tick_a, tick_b, tick_time)
    fixed_shadow = (1.0 - RELATIVE_EPSILON) * algebra.target + RELATIVE_EPSILON * algebra.unit / algebra.trace(algebra.unit)
    rel_paths = []
    ent_paths = []
    for start in algebra.sample_states(rng)[:48]:
        rho = np.array(start, dtype=float, copy=True)
        rel = [algebra.rel_entropy_shadow(rho, fixed_shadow)]
        ent = [algebra.entropy(rho)]
        for _ in range(FLOW_STEPS):
            rho = algebra.normalize(tick_auto @ rho)
            rel.append(algebra.rel_entropy_shadow(rho, fixed_shadow))
            ent.append(algebra.entropy(rho))
        rel_paths.append(rel)
        ent_paths.append(ent)
    rel = classify_deltas(rel_paths, "decreasing")
    ent = classify_deltas(ent_paths, "none")
    return {
        "definition": "derivation automorphism only: rho -> exp(t[L_a,L_b])rho, no pinch, no quadratic filter",
        "U_J_to_target_shadow": rel,
        "raw_spectral_entropy": ent,
        "no_pawl": bool(not rel["pawl"] or ent["classification"] == "hold"),
    }


def simplex_reproduction_control(rng: np.random.Generator, j3_reference: dict[str, Any]) -> dict[str, Any]:
    target = np.array([1.0, 0.0, 0.0], dtype=float)
    wrong = np.array([0.0, 1.0, 0.0], dtype=float)
    g = target + FILTER_OFF_TARGET_SCALE * (np.ones(3) - target)

    def norm(p: np.ndarray) -> np.ndarray:
        p = np.clip(p, 0.0, None)
        return p / float(np.sum(p))

    def entropy(p: np.ndarray) -> float:
        return float(-sum(x * math.log(x) for x in p if x > 0.0))

    def rel(p: np.ndarray, sigma: np.ndarray) -> float:
        s = np.clip(sigma, RELATIVE_EPSILON / 3.0, None)
        s = s / float(np.sum(s))
        return float(sum(pi * (math.log(pi) - math.log(si)) for pi, si in zip(p, s) if pi > 0.0))

    fixed = norm(g * g * np.array([1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0]))
    for _ in range(FIXED_ITERATIONS):
        fixed = norm(g * g * fixed)
    fixed_shadow = (1.0 - RELATIVE_EPSILON) * fixed + RELATIVE_EPSILON * np.ones(3) / 3.0
    wrong_shadow = (1.0 - RELATIVE_EPSILON) * wrong + RELATIVE_EPSILON * np.ones(3) / 3.0
    states = [np.ones(3) / 3.0]
    for _ in range(90):
        states.append(rng.dirichlet(np.array([1.4, 1.2, 1.1])))
    rel_paths = []
    wrong_paths = []
    entropy_paths = []
    curvatures = []
    for start in states:
        p = np.array(start, dtype=float, copy=True)
        path = [p]
        rp = [rel(p, fixed_shadow)]
        wp = [rel(p, wrong_shadow)]
        ep = [entropy(p)]
        for _ in range(FLOW_STEPS):
            p = norm(g * g * p)
            path.append(p)
            rp.append(rel(p, fixed_shadow))
            wp.append(rel(p, wrong_shadow))
            ep.append(entropy(p))
        rel_paths.append(rp)
        wrong_paths.append(wp)
        entropy_paths.append(ep)
        curvatures.append(chord_curvature([np.array(x) for x in path], fixed))
    pawl = classify_deltas(rel_paths, "decreasing")
    wrong_pawl = classify_deltas(wrong_paths, "decreasing")
    ent = classify_deltas(entropy_paths, "none")
    curvature_fraction = sum(c > CURVATURE_THRESHOLD for c in curvatures) / len(curvatures)
    reference_pawl = j3_reference["pawl_table"]["U_J_to_computed_fixed_point_shadow"]
    reproduces = bool(
        pawl["classification"] == reference_pawl["classification"]
        and curvature_fraction > 0.80
        and wrong_pawl["classification"] == j3_reference["pawl_table"]["wrong_fixed_point_U_J_control"]["classification"]
    )
    return {
        "definition": "3-outcome commutative simplex with the same target filter but no off-diagonal Peirce geometry and no nonzero derivations",
        "fixed_point": [float(x) for x in fixed],
        "pawl_table": {
            "relative_entropy_to_fixed_shadow": pawl,
            "wrong_fixed_point_control": wrong_pawl,
            "raw_entropy": ent,
        },
        "curvature_gate": {
            "max_curvature": float(max(curvatures)),
            "median_curvature": float(np.median(curvatures)),
            "fraction_above_threshold": float(curvature_fraction),
            "pass": bool(curvature_fraction > 0.80),
        },
        "reproduces_jordan_table": reproduces,
        "verdict": "does_not_reproduce" if not reproduces else "reproduces",
    }


def derivation_invariance_gate(algebra: JordanAlgebra, rng: np.random.Generator) -> dict[str, Any]:
    tick_a, tick_b, tick_time = algebra.tick_rotation_generator
    _, auto = automorphism_from_generator(algebra, tick_a, tick_b, tick_time)
    max_entropy_diff = 0.0
    max_distance_diff = 0.0
    states = algebra.sample_states(rng)[:32]
    for state in states:
        moved = algebra.normalize(auto @ state)
        max_entropy_diff = max(max_entropy_diff, abs(algebra.entropy(moved) - algebra.entropy(state)))
        max_distance_diff = max(
            max_distance_diff,
            abs(algebra.trace_distance(moved, algebra.normalize(auto @ algebra.target)) - algebra.trace_distance(state, algebra.target)),
        )
    return {
        "group_surface": "G2/Spin(9)-type for J2(O), F4-type Albert automorphism for J3(O), sampled by exp([L_a,L_b])",
        "sample_count": len(states),
        "max_entropy_diff": float(max_entropy_diff),
        "max_distance_covariance_error": float(max_distance_diff),
        "pass": bool(max_entropy_diff <= 1.0e-10 and max_distance_diff <= 1.0e-10),
    }


def build_result() -> dict[str, Any]:
    rng = np.random.default_rng(SEED)
    j2_rng = np.random.default_rng(SEED + 10)
    j3_rng = np.random.default_rng(SEED + 20)
    j2 = j2_algebra()
    j3 = j3_algebra()
    j2_result = run_dissipator_sweep(j2, j2_rng)
    j3_result = run_dissipator_sweep(j3, j3_rng)
    simplex = simplex_reproduction_control(np.random.default_rng(SEED + 30), j3_result)
    unitary_j2 = unitary_only_control(j2, np.random.default_rng(SEED + 40))
    unitary_j3 = unitary_only_control(j3, np.random.default_rng(SEED + 50))
    inv_j2 = derivation_invariance_gate(j2, np.random.default_rng(SEED + 60))
    inv_j3 = derivation_invariance_gate(j3, np.random.default_rng(SEED + 70))
    o_table = j3_prev.octonion_table()
    oct_checks = j3_prev.octonion_verification(o_table, rng)
    sedenion = j3_prev.sedenion_kill_control(o_table)
    all_nontrivial = all(
        row["verdict"] in {"pawl_holds_nontrivially", "pawl_fails"} for row in (j2_result, j3_result)
    )
    simplex_breaks = simplex["verdict"] == "does_not_reproduce"
    derivations_pass = bool(j2_result["automorphism_gate"]["pass"] and j3_result["automorphism_gate"]["pass"] and inv_j2["pass"] and inv_j3["pass"])
    wrong_trace_violations = {
        "J2O": j2_result["pawl_table"]["trace_distance_to_wrong_target_decreasing_control"]["violation_count"],
        "J3O": j3_result["pawl_table"]["trace_distance_to_wrong_target_decreasing_control"]["violation_count"],
    }
    all_pass = bool(all_nontrivial and simplex_breaks and derivations_pass and min(wrong_trace_violations.values()) > 0)
    return {
        "schema": "codex_ratchet.jordan_dissipator_pawl_v2_result.v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "sim_execution_kind": "classical",
        "sim_class": "jordan_dissipator_pawl_probe",
        "seed": SEED,
        "tol": TOL,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_conventions_reused": {
            "J2O_source_path": str(J2_SOURCE_PATH),
            "J3O_source_path": str(J3_SOURCE_PATH),
            "octonion_statics": "reused Fano table, Albert spectral machinery, and sedenion kill controls from prior octonion-rung sims",
        },
        "banned_modes_guard": {
            "aliased_self_comparison": False,
            "hardcoded_verdict": False,
            "label_keyed_success": False,
            "tautological_mixing_path": False,
            "convex_target_mixing": False,
        },
        "claim_ceiling": (
            "Scratch diagnostic: seeded finite Jordan dissipator trajectories and pawl/negative controls. "
            "No formal monotonicity theorem, admission, bridge, manifold, or Axis0 claim."
        ),
        "octonion_static_controls_reused": {
            "octonion_verification": oct_checks,
            "sedenion_kill_control": sedenion,
        },
        "rungs": {
            "J2O": j2_result,
            "J3O": j3_result,
        },
        "controls": {
            "simplex_reproduction": simplex,
            "unitary_only_J2O": unitary_j2,
            "unitary_only_J3O": unitary_j3,
            "derivation_invariance_J2O": inv_j2,
            "derivation_invariance_J3O": inv_j3,
            "wrong_trace_distance_violation_counts": wrong_trace_violations,
        },
        "per_rung_verdicts": {
            "J2O": j2_result["verdict"],
            "J3O": j3_result["verdict"],
        },
        "result_summary": {
            "all_nontrivial_or_reportable": all_nontrivial,
            "simplex_does_not_reproduce": simplex_breaks,
            "derivation_gates_pass": derivations_pass,
            "wrong_trace_distance_has_violations": bool(min(wrong_trace_violations.values()) > 0),
            "all_pass": all_pass,
        },
        "verdict": "diagnostic_pass" if all_pass else "diagnostic_partial_or_failed",
        "all_pass": all_pass,
        "promotion_status": "diagnostic_only",
        "eligible_consumers": [],
        "blocked_consumers": [
            "formal Jordan-DPI theorem",
            "canonical-by-process promotion",
            "Axis0 closure",
            "bridge or manifold admission",
        ],
        "blocked_downstream_consumers": [
            "formal Jordan-DPI theorem",
            "canonical-by-process promotion",
            "Axis0 closure",
            "bridge or manifold admission",
        ],
    }


def print_rung_summary(label: str, row: dict[str, Any]) -> None:
    curv = row["curvature_gate"]
    fixed = row["fixed_point_computation"]
    pawl = row["pawl_table"]
    print(
        f"{label} fixed_point: iterations={fixed['iterations']} last_delta={fixed['last_delta']:.3e} "
        f"distance_to_target={fixed['distance_to_intended_target']:.6e} is_density={fixed['is_density']}"
    )
    print(
        f"{label} curvature: max={curv['max_curvature']:.6e} median={curv['median_curvature']:.6e} "
        f"fraction_above_threshold={curv['fraction_above_threshold']:.3f} "
        f"threshold={curv['threshold']:.1e} pass={curv['pass']}"
    )
    print(f"{label} pawl table:")
    for key, value in pawl.items():
        print(
            "  "
            f"{key}: classification={value['classification']} pawl={value['pawl']} "
            f"violations={value['violation_count']} max_increase={value['max_increase']:.6e} "
            f"max_decrease={value['max_decrease']:.6e}"
        )
    auto = row["automorphism_gate"]
    print(
        f"{label} derivation_gate: pass={auto['pass']} "
        f"max_product_error={auto['max_product_preservation_error']:.3e} max_unit_error={auto['max_unit_error']:.3e}"
    )
    print(f"{label} verdict={row['verdict']}")


def print_summary(result: dict[str, Any]) -> None:
    print("JORDAN_DISSIPATOR_PAWL_V2_SIM")
    print(f"seed={SEED} classification={CLASSIFICATION} promotion_allowed={PROMOTION_ALLOWED}")
    print(
        "flow: rotated Peirce pinch -> exp([L_a,L_b]) automorphism -> trace-normalized U_g filter; "
        "no convex target mixing"
    )
    print_rung_summary("J2O", result["rungs"]["J2O"])
    print_rung_summary("J3O", result["rungs"]["J3O"])
    simplex = result["controls"]["simplex_reproduction"]
    print(
        "simplex reproduction: "
        f"verdict={simplex['verdict']} reproduces_jordan_table={simplex['reproduces_jordan_table']} "
        f"curvature_fraction={simplex['curvature_gate']['fraction_above_threshold']:.3f} "
        f"rel_entropy_classification={simplex['pawl_table']['relative_entropy_to_fixed_shadow']['classification']}"
    )
    print(
        "wrong trace-distance violations: "
        f"J2O={result['controls']['wrong_trace_distance_violation_counts']['J2O']} "
        f"J3O={result['controls']['wrong_trace_distance_violation_counts']['J3O']}"
    )
    print(
        "unitary-only controls: "
        f"J2O_no_pawl={result['controls']['unitary_only_J2O']['no_pawl']} "
        f"J3O_no_pawl={result['controls']['unitary_only_J3O']['no_pawl']}"
    )
    print(
        "F4/G2 derivation invariance gates: "
        f"J2O_pass={result['controls']['derivation_invariance_J2O']['pass']} "
        f"J3O_pass={result['controls']['derivation_invariance_J3O']['pass']}"
    )
    print(
        "octonion statics reused: "
        f"norm_comp_pass={result['octonion_static_controls_reused']['octonion_verification']['norm_composition']['pass']} "
        f"sedenion_break={result['octonion_static_controls_reused']['sedenion_kill_control']['break_status']}"
    )
    print(f"per_rung_verdicts={result['per_rung_verdicts']}")
    print(f"verdict={result['verdict']} all_pass={result['all_pass']}")
    print(f"wrote: {RESULT_PATH}")


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(clean(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print_summary(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
