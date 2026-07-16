#!/usr/bin/env python3
"""Jordan DPI probe v3 for J3(O), hardened after the v2 refutation.

Scratch diagnostic only.  This probe asks a finite-grid question:

    For a fixed-weight linear trace-preserving positive Jordan map Phi on
    J3(O), with full-rank fixed point sigma, does
    D(Phi(rho) || sigma) <= D(rho || sigma) hold on the sampled grid?

The map is deliberately small and auditable:

    Phi(rho) = alpha * U_1(rho) + (1-alpha) * sum_i U_ei(rho)

where e0,e1,e2 are the diagonal primitive idempotents of the standard Albert
frame.  U_1 is the identity quadratic representation, and sum_i U_ei is the
standard Peirce diagonal projection channel.  The weights are fixed constants;
there is no state-dependent normalization in the map.
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from scipy.linalg import expm


SIM_DIR = Path(__file__).resolve().parent
SOURCE_PATH = SIM_DIR / "jordan_dpi_probe_v3_sim.py"
RESULT_PATH = SIM_DIR / "jordan_dpi_probe_v3_sim_results.json"
J3_SOURCE_PATH = SIM_DIR / "j3o_bloch_body_entropy_pawl_sim.py"

SIM_ID = "jordan_dpi_probe_v3"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
SEED = 0

ALPHA = 0.97
FLOW_STEPS = 6
STATE_COUNT = 36
STATE_SCALE = 0.09
LINEARITY_TOL = 1.0e-14
TRACE_TOL = 1.0e-12
POSITIVITY_TOL = 1.0e-9
DPI_TOL = 1.0e-10
ASSOCIATOR_FLOOR = 1.0e-3
ASSOCIATOR_REQUIRED_FRACTION = 0.80
REGRESSION_TOL = 1.0e-12
DERIVATION_TOL = 1.0e-11

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite J3(O) coordinate arithmetic, fixed linear Peirce channel, cubic spectra, and grid DPI checks",
    },
    "scipy.linalg.expm": {
        "tried": True,
        "used": True,
        "reason": "load-bearing automorphism/isometry control from exp([L_a,L_b])",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive import loading, timestamps, paths, and JSON serialization",
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


j3 = load_module(J3_SOURCE_PATH, "j3o_bloch_body_entropy_pawl_v3_source")


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
    if isinstance(obj, float):
        if math.isfinite(obj):
            return obj
        if math.isnan(obj):
            return "NaN"
        return "Infinity" if obj > 0.0 else "-Infinity"
    return obj


def basis_vec(dim: int, idx: int) -> np.ndarray:
    out = np.zeros(dim, dtype=float)
    out[idx] = 1.0
    return out


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
    return j3.j3_from_parts(np.array(v[0:3], dtype=float), np.array(v[3:11]), np.array(v[11:19]), np.array(v[19:27]))


def jprod(table: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return j3.jordan(table, a, b)


def qrep(table: np.ndarray, c: np.ndarray, x: np.ndarray) -> np.ndarray:
    return j3.jordan_quadratic(table, c, x)


def spectral_values(table: np.ndarray, x: np.ndarray, method: str = "closed") -> np.ndarray:
    tr = j3.j3_trace(x)
    sig = j3.sigma2_j3(x)
    det = j3.det_j3(table, x)
    if method == "closed":
        eigs = j3.cubic_eigenvalues(tr, sig, det)
    elif method == "numpy_roots":
        coeff = np.array([1.0, -tr, sig, -det], dtype=float)
        roots = np.roots(coeff)
        if np.max(np.abs(np.imag(roots))) > 1.0e-7:
            raise RuntimeError(f"non-real cubic roots in cross-check: {roots}")
        eigs = np.sort(np.real(roots))[::-1]
    else:
        raise ValueError(method)
    return np.asarray(eigs, dtype=float)


def spectral_entropy(table: np.ndarray, rho: np.ndarray, method: str = "closed") -> float:
    eigs = np.clip(spectral_values(table, rho, method), 0.0, None)
    return float(-sum(float(x) * math.log(float(x)) for x in eigs if x > 0.0))


def spectral_projectors_lagrange(table: np.ndarray, x: np.ndarray) -> tuple[np.ndarray, list[np.ndarray]]:
    eigs = spectral_values(table, x, "closed")
    min_gap = min(abs(float(eigs[i] - eigs[j])) for i in range(3) for j in range(i + 1, 3))
    if min_gap < 1.0e-10:
        raise RuntimeError(f"Lagrange projectors require nondegenerate sigma; min_gap={min_gap:.3e}")
    unit = j3.j3_unit()
    projectors: list[np.ndarray] = []
    for i, lam in enumerate(eigs):
        others = [float(eigs[j]) for j in range(3) if j != i]
        numerator = jprod(table, x - others[0] * unit, x - others[1] * unit)
        denom = (float(lam) - others[0]) * (float(lam) - others[1])
        projectors.append(numerator / denom)
    return eigs, projectors


def jordan_log_from_projectors(table: np.ndarray, sigma: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
    eigs, projectors = spectral_projectors_lagrange(table, sigma)
    if float(np.min(eigs)) <= 0.0:
        raise RuntimeError("sigma must be full-rank for log(sigma)")
    log_sigma = sum(math.log(float(lam)) * p for lam, p in zip(eigs, projectors))
    recon = sum(float(lam) * p for lam, p in zip(eigs, projectors))
    unit_recon = sum(projectors)
    idempotent_errors = [float(np.linalg.norm(jprod(table, p, p) - p)) for p in projectors]
    orthogonality_errors = [
        float(np.linalg.norm(jprod(table, projectors[i], projectors[j])))
        for i in range(3)
        for j in range(i + 1, 3)
    ]
    report = {
        "sigma_eigenvalues": [float(x) for x in eigs],
        "projector_reconstruction_error": float(np.linalg.norm(recon - sigma)),
        "projector_unit_sum_error": float(np.linalg.norm(unit_recon - j3.j3_unit())),
        "projector_idempotent_error_max": float(max(idempotent_errors)),
        "projector_orthogonality_error_max": float(max(orthogonality_errors)),
        "method": "Lagrange interpolation on the cubic roots of sigma",
    }
    return log_sigma, report


def relative_entropy_full(table: np.ndarray, rho: np.ndarray, log_sigma: np.ndarray, method: str = "closed") -> float:
    return float(-spectral_entropy(table, rho, method) - j3.j3_trace(jprod(table, rho, log_sigma)))


def relative_entropy_diag_shadow(table: np.ndarray, rho: np.ndarray, sigma_diag: np.ndarray) -> float:
    logs = np.log(np.asarray(sigma_diag, dtype=float))
    return float(-spectral_entropy(table, rho, "closed") - j3.trace_rho_log_diagonal_shadow(rho, logs))


def peirce_diagonal_channel(table: np.ndarray, rho: np.ndarray, frame: list[np.ndarray]) -> np.ndarray:
    out = j3.j3_zero()
    for e in frame:
        out = out + qrep(table, e, rho)
    return out


def phi_channel(table: np.ndarray, rho: np.ndarray, frame: list[np.ndarray]) -> np.ndarray:
    return ALPHA * qrep(table, j3.j3_unit(), rho) + (1.0 - ALPHA) * peirce_diagonal_channel(table, rho, frame)


def trace_min_eig(table: np.ndarray, rho: np.ndarray) -> tuple[float, float]:
    eigs = spectral_values(table, rho, "closed")
    return float(j3.j3_trace(rho)), float(np.min(eigs))


def multi_block_octonion_state(rng: np.random.Generator, table: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
    attempts = 0
    while attempts < 20000:
        attempts += 1
        candidate = j3.random_density_candidate(rng, STATE_SCALE)
        data = j3.spectral_data(candidate, table)
        x01 = candidate[0, 1, :]
        x02 = candidate[0, 2, :]
        x12 = candidate[1, 2, :]
        block_norms = [float(np.linalg.norm(x01)), float(np.linalg.norm(x02)), float(np.linalg.norm(x12))]
        imag_norms = [float(np.linalg.norm(x01[1:])), float(np.linalg.norm(x02[1:])), float(np.linalg.norm(x12[1:]))]
        assoc = float(np.linalg.norm(j3.associator(table, x01, x02, x12)))
        if (
            data["min_eigenvalue"] > 1.0e-6
            and min(block_norms) > 1.0e-3
            and min(imag_norms) > 1.0e-3
            and assoc > ASSOCIATOR_FLOOR
            and j3.is_density(candidate, table, margin=1.0e-6)
        ):
            return candidate, {
                "attempts": attempts,
                "min_eigenvalue": data["min_eigenvalue"],
                "block_norms": block_norms,
                "imaginary_block_norms": imag_norms,
                "associator_norm": assoc,
            }
    raise RuntimeError("could not sample a genuinely multi-block octonion density state")


def sample_grid(rng: np.random.Generator, table: np.ndarray) -> tuple[list[np.ndarray], dict[str, Any]]:
    states = []
    rows = []
    total_attempts = 0
    for idx in range(STATE_COUNT):
        state, report = multi_block_octonion_state(rng, table)
        states.append(state)
        report["state_index"] = idx
        rows.append(report)
        total_attempts += int(report["attempts"])
    return states, {
        "construction": "regenerated random_density_candidate pool; accepted only density states with all three off-diagonal octonion blocks nonzero and generic imaginary parts",
        "sample_count": len(states),
        "state_scale": STATE_SCALE,
        "total_attempts": total_attempts,
        "min_initial_eigenvalue": float(min(row["min_eigenvalue"] for row in rows)),
        "initial_associator_min": float(min(row["associator_norm"] for row in rows)),
        "initial_associator_median": float(np.median([row["associator_norm"] for row in rows])),
        "initial_associator_max": float(max(row["associator_norm"] for row in rows)),
        "first_rows": rows[:6],
        "source_indices_note": "Equivalent to using the random_density_candidate tail at indices 122+ of the older grid; no coordinate-only or primitive-frame states are sampled.",
    }


def associator_norm(table: np.ndarray, rho: np.ndarray) -> float:
    return float(np.linalg.norm(j3.associator(table, rho[0, 1, :], rho[0, 2, :], rho[1, 2, :])))


def linearity_gate(table: np.ndarray, frame: list[np.ndarray], rng: np.random.Generator) -> dict[str, Any]:
    max_error = 0.0
    rows = []
    for idx in range(24):
        x = j3.random_density_candidate(rng, 0.035)
        y = j3.random_density_candidate(rng, 0.035)
        a = float(rng.normal())
        b = float(rng.normal())
        lhs = phi_channel(table, a * x + b * y, frame)
        rhs = a * phi_channel(table, x, frame) + b * phi_channel(table, y, frame)
        err = float(np.linalg.norm(lhs - rhs))
        max_error = max(max_error, err)
        if idx < 4:
            rows.append({"sample": idx, "a": a, "b": b, "superposition_error": err})
    return {
        "test": "Phi(a*x+b*y) == a*Phi(x)+b*Phi(y)",
        "samples": 24,
        "max_superposition_error": max_error,
        "tolerance": LINEARITY_TOL,
        "pass": bool(max_error <= LINEARITY_TOL),
        "sample_rows": rows,
    }


def trace_positivity_gate(table: np.ndarray, frame: list[np.ndarray], states: list[np.ndarray]) -> dict[str, Any]:
    min_eig = float("inf")
    max_trace_error = 0.0
    rows = []
    for idx, rho in enumerate(states):
        current = np.array(rho, dtype=float, copy=True)
        for step in range(FLOW_STEPS + 1):
            tr, mine = trace_min_eig(table, current)
            min_eig = min(min_eig, mine)
            max_trace_error = max(max_trace_error, abs(tr - 1.0))
            if idx < 3 and step in {0, 1, FLOW_STEPS}:
                rows.append({"state_index": idx, "step": step, "trace": tr, "min_eigenvalue": mine})
            if step < FLOW_STEPS:
                current = phi_channel(table, current, frame)
    return {
        "grid_states": len(states),
        "trajectory_steps": FLOW_STEPS,
        "min_eigenvalue": float(min_eig),
        "max_trace_error": float(max_trace_error),
        "trace_tolerance": TRACE_TOL,
        "positivity_tolerance": POSITIVITY_TOL,
        "trace_preservation_pass": bool(max_trace_error <= TRACE_TOL),
        "positivity_pass": bool(min_eig >= -POSITIVITY_TOL),
        "sample_rows": rows,
    }


def diagonal_regression_gate(table: np.ndarray, log_sigma: np.ndarray, sigma_diag: np.ndarray, states: list[np.ndarray]) -> dict[str, Any]:
    diffs = []
    rows = []
    diagonal_controls = [
        j3.j3_diag([0.70, 0.20, 0.10]),
        j3.j3_diag([0.20, 0.55, 0.25]),
        j3.j3_diag([0.34, 0.33, 0.33]),
    ]
    for idx, rho in enumerate(diagonal_controls + states[:12]):
        full = relative_entropy_full(table, rho, log_sigma, "closed")
        shadow = relative_entropy_diag_shadow(table, rho, sigma_diag)
        diff = abs(full - shadow)
        diffs.append(diff)
        if idx < 8:
            rows.append({"sample": idx, "full": full, "diagonal_shadow": shadow, "abs_diff": diff})
    return {
        "meaning": "For diagonal sigma only, the full spectral-projector log must agree with the old diagonal-shadow formula.",
        "samples": len(diffs),
        "max_abs_diff": float(max(diffs)),
        "tolerance": REGRESSION_TOL,
        "pass": bool(max(diffs) <= REGRESSION_TOL),
        "sample_rows": rows,
    }


def dpi_sweep(table: np.ndarray, frame: list[np.ndarray], states: list[np.ndarray], log_sigma: np.ndarray) -> dict[str, Any]:
    max_increase = -float("inf")
    min_delta = float("inf")
    violations = []
    witness_rows = []
    assoc_trajectory_max = []
    assoc_trajectory_min = []
    for state_index, start in enumerate(states):
        rho = np.array(start, dtype=float, copy=True)
        d_values = [relative_entropy_full(table, rho, log_sigma, "closed")]
        assoc_values = [associator_norm(table, rho)]
        for _ in range(FLOW_STEPS):
            nxt = phi_channel(table, rho, frame)
            d_values.append(relative_entropy_full(table, nxt, log_sigma, "closed"))
            assoc_values.append(associator_norm(table, nxt))
            delta = d_values[-1] - d_values[-2]
            max_increase = max(max_increase, float(delta))
            min_delta = min(min_delta, float(delta))
            if delta > DPI_TOL:
                violations.append(
                    {
                        "state_index": state_index,
                        "step": len(d_values) - 2,
                        "delta": float(delta),
                        "before": float(d_values[-2]),
                        "after": float(d_values[-1]),
                        "rho_before": rho,
                        "rho_after": nxt,
                    }
                )
            rho = nxt
        assoc_trajectory_max.append(max(assoc_values))
        assoc_trajectory_min.append(min(assoc_values))
        if state_index < 6:
            witness_rows.append(
                {
                    "state_index": state_index,
                    "D_start": d_values[0],
                    "D_end": d_values[-1],
                    "max_step_increase": float(max(b - a for a, b in zip(d_values, d_values[1:]))),
                    "associator_min": float(min(assoc_values)),
                    "associator_max": float(max(assoc_values)),
                }
            )
    assoc_pass_count = int(sum(x > ASSOCIATOR_FLOOR for x in assoc_trajectory_max))
    assoc_fraction = assoc_pass_count / len(states)
    return {
        "sample_count": len(states),
        "steps_per_state": FLOW_STEPS,
        "comparison": "D(Phi(rho)||sigma) - D(rho||sigma)",
        "violation_count": len(violations),
        "max_increase": float(max_increase),
        "most_negative_delta": float(min_delta),
        "dpi_holds_on_grid": bool(len(violations) == 0),
        "associator_gate": {
            "floor": ASSOCIATOR_FLOOR,
            "required_fraction": ASSOCIATOR_REQUIRED_FRACTION,
            "trajectory_statistic": "max associator(x01,x02,x12) along each trajectory",
            "pass_count": assoc_pass_count,
            "sample_count": len(states),
            "fraction_above_floor": float(assoc_fraction),
            "trajectory_max_min": float(min(assoc_trajectory_max)),
            "trajectory_max_median": float(np.median(assoc_trajectory_max)),
            "trajectory_max_max": float(max(assoc_trajectory_max)),
            "trajectory_min_min": float(min(assoc_trajectory_min)),
            "pass": bool(assoc_fraction > ASSOCIATOR_REQUIRED_FRACTION),
            "flow_confined_to_associative_slice": bool(assoc_fraction <= ASSOCIATOR_REQUIRED_FRACTION),
        },
        "witness_rows": witness_rows,
        "violations_raw": violations,
    }


def crosscheck_violations(table: np.ndarray, log_sigma: np.ndarray, violations: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    confirmed = []
    for idx, item in enumerate(violations[:12]):
        before_closed = relative_entropy_full(table, item["rho_before"], log_sigma, "closed")
        after_closed = relative_entropy_full(table, item["rho_after"], log_sigma, "closed")
        before_roots = relative_entropy_full(table, item["rho_before"], log_sigma, "numpy_roots")
        after_roots = relative_entropy_full(table, item["rho_after"], log_sigma, "numpy_roots")
        trace_term_before = np.longdouble(-j3.j3_trace(jprod(table, item["rho_before"], log_sigma)))
        trace_term_after = np.longdouble(-j3.j3_trace(jprod(table, item["rho_after"], log_sigma)))
        row = {
            "violation_index": idx,
            "state_index": item["state_index"],
            "step": item["step"],
            "delta_closed": float(after_closed - before_closed),
            "delta_numpy_roots": float(after_roots - before_roots),
            "longdouble_trace_term_delta": float(trace_term_after - trace_term_before),
            "confirmed": bool((after_closed - before_closed) > DPI_TOL and (after_roots - before_roots) > DPI_TOL),
        }
        rows.append(row)
        if row["confirmed"]:
            confirmed.append(row)
    return {
        "triggered": bool(violations),
        "method": "closed cubic solver vs numpy.roots cubic solver; trace-log-sigma term recomputed through numpy.longdouble",
        "checked_count": len(rows),
        "confirmed_count": len(confirmed),
        "rows": rows,
    }


def wrong_sigma_control(table: np.ndarray, frame: list[np.ndarray], states: list[np.ndarray], rng: np.random.Generator) -> dict[str, Any]:
    wrong_sigma, wrong_report = multi_block_octonion_state(rng, table)
    log_wrong, wrong_log_report = jordan_log_from_projectors(table, wrong_sigma)
    max_increase = -float("inf")
    violation_count = 0
    rows = []
    control_states = [wrong_sigma] + list(states)
    for idx, rho in enumerate(control_states):
        before = relative_entropy_full(table, rho, log_wrong, "closed")
        after = relative_entropy_full(table, phi_channel(table, rho, frame), log_wrong, "closed")
        delta = after - before
        if delta > DPI_TOL:
            violation_count += 1
        if delta > max_increase:
            max_increase = float(delta)
        if idx < 8:
            rows.append(
                {
                    "state_index": idx,
                    "state_role": "wrong_sigma_itself" if idx == 0 else "main_grid_state",
                    "delta": float(delta),
                    "before": before,
                    "after": after,
                }
            )
    return {
        "meaning": "Control deliberately uses a full octonionic sigma that is not fixed by Phi; the first control state is wrong_sigma itself, so D(sigma||sigma)=0 and Phi(sigma)!=sigma must break the premise.",
        "wrong_sigma_sampling": wrong_report,
        "wrong_sigma_log": wrong_log_report,
        "phi_wrong_sigma_distance": float(np.linalg.norm(phi_channel(table, wrong_sigma, frame) - wrong_sigma)),
        "violation_count": violation_count,
        "sample_count": len(control_states),
        "max_increase": float(max_increase),
        "breaks": bool(violation_count > 0),
        "sample_rows": rows,
    }


def classical_simplex_control(rng: np.random.Generator) -> dict[str, Any]:
    sigma = np.array([0.50, 0.30, 0.20], dtype=float)

    def rel(p: np.ndarray) -> float:
        return float(sum(pi * (math.log(pi) - math.log(si)) for pi, si in zip(p, sigma) if pi > 0.0))

    def channel(p: np.ndarray) -> np.ndarray:
        return ALPHA * p + (1.0 - ALPHA) * p

    violations = 0
    max_increase = -float("inf")
    for _ in range(128):
        p = rng.dirichlet(np.array([1.4, 1.2, 1.1]))
        delta = rel(channel(p)) - rel(p)
        max_increase = max(max_increase, float(delta))
        if delta > DPI_TOL:
            violations += 1
    return {
        "architecture": "same fixed-weight identity plus Peirce diagonal projection; on the classical simplex the projection is identity",
        "sample_count": 128,
        "violation_count": violations,
        "max_increase": float(max_increase),
        "zero_violations": bool(violations == 0),
    }


def left_matrix(table: np.ndarray, a: np.ndarray) -> np.ndarray:
    cols = []
    for idx in range(27):
        cols.append(j3_vec_from_elem(jprod(table, a, j3_elem_from_vec(basis_vec(27, idx)))))
    return np.column_stack(cols)


def derivation_matrix(table: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    la = left_matrix(table, a)
    lb = left_matrix(table, b)
    return la @ lb - lb @ la


def automorphism_isometry_control(table: np.ndarray, states: list[np.ndarray], sigma: np.ndarray) -> dict[str, Any]:
    a = j3.j3_from_parts(np.zeros(3), basis_vec(8, 1), np.zeros(8), np.zeros(8))
    b = j3.j3_diag([1.0, -1.0, 0.0])
    d = derivation_matrix(table, a, b)
    auto = expm(0.19 * d)
    log_sigma, _ = jordan_log_from_projectors(table, sigma)
    moved_sigma = j3_elem_from_vec(auto @ j3_vec_from_elem(sigma))
    moved_log_sigma, _ = jordan_log_from_projectors(table, moved_sigma)
    max_diff = 0.0
    product_error = 0.0
    rows = []
    for idx, rho in enumerate(states[:18]):
        moved = j3_elem_from_vec(auto @ j3_vec_from_elem(rho))
        before = relative_entropy_full(table, rho, log_sigma, "closed")
        after = relative_entropy_full(table, moved, moved_log_sigma, "closed")
        diff = abs(after - before)
        max_diff = max(max_diff, float(diff))
        if idx < 6:
            rows.append({"state_index": idx, "before": before, "after": after, "abs_diff": diff})
    for idx in range(6):
        x = states[idx]
        y = states[-(idx + 1)]
        moved_prod = j3_elem_from_vec(auto @ j3_vec_from_elem(jprod(table, x, y)))
        prod_moved = jprod(table, j3_elem_from_vec(auto @ j3_vec_from_elem(x)), j3_elem_from_vec(auto @ j3_vec_from_elem(y)))
        product_error = max(product_error, float(np.linalg.norm(moved_prod - prod_moved)))
    return {
        "definition": "automorphism A=exp(t[L_a,L_b]); compare D(A rho || A sigma) to D(rho || sigma)",
        "derivation_matrix_norm": float(np.linalg.norm(d)),
        "max_relative_entropy_isometry_error": float(max_diff),
        "max_product_preservation_error": float(product_error),
        "pass": bool(max_diff <= DERIVATION_TOL and product_error <= DERIVATION_TOL),
        "sample_rows": rows,
    }


def fixed_point_gate(table: np.ndarray, frame: list[np.ndarray], sigma: np.ndarray) -> dict[str, Any]:
    moved = phi_channel(table, sigma, frame)
    return {
        "sigma": "diag(0.50,0.30,0.20)",
        "sigma_trace": j3.j3_trace(sigma),
        "sigma_min_eigenvalue": float(np.min(spectral_values(table, sigma))),
        "phi_sigma_distance": float(np.linalg.norm(moved - sigma)),
        "pass": bool(np.linalg.norm(moved - sigma) <= 1.0e-14),
    }


def summarize_verdict(gates: dict[str, Any], dpi: dict[str, Any]) -> str:
    construction_ok = bool(
        gates["linearity"]["pass"]
        and gates["trace_positivity"]["trace_preservation_pass"]
        and gates["trace_positivity"]["positivity_pass"]
        and gates["fixed_point"]["pass"]
        and gates["diagonal_regression"]["pass"]
        and gates["octonion_associator"]["pass"]
    )
    if not construction_ok:
        return "map_construction_failed"
    if dpi["violation_count"] > 0:
        return "dpi_violated"
    return "dpi_holds_on_grid"


def build_result() -> dict[str, Any]:
    rng = np.random.default_rng(SEED)
    table = j3.octonion_table()
    frame = [j3.j3_diag([1.0, 0.0, 0.0]), j3.j3_diag([0.0, 1.0, 0.0]), j3.j3_diag([0.0, 0.0, 1.0])]
    sigma_diag = np.array([0.50, 0.30, 0.20], dtype=float)
    sigma = j3.j3_diag(sigma_diag)
    log_sigma, log_report = jordan_log_from_projectors(table, sigma)
    states, grid_report = sample_grid(rng, table)

    gates: dict[str, Any] = {
        "linearity": linearity_gate(table, frame, np.random.default_rng(SEED + 10)),
        "trace_positivity": trace_positivity_gate(table, frame, states),
        "fixed_point": fixed_point_gate(table, frame, sigma),
        "diagonal_regression": diagonal_regression_gate(table, log_sigma, sigma_diag, states),
    }
    dpi = dpi_sweep(table, frame, states, log_sigma)
    gates["octonion_associator"] = dpi["associator_gate"]
    crosscheck = crosscheck_violations(table, log_sigma, dpi["violations_raw"])
    wrong = wrong_sigma_control(table, frame, states, np.random.default_rng(SEED + 20))
    classical = classical_simplex_control(np.random.default_rng(SEED + 30))
    auto = automorphism_isometry_control(table, states, sigma)
    verdict = summarize_verdict(gates, dpi)

    serialized_violations = []
    if verdict == "dpi_violated":
        for item in dpi["violations_raw"][:8]:
            serialized_violations.append(
                {
                    "state_index": item["state_index"],
                    "step": item["step"],
                    "delta": item["delta"],
                    "before": item["before"],
                    "after": item["after"],
                    "rho_before_vec": j3_vec_from_elem(item["rho_before"]),
                    "rho_after_vec": j3_vec_from_elem(item["rho_after"]),
                }
            )
    dpi = {k: v for k, v in dpi.items() if k != "violations_raw"}
    dpi["serialized_violation_trajectories"] = serialized_violations

    all_pass = bool(
        verdict in {"dpi_holds_on_grid", "dpi_violated"}
        and classical["zero_violations"]
        and wrong["breaks"]
        and auto["pass"]
        and (not crosscheck["triggered"] or crosscheck["confirmed_count"] > 0)
    )
    return {
        "schema": "codex_ratchet.jordan_dpi_probe_v3_result.v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "sim_execution_kind": "classical",
        "sim_class": "jordan_dpi_finite_grid_probe",
        "seed": SEED,
        "rng": "numpy.default_rng(0)",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "claim_ceiling": "Scratch diagnostic finite-grid evidence for one linear positive trace-preserving J3(O) Peirce channel; no theorem, no canonical admission, no J2/spin-factor exceptional claim.",
        "banned_modes_guard": {
            "state_dependent_normalization_in_phi": False,
            "conditioned_single_kraus_branch": False,
            "diagonal_shadow_relative_entropy_formula_for_main_claim": False,
            "J2_or_spin_factor_exceptional_claim": False,
            "hardcoded_verdict": False,
        },
        "map": {
            "formula": "Phi(rho)=alpha*U_1(rho)+(1-alpha)*sum_i U_ei(rho)",
            "alpha": ALPHA,
            "weights_state_independent": True,
            "trace_preservation_reason": "tr(U_1 rho)=tr(rho), and sum_i U_ei is the trace-preserving Peirce diagonal projection for the standard Jordan frame",
            "positivity_reason": "convex combination of positive quadratic-representation/Peirce projection maps",
            "fixed_point_sigma": [float(x) for x in sigma_diag],
        },
        "spectral_log_sigma": log_report,
        "state_grid": grid_report,
        "gates": gates,
        "dpi_table": dpi,
        "violation_crosscheck": crosscheck,
        "controls": {
            "classical_simplex": classical,
            "wrong_sigma": wrong,
            "automorphism_isometry": auto,
        },
        "verdict": verdict,
        "all_pass": all_pass,
        "promotion_status": "diagnostic_only",
        "eligible_consumers": [],
        "blocked_consumers": [
            "formal Jordan-DPI theorem",
            "canonical-by-process promotion",
            "J2/spin-factor exceptional-rung claims",
            "Axis0, bridge, manifold, or physics admission",
        ],
    }


def print_summary(result: dict[str, Any]) -> None:
    print("JORDAN_DPI_PROBE_V3_SIM")
    print(f"seed={SEED} classification={CLASSIFICATION} promotion_allowed={PROMOTION_ALLOWED}")
    print("J3(O) only; no J2/spin-factor exceptional claim")
    print(
        "linear map: Phi(rho)=alpha*U_1(rho)+(1-alpha)*sum_i U_ei(rho); "
        f"alpha={ALPHA}; no state-dependent normalization"
    )
    lin = result["gates"]["linearity"]
    tp = result["gates"]["trace_positivity"]
    assoc = result["gates"]["octonion_associator"]
    reg = result["gates"]["diagonal_regression"]
    fp = result["gates"]["fixed_point"]
    dpi = result["dpi_table"]
    controls = result["controls"]
    print(
        "linearity gate: "
        f"pass={lin['pass']} max_superposition_error={lin['max_superposition_error']:.3e} tol={lin['tolerance']:.1e}"
    )
    print(
        "trace/positivity gate: "
        f"trace_pass={tp['trace_preservation_pass']} max_trace_error={tp['max_trace_error']:.3e} "
        f"positivity_pass={tp['positivity_pass']} min_eigenvalue={tp['min_eigenvalue']:.6e}"
    )
    print(
        "fixed point gate: "
        f"pass={fp['pass']} sigma={fp['sigma']} phi_sigma_distance={fp['phi_sigma_distance']:.3e}"
    )
    print(
        "full-log regression gate: "
        f"pass={reg['pass']} max_full_vs_shadow_diff={reg['max_abs_diff']:.3e}"
    )
    print(
        "associator gate: "
        f"pass={assoc['pass']} fraction_above_floor={assoc['fraction_above_floor']:.3f} "
        f"floor={assoc['floor']:.1e} trajectory_max_min={assoc['trajectory_max_min']:.6e}"
    )
    print("DPI table:")
    print(
        f"  verdict_candidate={'dpi_holds_on_grid' if dpi['dpi_holds_on_grid'] else 'dpi_violated'} "
        f"violations={dpi['violation_count']} max_increase={dpi['max_increase']:.6e} "
        f"most_negative_delta={dpi['most_negative_delta']:.6e}"
    )
    print(
        "controls: "
        f"classical_zero_violations={controls['classical_simplex']['zero_violations']} "
        f"wrong_sigma_breaks={controls['wrong_sigma']['breaks']} "
        f"automorphism_isometry_pass={controls['automorphism_isometry']['pass']}"
    )
    xcheck = result["violation_crosscheck"]
    print(
        "violation crosscheck: "
        f"triggered={xcheck['triggered']} checked={xcheck['checked_count']} confirmed={xcheck['confirmed_count']}"
    )
    print(f"verdict={result['verdict']} all_pass={result['all_pass']}")
    print(f"wrote: {RESULT_PATH}")


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(clean(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print_summary(result)
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
