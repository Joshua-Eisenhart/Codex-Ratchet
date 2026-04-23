#!/usr/bin/env python3
"""
sim_networkx_deep_expander_gap.py

Deep networkx integration sim. Lego: candidate constraint-manifold
transition graph. Claim: a 3-regular Ramanujan-like graph (a random
3-regular graph on 32 nodes, seed-fixed) admits a large spectral gap
(lambda_1 of the normalized Laplacian bounded away from 0), which is
load-bearing for a distinguishability claim on the transition manifold
(well-mixed within O(log n) steps). Negative test: a cycle graph C_32
has near-zero spectral gap and therefore does not satisfy the expander
property. Also closes an outstanding manifest-gate violation by
declaring networkx explicitly.

Classification: canonical (the spectral gap verdict IS the admission
evidence for "candidate transition manifold is an expander").
"""
import json, os
import numpy as np

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "numeric not needed"},
    "pyg": {"tried": False, "used": False, "reason": "no message passing"},
    "z3": {"tried": False, "used": False, "reason": "spectral numeric claim"},
    "cvc5": {"tried": False, "used": False, "reason": "spectral numeric claim"},
    "sympy": {"tried": False, "used": False, "reason": "numeric eigenvalues"},
    "clifford": {"tried": False, "used": False, "reason": "no GA"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold mean"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariance"},
    "rustworkx": {"tried": False, "used": False, "reason": "could substitute; networkx chosen for API match"},
    "xgi": {"tried": False, "used": False, "reason": "pairwise graph, not hypergraph"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistent homology"},
    "networkx": {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import networkx as nx
    TOOL_MANIFEST["networkx"]["tried"] = True
except ImportError:
    nx = None
    TOOL_MANIFEST["networkx"]["reason"] = "not installed -- BLOCKER"


def normalized_laplacian_spectrum(G):
    L = nx.normalized_laplacian_matrix(G).toarray()
    w = np.linalg.eigvalsh(0.5 * (L + L.T))
    return np.sort(w)


def positive_3regular_has_gap():
    G = nx.random_regular_graph(d=3, n=32, seed=1)
    w = normalized_laplacian_spectrum(G)
    # smallest nonzero eigenvalue (skip near-zero lambda_0)
    lam1 = float(w[1])
    gap_ok = lam1 > 0.05  # bounded well above the cycle-graph floor (~0.02)
    return gap_ok, {"lambda_1": lam1, "spectrum_head": w[:5].tolist()}


def negative_cycle_no_gap():
    G = nx.cycle_graph(32)
    w = normalized_laplacian_spectrum(G)
    lam1 = float(w[1])
    return lam1 < 0.02, {"lambda_1": lam1, "spectrum_head": w[:5].tolist()}


def boundary_complete_graph_max_gap():
    """Boundary: K_n has lambda_1 = n/(n-1) on the normalized Laplacian
    -- the maximum possible spectral gap. For n=16, that is 16/15."""
    n = 16
    G = nx.complete_graph(n)
    w = normalized_laplacian_spectrum(G)
    lam1 = float(w[1])
    target = n / (n - 1.0)
    return abs(lam1 - target) < 1e-8, {"lambda_1": lam1, "target": target}


def run_positive_tests():
    ok, info = positive_3regular_has_gap()
    TOOL_MANIFEST["networkx"]["used"] = True
    TOOL_MANIFEST["networkx"]["reason"] = "networkx builds the candidate transition graph and its normalized Laplacian; spectral gap verdict is the admission evidence"
    TOOL_INTEGRATION_DEPTH["networkx"] = "load_bearing"
    return {"random_3regular_expander_gap": {"pass": ok, **info}}


def run_negative_tests():
    ok, info = negative_cycle_no_gap()
    return {"cycle_graph_no_gap": {"pass": ok, **info}}


def run_boundary_tests():
    ok, info = boundary_complete_graph_max_gap()
    return {"complete_graph_max_gap": {"pass": ok, **info}}


if __name__ == "__main__":
    if nx is None:
        print("BLOCKER: networkx not importable")
        raise SystemExit(2)
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = (all(v["pass"] for v in pos.values())
                and all(v["pass"] for v in neg.values())
                and all(v["pass"] for v in bnd.values()))
    results = {
        "name": "sim_networkx_deep_expander_gap",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "overall_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_networkx_deep_expander_gap_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {out_path}")
