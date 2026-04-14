#!/usr/bin/env python3
"""Classical baseline: Holevo bound lego.

Classically, accessible information equals mutual information I(X;Y) for
a classical channel; Holevo chi reduces to H(sum p_i rho_i) - sum p_i H(rho_i)
on commuting (diagonal) states = H(sum p_i p_i_vec) - sum p_i H(p_i_vec),
which is simply the Jensen/mixing entropy inequality (classical).
"""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "entropy arithmetic on pmfs"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
    "sympy": {"tried": False, "used": False, "reason": "not needed numerically"},
    "z3": {"tried": False, "used": False, "reason": "no proof claim"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

def H(p):
    p = np.asarray(p, float).ravel(); p = p[p > 0]
    return float(-np.sum(p * np.log2(p)))

def holevo_classical(priors, dists):
    """priors p_i, dists rows = classical states (pmfs)."""
    priors = np.asarray(priors, float); dists = np.asarray(dists, float)
    mix = priors @ dists
    return H(mix) - float(sum(p * H(d) for p, d in zip(priors, dists)))

def run_positive_tests():
    priors = np.array([0.5, 0.5])
    dists = np.array([[1.0, 0.0],[0.0, 1.0]])  # perfectly distinguishable
    chi_perfect = holevo_classical(priors, dists)
    # identical -> chi = 0
    dists_id = np.array([[0.3, 0.7],[0.3, 0.7]])
    chi_zero = holevo_classical(priors, dists_id)
    # general bound chi <= H(priors) with equality for orthogonal
    return {
        "perfect_distinguishable_chi_equals_Hpriors": abs(chi_perfect - H(priors)) < 1e-10,
        "identical_states_chi_zero": abs(chi_zero) < 1e-10,
        "nonneg_random": all(holevo_classical(
            np.random.dirichlet(np.ones(3)),
            np.array([np.random.dirichlet(np.ones(4)) for _ in range(3)])
        ) >= -1e-10 for _ in range(25)),
    }

def run_negative_tests():
    # classical chi cannot exceed H(priors)
    priors = np.array([0.3, 0.3, 0.4])
    dists = np.array([np.random.dirichlet(np.ones(5)) for _ in range(3)])
    return {
        "chi_bounded_by_Hpriors": holevo_classical(priors, dists) <= H(priors) + 1e-10,
        "chi_bounded_by_log_dim": holevo_classical(priors, dists) <= np.log2(5) + 1e-10,
    }

def run_boundary_tests():
    priors = np.array([1.0, 0.0])
    dists = np.array([[0.2, 0.8],[0.5, 0.5]])
    return {
        "degenerate_prior_chi_zero": abs(holevo_classical(priors, dists)) < 1e-10,
        "two_state_symmetric": abs(
            holevo_classical([0.5,0.5], [[0.9,0.1],[0.1,0.9]]) -
            holevo_classical([0.5,0.5], [[0.1,0.9],[0.9,0.1]])
        ) < 1e-10,
    }

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "holevo_bound_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump({
            "name": "holevo_bound_classical",
            "classification": "classical_baseline",
            "tool_manifest": TOOL_MANIFEST,
            "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
            "positive": pos, "negative": neg, "boundary": bnd,
            "all_pass": all_pass, "summary": {"all_pass": all_pass},
            "divergence_log": [
                "classical chi collapses to mixing entropy on commuting states; misses noncommuting rho_i",
                "no advantage from nonorthogonal-but-overlapping quantum ensembles (Holevo < log d)",
                "cannot model chi > I_acc gap: classical equality is generic, quantum inequality is strict",
                "ignores probe-basis admissibility; assumes a single diagonalizing frame",
            ],
        }, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
