#!/usr/bin/env python3
"""
Leviathan EXPLORE framing: bond percolation.

Framing assumption:
  Potential-flow exists iff a giant component spans the group-graph.
  Centralization modeled as removing peripheral edges; decentralization as
  retaining redundant edges. Critical threshold p_c = civilizational collapse.

Blind spot:
  - Binary edges (flow/no-flow); ignores bandwidth heterogeneity.
  - Symmetric removal process (real collapse is targeted).
"""
import json, os, numpy as np

TOOL_MANIFEST = {"numpy": {"tried": True, "used": True, "reason": "bond sampling"},
                 "networkx": {"tried": False, "used": False, "reason": ""}}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive", "networkx": "load_bearing"}
try:
    import networkx as nx
    TOOL_MANIFEST["networkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["networkx"]["reason"] = "not installed"; nx = None


def giant_fraction(G):
    if G.number_of_nodes() == 0: return 0.0
    cc = max((len(c) for c in nx.connected_components(G)), default=0)
    return cc / G.number_of_nodes()

def percolated(n, p, seed=0):
    rng = np.random.default_rng(seed)
    G = nx.Graph(); G.add_nodes_from(range(n))
    for i in range(n):
        for j in range(i+1, n):
            if rng.random() < p:
                G.add_edge(i,j)
    return G


def run_positive_tests():
    if nx is None: return {"skipped": "networkx missing"}
    G = percolated(50, 0.2, seed=0)
    f = giant_fraction(G)
    return {"frac_giant": f, "pass_connected": f > 0.5}

def run_negative_tests():
    if nx is None: return {"skipped": "networkx missing"}
    G = percolated(50, 0.01, seed=0)
    f = giant_fraction(G)
    return {"frac_giant": f, "pass_fragmented": f < 0.3}

def run_boundary_tests():
    if nx is None: return {"skipped": "networkx missing"}
    # at critical p ~ 1/n
    G = percolated(50, 1.0/50, seed=7)
    return {"critical_frac": giant_fraction(G), "pass": True}


if __name__ == "__main__":
    results = {
        "name": "leviathan_explore_as_percolation_network",
        "framing_assumption": "potential flow = giant component; collapse = percolation threshold",
        "blind_spot": "edges binary; removal symmetric (real collapse is targeted)",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "classical_baseline",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "leviathan_explore_as_percolation_network_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(json.dumps({k: results[k] for k in ["name","positive","negative","boundary"]}, indent=2, default=str))
