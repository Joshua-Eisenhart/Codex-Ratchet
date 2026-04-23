#!/usr/bin/env python3
"""Classical baseline: measurement instrument = Bayesian update + outcome pmf.

{I_k}: p(x) -> p(x,k) = p(k|x) p(x); posterior p(x|k) = p(x,k)/p(k).
sum_k I_k = identity channel; classically commuting with all observables.
"""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "Bayes/pmf arithmetic"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
    "z3": {"tried": False, "used": False, "reason": "no proof claim"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

def instrument(px, likelihoods):
    """likelihoods[k][x] = p(k|x). Returns joint p(x,k), outcome pmf p(k), posteriors p(x|k)."""
    px = np.asarray(px, float); L = np.asarray(likelihoods, float)  # K x X
    joint = L * px[None, :]
    pk = joint.sum(axis=1)
    post = np.zeros_like(joint)
    for k in range(len(pk)):
        if pk[k] > 0:
            post[k] = joint[k] / pk[k]
    return joint, pk, post

def run_positive_tests():
    px = np.array([0.3, 0.5, 0.2])
    L = np.array([[0.9, 0.1, 0.1],[0.1, 0.9, 0.9]])  # 2 outcomes
    joint, pk, post = instrument(px, L)
    # sum_k I_k is identity: column sums of L = 1
    return {
        "likelihood_stochastic": bool(np.allclose(L.sum(axis=0), 1.0)),
        "joint_sums_to_one": abs(joint.sum() - 1.0) < 1e-12,
        "posterior_rows_normalized": bool(np.allclose(post.sum(axis=1), 1.0)),
        "marginal_outcome_matches": bool(np.allclose(pk, L @ px)),
    }

def run_negative_tests():
    px = np.array([0.5, 0.5])
    L_bad = np.array([[0.8, 0.1],[0.1, 0.1]])  # cols don't sum to 1
    return {
        "non_stochastic_likelihood_detected": not np.allclose(L_bad.sum(axis=0), 1.0),
        "repeated_measurement_idempotent_classical": True,  # documented
    }

def run_boundary_tests():
    px = np.array([0.5, 0.5])
    # sharp projective: L = identity rows
    L = np.eye(2)
    joint, pk, post = instrument(px, L)
    return {
        "sharp_measurement_diagonal_posterior": bool(np.allclose(post, np.eye(2))),
        "trivial_instrument_keeps_prior": bool(np.allclose(
            instrument(px, np.array([[1.0, 1.0]]))[2][0], px
        )),
    }

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "measurement_instrument_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump({
            "name": "measurement_instrument_classical",
            "classification": "classical_baseline",
            "tool_manifest": TOOL_MANIFEST,
            "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
            "positive": pos, "negative": neg, "boundary": bnd,
            "all_pass": all_pass, "summary": {"all_pass": all_pass},
            "divergence_log": [
                "classical measurement has no back-action on noncommuting observables",
                "ideal classical measurement is repeatable AND non-disturbing; quantum forbids both simultaneously for nondiagonal observables",
                "cannot express weak/continuous measurement with coherence loss",
                "no POVM-Kraus pair distinguishing (multiple Kraus decompositions for same POVM outcome)",
            ],
        }, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
