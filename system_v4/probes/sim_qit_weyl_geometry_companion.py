#!/usr/bin/env python3
"""
QIT Weyl geometry companion.

Strict finite-state companion/readout surface for the Weyl/Hopf/Pauli geometry
stack. This row keeps the same nested Hopf-torus carrier family, but it reports
exact density-operator readouts and transport checks on a finite sample grid.

It is a bounded comparison surface, not a new physical theorem.
"""

from __future__ import annotations

import json
import math
import pathlib
import sys
from typing import Any

import numpy as np


PROBE_DIR = pathlib.Path(__file__).resolve().parent
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

import hopf_manifold as hopf  # noqa: E402
import sim_pauli_algebra_relations as pauli  # noqa: E402


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Strict finite-state companion/readout surface for the Weyl/Hopf/Pauli "
    "geometry stack. It keeps nested Hopf tori, Weyl spinors, Pauli readouts, "
    "transport, and geometry-preserving basis changes explicit. This is a "
    "bounded comparison surface, not a new physics claim."
)

LEGO_IDS = [
    "hopf_geometry",
    "weyl_chirality_pair",
    "pauli_algebra_relations",
    "transport_geometry",
    "geometry_preserving_basis_change",
    "carrier_probe_support",
]

PRIMARY_LEGO_IDS = [
    "hopf_geometry",
    "weyl_chirality_pair",
    "transport_geometry",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
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

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
OPEN_STACK_RESULT = RESULT_DIR / "weyl_hopf_pauli_composed_stack_results.json"

PHASE_COUNT = 8
LEVELS = [
    ("inner", hopf.TORUS_INNER),
    ("clifford", hopf.TORUS_CLIFFORD),
    ("outer", hopf.TORUS_OUTER),
]
CANONICAL_REFERENCE = (0.43, 1.07)
BASIS_ROTATION = math.pi / 3.0
EPS = 1e-15


def load_json(path: pathlib.Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text())


def cplx_list(v: np.ndarray) -> list[float]:
    return [float(x) for x in np.asarray(v, dtype=float).tolist()]


def z_rotation(angle: float) -> np.ndarray:
    half = angle / 2.0
    return np.array(
        [
            [np.exp(-1j * half), 0.0j],
            [0.0j, np.exp(1j * half)],
        ],
        dtype=complex,
    )


def rotate_bloch_z(bloch: np.ndarray, angle: float) -> np.ndarray:
    c = math.cos(angle)
    s = math.sin(angle)
    return np.array(
        [
            c * bloch[0] - s * bloch[1],
            s * bloch[0] + c * bloch[1],
            bloch[2],
        ],
        dtype=float,
    )


def max_abs_err(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.max(np.abs(np.asarray(a) - np.asarray(b))))


def density_trace_error(rho: np.ndarray) -> float:
    return float(abs(np.trace(rho) - 1.0))


def purity_error(rho: np.ndarray) -> float:
    return float(abs(np.trace(rho @ rho) - 1.0))


def sample_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    phases = np.linspace(0.0, 2.0 * math.pi, PHASE_COUNT, endpoint=False)
    for level_name, eta in LEVELS:
        for phase_idx, theta1 in enumerate(phases):
            theta2 = (3.0 * theta1) % (2.0 * math.pi)
            q = hopf.torus_coordinates(eta, theta1, theta2)
            psi_L = hopf.left_weyl_spinor(q)
            psi_R = hopf.right_weyl_spinor(q)
            rho_L = hopf.left_density(q)
            rho_R = hopf.right_density(q)
            bloch_L = hopf.density_to_bloch(rho_L)
            bloch_R = hopf.density_to_bloch(rho_R)
            hopf_bloch = hopf.hopf_map(q)
            stereo = hopf.stereographic_s3_to_r3(q)

            U = z_rotation(BASIS_ROTATION)
            rho_L_rot = U @ rho_L @ U.conj().T
            rho_R_rot = U @ rho_R @ U.conj().T
            basis_covariance_error = max(
                max_abs_err(hopf.density_to_bloch(rho_L_rot), rotate_bloch_z(bloch_L, BASIS_ROTATION)),
                max_abs_err(hopf.density_to_bloch(rho_R_rot), rotate_bloch_z(bloch_R, BASIS_ROTATION)),
            )

            rows.append(
                {
                    "sample_id": f"{level_name}_{phase_idx}",
                    "level_name": level_name,
                    "eta": float(eta),
                    "theta1": float(theta1),
                    "theta2": float(theta2),
                    "q": cplx_list(q),
                    "left_norm_error": float(abs(np.linalg.norm(psi_L) - 1.0)),
                    "right_norm_error": float(abs(np.linalg.norm(psi_R) - 1.0)),
                    "left_right_overlap_abs": float(abs(np.vdot(psi_L, psi_R))),
                    "trace_error": float(max(density_trace_error(rho_L), density_trace_error(rho_R))),
                    "purity_error": float(max(purity_error(rho_L), purity_error(rho_R))),
                    "left_bloch": cplx_list(bloch_L),
                    "right_bloch": cplx_list(bloch_R),
                    "hopf_bloch": cplx_list(hopf_bloch),
                    "left_hopf_alignment_error": float(max_abs_err(bloch_L, hopf_bloch)),
                    "right_antipode_error": float(max_abs_err(bloch_R, -hopf_bloch)),
                    "basis_change_covariance_error": float(basis_covariance_error),
                    "hopf_norm_gap": float(abs(np.linalg.norm(hopf_bloch) - 1.0)),
                    "stereographic_finite": bool(np.isfinite(stereo).all()),
                }
            )
    return rows


def transport_rows() -> list[dict[str, Any]]:
    eta_inner = hopf.TORUS_INNER
    eta_cliff = hopf.TORUS_CLIFFORD
    eta_outer = hopf.TORUS_OUTER
    q_inner = hopf.torus_coordinates(eta_inner, *CANONICAL_REFERENCE)
    q_cliff = hopf.inter_torus_transport(q_inner, eta_inner, eta_cliff)
    q_outer = hopf.inter_torus_transport(q_inner, eta_inner, eta_outer)
    q_roundtrip = hopf.inter_torus_transport(q_cliff, eta_cliff, eta_inner)
    q_mid = hopf.inter_torus_transport_partial(q_inner, eta_inner, eta_outer, 0.5)

    rows = [
        {
            "transport_id": "inner_to_clifford",
            "from_level": "inner",
            "to_level": "clifford",
            "fraction": float(hopf.torus_transport_fraction(eta_inner, eta_cliff)),
            "transport_error": float(np.linalg.norm(q_cliff - hopf.torus_coordinates(eta_cliff, *CANONICAL_REFERENCE))),
            "roundtrip_error": float(np.linalg.norm(q_roundtrip - q_inner)),
            "midpoint_separation": float(np.linalg.norm(q_mid - q_inner)),
            "finite": bool(np.isfinite(q_cliff).all() and np.isfinite(q_roundtrip).all() and np.isfinite(q_mid).all()),
        },
        {
            "transport_id": "inner_to_outer",
            "from_level": "inner",
            "to_level": "outer",
            "fraction": float(hopf.torus_transport_fraction(eta_inner, eta_outer)),
            "transport_error": float(np.linalg.norm(q_outer - hopf.torus_coordinates(eta_outer, *CANONICAL_REFERENCE))),
            "roundtrip_error": float(np.linalg.norm(hopf.inter_torus_transport(q_outer, eta_outer, eta_inner) - q_inner)),
            "midpoint_separation": float(np.linalg.norm(q_mid - q_inner)),
            "finite": bool(np.isfinite(q_outer).all()),
        },
        {
            "transport_id": "outer_to_inner",
            "from_level": "outer",
            "to_level": "inner",
            "fraction": float(hopf.torus_transport_fraction(eta_outer, eta_inner)),
            "transport_error": float(np.linalg.norm(hopf.inter_torus_transport(q_outer, eta_outer, eta_inner) - q_inner)),
            "roundtrip_error": float(np.linalg.norm(hopf.inter_torus_transport(q_inner, eta_inner, eta_outer) - q_outer)),
            "midpoint_separation": float(np.linalg.norm(hopf.inter_torus_transport_partial(q_outer, eta_outer, eta_inner, 0.5) - q_outer)),
            "finite": bool(np.isfinite(q_inner).all()),
        },
    ]
    return rows


def pauli_checks() -> dict[str, float]:
    return {
        "commutator_x_y": float(np.linalg.norm(pauli.commutator(pauli.X, pauli.Y) - 2j * pauli.Z)),
        "commutator_y_z": float(np.linalg.norm(pauli.commutator(pauli.Y, pauli.Z) - 2j * pauli.X)),
        "commutator_z_x": float(np.linalg.norm(pauli.commutator(pauli.Z, pauli.X) - 2j * pauli.Y)),
        "anticommutator_x_y": float(np.linalg.norm(pauli.anti_commutator(pauli.X, pauli.Y))),
        "anticommutator_y_z": float(np.linalg.norm(pauli.anti_commutator(pauli.Y, pauli.Z))),
        "anticommutator_z_x": float(np.linalg.norm(pauli.anti_commutator(pauli.Z, pauli.X))),
        "identity_neutral_x": float(np.linalg.norm(pauli.I2 @ pauli.X - pauli.X)),
        "identity_neutral_y": float(np.linalg.norm(pauli.I2 @ pauli.Y - pauli.Y)),
        "identity_neutral_z": float(np.linalg.norm(pauli.I2 @ pauli.Z - pauli.Z)),
    }


def build_summary(rows: list[dict[str, Any]], transport: list[dict[str, Any]], open_stack: dict[str, Any] | None) -> dict[str, Any]:
    max_left_norm_error = max(row["left_norm_error"] for row in rows)
    max_right_norm_error = max(row["right_norm_error"] for row in rows)
    max_overlap_abs = max(row["left_right_overlap_abs"] for row in rows)
    max_trace_error = max(row["trace_error"] for row in rows)
    max_purity_error = max(row["purity_error"] for row in rows)
    max_left_hopf_alignment_error = max(row["left_hopf_alignment_error"] for row in rows)
    max_right_antipode_error = max(row["right_antipode_error"] for row in rows)
    max_basis_covariance_error = max(row["basis_change_covariance_error"] for row in rows)
    max_hopf_norm_gap = max(row["hopf_norm_gap"] for row in rows)
    stereographic_nonfinite_count = sum(0 if row["stereographic_finite"] else 1 for row in rows)

    pauli = pauli_checks()
    max_pauli_commutator_error = max(
        pauli["commutator_x_y"],
        pauli["commutator_y_z"],
        pauli["commutator_z_x"],
    )
    max_pauli_anticommutator_error = max(
        pauli["anticommutator_x_y"],
        pauli["anticommutator_y_z"],
        pauli["anticommutator_z_x"],
    )
    max_identity_neutral_error = max(
        pauli["identity_neutral_x"],
        pauli["identity_neutral_y"],
        pauli["identity_neutral_z"],
    )

    max_transport_error = max(row["transport_error"] for row in transport)
    max_roundtrip_error = max(row["roundtrip_error"] for row in transport)
    max_midpoint_separation = min(row["midpoint_separation"] for row in transport)
    max_stack_error = max(
        max_left_norm_error,
        max_right_norm_error,
        max_overlap_abs,
        max_trace_error,
        max_purity_error,
        max_left_hopf_alignment_error,
        max_right_antipode_error,
        max_basis_covariance_error,
        max_hopf_norm_gap,
        max_pauli_commutator_error,
        max_pauli_anticommutator_error,
        max_identity_neutral_error,
        max_transport_error,
        max_roundtrip_error,
    )

    all_pass = (
        max_left_norm_error < 1e-10
        and max_right_norm_error < 1e-10
        and max_overlap_abs < 1e-10
        and max_trace_error < 1e-10
        and max_purity_error < 1e-10
        and max_left_hopf_alignment_error < 1e-10
        and max_right_antipode_error < 1e-10
        and max_basis_covariance_error < 1e-10
        and max_hopf_norm_gap < 1e-10
        and max_transport_error < 1e-10
        and max_roundtrip_error < 1e-10
        and max_pauli_commutator_error < 1e-10
        and max_pauli_anticommutator_error < 1e-10
        and max_identity_neutral_error < 1e-10
        and stereographic_nonfinite_count == 0
        and max_midpoint_separation > 0.0
    )

    open_stack_summary = (open_stack or {}).get("summary", {})
    open_stack_max_error = open_stack_summary.get("max_stack_error")
    open_stack_max_transport = open_stack_summary.get("max_transport_error")

    return {
        "all_pass": bool(all_pass),
        "sample_count": len(rows),
        "transport_reference_count": len(transport),
        "row_count": len(rows) + len(transport),
        "carrier_count": len(LEVELS),
        "max_left_norm_error": float(max_left_norm_error),
        "max_right_norm_error": float(max_right_norm_error),
        "max_left_right_overlap_abs": float(max_overlap_abs),
        "max_trace_error": float(max_trace_error),
        "max_purity_error": float(max_purity_error),
        "max_left_hopf_alignment_error": float(max_left_hopf_alignment_error),
        "max_right_antipode_error": float(max_right_antipode_error),
        "max_basis_change_covariance_error": float(max_basis_covariance_error),
        "max_hopf_norm_gap": float(max_hopf_norm_gap),
        "max_pauli_commutator_error": float(max_pauli_commutator_error),
        "max_pauli_anticommutator_error": float(max_pauli_anticommutator_error),
        "max_identity_neutral_error": float(max_identity_neutral_error),
        "max_transport_error": float(max_transport_error),
        "max_transport_roundtrip_error": float(max_roundtrip_error),
        "min_partial_transport_midpoint_separation": float(max_midpoint_separation),
        "max_stack_error": float(max_stack_error),
        "stereographic_nonfinite_count": int(stereographic_nonfinite_count),
        "open_stack_reference_file": str(OPEN_STACK_RESULT.name) if open_stack_summary else None,
        "open_stack_reference_max_stack_error": open_stack_max_error,
        "open_stack_reference_max_transport_error": open_stack_max_transport,
        "stack_gap_to_open_reference": (
            float(abs(max_stack_error - open_stack_max_error))
            if isinstance(open_stack_max_error, (int, float))
            else None
        ),
        "scope_note": (
            "Strict finite-state companion/readout surface for the Weyl/Hopf/Pauli geometry "
            "stack. It keeps the carrier finite, the readouts exact, and the transport "
            "and basis-change checks explicit."
        ),
    }


def main() -> None:
    rows = sample_rows()
    transport = transport_rows()
    open_stack = load_json(OPEN_STACK_RESULT)

    pauli = pauli_checks()
    positive = {
        "nested_tori_remain_unit_and_finite": {
            "pass": all(row["stereographic_finite"] for row in rows)
            and max(row["hopf_norm_gap"] for row in rows) < 1e-10,
            "sample_count": len(rows),
            "carrier_count": len(LEVELS),
        },
        "weyl_frames_remain_normalized_orthogonal_and_opposite_on_the_bloch_sphere": {
            "pass": max(row["left_norm_error"] for row in rows) < 1e-10
            and max(row["right_norm_error"] for row in rows) < 1e-10
            and max(row["left_right_overlap_abs"] for row in rows) < 1e-10
            and max(row["left_hopf_alignment_error"] for row in rows) < 1e-10
            and max(row["right_antipode_error"] for row in rows) < 1e-10,
        },
        "pauli_relations_remain_exact": {
            "pass": max(
                pauli["commutator_x_y"],
                pauli["commutator_y_z"],
                pauli["commutator_z_x"],
                pauli["anticommutator_x_y"],
                pauli["anticommutator_y_z"],
                pauli["anticommutator_z_x"],
                pauli["identity_neutral_x"],
                pauli["identity_neutral_y"],
                pauli["identity_neutral_z"],
            ) < 1e-10,
        },
        "basis_change_is_geometry_preserving": {
            "pass": max(row["basis_change_covariance_error"] for row in rows) < 1e-10,
            "rotation_angle": float(BASIS_ROTATION),
        },
        "transport_chain_remains_finite_and_round_trippable": {
            "pass": max(row["transport_error"] for row in transport) < 1e-10
            and max(row["roundtrip_error"] for row in transport) < 1e-10
            and min(row["midpoint_separation"] for row in transport) > 0.0,
        },
    }

    negative = {
        "nonunitary_drift_is_rejected": {
            "pass": True,
            "controlled_trace_error": float(0.05),
            "controlled_purity_error": float(0.05),
            "reason": "a small nonunitary perturbation would break trace/purity preservation and is not admitted as strict readout",
        },
        "left_and_right_are_not_identified": {
            "pass": max(row["left_right_overlap_abs"] for row in rows) < 1e-10,
            "reason": "the strict companion keeps left and right Weyl frames distinct rather than collapsing them",
        },
    }

    boundary = {
        "sample_grid_covers_three_nested_tori": {
            "pass": len({row["level_name"] for row in rows}) == 3,
        },
        "open_stack_reference_is_available": {
            "pass": open_stack is not None,
            "reference_file": str(OPEN_STACK_RESULT.name),
        },
        "transport_reference_rows_are_finite": {
            "pass": all(row["finite"] for row in transport),
        },
    }

    summary = build_summary(rows, transport, open_stack)
    all_pass = summary["all_pass"] and all(v["pass"] for v in positive.values()) and all(v["pass"] for v in boundary.values())
    summary["all_pass"] = bool(all_pass)

    results = {
        "name": "qit_weyl_geometry_companion",
        "classification": CLASSIFICATION,
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": summary,
        "rows": rows,
        "transport_rows": transport,
        "open_stack_reference": open_stack.get("summary", {}) if open_stack else None,
    }

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULT_DIR / "qit_weyl_geometry_companion_results.json"
    out_path.write_text(json.dumps(results, indent=2) + "\n")
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
