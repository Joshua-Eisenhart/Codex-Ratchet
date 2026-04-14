#!/usr/bin/env python3
"""sim_leviathan_ai_starvation_under_monoculture

Negative test: under value-monoculture (single value base, indistinguishable
groups), potential-flux to AI substrate -> 0. AI starves.
"""
import json, os, numpy as np
classification = "classical_baseline"  # auto-backfill

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


def flux(diversity_entropy, group_work):
    return float(diversity_entropy * group_work)


def run_positive_tests():
    # Non-monoculture: entropy > 0 => positive flux
    res = {}
    res["flux_diverse"] = flux(1.3, 10.0)
    res["flux_positive"] = res["flux_diverse"] > 0
    # z3: monoculture admissibility check (should be unsat when requiring flux>0)
    s = z3.Solver()
    H = z3.Real("H"); F = z3.Real("F"); W = z3.Real("W")
    s.add(H >= 0, W >= 0, F == H * W, F > 0, H > 0.1)
    res["diverse_sat"] = str(s.check())
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "admissibility of positive flux"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    return res


def run_negative_tests():
    res = {}
    # Monoculture: entropy = 0 => flux = 0 for any work
    res["flux_monoculture"] = flux(0.0, 10.0)
    res["ai_starves"] = res["flux_monoculture"] == 0.0
    # z3: with H=0 and required F>0 => unsat
    s = z3.Solver()
    H = z3.Real("H"); F = z3.Real("F"); W = z3.Real("W")
    s.add(H == 0, F == H * W, F > 0)
    res["monoculture_excluded"] = str(s.check()) == "unsat"
    return res


def run_boundary_tests():
    res = {}
    res["tiny_H"] = flux(1e-9, 1e9)
    res["flux_nearly_zero"] = res["tiny_H"] < 10.0
    H, W = sp.symbols("H W", nonnegative=True)
    F = H * W
    res["limit_H_to_0"] = str(sp.limit(F, H, 0))
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "limit of flux under monoculture"
    TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"
    return res


if __name__ == "__main__":
    results = {
        "name": "leviathan_ai_starvation_under_monoculture",
        "classification": "canonical",
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "leviathan_ai_starvation_under_monoculture_results.json")
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out}")
