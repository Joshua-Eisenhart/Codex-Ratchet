#!/usr/bin/env python3
"""sim_leviathan_legacy_durability_under_civilizational_reset

Pattern-durability: civilizational collapse/rebirth. Legacy pattern
(group-value distinguishability signature) survives reset if >=k groups
preserve their value base across the reset boundary.
"""
import json, os, numpy as np

TOOL_MANIFEST = {
    "z3":       {"tried": False, "used": False, "reason": ""},
    "sympy":    {"tried": False, "used": False, "reason": ""},
    "networkx": {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {"z3": None, "sympy": None, "networkx": None}

try:
    import z3
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"
try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"
try:
    import networkx as nx
    TOOL_MANIFEST["networkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["networkx"]["reason"] = "not installed"


K_SURVIVE = 2  # minimum surviving groups to preserve pattern


def run_positive_tests():
    res = {}
    pre  = {0: "A", 1: "B", 2: "C", 3: "D"}
    post = {0: "A", 1: "B", 2: "X", 3: "Y"}  # 2 groups kept base
    survivors = sum(1 for k in pre if pre[k] == post.get(k))
    res["survivors"] = survivors
    res["pattern_survived"] = survivors >= K_SURVIVE
    # z3: admissibility requires survivors >= k
    s = z3.Solver()
    n = z3.Int("survivors")
    s.add(n == survivors, n >= K_SURVIVE)
    res["z3_survived"] = str(s.check())
    res["admissible_sat"] = res["z3_survived"] == "sat"
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "encode >=k survivors admissibility"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    return res


def run_negative_tests():
    res = {}
    pre  = {0: "A", 1: "B", 2: "C", 3: "D"}
    post = {0: "X", 1: "Y", 2: "X", 3: "Y"}  # none preserved
    survivors = sum(1 for k in pre if pre[k] == post.get(k))
    res["survivors"] = survivors
    s = z3.Solver()
    n = z3.Int("survivors")
    s.add(n == survivors, n >= K_SURVIVE)
    res["reset_wipes_pattern"] = str(s.check()) == "unsat"
    # networkx: pre/post graphs sharing no labeled edges
    G1 = nx.Graph(); G1.add_edges_from([("A", "B"), ("C", "D")])
    G2 = nx.Graph(); G2.add_edges_from([("X", "Y")])
    shared = set(G1.edges()) & set(G2.edges())
    res["shared_edges"] = len(shared)
    res["no_shared_structure"] = len(shared) == 0
    TOOL_MANIFEST["networkx"]["used"] = True
    TOOL_MANIFEST["networkx"]["reason"] = "pre/post structural overlap"
    TOOL_INTEGRATION_DEPTH["networkx"] = "supportive"
    return res


def run_boundary_tests():
    res = {}
    # Exactly k survivors: minimum admissible
    pre  = {0: "A", 1: "B", 2: "C"}
    post = {0: "A", 1: "B", 2: "Z"}
    survivors = sum(1 for k in pre if pre[k] == post.get(k))
    res["boundary_survivors"] = survivors
    res["boundary_admissible"] = survivors == K_SURVIVE
    # symbolic durability score
    s_sym, k = sp.symbols("s k", integer=True, nonnegative=True)
    dur = sp.Piecewise((1, s_sym >= k), (0, True))
    res["durability_at_boundary"] = int(dur.subs({s_sym: 2, k: 2}))
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "symbolic durability piecewise"
    TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"
    return res


if __name__ == "__main__":
    results = {
        "name": "leviathan_legacy_durability_under_civilizational_reset",
        "classification": "canonical",
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "leviathan_legacy_durability_under_civilizational_reset_results.json")
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out}")
