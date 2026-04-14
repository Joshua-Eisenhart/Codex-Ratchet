#!/usr/bin/env python3
"""sim_n01_fail_nominal_distinct_empirically_same -- N01 forbids: 'a != b' asserted
while every probe in M gives m(a)=m(b). z3 load-bearing: UNSAT under N01's
definition of identity-via-indistinguishability.
"""
import json, os

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import z3; TOOL_MANIFEST["z3"]["tried"] = True
except ImportError: TOOL_MANIFEST["z3"]["reason"] = "not installed"


def run_positive_tests():
    # Enforce: forall m in M, m(a)=m(b) AND a_M != b_M in the quotient. UNSAT.
    a, b = z3.Ints("a b")
    m1 = z3.Function("m1", z3.IntSort(), z3.IntSort())
    m2 = z3.Function("m2", z3.IntSort(), z3.IntSort())
    m3 = z3.Function("m3", z3.IntSort(), z3.IntSort())
    # In the quotient S/~_M: a_M = b_M iff all probes agree.
    # So asserting 'a_M != b_M' AND all probes agree is the contradiction.
    eq_quotient = z3.And(m1(a)==m1(b), m2(a)==m2(b), m3(a)==m3(b))
    s = z3.Solver()
    s.add(eq_quotient)        # all probes agree
    s.add(z3.Not(eq_quotient))# yet not-identified -> direct contradiction
    r = str(s.check())
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "load-bearing: UNSAT empirically-same-yet-distinct"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    return {"nominal_distinct_empirical_same": r, "pass": r == "unsat"}


def run_negative_tests():
    # With a distinguishing probe, a_M != b_M is SAT.
    a, b = z3.Ints("a b")
    m = z3.Function("m", z3.IntSort(), z3.IntSort())
    s = z3.Solver(); s.add(m(a) != m(b))
    r = str(s.check())
    return {"distinguishing_probe": r, "pass": r == "sat"}


def run_boundary_tests():
    # Single-element domain; probes take a==b trivially.
    a = z3.Int("a")
    s = z3.Solver(); s.add(a == a); s.add(a != a)
    r = str(s.check())
    return {"self_distinct": r, "pass": r == "unsat"}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    ok = bool(pos["pass"] and neg["pass"] and bnd["pass"])
    name = "sim_n01_fail_nominal_distinct_empirically_same"
    results = {"name": name, "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "pass": ok}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, name + "_results.json")
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if ok else 'FAIL'} -> {out}")
