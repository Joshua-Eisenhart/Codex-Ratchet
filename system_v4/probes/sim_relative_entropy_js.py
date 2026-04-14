#!/usr/bin/env python3
"""
PURE LEGO: Relative Entropy JS
==============================
Direct local symmetric entropy-comparison lego on bounded qubit state pairs.
"""

import json
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for Jensen-Shannon-style symmetric entropy comparison on bounded "
    "qubit state pairs, kept separate from directional relative entropy and geometry rows."
)

LEGO_IDS = [
    "relative_entropy_js",
]

PRIMARY_LEGO_IDS = [
    "relative_entropy_js",
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


def js_entropy_divergence(rho, sigma):
    mid = 0.5 * (rho + sigma)
    return float(vn_entropy(mid) - 0.5 * vn_entropy(rho) - 0.5 * vn_entropy(sigma))


def main():
    zero = pure_state([1, 0])
    one = pure_state([0, 1])
    plus = pure_state([1, 1])
    mm = np.eye(2, dtype=complex) / 2.0
    near_a = np.diag([0.7, 0.3]).astype(complex)
    near_b = np.diag([0.6, 0.4]).astype(complex)

    js_ident = js_entropy_divergence(zero, zero)
    js_orth = js_entropy_divergence(zero, one)
    js_nonorth = js_entropy_divergence(zero, plus)
    js_pure_mixed = js_entropy_divergence(zero, mm)
    js_near = js_entropy_divergence(near_a, near_b)

    positive = {
        "identical_pair_has_zero_js": {
            "value": js_ident,
            "pass": abs(js_ident) < EPS,
        },
        "symmetry_holds": {
            "zero_plus": js_nonorth,
            "plus_zero": js_entropy_divergence(plus, zero),
            "pass": abs(js_nonorth - js_entropy_divergence(plus, zero)) < EPS,
        },
        "all_nonidentical_pairs_are_positive": {
            "orthogonal": js_orth,
            "nonorthogonal": js_nonorth,
            "pure_mixed": js_pure_mixed,
            "nearby_mixed": js_near,
            "pass": min(js_orth, js_nonorth, js_pure_mixed, js_near) > EPS,
        },
    }

    negative = {
        "orthogonal_pure_pair_exceeds_nonorthogonal_pure_pair": {
            "orthogonal": js_orth,
            "nonorthogonal": js_nonorth,
            "pass": js_orth > js_nonorth + EPS,
        },
        "nearby_mixed_pair_is_smaller_than_pure_separated_pairs": {
            "nearby_mixed": js_near,
            "nonorthogonal": js_nonorth,
            "orthogonal": js_orth,
            "pass": js_near < js_nonorth - EPS and js_near < js_orth - EPS,
        },
    }

    boundary = {
        "bounded_local_ordering_holds": {
            "identical": js_ident,
            "nearby_mixed": js_near,
            "nonorthogonal": js_nonorth,
            "orthogonal": js_orth,
            "pass": js_ident < js_near < js_nonorth < js_orth,
        },
        "pure_vs_mixed_sits_between_identical_and_orthogonal": {
            "pure_vs_mixed": js_pure_mixed,
            "pass": js_ident < js_pure_mixed < js_orth,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "relative_entropy_js",
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
            "scope_note": "Direct local symmetric JS-style entropy-comparison lego on bounded qubit state pairs.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "relative_entropy_js_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
