#!/usr/bin/env python3
"""Classical baseline sim: shannon_entropy lego.

Lane B classical baseline (numpy-only). NOT canonical.
Captures: H(p) = -sum p_i log p_i on discrete distributions.
Innately missing: probe-relative distinguishability context. Shannon
entropy presumes a fixed classical alphabet with distinguishable outcomes.
It cannot see noncommuting observable families, indistinguishability
classes under admissible probes, or shell-local coupling constraints.
"""
import json, os, math
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "log/sum on discrete pmf"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
    "z3": {"tried": False, "used": False, "reason": "no constraint admissibility claim"},
    "sympy": {"tried": False, "used": False, "reason": "not needed for numeric entropy"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

def H(p):
    p = np.asarray(p, dtype=float)
    p = p[p > 0]
    return float(-np.sum(p * np.log2(p)))

def run_positive_tests():
    return {
        "uniform_2_is_1_bit": abs(H([0.5, 0.5]) - 1.0) < 1e-12,
        "uniform_4_is_2_bits": abs(H([0.25]*4) - 2.0) < 1e-12,
        "nonneg_on_random": all(H(np.random.dirichlet(np.ones(5))) >= -1e-12 for _ in range(20)),
    }

def run_negative_tests():
    return {
        "delta_is_zero": abs(H([1.0, 0.0, 0.0])) < 1e-12,
        "no_negative_entropy": H([0.9, 0.1]) >= 0.0,
    }

def run_boundary_tests():
    # concavity: H(0.5p + 0.5q) >= 0.5 H(p) + 0.5 H(q)
    p = np.array([0.8, 0.2]); q = np.array([0.2, 0.8])
    mix = 0.5*p + 0.5*q
    return {
        "concavity": H(mix) + 1e-12 >= 0.5*H(p) + 0.5*H(q),
        "bounded_by_log_n": H([1/3, 1/3, 1/3]) <= math.log2(3) + 1e-12,
    }

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "shannon_entropy_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": [
            "cannot encode noncommuting observable families",
            "presumes fixed classical alphabet with distinguishable outcomes",
            "blind to probe-relative indistinguishability classes",
            "no shell-coupling or admissibility structure",
        ],
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "shannon_entropy_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
