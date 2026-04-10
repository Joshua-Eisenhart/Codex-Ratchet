#!/usr/bin/env python3
"""
PURE LEGO: Conditional Entropy
==============================
Direct local bipartite entropy lego on bounded two-qubit states.
"""

import json
import pathlib
from datetime import datetime, timezone

import numpy as np


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for conditional entropy on bounded two-qubit states, kept "
    "separate from coherent information and seam-level files."
)

LEGO_IDS = [
    "conditional_entropy",
]

PRIMARY_LEGO_IDS = [
    "conditional_entropy",
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


def partial_trace(rho_ab, dim_a=2, dim_b=2, trace_out="B"):
    rho_ab = rho_ab.reshape(dim_a, dim_b, dim_a, dim_b)
    if trace_out == "B":
        return np.trace(rho_ab, axis1=1, axis2=3)
    return np.trace(rho_ab, axis1=0, axis2=2)


def vn_entropy(rho):
    evals = np.linalg.eigvalsh((rho + rho.conj().T) / 2)
    evals = np.maximum(evals, 0.0)
    evals = evals[evals > 1e-14]
    if evals.size == 0:
        return 0.0
    return float(-np.sum(evals * np.log2(evals)))


def conditional_entropy(rho_ab):
    rho_b = partial_trace(rho_ab, trace_out="A")
    return float(vn_entropy(rho_ab) - vn_entropy(rho_b))


def main():
    ket0 = ket([1, 0])
    ket1 = ket([0, 1])
    ketp = ket([1 / np.sqrt(2), 1 / np.sqrt(2)])

    prod_00 = np.kron(ket0, ket0) @ np.kron(ket0, ket0).conj().T
    prod_0p = np.kron(ket0, ketp) @ np.kron(ket0, ketp).conj().T

    bell_phi_p = ket([1, 0, 0, 1]) / np.sqrt(2)
    bell = bell_phi_p @ bell_phi_p.conj().T

    mixed_classical = 0.5 * dm([1, 0, 0, 0]) + 0.5 * dm([0, 0, 0, 1])

    s_prod_00 = conditional_entropy(prod_00)
    s_prod_0p = conditional_entropy(prod_0p)
    s_bell = conditional_entropy(bell)
    s_mixed = conditional_entropy(mixed_classical)

    positive = {
        "product_state_conditional_equals_local_entropy": {
            "value": s_prod_00,
            "pass": abs(s_prod_00 - vn_entropy(partial_trace(prod_00, trace_out='B'))) < EPS,
        },
        "bell_state_has_negative_conditional_entropy": {
            "value": s_bell,
            "pass": s_bell < -EPS,
        },
        "classical_mixture_has_nonnegative_conditional_entropy": {
            "value": s_mixed,
            "pass": s_mixed >= -EPS,
        },
    }

    negative = {
        "product_state_is_not_negative": {
            "value": s_prod_0p,
            "pass": s_prod_0p >= -EPS,
        },
        "bell_and_product_do_not_share_same_sign": {
            "bell": s_bell,
            "product": s_prod_0p,
            "pass": s_bell < 0.0 and s_prod_0p >= -EPS,
        },
    }

    boundary = {
        "pure_product_has_zero_conditional_entropy": {
            "value": s_prod_00,
            "pass": abs(s_prod_00) < EPS,
        },
        "independent_product_matches_marginal_entropy": {
            "value": s_prod_0p,
            "marginal_a_entropy": vn_entropy(partial_trace(prod_0p, trace_out="B")),
            "pass": abs(s_prod_0p - vn_entropy(partial_trace(prod_0p, trace_out="B"))) < EPS,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "conditional_entropy",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "scope_note": "Direct local conditional-entropy lego on bounded two-qubit product, Bell, and classical-mixture states.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "conditional_entropy_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
