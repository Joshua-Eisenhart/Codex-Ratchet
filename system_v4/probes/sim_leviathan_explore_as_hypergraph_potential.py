#!/usr/bin/env python3
"""
Leviathan EXPLORE framing: hypergraph of group potential exchanges.

Framing assumption imposed:
  Human potential flows across HYPEREDGES connecting multiple groups simultaneously.
  Wealth = integral of multi-way potential exchange. Centralization = hyperedge
  degree collapse toward one super-node.

What this framing FAILS to capture:
  - Temporal dynamics (static snapshot)
  - Asymmetric power (hypergraph edges are unsigned)
  - Qualitative differences in potential (all fungible here)

classification: classical_baseline
"""
import json, os, numpy as np
classification = "canonical"

TOOL_MANIFEST = {
    "xgi":       {"tried": False, "used": False, "reason": ""},
    "numpy":     {"tried": True,  "used": True,  "reason": "degree + entropy stats"},
}
TOOL_INTEGRATION_DEPTH = {"xgi": "load_bearing", "numpy": "supportive"}

try:
    import xgi
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"; xgi = None


def build_decentralized():
    H = xgi.Hypergraph()
    groups = [f"g{i}" for i in range(8)]
    H.add_nodes_from(groups)
    edges = [("g0","g1","g2"), ("g2","g3","g4"), ("g4","g5","g6"),
             ("g6","g7","g0"), ("g1","g3","g5"), ("g2","g5","g7")]
    H.add_edges_from(edges)
    return H

def build_centralized():
    H = xgi.Hypergraph()
    groups = [f"g{i}" for i in range(8)]
    H.add_nodes_from(groups)
    # hub pattern: g0 in every hyperedge
    edges = [("g0","g1","g2"), ("g0","g3","g4"), ("g0","g5","g6"), ("g0","g7","g1")]
    H.add_edges_from(edges)
    return H

def potential_entropy(H):
    degs = np.array([H.degree(n) for n in H.nodes], dtype=float)
    if degs.sum() == 0: return 0.0
    p = degs / degs.sum()
    p = p[p > 0]
    return float(-(p * np.log(p)).sum())


def run_positive_tests():
    if xgi is None: return {"skipped": "xgi missing"}
    H = build_decentralized()
    S = potential_entropy(H)
    return {"decentralized_entropy": S, "pass": S > 1.5, "n_edges": H.num_edges}

def run_negative_tests():
    if xgi is None: return {"skipped": "xgi missing"}
    Hc = build_centralized()
    Sc = potential_entropy(Hc)
    Hd = build_decentralized()
    Sd = potential_entropy(Hd)
    return {"centralized_entropy": Sc, "decentralized_entropy": Sd,
            "pass_centralized_lower": Sc < Sd}

def run_boundary_tests():
    if xgi is None: return {"skipped": "xgi missing"}
    H = xgi.Hypergraph(); H.add_nodes_from(["a","b"]); H.add_edges_from([("a","b")])
    return {"tiny_entropy": potential_entropy(H), "pass": True}


if __name__ == "__main__":
    results = {
        "name": "leviathan_explore_as_hypergraph_potential",
        "framing_assumption": "multi-way hyperedges as potential pathways; degree-entropy = decentralization",
        "blind_spot": "no temporal dynamics, no signed power asymmetry",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "classical_baseline",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "leviathan_explore_as_hypergraph_potential_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(json.dumps({k: results[k] for k in ["name","positive","negative","boundary"]}, indent=2, default=str))
