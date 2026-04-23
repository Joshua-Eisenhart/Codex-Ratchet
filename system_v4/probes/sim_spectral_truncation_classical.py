#!/usr/bin/env python3
"""Classical baseline: spectral_truncation (Eckart-Young for symmetric)."""
import json, os, numpy as np
from _classical_baseline_common import TOOL_MANIFEST, TOOL_INTEGRATION_DEPTH
classification = "classical_baseline"

NAME = "spectral_truncation"

def truncate(A, k):
    w, V = np.linalg.eigh((A + A.T) / 2)
    idx = np.argsort(-np.abs(w))
    w2, V2 = w[idx], V[:, idx]
    w2[k:] = 0
    return V2 @ np.diag(w2) @ V2.T, w[idx][k:]  # tail

def run_positive_tests():
    r = {}
    rng = np.random.default_rng(0)
    U, _ = np.linalg.qr(rng.standard_normal((5, 5)))
    d = np.array([10.0, 5.0, 2.0, 0.5, 0.1])
    A = U @ np.diag(d) @ U.T
    Ak, tail = truncate(A, 3)
    # Eckart-Young: ||A - Ak||_F^2 = sum of discarded eig^2
    err_F = np.linalg.norm(A - Ak)
    expected = np.sqrt(np.sum(tail ** 2))
    r["eckart_young_frobenius"] = {"err_F": float(err_F), "expected": float(expected), "pass": abs(err_F - expected) < 1e-8}
    # spectral norm = largest discarded |eig|
    err_2 = np.linalg.norm(A - Ak, 2)
    r["spectral_norm"] = {"err_2": float(err_2), "expected": float(np.max(np.abs(tail))), "pass": abs(err_2 - np.max(np.abs(tail))) < 1e-8}
    # rank(Ak) = k
    r["rank_k"] = {"rank": int(np.linalg.matrix_rank(Ak, tol=1e-8)), "pass": int(np.linalg.matrix_rank(Ak, tol=1e-8)) == 3}
    return r

def run_negative_tests():
    r = {}
    rng = np.random.default_rng(1)
    U, _ = np.linalg.qr(rng.standard_normal((4, 4)))
    d = np.array([4.0, 3.0, 2.0, 1.0])
    A = U @ np.diag(d) @ U.T
    # truncating to wrong tail (smallest-kept) gives worse error than top-k
    w, V = np.linalg.eigh(A); idx = np.argsort(w)  # ascending
    V_bad = V[:, idx[:2]]
    A_bad = V_bad @ np.diag(w[idx[:2]]) @ V_bad.T
    A_good, _ = truncate(A, 2)
    r["wrong_truncation_worse"] = {"bad": float(np.linalg.norm(A - A_bad)), "good": float(np.linalg.norm(A - A_good)),
        "pass": np.linalg.norm(A - A_bad) > np.linalg.norm(A - A_good)}
    # k > n should not exceed full reconstruction error (0)
    A_full, _ = truncate(A, 10)
    r["k_exceeds_n_zero_err"] = {"err": float(np.linalg.norm(A - A_full)), "pass": np.linalg.norm(A - A_full) < 1e-10}
    return r

def run_boundary_tests():
    r = {}
    A = np.diag([2.0, 2.0, 2.0, 2.0])
    Ak, _ = truncate(A, 2)
    r["degenerate_trace_4"] = {"trace": float(np.trace(Ak)), "pass": abs(np.trace(Ak) - 4.0) < 1e-8}
    A0, _ = truncate(np.eye(3), 0)
    r["k0_zero_matrix"] = {"norm": float(np.linalg.norm(A0)), "pass": float(np.linalg.norm(A0)) < 1e-12}
    return r

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(v.get("pass", False) for v in list(pos.values()) + list(neg.values()) + list(bnd.values()))
    results = {"name": NAME, "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "all_pass": all_pass,
        "note": "classical captures: Eckart-Young optimality for symmetric matrices in Frobenius/spectral norm. Innately fails: optimality for operator-valued / CP-map truncation, non-Hermitian ordering."}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results"); os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_classical_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"{NAME} all_pass={all_pass} -> {out_path}")
