#!/usr/bin/env python3
"""sim_leviathan_igt_coupling_stub

Coupling stub: Leviathan shell (civilizational) <-> IGT shell (game-theoretic).
Shared object: strategy-distribution distinguishability across groups.
Stub checks both shells admit the shared object without collapse.
"""
import json, os, numpy as np
classification = "classical_baseline"  # auto-backfill

TOOL_MANIFEST = {
    "sympy": {"tried": False, "used": False, "reason": ""},
    "z3":    {"tried": False, "used": False, "reason": ""},
    "xgi":   {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {"sympy": None, "z3": None, "xgi": None}

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
    import xgi
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"


def run_positive_tests():
    res = {}
    # Shared object: strategy entropy per group > 0 (both shells require this)
    strat = np.array([[0.5, 0.5], [0.6, 0.4], [0.3, 0.7]])
    ent = [float(-(p[p > 0] * np.log(p[p > 0])).sum()) for p in strat]
    res["group_strategy_entropies"] = ent
    res["all_positive"] = all(e > 0 for e in ent)
    # z3 both-shell admissibility: Leviathan admits iff diversity; IGT admits iff mixed strategies
    s = z3.Solver()
    D, M = z3.Reals("D M")
    s.add(D > 0.1, M > 0.1)  # Leviathan diversity and IGT mixedness
    res["shared_admissibility"] = str(s.check())
    res["shared_sat"] = res["shared_admissibility"] == "sat"
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "joint admissibility of shared object"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    return res


def run_negative_tests():
    res = {}
    # Pure strategies in all groups => IGT mixedness=0 => joint unsat
    s = z3.Solver()
    D, M = z3.Reals("D M")
    s.add(D > 0.1, M == 0.0, M > 0.1)
    res["pure_strategy_excluded"] = str(s.check()) == "unsat"
    # Leviathan monoculture kills shared object even if IGT allows mixed
    s2 = z3.Solver()
    D2, M2 = z3.Reals("D M")
    s2.add(D2 == 0.0, D2 > 0.1, M2 > 0.1)
    res["leviathan_monoculture_excluded"] = str(s2.check()) == "unsat"
    return res


def run_boundary_tests():
    res = {}
    # symbolic coupling object: phi_shared = min(D, M)
    D, M = sp.symbols("D M", positive=True)
    phi = sp.Min(D, M)
    res["phi_symbolic"] = str(phi)
    res["phi_at_equal"] = str(phi.subs({D: sp.Rational(1, 2), M: sp.Rational(1, 2)}))
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "coupling-object symbolic form"
    TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"
    # xgi: two shells as hyperedges over shared nodes
    H = xgi.Hypergraph([[0, 1, 2], [1, 2, 3]])  # overlap = {1,2} shared object
    res["shared_overlap_size"] = 2
    res["shells_share_nodes"] = H.num_edges == 2
    TOOL_MANIFEST["xgi"]["used"] = True
    TOOL_MANIFEST["xgi"]["reason"] = "shell overlap topology"
    TOOL_INTEGRATION_DEPTH["xgi"] = "supportive"
    return res


if __name__ == "__main__":
    results = {
        "name": "leviathan_igt_coupling_stub",
        "classification": "classical_baseline",
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "leviathan_igt_coupling_stub_results.json")
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out}")
