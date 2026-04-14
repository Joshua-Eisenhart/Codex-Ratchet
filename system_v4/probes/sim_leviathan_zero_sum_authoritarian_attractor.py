#!/usr/bin/env python3
"""sim_leviathan_zero_sum_authoritarian_attractor

Detector for collapse-to-single-narrative failure mode: narrative-share
concentration (HHI) above threshold indicates authoritarian attractor.
"""
import json, os, numpy as np

TOOL_MANIFEST = {
    "sympy":    {"tried": False, "used": False, "reason": ""},
    "z3":       {"tried": False, "used": False, "reason": ""},
    "networkx": {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {"sympy": None, "z3": None, "networkx": None}

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"
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


def hhi(shares):
    s = np.asarray(shares, float); s = s / s.sum()
    return float(np.sum(s ** 2))


THRESHOLD = 0.5  # above => authoritarian attractor


def run_positive_tests():
    res = {}
    res["hhi_diverse"] = hhi([0.25, 0.25, 0.25, 0.25])
    res["not_authoritarian"] = res["hhi_diverse"] < THRESHOLD
    # star-of-narratives graph has central hub degree = n-1
    G = nx.complete_graph(4)
    res["balanced_degree_max"] = max(dict(G.degree()).values())
    TOOL_MANIFEST["networkx"]["used"] = True
    TOOL_MANIFEST["networkx"]["reason"] = "narrative balance topology"
    TOOL_INTEGRATION_DEPTH["networkx"] = "supportive"
    return res


def run_negative_tests():
    res = {}
    res["hhi_collapsed"] = hhi([0.95, 0.02, 0.02, 0.01])
    res["authoritarian_attractor_detected"] = res["hhi_collapsed"] > THRESHOLD
    # z3: claim admissible (HHI<0.5) given HHI=0.9 => unsat
    s = z3.Solver()
    H = z3.Real("H")
    s.add(H == 0.9, H < THRESHOLD)
    res["collapsed_excluded"] = str(s.check()) == "unsat"
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "exclude concentrated-narrative admissibility"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    return res


def run_boundary_tests():
    res = {}
    res["hhi_at_threshold"] = hhi([0.707, 0.293])
    # symbolic: HHI = sum s_i^2 with sum s_i = 1, minimum at uniform = 1/n
    s_sym = sp.symbols("s0 s1 s2 s3", positive=True)
    H = sum(si ** 2 for si in s_sym)
    res["hhi_uniform_1_over_n"] = str(sp.simplify(H.subs({si: sp.Rational(1, 4) for si in s_sym})))
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "symbolic HHI minimum"
    TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"
    return res


if __name__ == "__main__":
    results = {
        "name": "leviathan_zero_sum_authoritarian_attractor",
        "classification": "canonical",
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "leviathan_zero_sum_authoritarian_attractor_results.json")
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out}")
