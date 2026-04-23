#!/usr/bin/env python3
"""Classical baseline: qpca_spectral_extraction (classical PCA on density-like matrices).
Boundary-data: classical PCA on quantum density matrices does NOT recover purification modes."""
import json, os, numpy as np
from _classical_baseline_common import TOOL_MANIFEST, TOOL_INTEGRATION_DEPTH
classification = "classical_baseline"

NAME = "qpca_spectral_extraction"

def classical_pca(rho, k):
    rho = (rho + rho.conj().T) / 2
    w, V = np.linalg.eigh(rho)
    idx = np.argsort(-w.real)[:k]
    return w[idx].real, V[:, idx]

def run_positive_tests():
    r = {}
    # Diagonal density matrix (classical mixture) -> eigenvalues are populations
    rho = np.diag([0.5, 0.3, 0.15, 0.05])
    w, V = classical_pca(rho, 2)
    r["diagonal_rho_eigs"] = {"eigs": w.tolist(), "pass": np.allclose(w, [0.5, 0.3])}
    # trace preserved (of full spectrum)
    w_full, _ = classical_pca(rho, 4)
    r["trace_sum_eigs"] = {"trace": float(np.trace(rho)), "sum_eigs": float(np.sum(w_full)), "pass": abs(np.trace(rho) - np.sum(w_full)) < 1e-12}
    # Positive density: eigenvalues in [0,1]
    rng = np.random.default_rng(0)
    X = rng.standard_normal((4, 4)); rho2 = X @ X.T; rho2 /= np.trace(rho2)
    w2, _ = classical_pca(rho2, 4)
    r["eigs_nonneg_bounded"] = {"min": float(w2.min()), "max": float(w2.max()), "pass": w2.min() > -1e-10 and w2.max() < 1 + 1e-10}
    return r

def run_negative_tests():
    r = {}
    # Pure-state density rho = |psi><psi| where |psi| = (|0>+|1>)/sqrt2 on 2 qubits
    # Purified coherent state has off-diagonal coherences. Classical "diag-PCA" (keeping diagonal only) fails.
    psi = np.array([1, 1, 1, 1]) / 2.0
    rho = np.outer(psi, psi.conj())
    # True pure state: one eigenvalue=1, rest=0
    w, _ = classical_pca(rho, 4)
    r["pure_state_has_single_unit_eig"] = {"eigs": w.tolist(), "pass": abs(w[0] - 1.0) < 1e-10 and abs(w[1]) < 1e-10}
    # If we throw away off-diagonals (naive diag PCA), we wrongly see maximally mixed state
    rho_diag = np.diag(np.diag(rho))
    w_diag, _ = classical_pca(rho_diag, 4)
    r["diag_only_misses_purity"] = {"top_eig": float(w_diag[0]), "pass": float(w_diag[0]) < 0.5}  # boundary data: innate failure mode
    return r

def run_boundary_tests():
    r = {}
    # Maximally mixed state
    rho = np.eye(4) / 4
    w, _ = classical_pca(rho, 4)
    r["max_mixed_degenerate"] = {"eigs": w.tolist(), "pass": np.allclose(w, 0.25)}
    # Rank-1 density matrix (pure): only one nonzero eigenvalue
    psi = np.array([0.6, 0.8, 0, 0])
    rho = np.outer(psi, psi)
    w, _ = classical_pca(rho, 4)
    r["pure_rank1"] = {"eigs": w.tolist(), "pass": abs(w[0] - 1.0) < 1e-10 and max(abs(w[1:])) < 1e-10}
    # Complex Hermitian rho
    H = np.array([[0.5, 0.3j], [-0.3j, 0.5]])
    w, _ = classical_pca(H, 2)
    r["complex_hermitian_real_eigs"] = {"eigs": w.tolist(), "pass": np.allclose(sorted(w), [0.2, 0.8])}
    return r

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(v.get("pass", False) for v in list(pos.values()) + list(neg.values()) + list(bnd.values()))
    results = {"name": NAME, "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "all_pass": all_pass,
        "note": "classical captures: spectrum of density matrix via eigh when given full Hermitian rho. Innately fails: QPCA's advantage (coherent access to rho^k, exponential speedup), and any approach that throws away off-diagonal coherences collapses pure states into mixed."}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results"); os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_classical_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"{NAME} all_pass={all_pass} -> {out_path}")
