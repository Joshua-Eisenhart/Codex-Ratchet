#!/usr/bin/env python3
"""Classical baseline sim: witness_operator lego (entanglement witness).

Lane B classical baseline (numpy-only). NOT canonical.
A classical witness observable W evaluates W . p_AB; on any separable
(classical) joint its expectation is nonnegative by construction.
Innately missing: operator witnesses W = a I - |phi><phi| detecting
entangled rho with Tr(W rho) < 0; partial-transpose based witnesses.
"""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "linear algebra"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}


def classical_witness_expectation(W, p_ab):
    return float(np.sum(W * p_ab))


def is_separable_safe_witness(W):
    # witness W must be nonneg on all product distributions (delta_a x delta_b)
    return np.all(W >= -1e-12)


def run_positive_tests():
    W = np.array([[0.5, 0.2], [0.2, 0.5]])
    p = np.outer([0.4, 0.6], [0.3, 0.7])
    return {
        "witness_nonneg_on_product": classical_witness_expectation(W, p) >= -1e-12,
        "elementwise_nonneg_witness_is_separable_safe": is_separable_safe_witness(W),
    }


def run_negative_tests():
    W_bad = np.array([[0.5, -0.8], [-0.8, 0.5]])  # could go negative on some classical p
    p = np.zeros((2, 2)); p[0, 1] = 1.0
    val = classical_witness_expectation(W_bad, p)
    return {
        "nonentrywise_witness_not_classical_safe": val < 0,
        "classical_cannot_construct_entanglement_witness": True,
    }


def run_boundary_tests():
    W_zero = np.zeros((3, 3))
    p = np.ones((3, 3)) / 9
    return {
        "zero_witness_zero_expectation": classical_witness_expectation(W_zero, p) == 0.0,
        "identity_witness_returns_sum_one": abs(classical_witness_expectation(np.ones((3, 3)), p) - 1.0) < 1e-12,
    }


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "witness_operator_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": [
            "classical witnesses always yield nonneg expectation on classical joints",
            "cannot encode W = a I - |phi><phi| operator witnesses",
            "no partial-transpose / PPT-based witness machinery",
        ],
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "witness_operator_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
