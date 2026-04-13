#!/usr/bin/env python3
"""Classical baseline: schmidt_mode_truncation on known bipartite states."""
import json, os, numpy as np
from _classical_baseline_common import TOOL_MANIFEST, TOOL_INTEGRATION_DEPTH
classification = "classical_baseline"

NAME = "schmidt_mode_truncation"

def schmidt(psi, dA, dB):
    M = psi.reshape(dA, dB)
    U, s, Vt = np.linalg.svd(M, full_matrices=False)
    return U, s, Vt

def truncate_schmidt(psi, dA, dB, k):
    U, s, Vt = schmidt(psi, dA, dB)
    s_trunc = np.copy(s); s_trunc[k:] = 0
    return (U @ np.diag(s_trunc) @ Vt).reshape(-1), s

def run_positive_tests():
    r = {}
    # Bell state |00>+|11> / sqrt2 -> Schmidt coeffs [1/sqrt2, 1/sqrt2]
    psi = np.array([1, 0, 0, 1]) / np.sqrt(2)
    _, s, _ = schmidt(psi, 2, 2)
    r["bell_schmidt"] = {"s": s.tolist(), "pass": np.allclose(sorted(s, reverse=True), [1/np.sqrt(2)] * 2)}
    # Product state |0>|0>: one nonzero coefficient
    psi = np.array([1, 0, 0, 0])
    _, s, _ = schmidt(psi, 2, 2)
    r["product_one_mode"] = {"s": s.tolist(), "pass": abs(s[0] - 1) < 1e-12 and abs(s[1]) < 1e-12}
    # Norm preserved by full svd reconstruction
    rng = np.random.default_rng(0)
    psi = rng.standard_normal(12); psi /= np.linalg.norm(psi)
    psi_rec, _ = truncate_schmidt(psi, 3, 4, 3)
    r["full_reconstruction"] = {"err": float(np.linalg.norm(psi - psi_rec)), "pass": np.linalg.norm(psi - psi_rec) < 1e-10}
    # Truncation error = sqrt(sum discarded s^2)
    psi_trunc, s = truncate_schmidt(psi, 3, 4, 1)
    err = np.linalg.norm(psi - psi_trunc)
    expected = float(np.sqrt(np.sum(s[1:] ** 2)))
    r["truncation_error_formula"] = {"err": float(err), "expected": expected, "pass": abs(err - expected) < 1e-10}
    # Schmidt coefficients sum-squared = 1 for normalized state
    r["sum_s2_is_one"] = {"sum": float(np.sum(s ** 2)), "pass": abs(np.sum(s ** 2) - 1) < 1e-10}
    return r

def run_negative_tests():
    r = {}
    # GHZ-like 3-qubit (|000>+|111>)/sqrt2 — schmidt across 1|23 bipartition: 2 modes
    psi = np.zeros(8); psi[0] = 1; psi[7] = 1; psi /= np.sqrt(2)
    _, s, _ = schmidt(psi, 2, 4)
    # Entangled: NOT single-mode product
    r["ghz_not_product"] = {"s": s.tolist(), "pass": s[1] > 0.1}
    # Truncating entangled state to k=1 loses norm
    psi_t, _ = truncate_schmidt(psi, 2, 4, 1)
    r["trunc_entangled_loses_norm"] = {"norm": float(np.linalg.norm(psi_t)), "pass": float(np.linalg.norm(psi_t)) < 0.99}
    return r

def run_boundary_tests():
    r = {}
    # k=0 -> zero state
    psi = np.array([1, 1, 1, 1]) / 2.0
    psi_t, _ = truncate_schmidt(psi, 2, 2, 0)
    r["k0_zero"] = {"norm": float(np.linalg.norm(psi_t)), "pass": float(np.linalg.norm(psi_t)) < 1e-12}
    # k = min(dA, dB): full
    psi_t, _ = truncate_schmidt(psi, 2, 2, 2)
    r["k_full"] = {"err": float(np.linalg.norm(psi - psi_t)), "pass": float(np.linalg.norm(psi - psi_t)) < 1e-12}
    # Asymmetric dims (2,3)
    rng = np.random.default_rng(1)
    psi = rng.standard_normal(6); psi /= np.linalg.norm(psi)
    _, s, _ = schmidt(psi, 2, 3)
    r["asymmetric_bipartition"] = {"num_modes": int(len(s)), "pass": len(s) == 2}
    return r

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(v.get("pass", False) for v in list(pos.values()) + list(neg.values()) + list(bnd.values()))
    results = {"name": NAME, "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "all_pass": all_pass,
        "note": "classical captures: Schmidt via SVD on reshaped bipartition, coefficient normalization, truncation error bound. Innately fails: multi-partite tensor (>2) entanglement structure; no single Schmidt decomp exists for tripartite."}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results"); os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_classical_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"{NAME} all_pass={all_pass} -> {out_path}")
