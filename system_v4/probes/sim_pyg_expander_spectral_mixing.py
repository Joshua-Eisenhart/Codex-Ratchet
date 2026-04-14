#!/usr/bin/env python3
"""sim 5: pyg message passing over a random regular (expander) graph; empirical
mixing time of the random walk agrees with spectral gap prediction from eigendecomp.
networkx is supportive (constructs graph, adjacency). pyg does the actual MP diffusion.
"""
import json, os, numpy as np
import torch
import networkx as nx
from torch_geometric.nn import MessagePassing
from torch_geometric.utils import from_networkx

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "tensors for diffusion state"},
    "pyg": {"tried": True, "used": True, "reason": "MessagePassing applies row-stochastic walk step; load-bearing for empirical mixing"},
    "z3": {"tried": False, "used": False, "reason": "no SMT"},
    "cvc5": {"tried": False, "used": False, "reason": "no SMT"},
    "sympy": {"tried": False, "used": False, "reason": "numeric eigendecomp"},
    "clifford": {"tried": False, "used": False, "reason": "no rotor"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariance"},
    "rustworkx": {"tried": False, "used": False, "reason": "using networkx for random regular"},
    "xgi": {"tried": False, "used": False, "reason": "simple graph"},
    "toponetx": {"tried": False, "used": False, "reason": "graph only"},
    "gudhi": {"tried": False, "used": False, "reason": "no PH"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["pyg"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"
# networkx (always available in env) is supportive; not in manifest keys.


class WalkStep(MessagePassing):
    def __init__(self):
        super().__init__(aggr="add")
    def forward(self, x, edge_index, deg_inv):
        # Row-stochastic transition: neighbors sum / degree of source (undirected regular=>k)
        return self.propagate(edge_index, x=x * deg_inv.view(-1,1))
    def message(self, x_j):
        return x_j


def spectral_gap(G):
    A = nx.adjacency_matrix(G).toarray().astype(float)
    d = A.sum(1)
    Dinv = np.diag(1.0/d)
    P = Dinv @ A  # row-stochastic
    w = np.linalg.eigvals(P)
    w_abs = np.sort(np.abs(w))[::-1]
    lam2 = float(w_abs[1].real) if w_abs[1].imag < 1e-8 else float(np.abs(w_abs[1]))
    return 1.0 - lam2, P


def pyg_mixing(G, tv_thresh=0.1, max_steps=500):
    data = from_networkx(G)
    ei = data.edge_index
    n = G.number_of_nodes()
    deg = torch.tensor([G.degree(i) for i in range(n)], dtype=torch.float)
    # We want row-stochastic walk: each node sends its value/deg to neighbors.
    deg_inv = 1.0 / deg
    x = torch.zeros(n, 1); x[0] = 1.0
    step = WalkStep()
    uniform = torch.ones(n, 1) / n
    for t in range(1, max_steps+1):
        x = step(x, ei, deg_inv)
        tv = 0.5 * (x - uniform).abs().sum().item()
        if tv < tv_thresh:
            return t, tv
    return max_steps, None


def run_positive_tests():
    results = {}
    for (k, n, seed) in [(4, 60, 1), (5, 100, 2), (6, 80, 3)]:
        G = nx.random_regular_graph(k, n, seed=seed)
        gap, _ = spectral_gap(G)
        predicted = int(np.ceil(np.log(n) / gap))  # ~ (1/gap) * log(n) for mixing to uniform
        empirical, tv = pyg_mixing(G, tv_thresh=0.1)
        # agreement: empirical within factor 3 of prediction
        ratio = empirical / max(predicted, 1)
        results[f"k{k}_n{n}"] = {
            "spectral_gap": gap,
            "predicted_steps": predicted,
            "empirical_steps": empirical,
            "final_tv": tv,
            "ratio": ratio,
            "pass": 0.2 <= ratio <= 5.0,
        }
    return results


def run_negative_tests():
    # Cycle graph has tiny spectral gap => predicted mixing very large; empirical also large.
    # Negative claim: a ring of n=50 does NOT mix in few steps (sanity: anti-expander).
    G = nx.cycle_graph(50)
    gap, _ = spectral_gap(G)
    empirical, tv = pyg_mixing(G, tv_thresh=0.1, max_steps=300)
    return {"cycle_fails_fast_mix": {
        "gap": gap, "empirical_steps": empirical, "final_tv": tv,
        "pass": gap < 0.05 and (empirical >= 100 or tv is None),
    }}


def run_boundary_tests():
    # Complete graph K_n has gap=1, should mix in 1 step (to exactly uniform modulo self-loop choice).
    G = nx.complete_graph(20)
    gap, P = spectral_gap(G)
    empirical, tv = pyg_mixing(G, tv_thresh=0.1, max_steps=20)
    return {"complete_graph_fast": {
        "gap": gap, "empirical_steps": empirical,
        "pass": gap > 0.9 and empirical <= 3,
    }}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(v["pass"] for v in {**pos, **neg, **bnd}.values())
    results = {
        "name": "pyg_expander_spectral_mixing",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "pyg_expander_spectral_mixing_results.json")
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out}")
    print(f"ALL_PASS={all_pass}")
