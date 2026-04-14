#!/usr/bin/env python3
"""
sim_cvc5_deep_z3_cvc5_agreement.py

Cross-solver agreement sim. Same formula posed to both cvc5 and z3;
both MUST return UNSAT. Any disagreement is flagged as a solver-bug
signal rather than a verdict we trust.

Formula: Pigeonhole-3-into-2. Integers p1,p2,p3 in {1,2}, require all
three distinct pairwise. That is UNSAT in both solvers.
Negative: 3 pigeons into 3 holes distinct is SAT in both.
Boundary: same formula with unit clause p1=1 added still UNSAT.

Classification: canonical. Both solvers load-bearing (agreement itself
is the evidence; a single verdict would not suffice).
"""
import json, os

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not a numeric claim"},
    "pyg":     {"tried": False, "used": False, "reason": "no graph"},
    "z3":      {"tried": False, "used": False, "reason": ""},
    "cvc5":    {"tried": False, "used": False, "reason": ""},
    "sympy":   {"tried": False, "used": False, "reason": "not symbolic algebra"},
    "clifford":{"tried": False, "used": False, "reason": "no GA"},
    "geomstats":{"tried": False, "used": False, "reason": "no manifold"},
    "e3nn":    {"tried": False, "used": False, "reason": "no equivariance"},
    "rustworkx":{"tried": False, "used": False, "reason": "no graph search"},
    "xgi":     {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx":{"tried": False, "used": False, "reason": "no complex"},
    "gudhi":   {"tried": False, "used": False, "reason": "no persistence"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import cvc5
    from cvc5 import Kind
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    cvc5 = None
try:
    import z3 as z3mod
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    z3mod = None


def cvc5_pigeon_3in2_unsat():
    tm = cvc5.TermManager(); s = cvc5.Solver(tm)
    s.setLogic("QF_LIA")
    Int = tm.getIntegerSort()
    ps = [tm.mkConst(Int, f"p{i}") for i in range(3)]
    one = tm.mkInteger(1); two = tm.mkInteger(2)
    for p in ps:
        s.assertFormula(tm.mkTerm(Kind.OR,
            tm.mkTerm(Kind.EQUAL, p, one),
            tm.mkTerm(Kind.EQUAL, p, two)))
    # pairwise distinct
    for i in range(3):
        for j in range(i+1, 3):
            s.assertFormula(tm.mkTerm(Kind.NOT,
                tm.mkTerm(Kind.EQUAL, ps[i], ps[j])))
    r = s.checkSat()
    return r.isUnsat(), str(r)


def z3_pigeon_3in2_unsat():
    ps = [z3mod.Int(f"p{i}") for i in range(3)]
    s = z3mod.Solver()
    for p in ps:
        s.add(z3mod.Or(p == 1, p == 2))
    for i in range(3):
        for j in range(i+1, 3):
            s.add(ps[i] != ps[j])
    return s.check() == z3mod.unsat, str(s.check())


def cvc5_pigeon_3in3_sat():
    tm = cvc5.TermManager(); s = cvc5.Solver(tm)
    s.setLogic("QF_LIA")
    Int = tm.getIntegerSort()
    ps = [tm.mkConst(Int, f"p{i}") for i in range(3)]
    for p in ps:
        s.assertFormula(tm.mkTerm(Kind.OR,
            tm.mkTerm(Kind.EQUAL, p, tm.mkInteger(1)),
            tm.mkTerm(Kind.OR,
                tm.mkTerm(Kind.EQUAL, p, tm.mkInteger(2)),
                tm.mkTerm(Kind.EQUAL, p, tm.mkInteger(3)))))
    for i in range(3):
        for j in range(i+1, 3):
            s.assertFormula(tm.mkTerm(Kind.NOT,
                tm.mkTerm(Kind.EQUAL, ps[i], ps[j])))
    r = s.checkSat()
    return r.isSat(), str(r)


def z3_pigeon_3in3_sat():
    ps = [z3mod.Int(f"p{i}") for i in range(3)]
    s = z3mod.Solver()
    for p in ps:
        s.add(z3mod.Or(p == 1, p == 2, p == 3))
    for i in range(3):
        for j in range(i+1, 3):
            s.add(ps[i] != ps[j])
    return s.check() == z3mod.sat, str(s.check())


def cvc5_pigeon_3in2_p1eq1_unsat():
    tm = cvc5.TermManager(); s = cvc5.Solver(tm)
    s.setLogic("QF_LIA")
    Int = tm.getIntegerSort()
    ps = [tm.mkConst(Int, f"p{i}") for i in range(3)]
    one = tm.mkInteger(1); two = tm.mkInteger(2)
    for p in ps:
        s.assertFormula(tm.mkTerm(Kind.OR,
            tm.mkTerm(Kind.EQUAL, p, one),
            tm.mkTerm(Kind.EQUAL, p, two)))
    for i in range(3):
        for j in range(i+1, 3):
            s.assertFormula(tm.mkTerm(Kind.NOT,
                tm.mkTerm(Kind.EQUAL, ps[i], ps[j])))
    s.assertFormula(tm.mkTerm(Kind.EQUAL, ps[0], one))
    r = s.checkSat()
    return r.isUnsat(), str(r)


def z3_pigeon_3in2_p1eq1_unsat():
    ps = [z3mod.Int(f"p{i}") for i in range(3)]
    s = z3mod.Solver()
    for p in ps:
        s.add(z3mod.Or(p == 1, p == 2))
    for i in range(3):
        for j in range(i+1, 3):
            s.add(ps[i] != ps[j])
    s.add(ps[0] == 1)
    return s.check() == z3mod.unsat, str(s.check())


def run_positive_tests():
    okC, vC = cvc5_pigeon_3in2_unsat()
    okZ, vZ = z3_pigeon_3in2_unsat()
    TOOL_MANIFEST["cvc5"]["used"] = True
    TOOL_MANIFEST["cvc5"]["reason"] = "cvc5 UNSAT on pigeonhole; agreement with z3 IS the evidence"
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "z3 UNSAT on pigeonhole; agreement with cvc5 IS the evidence"
    TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    agree = okC and okZ
    return {"agreement_unsat": {"pass": agree,
                                "cvc5": vC, "z3": vZ}}

def run_negative_tests():
    okC, vC = cvc5_pigeon_3in3_sat()
    okZ, vZ = z3_pigeon_3in3_sat()
    return {"agreement_sat_3in3": {"pass": okC and okZ, "cvc5": vC, "z3": vZ}}

def run_boundary_tests():
    okC, vC = cvc5_pigeon_3in2_p1eq1_unsat()
    okZ, vZ = z3_pigeon_3in2_p1eq1_unsat()
    return {"agreement_unsat_with_unit": {"pass": okC and okZ, "cvc5": vC, "z3": vZ}}


if __name__ == "__main__":
    if cvc5 is None or z3mod is None:
        print("BLOCKER: both cvc5 and z3 required for agreement sim")
        raise SystemExit(2)
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(v["pass"] for v in {**pos,**neg,**bnd}.values())
    results = {
        "name": "sim_cvc5_deep_z3_cvc5_agreement",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "overall_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_cvc5_deep_z3_cvc5_agreement_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {out_path}")
