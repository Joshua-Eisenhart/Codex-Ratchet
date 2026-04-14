#!/usr/bin/env python3
"""
PURE LEGO: Shannon Entropy
==========================
Direct local measurement-basis entropy lego on bounded one-qubit states.
"""

import json
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for Shannon entropy of measurement outcomes on bounded qubit "
    "states, kept separate from basis-free von Neumann entropy."
)

LEGO_IDS = [
    "shannon_entropy",
]

PRIMARY_LEGO_IDS = [
    "shannon_entropy",
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


def projectors_from_basis(basis):
    return [dm(vec) for vec in basis]


def measurement_probs(rho, basis):
    probs = [float(np.real_if_close(np.trace(rho @ proj))) for proj in projectors_from_basis(basis)]
    probs = np.array(probs, dtype=float)
    probs = np.clip(probs, 0.0, 1.0)
    probs = probs / probs.sum()
    return probs


def shannon_entropy(probs):
    probs = probs[probs > 1e-14]
    if probs.size == 0:
        return 0.0
    return float(-np.sum(probs * np.log2(probs)))


def main():
    ket0 = ket([1, 0])
    ket1 = ket([0, 1])
    ketp = ket([1 / np.sqrt(2), 1 / np.sqrt(2)])
    ketm = ket([1 / np.sqrt(2), -1 / np.sqrt(2)])

    z_basis = [ket0, ket1]
    x_basis = [ketp, ketm]

    rho_0 = dm(ket0)
    rho_p = dm(ketp)
    rho_mm = np.eye(2, dtype=complex) / 2.0

    h_z_0 = shannon_entropy(measurement_probs(rho_0, z_basis))
    h_x_0 = shannon_entropy(measurement_probs(rho_0, x_basis))
    h_z_p = shannon_entropy(measurement_probs(rho_p, z_basis))
    h_x_p = shannon_entropy(measurement_probs(rho_p, x_basis))
    h_z_mm = shannon_entropy(measurement_probs(rho_mm, z_basis))
    h_x_mm = shannon_entropy(measurement_probs(rho_mm, x_basis))

    positive = {
        "eigenstate_has_zero_shannon_entropy_in_its_own_basis": {
            "value": h_z_0,
            "pass": abs(h_z_0) < EPS,
        },
        "plus_state_has_zero_shannon_entropy_in_x_basis": {
            "value": h_x_p,
            "pass": abs(h_x_p) < EPS,
        },
        "maximally_mixed_state_has_one_bit_in_any_orthonormal_basis": {
            "z_basis": h_z_mm,
            "x_basis": h_x_mm,
            "pass": abs(h_z_mm - 1.0) < EPS and abs(h_x_mm - 1.0) < EPS,
        },
    }

    negative = {
        "same_state_does_not_have_basis_independent_shannon_entropy": {
            "z_basis": h_z_0,
            "x_basis": h_x_0,
            "pass": h_x_0 > h_z_0 + EPS,
        },
        "plus_state_is_not_zero_entropy_in_z_basis": {
            "value": h_z_p,
            "pass": h_z_p > EPS,
        },
    }

    boundary = {
        "computational_and_x_basis_swap_zero_and_one_bit_for_pure_basis_states": {
            "h_z_0": h_z_0,
            "h_x_0": h_x_0,
            "h_z_p": h_z_p,
            "h_x_p": h_x_p,
            "pass": abs(h_x_0 - 1.0) < EPS and abs(h_z_p - 1.0) < EPS,
        },
        "maximally_mixed_state_is_basis_invariant": {
            "pass": abs(h_z_mm - h_x_mm) < EPS,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "shannon_entropy",
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
            "scope_note": "Direct local Shannon-entropy lego on bounded qubit states under explicit Z and X basis measurements.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "shannon_entropy_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
