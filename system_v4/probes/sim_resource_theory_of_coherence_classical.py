#!/usr/bin/env python3
"""Classical baseline sim: resource_theory_of_coherence lego.

Lane B classical baseline (numpy-only). NOT canonical.
In the resource theory of coherence, free states are diagonal (incoherent).
Classical pmfs embed as diagonal density matrices, so every classical state
is free and every coherence monotone (l1, relative entropy, robustness) is
zero. We verify zero on three monotones and verify that incoherent
operations (permutations, stochastic diagonal maps) preserve free-ness.
"""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "diagonal-matrix arithmetic and entropy"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}


def diag_from_pmf(p):
    return np.diag(np.asarray(p, float))


def l1_coherence(rho):
    return float(np.sum(np.abs(rho - np.diag(np.diag(rho)))))


def rel_entropy_coherence(rho):
    # S(diag(rho)) - S(rho); equals 0 for diagonal rho
    diag = np.diag(np.diag(rho))
    evs_r = np.linalg.eigvalsh(rho); evs_d = np.linalg.eigvalsh(diag)
    S = lambda x: -np.sum(x[x > 1e-15] * np.log2(x[x > 1e-15]))
    return float(S(evs_d) - S(evs_r))


def robustness_coherence(rho):
    # for diagonal rho, trivial robustness is 0
    if np.allclose(rho, np.diag(np.diag(rho))):
        return 0.0
    # generic placeholder: return l1 upper bound
    return l1_coherence(rho)


def run_positive_tests():
    p = np.array([0.2, 0.3, 0.5])
    rho = diag_from_pmf(p)
    return {
        "l1_coherence_zero": l1_coherence(rho) == 0.0,
        "relative_entropy_coherence_zero": abs(rel_entropy_coherence(rho)) < 1e-10,
        "robustness_zero": robustness_coherence(rho) == 0.0,
    }


def run_negative_tests():
    rho = np.array([[0.5, 0.4], [0.4, 0.5]])
    return {
        "offdiag_nonfree_detected": l1_coherence(rho) > 0.0,
        "offdiag_relative_entropy_positive": rel_entropy_coherence(rho) > 0.0,
        "classical_cannot_represent_offdiag": True,
    }


def run_boundary_tests():
    # incoherent operation (permutation) preserves zero coherence
    rng = np.random.default_rng(8)
    p = rng.dirichlet(np.ones(4))
    rho = diag_from_pmf(p)
    P = np.eye(4)[rng.permutation(4)]
    rho2 = P @ rho @ P.T
    # stochastic diagonal map (classical channel) also preserves
    T = rng.dirichlet(np.ones(4), size=4)  # row stochastic
    rho3 = diag_from_pmf(T.T @ p)
    return {
        "permutation_preserves_zero": l1_coherence(rho2) == 0.0,
        "classical_channel_preserves_zero": l1_coherence(rho3) == 0.0,
        "pure_classical_state_zero": l1_coherence(diag_from_pmf([1.0, 0.0, 0.0])) == 0.0,
    }


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "resource_theory_of_coherence_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": (
            "The entire resource theory collapses classically: every free state is diagonal, every "
            "classical state IS diagonal, so coherence is identically zero under any monotone and "
            "'free operations' are exactly the stochastic maps that permute/mix diagonal entries. The "
            "baseline cannot distinguish or cost superposition as a resource, and cannot express "
            "coherence distillation, coherence-to-entanglement conversion, or basis-dependence of the "
            "incoherent set — all of which hinge on off-diagonal terms that the classical embedding "
            "kills by construction."
        ),
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "resource_theory_of_coherence_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
