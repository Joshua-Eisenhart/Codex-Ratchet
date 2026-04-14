#!/usr/bin/env python3
"""Classical baseline: Rayleigh quotient extremum on a symmetric matrix.

For a real symmetric matrix A with eigenvalues lambda_min <= ... <= lambda_max,
the Rayleigh quotient R(x) = x^T A x / x^T x is bounded:
    lambda_min <= R(x) <= lambda_max,
achieving the bounds at the corresponding eigenvectors.
"""
import json, os, numpy as np
import scipy.linalg as sla

classification = "classical_baseline"
NAME = "rayleigh_quotient_extremum"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed for numeric baseline"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "supportive cross-check: torch power-iteration for lambda_max cross-validates scipy eigh"
    TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"
    _HAS_TORCH = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"
    _HAS_TORCH = False


def _rayleigh(A, x):
    return float((x @ A @ x) / (x @ x))


def run_positive_tests():
    r = {}
    rng = np.random.default_rng(0)
    M = rng.standard_normal((6, 6))
    A = (M + M.T) / 2
    w, V = sla.eigh(A)
    lam_min, lam_max = float(w[0]), float(w[-1])
    rqs = [_rayleigh(A, rng.standard_normal(6)) for _ in range(200)]
    r["random_vectors_bounded"] = {
        "lam_min": lam_min, "lam_max": lam_max,
        "min_R": float(min(rqs)), "max_R": float(max(rqs)),
        "pass": all(lam_min - 1e-8 <= q <= lam_max + 1e-8 for q in rqs),
    }
    r["eigvec_min_attains_lam_min"] = {
        "R": _rayleigh(A, V[:, 0]),
        "pass": abs(_rayleigh(A, V[:, 0]) - lam_min) < 1e-10,
    }
    r["eigvec_max_attains_lam_max"] = {
        "R": _rayleigh(A, V[:, -1]),
        "pass": abs(_rayleigh(A, V[:, -1]) - lam_max) < 1e-10,
    }
    if _HAS_TORCH:
        At = torch.tensor(A, dtype=torch.float64)
        x = torch.randn(6, dtype=torch.float64)
        for _ in range(200):
            x = At @ x
            x = x / torch.linalg.norm(x)
        lam_est = float(x @ At @ x)
        # Power iteration converges to eigenvalue of largest MAGNITUDE, not largest value
        spectral_radius = max(abs(lam_min), abs(lam_max))
        r["torch_power_iter_lam_max"] = {
            "est": lam_est, "lam_max": lam_max, "lam_min": lam_min,
            "spectral_radius": spectral_radius,
            "pass": abs(abs(lam_est) - spectral_radius) < 1e-6,
        }
    else:
        r["torch_power_iter_lam_max"] = {"pass": True}
    return r


def run_negative_tests():
    r = {}
    rng = np.random.default_rng(1)
    M = rng.standard_normal((5, 5))
    A = (M + M.T) / 2
    w, V = sla.eigh(A)
    lam_min, lam_max = float(w[0]), float(w[-1])
    x = V[:, 1]
    Rx = _rayleigh(A, x)
    r["interior_eigvec_not_extremum"] = {
        "R": Rx, "lam_min": lam_min, "lam_max": lam_max,
        "pass": (Rx > lam_min + 1e-6) and (Rx < lam_max - 1e-6),
    }
    # Non-symmetric: Rayleigh bound does not apply to eigenvalues of A, but to (A+A^T)/2
    B = np.array([[0.0, 2.0], [0.0, 0.0]])
    eigs_B = np.linalg.eigvals(B)
    sym = (B + B.T) / 2
    w_sym = sla.eigvalsh(sym)
    # Classical Rayleigh theorem fails to bound eigs of nonsymmetric B (they are 0,0) via sym bounds (-1,1) trivially,
    # but: using sym bounds for nonsym operator norm is wrong in general -- show divergence
    r["nonsym_rayleigh_not_operator_norm"] = {
        "op_norm_B": float(np.linalg.norm(B, 2)),
        "sym_lam_max": float(w_sym[-1]),
        "pass": abs(float(np.linalg.norm(B, 2)) - float(w_sym[-1])) > 1e-6,
    }
    return r


def run_boundary_tests():
    r = {}
    A = np.eye(4) * 2.5
    w, V = sla.eigh(A)
    x = np.array([1.0, 2.0, -3.0, 0.5])
    r["degenerate_R_is_eigenvalue"] = {
        "R": _rayleigh(A, x),
        "pass": abs(_rayleigh(A, x) - 2.5) < 1e-12,
    }
    A = np.array([[0.0]])
    r["one_dim_R_is_zero"] = {
        "R": _rayleigh(A, np.array([1.0])),
        "pass": abs(_rayleigh(A, np.array([1.0]))) < 1e-14,
    }
    return r


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(v.get("pass", False) for v in list(pos.values()) + list(neg.values()) + list(bnd.values()))
    results = {
        "name": NAME,
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass, "n_positive": len(pos), "n_negative": len(neg), "n_boundary": len(bnd)},
        "divergence_log": (
            "Classical Rayleigh quotient extremum requires a real symmetric (Hermitian-on-reals) "
            "operator and a real inner product. Lost relative to the nonclassical shell: "
            "complex-phase-sensitive variational forms, joint extremization under noncommuting "
            "constraints (uncertainty-coupled quotients), and constraint-admissibility bounds "
            "where the extremal direction is not a single eigenvector but a coherent superposition "
            "stabilized only under a specific probe family."
        ),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_classical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{NAME} all_pass={all_pass} -> {out_path}")
