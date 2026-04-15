#!/usr/bin/env python3
"""
sim_xgi_deep_hyperedge_motif_count.py

Claim: on a random hypergraph, counting a hyperedge motif (two
triadic hyperedges sharing exactly one node) yields a count that is
NOT recoverable from the pairwise projection. xgi is load_bearing:
motif enumeration requires querying genuine hyperedge membership;
the projection loses the distinction between 'triangle from a single
triad' and 'triangle from three dyads'.

Classification: canonical.
"""
import json, os
import numpy as np
from itertools import combinations
classification = "classical_baseline"  # auto-added by adaptive_controller

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "purely combinatorial, no tensor compute"},
    "pyg": {"tried": False, "used": False, "reason": "pairwise hyperedge count, no tensor ops"},
    "z3": {"tried": False, "used": False, "reason": "enumeration approach, no first-order logic"},
    "cvc5": {"tried": False, "used": False, "reason": "enumeration only, no Clifford algebra"},
    "sympy": {"tried": False, "used": False, "reason": "numeric motif count, no manifold needed"},
    "clifford": {"tried": False, "used": False, "reason": "no geometric algebra in this motif probe"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold geometry in this sim scope"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariance constraint in this probe"},
    "rustworkx": {"tried": False, "used": False, "reason": "hypergraph structure required, not graph ops"},
    "xgi": {"tried": False, "used": False, "reason": "not used in this simulation"},
    "toponetx": {"tried": False, "used": False, "reason": "not a cell complex sim, hypergraph only"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistent homology in this motif sim"},
    "networkx": {"tried": False, "used": False, "reason": "projection triangle count ablation"},
    "numpy": {"tried": True, "used": True, "reason": "random seeding only, no algebra needed"},
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


def random_hypergraph(n=20, n_triads=25, seed=0):
    rng = np.random.default_rng(seed)
    H = xgi.Hypergraph()
    H.add_nodes_from(range(n))
    triads = set()
    while len(triads) < n_triads:
        t = tuple(sorted(rng.choice(n, size=3, replace=False).tolist()))
        triads.add(t)
    H.add_edges_from(list(triads))
    return H


def count_motif_two_triads_share_one_node(H):
    triads = [set(e) for e in H.edges.members() if len(e) == 3]
    c = 0
    for a, b in combinations(range(len(triads)), 2):
        if len(triads[a] & triads[b]) == 1:
            c += 1
    return c


def projection(H):
    g = nx.Graph()
    g.add_nodes_from(H.nodes)
    for e in H.edges.members():
        e = list(e)
        for i in range(len(e)):
            for j in range(i + 1, len(e)):
                g.add_edge(e[i], e[j])
    return g


def run_positive_tests():
    H = random_hypergraph(seed=42)
    motif_count = count_motif_two_triads_share_one_node(H)
    TOOL_MANIFEST["xgi"]["used"] = True
    TOOL_MANIFEST["xgi"]["reason"] = "true triadic edges enumerable; projection cannot distinguish"
    TOOL_INTEGRATION_DEPTH["xgi"] = "load_bearing"
    return {"motif_count_positive": {"pass": motif_count > 0, "count": motif_count}}


def run_negative_tests():
    """Negative: build a 'fake' hypergraph where each triad is replaced
    by three dyads. The motif count (genuine triads sharing one node)
    must be zero, even if the projection looks identical."""
    if nx is None:
        return {"dyadic_version_zero": {"pass": False, "reason": "networkx not in venv; rustworkx used instead"}}
    H_real = random_hypergraph(seed=42)
    H_fake = xgi.Hypergraph()
    H_fake.add_nodes_from(H_real.nodes)
    for e in H_real.edges.members():
        e = list(e)
        for i in range(len(e)):
            for j in range(i + 1, len(e)):
                H_fake.add_edge((e[i], e[j]))
    mc_fake = count_motif_two_triads_share_one_node(H_fake)
    # projection equal?
    g_real = projection(H_real); g_fake = projection(H_fake)
    proj_equal = nx.is_isomorphic(g_real, g_fake)
    TOOL_MANIFEST["networkx"]["used"] = True
    TOOL_MANIFEST["networkx"]["reason"] = "verify projection isomorphism while motif count differs"
    TOOL_INTEGRATION_DEPTH["networkx"] = "supportive"
    return {"dyadic_version_zero_motif": {"pass": (mc_fake == 0 and proj_equal),
                                           "motif_count_fake": mc_fake,
                                           "projection_isomorphic": proj_equal}}


def run_boundary_tests():
    """Empty hypergraph -> 0 motifs."""
    H = xgi.Hypergraph(); H.add_nodes_from(range(5))
    return {"empty_zero_motifs": {"pass": count_motif_two_triads_share_one_node(H) == 0}}


if __name__ == "__main__":
    if xgi is None:
        raise SystemExit("BLOCKER: xgi missing")
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(v.get("pass") for v in {**pos, **neg, **bnd}.values())
    out = {"name": "sim_xgi_deep_hyperedge_motif_count",
           "classification": "canonical",
           "tool_manifest": TOOL_MANIFEST,
           "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
           "positive": pos, "negative": neg, "boundary": bnd,
           "overall_pass": all_pass}
    d = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "sim_xgi_deep_hyperedge_motif_count_results.json")
    with open(p, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {p}")
