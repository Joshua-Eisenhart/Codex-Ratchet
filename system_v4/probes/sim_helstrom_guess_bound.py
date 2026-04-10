#!/usr/bin/env python3
"""
PURE LEGO: Helstrom Guess Bound
===============================
Direct local operational distinguishability lego on bounded qubit state pairs.
"""

import json
import pathlib

import numpy as np


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for the Helstrom optimal-guess bound on bounded qubit state "
    "pairs, tying trace distance to operational discrimination."
)

LEGO_IDS = [
    "helstrom_guess_bound",
]

PRIMARY_LEGO_IDS = [
    "helstrom_guess_bound",
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


def trace_distance(rho, sigma):
    diff = (rho - sigma + (rho - sigma).conj().T) / 2
    evals = np.linalg.eigvalsh(diff)
    return float(0.5 * np.sum(np.abs(evals)))


def helstrom_guess_prob(rho, sigma):
    return 0.5 * (1.0 + trace_distance(rho, sigma))


def main():
    rho0 = dm([1, 0])
    rho1 = dm([0, 1])
    rho_plus = dm([1 / np.sqrt(2), 1 / np.sqrt(2)])
    rho_mix = np.eye(2, dtype=complex) / 2.0
    rho_mid = 0.7 * rho0 + 0.3 * rho_mix

    p_same = helstrom_guess_prob(rho0, rho0)
    p_orth = helstrom_guess_prob(rho0, rho1)
    p_nonorth = helstrom_guess_prob(rho0, rho_plus)
    p_mix = helstrom_guess_prob(rho_mix, rho0)
    p_mid = helstrom_guess_prob(rho_mid, rho0)

    positive = {
        "identical_states_give_random_guessing": {
            "value": p_same,
            "pass": abs(p_same - 0.5) < EPS,
        },
        "orthogonal_states_give_perfect_guessing": {
            "value": p_orth,
            "pass": abs(p_orth - 1.0) < EPS,
        },
        "formula_matches_trace_distance_identity": {
            "lhs": p_nonorth,
            "rhs": 0.5 * (1.0 + trace_distance(rho0, rho_plus)),
            "pass": abs(p_nonorth - (0.5 * (1.0 + trace_distance(rho0, rho_plus)))) < EPS,
        },
    }

    negative = {
        "nonorthogonal_pair_is_not_perfectly_guessable": {
            "value": p_nonorth,
            "pass": p_nonorth < 1.0 - EPS,
        },
        "mixed_pair_is_not_below_random": {
            "value": p_mix,
            "pass": p_mix >= 0.5 - EPS,
        },
    }

    boundary = {
        "guess_probability_is_monotone_with_distance": {
            "same": p_same,
            "mid": p_mid,
            "mix": p_mix,
            "orth": p_orth,
            "pass": p_same <= p_mid + EPS and p_mid <= p_mix + EPS and p_mix <= p_orth + EPS,
        },
        "all_values_stay_in_operational_range": {
            "values": [p_same, p_orth, p_nonorth, p_mix, p_mid],
            "pass": all(0.5 - EPS <= x <= 1.0 + EPS for x in [p_same, p_orth, p_nonorth, p_mix, p_mid]),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "helstrom_guess_bound",
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
            "scope_note": "Direct local Helstrom guessing lego on bounded qubit state pairs.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "helstrom_guess_bound_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
