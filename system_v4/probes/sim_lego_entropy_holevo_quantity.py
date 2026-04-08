#!/usr/bin/env python3
"""
Holevo Quantity Entropy Lego
===========================
Pure-math lego for cq-ensemble entropy relations and simple channel-entropy bounds.
"""

import json
import os
from math import log2

import numpy as np

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed for cq ensemble entropy algebra"},
    "pyg": {"tried": False, "used": False, "reason": "not needed for graph-free entropy lego"},
    "z3": {"tried": False, "used": False, "reason": "not needed for this numerical entropy identity batch"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed for this numerical entropy identity batch"},
    "sympy": {"tried": False, "used": False, "reason": "not needed for current exact cases"},
    "clifford": {"tried": False, "used": False, "reason": "not needed for cq entropy relations"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed for this state-entropy lego"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed for this state-entropy lego"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed for non-graph entropy batch"},
    "xgi": {"tried": False, "used": False, "reason": "not needed for non-hypergraph entropy batch"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed for non-topological entropy batch"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed for non-persistent entropy batch"},
}

EPS = 1e-12
I2 = np.eye(2, dtype=complex)


def pure_state(vec):
    vec = np.asarray(vec, dtype=complex)
    vec = vec / np.linalg.norm(vec)
    return np.outer(vec, vec.conj())


def entropy(rho):
    evals = np.linalg.eigvalsh((rho + rho.conj().T) / 2)
    evals = np.clip(np.real(evals), 0.0, None)
    nz = evals[evals > EPS]
    if len(nz) == 0:
        return 0.0
    return float(-np.sum(nz * np.log2(nz)))


def dephase_z(rho, p):
    z = np.array([[1, 0], [0, -1]], dtype=complex)
    return (1 - p) * rho + p * (z @ rho @ z)


def holevo_quantity(probs, states):
    probs = np.asarray(probs, dtype=float)
    avg = np.zeros_like(states[0], dtype=complex)
    weighted = 0.0
    for p, rho in zip(probs, states):
        avg += p * rho
        weighted += p * entropy(rho)
    return float(entropy(avg) - weighted), avg


def binary_entropy(p):
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return float(-(p * log2(p) + (1 - p) * log2(1 - p)))


def run_positive_tests():
    zero = pure_state([1, 0])
    one = pure_state([0, 1])
    plus = pure_state([1, 1])

    chi_orth, avg_orth = holevo_quantity([0.5, 0.5], [zero, one])
    chi_ident, avg_ident = holevo_quantity([0.5, 0.5], [zero, zero])
    chi_nonorth, avg_nonorth = holevo_quantity([0.5, 0.5], [zero, plus])

    p = 0.25
    chi_before, avg_before = holevo_quantity([0.5, 0.5], [zero, plus])
    chi_after, avg_after = holevo_quantity([0.5, 0.5], [dephase_z(zero, p), dephase_z(plus, p)])

    positive = {
        "orthogonal_ensemble_one_bit": {
            "chi": chi_orth,
            "avg_entropy": entropy(avg_orth),
            "pass": bool(np.isclose(chi_orth, 1.0, atol=1e-12)),
        },
        "identical_states_zero_information": {
            "chi": chi_ident,
            "avg_entropy": entropy(avg_ident),
            "pass": bool(np.isclose(chi_ident, 0.0, atol=1e-12)),
        },
        "nonorthogonal_between_zero_and_one": {
            "chi": chi_nonorth,
            "avg_entropy": entropy(avg_nonorth),
            "pass": bool(EPS < chi_nonorth < 1.0 - EPS),
        },
        "holevo_bounded_by_output_entropy": {
            "chi": chi_nonorth,
            "output_entropy": entropy(avg_nonorth),
            "pass": bool(chi_nonorth <= entropy(avg_nonorth) + 1e-12),
        },
        "dephasing_does_not_increase_chi": {
            "chi_before": chi_before,
            "chi_after": chi_after,
            "avg_entropy_before": entropy(avg_before),
            "avg_entropy_after": entropy(avg_after),
            "pass": bool(chi_after <= chi_before + 1e-12),
        },
    }
    positive["pass"] = all(v["pass"] for v in positive.values())
    return positive


def run_negative_tests():
    zero = pure_state([1, 0])
    plus = pure_state([1, 1])

    chi, _ = holevo_quantity([0.5, 0.5], [zero, plus])
    negative = {
        "chi_never_negative": {
            "chi": chi,
            "pass": bool(chi >= -1e-12),
        },
        "qubit_chi_not_above_one": {
            "chi": chi,
            "pass": bool(chi <= 1.0 + 1e-12),
        },
        "average_entropy_not_less_than_zero": {
            "entropy_avg": entropy(0.5 * zero + 0.5 * plus),
            "pass": bool(entropy(0.5 * zero + 0.5 * plus) >= -1e-12),
        },
        "binary_entropy_caps_classical_qubit_case": {
            "H_half": binary_entropy(0.5),
            "pass": bool(np.isclose(binary_entropy(0.5), 1.0, atol=1e-12)),
        },
    }
    negative["pass"] = all(v["pass"] for v in negative.values())
    return negative


def run_boundary_tests():
    zero = pure_state([1, 0])
    one = pure_state([0, 1])

    chi_p0, _ = holevo_quantity([1.0, 0.0], [zero, one])
    chi_p1, _ = holevo_quantity([0.0, 1.0], [zero, one])
    chi_mixed, avg_mixed = holevo_quantity([0.5, 0.5], [zero, one])

    boundary = {
        "delta_ensemble_zero_info": {
            "chi_p0": chi_p0,
            "chi_p1": chi_p1,
            "pass": bool(np.isclose(chi_p0, 0.0, atol=1e-12) and np.isclose(chi_p1, 0.0, atol=1e-12)),
        },
        "maximally_mixed_average_reaches_one": {
            "chi": chi_mixed,
            "avg_entropy": entropy(avg_mixed),
            "pass": bool(np.isclose(chi_mixed, 1.0, atol=1e-12)),
        },
        "pure_state_ensemble_average_matches_binary_entropy": {
            "avg_entropy": entropy(0.75 * zero + 0.25 * one),
            "binary_entropy": binary_entropy(0.25),
            "pass": bool(np.isclose(entropy(0.75 * zero + 0.25 * one), binary_entropy(0.25), atol=1e-12)),
        },
    }
    boundary["pass"] = all(v["pass"] for v in boundary.values())
    return boundary


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    results = {
        "name": "lego_entropy_holevo_quantity",
        "schema": "lego_entropy_holevo_quantity/v1",
        "description": "Pure-math cq ensemble entropy lego for Holevo quantity and simple channel-entropy bounds.",
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "canonical",
        "summary": {
            "positive_pass": bool(positive["pass"]),
            "negative_pass": bool(negative["pass"]),
            "boundary_pass": bool(boundary["pass"]),
            "all_pass": bool(positive["pass"] and negative["pass"] and boundary["pass"]),
        },
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "lego_entropy_holevo_quantity_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(results["summary"])
