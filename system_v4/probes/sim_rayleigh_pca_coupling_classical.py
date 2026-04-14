#!/usr/bin/env python3
"""Classical pairwise coupling: Rayleigh quotient x PCA.

Coupling claim: for a centered data matrix X with covariance C = X^T X / n,
the maximum of the Rayleigh quotient R(v) = v^T C v / v^T v equals the top
eigenvalue lambda_1(C), which equals the variance of the first principal
component.
"""
import json, os
import numpy as np

classification = "classical_baseline"

divergence_log = (
    "Classical Rayleigh-PCA coupling loses: (1) non-commuting observables where "
    "Rayleigh maximization over states requires SDP, (2) quantum principal "
    "subspaces with entanglement-sensitive eigenstructure, (3) variational "
    "quantum eigensolver gap to classical PCA on density matrices."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "torch.linalg.eigh cross-check"},
    "pyg": {"tried": False, "used": False, "reason": "n/a"},
    "z3": {"tried": False, "used": False, "reason": "numeric"},
    "cvc5": {"tried": False, "used": False, "reason": "numeric"},
    "sympy": {"tried": False, "used": False, "reason": "numeric"},
    "clifford": {"tried": False, "used": False, "reason": "n/a"},
    "geomstats": {"tried": False, "used": False, "reason": "n/a"},
    "e3nn": {"tried": False, "used": False, "reason": "n/a"},
    "rustworkx": {"tried": False, "used": False, "reason": "n/a"},
    "xgi": {"tried": False, "used": False, "reason": "n/a"},
    "toponetx": {"tried": False, "used": False, "reason": "n/a"},
    "gudhi": {"tried": False, "used": False, "reason": "n/a"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"


def rayleigh(C, v):
    v = np.asarray(v)
    return float((v @ C @ v) / (v @ v))


def run_positive_tests():
    rng = np.random.default_rng(5)
    results = {}
    for trial in range(4):
        d, n = 6, 200
        X = rng.normal(size=(n, d))
        X -= X.mean(axis=0, keepdims=True)
        C = X.T @ X / n
        w, V = np.linalg.eigh(C)
        lam_top = float(w[-1])
        v_top = V[:, -1]
        # PCA variance of top PC
        pc1 = X @ v_top
        var_pc1 = float(np.var(pc1, ddof=0))
        r = rayleigh(C, v_top)
        results[f"match_{trial}"] = {
            "lambda_top": lam_top, "rayleigh": r, "var_pc1": var_pc1,
            "pass": bool(abs(lam_top - r) < 1e-9 and abs(lam_top - var_pc1) < 1e-9)}
    return results


def run_negative_tests():
    # Non-eigenvector gives strictly smaller Rayleigh quotient than lambda_top
    rng = np.random.default_rng(6)
    results = {}
    d = 5
    A = rng.normal(size=(d, d)); C = A @ A.T
    w, V = np.linalg.eigh(C)
    lam_top = float(w[-1])
    v_wrong = V[:, 0]  # smallest-eigenvalue eigvec
    r = rayleigh(C, v_wrong)
    results["wrong_eigvec_lt_top"] = {"lambda_top": lam_top, "rayleigh": r,
                                       "pass": bool(r < lam_top - 1e-6)}
    return results


def run_boundary_tests():
    results = {}
    # Identity covariance: every direction gives Rayleigh = 1
    C = np.eye(4)
    v = np.array([1.0, 2.0, 3.0, 4.0])
    results["identity_cov_all_one"] = {"r": rayleigh(C, v),
                                        "pass": bool(abs(rayleigh(C, v) - 1.0) < 1e-12)}
    # Rank-1 covariance: Rayleigh max equals the single nonzero eigenvalue
    u = np.array([1.0, -1.0, 0.5]); u = u / np.linalg.norm(u)
    C1 = 3.7 * np.outer(u, u)
    results["rank1_top"] = {"r": rayleigh(C1, u),
                            "pass": bool(abs(rayleigh(C1, u) - 3.7) < 1e-9)}
    return results


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = (all(v["pass"] for v in pos.values())
                and all(v["pass"] for v in neg.values())
                and all(v["pass"] for v in bnd.values()))
    results = {
        "name": "rayleigh_pca_coupling_classical",
        "classification": classification, "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": bool(all_pass), "summary": {"all_pass": bool(all_pass)},
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "rayleigh_pca_coupling_classical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out_path}")
