#!/usr/bin/env python3
"""
PURE LEGO: Coherent Information
===============================
Direct local bipartite entropy lego on bounded two-qubit states.
"""

import json
import pathlib

import numpy as np


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for coherent information on bounded two-qubit states, kept "
    "separate from conditional entropy, mutual information, and seam-level Phi0 files."
)

LEGO_IDS = [
    "coherent_information_measure",
]

PRIMARY_LEGO_IDS = [
    "coherent_information_measure",
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


def ket(v):
    return np.array(v, dtype=complex).reshape(-1, 1)


def dm(v):
    v = np.array(v, dtype=complex).reshape(-1, 1)
    return v @ v.conj().T


def partial_trace(rho_ab, dim_a=2, dim_b=2, trace_out="A"):
    rho_ab = rho_ab.reshape(dim_a, dim_b, dim_a, dim_b)
    if trace_out == "A":
        return np.trace(rho_ab, axis1=0, axis2=2)
    return np.trace(rho_ab, axis1=1, axis2=3)


def vn_entropy(rho):
    evals = np.linalg.eigvalsh((rho + rho.conj().T) / 2)
    evals = np.maximum(evals, 0.0)
    evals = evals[evals > 1e-14]
    if evals.size == 0:
        return 0.0
    return float(-np.sum(evals * np.log2(evals)))


def coherent_information(rho_ab):
    rho_b = partial_trace(rho_ab, trace_out="A")
    return float(vn_entropy(rho_b) - vn_entropy(rho_ab))


def werner_state(r):
    phi_plus = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
    return (1 - r) * np.eye(4, dtype=complex) / 4.0 + r * dm(phi_plus)


def main():
    ket0 = ket([1, 0])
    ket1 = ket([0, 1])

    prod_00 = np.kron(ket0, ket0) @ np.kron(ket0, ket0).conj().T
    classical = 0.5 * dm([1, 0, 0, 0]) + 0.5 * dm([0, 0, 0, 1])
    bell_phi_p = ket([1, 0, 0, 1]) / np.sqrt(2)
    bell = bell_phi_p @ bell_phi_p.conj().T
    werner_low = werner_state(0.2)
    werner_high = werner_state(0.8)

    ci_prod = coherent_information(prod_00)
    ci_classical = coherent_information(classical)
    ci_bell = coherent_information(bell)
    ci_werner_low = coherent_information(werner_low)
    ci_werner_high = coherent_information(werner_high)

    positive = {
        "product_state_has_zero_coherent_information": {
            "value": ci_prod,
            "pass": abs(ci_prod) < EPS,
        },
        "bell_state_has_positive_coherent_information": {
            "value": ci_bell,
            "pass": abs(ci_bell - 1.0) < EPS,
        },
        "high_werner_state_has_positive_coherent_information": {
            "value": ci_werner_high,
            "pass": ci_werner_high > EPS,
        },
    }

    negative = {
        "classical_correlation_does_not_force_positive_coherent_information": {
            "value": ci_classical,
            "pass": ci_classical <= EPS,
        },
        "low_werner_state_is_not_positive": {
            "value": ci_werner_low,
            "pass": ci_werner_low <= EPS,
        },
    }

    boundary = {
        "bell_exceeds_product": {
            "bell": ci_bell,
            "product": ci_prod,
            "pass": ci_bell > ci_prod + EPS,
        },
        "werner_coherent_information_grows_with_entanglement_strength": {
            "low": ci_werner_low,
            "high": ci_werner_high,
            "pass": ci_werner_high > ci_werner_low + EPS,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "coherent_information_measure",
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
            "scope_note": "Direct local coherent-information lego on bounded two-qubit product, Bell, classical-mixture, and Werner states.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "coherent_information_measure_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
