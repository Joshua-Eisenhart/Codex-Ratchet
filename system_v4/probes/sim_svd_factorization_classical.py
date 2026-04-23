#!/usr/bin/env python3
"""Classical baseline: svd_factorization."""
import json, os, numpy as np
from _classical_baseline_common import TOOL_MANIFEST, TOOL_INTEGRATION_DEPTH
classification = "classical_baseline"

NAME = "svd_factorization"

def run_positive_tests():
    r = {}
    # closed form: diag(3,2) -> singvals [3,2]
    A = np.diag([3.0, 2.0])
    U, s, Vt = np.linalg.svd(A)
    r["diag_singvals"] = {"s": s.tolist(), "pass": np.allclose(sorted(s, reverse=True), [3.0, 2.0])}
    # reconstruction
    rng = np.random.default_rng(0)
    M = rng.standard_normal((5, 3))
    U, s, Vt = np.linalg.svd(M, full_matrices=False)
    recon = U @ np.diag(s) @ Vt
    r["reconstruction"] = {"err": float(np.max(np.abs(M - recon))), "pass": np.allclose(M, recon)}
    # U, V orthonormal
    r["U_orthonormal"] = {"err": float(np.max(np.abs(U.T @ U - np.eye(3)))), "pass": np.allclose(U.T @ U, np.eye(3))}
    r["V_orthonormal"] = {"err": float(np.max(np.abs(Vt @ Vt.T - np.eye(3)))), "pass": np.allclose(Vt @ Vt.T, np.eye(3))}
    # singvals nonneg descending
    r["singvals_descending"] = {"s": s.tolist(), "pass": bool(np.all(np.diff(s) <= 1e-12)) and bool(s.min() >= -1e-12)}
    # svd^2 eigenvalues of M^T M
    w = np.linalg.eigvalsh(M.T @ M)
    r["s2_matches_MTM_eigs"] = {"err": float(np.max(np.abs(np.sort(s ** 2) - np.sort(w)))), "pass": np.allclose(np.sort(s ** 2), np.sort(w))}
    return r

def run_negative_tests():
    r = {}
    # naive "svd" using eig of M^T M loses sign info; test pure svd does not
    rng = np.random.default_rng(1)
    M = rng.standard_normal((4, 4))
    _, s, _ = np.linalg.svd(M)
    w = np.linalg.eigvals(M)  # eigenvalues of square nonsym M != singvals
    r["eigs_ne_singvals"] = {"pass": not np.allclose(np.sort(np.abs(w)), np.sort(s))}
    # random pseudo-factorization (non-orthogonal) gives larger recon err
    U = rng.standard_normal((4, 4)); s = rng.standard_normal(4); Vt = rng.standard_normal((4, 4))
    recon_bad = U @ np.diag(s) @ Vt
    r["random_factorization_wrong"] = {"err": float(np.linalg.norm(M - recon_bad)), "pass": float(np.linalg.norm(M - recon_bad)) > 0.1}
    return r

def run_boundary_tests():
    r = {}
    # zero matrix
    U, s, Vt = np.linalg.svd(np.zeros((3, 4)))
    r["zero_matrix"] = {"s": s.tolist(), "pass": np.allclose(s, 0)}
    # 1x1
    U, s, Vt = np.linalg.svd(np.array([[-5.0]]))
    r["1x1_abs"] = {"s": s.tolist(), "pass": np.allclose(s, [5.0])}
    # tall: m>>n
    rng = np.random.default_rng(2)
    M = rng.standard_normal((50, 3))
    U, s, Vt = np.linalg.svd(M, full_matrices=False)
    r["tall_shape"] = {"U_shape": list(U.shape), "pass": U.shape == (50, 3)}
    return r

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(v.get("pass", False) for v in list(pos.values()) + list(neg.values()) + list(bnd.values()))
    results = {"name": NAME, "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "all_pass": all_pass,
        "note": "classical captures: real SVD existence, orthonormality, Eckart-Young singular value ordering. Innately fails: SVD of operator-tensors with gauge, complex phases on degenerate singvals."}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results"); os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_classical_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"{NAME} all_pass={all_pass} -> {out_path}")
