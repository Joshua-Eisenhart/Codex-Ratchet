#!/usr/bin/env python3
"""
PURE LEGO: Local Operator Action
================================
Direct local operator-action lego on a tiny admitted qubit state set.
"""

import json
import pathlib

import numpy as np


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for primitive local operator action on admitted qubit states, "
    "kept separate from basis rows, commutator rows, joint action, and composition-order rows."
)

LEGO_IDS = [
    "local_operator_action",
]

PRIMARY_LEGO_IDS = [
    "local_operator_action",
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
Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)


def dm(v):
    vec = np.array(v, dtype=complex).reshape(-1, 1)
    return vec @ vec.conj().T


def purity(rho):
    return float(np.real(np.trace(rho @ rho)))


def apply_unitary(u, rho):
    return u @ rho @ u.conj().T


def is_valid_density(rho):
    hermitian = np.allclose(rho, rho.conj().T, atol=EPS)
    trace_one = abs(np.trace(rho) - 1.0) < EPS
    evals = np.linalg.eigvalsh((rho + rho.conj().T) / 2)
    psd = np.min(evals) > -1e-10
    return bool(hermitian and trace_one and psd)


def main():
    ket0 = dm([1.0, 0.0])
    ket1 = dm([0.0, 1.0])
    ket_plus = dm([1.0 / np.sqrt(2.0), 1.0 / np.sqrt(2.0)])
    ket_minus = dm([1.0 / np.sqrt(2.0), -1.0 / np.sqrt(2.0)])
    maximally_mixed = I2 / 2.0

    x_on_zero = apply_unitary(X, ket0)
    z_on_plus = apply_unitary(Z, ket_plus)
    z_on_zero = apply_unitary(Z, ket0)
    x_on_mixed = apply_unitary(X, maximally_mixed)

    counterfeit = np.array([[1.0, 1.0], [0.0, 1.0]], dtype=complex)
    counterfeit_on_plus = counterfeit @ ket_plus @ counterfeit.conj().T

    positive = {
        "unitary_action_preserves_density_matrix_legality": {
            "pass": all(
                is_valid_density(apply_unitary(u, rho))
                for u in [I2, X, Z]
                for rho in [ket0, ket_plus, maximally_mixed]
            ),
        },
        "unitary_action_preserves_purity": {
            "pass": all(
                abs(purity(apply_unitary(u, rho)) - purity(rho)) < EPS
                for u in [I2, X, Z]
                for rho in [ket0, ket_plus, maximally_mixed]
            ),
        },
        "x_flips_zero_to_one_projector": {
            "pass": np.allclose(x_on_zero, ket1, atol=EPS),
        },
        "z_flips_plus_to_minus_projector": {
            "pass": np.allclose(z_on_plus, ket_minus, atol=EPS),
        },
    }

    negative = {
        "nontrivial_local_action_does_not_fix_all_pure_states": {
            "pass": (
                not np.allclose(x_on_zero, ket0, atol=EPS)
                and not np.allclose(z_on_plus, ket_plus, atol=EPS)
            ),
        },
        "counterfeit_nonunitary_map_fails_density_legality": {
            "pass": not is_valid_density(counterfeit_on_plus),
        },
    }

    boundary = {
        "identity_action_leaves_states_unchanged": {
            "pass": all(
                np.allclose(apply_unitary(I2, rho), rho, atol=EPS)
                for rho in [ket0, ket_plus, maximally_mixed]
            ),
        },
        "maximally_mixed_state_is_fixed_by_unitary_conjugation": {
            "pass": np.allclose(x_on_mixed, maximally_mixed, atol=EPS)
            and np.allclose(apply_unitary(Z, maximally_mixed), maximally_mixed, atol=EPS),
        },
        "z_action_keeps_z_eigenstate_fixed": {
            "pass": np.allclose(z_on_zero, ket0, atol=EPS),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "local_operator_action",
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
            "scope_note": "Direct local operator-action lego on a tiny admitted qubit state set under unitary conjugation.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "local_operator_action_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
