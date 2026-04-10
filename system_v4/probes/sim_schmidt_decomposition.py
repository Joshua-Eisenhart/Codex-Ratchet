#!/usr/bin/env python3
"""
PURE LEGO: Schmidt Decomposition
================================
Direct local bipartite lego.

Factor small 2-qubit pure states, compare Schmidt coefficients to reduced-state
spectrum, and verify exact reconstruction.
"""

import json
import pathlib

import numpy as np


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for Schmidt decomposition on bounded bipartite pure states."
)

LEGO_IDS = [
    "schmidt_decomposition",
    "partial_trace_operator",
    "reduced_state_object",
]

PRIMARY_LEGO_IDS = [
    "schmidt_decomposition",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed -- direct numpy SVD lego"},
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


def partial_trace_B(rho, da=2, db=2):
    rho = rho.reshape(da, db, da, db)
    return np.trace(rho, axis1=1, axis2=3)


def schmidt_data(psi):
    amp = np.array(psi, dtype=complex).reshape(2, 2)
    u, s, vh = np.linalg.svd(amp, full_matrices=False)
    recon = u @ np.diag(s) @ vh
    rho_ab = np.outer(psi, psi.conj())
    rho_a = partial_trace_B(rho_ab)
    rho_a_eigs = sorted(np.linalg.eigvalsh((rho_a + rho_a.conj().T) / 2), reverse=True)
    return {
        "coefficients": [float(x) for x in s],
        "rank": int(np.sum(s > EPS)),
        "reconstruction_error": float(np.linalg.norm(recon - amp)),
        "reduced_state_eigenvalues": [float(x) for x in rho_a_eigs],
    }


def main():
    prod = np.array([1, 0, 0, 0], dtype=complex)
    bell = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
    partial = np.array([np.sqrt(0.8), 0, 0, np.sqrt(0.2)], dtype=complex)

    prod_data = schmidt_data(prod)
    bell_data = schmidt_data(bell)
    partial_data = schmidt_data(partial)

    positive = {
        "product_state_has_rank_one": {
            **prod_data,
            "pass": (
                prod_data["rank"] == 1
                and np.allclose(prod_data["coefficients"], [1.0, 0.0], atol=EPS)
                and np.allclose(prod_data["reduced_state_eigenvalues"], [1.0, 0.0], atol=EPS)
                and prod_data["reconstruction_error"] < EPS
            ),
        },
        "bell_state_has_equal_schmidt_coefficients": {
            **bell_data,
            "pass": (
                bell_data["rank"] == 2
                and np.allclose(bell_data["coefficients"], [1 / np.sqrt(2), 1 / np.sqrt(2)], atol=EPS)
                and np.allclose(bell_data["reduced_state_eigenvalues"], [0.5, 0.5], atol=EPS)
                and bell_data["reconstruction_error"] < EPS
            ),
        },
        "partially_entangled_state_matches_reduced_spectrum": {
            **partial_data,
            "pass": (
                partial_data["rank"] == 2
                and np.allclose(
                    np.square(partial_data["coefficients"]),
                    partial_data["reduced_state_eigenvalues"],
                    atol=EPS,
                )
                and partial_data["reconstruction_error"] < EPS
            ),
        },
    }

    negative = {
        "product_state_is_not_rank_two": {
            "pass": prod_data["rank"] != 2,
        },
        "bell_state_is_not_rank_one": {
            "pass": bell_data["rank"] != 1,
        },
    }

    boundary = {
        "schmidt_squares_equal_reduced_eigenvalues_for_all_cases": {
            "pass": all(
                np.allclose(
                    np.square(case["coefficients"]),
                    case["reduced_state_eigenvalues"],
                    atol=EPS,
                )
                for case in [prod_data, bell_data, partial_data]
            ),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "schmidt_decomposition",
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
            "scope_note": "Direct local Schmidt-factorization lego on bounded two-qubit pure states.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "schmidt_decomposition_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
