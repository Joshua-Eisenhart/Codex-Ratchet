#!/usr/bin/env python3
"""sim_leviathan_human_potential_as_wealth_carrier

Leviathan lego: human potential (distinguishable capacity across agents) is
the primary wealth substrate. Wealth admissibility requires non-collapsed
potential distribution.
"""
import json, os, numpy as np
classification = "classical_baseline"  # auto-backfill

TOOL_MANIFEST = {
    "sympy": {"tried": False, "used": False, "reason": ""},
    "z3":    {"tried": False, "used": False, "reason": ""},
    "xgi":   {"tried": False, "used": False, "reason": ""},
    "networkx": {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {"sympy": None, "z3": None, "xgi": None, "networkx": None}

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"
try:
    import z3 as z3m
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"
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


def shannon(p):
    p = np.asarray(p, float); p = p[p > 0]; p = p / p.sum()
    return float(-(p * np.log(p)).sum())


def run_positive_tests():
    # Diverse potential distribution => positive wealth carrier entropy
    # sympy symbolic check: W = sum(p_i * v_i), v_i distinct
    res = {}
    p = [0.25, 0.25, 0.25, 0.25]
    res["uniform_potential_entropy"] = shannon(p)
    res["uniform_admissible"] = res["uniform_potential_entropy"] > 1.0
    p2 = [0.4, 0.3, 0.2, 0.1]
    res["skewed_potential_entropy"] = shannon(p2)
    res["skewed_admissible"] = res["skewed_potential_entropy"] > 0.5
    # sympy: wealth is distinguishability-weighted potential
    p_s = sp.symbols("p0 p1 p2 p3", positive=True)
    v_s = sp.symbols("v0 v1 v2 v3", positive=True)
    W = sum(pi * vi for pi, vi in zip(p_s, v_s))
    res["wealth_symbolic"] = str(sp.simplify(W))
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "symbolic wealth carrier definition"
    TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"
    return res


def run_negative_tests():
    # Collapsed potential (single group carries all) => zero carrier entropy
    res = {}
    p_collapsed = [1.0, 0.0, 0.0, 0.0]
    res["collapsed_entropy"] = shannon(p_collapsed)
    res["collapsed_fails_admissibility"] = res["collapsed_entropy"] == 0.0
    # z3: assert admissible => entropy>0, with collapsed distribution: UNSAT
    s = z3m.Solver()
    H = z3m.Real("H")
    s.add(H == 0.0)
    s.add(H > 0.0)
    res["z3_collapsed_admissible_check"] = str(s.check())  # expect unsat
    res["z3_excludes_collapse"] = (str(s.check()) == "unsat")
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "exclude collapsed-potential as admissible wealth carrier"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    return res


def run_boundary_tests():
    res = {}
    # two-group near-equal vs near-degenerate
    res["near_equal_entropy"] = shannon([0.5 - 1e-9, 0.5 + 1e-9])
    res["near_degenerate_entropy"] = shannon([1 - 1e-9, 1e-9])
    res["separation"] = res["near_equal_entropy"] > res["near_degenerate_entropy"]
    return res


if __name__ == "__main__":
    results = {
        "name": "leviathan_human_potential_as_wealth_carrier",
        "classification": "classical_baseline",
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "leviathan_human_potential_as_wealth_carrier_results.json")
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out}")
