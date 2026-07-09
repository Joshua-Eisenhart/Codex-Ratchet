#!/usr/bin/env python3
"""Finite Araki modular crosscheck for the Umegaki terrain pawl.

Scratch diagnostic only.  This file checks that the finite-dimensional
relative modular operator route reproduces the same Umegaki quantity used by
the terrain pawl census on the associative qubit terrains.

Scope boundary: the construction below is the standard matrix-algebra/GNS
construction on vectorized M_2(C).  It is not applied to the exceptional
Jordan/Albert factor, where the no-associative-embedding fact blocks this
associative modular route.
"""

from __future__ import annotations

import datetime as dt
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from scipy.linalg import logm

from terrain_lyapunov_pawl_census_sim import (
    SEED,
    TERR,
    TERRAIN_LABELS,
    bloch,
    long_fixed_point,
    seeded_state_grid,
)


HERE = Path(__file__).resolve().parent
SOURCE_PATH = HERE / "araki_modular_umegaki_crosscheck_sim.py"
RESULT_PATH = HERE / "araki_modular_umegaki_crosscheck_sim_results.json"

SIM_ID = "araki_modular_umegaki_crosscheck_sim"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False

DIM = 2
GNS_DIM = DIM * DIM
CLASSICAL_TOL = 1.0e-12
AGREEMENT_TOL = 1.0e-10
SPECTRAL_TOL = 1.0e-12

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing 2x2 states, vectorized GNS space, modular operator matrices, spectral support checks, seeded terrain census",
    },
    "scipy.linalg.logm": {
        "tried": True,
        "used": True,
        "reason": "load-bearing logarithm of the 4x4 finite relative modular operator",
    },
    "terrain_lyapunov_pawl_census_sim": {
        "tried": True,
        "used": True,
        "reason": "load-bearing reuse of the seeded 256-state grid, 8 terrain labels, and terrain fixed points",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive timestamps, paths, JSON serialization, and scalar math",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "scipy.linalg.logm": "load_bearing",
    "terrain_lyapunov_pawl_census_sim": "load_bearing",
    "python_stdlib": "supportive",
}


def clean_density(rho: np.ndarray) -> np.ndarray:
    rho = np.asarray(rho, dtype=complex)
    rho = 0.5 * (rho + rho.conj().T)
    tr = float(np.trace(rho).real)
    if not math.isfinite(tr) or abs(tr) <= SPECTRAL_TOL:
        raise ValueError("density matrix has zero or non-finite trace")
    return rho / tr


def spectrum(rho: np.ndarray) -> np.ndarray:
    return np.linalg.eigvalsh(clean_density(rho)).real


def is_positive_definite(rho: np.ndarray) -> bool:
    return bool(np.min(spectrum(rho)) > SPECTRAL_TOL)


def matrix_function_psd(rho: np.ndarray, fn: str) -> np.ndarray:
    vals, vecs = np.linalg.eigh(clean_density(rho))
    vals = vals.real
    if np.min(vals) <= SPECTRAL_TOL:
        raise ValueError(f"{fn} requires a strictly positive density matrix")
    if fn == "sqrt":
        diag = np.sqrt(vals)
    elif fn == "log":
        diag = np.log(vals)
    else:
        raise ValueError(f"unknown matrix function: {fn}")
    return vecs @ np.diag(diag) @ vecs.conj().T


def vec(matrix: np.ndarray) -> np.ndarray:
    return np.asarray(matrix, dtype=complex).reshape((-1,), order="F")


def left_multiply_matrix(a: np.ndarray) -> np.ndarray:
    return np.kron(np.eye(a.shape[0], dtype=complex), a)


def right_multiply_inverse_matrix(b: np.ndarray) -> np.ndarray:
    return np.kron(np.linalg.inv(b).T, np.eye(b.shape[0], dtype=complex))


def relative_modular_operator(delta_left: np.ndarray, delta_right: np.ndarray) -> np.ndarray:
    """Return Delta = L_delta_left R_delta_right^{-1} on column-vectorized M_2(C)."""
    left = left_multiply_matrix(clean_density(delta_left))
    right_inverse = right_multiply_inverse_matrix(clean_density(delta_right))
    return left @ right_inverse


