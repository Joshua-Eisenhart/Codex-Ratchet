#!/usr/bin/env python3
"""Classical baseline sim: schmidt_decomposition lego.

Lane B classical baseline (numpy-only). NOT canonical.
Captures: SVD of a real/complex matrix amplitude form. Schmidt rank =
number of nonzero singular values. For PRODUCT joint pmfs sqrt-amplitude,
rank=1. For a 'correlated' amplitude matrix, rank>1.
Innately missing: meaning of Schmidt rank as entanglement vs. classical
correlation — classically, rank>1 just signals non-factorizable pmf, not
a nonlocal resource.
"""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "SVD"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

def schmidt(A, tol=1e-10):
    U, s, Vh = np.linalg.svd(A, full_matrices=False)
    rank = int(np.sum(s > tol))
    return U, s, Vh, rank

def run_positive_tests():
    # product amplitude -> rank 1
    a = np.array([0.6, 0.8]); b = np.array([1.0, 0.0])
    A = np.outer(a, b)
    _, _, _, r = schmidt(A)
    # bell-like amplitude
    B = np.array([[1.0, 0.0],[0.0, 1.0]])/np.sqrt(2)
    _, sB, _, rB = schmidt(B)
    return {
        "product_rank_1": r == 1,
        "bell_rank_2": rB == 2,
        "bell_schmidt_values_equal": abs(sB[0] - sB[1]) < 1e-10,
    }

def run_negative_tests():
    # zero matrix
    Z = np.zeros((3,3))
    _, _, _, r = schmidt(Z)
    return {"zero_matrix_rank_zero": r == 0}

def run_boundary_tests():
    # reconstruction: A = U diag(s) Vh
    A = np.random.randn(4,3)
    U, s, Vh, _ = schmidt(A, tol=1e-14)
    recon = U @ np.diag(s) @ Vh
    # singular values non-increasing
    nonincreasing = all(s[i] >= s[i+1] - 1e-12 for i in range(len(s)-1))
    return {
        "reconstruction_exact": np.allclose(recon, A, atol=1e-10),
        "singular_values_nonincreasing": nonincreasing,
    }

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "schmidt_decomposition_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": [
            "Schmidt rank purely algebraic; no entanglement-as-resource distinction",
            "cannot distinguish locally-prepared correlation from nonlocal entanglement",
            "no relation to reduced-state entropy under partial trace (requires quantum structure)",
        ],
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "schmidt_decomposition_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
