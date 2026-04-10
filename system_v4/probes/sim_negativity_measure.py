#!/usr/bin/env python3
"""
PURE LEGO: Negativity
=====================
Direct local bipartite entanglement lego for negativity and log-negativity.
"""

import json
import pathlib

import numpy as np


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for negativity and logarithmic negativity on bounded two-qubit "
    "states, separated from topology or filtration successors."
)

LEGO_IDS = [
    "negativity_measure",
    "logarithmic_negativity",
]

PRIMARY_LEGO_IDS = [
    "negativity_measure",
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


def dm(v):
    v = np.array(v, dtype=complex).reshape(-1, 1)
    return v @ v.conj().T


def partial_transpose_b(rho, dim_a=2, dim_b=2):
    rho_r = rho.reshape(dim_a, dim_b, dim_a, dim_b)
    return rho_r.transpose(0, 3, 2, 1).reshape(dim_a * dim_b, dim_a * dim_b)


def negativity(rho):
    evals = np.linalg.eigvalsh(partial_transpose_b(rho))
    return float(np.sum(np.abs(evals[evals < -EPS])))


def log_negativity(rho):
    return float(np.log2(2.0 * negativity(rho) + 1.0))


def werner_state(r):
    phi_plus = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
    return (1 - r) * np.eye(4, dtype=complex) / 4.0 + r * dm(phi_plus)


def main():
    ket0 = np.array([1, 0], dtype=complex)
    phi_plus = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)

    rho_product = dm(np.kron(ket0, ket0))
    rho_bell = dm(phi_plus)
    werner_low = werner_state(0.2)
    werner_mid = werner_state(0.5)
    werner_high = werner_state(0.9)

    n_product = negativity(rho_product)
    n_bell = negativity(rho_bell)
    n_low = negativity(werner_low)
    n_mid = negativity(werner_mid)
    n_high = negativity(werner_high)

    ln_product = log_negativity(rho_product)
    ln_bell = log_negativity(rho_bell)

    positive = {
        "product_state_has_zero_negativity": {
            "value": n_product,
            "pass": abs(n_product) < EPS and abs(ln_product) < EPS,
        },
        "bell_state_has_positive_negativity": {
            "negativity": n_bell,
            "log_negativity": ln_bell,
            "pass": n_bell > 0.0 and abs(ln_bell - 1.0) < EPS,
        },
        "werner_negativity_is_monotone_in_r": {
            "values": {"r_0_2": n_low, "r_0_5": n_mid, "r_0_9": n_high},
            "pass": n_low <= n_mid + EPS and n_mid <= n_high + EPS,
        },
    }

    negative = {
        "low_werner_state_is_not_entangled_by_negativity": {
            "value": n_low,
            "pass": abs(n_low) < EPS,
        },
        "product_and_bell_do_not_share_same_negativity": {
            "product": n_product,
            "bell": n_bell,
            "pass": n_bell > n_product + EPS,
        },
    }

    boundary = {
        "werner_above_one_third_has_positive_negativity": {
            "value_mid": n_mid,
            "value_high": n_high,
            "pass": n_mid > EPS and n_high > EPS,
        },
        "log_negativity_tracks_negativity_order": {
            "pass": log_negativity(werner_low) <= log_negativity(werner_mid) + EPS
            and log_negativity(werner_mid) <= log_negativity(werner_high) + EPS,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "negativity_measure",
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
            "scope_note": "Direct local negativity lego on bounded two-qubit product, Bell, and Werner states.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "negativity_measure_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
