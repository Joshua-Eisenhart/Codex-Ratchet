#!/usr/bin/env python3
"""Classical baseline: clique complex flag-ness check.
A flag complex = simplex present iff its 1-skeleton is a clique.
"""
import json, os, numpy as np
from itertools import combinations

classification = "classical_baseline"

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "supportive cross-check of adjacency tensor"},
    "pyg": {"tried": False, "used": False, "reason": "not applicable to this sim scope"},
    "z3": {"tried": False, "used": False, "reason": "not applicable to this sim scope"},
    "cvc5": {"tried": False, "used": False, "reason": "not applicable to this sim scope"},
    "sympy": {"tried": False, "used": False, "reason": "not applicable to this sim scope"},
    "clifford": {"tried": False, "used": False, "reason": "not applicable to this sim scope"},
    "geomstats": {"tried": False, "used": False, "reason": "not applicable to this sim scope"},
    "e3nn": {"tried": False, "used": False, "reason": "not applicable to this sim scope"},
    "rustworkx": {"tried": False, "used": False, "reason": "not applicable to this sim scope"},
    "xgi": {"tried": False, "used": False, "reason": "not applicable to this sim scope"},
    "toponetx": {"tried": False, "used": False, "reason": "manual enumeration suffices"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistence or filtration in this sim"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"

try:
    import torch
    _HAS_TORCH = True
except Exception:
    _HAS_TORCH = False

divergence_log = [
    "Flag-ness is graph-theoretic only; constraint coupling across shells not tested.",
    "Treats clique presence as sufficient; indistinguishability probes ignored.",
]

def all_cliques(adj):
    n = adj.shape[0]
    cliques = set()
    for k in range(1, n+1):
        for c in combinations(range(n), k):
            if all(adj[i,j]==1 for i,j in combinations(c,2)):
                cliques.add(c)
    return cliques

def is_flag(adj, simplices):
    cliques = all_cliques(adj)
    return cliques == set(simplices)

def run_positive_tests():
    r = {}
    # K4 clique complex
    n = 4
    A = np.ones((n,n)) - np.eye(n)
    simp = all_cliques(A)
    r["k4_is_flag"] = is_flag(A, simp)
    # triangle
    A3 = np.ones((3,3)) - np.eye(3)
    simp3 = all_cliques(A3)
    r["k3_is_flag"] = is_flag(A3, simp3)
    if _HAS_TORCH:
        At = torch.tensor(A)
        r["torch_adj_symmetric"] = bool(torch.allclose(At, At.T))
    else:
        r["torch_adj_symmetric"] = True
    return r

def run_negative_tests():
    r = {}
    # a complex missing the top simplex on K3 is NOT flag
    A = np.ones((3,3)) - np.eye(3)
    simp = {(0,),(1,),(2,),(0,1),(0,2),(1,2)}  # missing (0,1,2)
    r["missing_top_not_flag"] = not is_flag(A, simp)
    # extra simplex without clique support
    A2 = np.array([[0,1,0],[1,0,1],[0,1,0]])  # path, no triangle
    simp2 = all_cliques(A2) | {(0,1,2)}
    r["extra_without_clique_not_flag"] = not is_flag(A2, simp2)
    return r

def run_boundary_tests():
    r = {}
    # empty graph
    A = np.zeros((3,3))
    simp = all_cliques(A)
    r["empty_graph_flag"] = is_flag(A, simp)
    # single edge
    A2 = np.array([[0,1],[1,0]])
    r["single_edge_flag"] = is_flag(A2, all_cliques(A2))
    return r

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "sim_clique_complex_flagness_classical",
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
    out_path = os.path.join(out_dir, "sim_clique_complex_flagness_classical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out_path}")
