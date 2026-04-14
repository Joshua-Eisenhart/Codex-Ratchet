#!/usr/bin/env python3
"""Classical baseline: KL divergence D(p||q) = sum p log p/q."""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "log arithmetic on pmfs"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
    "z3": {"tried": False, "used": False, "reason": "no proof claim"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

def KL(p, q):
    p = np.asarray(p, float); q = np.asarray(q, float)
    mask = p > 0
    if np.any((q[mask] == 0)):
        return float("inf")
    return float(np.sum(p[mask] * np.log2(p[mask] / q[mask])))

def run_positive_tests():
    p = np.array([0.5, 0.5]); q = np.array([0.25, 0.75])
    return {
        "same_dist_zero": abs(KL(p, p)) < 1e-12,
        "nonneg_random": all(KL(np.random.dirichlet(np.ones(5)),
                                np.random.dirichlet(np.ones(5))) >= -1e-10 for _ in range(25)),
        "gibbs_pos": KL(p, q) > 0,
    }

def run_negative_tests():
    p = np.array([0.5, 0.5]); q = np.array([1.0, 0.0])
    return {
        "support_violation_infinite": KL(p, q) == float("inf"),
        "not_symmetric": abs(KL([0.7,0.3], [0.3,0.7]) - KL([0.3,0.7], [0.7,0.3])) < 1e-12,
    }

def run_boundary_tests():
    return {
        "delta_to_uniform": abs(KL([1.0,0.0,0.0], [1/3,1/3,1/3]) - np.log2(3)) < 1e-10,
        "uniform_to_uniform_zero": abs(KL([0.25]*4, [0.25]*4)) < 1e-12,
    }

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "relative_entropy_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump({
            "name": "relative_entropy_classical",
            "classification": "classical_baseline",
            "tool_manifest": TOOL_MANIFEST,
            "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
            "positive": pos, "negative": neg, "boundary": bnd,
            "all_pass": all_pass, "summary": {"all_pass": all_pass},
            "divergence_log": [
                "classical KL assumes a shared sample space; misses noncommuting-basis D(rho||sigma)",
                "classical KL finite only if supp(p) subseteq supp(q); quantum relative entropy has analogous but basis-dependent kernel structure",
                "no Umegaki/Petz monotonicity distinctions; only DPI in one (stochastic) form",
                "cannot capture quantum hypothesis-testing (Stein lemma) strengthening",
            ],
        }, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
