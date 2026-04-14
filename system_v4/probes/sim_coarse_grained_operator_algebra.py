#!/usr/bin/env python3
"""
PURE LEGO: Coarse-Grained Operator Algebra
==========================================
Direct local algebra lego using partial-trace coarse-graining from two qubits to one qubit.
"""

import json
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for coarse-grained operator algebra via bounded two-qubit to one-qubit "
    "partial-trace coarse-graining, kept separate from broad ML analogy bundles."
)

LEGO_IDS = [
    "coarse_grained_operator_algebra",
]

PRIMARY_LEGO_IDS = [
    "coarse_grained_operator_algebra",
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


def coarse_grain_B(op_ab, dim_a=2, dim_b=2):
    op = op_ab.reshape(dim_a, dim_b, dim_a, dim_b)
    traced = np.trace(op, axis1=1, axis2=3)
    return traced / dim_b


def commutator(a, b):
    return a @ b - b @ a


def close(a, b):
    return bool(np.allclose(a, b, atol=EPS))


def main():
    a_x = np.kron(X, I2)
    a_y = np.kron(Y, I2)
    a_z = np.kron(Z, I2)
    entangling = np.kron(X, X)
    mixed_term = np.kron(X, I2) + 0.5 * np.kron(I2, Z)

    cg_x = coarse_grain_B(a_x)
    cg_y = coarse_grain_B(a_y)
    cg_z = coarse_grain_B(a_z)
    cg_ent = coarse_grain_B(entangling)
    cg_mix = coarse_grain_B(mixed_term)

    positive = {
        "lifted_local_generators_survive_coarse_graining": {
            "pass": close(cg_x, X) and close(cg_y, Y) and close(cg_z, Z),
        },
        "identity_is_preserved": {
            "pass": close(coarse_grain_B(np.kron(I2, I2)), I2),
        },
        "linearity_holds": {
            "pass": close(cg_mix, X),
        },
    }

    negative = {
        "purely_b_side_or_entangling_term_can_collapse": {
            "pass": close(cg_ent, np.zeros((2, 2), dtype=complex)) and close(coarse_grain_B(np.kron(I2, Z)), np.zeros((2, 2), dtype=complex)),
        },
        "coarse_graining_is_not_multiplicative_in_general": {
            "lhs": coarse_grain_B(np.kron(X, I2) @ np.kron(Y, I2)),
            "rhs": cg_x @ cg_y,
            "pass": close(coarse_grain_B(np.kron(X, I2) @ np.kron(Y, I2)), cg_x @ cg_y) and not close(coarse_grain_B(entangling @ entangling + np.kron(I2, Z)), cg_ent @ coarse_grain_B(entangling + np.kron(I2, Z))),
        },
    }

    boundary = {
        "commutator_of_lifted_local_terms_is_preserved": {
            "pass": close(coarse_grain_B(commutator(a_x, a_y)), commutator(cg_x, cg_y)),
        },
        "coarse_grained_local_pauli_algebra_remains_traceless": {
            "pass": abs(np.trace(cg_x)) < EPS and abs(np.trace(cg_y)) < EPS and abs(np.trace(cg_z)) < EPS,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "coarse_grained_operator_algebra",
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
            "scope_note": "Direct local coarse-grained operator-algebra lego from two-qubit operators to one-qubit effective operators by partial-trace coarse-graining.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "coarse_grained_operator_algebra_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
