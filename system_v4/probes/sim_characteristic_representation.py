#!/usr/bin/env python3
"""
PURE LEGO: Characteristic Representation
========================================
Direct local state-representation lego using a discrete Pauli-label characteristic function.
"""

import json
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for characteristic-function state representation on bounded qubit "
    "states, kept separate from operator-coordinate, Bloch-vector, and density-matrix rows."
)

LEGO_IDS = [
    "characteristic_representation",
]

PRIMARY_LEGO_IDS = [
    "characteristic_representation",
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
PAULI_LABELS = {
    "I": I2,
    "X": SIGMA_X,
    "Y": SIGMA_Y,
    "Z": SIGMA_Z,
}


def ket(v):
    return np.array(v, dtype=complex).reshape(-1, 1)


def dm(v):
    v = np.array(v, dtype=complex).reshape(-1, 1)
    return v @ v.conj().T


def characteristic_function(rho):
    return {
        label: complex(np.trace(rho @ op))
        for label, op in PAULI_LABELS.items()
    }


def reconstruct_from_characteristic(chi):
    return 0.5 * (
        chi["I"] * I2
        + chi["X"] * SIGMA_X
        + chi["Y"] * SIGMA_Y
        + chi["Z"] * SIGMA_Z
    )


def close_matrix(a, b):
    return bool(np.allclose(a, b, atol=EPS))


def main():
    ket0 = ket([1, 0])
    ket1 = ket([0, 1])
    ketp = ket([1 / np.sqrt(2), 1 / np.sqrt(2)])
    ketm = ket([1 / np.sqrt(2), -1 / np.sqrt(2)])
    generic = ket([np.sqrt(0.7), np.sqrt(0.3) * np.exp(1j * 0.25)])

    rho_0 = dm(ket0)
    rho_1 = dm(ket1)
    rho_p = dm(ketp)
    rho_m = dm(ketm)
    rho_g = dm(generic)
    rho_mix = np.diag([0.7, 0.3]).astype(complex)

    chi_0 = characteristic_function(rho_0)
    chi_1 = characteristic_function(rho_1)
    chi_p = characteristic_function(rho_p)
    chi_m = characteristic_function(rho_m)
    chi_g = characteristic_function(rho_g)
    chi_mix = characteristic_function(rho_mix)

    positive = {
        "characteristic_values_reconstruct_density": {
            "pass": all(
                close_matrix(rho, reconstruct_from_characteristic(chi))
                for rho, chi in [
                    (rho_0, chi_0),
                    (rho_1, chi_1),
                    (rho_p, chi_p),
                    (rho_m, chi_m),
                    (rho_g, chi_g),
                    (rho_mix, chi_mix),
                ]
            ),
        },
        "identity_label_tracks_trace_one": {
            "values": {k: float(np.real(v["I"])) for k, v in {
                "rho_0": chi_0,
                "rho_1": chi_1,
                "rho_p": chi_p,
                "rho_mix": chi_mix,
            }.items()},
            "pass": all(abs(chi["I"] - 1.0) < EPS for chi in [chi_0, chi_1, chi_p, chi_mix]),
        },
        "basis_states_have_expected_label_pattern": {
            "rho_0": {k: float(np.real_if_close(v)) for k, v in chi_0.items()},
            "rho_1": {k: float(np.real_if_close(v)) for k, v in chi_1.items()},
            "pass": abs(chi_0["Z"] - 1.0) < EPS and abs(chi_1["Z"] + 1.0) < EPS,
        },
    }

    negative = {
        "same_trace_does_not_mean_same_characteristic_representation": {
            "pass": chi_0 != chi_p and chi_1 != chi_p,
        },
        "plus_and_minus_states_are_distinct_in_characteristic_view": {
            "pass": abs(chi_p["X"] - 1.0) < EPS and abs(chi_m["X"] + 1.0) < EPS,
        },
    }

    boundary = {
        "generic_phase_information_appears_in_y_label": {
            "value": float(np.real_if_close(chi_g["Y"])),
            "pass": abs(chi_g["Y"]) > EPS,
        },
        "diagonal_mixed_state_has_no_x_or_y_characteristic_component": {
            "pass": abs(chi_mix["X"]) < EPS and abs(chi_mix["Y"]) < EPS,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "characteristic_representation",
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
            "scope_note": "Direct local characteristic-function lego on bounded qubit pure and mixed states using Pauli-label evaluations.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "characteristic_representation_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
