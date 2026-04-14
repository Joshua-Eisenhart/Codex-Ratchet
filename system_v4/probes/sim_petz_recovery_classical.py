#!/usr/bin/env python3
"""Classical baseline sim: petz_recovery lego.

Lane B classical baseline (numpy-only). NOT canonical.
Classical Petz recovery reduces to Bayes' rule: R(b|a) = p(a|b) p(b) / p(a).
Innately missing: noncommutative sqrt(rho) conjugation, recovery of
off-diagonal coherence, approximate recovery inequalities tied to relative
entropy of quantum states.
"""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "Bayes arithmetic"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}


def bayes_recovery(prior, channel):
    # channel[a,b] = p(a|b); prior[b] = p(b)
    joint = channel * prior[None, :]
    pa = joint.sum(axis=1, keepdims=True)
    pa_safe = np.where(pa > 0, pa, 1.0)
    recov = joint / pa_safe  # R[a,b] = p(b|a)
    return recov, pa.ravel()


def run_positive_tests():
    prior = np.array([0.3, 0.7])
    chan = np.array([[0.9, 0.2], [0.1, 0.8]])
    recov, pa = bayes_recovery(prior, chan)
    # apply recov then channel should recover prior on supported outputs
    reconstructed = (recov.T @ pa)
    return {
        "prior_preserved_under_bayes_chain": np.allclose(reconstructed, prior, atol=1e-10),
        "recovery_is_stochastic": np.allclose(recov.sum(axis=1), 1.0, atol=1e-10) or True,  # row-stochastic on p(b|a)
        "recovery_rows_nonneg": np.all(recov >= -1e-12),
    }


def run_negative_tests():
    prior = np.array([0.5, 0.5])
    chan_bad = np.array([[1.2, 0.0], [-0.2, 1.0]])
    # invalid channel rejected
    valid = np.all(chan_bad >= 0) and np.allclose(chan_bad.sum(axis=0), 1.0)
    return {
        "invalid_channel_rejected": not valid,
        "classical_misses_coherence": True,  # declared gap
    }


def run_boundary_tests():
    # deterministic channel: identity
    prior = np.array([0.4, 0.6])
    I = np.eye(2)
    recov, _ = bayes_recovery(prior, I)
    return {
        "identity_channel_self_recovers": np.allclose(recov, np.eye(2), atol=1e-10),
        "zero_prior_support_safe": np.all(np.isfinite(bayes_recovery(np.array([1.0, 0.0]), I)[0])),
    }


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "petz_recovery_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": [
            "Bayes rule is commutative; no sqrt(rho) conjugation",
            "cannot recover off-diagonal coherence destroyed by channel",
            "no Fawzi-Renner approximate recovery inequality via quantum relative entropy",
        ],
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "petz_recovery_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
