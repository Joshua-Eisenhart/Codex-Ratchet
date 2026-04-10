#!/usr/bin/env python3
"""
PURE LEGO: Mutual Information Measure
=====================================
Direct local bipartite/correlation lego on bounded two-qubit states.
"""

import json
import pathlib

import numpy as np


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for mutual information on bounded two-qubit joint states."
)

LEGO_IDS = [
    "mutual_information_measure",
    "joint_density_matrix",
    "reduced_state_object",
]

PRIMARY_LEGO_IDS = [
    "mutual_information_measure",
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


def partial_trace_B(rho, da=2, db=2):
    rho = rho.reshape(da, db, da, db)
    return np.trace(rho, axis1=1, axis2=3)


def partial_trace_A(rho, da=2, db=2):
    rho = rho.reshape(da, db, da, db)
    return np.trace(rho, axis1=0, axis2=2)


def entropy(rho):
    evals = np.linalg.eigvalsh((rho + rho.conj().T) / 2)
    evals = evals[evals > 1e-15]
    return float(-np.sum(evals * np.log2(evals))) if len(evals) else 0.0


def mutual_information(rho_ab):
    rho_a = partial_trace_B(rho_ab)
    rho_b = partial_trace_A(rho_ab)
    return float(entropy(rho_a) + entropy(rho_b) - entropy(rho_ab))


def main():
    k0 = [1, 0]
    k1 = [0, 1]
    prod = dm(np.kron(k0, k1))
    classical = 0.5 * dm(np.kron(k0, k0)) + 0.5 * dm(np.kron(k1, k1))
    bell = dm((np.kron(k0, k0) + np.kron(k1, k1)) / np.sqrt(2))

    mi_prod = mutual_information(prod)
    mi_classical = mutual_information(classical)
    mi_bell = mutual_information(bell)

    positive = {
        "product_state_has_zero_mutual_information": {
            "value": mi_prod,
            "pass": abs(mi_prod) < EPS,
        },
        "classical_correlation_has_positive_mutual_information": {
            "value": mi_classical,
            "pass": mi_classical > 0.0,
        },
        "bell_state_has_positive_mutual_information": {
            "value": mi_bell,
            "pass": mi_bell > 0.0,
        },
    }

    negative = {
        "bell_exceeds_product_correlation": {
            "pass": mi_bell > mi_prod + EPS,
        },
        "classical_exceeds_product_correlation": {
            "pass": mi_classical > mi_prod + EPS,
        },
    }

    boundary = {
        "bell_and_classical_examples_agree_on_nonnegativity": {
            "pass": mi_bell >= -EPS and mi_classical >= -EPS,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "mutual_information_measure",
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
            "scope_note": "Direct local mutual-information lego on bounded two-qubit states.",
        },
    }

    out_path = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results" / "mutual_information_measure_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
