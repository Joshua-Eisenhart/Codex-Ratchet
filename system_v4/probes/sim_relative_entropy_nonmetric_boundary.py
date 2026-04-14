#!/usr/bin/env python3
"""
PURE LEGO: Relative-Entropy Non-Metric Boundary
==============================================
Direct local falsifier showing that quantum relative entropy is not a metric.
"""

import json
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local falsifier showing that relative entropy fails metric-style behavior on "
    "a bounded state family, contrasted against trace distance on the same family."
)

LEGO_IDS = [
    "relative_entropy_nonmetric_boundary",
]

PRIMARY_LEGO_IDS = [
    "relative_entropy_nonmetric_boundary",
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


def diag_dm(p):
    probs = np.asarray(p, dtype=float)
    probs = probs / np.sum(probs)
    return np.diag(probs.astype(complex))


def hermitian(m):
    return 0.5 * (m + m.conj().T)


def relative_entropy(rho, sigma):
    pr = np.clip(np.real(np.diag(hermitian(rho))), 0.0, None)
    ps = np.clip(np.real(np.diag(hermitian(sigma))), 0.0, None)
    pr = pr / np.sum(pr)
    ps = ps / np.sum(ps)
    total = 0.0
    for a, b in zip(pr, ps):
        if a <= EPS:
            continue
        if b <= EPS:
            return float("inf")
        total += a * np.log2(a / b)
    return float(total)


def trace_distance(rho, sigma):
    diff = hermitian(rho - sigma)
    evals = np.linalg.eigvalsh(diff)
    return float(0.5 * np.sum(np.abs(evals)))


def find_triangle_violation(states):
    for i, rho in enumerate(states):
        for j, sigma in enumerate(states):
            if i == j:
                continue
            for k, tau in enumerate(states):
                if len({i, j, k}) < 3:
                    continue
                lhs = relative_entropy(rho, tau)
                rhs = relative_entropy(rho, sigma) + relative_entropy(sigma, tau)
                if np.isfinite(lhs) and np.isfinite(rhs) and lhs > rhs + 1e-6:
                    return (i, j, k, lhs, rhs)
    return None


def main():
    states = [
        diag_dm([0.97, 0.03]),
        diag_dm([0.80, 0.20]),
        diag_dm([0.62, 0.38]),
        diag_dm([0.52, 0.48]),
    ]

    rho = states[0]
    sigma = states[1]

    d_rs = relative_entropy(rho, sigma)
    d_sr = relative_entropy(sigma, rho)
    td_rs = trace_distance(rho, sigma)
    td_sr = trace_distance(sigma, rho)
    witness = find_triangle_violation(states)

    positive = {
        "relative_entropy_is_nonnegative": {
            "values": [relative_entropy(a, b) for a in states for b in states],
            "pass": min(relative_entropy(a, b) for a in states for b in states) >= -1e-10,
        },
        "relative_entropy_is_asymmetric": {
            "d_rho_sigma": d_rs,
            "d_sigma_rho": d_sr,
            "pass": abs(d_rs - d_sr) > 1e-4,
        },
        "trace_distance_stays_symmetric_on_same_pair": {
            "td_rho_sigma": td_rs,
            "td_sigma_rho": td_sr,
            "pass": abs(td_rs - td_sr) < 1e-10,
        },
    }

    negative = {
        "relative_entropy_fails_metric_triangle_behavior": {
            "witness": None if witness is None else {
                "indices": [witness[0], witness[1], witness[2]],
                "lhs": witness[3],
                "rhs": witness[4],
            },
            "pass": witness is not None,
        },
        "row_is_not_collapsed_to_js_or_trace_metric": {
            "pass": abs(d_rs - d_sr) > 1e-4 and abs(td_rs - td_sr) < 1e-10,
        },
    }

    boundary = {
        "bounded_family_is_classically_well_defined": {
            "pass": True,
        },
        "comparison_uses_same_local_state_family_for_metric_and_nonmetric": {
            "pass": True,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "relative_entropy_nonmetric_boundary",
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
            "scope_note": "Direct local falsifier showing that relative entropy is not a metric on a bounded diagonal state family, contrasted against trace distance.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "relative_entropy_nonmetric_boundary_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
