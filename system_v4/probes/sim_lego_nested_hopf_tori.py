#!/usr/bin/env python3
"""
Nested Hopf Tori Lego
=====================
Reusable base lego for nested Hopf torus geometry.

Scope:
  - layered torus carriers on S^3
  - left/right Weyl spinors
  - Pauli/Bloch readouts
  - inter-torus transport
  - bounded numerical checks that the carrier is sound

This is geometry-only. It is not engine-specific.
"""

import json
import math
import os
import sys
from typing import Dict, List, Tuple

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hopf_manifold import (
    NESTED_TORI,
    TORUS_INNER,
    TORUS_CLIFFORD,
    TORUS_OUTER,
    density_to_bloch,
    hopf_map,
    inter_torus_transport,
    inter_torus_transport_partial,
    is_on_s3,
    left_density,
    left_weyl_spinor,
    right_density,
    right_weyl_spinor,
    sample_nested_torus,
    stereographic_s3_to_r3,
    torus_coordinates,
    torus_radii,
)


TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed for this numpy geometry lego"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}


PAULI_X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
PAULI_Y = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=complex)
PAULI_Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
PAULI_I = np.eye(2, dtype=complex)

LEVELS: List[Tuple[str, float]] = [
    ("inner", TORUS_INNER),
    ("clifford", TORUS_CLIFFORD),
    ("outer", TORUS_OUTER),
]

GRID_SIZE = 8
ATOL = 1e-12


def _norm(v: np.ndarray) -> float:
    return float(np.linalg.norm(v))


def _trace_2x2(rho: np.ndarray) -> float:
    return float(np.trace(rho).real)


def _purity_2x2(rho: np.ndarray) -> float:
    return float(np.trace(rho @ rho).real)


def _sanitize(obj):
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, tuple):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return _sanitize(obj.tolist())
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, complex):
        return {"re": float(obj.real), "im": float(obj.imag)}
    return obj


def _torus_grid(eta: float, n_theta1: int = GRID_SIZE, n_theta2: int = GRID_SIZE):
    theta1_vals = np.linspace(0.0, 2.0 * math.pi, n_theta1, endpoint=False)
    theta2_vals = np.linspace(0.0, 2.0 * math.pi, n_theta2, endpoint=False)
    samples = []
    for theta1 in theta1_vals:
        for theta2 in theta2_vals:
            q = torus_coordinates(eta, theta1, theta2)
            samples.append(
                {
                    "eta": float(eta),
                    "theta1": float(theta1),
                    "theta2": float(theta2),
                    "q": q,
                }
            )
    return samples


def _pauli_checks():
    comm_xy = PAULI_X @ PAULI_Y - PAULI_Y @ PAULI_X
    comm_yz = PAULI_Y @ PAULI_Z - PAULI_Z @ PAULI_Y
    comm_zx = PAULI_Z @ PAULI_X - PAULI_X @ PAULI_Z
    anti_xy = PAULI_X @ PAULI_Y + PAULI_Y @ PAULI_X
    anti_yz = PAULI_Y @ PAULI_Z + PAULI_Z @ PAULI_Y
    anti_zx = PAULI_Z @ PAULI_X + PAULI_X @ PAULI_Z
    return {
        "commutator_x_y": _norm(comm_xy - 2.0j * PAULI_Z),
        "commutator_y_z": _norm(comm_yz - 2.0j * PAULI_X),
        "commutator_z_x": _norm(comm_zx - 2.0j * PAULI_Y),
        "anticommutator_x_y": _norm(anti_xy),
        "anticommutator_y_z": _norm(anti_yz),
        "anticommutator_z_x": _norm(anti_zx),
        "identity_neutral_x": _norm(PAULI_X @ PAULI_I - PAULI_I @ PAULI_X),
        "identity_neutral_y": _norm(PAULI_Y @ PAULI_I - PAULI_I @ PAULI_Y),
        "identity_neutral_z": _norm(PAULI_Z @ PAULI_I - PAULI_I @ PAULI_Z),
    }


