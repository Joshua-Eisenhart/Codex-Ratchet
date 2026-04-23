#!/usr/bin/env python3
"""Classical baseline: correlation_tensor_principal_directions (HOSVD / mode-n SVD)."""
import json, os, numpy as np
classification = "classical_baseline"
divergence_log = "Classical baseline: correlation-tensor principal directions are modeled here by HOSVD numerics, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "tensor unfoldings and SVD-based principal-direction numerics"},
    "sympy": {"tried": False, "used": False, "reason": "not needed for this numeric baseline"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "sympy": None,
}

NAME = "correlation_tensor_principal_directions"

def unfold(T, mode):
    return np.moveaxis(T, mode, 0).reshape(T.shape[mode], -1)

def hosvd_factors(T):
    return [np.linalg.svd(unfold(T, m), full_matrices=False)[0] for m in range(T.ndim)]

def run_positive_tests():
    r = {}
    rng = np.random.default_rng(0)
    T = rng.standard_normal((4, 5, 3))
    Us = hosvd_factors(T)
    # Each factor is orthonormal on its columns
    for i, U in enumerate(Us):
        ok = np.allclose(U.T @ U, np.eye(U.shape[1]))
        r[f"mode_{i}_orthonormal"] = {"err": float(np.max(np.abs(U.T @ U - np.eye(U.shape[1])))), "pass": ok}
    # Mode-1 factor matches eigenvectors of unfolding @ unfolding.T
    M0 = unfold(T, 0)
    w, V = np.linalg.eigh(M0 @ M0.T)
    # top singular vectors (abs of eigenvectors for non-degenerate)
    idx = np.argsort(-w)
    # match up to sign
    U0 = Us[0]
    V_sorted = V[:, idx[:U0.shape[1]]]
    inner = np.abs(np.diag(U0.T @ V_sorted))
    r["mode_0_matches_eigh"] = {"min_inner": float(inner.min()), "pass": inner.min() > 0.99}
    # Rank-(r1,r2,r3) recovery: construct known Tucker tensor
    core = rng.standard_normal((2, 2, 2))
    A = np.linalg.qr(rng.standard_normal((4, 2)))[0]
    B = np.linalg.qr(rng.standard_normal((5, 2)))[0]
    C = np.linalg.qr(rng.standard_normal((3, 2)))[0]
    T2 = np.einsum('ijk,ai,bj,ck->abc', core, A, B, C)
    Us2 = hosvd_factors(T2)
    # First 2 singular vectors of mode-0 unfolding should span colspace of A
    proj = Us2[0][:, :2] @ Us2[0][:, :2].T
    residual = proj @ A - A
    r["tucker_mode_recovered"] = {"residual": float(np.linalg.norm(residual)), "pass": np.linalg.norm(residual) < 1e-8}
    return r

def run_negative_tests():
    r = {}
    rng = np.random.default_rng(1)
    T = rng.standard_normal((3, 3, 3))
    Us = hosvd_factors(T)
    # Random matrices are NOT orthonormal
    R = rng.standard_normal((3, 3))
    r["random_not_orthonormal"] = {"err": float(np.max(np.abs(R.T @ R - np.eye(3)))), "pass": float(np.max(np.abs(R.T @ R - np.eye(3)))) > 0.1}
    # Mode-0 factors != Mode-1 factors (different unfoldings)
    r["factors_differ_across_modes"] = {"diff": float(np.linalg.norm(Us[0] - Us[1])), "pass": float(np.linalg.norm(Us[0] - Us[1])) > 0.1}
    return r

def run_boundary_tests():
    r = {}
    # Zero tensor -> factors are identity-ish (but singular)
    T = np.zeros((3, 3, 3))
    Us = hosvd_factors(T)
    r["zero_tensor_factor_shape"] = {"shape": list(Us[0].shape), "pass": Us[0].shape[0] == 3}
    # Rank-1 tensor: first mode-0 singular vector captures it
    a = np.array([1.0, 2.0, 3.0]); b = np.array([1.0, 0.0]); c = np.array([1.0, 1.0, 1.0, 1.0])
    T = np.einsum('i,j,k->ijk', a, b, c)
    Us = hosvd_factors(T)
    u0 = Us[0][:, 0]
    cos = abs(u0 @ (a / np.linalg.norm(a)))
    r["rank1_first_factor_aligned"] = {"cos": float(cos), "pass": cos > 0.999}
    return r

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(v.get("pass", False) for v in list(pos.values()) + list(neg.values()) + list(bnd.values()))
    results = {"name": NAME, "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "all_pass": all_pass,
        "note": "classical captures: HOSVD per-mode orthonormal factors, Tucker-rank recovery. Innately fails: no tensor Eckart-Young (truncated HOSVD is only quasi-optimal); ill-posed best rank-r tensor approx in general."}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results"); os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_classical_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"{NAME} all_pass={all_pass} -> {out_path}")
