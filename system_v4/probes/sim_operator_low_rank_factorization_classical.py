#!/usr/bin/env python3
"""Classical baseline: operator_low_rank_factorization (A ~ B C, rank k)."""
import json, os, numpy as np
from _classical_baseline_common import TOOL_MANIFEST, TOOL_INTEGRATION_DEPTH
classification = "classical_baseline"

NAME = "operator_low_rank_factorization"

def lowrank_factor(A, k):
    U, s, Vt = np.linalg.svd(A, full_matrices=False)
    B = U[:, :k] * s[:k]
    C = Vt[:k, :]
    return B, C

def run_positive_tests():
    r = {}
    rng = np.random.default_rng(0)
    # true rank-k
    B0 = rng.standard_normal((6, 3)); C0 = rng.standard_normal((3, 5))
    A = B0 @ C0
    B, C = lowrank_factor(A, 3)
    r["exact_rank_recovery"] = {"err": float(np.linalg.norm(A - B @ C)), "pass": np.linalg.norm(A - B @ C) < 1e-10}
    # shapes
    r["factor_shapes"] = {"B": list(B.shape), "C": list(C.shape), "pass": B.shape == (6, 3) and C.shape == (3, 5)}
    # rank of product
    r["product_rank"] = {"rank": int(np.linalg.matrix_rank(B @ C, tol=1e-8)), "pass": int(np.linalg.matrix_rank(B @ C, tol=1e-8)) == 3}
    # Eckart-Young on truncation error
    M = rng.standard_normal((5, 7))
    _, s, _ = np.linalg.svd(M, full_matrices=False)
    B, C = lowrank_factor(M, 2)
    err = np.linalg.norm(M - B @ C)
    expected = float(np.sqrt(np.sum(s[2:] ** 2)))
    r["ey_error"] = {"err": float(err), "expected": expected, "pass": abs(err - expected) < 1e-8}
    return r

def run_negative_tests():
    r = {}
    rng = np.random.default_rng(1)
    A = rng.standard_normal((4, 4))
    # random factorization
    Bbad = rng.standard_normal((4, 2)); Cbad = rng.standard_normal((2, 4))
    B, C = lowrank_factor(A, 2)
    r["random_factor_worse"] = {"bad": float(np.linalg.norm(A - Bbad @ Cbad)), "good": float(np.linalg.norm(A - B @ C)),
        "pass": np.linalg.norm(A - Bbad @ Cbad) > np.linalg.norm(A - B @ C)}
    # k=0 -> zero product
    B, C = lowrank_factor(A, 0)
    r["k0_zero_product"] = {"err": float(np.linalg.norm(B @ C)), "pass": np.linalg.norm(B @ C) < 1e-10}
    return r

def run_boundary_tests():
    r = {}
    # k > rank
    A = np.diag([2.0, 1.0, 0.0, 0.0])
    B, C = lowrank_factor(A, 4)
    r["k_exceeds_rank_ok"] = {"err": float(np.linalg.norm(A - B @ C)), "pass": np.linalg.norm(A - B @ C) < 1e-10}
    # rectangular tall
    rng = np.random.default_rng(3)
    M = rng.standard_normal((10, 3))
    B, C = lowrank_factor(M, 3)
    r["tall_exact"] = {"err": float(np.linalg.norm(M - B @ C)), "pass": np.linalg.norm(M - B @ C) < 1e-10}
    return r

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(v.get("pass", False) for v in list(pos.values()) + list(neg.values()) + list(bnd.values()))
    results = {"name": NAME, "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "all_pass": all_pass,
        "note": "classical captures: A=BC factorization via truncated SVD, Eckart-Young optimality. Innately fails: gauge freedom (B->BG, C->G^-1 C) non-unique; CP-map / Kraus factorization constraints not enforced."}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results"); os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_classical_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"{NAME} all_pass={all_pass} -> {out_path}")
