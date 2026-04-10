#!/usr/bin/env python3
"""
PURE LEGO: Entanglement Entropy
===============================
Direct local pure-state bipartite entropy lego on bounded two-qubit states.
"""

import json
import pathlib

import numpy as np


EPS = 1e-10

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical local lego for entanglement entropy on bounded pure two-qubit states, "
    "kept separate from entanglement spectrum, negativity, and broad bipartite bundles."
)

LEGO_IDS = [
    "entanglement_entropy",
]

PRIMARY_LEGO_IDS = [
    "entanglement_entropy",
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


def density_from_pure(psi):
    psi = np.asarray(psi, dtype=complex).reshape(4, 1)
    return psi @ psi.conj().T


def partial_trace_A(rho):
    rho = rho.reshape(2, 2, 2, 2)
    return np.trace(rho, axis1=0, axis2=2)


def partial_trace_B(rho):
    rho = rho.reshape(2, 2, 2, 2)
    return np.trace(rho, axis1=1, axis2=3)


def vn_entropy(rho):
    evals = np.linalg.eigvalsh((rho + rho.conj().T) / 2)
    evals = np.maximum(evals, 0.0)
    evals = evals[evals > 1e-14]
    if evals.size == 0:
        return 0.0
    return float(-np.sum(evals * np.log2(evals)))


def entanglement_entropy(psi):
    rho = density_from_pure(psi)
    return vn_entropy(partial_trace_B(rho))


def schmidt_family(theta):
    psi = np.array([np.cos(theta), 0.0, 0.0, np.sin(theta)], dtype=complex)
    return psi / np.linalg.norm(psi)


def main():
    psi_prod = np.array([1.0, 0.0, 0.0, 0.0], dtype=complex)
    psi_partial = schmidt_family(0.35)
    psi_bell = schmidt_family(np.pi / 4)

    rho_prod = density_from_pure(psi_prod)
    rho_partial = density_from_pure(psi_partial)
    rho_bell = density_from_pure(psi_bell)

    s_prod = entanglement_entropy(psi_prod)
    s_partial = entanglement_entropy(psi_partial)
    s_bell = entanglement_entropy(psi_bell)

    rho_a_partial = partial_trace_B(rho_partial)
    rho_b_partial = partial_trace_A(rho_partial)

    positive = {
        "product_state_has_zero_entanglement_entropy": {
            "value": s_prod,
            "pass": abs(s_prod) < EPS,
        },
        "bell_state_has_one_bit_entanglement_entropy": {
            "value": s_bell,
            "pass": abs(s_bell - 1.0) < EPS,
        },
        "reduced_state_entropies_match_for_pure_bipartite_state": {
            "entropy_A": vn_entropy(rho_a_partial),
            "entropy_B": vn_entropy(rho_b_partial),
            "pass": abs(vn_entropy(rho_a_partial) - vn_entropy(rho_b_partial)) < EPS,
        },
    }

    negative = {
        "partially_entangled_state_is_not_zero_or_maximal": {
            "value": s_partial,
            "pass": s_partial > EPS and s_partial < 1.0 - EPS,
        },
        "product_and_bell_do_not_share_same_entanglement_entropy": {
            "pass": abs(s_prod - s_bell) > EPS,
        },
    }

    boundary = {
        "schmidt_family_orders_entropy_monotonically_to_bell_point": {
            "product": s_prod,
            "partial": s_partial,
            "bell": s_bell,
            "pass": s_prod < s_partial < s_bell,
        },
        "entropy_is_basis_independent_under_local_phase_on_component": {
            "pass": abs(entanglement_entropy(np.array([np.cos(0.35), 0.0, 0.0, np.exp(1j * 0.8) * np.sin(0.35)], dtype=complex)) - s_partial) < EPS,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "entanglement_entropy",
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
            "scope_note": "Direct local entanglement-entropy lego on bounded pure two-qubit Schmidt-family states.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "entanglement_entropy_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
