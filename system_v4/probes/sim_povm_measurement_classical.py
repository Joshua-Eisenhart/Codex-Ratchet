#!/usr/bin/env python3
"""Classical baseline sim: povm_measurement_family lego.

Lane B classical baseline (numpy-only). NOT canonical.
Captures: classical POVM = stochastic measurement matrix M (rows =
outcomes, cols = states), M_ki >= 0, sum_k M_ki = 1. Measurement outcome
distribution q = M p.
Innately missing: noncommuting POVM elements {E_k} as PSD operators
summing to identity, Naimark dilation, Helstrom-optimal projectors
acting on eigenbasis of rho_0 - rho_1.
"""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "stochastic matrix arithmetic"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

def is_classical_povm(M, tol=1e-10):
    M = np.asarray(M, dtype=float)
    return np.all(M >= -tol) and np.allclose(M.sum(axis=0), 1.0, atol=tol)

def measure(M, p): return M @ np.asarray(p)

def run_positive_tests():
    M = np.array([[0.8, 0.1],[0.2, 0.9]])
    p = np.array([0.6, 0.4])
    q = measure(M, p)
    # trivial identity measurement
    I = np.eye(3)
    return {
        "valid_classical_povm": is_classical_povm(M),
        "outcome_normalized": abs(q.sum() - 1.0) < 1e-12,
        "outcome_nonneg": np.all(q >= -1e-12),
        "identity_is_povm": is_classical_povm(I),
    }

def run_negative_tests():
    bad1 = np.array([[1.2, 0.0],[-0.2, 1.0]])
    bad2 = np.array([[0.5, 0.5],[0.4, 0.4]])  # cols don't sum to 1
    return {
        "negative_entry_rejected": not is_classical_povm(bad1),
        "nonnormalized_rejected": not is_classical_povm(bad2),
    }

def run_boundary_tests():
    # binary projective classical: [[1,0],[0,1]] perfectly distinguishes pure distributions
    P = np.eye(2)
    p0 = np.array([1.0, 0.0]); p1 = np.array([0.0, 1.0])
    # equiprobable guess success = 1 when distinguishable
    success = 0.5*measure(P,p0)[0] + 0.5*measure(P,p1)[1]
    return {
        "orthogonal_pmfs_perfectly_distinguished": abs(success - 1.0) < 1e-12,
        "guess_bound_le_1": success <= 1.0 + 1e-12,
    }

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "povm_measurement_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": [
            "POVM elements are scalars/rows, not PSD operators on a Hilbert space",
            "no noncommuting measurement structure; cannot saturate Helstrom bound generically",
            "no Naimark dilation; measurement instrument state-update undefined",
        ],
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "povm_measurement_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
