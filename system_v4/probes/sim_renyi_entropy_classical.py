#!/usr/bin/env python3
"""Classical baseline: Renyi entropy family H_alpha(p) = 1/(1-a) log sum p^a."""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "pmf power sums and log"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
    "z3": {"tried": False, "used": False, "reason": "no proof claim"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

def renyi(p, alpha):
    p = np.asarray(p, float); p = p[p > 0]
    if abs(alpha - 1.0) < 1e-12:
        return float(-np.sum(p * np.log2(p)))  # Shannon
    if alpha == float("inf"):
        return float(-np.log2(p.max()))
    if alpha == 0:
        return float(np.log2(len(p)))  # Hartley
    return float(np.log2(np.sum(p ** alpha)) / (1 - alpha))

def run_positive_tests():
    p = np.array([0.25, 0.25, 0.25, 0.25])
    # uniform: H_alpha = log2(n) for all alpha
    vals = [renyi(p, a) for a in [0, 0.5, 1.0, 2.0, 5.0, float("inf")]]
    return {
        "uniform_alpha_invariant": all(abs(v - 2.0) < 1e-10 for v in vals),
        "shannon_matches_alpha_one": abs(renyi([0.3,0.7], 1.0) -
                                         (-0.3*np.log2(0.3)-0.7*np.log2(0.7))) < 1e-10,
        "monotone_decreasing_in_alpha": (renyi([0.1,0.2,0.7], 0.5) >=
                                         renyi([0.1,0.2,0.7], 2.0) - 1e-10),
    }

def run_negative_tests():
    # Non-monotonicity across arbitrary alpha is NOT general; Renyi is non-increasing in alpha
    p = np.array([0.1, 0.3, 0.6])
    return {
        "nonincreasing_0_to_2": renyi(p, 0) >= renyi(p, 1) >= renyi(p, 2) - 1e-10,
        "hmin_le_hmax": renyi(p, float("inf")) <= renyi(p, 0) + 1e-10,
    }

def run_boundary_tests():
    p = np.array([1.0, 0.0, 0.0])
    return {
        "delta_zero_entropy": abs(renyi(p, 2.0)) < 1e-10,
        "alpha_zero_hartley": abs(renyi([0.5,0.5], 0) - 1.0) < 1e-10,
        "alpha_inf_minlog": abs(renyi([0.7,0.3], float("inf")) - (-np.log2(0.7))) < 1e-10,
    }

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "renyi_entropy_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump({
            "name": "renyi_entropy_classical",
            "classification": "classical_baseline",
            "tool_manifest": TOOL_MANIFEST,
            "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
            "positive": pos, "negative": neg, "boundary": bnd,
            "all_pass": all_pass, "summary": {"all_pass": all_pass},
            "divergence_log": [
                "classical Renyi acts on a single-basis pmf; misses sandwiched/Petz quantum Renyi divergences (distinct for noncommuting rho, sigma)",
                "no data-processing contraction distinguishing alpha<1 vs alpha>1 under nonunital channels",
                "cannot detect coherence spectrum (majorization on eigenvalues); classical sees only a diagonal",
                "lacks min/max entropy smoothing in the one-shot quantum sense (purified distance unavailable)",
            ],
        }, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
