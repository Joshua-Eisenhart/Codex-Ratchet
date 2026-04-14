#!/usr/bin/env python3
"""
PURE LEGO: Entanglement Witness Family
======================================
Direct local witness-operator lego on bounded two-qubit states.
"""

import json
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for bounded two-qubit entanglement witnesses, kept separate "
    "from scalar entanglement summaries like concurrence or negativity."
)

LEGO_IDS = [
    "entanglement_witness_family",
]

PRIMARY_LEGO_IDS = [
    "entanglement_witness_family",
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


def dm(v):
    v = np.array(v, dtype=complex).reshape(-1, 1)
    return v @ v.conj().T


def werner_state(r):
    phi_plus = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
    return (1 - r) * np.eye(4, dtype=complex) / 4.0 + r * dm(phi_plus)


def witness_expectation(rho, witness):
    return float(np.real(np.trace(witness @ rho)))


def main():
    ket0 = np.array([1, 0], dtype=complex)
    phi_plus = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)

    rho_product = dm(np.kron(ket0, ket0))
    rho_bell = dm(phi_plus)
    rho_werner_low = werner_state(0.2)
    rho_werner_high = werner_state(0.8)

    # Standard witness for |Phi+>: W = I/2 - |Phi+><Phi+|
    bell_projector = dm(phi_plus)
    witness = 0.5 * np.eye(4, dtype=complex) - bell_projector

    e_product = witness_expectation(rho_product, witness)
    e_bell = witness_expectation(rho_bell, witness)
    e_low = witness_expectation(rho_werner_low, witness)
    e_high = witness_expectation(rho_werner_high, witness)

    positive = {
        "witness_is_nonnegative_on_product_state": {
            "value": e_product,
            "pass": e_product >= -EPS,
        },
        "witness_detects_bell_state": {
            "value": e_bell,
            "pass": e_bell < -EPS,
        },
        "witness_detects_high_werner_entanglement": {
            "value": e_high,
            "pass": e_high < -EPS,
        },
    }

    negative = {
        "low_werner_state_is_not_falsely_detected": {
            "value": e_low,
            "pass": e_low >= -EPS,
        },
        "witness_row_is_not_scalar_summary_row": {
            "product_value": e_product,
            "bell_value": e_bell,
            "pass": abs(e_product - e_bell) > EPS,
        },
    }

    boundary = {
        "werner_detection_changes_across_threshold": {
            "low_r": e_low,
            "high_r": e_high,
            "pass": e_low >= -EPS and e_high < -EPS,
        },
        "witness_operator_is_hermitian": {
            "pass": np.allclose(witness, witness.conj().T, atol=EPS),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "entanglement_witness_family",
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
            "scope_note": "Direct local entanglement-witness lego on product, Bell, and Werner states.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "entanglement_witness_family_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
