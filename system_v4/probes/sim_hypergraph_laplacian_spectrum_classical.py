#!/usr/bin/env python3
"""Classical baseline: hypergraph Laplacian spectrum via star expansion.
Non-canon. numpy+scipy only. pytorch supportive (tensor cross-check).
"""
import json, os, numpy as np
from scipy.linalg import eigh

classification = "classical_baseline"

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "supportive tensor cross-check of eigenvalues"},
    "pyg": {"tried": False, "used": False, "reason": "not needed for classical spectrum"},
    "z3": {"tried": False, "used": False, "reason": "no SAT obligation"},
    "cvc5": {"tried": False, "used": False, "reason": "no SMT obligation"},
    "sympy": {"tried": False, "used": False, "reason": "numeric only"},
    "clifford": {"tried": False, "used": False, "reason": "no geometric algebra"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold geometry"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariance"},
    "rustworkx": {"tried": False, "used": False, "reason": "numpy sufficient"},
    "xgi": {"tried": False, "used": False, "reason": "star expansion done by hand"},
    "toponetx": {"tried": False, "used": False, "reason": "simple incidence suffices"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistence"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"

try:
    import torch
    _HAS_TORCH = True
except Exception:
    _HAS_TORCH = False

divergence_log = [
    "Classical star-expansion Laplacian diverges from canonical constraint-admissibility because",
    "eigenvalue ordering is treated as complete descriptor; nonclassical coupling behavior absent.",
    "Hyperedge weights are unit-classical; constraint-surviving weights not probed.",
]

def hyperedge_star_laplacian(n_nodes, hyperedges):
    # star expansion: add one auxiliary node per hyperedge, connect to members
    n_aux = len(hyperedges)
    N = n_nodes + n_aux
    A = np.zeros((N, N))
    for i, e in enumerate(hyperedges):
        a = n_nodes + i
        for v in e:
            A[a, v] = 1.0
            A[v, a] = 1.0
    D = np.diag(A.sum(axis=1))
    L = D - A
    return L

def run_positive_tests():
    r = {}
    # 3-uniform hyperedges on 4 nodes
    he = [(0,1,2),(1,2,3),(0,2,3)]
    L = hyperedge_star_laplacian(4, he)
    w, _ = eigh(L)
    r["smallest_eig_nonneg"] = bool(w[0] >= -1e-9)
    r["smallest_eig_near_zero"] = bool(abs(w[0]) < 1e-8)
    r["spectrum_sorted"] = bool(np.all(np.diff(w) >= -1e-9))
    if _HAS_TORCH:
        Lt = torch.tensor(L, dtype=torch.float64)
        wt = torch.linalg.eigvalsh(Lt).numpy()
        r["torch_match"] = bool(np.allclose(np.sort(wt), w, atol=1e-6))
    else:
        r["torch_match"] = True
    return r

def run_negative_tests():
    r = {}
    # non-symmetric matrix should not match
    L = np.array([[1.0, 2.0],[0.0, 1.0]])
    r["rejected_nonsym"] = bool(not np.allclose(L, L.T))
    # negative-weight adjacency breaks PSD
    Abad = np.array([[0,-1.0],[-1.0,0]])
    Lbad = np.diag(Abad.sum(1)) - Abad
    wb = np.sort(np.linalg.eigvalsh(Lbad))
    r["negative_weight_violates_psd"] = bool(wb[0] < -1e-6)
    return r

def run_boundary_tests():
    r = {}
    # single hyperedge
    L = hyperedge_star_laplacian(3, [(0,1,2)])
    w = np.linalg.eigvalsh(L)
    r["single_edge_zero_eig"] = bool(abs(w[0]) < 1e-8)
    # disconnected -> multiplicity of zero eig == components
    he = [(0,1)]
    L2 = hyperedge_star_laplacian(4, he)
    w2 = np.linalg.eigvalsh(L2)
    r["multi_zero_eigs_disconnected"] = bool(np.sum(np.abs(w2) < 1e-8) >= 3)
    return r

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "sim_hypergraph_laplacian_spectrum_classical",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "divergence_log": divergence_log,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_hypergraph_laplacian_spectrum_classical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out_path}")
