#!/usr/bin/env python3
"""Classical baseline sim: branch_weight lego.

Lane B classical baseline (numpy-only). NOT canonical.
Captures: classical branch weight along a finite trajectory of Markov
transitions: P(a_1,...,a_n) = prod_t P(a_{t+1}|a_t) p(a_1). Branch weights
are always nonnegative and sum to 1 over all paths of length n.
Innately missing: quantum branch weight Tr(rho-tilde) after sequence of
CPTP operations with NO consistent product-probability structure between
noncommuting branches; decoherence-functional diagonality is required for
classical probability assignment to reappear.
"""
import json, os
from itertools import product
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "trajectory product arithmetic"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

def branch_weight(T, p0, path):
    # T[j,i] = P(j|i); path is tuple of state indices
    w = p0[path[0]]
    for t in range(len(path)-1):
        w *= T[path[t+1], path[t]]
    return float(w)

def enumerate_weights(T, p0, n):
    d = len(p0)
    weights = {}
    for path in product(range(d), repeat=n):
        weights[path] = branch_weight(T, p0, path)
    return weights

def run_positive_tests():
    T = np.array([[0.7, 0.4],[0.3, 0.6]])
    p0 = np.array([0.5, 0.5])
    W = enumerate_weights(T, p0, 3)
    s = sum(W.values())
    return {
        "weights_sum_to_1": abs(s - 1.0) < 1e-12,
        "weights_nonneg": all(w >= -1e-12 for w in W.values()),
    }

def run_negative_tests():
    # negative rate in T should produce negative branch weights (unphysical)
    T = np.array([[0.9, -0.1],[0.1, 1.1]])  # columns still sum to 1
    p0 = np.array([0.0, 1.0])
    W = enumerate_weights(T, p0, 2)
    return {
        "negative_transition_yields_negative_branch": any(w < -1e-10 for w in W.values()),
    }

def run_boundary_tests():
    # length-1 path: marginals equal initial distribution
    T = np.array([[0.6, 0.3],[0.4, 0.7]])
    p0 = np.array([0.5, 0.5])
    W = enumerate_weights(T, p0, 1)
    marginal = [W[(0,)], W[(1,)]]
    # consistency under marginalization: sum over first step path
    W2 = enumerate_weights(T, p0, 2)
    marg_end = np.zeros(2)
    for (a,b), w in W2.items():
        marg_end[b] += w
    expected_end = T @ p0
    return {
        "length1_equals_initial": np.allclose(marginal, p0, atol=1e-12),
        "marginalization_consistent": np.allclose(marg_end, expected_end, atol=1e-12),
    }

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "branch_weight_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": [
            "no off-diagonal decoherence-functional entries; cannot test consistent-histories diagonality",
            "branch weights always multiplicative; no interference between paths",
            "cannot represent quantum trajectory where Tr(rho-tilde) fails to factorize over paths",
        ],
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "branch_weight_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
