#!/usr/bin/env python3
"""Classical baseline sim: lindbladian_evolution lego (classical dynamics).

Lane B classical baseline (numpy-only). NOT canonical.
Captures: classical master equation
  dp/dt = L p,  L_ij = W_ij (i!=j),  L_ii = -sum_{k!=i} W_ki
with W_ij >= 0 (transition rates). Generates stochastic semigroup
exp(L t) that preserves nonnegativity and normalization.
Innately missing: dissipator form -i[H,rho] + sum_k (L_k rho L_k^dag -
1/2 {L_k^dag L_k, rho}); cannot produce decoherence on off-diagonals,
cannot generate quantum Zeno behavior, cannot have a Hamiltonian commutator
piece.
"""
import json, os
import numpy as np
from scipy.linalg import expm  # scipy is numeric, fine as supportive

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "matrix exp/master eqn"},
    "scipy": {"tried": True, "used": True, "reason": "expm for semigroup"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive", "scipy": "supportive"}

def build_L(W):
    W = np.asarray(W, dtype=float)
    n = W.shape[0]
    L = W.copy()
    np.fill_diagonal(L, 0.0)
    for i in range(n):
        L[i,i] = -np.sum(W[:,i]) + W[i,i]  # subtract off-diagonal column sum
    # correct: diag = -sum_{k!=i} W_ki
    for i in range(n):
        L[i,i] = -(np.sum(W[:,i]) - W[i,i])
    return L

def evolve(L, p0, t):
    return expm(L * t) @ np.asarray(p0)

def run_positive_tests():
    W = np.array([[0.0, 0.5],[0.3, 0.0]])
    L = build_L(W)
    p0 = np.array([1.0, 0.0])
    pt = evolve(L, p0, 1.0)
    p_inf = evolve(L, p0, 1000.0)
    return {
        "column_sums_zero": np.allclose(L.sum(axis=0), 0.0, atol=1e-12),
        "norm_preserved": abs(pt.sum() - 1.0) < 1e-10,
        "nonneg_preserved": np.all(pt >= -1e-10),
        "steady_state_exists": np.all(p_inf >= -1e-10) and abs(p_inf.sum() - 1.0) < 1e-8,
    }

def run_negative_tests():
    # negative off-diagonal rate -> unphysical
    W = np.array([[0.0, -0.2],[0.3, 0.0]])
    L = build_L(W)
    p = evolve(L, np.array([1.0, 0.0]), 5.0)
    return {
        "negative_rate_breaks_positivity": np.any(p < -1e-6),
    }

def run_boundary_tests():
    # at t=0, identity
    W = np.array([[0.0, 0.2, 0.1],[0.3, 0.0, 0.4],[0.1, 0.2, 0.0]])
    L = build_L(W)
    p0 = np.array([0.5, 0.3, 0.2])
    return {
        "t_zero_identity": np.allclose(evolve(L, p0, 0.0), p0, atol=1e-12),
        "semigroup": np.allclose(evolve(L, p0, 0.6),
                                  evolve(L, evolve(L, p0, 0.2), 0.4), atol=1e-10),
    }

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "lindbladian_evolution_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": [
            "no Hamiltonian commutator -i[H,rho] piece; purely dissipative rates",
            "no decoherence on off-diagonals (none exist classically)",
            "no Kraus/GKSL structure; cannot represent quantum Zeno or dephasing",
        ],
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "lindbladian_evolution_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
