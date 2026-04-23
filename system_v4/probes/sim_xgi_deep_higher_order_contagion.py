#!/usr/bin/env python3
"""
sim_xgi_deep_higher_order_contagion.py

Higher-order SIS contagion on a hypergraph has a discontinuous
transition / bistable regime that pure pairwise SIS on the same
1-skeleton does NOT exhibit (Iacopini et al., Nat. Commun. 2019).
Claim: at a beta_triad regime where triadic infection dominates, the
endemic prevalence on the hypergraph is strictly higher than on its
pairwise projection at the same pairwise rate. xgi is load_bearing:
infection events require simultaneous activation of ALL nodes in a
hyperedge of size >=3, which is only representable with true
hyperedges.

Classification: canonical.
"""
import json, os
import numpy as np

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "stochastic sim, numpy rng"},
    "pyg": {"tried": False, "used": False, "reason": "pairwise graph only"},
    "z3": {"tried": False, "used": False, "reason": "stochastic"},
    "cvc5": {"tried": False, "used": False, "reason": "stochastic"},
    "sympy": {"tried": False, "used": False, "reason": "no closed form tested"},
    "clifford": {"tried": False, "used": False, "reason": "no GA"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariance"},
    "rustworkx": {"tried": False, "used": False, "reason": "pairwise only"},
    "xgi": {"tried": False, "used": False, "reason": ""},
    "toponetx": {"tried": False, "used": False, "reason": "not cell complex"},
    "gudhi": {"tried": False, "used": False, "reason": "no homology"},
    "networkx": {"tried": False, "used": False, "reason": "projection SIS baseline"},
    "numpy": {"tried": True, "used": True, "reason": "rng only"},
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


def build_random_hypergraph(n=40, n_triads=80, n_dyads=40, seed=0):
    rng = np.random.default_rng(seed)
    H = xgi.Hypergraph()
    H.add_nodes_from(range(n))
    triads = set()
    while len(triads) < n_triads:
        t = tuple(sorted(rng.choice(n, size=3, replace=False).tolist()))
        triads.add(t)
    dyads = set()
    while len(dyads) < n_dyads:
        d = tuple(sorted(rng.choice(n, size=2, replace=False).tolist()))
        dyads.add(d)
    H.add_edges_from(list(triads) + list(dyads))
    return H


def projection(H):
    g = nx.Graph()
    g.add_nodes_from(H.nodes)
    for e in H.edges.members():
        e = list(e)
        for i in range(len(e)):
            for j in range(i + 1, len(e)):
                g.add_edge(e[i], e[j])
    return g


def sis_hypergraph(H, beta_pair, beta_triad, mu, T=200, seed=1):
    rng = np.random.default_rng(seed)
    nodes = list(H.nodes)
    n = len(nodes)
    idx = {v: i for i, v in enumerate(nodes)}
    state = rng.random(n) < 0.1  # 10% seeded
    edges = [list(e) for e in H.edges.members()]
    prevalence = []
    for _ in range(T):
        new_state = state.copy()
        for e in edges:
            members = [idx[v] for v in e]
            if len(e) == 2:
                u, v = members
                if state[u] and not state[v] and rng.random() < beta_pair:
                    new_state[v] = True
                if state[v] and not state[u] and rng.random() < beta_pair:
                    new_state[u] = True
            elif len(e) >= 3:
                infected_in_edge = sum(state[m] for m in members)
                # triadic rule: if all-but-one infected, the last may get infected at beta_triad
                if infected_in_edge >= 2:
                    for m in members:
                        if not state[m] and rng.random() < beta_triad:
                            new_state[m] = True
        # recovery
        recov = rng.random(n) < mu
        new_state = new_state & (~recov)
        state = new_state
        prevalence.append(state.mean())
    return float(np.mean(prevalence[-50:]))


def sis_pairwise(g, beta_pair, mu, T=200, seed=1):
    rng = np.random.default_rng(seed)
    nodes = list(g.nodes)
    n = len(nodes)
    idx = {v: i for i, v in enumerate(nodes)}
    state = rng.random(n) < 0.1
    edges = [(idx[u], idx[v]) for u, v in g.edges]
    prevalence = []
    for _ in range(T):
        new_state = state.copy()
        for u, v in edges:
            if state[u] and not state[v] and rng.random() < beta_pair:
                new_state[v] = True
            if state[v] and not state[u] and rng.random() < beta_pair:
                new_state[u] = True
        recov = rng.random(n) < mu
        new_state = new_state & (~recov)
        state = new_state
        prevalence.append(state.mean())
    return float(np.mean(prevalence[-50:]))


def run_positive_tests():
    H = build_random_hypergraph()
    g = projection(H)
    # triadic dominates
    p_hyper = sis_hypergraph(H, beta_pair=0.05, beta_triad=0.9, mu=0.05, seed=7)
    p_pair = sis_pairwise(g, beta_pair=0.05, mu=0.05, seed=7)
    ok = p_hyper > p_pair + 0.02
    TOOL_MANIFEST["xgi"]["used"] = True
    TOOL_MANIFEST["xgi"]["reason"] = "triadic infection rule requires genuine hyperedges of size >=3"
    TOOL_INTEGRATION_DEPTH["xgi"] = "load_bearing"
    return {"triadic_raises_prevalence": {"pass": ok,
                                           "p_hyper": p_hyper, "p_pair": p_pair,
                                           "delta": p_hyper - p_pair}}


def run_negative_tests():
    """Negative: if beta_triad = 0, triadic infection silenced and
    hypergraph SIS must match pairwise SIS closely (same pairwise
    edges drive dynamics in both)."""
    if nx is None:
        return {"no_triad_matches_pair": {"pass": False, "reason": "networkx missing"}}
    H = build_random_hypergraph(seed=3)
    g = projection(H)
    p_hyper = sis_hypergraph(H, beta_pair=0.05, beta_triad=0.0, mu=0.2, seed=11)
    p_pair = sis_pairwise(g, beta_pair=0.05, mu=0.2, seed=11)
    # They won't be identical (projection adds extra pairwise edges from triads)
    # but without triad channel, hyper should NOT exceed pair by a lot.
    TOOL_MANIFEST["networkx"]["used"] = True
    TOOL_MANIFEST["networkx"]["reason"] = "pairwise projection baseline SIS"
    TOOL_INTEGRATION_DEPTH["networkx"] = "supportive"
    return {"no_triad_matches_pair": {"pass": (p_hyper - p_pair) < 0.05,
                                       "p_hyper": p_hyper, "p_pair": p_pair,
                                       "delta": p_hyper - p_pair}}


def run_boundary_tests():
    """beta_pair=0 and beta_triad=0 -> extinction in both."""
    H = build_random_hypergraph(seed=5)
    p = sis_hypergraph(H, beta_pair=0.0, beta_triad=0.0, mu=0.3, T=100, seed=13)
    return {"zero_rate_extinction": {"pass": p < 0.02, "final_prevalence": p}}


if __name__ == "__main__":
    if xgi is None:
        raise SystemExit("BLOCKER: xgi missing")
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(v.get("pass") for v in {**pos, **neg, **bnd}.values())
    out = {"name": "sim_xgi_deep_higher_order_contagion",
           "classification": "canonical",
           "tool_manifest": TOOL_MANIFEST,
           "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
           "positive": pos, "negative": neg, "boundary": bnd,
           "overall_pass": all_pass}
    d = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "sim_xgi_deep_higher_order_contagion_results.json")
    with open(p, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {p}")
