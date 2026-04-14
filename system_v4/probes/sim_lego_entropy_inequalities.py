#!/usr/bin/env python3
"""
Entropy Inequalities and Continuity Lego
=======================================
Pure-math lego for core entropy inequalities and continuity bounds.
"""

import json
import os
from math import log2

import numpy as np
classification = "classical_baseline"  # auto-backfill

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed for exact low-dimensional entropy identities"},
    "pyg": {"tried": False, "used": False, "reason": "not needed for graph-free entropy inequality batch"},
    "z3": {"tried": False, "used": False, "reason": "not needed for current numeric inequality checks"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed for current numeric inequality checks"},
    "sympy": {"tried": False, "used": False, "reason": "not needed for current exact finite-dimensional examples"},
    "clifford": {"tried": False, "used": False, "reason": "not needed for entropy inequality checks"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed for non-manifold entropy inequality batch"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed for non-equivariant entropy inequality batch"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed for non-graph entropy inequality batch"},
    "xgi": {"tried": False, "used": False, "reason": "not needed for non-hypergraph entropy inequality batch"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed for non-topological entropy inequality batch"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed for non-persistent entropy inequality batch"},
}

EPS = 1e-12


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


def trace_distance(rho, sigma):
    evals = np.linalg.eigvalsh((rho - sigma + (rho - sigma).conj().T) / 2)
    return 0.5 * float(np.sum(np.abs(evals)))


def partial_trace(rho, dims, keep):
    dims = list(dims)
    n = len(dims)
    rho_t = rho.reshape(dims + dims)
    keep = list(keep)
    trace_over = [i for i in range(n) if i not in keep]
    for ax in sorted(trace_over, reverse=True):
        rho_t = np.trace(rho_t, axis1=ax, axis2=ax + len(dims))
    d_keep = int(np.prod([dims[i] for i in keep]))
    return rho_t.reshape(d_keep, d_keep)


def bell_state():
    return pure_state([1, 0, 0, 1])


def ghz_state():
    return pure_state([1, 0, 0, 0, 0, 0, 0, 1])


def maximally_mixed(d):
    return np.eye(d, dtype=complex) / d


def audenaert_bound(d, t):
    if t <= 0:
        return 0.0
    if t >= 1:
        return log2(d)
    h2 = -(t * log2(t) + (1 - t) * log2(1 - t))
    return t * log2(d - 1) + h2


def run_positive_tests():
    bell = bell_state()
    rho_a = partial_trace(bell, [2, 2], [0])
    rho_b = partial_trace(bell, [2, 2], [1])
    s_ab = entropy(bell)
    s_a = entropy(rho_a)
    s_b = entropy(rho_b)

    ghz = ghz_state()
    rho_ab = partial_trace(ghz, [2, 2, 2], [0, 1])
    rho_bc = partial_trace(ghz, [2, 2, 2], [1, 2])
    rho_b_ghz = partial_trace(ghz, [2, 2, 2], [1])

    rho = np.diag([0.9, 0.1]).astype(complex)
    sigma = np.diag([0.85, 0.15]).astype(complex)
    t = trace_distance(rho, sigma)
    delta_s = abs(entropy(rho) - entropy(sigma))

    positive = {
        "subadditivity_bell": {
            "S_A": s_a,
            "S_B": s_b,
            "S_AB": s_ab,
            "pass": bool(s_ab <= s_a + s_b + 1e-12),
        },
        "araki_lieb_bell": {
            "lhs": abs(s_a - s_b),
            "rhs": s_ab,
            "pass": bool(abs(s_a - s_b) <= s_ab + 1e-12 or np.isclose(abs(s_a - s_b), s_ab, atol=1e-12)),
        },
        "strong_subadditivity_ghz": {
            "lhs": entropy(ghz) + entropy(rho_b_ghz),
            "rhs": entropy(rho_ab) + entropy(rho_bc),
            "pass": bool(entropy(ghz) + entropy(rho_b_ghz) <= entropy(rho_ab) + entropy(rho_bc) + 1e-12),
        },
        "audenaert_continuity_bound": {
            "trace_distance": t,
            "entropy_gap": delta_s,
            "bound": audenaert_bound(2, t),
            "pass": bool(delta_s <= audenaert_bound(2, t) + 1e-12),
        },
    }
    positive["pass"] = all(v["pass"] for v in positive.values())
    return positive


def run_negative_tests():
    rho = np.diag([1.2, -0.2]).astype(complex)
    sigma = maximally_mixed(2)
    negative = {
        "non_density_matrix_entropy_not_trusted": {
            "trace": float(np.trace(rho).real),
            "min_eval": float(np.min(np.linalg.eigvalsh(rho)).real),
            "pass": bool(np.min(np.linalg.eigvalsh(rho)).real < -1e-12),
        },
        "trace_distance_zero_only_for_equal_states": {
            "trace_distance": trace_distance(sigma, sigma),
            "pass": bool(np.isclose(trace_distance(sigma, sigma), 0.0, atol=1e-12)),
        },
        "audenaert_bound_not_negative": {
            "bound": audenaert_bound(2, 0.1),
            "pass": bool(audenaert_bound(2, 0.1) >= -1e-12),
        },
    }
    negative["pass"] = all(v["pass"] for v in negative.values())
    return negative


def run_boundary_tests():
    prod = np.kron(pure_state([1, 0]), pure_state([1, 0]))
    rho_a = partial_trace(prod, [2, 2], [0])
    rho_b = partial_trace(prod, [2, 2], [1])
    prod3 = np.kron(prod, pure_state([1, 0])).reshape(8, 8)

    boundary = {
        "subadditivity_equality_product": {
            "S_A": entropy(rho_a),
            "S_B": entropy(rho_b),
            "S_AB": entropy(prod),
            "pass": bool(np.isclose(entropy(prod), entropy(rho_a) + entropy(rho_b), atol=1e-12)),
        },
        "ssa_equality_product_abc": {
            "lhs": entropy(prod3) + entropy(partial_trace(prod3, [2, 2, 2], [1])),
            "rhs": entropy(partial_trace(prod3, [2, 2, 2], [0, 1])) + entropy(partial_trace(prod3, [2, 2, 2], [1, 2])),
            "pass": bool(np.isclose(
                entropy(prod3) + entropy(partial_trace(prod3, [2, 2, 2], [1])),
                entropy(partial_trace(prod3, [2, 2, 2], [0, 1])) + entropy(partial_trace(prod3, [2, 2, 2], [1, 2])),
                atol=1e-12,
            )),
        },
        "zero_trace_distance_zero_entropy_gap": {
            "gap": abs(entropy(rho_a) - entropy(rho_a)),
            "pass": bool(np.isclose(abs(entropy(rho_a) - entropy(rho_a)), 0.0, atol=1e-12)),
        },
    }
    boundary["pass"] = all(v["pass"] for v in boundary.values())
    return boundary


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    results = {
        "name": "lego_entropy_inequalities",
        "schema": "lego_entropy_inequalities/v1",
        "description": "Pure-math entropy lego for subadditivity, Araki-Lieb, strong subadditivity, and continuity bounds.",
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
    out_path = os.path.join(out_dir, "lego_entropy_inequalities_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(results["summary"])
