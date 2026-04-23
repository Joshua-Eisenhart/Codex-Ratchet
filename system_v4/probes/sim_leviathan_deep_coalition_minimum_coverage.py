#!/usr/bin/env python3
"""
Leviathan deep -- coalition minimum coverage (z3 load-bearing).

Scope: given a set of agents and required 'obligation' predicates, find the
minimum coalition size whose union covers all obligations. Smaller coalitions
that claim coverage are EXCLUDED by UNSAT.
"""
import json, os
from z3 import Solver, Bools, And, Or, Not, sat, unsat, If, Sum, Int, IntVal

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn",
     "rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_MANIFEST["z3"]["tried"] = True
for k in TOOL_MANIFEST:
    if not TOOL_MANIFEST[k]["tried"]:
        TOOL_MANIFEST[k]["reason"] = "not required for set-cover UNSAT bound"


# 5 agents, 4 obligations: capability matrix (agent covers obligation)
CAP = [
    [1,1,0,0],
    [0,1,1,0],
    [0,0,1,1],
    [1,0,0,1],
    [1,0,1,0],
]
N_AGENTS = 5; N_OBL = 4


def _solve_for_bound(k):
    picks = [Bools(f"a_{i}")[0] for i in range(N_AGENTS)]
    picks = [b for b in picks]
    # Redefine properly:
    picks = []
    for i in range(N_AGENTS):
        picks.append(Bools(f"p{i}")[0])
    s = Solver()
    # at most k agents
    s.add(Sum([If(p, 1, 0) for p in picks]) <= k)
    # every obligation covered
    for j in range(N_OBL):
        s.add(Or([And(picks[i], CAP[i][j] == 1) for i in range(N_AGENTS)]))
    return s.check()


def run_positive_tests():
    r = {}
    # Known minimum: coalition {0,2} covers {0,1,2,3} -> size 2 works.
    r["k2_sat"] = {"pass": _solve_for_bound(2) == sat}
    return r


def run_negative_tests():
    r = {}
    # k=1 cannot cover all 4 obligations (no agent covers all four).
    r["k1_unsat"] = {"pass": _solve_for_bound(1) == unsat}
    return r


def run_boundary_tests():
    r = {}
    # k=0 trivially UNSAT (no one covers anything).
    r["k0_unsat"] = {"pass": _solve_for_bound(0) == unsat}
    # k=N_AGENTS trivially SAT.
    r["kN_sat"] = {"pass": _solve_for_bound(N_AGENTS) == sat}
    return r


if __name__ == "__main__":
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "SAT/UNSAT bounds exclude coalition sizes"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    pos, neg, bnd = run_positive_tests(), run_negative_tests(), run_boundary_tests()
    allpass = lambda d: all(v.get("pass", False) for v in d.values())
    ap = allpass(pos) and allpass(neg) and allpass(bnd)
    res = {"name": "leviathan_deep_coalition_minimum_coverage",
           "classification": "canonical",
           "scope_note": "OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md",
           "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
           "positive": pos, "negative": neg, "boundary": bnd, "all_pass": ap}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "leviathan_deep_coalition_minimum_coverage_results.json")
    with open(out, "w") as f: json.dump(res, f, indent=2, default=str)
    print(f"[{res['name']}] all_pass={ap} -> {out}")