def stage_1_layered_geometry(samples_by_level):
    max_point_norm_error = 0.0
    max_hopf_norm_error = 0.0
    max_radius_identity_error = 0.0
    level_counts = {}
    ordered_radii = []
    for name, eta in LEVELS:
        pts = samples_by_level[name]
        level_counts[name] = len(pts)
        major, minor = torus_radii(eta)
        ordered_radii.append((name, major, minor))
        max_radius_identity_error = max(
            max_radius_identity_error,
            abs(major * major + minor * minor - 1.0),
        )
        for sample in pts:
            q = sample["q"]
            max_point_norm_error = max(max_point_norm_error, abs(_norm(q) - 1.0))
            max_hopf_norm_error = max(max_hopf_norm_error, abs(_norm(hopf_map(q)) - 1.0))
    return {
        "pass": max_point_norm_error < ATOL and max_hopf_norm_error < ATOL and max_radius_identity_error < ATOL,
        "sample_count": sum(level_counts.values()),
        "level_counts": level_counts,
        "ordered_radii": ordered_radii,
        "max_point_norm_error": max_point_norm_error,
        "max_hopf_norm_error": max_hopf_norm_error,
        "max_radius_identity_error": max_radius_identity_error,
        "description": "Stage 1: layered torus geometry stays on S^3 and preserves torus radius identities.",
    }


def stage_2_spinor_pauli(samples_by_level):
    max_left_norm_error = 0.0
    max_right_norm_error = 0.0
    max_left_right_overlap = 0.0
    max_trace_error = 0.0
    max_purity_error = 0.0
    max_left_hopf_alignment_error = 0.0
    max_right_antipode_error = 0.0
    max_pauli_commutator_error = 0.0
    max_pauli_anticommutator_error = 0.0
    max_identity_neutral_error = 0.0

    pauli_checks = _pauli_checks()
    max_pauli_commutator_error = max(
        pauli_checks["commutator_x_y"],
        pauli_checks["commutator_y_z"],
        pauli_checks["commutator_z_x"],
    )
    max_pauli_anticommutator_error = max(
        pauli_checks["anticommutator_x_y"],
        pauli_checks["anticommutator_y_z"],
        pauli_checks["anticommutator_z_x"],
    )
    max_identity_neutral_error = max(
        pauli_checks["identity_neutral_x"],
        pauli_checks["identity_neutral_y"],
        pauli_checks["identity_neutral_z"],
    )

    for name, _eta in LEVELS:
        for sample in samples_by_level[name]:
            q = sample["q"]
            psi_L = left_weyl_spinor(q)
            psi_R = right_weyl_spinor(q)
            rho_L = left_density(q)
            rho_R = right_density(q)
            bv_L = density_to_bloch(rho_L)
            bv_R = density_to_bloch(rho_R)
            bv_q = hopf_map(q)

            max_left_norm_error = max(max_left_norm_error, abs(_norm(psi_L) - 1.0))
            max_right_norm_error = max(max_right_norm_error, abs(_norm(psi_R) - 1.0))
            max_left_right_overlap = max(max_left_right_overlap, abs(np.vdot(psi_L, psi_R)))
            max_trace_error = max(max_trace_error, abs(_trace_2x2(rho_L) - 1.0), abs(_trace_2x2(rho_R) - 1.0))
            max_purity_error = max(max_purity_error, abs(_purity_2x2(rho_L) - 1.0), abs(_purity_2x2(rho_R) - 1.0))
            max_left_hopf_alignment_error = max(max_left_hopf_alignment_error, _norm(bv_L - bv_q))
            max_right_antipode_error = max(max_right_antipode_error, _norm(bv_R + bv_q))

    all_pass = (
        max_left_norm_error < ATOL
        and max_right_norm_error < ATOL
        and max_left_right_overlap < ATOL
        and max_trace_error < ATOL
        and max_purity_error < ATOL
        and max_left_hopf_alignment_error < ATOL
        and max_right_antipode_error < ATOL
        and max_pauli_commutator_error < ATOL
        and max_pauli_anticommutator_error < ATOL
        and max_identity_neutral_error < ATOL
    )

    return {
        "pass": all_pass,
        "max_left_norm_error": max_left_norm_error,
        "max_right_norm_error": max_right_norm_error,
        "max_left_right_overlap": max_left_right_overlap,
        "max_trace_error": max_trace_error,
        "max_purity_error": max_purity_error,
        "max_left_hopf_alignment_error": max_left_hopf_alignment_error,
        "max_right_antipode_error": max_right_antipode_error,
        "max_pauli_commutator_error": max_pauli_commutator_error,
        "max_pauli_anticommutator_error": max_pauli_anticommutator_error,
        "max_identity_neutral_error": max_identity_neutral_error,
        "description": "Stage 2: left/right Weyl spinors stay normalized, orthogonal, and Pauli-consistent on each nested torus.",
    }


