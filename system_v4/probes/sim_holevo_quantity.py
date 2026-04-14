#!/usr/bin/env python3
"""
PURE LEGO: Holevo Quantity
==========================
Direct local cq-ensemble accessibility lego on bounded qubit ensembles.
"""

import json
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for Holevo quantity on bounded qubit ensembles, kept separate "
    "from mutual information and full channel-capacity rows."
)

LEGO_IDS = [
    "holevo_quantity",
]

PRIMARY_LEGO_IDS = [
    "holevo_quantity",
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


def pure_state(vec):
    vec = np.asarray(vec, dtype=complex)
    vec = vec / np.linalg.norm(vec)
    return np.outer(vec, vec.conj())


def vn_entropy(rho):
    evals = np.linalg.eigvalsh((rho + rho.conj().T) / 2)
    evals = np.maximum(np.real(evals), 0.0)
    evals = evals[evals > 1e-14]
    if evals.size == 0:
        return 0.0
    return float(-np.sum(evals * np.log2(evals)))


def holevo_quantity(probs, states):
    avg = np.zeros_like(states[0], dtype=complex)
    weighted = 0.0
    for p, rho in zip(probs, states):
        avg += p * rho
        weighted += p * vn_entropy(rho)
    return float(vn_entropy(avg) - weighted), avg


def dephase_z(rho, p):
    z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
    return (1.0 - p) * rho + p * (z @ rho @ z)


def main():
    zero = pure_state([1, 0])
    one = pure_state([0, 1])
    plus = pure_state([1, 1])
    mixed = np.diag([0.7, 0.3]).astype(complex)

    chi_orth, avg_orth = holevo_quantity([0.5, 0.5], [zero, one])
    chi_ident, avg_ident = holevo_quantity([0.5, 0.5], [zero, zero])
    chi_nonorth, avg_nonorth = holevo_quantity([0.5, 0.5], [zero, plus])
    chi_mixed, avg_mixed = holevo_quantity([0.5, 0.5], [zero, mixed])

    chi_before, _ = holevo_quantity([0.5, 0.5], [zero, plus])
    chi_after, _ = holevo_quantity([0.5, 0.5], [dephase_z(zero, 0.25), dephase_z(plus, 0.25)])

    positive = {
        "orthogonal_two_state_ensemble_has_one_bit_holevo": {
            "value": chi_orth,
            "pass": abs(chi_orth - 1.0) < EPS,
        },
        "identical_states_have_zero_holevo": {
            "value": chi_ident,
            "pass": abs(chi_ident) < EPS,
        },
        "nonorthogonal_ensemble_has_intermediate_holevo": {
            "value": chi_nonorth,
            "pass": EPS < chi_nonorth < 1.0 - EPS,
        },
    }

    negative = {
        "holevo_is_bounded_by_entropy_of_average_state": {
            "holevo": chi_nonorth,
            "entropy_avg": vn_entropy(avg_nonorth),
            "pass": chi_nonorth <= vn_entropy(avg_nonorth) + EPS,
        },
        "dephasing_does_not_increase_holevo_for_this_ensemble": {
            "before": chi_before,
            "after": chi_after,
            "pass": chi_after <= chi_before + EPS,
        },
    }

    boundary = {
        "mixed_state_ensemble_sits_between_identical_and_orthogonal_cases": {
            "chi_ident": chi_ident,
            "chi_mixed": chi_mixed,
            "chi_orth": chi_orth,
            "pass": chi_ident + EPS < chi_mixed < chi_orth - EPS,
        },
        "average_state_entropy_tracks_accessible_information_ordering": {
            "orth_entropy": vn_entropy(avg_orth),
            "nonorth_entropy": vn_entropy(avg_nonorth),
            "ident_entropy": vn_entropy(avg_ident),
            "pass": vn_entropy(avg_orth) >= vn_entropy(avg_nonorth) >= vn_entropy(avg_ident) - EPS,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "holevo_quantity",
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
            "scope_note": "Direct local Holevo-quantity lego on bounded two-state qubit ensembles.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "holevo_quantity_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
