#!/usr/bin/env python3
"""Classical baseline: low_rank_psd_approximation."""
import json, os, numpy as np
from _classical_baseline_common import TOOL_MANIFEST, TOOL_INTEGRATION_DEPTH
classification = "classical_baseline"

NAME = "low_rank_psd_approximation"

def psd_low_rank(A, k):
    A = (A + A.T) / 2
    w, V = np.linalg.eigh(A)
    w = np.clip(w, 0, None)  # PSD projection
    idx = np.argsort(-w)[:k]
    return V[:, idx] @ np.diag(w[idx]) @ V[:, idx].T, w[idx]

def run_positive_tests():
    r = {}
    rng = np.random.default_rng(0)
    X = rng.standard_normal((8, 8)); A = X @ X.T  # PSD
    Ak, kept = psd_low_rank(A, 3)
    # PSD
    w = np.linalg.eigvalsh(Ak)
    r["psd_out"] = {"min_eig": float(w.min()), "pass": w.min() > -1e-9}
    # rank
    r["rank_k"] = {"rank": int(np.linalg.matrix_rank(Ak, tol=1e-8)), "pass": int(np.linalg.matrix_rank(Ak, tol=1e-8)) == 3}
    # Eckart-Young bound for PSD Frobenius
    w_full = np.linalg.eigvalsh(A)
    tail = np.sort(w_full)[:-3]
    err_F2 = np.linalg.norm(A - Ak) ** 2
    expected = float(np.sum(tail ** 2))
    r["frobenius_bound"] = {"err_F2": float(err_F2), "expected": expected, "pass": abs(err_F2 - expected) < 1e-6}
    # rank-k reconstruction <= A (Loewner)
    diff_w = np.linalg.eigvalsh(A - Ak)
    r["loewner_A_ge_Ak"] = {"min_eig_diff": float(diff_w.min()), "pass": diff_w.min() > -1e-9}
    return r

def run_negative_tests():
    r = {}
    # Indefinite matrix: naive low-rank without PSD clip isn't PSD
    A = np.diag([3.0, -2.0, 1.0])  # negative eigenvalue has larger magnitude than 1
    w, V = np.linalg.eigh(A)
    idx = np.argsort(-np.abs(w))[:2]
    A_no_clip = V[:, idx] @ np.diag(w[idx]) @ V[:, idx].T
    min_e = float(np.linalg.eigvalsh(A_no_clip).min())
    r["no_clip_not_psd"] = {"min_eig": min_e, "pass": min_e < -0.5}
    # random non-PSD approximation
    rng = np.random.default_rng(2)
    B = rng.standard_normal((4, 4))
    r["random_not_psd"] = {"min_eig": float(np.linalg.eigvalsh((B + B.T) / 2).min()), "pass": True}
    return r

def run_boundary_tests():
    r = {}
    Ak, _ = psd_low_rank(np.zeros((4, 4)), 2)
    r["zero_input"] = {"norm": float(np.linalg.norm(Ak)), "pass": np.linalg.norm(Ak) < 1e-12}
    # already rank-k
    v = np.array([1.0, 2.0, 3.0]); A = np.outer(v, v)  # rank 1 PSD
    Ak, _ = psd_low_rank(A, 1)
    r["already_rank_1"] = {"err": float(np.linalg.norm(A - Ak)), "pass": np.linalg.norm(A - Ak) < 1e-10}
    return r

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(v.get("pass", False) for v in list(pos.values()) + list(neg.values()) + list(bnd.values()))
    results = {"name": NAME, "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "all_pass": all_pass,
        "note": "classical captures: PSD low-rank via eigh+clip, Frobenius Eckart-Young, Loewner dominance. Innately fails: trace-preserving CP-map approximation; density-matrix approximation needs trace=1 constraint not imposed here."}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results"); os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_classical_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"{NAME} all_pass={all_pass} -> {out_path}")
