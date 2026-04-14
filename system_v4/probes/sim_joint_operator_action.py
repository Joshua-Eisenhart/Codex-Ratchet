#!/usr/bin/env python3
"""
PURE LEGO: Joint Operator Action
================================
Direct local two-qubit operator-action lego on a tiny admitted state set.
"""

import json
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for primitive two-qubit operator action on admitted joint states, "
    "kept separate from local operator action, composition-order rows, and channel-capacity rows."
)

LEGO_IDS = [
    "joint_operator_action",
]

PRIMARY_LEGO_IDS = [
    "joint_operator_action",
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
I4 = np.eye(4, dtype=complex)
X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)


def dm(v):
    vec = np.array(v, dtype=complex).reshape(-1, 1)
    return vec @ vec.conj().T


def kron(a, b):
    return np.kron(a, b)


def apply_unitary(u, rho):
    return u @ rho @ u.conj().T


def is_valid_density(rho):
    hermitian = np.allclose(rho, rho.conj().T, atol=EPS)
    trace_one = abs(np.trace(rho) - 1.0) < EPS
    evals = np.linalg.eigvalsh((rho + rho.conj().T) / 2)
    psd = np.min(evals) > -1e-10
    return bool(hermitian and trace_one and psd)


def partial_trace_B(rho, da=2, db=2):
    rho = rho.reshape(da, db, da, db)
    return np.trace(rho, axis1=1, axis2=3)


def concurrence_pure(psi):
    a00, a01, a10, a11 = np.array(psi, dtype=complex).reshape(4)
    return float(2.0 * abs(a00 * a11 - a01 * a10))


def main():
    ket00 = np.array([1.0, 0.0, 0.0, 0.0], dtype=complex)
    ket_plus0 = np.array([1.0, 0.0, 1.0, 0.0], dtype=complex) / np.sqrt(2.0)
    ket_pp = np.array([1.0, 1.0, 1.0, 1.0], dtype=complex) / 2.0

    rho00 = dm(ket00)
    rho_plus0 = dm(ket_plus0)
    rho_pp = dm(ket_pp)
    rho_mixed = I4 / 4.0

    cnot = np.array(
        [[1, 0, 0, 0],
         [0, 1, 0, 0],
         [0, 0, 0, 1],
         [0, 0, 1, 0]],
        dtype=complex,
    )
    cz = np.diag([1.0, 1.0, 1.0, -1.0]).astype(complex)
    swap = np.array(
        [[1, 0, 0, 0],
         [0, 0, 1, 0],
         [0, 1, 0, 0],
         [0, 0, 0, 1]],
        dtype=complex,
    )
    counterfeit = np.diag([1.0, 1.0, 0.5, 1.0]).astype(complex)

    rho_cnot_plus0 = apply_unitary(cnot, rho_plus0)
    bell_like = cnot @ ket_plus0
    rho_swap_00 = apply_unitary(swap, rho00)
    rho_cz_pp = apply_unitary(cz, rho_pp)
    rho_bad = counterfeit @ rho_plus0 @ counterfeit.conj().T

    positive = {
        "joint_unitary_action_preserves_density_validity": {
            "pass": all(
                is_valid_density(apply_unitary(u, rho))
                for u in [cnot, cz, swap]
                for rho in [rho00, rho_plus0, rho_pp, rho_mixed]
            ),
        },
        "entangling_joint_action_example_exists": {
            "concurrence_after_cnot_plus0": concurrence_pure(bell_like),
            "pass": concurrence_pure(bell_like) > 1.0 - 1e-8,
        },
        "swap_gives_structure_preserving_relabeling": {
            "pass": np.allclose(rho_swap_00, rho00, atol=EPS),
        },
    }

    negative = {
        "nontrivial_joint_action_does_not_fix_all_joint_states": {
            "pass": (
                not np.allclose(rho_cnot_plus0, rho_plus0, atol=EPS)
                and not np.allclose(rho_cz_pp, rho_pp, atol=EPS)
            ),
        },
        "counterfeit_nonunitary_joint_map_is_rejected": {
            "pass": not is_valid_density(rho_bad),
        },
    }

    boundary = {
        "maximally_mixed_joint_state_is_fixed_by_joint_unitaries": {
            "pass": all(
                np.allclose(apply_unitary(u, rho_mixed), rho_mixed, atol=EPS)
                for u in [cnot, cz, swap]
            ),
        },
        "entangling_example_changes_reduced_state_purity": {
            "pass": np.allclose(partial_trace_B(rho_cnot_plus0), I2 / 2.0, atol=EPS),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "joint_operator_action",
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
            "scope_note": "Direct local two-qubit operator-action lego on a tiny admitted state set with one-step joint unitaries only.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "joint_operator_action_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
