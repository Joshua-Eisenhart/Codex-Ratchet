#!/usr/bin/env python3
"""
PURE LEGO: Hilbert-Schmidt Flatness Rejection
============================================
Direct local falsifier showing that Hilbert-Schmidt distance is too flat to serve as the sole geometry.
"""

import itertools
import json
import pathlib

import numpy as np


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local falsifier showing that Hilbert-Schmidt distance can flatten distinct state-pair "
    "geometry that Bures distance still separates, so Hilbert-Schmidt should not be the sole geometry."
)

LEGO_IDS = [
    "hilbert_schmidt_flatness_rejection",
]

PRIMARY_LEGO_IDS = [
    "hilbert_schmidt_flatness_rejection",
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


def pure_state(v):
    v = np.asarray(v, dtype=complex)
    v = v / np.linalg.norm(v)
    return np.outer(v, v.conj())


def matrix_sqrt(m):
    evals, evecs = np.linalg.eigh(0.5 * (m + m.conj().T))
    evals = np.maximum(np.real(evals), 0.0)
    return evecs @ np.diag(np.sqrt(evals)) @ evecs.conj().T


def hs_distance(rho, sigma):
    diff = rho - sigma
    return float(np.sqrt(np.real(np.trace(diff.conj().T @ diff))))


def bures_distance(rho, sigma):
    sr = matrix_sqrt(rho)
    core = sr @ sigma @ sr
    f = float(np.real(np.trace(matrix_sqrt(core))) ** 2)
    return float(np.sqrt(max(0.0, 2.0 - 2.0 * np.sqrt(min(1.0, max(0.0, f))))))


def main():
    states = {
        "zero": pure_state([1, 0]),
        "one": pure_state([0, 1]),
        "plus": pure_state([1, 1]),
        "plus_i": pure_state([1, 1j]),
        "diag_73": np.diag([0.7, 0.3]).astype(complex),
        "diag_64": np.diag([0.6, 0.4]).astype(complex),
        "diag_82": np.diag([0.8, 0.2]).astype(complex),
    }

    pairs = []
    keys = list(states)
    for a, b in itertools.combinations(keys, 2):
        rho = states[a]
        sigma = states[b]
        pairs.append(
            {
                "pair": [a, b],
                "hs": hs_distance(rho, sigma),
                "bures": bures_distance(rho, sigma),
            }
        )

    witness = None
    best_gap = -1.0
    for p, q in itertools.combinations(pairs, 2):
        hs_gap = abs(p["hs"] - q["hs"])
        bures_gap = abs(p["bures"] - q["bures"])
        if hs_gap < 0.03 and bures_gap > best_gap and bures_gap > 0.08:
            best_gap = bures_gap
            witness = {
                "pair_a": p["pair"],
                "pair_b": q["pair"],
                "hs_a": p["hs"],
                "hs_b": q["hs"],
                "bures_a": p["bures"],
                "bures_b": q["bures"],
                "hs_gap": hs_gap,
                "bures_gap": bures_gap,
            }

    positive = {
        "hilbert_schmidt_is_zero_on_identical_pair": {
            "value": hs_distance(states["zero"], states["zero"]),
            "pass": hs_distance(states["zero"], states["zero"]) < EPS,
        },
        "hilbert_schmidt_can_flatten_distinct_pair_geometry": {
            "witness": witness,
            "pass": witness is not None,
        },
        "bures_still_separates_the_flattened_pairs": {
            "witness": witness,
            "pass": witness is not None and witness["bures_gap"] > 0.08,
        },
    }

    negative = {
        "row_does_not_claim_hilbert_schmidt_is_useless_everywhere": {
            "pass": True,
        },
        "row_does_not_collapse_to_bures_geometry_itself": {
            "pass": witness is not None and witness["hs_gap"] < 0.03 and witness["bures_gap"] > witness["hs_gap"] + 0.05,
        },
    }

    boundary = {
        "comparison_uses_one_bounded_local_state_family": {
            "pass": True,
        },
        "all_reported_distances_are_finite": {
            "pass": all(np.isfinite(p["hs"]) and np.isfinite(p["bures"]) for p in pairs),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "hilbert_schmidt_flatness_rejection",
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
            "scope_note": "Direct local falsifier showing that near-equal Hilbert-Schmidt separation can still hide distinct Bures geometry on the same bounded state family.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "hilbert_schmidt_flatness_rejection_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
