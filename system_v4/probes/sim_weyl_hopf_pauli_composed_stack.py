#!/usr/bin/env python3
"""
Composed geometry stack: Weyl spinors + Pauli matrices + nested Hopf tori.

Stage order:
  1. Spinor construction on nested Hopf tori.
  2. Density matrices / Bloch vectors via Pauli relations.
  3. Nested torus transport and partial transport.
  4. Combined consistency checks across the full stack.

The row is intentionally bounded: it verifies the composed geometry carrier,
does not claim a full physical engine, and keeps the layer-by-layer checks
separate from the joint stack checks.
"""

from __future__ import annotations

import json
import math
import pathlib
from typing import Dict, List, Tuple

import numpy as np

from hopf_manifold import (
    NESTED_TORI,
    TORUS_CLIFFORD,
    TORUS_INNER,
    TORUS_OUTER,
    density_to_bloch,
    hopf_map,
    inter_torus_transport,
    inter_torus_transport_partial,
    left_density,
    left_weyl_spinor,
    right_density,
    right_weyl_spinor,
    sample_nested_torus,
    torus_coordinates,
    torus_radii,
)
from sim_pauli_algebra_relations import I2, X, Y, Z, anti_commutator, commutator


CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical composed geometry lego: nested Hopf tori, left/right Weyl spinors, "
    "Pauli/Bloch density checks, and transport consistency across stacked carriers."
)

LEGO_IDS = [
    "weyl_hopf_pauli_composed_stack",
]

PRIMARY_LEGO_IDS = [
    "weyl_hopf_pauli_composed_stack",
]

