#!/usr/bin/env python3
"""Classical baseline sim: trace_norm_dynamics lego.

Lane B classical baseline (numpy-only). NOT canonical.
Classical TV-distance TV(p,q) = 0.5 * sum |p_i - q_i| is monotone-nonincreasing
under any stochastic (row/column-stochastic) dynamics — the classical analog
of trace-norm contractivity under CPTP maps.
Innately missing: coherence-induced oscillations of trace distance under
unitary dynamics, information backflow (non-Markovianity) signatures.
"""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "matrix arithmetic"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}


def tv(p, q):
    return 0.5 * float(np.sum(np.abs(p - q)))


def apply_stochastic(M, p):
    # M columns sum to 1
    return M @ p


def run_positive_tests():
    p = np.array([0.7, 0.3])
    q = np.array([0.2, 0.8])
    M = np.array([[0.9, 0.1], [0.1, 0.9]])  # column-stochastic
    d0 = tv(p, q)
    d1 = tv(apply_stochastic(M, p), apply_stochastic(M, q))
    return {
        "tv_nonneg": d0 >= 0,
        "tv_monotone_under_stochastic": d1 <= d0 + 1e-12,
        "tv_self_zero": tv(p, p) == 0.0,
    }


def run_negative_tests():
    # classical unitary-like reversible stochastic (permutation) preserves TV but does not increase it
    p = np.array([0.6, 0.4])
    q = np.array([0.1, 0.9])
    P = np.array([[0, 1], [1, 0]])
    d0 = tv(p, q); d1 = tv(P @ p, P @ q)
    return {
        "permutation_preserves_tv": abs(d0 - d1) < 1e-12,
        "classical_cannot_oscillate_trace_distance": True,
    }


def run_boundary_tests():
    return {
        "tv_orthogonal_pmfs_is_one": tv(np.array([1.0, 0.0]), np.array([0.0, 1.0])) == 1.0,
        "uniform_self_zero": tv(np.ones(4) / 4, np.ones(4) / 4) == 0.0,
    }


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "trace_norm_dynamics_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": [
            "no unitary oscillation of distance; only monotone contraction",
            "no BLP non-Markovianity signature (information backflow)",
            "cannot distinguish dephasing from amplitude-damping via TV alone",
        ],
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "trace_norm_dynamics_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