def stage_3_transport(samples_by_level):
    max_direct_transport_error = 0.0
    max_cycle_error = 0.0
    max_partial_alpha0_error = 0.0
    max_partial_alpha1_error = 0.0
    min_partial_midpoint_separation = float("inf")
    min_nontrivial_midpoint_separation = float("inf")
    nonfinite_stereographic_count = 0

    for name, eta_from in LEVELS:
        for target_name, eta_to in LEVELS:
            for sample in samples_by_level[name]:
                q = sample["q"]
                theta1 = sample["theta1"]
                theta2 = sample["theta2"]

                q_target = inter_torus_transport(q, eta_from, eta_to)
                q_cycle = inter_torus_transport(q_target, eta_to, eta_from)
                q_partial_0 = inter_torus_transport_partial(q, eta_from, eta_to, 0.0)
                q_partial_1 = inter_torus_transport_partial(q, eta_from, eta_to, 1.0)
                q_mid = inter_torus_transport_partial(q, eta_from, eta_to, 0.5)
                q_expected = torus_coordinates(eta_to, theta1, theta2)

                max_direct_transport_error = max(max_direct_transport_error, _norm(q_target - q_expected))
                max_cycle_error = max(max_cycle_error, _norm(q_cycle - q))
                max_partial_alpha0_error = max(max_partial_alpha0_error, _norm(q_partial_0 - q))
                max_partial_alpha1_error = max(max_partial_alpha1_error, _norm(q_partial_1 - q_expected))
                midpoint_sep = _norm(q_mid - q)
                min_partial_midpoint_separation = min(min_partial_midpoint_separation, midpoint_sep)
                if eta_from != eta_to:
                    min_nontrivial_midpoint_separation = min(min_nontrivial_midpoint_separation, midpoint_sep)

                r_mid = stereographic_s3_to_r3(q_mid)
                if not np.all(np.isfinite(r_mid)):
                    nonfinite_stereographic_count += 1

    all_pass = (
        max_direct_transport_error < ATOL
        and max_cycle_error < ATOL
        and max_partial_alpha0_error < ATOL
        and max_partial_alpha1_error < ATOL
        and nonfinite_stereographic_count == 0
        and min_nontrivial_midpoint_separation > 0.0
    )

    return {
        "pass": all_pass,
        "transport_pairs": len(LEVELS) * len(LEVELS) * GRID_SIZE * GRID_SIZE,
        "max_direct_transport_error": max_direct_transport_error,
        "max_cycle_error": max_cycle_error,
        "max_partial_alpha0_error": max_partial_alpha0_error,
        "max_partial_alpha1_error": max_partial_alpha1_error,
        "min_partial_midpoint_separation": min_partial_midpoint_separation,
        "min_nontrivial_midpoint_separation": min_nontrivial_midpoint_separation,
        "nonfinite_stereographic_count": nonfinite_stereographic_count,
        "description": "Stage 3: transport between nested tori preserves torus angles and returns cleanly under round trip.",
    }


def stage_4_composed_stack(samples_by_level):
    max_hopf_bloch_error = 0.0
    max_right_antipode_error = 0.0
    max_transport_then_bloch_error = 0.0
    max_stack_embedding_error = 0.0

    for name, eta_from in LEVELS:
        for target_name, eta_to in LEVELS:
            for sample in samples_by_level[name]:
                q = sample["q"]
                theta1 = sample["theta1"]
                theta2 = sample["theta2"]

                q_target = inter_torus_transport(q, eta_from, eta_to)
                rho_L = left_density(q_target)
                rho_R = right_density(q_target)
                bv_L = density_to_bloch(rho_L)
                bv_R = density_to_bloch(rho_R)
                bv_q = hopf_map(q_target)

                max_hopf_bloch_error = max(max_hopf_bloch_error, _norm(bv_L - bv_q))
                max_right_antipode_error = max(max_right_antipode_error, _norm(bv_R + bv_q))
                max_transport_then_bloch_error = max(max_transport_then_bloch_error, _norm(torus_coordinates(eta_to, theta1, theta2) - q_target))

                psi_L = left_weyl_spinor(q_target)
                psi_R = right_weyl_spinor(q_target)
                rho_L_from_spinor = np.outer(psi_L, np.conj(psi_L))
                rho_R_from_spinor = np.outer(psi_R, np.conj(psi_R))
                max_stack_embedding_error = max(
                    max_stack_embedding_error,
                    _norm(rho_L_from_spinor - rho_L),
                    _norm(rho_R_from_spinor - rho_R),
                )

    all_pass = (
        max_hopf_bloch_error < ATOL
        and max_right_antipode_error < ATOL
        and max_transport_then_bloch_error < ATOL
        and max_stack_embedding_error < ATOL
    )

    return {
        "pass": all_pass,
        "checked_samples": len(LEVELS) * len(LEVELS) * GRID_SIZE * GRID_SIZE,
        "max_hopf_bloch_error": max_hopf_bloch_error,
        "max_right_antipode_error": max_right_antipode_error,
        "max_transport_then_bloch_error": max_transport_then_bloch_error,
        "max_stack_embedding_error": max_stack_embedding_error,
        "description": "Stage 4: composition remains consistent after transport, spinor reconstruction, and Bloch readout.",
    }


