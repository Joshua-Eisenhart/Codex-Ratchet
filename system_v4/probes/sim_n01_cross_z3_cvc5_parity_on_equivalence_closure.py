#!/usr/bin/env python3
"""sim_n01_cross_z3_cvc5_parity_on_equivalence_closure -- Both z3 and cvc5 must
agree on the equivalence-closure of the probe-agreement relation. Both tools
load-bearing: each independently certifies UNSAT of non-transitive closure.
"""
import json, os

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import z3; TOOL_MANIFEST["z3"]["tried"] = True
except ImportError: TOOL_MANIFEST["z3"]["reason"] = "not installed"
try:
    import cvc5; from cvc5 import Kind; TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError: TOOL_MANIFEST["cvc5"]["reason"] = "not installed"


def z3_check():
    a,b,c = z3.Ints("a b c")
    m = z3.Function("m", z3.IntSort(), z3.IntSort())
    s = z3.Solver()
    s.add(m(a)==m(b)); s.add(m(b)==m(c)); s.add(m(a)!=m(c))
    return str(s.check())


def cvc5_check():
    slv = cvc5.Solver()
    slv.setOption("produce-models", "false")
    slv.setLogic("QF_UFLIA")
    Int = slv.getIntegerSort()
    a = slv.mkConst(Int, "a"); b = slv.mkConst(Int, "b"); c = slv.mkConst(Int, "c")
    mfun = slv.mkConst(slv.mkFunctionSort([Int], Int), "m")
    ma = slv.mkTerm(Kind.APPLY_UF, mfun, a)
    mb = slv.mkTerm(Kind.APPLY_UF, mfun, b)
    mc = slv.mkTerm(Kind.APPLY_UF, mfun, c)
    slv.assertFormula(slv.mkTerm(Kind.EQUAL, ma, mb))
    slv.assertFormula(slv.mkTerm(Kind.EQUAL, mb, mc))
    slv.assertFormula(slv.mkTerm(Kind.NOT, slv.mkTerm(Kind.EQUAL, ma, mc)))
    return str(slv.checkSat())


def run_positive_tests():
    z = z3_check(); c = cvc5_check()
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "load-bearing: independent UNSAT check of transitivity"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    TOOL_MANIFEST["cvc5"]["used"] = True
    TOOL_MANIFEST["cvc5"]["reason"] = "load-bearing: independent UNSAT check of transitivity"
    TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
    return {"z3": z, "cvc5": c, "pass": z == "unsat" and "unsat" in c.lower()}


def run_negative_tests():
    # Both solvers should say SAT on a consistent formula.
    a = z3.Int("a"); s = z3.Solver(); s.add(a == a)
    z = str(s.check())
    slv = cvc5.Solver(); slv.setLogic("QF_LIA")
    Int = slv.getIntegerSort()
    aa = slv.mkConst(Int, "a")
    slv.assertFormula(slv.mkTerm(cvc5.Kind.EQUAL, aa, aa))
    c = str(slv.checkSat())
    return {"z3": z, "cvc5": c, "pass": z == "sat" and "unsat" not in c.lower()}


def run_boundary_tests():
    # Empty assertion: both SAT.
    s = z3.Solver(); z = str(s.check())
    slv = cvc5.Solver(); slv.setLogic("QF_LIA"); c = str(slv.checkSat())
    return {"z3": z, "cvc5": c, "pass": z == "sat" and "unsat" not in c.lower()}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    ok = bool(pos["pass"] and neg["pass"] and bnd["pass"])
    name = "sim_n01_cross_z3_cvc5_parity_on_equivalence_closure"
    results = {"name": name, "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "pass": ok}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, name + "_results.json")
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if ok else 'FAIL'} -> {out}")