def finite_modular_entropy(
    xi_state: np.ndarray,
    delta_left: np.ndarray,
    delta_right: np.ndarray,
) -> dict[str, Any]:
    """Compute -<xi_state^1/2, log(L_delta_left R_delta_right^-1) xi_state^1/2>."""
    xi_state = clean_density(xi_state)
    delta_left = clean_density(delta_left)
    delta_right = clean_density(delta_right)
    if not is_positive_definite(xi_state):
        return {"ok": False, "status": "ill_defined_singular_xi_state"}
    if not is_positive_definite(delta_left):
        return {"ok": False, "status": "ill_defined_singular_delta_left"}
    if not is_positive_definite(delta_right):
        return {"ok": False, "status": "ill_defined_singular_delta_right"}
    xi = vec(matrix_function_psd(xi_state, "sqrt"))
    delta = relative_modular_operator(delta_left, delta_right)
    log_delta = logm(delta)
    raw = -np.vdot(xi, log_delta @ xi)
    return {
        "ok": True,
        "status": "finite",
        "value": float(np.real_if_close(raw, tol=1000).real),
        "imag_abs": float(abs(raw.imag)),
        "delta_shape": list(delta.shape),
        "delta_eigenvalues": [float(np.real_if_close(x).real) for x in np.linalg.eigvals(delta)],
    }


def araki_relative_entropy(rho: np.ndarray, sigma: np.ndarray) -> dict[str, Any]:
    """Convention under test: S(rho||sigma) = -<xi_rho, log Delta_{sigma|rho} xi_rho>."""
    return finite_modular_entropy(rho, sigma, rho)


def swapped_delta_control(rho: np.ndarray, sigma: np.ndarray) -> dict[str, Any]:
    """Wrong control: keep xi_rho but swap Delta_{sigma|rho} to Delta_{rho|sigma}."""
    return finite_modular_entropy(rho, rho, sigma)


def umegaki_relative_entropy(rho: np.ndarray, sigma: np.ndarray) -> dict[str, Any]:
    rho = clean_density(rho)
    sigma = clean_density(sigma)
    if not is_positive_definite(rho):
        return {"ok": False, "status": "ill_defined_singular_rho"}
    if not is_positive_definite(sigma):
        return {"ok": False, "status": "ill_defined_singular_sigma"}
    log_rho = matrix_function_psd(rho, "log")
    log_sigma = matrix_function_psd(sigma, "log")
    value = np.trace(rho @ (log_rho - log_sigma))
    return {"ok": True, "status": "finite", "value": float(np.real_if_close(value, tol=1000).real)}


def classical_pair_gate() -> dict[str, Any]:
    rho = np.diag([0.7, 0.3]).astype(complex)
    sigma = np.diag([0.4, 0.6]).astype(complex)
    expected = float(0.7 * math.log(0.7 / 0.4) + 0.3 * math.log(0.3 / 0.6))
    araki = araki_relative_entropy(rho, sigma)
    swapped = swapped_delta_control(rho, sigma)
    diff = abs(araki.get("value", float("nan")) - expected) if araki["ok"] else float("inf")
    swapped_mismatch = abs(swapped.get("value", float("nan")) - expected) if swapped["ok"] else float("inf")
    passed = bool(araki["ok"] and diff <= CLASSICAL_TOL and swapped["ok"] and swapped_mismatch > 1.0e-6)
    return {
        "pair": {"rho_diag": [0.7, 0.3], "sigma_diag": [0.4, 0.6]},
        "expected_kl_nats": expected,
        "passed_convention": "S(rho||sigma)=-<vec(sqrt(rho)), log(L_sigma R_rho^{-1}) vec(sqrt(rho))>",
        "gns_vector": "xi_rho=vec(rho^{1/2}), column-major vectorization",
        "relative_modular_operator": "Delta_{sigma|rho}=L_sigma R_rho^{-1} on vectorized M_2(C)",
        "araki": araki,
        "abs_diff": diff,
        "swapped_delta_control": {
            "value": swapped.get("value"),
            "abs_mismatch_from_kl": swapped_mismatch,
            "nonmatching": bool(swapped["ok"] and swapped_mismatch > 1.0e-6),
        },
        "pass": passed,
    }


