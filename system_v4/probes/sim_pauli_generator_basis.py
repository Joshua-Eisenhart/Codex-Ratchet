#!/usr/bin/env python3
"""
PURE LEGO: Pauli Generator Basis
================================
Direct local operator-basis lego on the qubit Pauli generators.
"""

import json
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for the Pauli generator basis on a qubit carrier, kept separate "
    "from full algebra relations, Bloch decomposition maps, and operator-action rows."
)

LEGO_IDS = [
    "pauli_generator_basis",
]

PRIMARY_LEGO_IDS = [
    "pauli_generator_basis",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed for this basis-identification row"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

I2 = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=complex)
SX = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
SY = np.array([[0.0, -1j], [1j, 0.0]], dtype=complex)
SZ = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)


def hs_inner(a, b):
    return np.trace(a.conj().T @ b)


def matrix_rank_from_vecs(mats):
    stacked = np.stack([m.reshape(-1) for m in mats], axis=1)
    return int(np.linalg.matrix_rank(stacked))


def main():
    basis = {"I": I2, "X": SX, "Y": SY, "Z": SZ}
    counterfeit = {"I": I2, "X": SX, "Y": SX, "Z": SZ}

    positive = {
        "all_basis_elements_are_hermitian": {
            "pass": all(np.allclose(m, m.conj().T, atol=EPS) for m in basis.values()),
        },
        "trace_structure_matches_pauli_basis": {
            "traces": {k: complex(np.trace(v)) for k, v in basis.items()},
            "pass": abs(np.trace(I2) - 2.0) < EPS
            and all(abs(np.trace(m)) < EPS for k, m in basis.items() if k != "I"),
        },
        "hilbert_schmidt_orthogonality_holds": {
            "pass": all(
                abs(hs_inner(a, b)) < EPS
                for ka, a in basis.items()
                for kb, b in basis.items()
                if ka != kb
            ),
        },
    }

    negative = {
        "linear_independence_gives_full_operator_space_rank": {
            "rank": matrix_rank_from_vecs(list(basis.values())),
            "pass": matrix_rank_from_vecs(list(basis.values())) == 4,
        },
        "counterfeit_basis_is_rejected": {
            "counterfeit_rank": matrix_rank_from_vecs(list(counterfeit.values())),
            "pass": matrix_rank_from_vecs(list(counterfeit.values())) < 4,
        },
    }

    boundary = {
        "nonidentity_generators_are_exactly_three": {
            "pass": len([k for k in basis if k != "I"]) == 3,
        },
        "generator_squares_equal_identity": {
            "pass": all(np.allclose(m @ m, I2, atol=EPS) for k, m in basis.items() if k != "I"),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "pauli_generator_basis",
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
            "scope_note": "Direct local Pauli-basis lego on {I, X, Y, Z} as the qubit operator basis.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "pauli_generator_basis_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
