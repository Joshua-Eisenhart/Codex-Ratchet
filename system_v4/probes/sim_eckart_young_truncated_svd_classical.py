#!/usr/bin/env python3
"""Classical baseline: low-rank approximation via truncated SVD -- Eckart-Young bound.

For any matrix A with singular values sigma_1 >= sigma_2 >= ... , the best
rank-k Frobenius approximation A_k satisfies
    ||A - A_k||_F^2 = sum_{i>k} sigma_i^2
and the best spectral-norm approximation satisfies ||A - A_k||_2 = sigma_{k+1}.
"""
import json, os, numpy as np

classification = "classical_baseline"
NAME = "eckart_young_truncated_svd"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed for numeric SVD baseline"},
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
    TOOL_MANIFEST["pytorch"]["reason"] = "supportive cross-check: torch.linalg.svd re-run to confirm singular values match numpy"
    TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"
    _HAS_TORCH = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed; baseline uses numpy only"
    _HAS_TORCH = False


def _truncate(U, s, Vt, k):
    return U[:, :k] @ np.diag(s[:k]) @ Vt[:k, :]


def run_positive_tests():
    r = {}
    rng = np.random.default_rng(0)
    A = rng.standard_normal((8, 6))
    U, s, Vt = np.linalg.svd(A, full_matrices=False)
    for k in [1, 2, 3, 4, 5]:
        A_k = _truncate(U, s, Vt, k)
        fro_err2 = float(np.sum((A - A_k) ** 2))
        tail2 = float(np.sum(s[k:] ** 2))
        spec_err = float(np.linalg.norm(A - A_k, 2))
        sigma_next = float(s[k]) if k < len(s) else 0.0
        r[f"eckart_young_k{k}"] = {
            "fro_err2": fro_err2,
            "tail2": tail2,
            "spec_err": spec_err,
            "sigma_next": sigma_next,
            "pass": (abs(fro_err2 - tail2) < 1e-10) and (abs(spec_err - sigma_next) < 1e-10),
        }
    if _HAS_TORCH:
        U_t, s_t, V_t = torch.linalg.svd(torch.tensor(A, dtype=torch.float64), full_matrices=False)
        r["torch_agrees"] = {
            "max_abs_diff_s": float(np.max(np.abs(s_t.numpy() - s))),
            "pass": float(np.max(np.abs(s_t.numpy() - s))) < 1e-10,
        }
    else:
        r["torch_agrees"] = {"pass": True, "note": "torch unavailable"}
    return r


def run_negative_tests():
    r = {}
    rng = np.random.default_rng(1)
    A = rng.standard_normal((5, 4))
    U, s, Vt = np.linalg.svd(A, full_matrices=False)
    bad = U[:, :2] @ np.diag(s[1:3]) @ Vt[:2, :]  # wrong singular values
    fro_err2 = float(np.sum((A - bad) ** 2))
    tail2 = float(np.sum(s[2:] ** 2))
    r["non_top_k_violates_bound"] = {
        "fro_err2": fro_err2,
        "tail2": tail2,
        "pass": fro_err2 > tail2 + 1e-6,
    }
    k = 2
    A_k = _truncate(U, s, Vt, k)
    # Random perturbation of same rank should have >= Frobenius error
    rng2 = np.random.default_rng(7)
    Up = U[:, :k] + 0.3 * rng2.standard_normal(U[:, :k].shape)
    Up, _ = np.linalg.qr(Up)
    A_pert = Up @ (Up.T @ A)
    fro_pert = float(np.sum((A - A_pert) ** 2))
    fro_opt = float(np.sum((A - A_k) ** 2))
    r["optimal_le_perturbed"] = {
        "fro_opt": fro_opt,
        "fro_pert": fro_pert,
        "pass": fro_opt <= fro_pert + 1e-10,
    }
    return r


def run_boundary_tests():
    r = {}
    A = np.eye(4)
    U, s, Vt = np.linalg.svd(A, full_matrices=False)
    A_0 = _truncate(U, s, Vt, 0)
    r["k_zero_full_error"] = {
        "fro_err2": float(np.sum((A - A_0) ** 2)),
        "pass": abs(float(np.sum((A - A_0) ** 2)) - 4.0) < 1e-10,
    }
    A = np.array([[3.0, 0.0], [0.0, 0.0]])
    U, s, Vt = np.linalg.svd(A, full_matrices=False)
    A_1 = _truncate(U, s, Vt, 1)
    r["rank_deficient_exact"] = {
        "fro_err2": float(np.sum((A - A_1) ** 2)),
        "pass": abs(float(np.sum((A - A_1) ** 2))) < 1e-14,
    }
    rng = np.random.default_rng(3)
    A = rng.standard_normal((6, 6))
    U, s, Vt = np.linalg.svd(A, full_matrices=False)
    A_full = _truncate(U, s, Vt, 6)
    r["k_full_zero_error"] = {
        "fro_err2": float(np.sum((A - A_full) ** 2)),
        "pass": float(np.sum((A - A_full) ** 2)) < 1e-20,
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
            "Classical Eckart-Young bounds rest on Frobenius/spectral norms of real matrices "
            "with ordered real singular values. Lost relative to nonclassical compression: "
            "operator-Schatten-p bounds with noncommuting corrections, purification-dependent "
            "rank (rank of density matrix vs rank of its classical embedding), entanglement "
            "spectrum structure, and constraint-admissibility restrictions on which truncations "
            "preserve distinguishability under a probe family."
        ),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_classical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{NAME} all_pass={all_pass} -> {out_path}")
