#!/usr/bin/env python3
"""
PURE LEGO: Concurrence
======================
Direct local bipartite entanglement lego on bounded two-qubit states.
"""

import json
import pathlib

import numpy as np


EPS = 1e-8

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for concurrence on bounded two-qubit states, including "
    "product, Bell, and Werner-family checks."
)

LEGO_IDS = [
    "concurrence_measure",
]

PRIMARY_LEGO_IDS = [
    "concurrence_measure",
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
    "gudhi": {"tried": False, "used": False, "reason": "saved for later filtration successor"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}


SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
YY = np.kron(SIGMA_Y, SIGMA_Y)


def dm(v):
    v = np.array(v, dtype=complex).reshape(-1, 1)
    return v @ v.conj().T


def concurrence(rho):
    spin_flip = YY @ rho.conj() @ YY
    evals = np.linalg.eigvals(rho @ spin_flip)
    lambdas = np.sort(np.sqrt(np.maximum(np.real_if_close(evals, tol=1e5).real, 0.0)))[::-1]
    return float(max(0.0, lambdas[0] - lambdas[1] - lambdas[2] - lambdas[3]))


def werner_state(r):
    phi_plus = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
    return (1 - r) * np.eye(4, dtype=complex) / 4.0 + r * dm(phi_plus)


def main():
    ket0 = np.array([1, 0], dtype=complex)
    ket1 = np.array([0, 1], dtype=complex)
    phi_plus = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)

    rho_product = dm(np.kron(ket0, ket0))
    rho_bell = dm(phi_plus)
    werner_low = werner_state(0.2)
    werner_mid = werner_state(0.5)
    werner_high = werner_state(0.9)

    c_product = concurrence(rho_product)
    c_bell = concurrence(rho_bell)
    c_low = concurrence(werner_low)
    c_mid = concurrence(werner_mid)
    c_high = concurrence(werner_high)

    positive = {
        "product_state_has_zero_concurrence": {
            "value": c_product,
            "pass": abs(c_product) < EPS,
        },
        "bell_state_has_unit_concurrence": {
            "value": c_bell,
            "pass": abs(c_bell - 1.0) < EPS,
        },
        "werner_concurrence_increases_with_r": {
            "values": {"r_0_2": c_low, "r_0_5": c_mid, "r_0_9": c_high},
            "pass": c_low <= c_mid + EPS and c_mid <= c_high + EPS,
        },
    }

    negative = {
        "low_werner_state_is_not_maximally_entangled": {
            "value": c_low,
            "pass": c_low < 1.0 - EPS,
        },
        "product_and_bell_do_not_share_same_readout": {
            "product": c_product,
            "bell": c_bell,
            "pass": abs(c_product - c_bell) > 0.5,
        },
    }

    boundary = {
        "werner_below_one_third_is_zero": {
            "value": c_low,
            "pass": c_low < EPS,
        },
        "werner_above_one_third_is_positive": {
            "value": c_mid,
            "pass": c_mid > EPS and c_high > EPS,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "concurrence_measure",
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
            "scope_note": "Direct local concurrence lego on bounded two-qubit product, Bell, and Werner states.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "concurrence_measure_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
