#!/usr/bin/env python3
"""
PURE LEGO: Pauli Algebra Relations
==================================
Direct local algebra-relations lego on the qubit Pauli generators.
"""

import json
import pathlib

import numpy as np


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for Pauli multiplication and commutation relations on the qubit "
    "carrier, kept separate from basis rows, local operator action, and broader operator bundles."
)

LEGO_IDS = [
    "pauli_algebra_relations",
]

PRIMARY_LEGO_IDS = [
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

I2 = np.eye(2, dtype=complex)
X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
Y = np.array([[0.0, -1j], [1j, 0.0]], dtype=complex)
Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)


def close(a, b):
    return bool(np.allclose(a, b, atol=EPS))


def commutator(a, b):
    return a @ b - b @ a


def anti_commutator(a, b):
    return a @ b + b @ a


def main():
    positive = {
        "cyclic_multiplication_relations_hold": {
            "pass": close(X @ Y, 1j * Z) and close(Y @ Z, 1j * X) and close(Z @ X, 1j * Y),
        },
        "generator_squares_equal_identity": {
            "pass": close(X @ X, I2) and close(Y @ Y, I2) and close(Z @ Z, I2),
        },
        "commutator_relations_match_pauli_algebra": {
            "pass": close(commutator(X, Y), 2j * Z)
            and close(commutator(Y, Z), 2j * X)
            and close(commutator(Z, X), 2j * Y),
        },
    }

    negative = {
        "anticommutators_of_distinct_generators_vanish": {
            "pass": close(anti_commutator(X, Y), np.zeros((2, 2), dtype=complex))
            and close(anti_commutator(Y, Z), np.zeros((2, 2), dtype=complex))
            and close(anti_commutator(Z, X), np.zeros((2, 2), dtype=complex)),
        },
        "wrong_sign_relation_is_rejected": {
            "pass": not close(X @ Y, -1j * Z),
        },
    }

    boundary = {
        "identity_is_two_sided_multiplicative_neutral": {
            "pass": all(close(I2 @ a, a) and close(a @ I2, a) for a in [X, Y, Z]),
        },
        "generator_products_close_in_pauli_set_up_to_phase": {
            "pass": all(
                any(close(a @ b, c) for c in [I2, -I2, 1j * X, -1j * X, 1j * Y, -1j * Y, 1j * Z, -1j * Z])
                for a in [X, Y, Z]
                for b in [X, Y, Z]
            ),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "pauli_algebra_relations",
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
            "scope_note": "Direct local Pauli-algebra lego covering multiplication and commutation identities on the qubit carrier.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "pauli_algebra_relations_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
