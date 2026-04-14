#!/usr/bin/env python3
"""
PURE LEGO: Commutator Algebra
=============================
Direct local bracket-structure lego on the qubit Pauli generators.
"""

import json
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for commutator algebra on the qubit Pauli generators, kept "
    "separate from the basis row, full Pauli algebra bundle, and later gauge/falsifier work."
)

LEGO_IDS = [
    "commutator_algebra",
]

PRIMARY_LEGO_IDS = [
    "commutator_algebra",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed for this bracket-structure row"},
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


def commutator(a, b):
    return a @ b - b @ a


def anti_commutator(a, b):
    return a @ b + b @ a


def close(a, b):
    return bool(np.allclose(a, b, atol=EPS))


def main():
    c_xy = commutator(SX, SY)
    c_yz = commutator(SY, SZ)
    c_zx = commutator(SZ, SX)

    positive = {
        "basic_pauli_commutators_match_expected_closure": {
            "pass": close(c_xy, 2j * SZ) and close(c_yz, 2j * SX) and close(c_zx, 2j * SY),
        },
        "identity_commutes_with_generators": {
            "pass": close(commutator(I2, SX), np.zeros((2, 2), dtype=complex))
            and close(commutator(I2, SY), np.zeros((2, 2), dtype=complex))
            and close(commutator(I2, SZ), np.zeros((2, 2), dtype=complex)),
        },
        "commutator_of_generators_stays_in_generator_span": {
            "pass": close(c_xy / (2j), SZ) and close(c_yz / (2j), SX) and close(c_zx / (2j), SY),
        },
    }

    negative = {
        "generators_are_not_pairwise_commuting": {
            "pass": np.linalg.norm(c_xy) > EPS and np.linalg.norm(c_yz) > EPS and np.linalg.norm(c_zx) > EPS,
        },
        "anticommutator_differs_from_commutator": {
            "pass": not close(commutator(SX, SY), anti_commutator(SX, SY)),
        },
    }

    boundary = {
        "self_commutators_vanish": {
            "pass": close(commutator(SX, SX), np.zeros((2, 2), dtype=complex))
            and close(commutator(SY, SY), np.zeros((2, 2), dtype=complex))
            and close(commutator(SZ, SZ), np.zeros((2, 2), dtype=complex)),
        },
        "jacobi_identity_holds": {
            "value": commutator(SX, commutator(SY, SZ))
            + commutator(SY, commutator(SZ, SX))
            + commutator(SZ, commutator(SX, SY)),
            "pass": close(
                commutator(SX, commutator(SY, SZ))
                + commutator(SY, commutator(SZ, SX))
                + commutator(SZ, commutator(SX, SY)),
                np.zeros((2, 2), dtype=complex),
            ),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "commutator_algebra",
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
            "scope_note": "Direct local commutator-algebra lego on the qubit Pauli generators.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "commutator_algebra_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