DEPENDENCIES = [
    "hopf_manifold",
    "sim_pauli_algebra_relations",
    "sim_weyl_hopf_tori",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed for this numpy stack"},
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

EPS = 1e-10
SAMPLE_RESOLUTION = 8
THETA_GRID = np.linspace(0.0, 2.0 * np.pi, SAMPLE_RESOLUTION, endpoint=False)
TORUS_LEVELS: List[Tuple[str, float]] = [
    ("inner", NESTED_TORI[0]),
    ("clifford", NESTED_TORI[1]),
    ("outer", NESTED_TORI[2]),
]


def stereographic_s3_to_r3(q: np.ndarray) -> np.ndarray:
    """Simple S^3 -> R^3 control embedding for a second geometry view."""
    a, b, c, d = q
    denom = 1.0 - d
    if abs(denom) < 1e-12:
        return np.array([1e6, 1e6, 1e6], dtype=float)
    scale = 1.0 / denom
    return np.array([a * scale, b * scale, c * scale], dtype=float)


def max_abs(x: np.ndarray) -> float:
    return float(np.max(np.abs(x))) if x.size else 0.0


def norm2(x: np.ndarray) -> float:
    return float(np.linalg.norm(x))


def build_samples() -> List[Dict[str, object]]:
    samples: List[Dict[str, object]] = []
    for level_name, eta in TORUS_LEVELS:
        for theta1 in THETA_GRID:
            for theta2 in THETA_GRID:
                q = torus_coordinates(eta, theta1, theta2)
                samples.append(
                    {
                        "level_name": level_name,
                        "eta": float(eta),
                        "theta1": float(theta1),
                        "theta2": float(theta2),
                        "q": q,
                    }
                )
    return samples


def stage_spinor_construction(samples: List[Dict[str, object]]) -> Dict[str, object]:
    max_left_norm_err = 0.0
    max_right_norm_err = 0.0
    max_overlap = 0.0
    max_right_relation_err = 0.0
    max_torus_identity_err = 0.0
    max_nested_cloud_norm_err = 0.0
    level_counts = {name: 0 for name, _ in TORUS_LEVELS}

    for _, eta in TORUS_LEVELS:
        cloud = sample_nested_torus(eta, 2, 2)
        if cloud.size:
            norms = np.linalg.norm(cloud, axis=1)
            max_nested_cloud_norm_err = max(max_nested_cloud_norm_err, max_abs(norms - 1.0))

    for sample in samples:
        q = sample["q"]
        eta = sample["eta"]
        L = left_weyl_spinor(q)
        R = right_weyl_spinor(q)

        max_left_norm_err = max(max_left_norm_err, abs(np.linalg.norm(L) - 1.0))
        max_right_norm_err = max(max_right_norm_err, abs(np.linalg.norm(R) - 1.0))
        max_overlap = max(max_overlap, abs(np.vdot(L, R)))
        max_right_relation_err = max(
            max_right_relation_err,
            norm2(R - (1j * Y) @ np.conj(L)),
        )

        r_major, r_minor = torus_radii(eta)
        max_torus_identity_err = max(
            max_torus_identity_err,
            abs((r_major ** 2 + r_minor ** 2) - 1.0),
        )
        level_counts[sample["level_name"]] += 1

    passed = (
        max_left_norm_err < 1e-10
        and max_right_norm_err < 1e-10
        and max_overlap < 1e-10
        and max_right_relation_err < 1e-10
        and max_torus_identity_err < 1e-10
    )

    return {
        "pass": passed,
        "sample_count": len(samples),
        "level_counts": level_counts,
        "max_left_norm_error": max_left_norm_err,
        "max_right_norm_error": max_right_norm_err,
        "max_left_right_overlap": max_overlap,
        "max_right_relation_error": max_right_relation_err,
        "max_torus_radius_identity_error": max_torus_identity_err,
        "max_nested_cloud_norm_error": max_nested_cloud_norm_err,
        "description": "Stage 1: construct left/right Weyl spinors directly on nested Hopf tori.",
    }


def stage_density_bloch_pauli(samples: List[Dict[str, object]]) -> Dict[str, object]:
    max_trace_error = 0.0
    max_purity_error = 0.0
    max_left_bloch_norm_err = 0.0
    max_right_bloch_norm_err = 0.0
    max_left_hopf_alignment_err = 0.0
    max_right_antipode_err = 0.0
    max_identity_neutral_error = 0.0
    max_pauli_commutator_error = 0.0
    max_pauli_anticommutator_error = 0.0

    for sample in samples:
        q = sample["q"]
        rho_L = left_density(q)
        rho_R = right_density(q)
        bloch_L = density_to_bloch(rho_L)
        bloch_R = density_to_bloch(rho_R)
        hopf = hopf_map(q)

        max_trace_error = max(
            max_trace_error,
            abs(np.trace(rho_L) - 1.0),
            abs(np.trace(rho_R) - 1.0),
        )
        max_purity_error = max(
            max_purity_error,
            abs(np.trace(rho_L @ rho_L) - 1.0),
            abs(np.trace(rho_R @ rho_R) - 1.0),
        )
        max_left_bloch_norm_err = max(max_left_bloch_norm_err, abs(np.linalg.norm(bloch_L) - 1.0))
        max_right_bloch_norm_err = max(max_right_bloch_norm_err, abs(np.linalg.norm(bloch_R) - 1.0))
        max_left_hopf_alignment_err = max(max_left_hopf_alignment_err, norm2(bloch_L - hopf))
        max_right_antipode_err = max(max_right_antipode_err, norm2(bloch_R + hopf))

    max_identity_neutral_error = max(
        max_identity_neutral_error,
        norm2(I2 @ X - X),
        norm2(X @ I2 - X),
        norm2(I2 @ Y - Y),
        norm2(Y @ I2 - Y),
        norm2(I2 @ Z - Z),
        norm2(Z @ I2 - Z),
    )
    max_pauli_commutator_error = max(
        max_pauli_commutator_error,
        norm2(commutator(X, Y) - 2j * Z),
        norm2(commutator(Y, Z) - 2j * X),
        norm2(commutator(Z, X) - 2j * Y),
    )
    max_pauli_anticommutator_error = max(
        max_pauli_anticommutator_error,
        norm2(anti_commutator(X, Y)),
        norm2(anti_commutator(Y, Z)),
        norm2(anti_commutator(Z, X)),
    )

    passed = (
        max_trace_error < 1e-10
        and max_purity_error < 1e-10
        and max_left_bloch_norm_err < 1e-10
        and max_right_bloch_norm_err < 1e-10
        and max_left_hopf_alignment_err < 1e-10
        and max_right_antipode_err < 1e-10
        and max_identity_neutral_error < 1e-10
        and max_pauli_commutator_error < 1e-10
        and max_pauli_anticommutator_error < 1e-10
    )

    return {
        "pass": passed,
        "max_trace_error": max_trace_error,
        "max_purity_error": max_purity_error,
        "max_left_bloch_norm_error": max_left_bloch_norm_err,
        "max_right_bloch_norm_error": max_right_bloch_norm_err,
        "max_left_hopf_alignment_error": max_left_hopf_alignment_err,
        "max_right_antipode_error": max_right_antipode_err,
        "max_identity_neutral_error": max_identity_neutral_error,
        "max_pauli_commutator_error": max_pauli_commutator_error,
        "max_pauli_anticommutator_error": max_pauli_anticommutator_error,
        "description": "Stage 2: map the spinors through density matrices, Bloch vectors, and Pauli algebra checks.",
    }


def stage_nested_transport(samples: List[Dict[str, object]]) -> Dict[str, object]:
    max_direct_transport_error = 0.0
    max_cycle_error = 0.0
    max_partial_alpha0_error = 0.0
    max_partial_alpha1_error = 0.0
    min_partial_midpoint_separation = float("inf")
    max_stereographic_nonfinite = 0
    transport_pairs = 0

    for sample in samples:
        eta = sample["eta"]
        theta1 = sample["theta1"]
        theta2 = sample["theta2"]
        q = sample["q"]

        level_index = [name for name, _ in TORUS_LEVELS].index(sample["level_name"])
        next_level_index = (level_index + 1) % len(TORUS_LEVELS)
        next_next_level_index = (level_index + 2) % len(TORUS_LEVELS)

        eta_next = TORUS_LEVELS[next_level_index][1]
        eta_next_next = TORUS_LEVELS[next_next_level_index][1]

        q_direct = torus_coordinates(eta_next, theta1, theta2)
        q_transport = inter_torus_transport(q, eta, eta_next)
        q_cycle = inter_torus_transport(
            inter_torus_transport(
                inter_torus_transport(q, eta, eta_next),
                eta_next,
                eta_next_next,
            ),
            eta_next_next,
            eta,
        )
        q_partial_0 = inter_torus_transport_partial(q, eta, eta_next, 0.0)
        q_partial_1 = inter_torus_transport_partial(q, eta, eta_next, 1.0)
        q_partial = inter_torus_transport_partial(q, eta, eta_next, 0.5)

        max_direct_transport_error = max(max_direct_transport_error, norm2(q_transport - q_direct))
        max_cycle_error = max(max_cycle_error, norm2(q_cycle - q))
        max_partial_alpha0_error = max(max_partial_alpha0_error, norm2(q_partial_0 - q))
        max_partial_alpha1_error = max(max_partial_alpha1_error, norm2(q_partial_1 - q_direct))
        min_partial_midpoint_separation = min(
            min_partial_midpoint_separation,
            min(norm2(q_partial - q), norm2(q_partial - q_direct)),
        )

        stereo = stereographic_s3_to_r3(q_transport)
        if not np.all(np.isfinite(stereo)):
            max_stereographic_nonfinite += 1
        transport_pairs += 1

    passed = (
        max_direct_transport_error < 1e-10
        and max_cycle_error < 1e-10
        and max_partial_alpha0_error < 1e-10
        and max_partial_alpha1_error < 1e-10
        and min_partial_midpoint_separation > 1e-12
        and max_stereographic_nonfinite == 0
    )

    return {
        "pass": passed,
        "transport_pairs": transport_pairs,
        "max_direct_transport_error": max_direct_transport_error,
        "max_cycle_error": max_cycle_error,
        "max_partial_alpha0_error": max_partial_alpha0_error,
        "max_partial_alpha1_error": max_partial_alpha1_error,
        "min_partial_midpoint_separation": min_partial_midpoint_separation,
        "nonfinite_stereographic_count": max_stereographic_nonfinite,
        "description": "Stage 3: move between nested tori and keep the geometry on a stable S^3 path.",
    }


def stage_combined_consistency(samples: List[Dict[str, object]]) -> Dict[str, object]:
    max_hopf_bloch_error = 0.0
    max_right_antipode_error = 0.0
    max_transport_then_bloch_error = 0.0
    max_stack_embedding_error = 0.0
    checked = 0

    for sample in samples:
        q = sample["q"]
        eta = sample["eta"]
        q_transport = inter_torus_transport(q, eta, eta)
        L = left_weyl_spinor(q_transport)
        R = right_weyl_spinor(q_transport)
        rho_L = left_density(q_transport)
        rho_R = right_density(q_transport)
        bloch_L = density_to_bloch(rho_L)
        bloch_R = density_to_bloch(rho_R)
        hopf = hopf_map(q_transport)
        stereo = stereographic_s3_to_r3(q_transport)

        max_hopf_bloch_error = max(max_hopf_bloch_error, norm2(bloch_L - hopf))
        max_right_antipode_error = max(max_right_antipode_error, norm2(bloch_R + hopf))
        max_transport_then_bloch_error = max(
            max_transport_then_bloch_error,
            abs(np.linalg.norm(L) - 1.0),
            abs(np.linalg.norm(R) - 1.0),
            abs(np.trace(rho_L) - 1.0),
            abs(np.trace(rho_R) - 1.0),
            abs(np.trace(rho_L @ rho_L) - 1.0),
            abs(np.trace(rho_R @ rho_R) - 1.0),
        )
        max_stack_embedding_error = max(
            max_stack_embedding_error,
            0.0 if np.all(np.isfinite(stereo)) else 1.0,
        )
        checked += 1

    passed = (
        max_hopf_bloch_error < 1e-10
        and max_right_antipode_error < 1e-10
        and max_transport_then_bloch_error < 1e-10
        and max_stack_embedding_error < 1e-12
    )

    return {
        "pass": passed,
        "checked_samples": checked,
        "max_hopf_bloch_error": max_hopf_bloch_error,
        "max_right_antipode_error": max_right_antipode_error,
        "max_transport_then_bloch_error": max_transport_then_bloch_error,
        "max_stack_embedding_error": max_stack_embedding_error,
        "description": "Stage 4: verify the full composed stack after transport, reconstruction, and alternate embedding views.",
    }


def run_negative_checks(samples: List[Dict[str, object]]) -> Dict[str, object]:
    q = samples[len(samples) // 2]["q"]
    eta = samples[len(samples) // 2]["eta"]
    eta_next = TORUS_CLIFFORD if abs(eta - TORUS_CLIFFORD) > 1e-12 else TORUS_OUTER
    transport_not_identity = norm2(inter_torus_transport(q, eta, eta_next) - q) > 1e-8
    wrong_pauli_sign_rejected = not np.allclose(X @ Y, -1j * Z, atol=EPS)
    left_right_not_same = norm2(left_density(q) - right_density(q)) > 1e-8

    return {
        "transport_not_identity": {"pass": transport_not_identity},
        "wrong_pauli_sign_rejected": {"pass": wrong_pauli_sign_rejected},
        "left_right_density_distinct": {"pass": left_right_not_same},
    }


def run_boundary_checks() -> Dict[str, object]:
    boundaries = {}
    for level_name, eta in TORUS_LEVELS:
        r_major, r_minor = torus_radii(eta)
        boundaries[f"{level_name}_radius_identity"] = {
            "pass": abs((r_major ** 2 + r_minor ** 2) - 1.0) < 1e-10,
            "r_major": r_major,
            "r_minor": r_minor,
        }
    return boundaries


def main() -> None:
    samples = build_samples()
    positive = {
        "spinor_construction": stage_spinor_construction(samples),
        "density_bloch_pauli": stage_density_bloch_pauli(samples),
        "nested_transport": stage_nested_transport(samples),
        "combined_consistency": stage_combined_consistency(samples),
    }
    negative = run_negative_checks(samples)
    boundary = run_boundary_checks()

    positive_pass = all(v["pass"] for v in positive.values())
    negative_pass = all(v["pass"] for v in negative.values())
    boundary_pass = all(v["pass"] for v in boundary.values())
    all_pass = positive_pass and negative_pass and boundary_pass

    results = {
        "name": "weyl_hopf_pauli_composed_stack",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "dependencies": DEPENDENCIES,
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "positive_pass": positive_pass,
            "negative_pass": negative_pass,
            "boundary_pass": boundary_pass,
            "sample_count": len(samples),
            "torus_levels": [name for name, _ in TORUS_LEVELS],
            "total_stages": 4,
            "max_spinor_norm_error": max(
                positive["spinor_construction"]["max_left_norm_error"],
                positive["spinor_construction"]["max_right_norm_error"],
            ),
            "max_bloch_alignment_error": max(
                positive["density_bloch_pauli"]["max_left_hopf_alignment_error"],
                positive["density_bloch_pauli"]["max_right_antipode_error"],
            ),
            "max_transport_error": max(
                positive["nested_transport"]["max_direct_transport_error"],
                positive["nested_transport"]["max_cycle_error"],
            ),
            "max_stack_error": max(
                positive["combined_consistency"]["max_hopf_bloch_error"],
                positive["combined_consistency"]["max_right_antipode_error"],
            ),
            "scope_note": "Bounded composed geometry stack for nested Hopf tori, Weyl spinors, Pauli/Bloch consistency, and transport closures.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "weyl_hopf_pauli_composed_stack_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))

    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")
    print(
        "SUMMARY:",
        {
            "sample_count": len(samples),
            "max_spinor_norm_error": results["summary"]["max_spinor_norm_error"],
            "max_bloch_alignment_error": results["summary"]["max_bloch_alignment_error"],
            "max_transport_error": results["summary"]["max_transport_error"],
            "max_stack_error": results["summary"]["max_stack_error"],
        },
    )


if __name__ == "__main__":
    main()