def terrain_census() -> dict[str, Any]:
    rng = np.random.default_rng(SEED)
    states = seeded_state_grid(rng)
    fixed_points = {ti: long_fixed_point(ti) for ti in range(8)}
    rows: list[dict[str, Any]] = []
    max_abs_diff = 0.0
    worst_row: dict[str, Any] | None = None
    swapped_mismatches = []
    ill_defined = []

    for ti in range(8):
        sigma = fixed_points[ti]
        sigma_spectrum = spectrum(sigma)
        for state_idx, rho in enumerate(states):
            araki = araki_relative_entropy(rho, sigma)
            umegaki = umegaki_relative_entropy(rho, sigma)
            if not (araki["ok"] and umegaki["ok"]):
                ill_defined.append({"terrain": ti, "state_index": state_idx, "araki": araki, "umegaki": umegaki})
                continue
            diff = abs(araki["value"] - umegaki["value"])
            if diff > max_abs_diff:
                max_abs_diff = diff
                worst_row = {
                    "terrain": ti,
                    "label": TERRAIN_LABELS[ti],
                    "state_index": state_idx,
                    "araki": araki["value"],
                    "umegaki": umegaki["value"],
                    "abs_diff": diff,
                    "rho_bloch": [float(x) for x in bloch(rho)],
                    "sigma_bloch": [float(x) for x in bloch(sigma)],
                }
            swapped = swapped_delta_control(rho, sigma)
            if swapped["ok"] and umegaki["value"] > 1.0e-9:
                swapped_mismatches.append(abs(swapped["value"] - umegaki["value"]))
            rows.append(
                {
                    "terrain": ti,
                    "label": TERRAIN_LABELS[ti],
                    "kind": TERR[ti][1],
                    "state_index": state_idx,
                    "araki": round(float(araki["value"]), 14),
                    "umegaki": round(float(umegaki["value"]), 14),
                    "abs_diff": float(diff),
                    "delta_shape": araki["delta_shape"],
                }
            )

    agreement_pass = bool(not ill_defined and max_abs_diff <= AGREEMENT_TOL)
    return {
        "seed": SEED,
        "state_count": len(states),
        "terrain_count": 8,
        "pair_count": len(rows),
        "expected_pair_count": len(states) * 8,
        "fixed_point_spectra": {
            str(ti): [float(x) for x in spectrum(fp)] for ti, fp in fixed_points.items()
        },
        "max_abs_araki_minus_umegaki": max_abs_diff,
        "worst_row": worst_row,
        "agreement_tolerance": AGREEMENT_TOL,
        "agreement_pass": agreement_pass,
        "ill_defined_pairs": ill_defined,
        "swapped_delta_control": {
            "tested_nonzero_pairs": len(swapped_mismatches),
            "min_abs_mismatch": float(min(swapped_mismatches)) if swapped_mismatches else None,
            "max_abs_mismatch": float(max(swapped_mismatches)) if swapped_mismatches else None,
            "mean_abs_mismatch": float(np.mean(swapped_mismatches)) if swapped_mismatches else None,
            "nonmatching": bool(swapped_mismatches and max(swapped_mismatches) > 1.0e-6),
            "note": "rho=sigma zero-entropy pairs are excluded because the swapped control is mathematically also zero there",
        },
        "rows": rows,
    }


def singular_sigma_control() -> dict[str, Any]:
    rho = np.diag([0.6, 0.4]).astype(complex)
    pure_sigma = np.diag([1.0, 0.0]).astype(complex)
    araki = araki_relative_entropy(rho, pure_sigma)
    umegaki = umegaki_relative_entropy(rho, pure_sigma)
    flagged = bool((not araki["ok"]) and (not umegaki["ok"]))
    return {
        "rho_diag": [0.6, 0.4],
        "sigma_diag": [1.0, 0.0],
        "araki": araki,
        "umegaki": umegaki,
        "flagged_ill_defined_without_regularization": flagged,
        "epsilon_patch_used": False,
        "pass": flagged,
    }


