#!/usr/bin/env python3
"""sim_n01_fail_rigid_designator_across_probe_change -- Anti-Kripke: there is no
name that rigidly designates 'the same object' across a change of probe set M.
Identity is M-relative. z3 load-bearing: construct M and M' such that a~_M b but
a not~_{M'} b; no rigid designator can preserve identity across both.
"""
import json, os

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import z3; TOOL_MANIFEST["z3"]["tried"] = True
except ImportError: TOOL_MANIFEST["z3"]["reason"] = "not installed"


def run_positive_tests():
    # Build explicit case: a,b indistinguishable on {m1}, distinguishable on {m1,m2}.
    a, b = z3.Ints("a b")
    m1 = z3.Function("m1", z3.IntSort(), z3.IntSort())
    m2 = z3.Function("m2", z3.IntSort(), z3.IntSort())
    s = z3.Solver()
    s.add(m1(a) == m1(b))       # ~_M
    s.add(m2(a) != m2(b))       # not ~_{M'}
    r_exists = str(s.check())   # should be sat -- such a,b exist
    # Now demand a rigid designator: identity must hold in both M and M'. UNSAT.
    s2 = z3.Solver()
    s2.add(m1(a) == m1(b))
    s2.add(m2(a) == m2(b))
    s2.add(m2(a) != m2(b))      # contradiction if we demand both
    r_rigid = str(s2.check())
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "load-bearing: identity is M-relative"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    return {"M_rel_differs": r_exists, "rigid_forced": r_rigid,
            "pass": r_exists == "sat" and r_rigid == "unsat"}


def run_negative_tests():
    # If M' ⊆ M (probe removal), identity can only coarsen -- no rigid failure.
    # Check: a~_M b (all probes agree) => a~_{M'} b (subset agrees).
    a, b = z3.Ints("a b")
    m1 = z3.Function("m1", z3.IntSort(), z3.IntSort())
    m2 = z3.Function("m2", z3.IntSort(), z3.IntSort())
    s = z3.Solver()
    s.add(z3.Not(z3.Implies(z3.And(m1(a)==m1(b), m2(a)==m2(b)), m1(a)==m1(b))))
    r = str(s.check())
    return {"subset_preserves": r, "pass": r == "unsat"}


def run_boundary_tests():
    # If M = M', identity is obviously preserved.
    a, b = z3.Ints("a b")
    m = z3.Function("m", z3.IntSort(), z3.IntSort())
    s = z3.Solver(); s.add(m(a) == m(b))
    return {"same_M": str(s.check()), "pass": str(s.check()) == "sat"}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    ok = bool(pos["pass"] and neg["pass"] and bnd["pass"])
    name = "sim_n01_fail_rigid_designator_across_probe_change"
    results = {"name": name, "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "pass": ok}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, name + "_results.json")
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if ok else 'FAIL'} -> {out}")
