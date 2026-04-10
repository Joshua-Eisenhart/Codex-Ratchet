#!/usr/bin/env python3
"""
PURE LEGO: Sphere Geometry
==========================
Direct local sphere-geometry lego on one admitted qubit carrier.
"""

import json
import pathlib

import numpy as np


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for sphere geometry on a one-qubit carrier via Bloch-sphere embedding, "
    "kept separate from Hopf fiber, torus nesting, Berry phase, and transport rows."
)

LEGO_IDS = [
    "sphere_geometry",
]

PRIMARY_LEGO_IDS = [
    "sphere_geometry",
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

SX = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
SY = np.array([[0.0, -1j], [1j, 0.0]], dtype=complex)
SZ = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)


def dm(v):
    vec = np.array(v, dtype=complex).reshape(-1, 1)
    return vec @ vec.conj().T


def bloch_vector(rho):
    return np.array(
        [
            float(np.real(np.trace(rho @ SX))),
            float(np.real(np.trace(rho @ SY))),
            float(np.real(np.trace(rho @ SZ))),
        ]
    )


def geodesic_distance(u, v):
    uu = u / np.linalg.norm(u)
    vv = v / np.linalg.norm(v)
    cosang = float(np.clip(np.dot(uu, vv), -1.0, 1.0))
    return float(np.arccos(cosang))


def main():
    ket0 = dm([1.0, 0.0])
    ket1 = dm([0.0, 1.0])
    ket_plus = dm([1.0 / np.sqrt(2.0), 1.0 / np.sqrt(2.0)])
    ket_minus = dm([1.0 / np.sqrt(2.0), -1.0 / np.sqrt(2.0)])
    ket_plus_i = dm([1.0 / np.sqrt(2.0), 1j / np.sqrt(2.0)])

    v0 = bloch_vector(ket0)
    v1 = bloch_vector(ket1)
    v_plus = bloch_vector(ket_plus)
    v_minus = bloch_vector(ket_minus)
    v_plus_i = bloch_vector(ket_plus_i)

    positive = {
        "pure_qubit_states_embed_on_unit_sphere": {
            "pass": all(
                abs(np.linalg.norm(v) - 1.0) < EPS
                for v in [v0, v1, v_plus, v_minus, v_plus_i]
            ),
        },
        "orthogonal_basis_states_map_to_antipodes": {
            "pass": np.allclose(v1, -v0, atol=EPS) and np.allclose(v_minus, -v_plus, atol=EPS),
        },
        "geodesic_distances_match_expected_local_angles": {
            "d_0_plus": geodesic_distance(v0, v_plus),
            "d_plus_plus_i": geodesic_distance(v_plus, v_plus_i),
            "pass": abs(geodesic_distance(v0, v_plus) - (np.pi / 2.0)) < 1e-8
            and abs(geodesic_distance(v_plus, v_plus_i) - (np.pi / 2.0)) < 1e-8,
        },
    }

    negative = {
        "nonantipodal_distinct_states_are_not_collapsed": {
            "pass": not np.allclose(v0, v_plus, atol=EPS) and not np.allclose(v_plus, v_plus_i, atol=EPS),
        },
        "sphere_local_data_collapses_global_phase_information": {
            "pass": np.allclose(
                v_plus,
                bloch_vector(
                    dm(
                        [
                            np.exp(1j * 0.37) / np.sqrt(2.0),
                            np.exp(1j * 0.37) / np.sqrt(2.0),
                        ]
                    )
                ),
                atol=1e-8,
            ),
        },
    }

    boundary = {
        "bloch_coordinates_stay_in_real_three_space": {
            "pass": all(np.all(np.isreal(v)) for v in [v0, v1, v_plus, v_minus, v_plus_i]),
        },
        "identical_states_have_zero_geodesic_distance": {
            "pass": abs(geodesic_distance(v0, v0)) < EPS and abs(geodesic_distance(v_plus, v_plus)) < EPS,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "sphere_geometry",
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
            "scope_note": "Direct local sphere-geometry lego on one qubit carrier via Bloch-sphere embedding and local geodesic checks.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "sphere_geometry_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