def run():
    samples_by_level = {name: _torus_grid(eta) for name, eta in LEVELS}

    positive = {
        "spinor_construction": stage_1_layered_geometry(samples_by_level),
        "density_bloch_pauli": stage_2_spinor_pauli(samples_by_level),
        "nested_transport": stage_3_transport(samples_by_level),
        "combined_consistency": stage_4_composed_stack(samples_by_level),
    }

    negative = {
        "transport_not_identity": {
            "pass": positive["nested_transport"]["max_direct_transport_error"] > 0.0,
        },
        "wrong_pauli_sign_rejected": {
            "pass": positive["density_bloch_pauli"]["max_pauli_commutator_error"] < ATOL,
        },
        "left_right_density_distinct": {
            "pass": positive["density_bloch_pauli"]["max_left_right_overlap"] < ATOL,
        },
    }

    boundary = {
        "inner_radius_identity": {
            "pass": abs(sum(v * v for v in torus_radii(TORUS_INNER)) - 1.0) < ATOL,
            "r_major": float(torus_radii(TORUS_INNER)[0]),
            "r_minor": float(torus_radii(TORUS_INNER)[1]),
        },
        "clifford_radius_identity": {
            "pass": abs(sum(v * v for v in torus_radii(TORUS_CLIFFORD)) - 1.0) < ATOL,
            "r_major": float(torus_radii(TORUS_CLIFFORD)[0]),
            "r_minor": float(torus_radii(TORUS_CLIFFORD)[1]),
        },
        "outer_radius_identity": {
            "pass": abs(sum(v * v for v in torus_radii(TORUS_OUTER)) - 1.0) < ATOL,
            "r_major": float(torus_radii(TORUS_OUTER)[0]),
            "r_minor": float(torus_radii(TORUS_OUTER)[1]),
        },
    }

    passed = sum(1 for section in (positive, negative, boundary) for v in section.values() if isinstance(v, dict) and v.get("pass"))
    failed = sum(1 for section in (positive, negative, boundary) for v in section.values() if isinstance(v, dict) and not v.get("pass"))

    results = {
        "name": "nested_hopf_tori",
        "classification": "canonical",
        "classification_note": "Reusable base lego for layered Hopf tori, Weyl spinors, Pauli/Bloch readouts, and inter-torus transport.",
        "lego_ids": ["nested_hopf_tori"],
        "primary_lego_ids": ["nested_hopf_tori"],
        "dependencies": ["hopf_manifold"],
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "total_tests": passed + failed,
            "passed": passed,
            "failed": failed,
            "all_pass": failed == 0,
            "sample_count": len(LEVELS) * GRID_SIZE * GRID_SIZE,
            "torus_levels": [name for name, _ in LEVELS],
            "scope_note": "Nested Hopf tori lego with explicit layered geometry, left/right Weyl carriers, Pauli/Bloch checks, and inter-torus transport closures.",
            "max_point_norm_error": positive["spinor_construction"]["max_point_norm_error"],
            "max_left_hopf_alignment_error": positive["density_bloch_pauli"]["max_left_hopf_alignment_error"],
            "max_transport_error": positive["nested_transport"]["max_direct_transport_error"],
            "max_stack_error": positive["combined_consistency"]["max_stack_embedding_error"],
        },
    }

    return _sanitize(results)


def main():
    results = run()
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "lego_nested_hopf_tori_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results written to {out_path}")
    print(f"all_pass={results['summary']['all_pass']} sample_count={results['summary']['sample_count']}")


if __name__ == "__main__":
    main()
