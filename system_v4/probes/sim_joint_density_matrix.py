#!/usr/bin/env python3
"""
PURE LEGO: Joint Density Matrix
===============================
Direct local bipartite lego.

Construct bounded two-qubit joint states, verify density-matrix legality, and
keep product / mixed / entangled joint states distinct at the state level.
"""

import json
import pathlib

import numpy as np


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for bounded two-qubit joint density matrices before "
    "derived witness or entropy layers."
)

LEGO_IDS = [
    "joint_density_matrix",
    "reduced_state_object",
    "partial_trace_operator",
]

PRIMARY_LEGO_IDS = [
    "joint_density_matrix",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed -- direct numpy joint-state lego"},
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


def ket(v):
    return np.array(v, dtype=complex).reshape(-1, 1)


def dm(v):
    k = ket(v).flatten()
    return np.outer(k, k.conj())


def is_valid_dm(rho):
    herm = np.allclose(rho, rho.conj().T, atol=EPS)
    trace_one = abs(np.trace(rho) - 1.0) < EPS
    evals = np.linalg.eigvalsh((rho + rho.conj().T) / 2)
    psd = np.all(evals >= -EPS)
    return {
        "hermitian": bool(herm),
        "trace_one": bool(trace_one),
        "psd": bool(psd),
        "eigenvalues": [float(x) for x in evals],
    }


def partial_trace_B(rho, da=2, db=2):
    rho = rho.reshape(da, db, da, db)
    return np.trace(rho, axis1=1, axis2=3)


def main():
    k0 = [1, 0]
    k1 = [0, 1]
    prod_01 = dm(np.kron(k0, k1))
    bell = dm((np.kron(k0, k0) + np.kron(k1, k1)) / np.sqrt(2))
    classical_mix = 0.5 * dm(np.kron(k0, k0)) + 0.5 * dm(np.kron(k1, k1))
    invalid_negative = np.diag([1.1, -0.1, 0.0, 0.0]).astype(complex)
    invalid_trace = 0.6 * np.eye(4, dtype=complex)

    prod_chk = is_valid_dm(prod_01)
    bell_chk = is_valid_dm(bell)
    mix_chk = is_valid_dm(classical_mix)
    invalid_neg_chk = is_valid_dm(invalid_negative)
    invalid_trace_chk = is_valid_dm(invalid_trace)

    positive = {
        "product_joint_state_is_valid": {
            **prod_chk,
            "pass": prod_chk["hermitian"] and prod_chk["trace_one"] and prod_chk["psd"],
        },
        "bell_joint_state_is_valid": {
            **bell_chk,
            "pass": bell_chk["hermitian"] and bell_chk["trace_one"] and bell_chk["psd"],
        },
        "classical_mixture_is_valid": {
            **mix_chk,
            "pass": mix_chk["hermitian"] and mix_chk["trace_one"] and mix_chk["psd"],
        },
    }

    negative = {
        "negative_eigenvalue_joint_state_is_rejected": {
            **invalid_neg_chk,
            "pass": not invalid_neg_chk["psd"],
        },
        "wrong_trace_joint_state_is_rejected": {
            **invalid_trace_chk,
            "pass": not invalid_trace_chk["trace_one"],
        },
    }

    boundary = {
        "bell_and_product_joint_states_are_distinct": {
            "fro_norm_difference": float(np.linalg.norm(bell - prod_01)),
            "pass": float(np.linalg.norm(bell - prod_01)) > EPS,
        },
        "product_joint_marginal_is_pure": {
            "pass": np.allclose(partial_trace_B(prod_01), dm(k0), atol=EPS),
        },
        "bell_joint_marginal_is_mixed": {
            "pass": np.allclose(partial_trace_B(bell), np.eye(2) / 2, atol=EPS),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "joint_density_matrix",
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
            "scope_note": "Direct local joint-density-state lego on bounded two-qubit examples.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "joint_density_matrix_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
