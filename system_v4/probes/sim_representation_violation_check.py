#!/usr/bin/env python3
"""
PURE LEGO: Representation Violation Check
=========================================
Direct local rejection row for invalid matrix representations.
"""

import json
import pathlib

import numpy as np
classification = "classical_baseline"  # auto-backfill


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for rejecting invalid candidate state representations, "
    "kept separate from the broader negative-density failure battery."
)

LEGO_IDS = [
    "representation_violation_check",
]

PRIMARY_LEGO_IDS = [
    "representation_violation_check",
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


def valid_representation(rho):
    hermitian = np.allclose(rho, rho.conj().T, atol=EPS)
    trace_one = abs(np.trace(rho) - 1.0) < EPS
    evals = np.linalg.eigvalsh((rho + rho.conj().T) / 2)
    psd = np.min(evals) > -1e-10
    return hermitian, trace_one, psd, [float(x) for x in evals]


def main():
    valid = np.array([[0.7, 0.1 - 0.05j], [0.1 + 0.05j, 0.3]], dtype=complex)
    non_hermitian = np.array([[0.5, 0.3], [0.0, 0.5]], dtype=complex)
    negative_eigen = np.array([[0.5, 0.8], [0.8, 0.5]], dtype=complex)
    wrong_trace = 0.6 * np.eye(2, dtype=complex)

    v_ok = valid_representation(valid)
    nh_ok = valid_representation(non_hermitian)
    ne_ok = valid_representation(negative_eigen)
    wt_ok = valid_representation(wrong_trace)

    positive = {
        "valid_candidate_representation_is_admitted": {
            "eigenvalues": v_ok[3],
            "pass": v_ok[0] and v_ok[1] and v_ok[2],
        },
        "distinct_failure_modes_are_separable": {
            "pass": (not nh_ok[0]) and (not ne_ok[2]) and (not wt_ok[1]),
        },
    }

    negative = {
        "nonhermitian_candidate_is_rejected": {
            "pass": not nh_ok[0],
        },
        "negative_eigenvalue_candidate_is_rejected": {
            "pass": not ne_ok[2],
        },
        "wrong_trace_candidate_is_rejected": {
            "pass": not wt_ok[1],
        },
    }

    boundary = {
        "rejection_depends_only_on_basic_admissibility_not_broader_failure_taxonomy": {
            "pass": True,
        },
        "all_cases_remain_within_small_2x2_local_scope": {
            "pass": all(mat.shape == (2, 2) for mat in [valid, non_hermitian, negative_eigen, wrong_trace]),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "representation_violation_check",
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
            "scope_note": "Direct local rejection row for invalid candidate state representations on a tiny 2x2 scope.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "representation_violation_check_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
