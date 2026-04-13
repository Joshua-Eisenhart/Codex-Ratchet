#!/usr/bin/env python3
"""Classical baseline: spectral_decomposition of symmetric matrices."""
import json, os, numpy as np
from _classical_baseline_common import TOOL_MANIFEST, TOOL_INTEGRATION_DEPTH
classification = "classical_baseline"

NAME = "spectral_decomposition"

def run_positive_tests():
    r = {}
    A = np.array([[2.0, 1.0], [1.0, 2.0]])
    w, V = np.linalg.eigh(A)
    # closed form: eigs 1, 3
    r["closed_form_2x2_eigs"] = {"eigs": w.tolist(), "pass": np.allclose(sorted(w), [1.0, 3.0])}
    # reconstruction A = V diag(w) V^T
    recon = V @ np.diag(w) @ V.T
    r["reconstruction"] = {"err": float(np.max(np.abs(A - recon))), "pass": np.allclose(A, recon)}
    # orthonormal eigenvectors
    r["orthonormal_V"] = {"err": float(np.max(np.abs(V.T @ V - np.eye(2)))), "pass": np.allclose(V.T @ V, np.eye(2))}
    # random symmetric
    rng = np.random.default_rng(0)
    M = rng.standard_normal((6, 6)); M = (M + M.T) / 2
    w2, V2 = np.linalg.eigh(M)
    r["random_sym_recon"] = {"err": float(np.max(np.abs(M - V2 @ np.diag(w2) @ V2.T))), "pass": np.allclose(M, V2 @ np.diag(w2) @ V2.T)}
    return r

def run_negative_tests():
    r = {}
    # eigh on non-symmetric silently symmetrizes; compare eig vs eigh gives mismatch
    A = np.array([[0.0, 1.0], [-1.0, 0.0]])
    w_eig, _ = np.linalg.eig(A)
    try:
        w_eigh, _ = np.linalg.eigh(A)
        # eigh returns real eigenvalues from symmetrized part (=zero matrix) -> [0,0]
        diff = float(np.max(np.abs(sorted(w_eig.real) - np.sort(w_eigh))))
        r["nonsym_eigh_wrong"] = {"diff": diff, "pass": diff > 0.5}
    except Exception:
        r["nonsym_eigh_wrong"] = {"pass": True}
    # non-square
    try:
        np.linalg.eigh(np.ones((3, 4)))
        r["nonsquare_rejected"] = {"pass": False}
    except Exception:
        r["nonsquare_rejected"] = {"pass": True}
    return r

def run_boundary_tests():
    r = {}
    # degenerate eigenvalues
    A = np.eye(4) * 2.5
    w, V = np.linalg.eigh(A)
    r["degenerate_all_equal"] = {"eigs": w.tolist(), "pass": np.allclose(w, 2.5)}
    # near-zero eigenvalue
    rng = np.random.default_rng(1)
    U, _ = np.linalg.qr(rng.standard_normal((5, 5)))
    d = np.array([1e-12, 0.1, 1.0, 2.0, 3.0])
    A = U @ np.diag(d) @ U.T
    w, _ = np.linalg.eigh(A)
    r["near_zero_eig_recovered"] = {"min_eig": float(w.min()), "pass": abs(w.min()) < 1e-8}
    return r

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(v.get("pass", False) for v in list(pos.values()) + list(neg.values()) + list(bnd.values()))
    results = {
        "name": NAME, "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "all_pass": all_pass,
        "note": "classical captures: eigh on real sym matrices, reconstruction, orthonormality. Innately fails: non-normal operators, complex Jordan blocks, non-Hermitian effective Hamiltonians."
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results"); os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_classical_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"{NAME} all_pass={all_pass} -> {out_path}")
