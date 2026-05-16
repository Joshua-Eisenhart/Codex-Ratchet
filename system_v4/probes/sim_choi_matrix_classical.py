#!/usr/bin/env python3
"""Classical baseline: Choi representation of a stochastic channel.

For classical channel T (X x X stochastic), 'Choi' is the block-diagonal
matrix with entries J_{ij,kl} = T[i,k] * delta_{j,l} delta_{i,k}? We use
the simpler canonical encoding: J_T = sum_{i,k} T[i,k] |i><k| tensor |i><k|
which is diagonal in the product basis. CP <=> entrywise nonneg; TP <=>
partial trace over output = I.
"""
import json, os
import numpy as np

from receipt_boundary import apply_default_receipt_boundary

classification = "classical_baseline"
divergence_log = (
    "Classical Choi is block-diagonal; misses off-diagonal coherences that "
    "witness non-CP-divisible or entanglement-breaking distinctions. Choi "
    "rank=1 (unitary) is unreachable classically except for permutations. "
    "No Jamiolkowski isomorphism subtlety: state-channel duality is trivial "
    "on diagonals. Classical Choi cannot detect PPT/NPT entanglement and is "
    "always separable."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "block-diagonal Choi on stochastic matrix"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
    "z3": {"tried": False, "used": False, "reason": "no proof claim"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

def choi_classical(T):
    """Diagonal Choi: J = diag(flatten(T)) in |out,in> basis, size d^2 x d^2."""
    T = np.asarray(T, float); d = T.shape[0]
    J = np.zeros((d*d, d*d))
    for i in range(d):
        for k in range(d):
            idx = i * d + k
            J[idx, idx] = T[i, k]
    return J

def partial_trace_out(J, d):
    """Trace over output index i (first): should give identity on input if TP."""
    M = np.zeros((d, d))
    for k in range(d):
        for l in range(d):
            # sum_i J[(i,k),(i,l)]
            s = 0.0
            for i in range(d):
                s += J[i*d + k, i*d + l]
            M[k, l] = s
    return M

def run_positive_tests():
    rng = np.random.default_rng(0)
    T = rng.dirichlet(np.ones(3), size=3).T  # columns sum to 1
    J = choi_classical(T)
    eigs = np.linalg.eigvalsh((J + J.T)/2)
    pt = partial_trace_out(J, 3)
    return {
        "choi_psd_cp": bool(np.all(eigs >= -1e-10)),
        "partial_trace_identity_tp": bool(np.allclose(pt, np.eye(3))),
        "block_diagonal_classical": bool(np.allclose(J - np.diag(np.diag(J)), 0)),
    }

def run_negative_tests():
    # non-CP: negative entries in T -> negative eig in Choi
    T = np.array([[0.9, -0.1, 0.2],[0.1, 0.7, 0.4],[0.0, 0.4, 0.4]])
    J = choi_classical(T)
    eigs = np.linalg.eigvalsh((J + J.T)/2)
    # non-TP
    T2 = np.array([[0.5, 0.2],[0.4, 0.5]])
    pt2 = partial_trace_out(choi_classical(T2), 2)
    return {
        "non_cp_detected_neg_eig": bool(np.any(eigs < -1e-10)),
        "non_tp_detected": not np.allclose(pt2, np.eye(2)),
    }

def run_boundary_tests():
    # identity channel
    T = np.eye(3)
    J = choi_classical(T)
    return {
        "identity_channel_cptp": bool(np.all(np.linalg.eigvalsh((J+J.T)/2) >= -1e-10)
                                      and np.allclose(partial_trace_out(J, 3), np.eye(3))),
        "choi_rank_equals_nonzero_T_entries": int(np.sum(np.diag(J) > 1e-12)) == int(np.sum(T > 1e-12)),
    }

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    name = "sim_choi_matrix_classical"
    results = {
        "name": name,
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass, "summary": {"all_pass": all_pass},
        "divergence_log": divergence_log,
        "promotion_allowed": False,
        "claim_ceiling": (
            "finite classical Choi-matrix baseline receipt only; "
            "no claims beyond a diagonal stochastic-map control"
        ),
        "out_of_scope": [
            "operator-coupling admission",
            "geometric manifold promotion",
            "cycle-mechanics admission",
            "state-space promotion",
            "cross-layer admission",
        ],
    }
    results = apply_default_receipt_boundary(
        results,
        source_name=name,
        target=(
            "Use as bounded classical Choi-matrix baseline evidence before "
            "channel/tool-lego comparison."
        ),
    )
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       f"{name}_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
