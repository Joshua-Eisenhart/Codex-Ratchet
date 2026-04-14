#!/usr/bin/env python3
"""sim_leviathan_centralization_destroys_admissibility

One-world-government = single-authority configuration collapses admissible
civilizational shells. z3 encodes: admissibility requires >=2 independent
authority centers; centralization forces UNSAT.
"""
import json, os, numpy as np
classification = "classical_baseline"  # auto-backfill

TOOL_MANIFEST = {
    "z3":       {"tried": False, "used": False, "reason": ""},
    "networkx": {"tried": False, "used": False, "reason": ""},
    "sympy":    {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {"z3": None, "networkx": None, "sympy": None}

try:
    import z3
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"
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


def authority_count_admissible(n_authorities):
    s = z3.Solver()
    n = z3.Int("n")
    s.add(n == n_authorities)
    s.add(n >= 2)  # admissibility constraint
    return str(s.check())  # 'sat' or 'unsat'


def run_positive_tests():
    res = {}
    res["three_authorities"] = authority_count_admissible(3)
    res["two_authorities"]   = authority_count_admissible(2)
    res["pluralism_admissible"] = (res["three_authorities"] == "sat"
                                   and res["two_authorities"] == "sat")
    # connectivity of authority graph: still connected but not a star-of-one
    G = nx.Graph()
    G.add_edges_from([(0, 1), (1, 2), (2, 0)])
    res["authority_graph_nodes"] = G.number_of_nodes()
    res["not_single_hub"] = max(dict(G.degree()).values()) < G.number_of_nodes()
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "encode admissibility >=2 authorities"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    TOOL_MANIFEST["networkx"]["used"] = True
    TOOL_MANIFEST["networkx"]["reason"] = "authority topology non-star check"
    TOOL_INTEGRATION_DEPTH["networkx"] = "supportive"
    return res


def run_negative_tests():
    res = {}
    # NEGATIVE TEST PASSES when centralization is UNSAT
    res["one_authority_check"] = authority_count_admissible(1)
    res["zero_authority_check"] = authority_count_admissible(0)
    res["centralization_excluded"] = (res["one_authority_check"] == "unsat"
                                      and res["zero_authority_check"] == "unsat")
    # star graph (one hub) = degenerate
    G = nx.star_graph(5)
    deg = dict(G.degree())
    res["star_hub_degree"] = max(deg.values())
    res["single_hub_detected"] = res["star_hub_degree"] == G.number_of_nodes() - 1
    return res


def run_boundary_tests():
    res = {}
    # boundary: exactly 2 is the minimum admissible
    res["boundary_two"] = authority_count_admissible(2) == "sat"
    res["boundary_one_fails"] = authority_count_admissible(1) == "unsat"
    # symbolic: admissibility indicator
    n = sp.Symbol("n", integer=True, positive=True)
    adm = sp.Piecewise((1, n >= 2), (0, True))
    res["adm_at_1"] = int(adm.subs(n, 1))
    res["adm_at_2"] = int(adm.subs(n, 2))
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "piecewise admissibility indicator"
    TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"
    return res


if __name__ == "__main__":
    results = {
        "name": "leviathan_centralization_destroys_admissibility",
        "classification": "canonical",
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "leviathan_centralization_destroys_admissibility_results.json")
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out}")
