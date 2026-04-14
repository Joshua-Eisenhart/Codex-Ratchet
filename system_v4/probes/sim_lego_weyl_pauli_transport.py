#!/usr/bin/env python3
"""
PURE LEGO: Weyl + Pauli Transport on Nested Hopf Tori
======================================================
Reusable base lego for left/right Weyl spinors, Pauli readouts, and
transport across nested Hopf tori.

This probe stays finite and bounded:
  - sample a small grid of torus points
  - read out left/right Weyl spinors and Pauli projections
  - transport between inner / Clifford / outer tori
  - verify roundtrips, chirality separation, and Pauli algebra

Classification: canonical when all checks pass.
"""

from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
classification = "classical_baseline"  # auto-backfill

PROBE_DIR = pathlib.Path(__file__).resolve().parent
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

import hopf_manifold as hopf
import sim_pauli_algebra_relations as pauli


CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Reusable Weyl/Hopf/Pauli transport lego for nested torus geometry. "
    "It exposes left/right spinor readouts, Pauli projections, transport "
    "roundtrips, and bounded negative controls without making runtime engine claims."
)

LEGO_IDS = [
    "weyl_pauli_transport",
    "hopf_torus_lego",
    "pauli_algebra_relations",
]

PRIMARY_LEGO_IDS = [
    "hopf_torus_lego",
    "pauli_algebra_relations",
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

EPS = 1e-10
SAMPLE_THETA_PAIRS = [
    (0.11, 0.37),
    (0.43, 1.07),
    (0.89, 1.71),
    (1.23, 2.19),
    (1.87, 2.61),
    (2.41, 3.17),
]

INNER_ETA = hopf.TORUS_INNER
CLIFFORD_ETA = hopf.TORUS_CLIFFORD
OUTER_ETA = hopf.TORUS_OUTER
TORUS_LEVELS = [
    ("inner", INNER_ETA),
    ("clifford", CLIFFORD_ETA),
    ("outer", OUTER_ETA),
]


def pauli_expectations(rho: np.ndarray) -> dict:
    return {
        "x": float(np.real(np.trace(rho @ pauli.X))),
        "y": float(np.real(np.trace(rho @ pauli.Y))),
        "z": float(np.real(np.trace(rho @ pauli.Z))),
    }


def spinor_packet(q: np.ndarray) -> dict:
    psi_l = hopf.left_weyl_spinor(q)
    psi_r = hopf.right_weyl_spinor(q)
    rho_l = hopf.left_density(q)
    rho_r = hopf.right_density(q)
    bloch_l = hopf.density_to_bloch(rho_l)
    bloch_r = hopf.density_to_bloch(rho_r)
    hopf_image = hopf.hopf_map(q)
    stereo = hopf.stereographic_s3_to_r3(q)

    return {
        "q_norm": float(np.linalg.norm(q)),
        "left_norm": float(np.linalg.norm(psi_l)),
        "right_norm": float(np.linalg.norm(psi_r)),
        "left_right_overlap_abs": float(abs(np.vdot(psi_l, psi_r))),
        "left_bloch": bloch_l.tolist(),
        "right_bloch": bloch_r.tolist(),
        "bloch_antipodal_gap": float(np.linalg.norm(bloch_l + bloch_r)),
        "chiral_z_gap": float(abs(float(bloch_l[2]) - float(bloch_r[2]))),
        "hopf_image_norm_gap": float(abs(np.linalg.norm(hopf_image) - 1.0)),
        "stereographic_finite": bool(np.all(np.isfinite(stereo))),
        "stereographic_norm": float(np.linalg.norm(stereo)),
        "pauli_left": pauli_expectations(rho_l),
        "pauli_right": pauli_expectations(rho_r),
    }


def build_sample_records() -> list[dict]:
    records = []
    for level_name, eta in TORUS_LEVELS:
        radii = hopf.torus_radii(eta)
        for theta1, theta2 in SAMPLE_THETA_PAIRS:
            q = hopf.torus_coordinates(eta, theta1, theta2)
            packet = spinor_packet(q)
            packet.update(
                {
                    "level": level_name,
                    "eta": float(eta),
                    "theta1": float(theta1),
                    "theta2": float(theta2),
                    "major_radius": float(radii[0]),
                    "minor_radius": float(radii[1]),
                }
            )
            records.append(packet)
    return records


def build_transport_records() -> list[dict]:
    source = hopf.torus_coordinates(INNER_ETA, 0.43, 1.07)
    source_back = hopf.torus_coordinates(CLIFFORD_ETA, 0.43, 1.07)
    transport_pairs = [
        ("inner_to_clifford", INNER_ETA, CLIFFORD_ETA),
        ("inner_to_outer", INNER_ETA, OUTER_ETA),
        ("clifford_to_outer", CLIFFORD_ETA, OUTER_ETA),
    ]

    records = []
    for label, eta_from, eta_to in transport_pairs:
        base = source if eta_from == INNER_ETA else source_back
        q_target = hopf.inter_torus_transport(base, eta_from, eta_to)
        q_roundtrip = hopf.inter_torus_transport(q_target, eta_to, eta_from)
        q_partial = hopf.inter_torus_transport_partial(base, eta_from, eta_to, 0.5)

        records.append(
            {
                "label": label,
                "eta_from": float(eta_from),
                "eta_to": float(eta_to),
                "source_norm": float(np.linalg.norm(base)),
                "target_norm": float(np.linalg.norm(q_target)),
                "roundtrip_error": float(np.linalg.norm(q_roundtrip - base)),
                "partial_midpoint_separation": float(np.linalg.norm(q_partial - base)),
                "partial_midpoint_finite": bool(np.all(np.isfinite(q_partial))),
                "source_bloch": hopf.density_to_bloch(hopf.left_density(base)).tolist(),
                "target_bloch": hopf.density_to_bloch(hopf.left_density(q_target)).tolist(),
            }
        )

    return records


def prove_pauli_algebra() -> dict:
    positive = {
        "cyclic_multiplication_relations_hold": bool(
            np.allclose(pauli.X @ pauli.Y, 1j * pauli.Z, atol=EPS)
            and np.allclose(pauli.Y @ pauli.Z, 1j * pauli.X, atol=EPS)
            and np.allclose(pauli.Z @ pauli.X, 1j * pauli.Y, atol=EPS)
        ),
        "generator_squares_equal_identity": bool(
            np.allclose(pauli.X @ pauli.X, pauli.I2, atol=EPS)
            and np.allclose(pauli.Y @ pauli.Y, pauli.I2, atol=EPS)
            and np.allclose(pauli.Z @ pauli.Z, pauli.I2, atol=EPS)
        ),
        "commutator_relations_match_pauli_algebra": bool(
            np.allclose(pauli.commutator(pauli.X, pauli.Y), 2j * pauli.Z, atol=EPS)
            and np.allclose(pauli.commutator(pauli.Y, pauli.Z), 2j * pauli.X, atol=EPS)
            and np.allclose(pauli.commutator(pauli.Z, pauli.X), 2j * pauli.Y, atol=EPS)
        ),
    }

    negative = {
        "wrong_sign_relation_is_rejected": bool(
            not np.allclose(pauli.X @ pauli.Y, -1j * pauli.Z, atol=EPS)
        ),
        "distinct_generators_anticommutator_vanishes": bool(
            np.allclose(
                pauli.anti_commutator(pauli.X, pauli.Y),
                np.zeros((2, 2), dtype=complex),
                atol=EPS,
            )
        ),
    }

    boundary = {
        "identity_is_two_sided_multiplicative_neutral": bool(
            all(
                np.allclose(pauli.I2 @ a, a, atol=EPS) and np.allclose(a @ pauli.I2, a, atol=EPS)
                for a in [pauli.X, pauli.Y, pauli.Z]
            )
        ),
        "generator_products_close_in_pauli_set_up_to_phase": bool(
            all(
                any(
                    np.allclose(a @ b, c, atol=EPS)
                    for c in [
                        pauli.I2,
                        -pauli.I2,
                        1j * pauli.X,
                        -1j * pauli.X,
                        1j * pauli.Y,
                        -1j * pauli.Y,
                        1j * pauli.Z,
                        -1j * pauli.Z,
                    ]
                )
                for a in [pauli.X, pauli.Y, pauli.Z]
                for b in [pauli.X, pauli.Y, pauli.Z]
            )
        ),
    }

    return {
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
    }


def run_positive_tests() -> dict:
    sample_records = build_sample_records()
    transport_records = build_transport_records()
    pauli_checks = prove_pauli_algebra()

    max_q_norm_gap = max(abs(row["q_norm"] - 1.0) for row in sample_records)
    max_left_norm_gap = max(abs(row["left_norm"] - 1.0) for row in sample_records)
    max_right_norm_gap = max(abs(row["right_norm"] - 1.0) for row in sample_records)
    max_left_right_overlap = max(row["left_right_overlap_abs"] for row in sample_records)
    max_bloch_gap = max(row["bloch_antipodal_gap"] for row in sample_records)
    max_chiral_z_gap = max(row["chiral_z_gap"] for row in sample_records)
    max_hopf_gap = max(row["hopf_image_norm_gap"] for row in sample_records)
    all_stereo_finite = all(row["stereographic_finite"] for row in sample_records)
    pauli_readout_gap_left = max(
        max(
            abs(row["pauli_left"][axis] - row["left_bloch"][idx])
            for idx, axis in enumerate(["x", "y", "z"])
        )
        for row in sample_records
    )
    pauli_readout_gap_right = max(
        max(
            abs(row["pauli_right"][axis] - row["right_bloch"][idx])
            for idx, axis in enumerate(["x", "y", "z"])
        )
        for row in sample_records
    )
    pauli_readout_gap = max(pauli_readout_gap_left, pauli_readout_gap_right)
    transport_roundtrip_error = max(row["roundtrip_error"] for row in transport_records)
    transport_partial_separation = min(row["partial_midpoint_separation"] for row in transport_records)
    transport_partial_finite = all(row["partial_midpoint_finite"] for row in transport_records)

    torus_major = [hopf.torus_radii(eta)[0] for _, eta in TORUS_LEVELS]
    torus_minor = [hopf.torus_radii(eta)[1] for _, eta in TORUS_LEVELS]
    radii_monotone = bool(
        torus_major[0] > torus_major[1] > torus_major[2]
        and torus_minor[0] < torus_minor[1] < torus_minor[2]
    )

    return {
        "sample_records": sample_records,
        "transport_records": transport_records,
        "max_q_norm_gap": max_q_norm_gap,
        "max_left_norm_gap": max_left_norm_gap,
        "max_right_norm_gap": max_right_norm_gap,
        "max_left_right_overlap_abs": max_left_right_overlap,
        "max_bloch_antipodal_gap": max_bloch_gap,
        "max_chiral_z_gap": max_chiral_z_gap,
        "max_hopf_image_norm_gap": max_hopf_gap,
        "all_stereographic_finite": all_stereo_finite,
        "pauli_readout_gap": pauli_readout_gap,
        "transport_roundtrip_error": transport_roundtrip_error,
        "transport_partial_midpoint_separation": transport_partial_separation,
        "transport_partial_finite": transport_partial_finite,
        "torus_major_radii": torus_major,
        "torus_minor_radii": torus_minor,
        "radii_monotone": radii_monotone,
        "pauli_checks": pauli_checks,
    }


def run_negative_tests() -> dict:
    wrong_chirality_identification = any(
        row["bloch_antipodal_gap"] > 1e-6 for row in build_sample_records()
    )
    wrong_transport_identity = any(
        row["roundtrip_error"] > 1e-6 for row in build_transport_records()
    )

    return {
        "wrong_chirality_identification_is_rejected": {
            "pass": bool(not wrong_chirality_identification),
            "description": "Left and right Bloch readouts should stay antipodal, not identical.",
        },
        "wrong_transport_identity_is_rejected": {
            "pass": bool(not wrong_transport_identity),
            "description": "Torus transport should roundtrip back to the source to machine precision.",
        },
        "wrong_sign_relation_is_rejected": {
            "pass": bool(prove_pauli_algebra()["negative"]["wrong_sign_relation_is_rejected"]),
            "description": "The Pauli product X Y = -i Z should not be accepted.",
        },
    }


def run_boundary_tests() -> dict:
    boundary_cases = {
        "eta_0_north_pole": 0.0,
        "eta_pi4_clifford_torus": np.pi / 4,
        "eta_pi2_south_pole": np.pi / 2,
    }
    records = {}
    for label, eta in boundary_cases.items():
        q = hopf.torus_coordinates(eta, 0.43, 1.07)
        packet = spinor_packet(q)
        records[label] = {
            "eta": float(eta),
            "q_norm": packet["q_norm"],
            "left_norm": packet["left_norm"],
            "right_norm": packet["right_norm"],
            "max_bloch_antipodal_gap": packet["bloch_antipodal_gap"],
            "max_hopf_image_norm_gap": packet["hopf_image_norm_gap"],
            "stereographic_finite": packet["stereographic_finite"],
        }

    all_pass = all(
        abs(row["q_norm"] - 1.0) < EPS
        and abs(row["left_norm"] - 1.0) < EPS
        and abs(row["right_norm"] - 1.0) < EPS
        and row["max_hopf_image_norm_gap"] < 1e-8
        and row["stereographic_finite"]
        for row in records.values()
    )

    return {
        "cases": records,
        "pass": bool(all_pass),
    }


def main():
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    all_pass = (
        positive["max_q_norm_gap"] < 1e-10
        and positive["max_left_norm_gap"] < 1e-10
        and positive["max_right_norm_gap"] < 1e-10
        and positive["max_left_right_overlap_abs"] < 1e-10
        and positive["max_bloch_antipodal_gap"] < 1e-10
        and positive["max_chiral_z_gap"] > 1e-6
        and positive["max_hopf_image_norm_gap"] < 1e-10
        and positive["all_stereographic_finite"]
        and positive["pauli_readout_gap"] < 1e-10
        and positive["transport_roundtrip_error"] < 1e-10
        and positive["transport_partial_midpoint_separation"] > 1e-6
        and positive["transport_partial_finite"]
        and positive["radii_monotone"]
        and all(v["pass"] for v in negative.values())
        and boundary["pass"]
        and all(positive["pauli_checks"]["positive"].values())
        and all(positive["pauli_checks"]["negative"].values())
        and all(positive["pauli_checks"]["boundary"].values())
    )

    results = {
        "name": "lego_weyl_pauli_transport",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "scope_note": (
                "Reusable Weyl/Hopf/Pauli transport lego on nested torus geometry with "
                "bounded sample grids, transport roundtrips, and Pauli-algebra checks."
            ),
            "sample_count": len(positive["sample_records"]),
            "transport_count": len(positive["transport_records"]),
            "torus_levels": [name for name, _ in TORUS_LEVELS],
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "lego_weyl_pauli_transport_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
