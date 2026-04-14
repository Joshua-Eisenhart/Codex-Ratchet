#!/usr/bin/env python3
"""bridge_ladder_L11_placement_z3 -- canonical bridge: z3 (load_bearing) proves
ladder placement admissibility/exclusion for an L11 placement problem.
Uses SAT for positive (placement exists) and UNSAT for negative (forbidden
configuration structurally impossible).

scope_note: system_v5/new docs/LADDERS_FENCES_ADMISSION_REFERENCE.md L11
placement; CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md structural admissibility.
"""
from z3 import Solver, Int, And, Or, Distinct, sat, unsat, Not
from _doc_illum_common import build_manifest, write_results

TOOL_MANIFEST, TOOL_INTEGRATION_DEPTH = build_manifest()
TOOL_MANIFEST["z3"] = {"tried": True, "used": True, "reason": "SAT/UNSAT placement proof"}
TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"


def placement_solver(n=4, forbid_adjacent=True):
    s = Solver()
    xs = [Int(f"x_{i}") for i in range(n)]
    for x in xs:
        s.add(And(x >= 0, x < n))
    s.add(Distinct(xs))
    if forbid_adjacent:
        for i in range(n - 1):
            s.add(xs[i + 1] - xs[i] != 1)
            s.add(xs[i + 1] - xs[i] != -1)
    return s, xs


def run_positive_tests():
    r = {}
    # Satisfiable with no adjacency constraint
    s, _ = placement_solver(n=4, forbid_adjacent=False)
    r["basic_placement_sat"] = {"pass": s.check() == sat}
    # Satisfiable with adjacency constraint on n=4 (e.g. 1,3,0,2)
    s2, _ = placement_solver(n=4, forbid_adjacent=True)
    r["adjacent_forbidden_still_sat"] = {"pass": s2.check() == sat}
    return r


def run_negative_tests():
    r = {}
    # n=2 with forbid_adjacent is UNSAT (only {0,1} or {1,0}, both adjacent)
    s, _ = placement_solver(n=2, forbid_adjacent=True)
    r["n2_forbidden_unsat"] = {"pass": s.check() == unsat}
    return r


def run_boundary_tests():
    r = {}
    # n=1: trivially sat
    s, _ = placement_solver(n=1, forbid_adjacent=True)
    r["n1_trivial_sat"] = {"pass": s.check() == sat}
    return r


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    allp = all(v["pass"] for v in {**pos, **neg, **bnd}.values())
    results = {
        "name": "bridge_ladder_L11_placement_z3",
        "classification": "canonical",
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md L11; CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md admissibility",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "pass": allp,
    }
    write_results("bridge_ladder_L11_placement_z3", results)
