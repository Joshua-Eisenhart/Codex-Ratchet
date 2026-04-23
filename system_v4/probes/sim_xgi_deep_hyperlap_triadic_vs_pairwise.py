#!/usr/bin/env python3
"""
sim_xgi_deep_hyperlap_triadic_vs_pairwise.py

Tightened version of the triadic-vs-pairwise hyper-Laplacian separation
claim. Two hypergraphs H_tri and H_pair share IDENTICAL 1-skeletons
(same pairwise edge multiset, isomorphic graph projection), but one
carries genuine triadic hyperedges {a,b,c} while the other carries
only the three pairwise edges {a,b},{a,c},{b,c}. xgi hypergraph
Laplacian is load_bearing: graph Laplacian on projection collapses
them; xgi preserves cardinality and separates.

Classification: canonical.
"""
import json, os
import numpy as np

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "numeric eig only"},
    "pyg": {"tried": False, "used": False, "reason": "not a pairwise graph sim"},
    "z3": {"tried": False, "used": False, "reason": "spectral, not FOL"},
    "cvc5": {"tried": False, "used": False, "reason": "spectral, not FOL"},
    "sympy": {"tried": False, "used": False, "reason": "numeric eigs"},
    "clifford": {"tried": False, "used": False, "reason": "no GA"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariance"},
    "rustworkx": {"tried": False, "used": False, "reason": "hypergraph-native required"},
    "xgi": {"tried": False, "used": False, "reason": ""},
    "toponetx": {"tried": False, "used": False, "reason": "pure hypergraph claim"},
    "gudhi": {"tried": False, "used": False, "reason": "no homology"},
    "networkx": {"tried": False, "used": False, "reason": "graph baseline for ablation"},
    "numpy": {"tried": True, "used": True, "reason": "eigendecomposition only; not the distinguishing structure"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["numpy"] = "supportive"

try:
    import xgi
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    xgi = None
try:
    import networkx as nx
    TOOL_MANIFEST["networkx"]["tried"] = True
except ImportError:
    nx = None


def H_triadic():
    H = xgi.Hypergraph()
    H.add_nodes_from(range(4))
    # two triangles sharing edge (0,1)
    H.add_edges_from([(0, 1, 2), (0, 1, 3)])
    return H


def H_pairwise():
    H = xgi.Hypergraph()
    H.add_nodes_from(range(4))
    # identical 1-skeleton as H_triadic (edges: 01,02,12,03,13)
    H.add_edges_from([(0, 1), (0, 2), (1, 2), (0, 3), (1, 3)])
    return H


def hyper_lap_spec(H):
    B = xgi.incidence_matrix(H, sparse=False).astype(float)
    d_v = B.sum(axis=1)
    d_e = B.sum(axis=0)
    D_v = np.diag(d_v)
    D_e_inv = np.diag(1.0 / np.where(d_e > 0, d_e, 1.0))
    L = D_v - B @ D_e_inv @ B.T
    return np.sort(np.linalg.eigvalsh(0.5 * (L + L.T)))


def skeleton(H):
    g = nx.Graph()
    g.add_nodes_from(H.nodes)
    for e in H.edges.members():
        e = list(e)
        for i in range(len(e)):
            for j in range(i + 1, len(e)):
                g.add_edge(e[i], e[j])
    return g


def run_positive_tests():
    HT, HP = H_triadic(), H_pairwise()
    sT = hyper_lap_spec(HT); sP = hyper_lap_spec(HP)
    diff = float(np.max(np.abs(sT - sP)))
    ok = diff > 1e-6
    TOOL_MANIFEST["xgi"]["used"] = True
    TOOL_MANIFEST["xgi"]["reason"] = "hypergraph incidence with true edge cardinality separates triadic from pairwise carriers sharing 1-skeleton"
    TOOL_INTEGRATION_DEPTH["xgi"] = "load_bearing"
    return {"hyperlap_separates_tri_vs_pair": {"pass": ok, "spec_tri": sT.tolist(),
                                                "spec_pair": sP.tolist(), "max_diff": diff}}


def run_negative_tests():
    if nx is None:
        return {"skeleton_lap_collapses": {"pass": False, "reason": "networkx missing"}}
    HT, HP = H_triadic(), H_pairwise()
    gT, gP = skeleton(HT), skeleton(HP)
    iso = nx.is_isomorphic(gT, gP)
    sT = np.sort(np.linalg.eigvalsh(nx.laplacian_matrix(gT).toarray().astype(float)))
    sP = np.sort(np.linalg.eigvalsh(nx.laplacian_matrix(gP).toarray().astype(float)))
    same = bool(np.allclose(sT, sP, atol=1e-8))
    TOOL_MANIFEST["networkx"]["used"] = True
    TOOL_MANIFEST["networkx"]["reason"] = "graph-projection ablation; its spectral collapse IS the negative"
    TOOL_INTEGRATION_DEPTH["networkx"] = "supportive"
    return {"skeleton_lap_collapses": {"pass": (iso and same),
                                       "iso": iso, "spec_equal": same,
                                       "spec_tri_skel": sT.tolist(), "spec_pair_skel": sP.tolist()}}


def run_boundary_tests():
    HT = H_triadic()
    s1 = hyper_lap_spec(HT); s2 = hyper_lap_spec(H_triadic())
    return {"identical_input_identical_spectrum": {"pass": bool(np.allclose(s1, s2, atol=1e-10)),
                                                    "max_abs_diff": float(np.max(np.abs(s1 - s2)))}}


if __name__ == "__main__":
    if xgi is None:
        raise SystemExit("BLOCKER: xgi missing")
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(v.get("pass") for v in {**pos, **neg, **bnd}.values())
    out = {"name": "sim_xgi_deep_hyperlap_triadic_vs_pairwise",
           "classification": "canonical",
           "tool_manifest": TOOL_MANIFEST,
           "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
           "positive": pos, "negative": neg, "boundary": bnd,
           "overall_pass": all_pass}
    d = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "sim_xgi_deep_hyperlap_triadic_vs_pairwise_results.json")
    with open(p, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {p}")
