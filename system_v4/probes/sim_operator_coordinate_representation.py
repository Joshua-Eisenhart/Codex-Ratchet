#!/usr/bin/env python3
"""
PURE LEGO: Operator-Coordinate Representation
=============================================
Direct local state-representation lego using Pauli operator coordinates.
"""

import json
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for operator-coordinate state representation on bounded qubit "
    "states, kept separate from Bloch-vector, Stokes, and generic density-object rows."
)

LEGO_IDS = [
    "operator_coordinate_representation",
]

PRIMARY_LEGO_IDS = [
    "operator_coordinate_representation",
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

I2 = np.eye(2, dtype=complex)
SIGMA_X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
SIGMA_Y = np.array([[0.0, -1j], [1j, 0.0]], dtype=complex)
SIGMA_Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
PAULI_BASIS = [I2, SIGMA_X, SIGMA_Y, SIGMA_Z]


def ket(v):
    return np.array(v, dtype=complex).reshape(-1, 1)


def dm(v):
    v = np.array(v, dtype=complex).reshape(-1, 1)
    return v @ v.conj().T


def operator_coordinates(rho):
    return np.array(
        [0.5 * np.trace(rho @ basis) for basis in PAULI_BASIS],
        dtype=complex,
    )


def reconstruct_from_coordinates(coords):
    return sum(coords[i] * PAULI_BASIS[i] for i in range(4))


def matrix_close(a, b):
    return bool(np.allclose(a, b, atol=EPS))


def main():
    ket0 = ket([1, 0])
    ket1 = ket([0, 1])
    ketp = ket([1 / np.sqrt(2), 1 / np.sqrt(2)])
    pure_generic = ket([np.sqrt(0.7), np.sqrt(0.3) * np.exp(1j * 0.4)])

    rho_0 = dm(ket0)
    rho_1 = dm(ket1)
    rho_p = dm(ketp)
    rho_g = dm(pure_generic)
    rho_m = np.array([[0.7, 0.0], [0.0, 0.3]], dtype=complex)

    c0 = operator_coordinates(rho_0)
    c1 = operator_coordinates(rho_1)
    cp = operator_coordinates(rho_p)
    cg = operator_coordinates(rho_g)
    cm = operator_coordinates(rho_m)

    positive = {
        "coordinates_reconstruct_density_exactly": {
            "pass": all(
                matrix_close(rho, reconstruct_from_coordinates(coords))
                for rho, coords in [
                    (rho_0, c0),
                    (rho_1, c1),
                    (rho_p, cp),
                    (rho_g, cg),
                    (rho_m, cm),
                ]
            ),
        },
        "computational_basis_states_have_expected_z_coordinate": {
            "rho_0_coords": [float(np.real_if_close(x)) for x in c0],
            "rho_1_coords": [float(np.real_if_close(x)) for x in c1],
            "pass": abs(c0[0] - 0.5) < EPS and abs(c0[3] - 0.5) < EPS and abs(c1[3] + 0.5) < EPS,
        },
        "plus_state_has_expected_x_coordinate": {
            "rho_plus_coords": [float(np.real_if_close(x)) for x in cp],
            "pass": abs(cp[1] - 0.5) < EPS and abs(cp[2]) < EPS and abs(cp[3]) < EPS,
        },
    }

    negative = {
        "distinct_states_do_not_share_same_coordinates": {
            "pass": not np.allclose(c0, cp, atol=EPS) and not np.allclose(c1, cp, atol=EPS),
        },
        "mixed_diagonal_state_is_not_pure_state_coordinate_pattern": {
            "pass": abs(cm[1]) < EPS and abs(cm[2]) < EPS and abs(cm[3] - 0.2) < EPS,
        },
    }

    boundary = {
        "identity_coordinate_is_fixed_at_one_half_for_trace_one_states": {
            "pass": all(abs(coords[0] - 0.5) < EPS for coords in [c0, c1, cp, cg, cm]),
        },
        "generic_state_needs_y_coordinate_for_phase_information": {
            "coords": [float(np.real_if_close(x)) for x in cg],
            "pass": abs(cg[2]) > EPS,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "operator_coordinate_representation",
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
            "scope_note": "Direct local operator-coordinate lego on bounded qubit pure and mixed states using the Pauli operator basis.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "operator_coordinate_representation_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
