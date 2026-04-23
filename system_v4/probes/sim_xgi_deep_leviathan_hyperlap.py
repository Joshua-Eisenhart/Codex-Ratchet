#!/usr/bin/env python3
"""
sim_xgi_deep_leviathan_hyperlap.py

Deep xgi integration sim. Lego: Leviathan-shell carrier as a hypergraph
where each hyperedge is a coalition (triad or tetrad) of agents, and the
claim is a distinguishability statement: two agent labelings that induce
DIFFERENT hyperedge-incidence patterns must produce DIFFERENT hypergraph
Laplacian spectra. xgi's hypergraph Laplacian is load-bearing: a plain
graph Laplacian on the 1-skeleton cannot separate these two labelings
(demonstrated in negative test).

Classification: canonical.
"""
import json, os
import numpy as np

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "numeric not needed"},
    "pyg": {"tried": False, "used": False, "reason": "hypergraph, not pairwise graph"},
    "z3": {"tried": False, "used": False, "reason": "spectral claim, not FOL"},
    "cvc5": {"tried": False, "used": False, "reason": "spectral claim, not FOL"},
    "sympy": {"tried": False, "used": False, "reason": "numeric eigenvalues"},
    "clifford": {"tried": False, "used": False, "reason": "no GA"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariance"},
    "rustworkx": {"tried": False, "used": False, "reason": "hypergraph-native tool required"},
    "xgi": {"tried": False, "used": False, "reason": ""},
    "toponetx": {"tried": False, "used": False, "reason": "not cell complex"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistent homology"},
    "networkx": {"tried": False, "used": False, "reason": "graph baseline for negative test"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import xgi
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    xgi = None
    TOOL_MANIFEST["xgi"]["reason"] = "not installed -- BLOCKER"

try:
    import networkx as nx
    TOOL_MANIFEST["networkx"]["tried"] = True
except ImportError:
    nx = None
    TOOL_MANIFEST["networkx"]["reason"] = "not installed"


def leviathan_carrier_A():
    """6 agents, 4 triadic coalitions (distinguishing pattern A)."""
    H = xgi.Hypergraph()
    H.add_nodes_from(range(6))
    H.add_edges_from([(0,1,2), (0,1,3), (2,3,4), (3,4,5)])
    return H


def leviathan_carrier_B():
    """Same 6 agents, DIFFERENT triadic coalitions (pattern B) but
    identical pairwise 1-skeleton: same induced edges {(0,1),(0,2),
    (1,2),(0,3),(1,3),(2,3),(2,4),(3,4),(3,5),(4,5)}? We construct B
    so its 1-skeleton is identical to A but triadic structure differs."""
    H = xgi.Hypergraph()
    H.add_nodes_from(range(6))
    # A's 1-skeleton edges:
    # (0,1),(0,2),(1,2),(0,1),(0,3),(1,3),(2,3),(2,4),(3,4),(3,5),(4,5)
    # We pick triads so union of pairwise edges matches A's skeleton
    # B replaces triads (0,1,2)+(0,1,3) with a single tetrad (0,1,2,3)
    # which covers the same pairwise skeleton on {0,1,2,3} but differs
    # in hyperedge CARDINALITY, so the hyper-Laplacian differs while
    # the 1-skeleton spectrum is identical.
    H.add_edges_from([(0,1,2,3), (2,3,4), (3,4,5)])
    return H


def hypergraph_laplacian_spectrum(H):
    """Compute the normalized clique-expansion-free Laplacian via xgi's
    incidence matrix: L = D_v - B D_e^{-1} B^T where B is node-edge
    incidence and D_v, D_e are degree diagonals."""
    B = xgi.incidence_matrix(H, sparse=False).astype(float)
    d_v = B.sum(axis=1)
    d_e = B.sum(axis=0)
    D_v = np.diag(d_v)
    D_e_inv = np.diag(1.0 / np.where(d_e > 0, d_e, 1.0))
    L = D_v - B @ D_e_inv @ B.T
    w = np.linalg.eigvalsh(0.5 * (L + L.T))
    return np.sort(w)


def skeleton_graph(H):
    g = nx.Graph()
    g.add_nodes_from(H.nodes)
    for e in H.edges.members():
        e = list(e)
        for i in range(len(e)):
            for j in range(i+1, len(e)):
                g.add_edge(e[i], e[j])
    return g


def positive_hyperlap_distinguishes():
    HA = leviathan_carrier_A(); HB = leviathan_carrier_B()
    sA = hypergraph_laplacian_spectrum(HA)
    sB = hypergraph_laplacian_spectrum(HB)
    diff = float(np.max(np.abs(sA - sB)))
    return diff > 1e-6, {"spec_A": sA.tolist(), "spec_B": sB.tolist(), "max_diff": diff}


def negative_skeleton_laplacian_cannot():
    HA = leviathan_carrier_A(); HB = leviathan_carrier_B()
    gA = skeleton_graph(HA); gB = skeleton_graph(HB)
    # If skeletons are isomorphic, their Laplacian spectra coincide and
    # so fail to distinguish -- exactly the distinguishability gap xgi closes.
    iso = nx.is_isomorphic(gA, gB)
    LA = nx.laplacian_matrix(gA).toarray().astype(float)
    LB = nx.laplacian_matrix(gB).toarray().astype(float)
    sA = np.sort(np.linalg.eigvalsh(LA))
    sB = np.sort(np.linalg.eigvalsh(LB))
    same = bool(np.allclose(sA, sB, atol=1e-8))
    # The negative claim: skeleton alone does NOT distinguish when
    # skeletons are isomorphic. PASS = (iso and same).
    return (iso and same), {
        "skeletons_isomorphic": iso, "spec_equal": same,
        "spec_A_skeleton": sA.tolist(), "spec_B_skeleton": sB.tolist(),
    }


def boundary_identical_hypergraphs():
    """Boundary: two copies of the same hypergraph must have identical
    spectrum (within float tol)."""
    HA = leviathan_carrier_A()
    HA2 = leviathan_carrier_A()
    sA = hypergraph_laplacian_spectrum(HA)
    sA2 = hypergraph_laplacian_spectrum(HA2)
    eq = bool(np.allclose(sA, sA2, atol=1e-10))
    return eq, {"max_abs_diff": float(np.max(np.abs(sA - sA2)))}


def run_positive_tests():
    ok, info = positive_hyperlap_distinguishes()
    TOOL_MANIFEST["xgi"]["used"] = True
    TOOL_MANIFEST["xgi"]["reason"] = "xgi hypergraph incidence powers the Laplacian that separates the two Leviathan carriers; clique-expansion graph cannot"
    TOOL_INTEGRATION_DEPTH["xgi"] = "load_bearing"
    return {"hyperlap_separates_leviathan_carriers": {"pass": ok, **info}}


def run_negative_tests():
    if nx is None:
        return {"skeleton_cannot_separate": {"pass": False, "reason": "networkx missing"}}
    ok, info = negative_skeleton_laplacian_cannot()
    TOOL_MANIFEST["networkx"]["used"] = True
    TOOL_MANIFEST["networkx"]["reason"] = "baseline 1-skeleton Laplacian; its failure to separate IS the negative test"
    TOOL_INTEGRATION_DEPTH["networkx"] = "supportive"
    return {"skeleton_cannot_separate": {"pass": ok, **info}}


def run_boundary_tests():
    ok, info = boundary_identical_hypergraphs()
    return {"identical_hypergraphs_identical_spectrum": {"pass": ok, **info}}


if __name__ == "__main__":
    if xgi is None:
        print("BLOCKER: xgi not importable")
        raise SystemExit(2)
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = (all(v["pass"] for v in pos.values())
                and all(v["pass"] for v in neg.values())
                and all(v["pass"] for v in bnd.values()))
    results = {
        "name": "sim_xgi_deep_leviathan_hyperlap",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "overall_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_xgi_deep_leviathan_hyperlap_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {out_path}")
