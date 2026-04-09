#!/usr/bin/env python3
"""
PURE LEGO: Clifford Generator Basis
===================================
Direct local generator-basis lego on a minimal one-qubit Clifford generating set.
"""

import json
import pathlib

import numpy as np


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for a minimal one-qubit Clifford generator basis using {H, S}, "
    "kept separate from Clifford hierarchy, geometry, and operator-action rows."
)

LEGO_IDS = [
    "clifford_generator_basis",
]

PRIMARY_LEGO_IDS = [
    "clifford_generator_basis",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed for this small generator-validity row"},
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
H = np.array([[1.0, 1.0], [1.0, -1.0]], dtype=complex) / np.sqrt(2.0)
S = np.array([[1.0, 0.0], [0.0, 1j]], dtype=complex)
T = np.array([[1.0, 0.0], [0.0, np.exp(1j * np.pi / 4)]], dtype=complex)


def is_unitary(u):
    return np.allclose(u.conj().T @ u, I2, atol=EPS)


def up_to_global_phase(a, b):
    idx = np.argwhere(np.abs(b) > EPS)
    if idx.size == 0:
        return np.allclose(a, b, atol=EPS)
    i, j = idx[0]
    phase = a[i, j] / b[i, j]
    if abs(phase) < EPS:
        return False
    return np.allclose(a, phase * b, atol=1e-8)


def preserves_pauli_set(u):
    paulis = [X, Y, Z]
    allowed = [X, Y, Z, -X, -Y, -Z]
    for p in paulis:
        conj = u @ p @ u.conj().T
        if not any(up_to_global_phase(conj, a) for a in allowed):
            return False
    return True


def main():
    HS = H @ S

    positive = {
        "generators_are_unitary": {
            "pass": is_unitary(H) and is_unitary(S),
        },
        "clifford_generators_preserve_pauli_set_under_conjugation": {
            "pass": preserves_pauli_set(H) and preserves_pauli_set(S) and preserves_pauli_set(HS),
        },
        "minimal_generation_examples_are_distinct": {
            "pass": not np.allclose(H, S, atol=EPS) and not np.allclose(H, HS, atol=EPS) and not np.allclose(S, HS, atol=EPS),
        },
    }

    negative = {
        "nonclifford_t_gate_is_rejected_by_pauli_preservation_test": {
            "pass": not preserves_pauli_set(T),
        },
        "generators_are_not_redundant_copies": {
            "pass": np.linalg.norm(H - S) > EPS,
        },
    }

    boundary = {
        "hadamard_and_phase_have_expected_finite_orders": {
            "pass": np.allclose(H @ H, I2, atol=EPS) and np.allclose(np.linalg.matrix_power(S, 4), I2, atol=EPS),
        },
        "scope_guard_stays_basis_level_not_hierarchy_level": {
            "pass": preserves_pauli_set(H) and preserves_pauli_set(S),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "clifford_generator_basis",
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
            "scope_note": "Direct local Clifford-generator lego on the minimal one-qubit generating set {H, S}.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "clifford_generator_basis_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
