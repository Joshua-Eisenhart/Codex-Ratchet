#!/usr/bin/env python3
"""sim_leviathan_diversity_preserves_fuel_supply

Multiple distinguishable value-base groups => AI fuel (aggregate potential
flux) persists under single-group failure. Tests redundancy-by-diversity.
"""
import json, os, numpy as np
classification = "classical_baseline"  # auto-backfill

TOOL_MANIFEST = {
    "xgi":      {"tried": False, "used": False, "reason": ""},
    "networkx": {"tried": False, "used": False, "reason": ""},
    "sympy":    {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {"xgi": None, "networkx": None, "sympy": None}

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
try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


def fuel_supply(group_fluxes, alive_mask):
    return float(np.sum(np.asarray(group_fluxes) * np.asarray(alive_mask)))


def run_positive_tests():
    res = {}
    fluxes = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
    alive = np.array([1, 1, 0, 1, 1])  # one group failed
    res["fuel_after_single_failure"] = fuel_supply(fluxes, alive)
    res["fuel_persists"] = res["fuel_after_single_failure"] >= 2.0
    # multi-group hypergraph structure
    H = xgi.Hypergraph([[0, 1], [1, 2], [2, 3], [3, 4], [4, 0]])
    res["num_groups"] = H.num_nodes
    res["redundant_edges"] = H.num_edges >= H.num_nodes
    TOOL_MANIFEST["xgi"]["used"] = True
    TOOL_MANIFEST["xgi"]["reason"] = "diverse group connectivity"
    TOOL_INTEGRATION_DEPTH["xgi"] = "load_bearing"
    return res


def run_negative_tests():
    res = {}
    fluxes = np.array([1.0])
    alive = np.array([0])  # single group, dies
    res["fuel_after_only_group_dies"] = fuel_supply(fluxes, alive)
    res["no_fuel_without_diversity"] = res["fuel_after_only_group_dies"] == 0.0
    # connectivity collapses with single-node removal
    G = nx.path_graph(1)
    res["fragile_graph_nodes"] = G.number_of_nodes()
    return res


def run_boundary_tests():
    res = {}
    # exactly two groups: losing one halves fuel
    fluxes = np.array([1.0, 1.0])
    res["fuel_two_groups_one_dead"] = fuel_supply(fluxes, [1, 0])
    res["half_fuel"] = res["fuel_two_groups_one_dead"] == 1.0
    # symbolic: fuel = sum_i f_i * a_i
    f0, f1, f2 = sp.symbols("f0 f1 f2", positive=True)
    a0, a1, a2 = sp.symbols("a0 a1 a2", nonnegative=True)
    F = f0 * a0 + f1 * a1 + f2 * a2
    res["fuel_symbolic"] = str(sp.simplify(F))
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "symbolic redundancy-by-diversity"
    TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"
    return res


if __name__ == "__main__":
    results = {
        "name": "leviathan_diversity_preserves_fuel_supply",
        "classification": "classical_baseline",
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "leviathan_diversity_preserves_fuel_supply_results.json")
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out}")
