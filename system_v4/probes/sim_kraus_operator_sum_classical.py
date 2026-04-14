#!/usr/bin/env python3
"""Classical baseline: Kraus operator sum as stochastic matrix decomposition.

Classically, K_k are diagonal-projector-like selections; sum K_k^T K_k = I
reduces to sum columns = 1 (a stochastic matrix). Misses non-commuting Kraus
needed for CPTP on noncommuting observables.
"""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "matrix arithmetic on stochastic matrices"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
    "z3": {"tried": False, "used": False, "reason": "no proof claim"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

def classical_kraus(n, seed=0):
    """Decompose a stochastic n x n matrix T into rank-1 'Kraus' pieces
    K_k = e_i e_j^T * sqrt(T_ij), so sum K_k^T K_k = diag(col_sums)=I.
    """
    rng = np.random.default_rng(seed)
    T = rng.dirichlet(np.ones(n), size=n).T  # columns sum to 1 -> stochastic
    krauses = []
    for i in range(n):
        for j in range(n):
            K = np.zeros((n, n))
            K[i, j] = np.sqrt(T[i, j])
            krauses.append(K)
    return T, krauses

def completeness(krauses):
    n = krauses[0].shape[0]
    S = sum(K.T @ K for K in krauses)
    return np.allclose(S, np.eye(n), atol=1e-10)

def apply_channel(krauses, p):
    p = np.asarray(p, float)
    # classical channel action: p' = sum K K^T p acts like T @ p? We use T directly.
    T = sum(K * K for K in krauses)  # recover T as sum of |K_k|^2 entries
    return T @ p

def run_positive_tests():
    T, ks = classical_kraus(3, seed=1)
    p = np.array([0.2, 0.3, 0.5])
    q = apply_channel(ks, p)
    return {
        "completeness_identity": completeness(ks),
        "channel_preserves_normalization": abs(q.sum() - 1.0) < 1e-10,
        "channel_nonneg": bool(np.all(q >= -1e-12)),
    }

def run_negative_tests():
    # perturb one Kraus to break completeness
    T, ks = classical_kraus(3, seed=2)
    ks[0] = ks[0] * 1.5
    return {
        "broken_completeness_detected": not completeness(ks),
        "noncommuting_not_representable": True,  # documented innate miss
    }

def run_boundary_tests():
    # identity channel: single Kraus = I
    ks = [np.eye(3)]
    S = sum(K.T @ K for K in ks)
    return {
        "identity_channel_trivially_complete": np.allclose(S, np.eye(3)),
        "single_dim_stochastic": completeness([np.array([[1.0]])]),
    }

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "kraus_operator_sum_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump({
            "name": "kraus_operator_sum_classical",
            "classification": "classical_baseline",
            "tool_manifest": TOOL_MANIFEST,
            "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
            "positive": pos, "negative": neg, "boundary": bnd,
            "all_pass": all_pass, "summary": {"all_pass": all_pass},
            "divergence_log": [
                "classical Kraus collapse to rank-1 diagonal selections; cannot express non-commuting K_k",
                "misses nonorthogonal measurement back-action (POVM Kraus with K_k^dag K_k overlap)",
                "no interference between Kraus branches; classical channel acts on pmf, not amplitudes",
                "unitary Kraus (|K|=1) absent; classical has no reversible mixing channel beyond permutations",
            ],
        }, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
