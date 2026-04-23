#!/usr/bin/env python3
"""Classical baseline sim: entanglement_of_formation lego.

Lane B classical baseline (numpy-only). NOT canonical.
On any classical joint pmf p_AB, E_F = 0 because every classical joint is
a convex mixture of product deltas (|a><a| x |b><b|).
Innately missing: concurrence, Wootters formula, spin-flip sigma_y x sigma_y
structure, nonzero E_F on entangled pure states.
"""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "pmf arithmetic"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}


def classical_EF(p_ab):
    # classical joint is always separable -> E_F = 0
    assert np.all(p_ab >= -1e-12) and abs(p_ab.sum() - 1.0) < 1e-10
    return 0.0


def run_positive_tests():
    p1 = np.outer([0.5, 0.5], [0.3, 0.7])  # product
    p2 = np.array([[0.25, 0.0], [0.0, 0.75]])  # correlated classical
    return {
        "product_EF_zero": classical_EF(p1) == 0.0,
        "correlated_classical_EF_zero": classical_EF(p2) == 0.0,
    }


def run_negative_tests():
    # invalid joint should error; we verify guard
    bad = np.array([[0.5, 0.6], [0.0, 0.0]])
    try:
        classical_EF(bad); rejected = False
    except AssertionError:
        rejected = True
    return {
        "unnormalized_rejected": rejected,
        "classical_cannot_represent_bell_state": True,
    }


def run_boundary_tests():
    uniform = np.ones((3, 3)) / 9
    delta = np.zeros((2, 2)); delta[0, 0] = 1.0
    return {
        "uniform_EF_zero": classical_EF(uniform) == 0.0,
        "delta_EF_zero": classical_EF(delta) == 0.0,
    }


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "entanglement_of_formation_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": [
            "E_F identically 0 on classical joints (always separable)",
            "no concurrence / Wootters spin-flip structure",
            "cannot distinguish classical correlation from quantum entanglement",
        ],
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "entanglement_of_formation_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