def build_result() -> dict[str, Any]:
    classical = classical_pair_gate()
    if classical["pass"]:
        census = terrain_census()
    else:
        census = {
            "agreement_pass": False,
            "skipped": True,
            "reason": "classical convention gate failed; terrain census not run",
        }
    singular = singular_sigma_control()
    controls_pass = bool(
        classical["swapped_delta_control"]["nonmatching"]
        and singular["pass"]
        and census.get("swapped_delta_control", {}).get("nonmatching", False)
    )
    if not classical["pass"]:
        verdict = "mismatch_found"
    elif not census.get("agreement_pass", False):
        verdict = "mismatch_found"
    elif not singular["pass"]:
        verdict = "ill_posed"
    elif not controls_pass:
        verdict = "mismatch_found"
    else:
        verdict = "modular_face_earned"
    all_pass = verdict == "modular_face_earned"
    return {
        "schema": "codex_ratchet.araki_modular_umegaki_crosscheck.v1",
        "sim_id": SIM_ID,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": "scratch_diagnostic; local rerun only; no canonical, bridge, axis, exceptional-factor, or admission claim",
        "question": "Does finite-dimensional Araki relative entropy from the relative modular operator reproduce Umegaki S(rho||sigma) on the 8 associative qubit engine terrains?",
        "scope": {
            "included": "associative qubit terrains only; vectorized M_2(C) GNS space has dimension 4 and Delta is 4x4",
            "excluded": "exceptional Jordan/Albert factor",
            "boundary_reason": "the modular route here requires an associative matrix algebra; H_3(O)/exceptional Albert is non-special with no associative embedding",
            "boundary_source": "system_v7/constraint_core/sims_and_scripts/holism_does_not_force_octonions_sim.py records H_3(O) as unique exceptional non-special/no associative embedding; engine_field_choi_jordan_albert_probe_sim.py keeps Albert packing diagnostic-only",
        },
        "convention_derivation": {
            "formula": "S(rho||sigma)=-<xi_rho, log(Delta_{sigma|rho}) xi_rho>",
            "xi": "xi_rho=vec(rho^{1/2})",
            "delta": "Delta_{sigma|rho}=L_sigma R_rho^{-1}",
            "finite_identity": "-Tr[rho^{1/2}(log(sigma)rho^{1/2}-rho^{1/2}log(rho))]=Tr[rho(log(rho)-log(sigma))]",
            "vectorized_space_dimension": GNS_DIM,
            "delta_shape": [GNS_DIM, GNS_DIM],
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "gates": {
            "classical_pair_convention_gate": classical,
            "terrain_agreement_gate": census,
            "singular_sigma_control": singular,
            "controls_pass": controls_pass,
        },
        "verdict": verdict,
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    terrain_gate = result["gates"]["terrain_agreement_gate"]
    print("FINITE ARAKI MODULAR / UMEGAKI CROSSCHECK")
    print(f"  wrote: {RESULT_PATH}")
    print(f"  convention gate: {result['gates']['classical_pair_convention_gate']['pass']}")
    print(f"  convention: {result['gates']['classical_pair_convention_gate']['passed_convention']}")
    print(
        "  terrain agreement: "
        f"{terrain_gate.get('agreement_pass')} "
        f"pairs={terrain_gate.get('pair_count')}/{terrain_gate.get('expected_pair_count')} "
        f"max_abs_diff={terrain_gate.get('max_abs_araki_minus_umegaki')}"
    )
    swapped = terrain_gate.get("swapped_delta_control", {})
    print(
        "  swapped-delta control: "
        f"nonmatching={swapped.get('nonmatching')} "
        f"tested_nonzero_pairs={swapped.get('tested_nonzero_pairs')} "
        f"max_mismatch={swapped.get('max_abs_mismatch')}"
    )
    print(
        "  singular-sigma control: "
        f"flagged={result['gates']['singular_sigma_control']['flagged_ill_defined_without_regularization']} "
        f"epsilon_patch_used={result['gates']['singular_sigma_control']['epsilon_patch_used']}"
    )
    print(f"  scope boundary: {result['scope']['excluded']} -> {result['scope']['boundary_reason']}")
    print(f"VERDICT: {result['verdict']}")
    print("ALL_GATES:", "PASS" if result["all_pass"] else "FAIL", "->", RESULT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
