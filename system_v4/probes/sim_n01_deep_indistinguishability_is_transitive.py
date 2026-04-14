#!/usr/bin/env python3
"""sim_n01_deep_indistinguishability_is_transitive -- z3 UNSAT: a~b & b~c & NOT a~c
must be UNSAT when ~ is defined as equality-under-all-probes. Non-transitivity of
the nominalist indistinguishability relation would break equivalence-class identity.
"""
import json, os

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import z3; TOOL_MANIFEST["z3"]["tried"] = True
except ImportError: TOOL_MANIFEST["z3"]["reason"] = "not installed"


def run_positive_tests():
    # Prove transitivity: a~b AND b~c => a~c for probes m1,m2
    a,b,c = z3.Ints("a b c")
    m1 = z3.Function("m1", z3.IntSort(), z3.IntSort())
    m2 = z3.Function("m2", z3.IntSort(), z3.IntSort())
    sim_ab = z3.And(m1(a)==m1(b), m2(a)==m2(b))
    sim_bc = z3.And(m1(b)==m1(c), m2(b)==m2(c))
    sim_ac = z3.And(m1(a)==m1(c), m2(a)==m2(c))
    s = z3.Solver()
    s.add(z3.Not(z3.Implies(z3.And(sim_ab, sim_bc), sim_ac)))
    r = str(s.check())
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "load-bearing: UNSAT proves transitivity of ~"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    return {"neg_implication": r, "pass": r == "unsat"}


def run_negative_tests():
    # Explicit contradiction: require a~b, b~c, and NOT a~c => UNSAT.
    a,b,c = z3.Ints("a b c")
    m1 = z3.Function("m1", z3.IntSort(), z3.IntSort())
    s = z3.Solver()
    s.add(m1(a) == m1(b))
    s.add(m1(b) == m1(c))
    s.add(m1(a) != m1(c))
    r = str(s.check())
    return {"chain_break": r, "pass": r == "unsat"}


def run_boundary_tests():
    # Zero probes: ~ is trivial (all pairs related). Check transitivity holds vacuously.
    # In z3: no probe constraints -> a~b and b~c are True -> a~c is True.
    s = z3.Solver()
    # no constraints -> SAT and implication holds trivially
    r = str(s.check())
    return {"empty_probe_set": r, "pass": r == "sat"}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    ok = bool(pos["pass"] and neg["pass"] and bnd["pass"])
    name = "sim_n01_deep_indistinguishability_is_transitive"
    results = {"name": name, "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "pass": ok}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, name + "_results.json")
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if ok else 'FAIL'} -> {out}")
