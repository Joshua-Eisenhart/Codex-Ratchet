#!/usr/bin/env python3
"""Classical baseline sim: min_entropy / max_entropy lego.

Lane B classical baseline (numpy-only). NOT canonical.
Captures:
  H_min(p) = -log2 max_i p_i
  H_max(p) = log2 |supp(p)|
Innately missing: smooth one-shot quantum min/max entropies, their
operational meaning under CPTP channels, and noncommuting-support semantics.
"""
import json, os, math
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "max/support on pmf"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

def H_min(p):
    p = np.asarray(p, dtype=float)
    return float(-np.log2(np.max(p)))

def H_max(p):
    p = np.asarray(p, dtype=float)
    return float(np.log2(np.sum(p > 1e-15)))

def H_shan(p):
    p = np.asarray(p, dtype=float); p = p[p > 0]
    return float(-np.sum(p*np.log2(p)))

def run_positive_tests():
    u = np.array([0.25]*4)
    return {
        "uniform_min_equals_max": abs(H_min(u) - H_max(u)) < 1e-12,
        "uniform_min_is_2": abs(H_min(u) - 2.0) < 1e-12,
        "delta_min_zero": abs(H_min([1.0, 0.0])) < 1e-12,
    }

def run_negative_tests():
    return {
        "delta_max_zero": abs(H_max([1.0, 0.0])) < 1e-12,
        "nonneg_min": H_min([0.7, 0.3]) >= -1e-12,
    }

def run_boundary_tests():
    # Ordering: H_min <= H_shan <= H_max
    oks = []
    for _ in range(30):
        p = np.random.dirichlet(np.ones(6))
        oks.append(H_min(p) <= H_shan(p) + 1e-10 <= H_max(p) + 1e-10)
    return {
        "ordering_min_le_shan_le_max": all(oks),
    }

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "min_max_entropy_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": [
            "no smooth epsilon-ball around state (one-shot quantum notion)",
            "no operational channel-compression meaning",
            "cannot distinguish commuting vs noncommuting support",
        ],
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "min_max_entropy_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
