#!/usr/bin/env python3
"""Classical baseline: covariance_operator. numpy-only."""
import json, os, numpy as np
classification = "classical_baseline"
divergence_log = "Classical baseline: covariance-operator behavior is modeled here by sample-covariance numerics, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "sample-covariance construction and eigenspectrum checks"},
    "sympy": {"tried": False, "used": False, "reason": "not needed for this numeric baseline"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "sympy": None,
}

NAME = "covariance_operator"

def cov(X):  # rows = samples
    Xc = X - X.mean(axis=0, keepdims=True)
    return (Xc.T @ Xc) / (X.shape[0] - 1)

def run_positive_tests():
    r = {}
    rng = np.random.default_rng(0)
    # isotropic
    X = rng.standard_normal((5000, 4))
    C = cov(X)
    r["isotropic_near_identity"] = {"max_off_diag": float(np.max(np.abs(C - np.eye(4)))), "pass": float(np.max(np.abs(C - np.eye(4)))) < 0.1}
    # symmetry
    r["symmetric"] = {"asym": float(np.max(np.abs(C - C.T))), "pass": np.allclose(C, C.T)}
    # PSD
    w = np.linalg.eigvalsh(C)
    r["psd"] = {"min_eig": float(w.min()), "pass": bool(w.min() > -1e-9)}
    # known covariance: diagonal scale
    A = np.diag([1.0, 4.0, 9.0])
    Y = rng.standard_normal((20000, 3)) @ A
    Cy = cov(Y)
    expected = A @ A.T
    r["diagonal_scaling_recovered"] = {"err": float(np.max(np.abs(Cy - expected))), "pass": float(np.max(np.abs(Cy - expected))) < 0.5}
    return r

def run_negative_tests():
    r = {}
    # non-centered data without centering yields wrong cov
    X = np.ones((100, 3)) * 5 + np.random.default_rng(1).standard_normal((100, 3))
    uncentered = (X.T @ X) / (X.shape[0] - 1)
    C = cov(X)
    r["uncentered_differs"] = {"diff": float(np.max(np.abs(uncentered - C))), "pass": float(np.max(np.abs(uncentered - C))) > 1.0}
    # single sample -> undefined (n-1 = 0) -> NaN/Inf result
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = cov(np.array([[1.0, 2.0]]))
    r["single_sample_rejected"] = {"has_nonfinite": bool(not np.all(np.isfinite(res))), "pass": bool(not np.all(np.isfinite(res)))}
    return r

def run_boundary_tests():
    r = {}
    # rank-deficient: two copies of same column -> singular cov
    rng = np.random.default_rng(2)
    x = rng.standard_normal(500)
    X = np.stack([x, x, rng.standard_normal(500)], axis=1)
    C = cov(X)
    w = np.linalg.eigvalsh(C)
    r["rank_deficient_has_zero_eig"] = {"min_eig": float(w.min()), "pass": bool(abs(w.min()) < 0.05)}
    # tiny n vs d (high-dim small-sample)
    Y = rng.standard_normal((3, 50))
    Cy = cov(Y)
    r["high_dim_small_n_low_rank"] = {"rank": int(np.linalg.matrix_rank(Cy, tol=1e-8)), "pass": int(np.linalg.matrix_rank(Cy, tol=1e-8)) <= 2}
    return r

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(v.get("pass", False) for v in list(pos.values()) + list(neg.values()) + list(bnd.values()))
    results = {
        "name": NAME, "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "all_pass": all_pass,
        "note": "classical captures: symmetry, PSD, known-covariance recovery. Innately fails: quantum covariances with complex off-diagonal coherences / operator ordering."
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_classical_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"{NAME} all_pass={all_pass} -> {out_path}")
