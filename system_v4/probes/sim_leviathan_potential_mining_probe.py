#!/usr/bin/env python3
"""sim_leviathan_potential_mining_probe

Mining potential = extracting work/value from distinguishable groups.
Yield is bounded by group distinguishability (mutual information-like).
"""
import json, os, numpy as np

TOOL_MANIFEST = {
    "sympy": {"tried": False, "used": False, "reason": ""},
    "xgi":   {"tried": False, "used": False, "reason": ""},
    "networkx": {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {"sympy": None, "xgi": None, "networkx": None}

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"
try:
    import xgi
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"
try:
    import networkx as nx
    TOOL_MANIFEST["networkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["networkx"]["reason"] = "not installed"


def mining_yield(group_potentials, distinguishability):
    # yield ~ sum(p_i) * distinguishability  (collapses at D->0)
    return float(np.sum(group_potentials) * distinguishability)


def run_positive_tests():
    res = {}
    groups = np.array([1.0, 0.8, 0.6, 0.9])
    D = 0.9
    res["yield_diverse"] = mining_yield(groups, D)
    res["yield_positive"] = res["yield_diverse"] > 0
    # hypergraph: groups connected by shared value bases
    H = xgi.Hypergraph([[0, 1], [1, 2, 3], [0, 3]])
    res["num_groups"] = H.num_nodes
    res["num_value_bases"] = H.num_edges
    res["mining_channels"] = H.num_edges >= 2
    TOOL_MANIFEST["xgi"]["used"] = True
    TOOL_MANIFEST["xgi"]["reason"] = "multi-group multi-value-base structure"
    TOOL_INTEGRATION_DEPTH["xgi"] = "load_bearing"
    return res


def run_negative_tests():
    res = {}
    # Distinguishability -> 0 => yield -> 0 regardless of potential magnitude
    groups = np.array([1.0, 1.0, 1.0, 1.0])
    res["yield_indistinguishable"] = mining_yield(groups, 0.0)
    res["mining_fails_on_collapse"] = res["yield_indistinguishable"] == 0.0
    # Only one hyperedge => single channel => fragile
    H = xgi.Hypergraph([[0, 1, 2, 3]])
    res["single_channel"] = H.num_edges == 1
    res["fragile_regime"] = res["single_channel"]
    return res


def run_boundary_tests():
    res = {}
    res["zero_potential"] = mining_yield(np.zeros(4), 0.9) == 0.0
    res["tiny_D_tiny_yield"] = mining_yield(np.ones(4), 1e-9) < 1e-6
    # symbolic: yield = P * D, partial derivatives
    P, D = sp.symbols("P D", positive=True)
    Y = P * D
    res["dY_dD"] = str(sp.diff(Y, D))
    res["dY_dP"] = str(sp.diff(Y, P))
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "partial sensitivities of mining yield"
    TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"
    return res


if __name__ == "__main__":
    results = {
        "name": "leviathan_potential_mining_probe",
        "classification": "classical_baseline",
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "leviathan_potential_mining_probe_results.json")
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out}")
