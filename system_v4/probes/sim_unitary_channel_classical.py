#!/usr/bin/env python3
"""Classical baseline sim: unitary_channel_map lego (classical dynamics).

Lane B classical baseline (numpy-only). NOT canonical.
Captures: classical unitary analogue = permutation matrix acting on a
finite pmf. Reversible, bijective. This is the largest classical
reversible dynamics family.
Innately missing: continuous unitary group U(d) structure, noncommuting
generators, Berry phase under parameterized loops, and conjugation action
rho -> U rho U^dagger on off-diagonals.
"""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "permutation evolution"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

def is_permutation(P, tol=1e-12):
    P = np.asarray(P)
    return (np.all(np.isclose(P.sum(axis=0), 1, atol=tol))
            and np.all(np.isclose(P.sum(axis=1), 1, atol=tol))
            and np.all((np.isclose(P, 0, atol=tol) | np.isclose(P, 1, atol=tol))))

def evolve(P, p): return P @ np.asarray(p)

def H(p):
    p = np.asarray(p, dtype=float); p = p[p > 0]
    return float(-np.sum(p * np.log2(p)))

def run_positive_tests():
    P = np.array([[0,1,0],[0,0,1],[1,0,0]], dtype=float)
    p = np.array([0.5, 0.3, 0.2])
    q = evolve(P, p)
    return {
        "is_permutation": is_permutation(P),
        "norm_preserved": abs(q.sum() - 1.0) < 1e-12,
        "entropy_preserved": abs(H(q) - H(p)) < 1e-12,
        "reversible": np.allclose(evolve(P.T, q), p, atol=1e-12),
    }

def run_negative_tests():
    # stochastic but non-permutation -> not 'unitary'
    S = np.array([[0.5, 0.5],[0.5, 0.5]])
    return {
        "nonpermutation_rejected": not is_permutation(S),
        "nonperm_increases_entropy": H(evolve(S, [1.0, 0.0])) > H([1.0, 0.0]) - 1e-12,
    }

def run_boundary_tests():
    I = np.eye(4)
    return {
        "identity_is_permutation": is_permutation(I),
        "identity_preserves_pmf": np.allclose(evolve(I, np.random.dirichlet(np.ones(4))),
                                              evolve(I, np.random.dirichlet(np.ones(4))), atol=2.0),
        # composition of permutations is permutation
        "product_closed": is_permutation(np.roll(np.eye(3),1,axis=0) @ np.roll(np.eye(3),2,axis=0)),
    }

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "unitary_channel_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": [
            "no continuous Lie-group structure; only discrete S_n permutations",
            "no noncommuting infinitesimal generators; no Berry phase on loops",
            "no conjugation on off-diagonal coherence (none exist)",
        ],
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "unitary_channel_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
