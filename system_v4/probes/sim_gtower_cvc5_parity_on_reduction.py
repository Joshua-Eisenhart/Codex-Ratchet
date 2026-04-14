#!/usr/bin/env python3
"""sim_gtower_cvc5_parity_on_reduction -- cvc5 vs z3 parity on G-tower fences.

Scope note: LADDERS_FENCES_ADMISSION_REFERENCE.md: fence proofs should be
solver-independent. Load-bearing: cvc5 reproduces the UNSAT verdicts that
z3 returns on the same forbidden-reduction encodings (orientation fence,
Sp-det fence). Mismatch => fence not solver-invariant => flagged.
"""
import json, os

classification = "canonical"

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import z3
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5
    from cvc5 import Kind
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"


def z3_orientation_unsat():
    a, b, c, d = z3.Reals("a b c d")
    s = z3.Solver()
    s.add(a*a + c*c == 1, b*b + d*d == 1, a*b + c*d == 0)
    s.add(a*d - b*c == -1)
    s.add(a*d - b*c == 1)
    return str(s.check())


def cvc5_orientation_unsat():
    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("QF_NRA")
    R = tm.getRealSort()
    a, b, c, d = [tm.mkConst(R, n) for n in ("a", "b", "c", "d")]
    one = tm.mkReal(1)
    mone = tm.mkReal(-1)
    zero = tm.mkReal(0)

    def mul(x, y): return tm.mkTerm(Kind.MULT, x, y)
    def add(*xs):  return tm.mkTerm(Kind.ADD, *xs)
    def sub(x, y): return tm.mkTerm(Kind.SUB, x, y)
    def eq(x, y):  return tm.mkTerm(Kind.EQUAL, x, y)

    # a^2 + c^2 = 1
    slv.assertFormula(eq(add(mul(a, a), mul(c, c)), one))
    slv.assertFormula(eq(add(mul(b, b), mul(d, d)), one))
    slv.assertFormula(eq(add(mul(a, b), mul(c, d)), zero))
    det = sub(mul(a, d), mul(b, c))
    slv.assertFormula(eq(det, mone))
    slv.assertFormula(eq(det, one))
    return str(slv.checkSat())


def cvc5_sp_det_unsat():
    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("QF_NRA")
    R = tm.getRealSort()
    a, b, c, d = [tm.mkConst(R, n) for n in ("a", "b", "c", "d")]
    one = tm.mkReal(1); mone = tm.mkReal(-1)
    def mul(x, y): return tm.mkTerm(Kind.MULT, x, y)
    def sub(x, y): return tm.mkTerm(Kind.SUB, x, y)
    def eq(x, y):  return tm.mkTerm(Kind.EQUAL, x, y)
    det = sub(mul(a, d), mul(b, c))
    slv.assertFormula(eq(det, one))
    slv.assertFormula(eq(det, mone))
    return str(slv.checkSat())


def z3_sp_det_unsat():
    a, b, c, d = z3.Reals("a b c d")
    s = z3.Solver()
    s.add(a*d - b*c == 1)
    s.add(a*d - b*c == -1)
    return str(s.check())


def run_positive_tests():
    r = {}
    if not (TOOL_MANIFEST["z3"]["tried"] and TOOL_MANIFEST["cvc5"]["tried"]):
        return {"skipped": True}
    z3o = z3_orientation_unsat()
    c5o = cvc5_orientation_unsat()
    z3s = z3_sp_det_unsat()
    c5s = cvc5_sp_det_unsat()
    r["z3_orientation"] = z3o
    r["cvc5_orientation"] = c5o
    r["orientation_parity"] = (z3o == "unsat" and c5o == "unsat")
    r["z3_sp_det"] = z3s
    r["cvc5_sp_det"] = c5s
    r["sp_det_parity"] = (z3s == "unsat" and c5s == "unsat")
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "reference UNSAT verdicts for fence obstructions"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    TOOL_MANIFEST["cvc5"]["used"] = True
    TOOL_MANIFEST["cvc5"]["reason"] = "independent UNSAT reproduction -- solver-parity check"
    TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
    return r


def run_negative_tests():
    r = {}
    if not TOOL_MANIFEST["cvc5"]["tried"]:
        return {"skipped": True}
    # cvc5 satisfiable case: det=1 alone
    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("QF_NRA")
    R = tm.getRealSort()
    a, b, c, d = [tm.mkConst(R, n) for n in ("a", "b", "c", "d")]
    one = tm.mkReal(1)
    def mul(x, y): return tm.mkTerm(Kind.MULT, x, y)
    def sub(x, y): return tm.mkTerm(Kind.SUB, x, y)
    def eq(x, y):  return tm.mkTerm(Kind.EQUAL, x, y)
    slv.assertFormula(eq(sub(mul(a, d), mul(b, c)), one))
    verdict = str(slv.checkSat())
    r["sat_case"] = verdict
    r["sat_ok"] = (verdict == "sat")
    return r


def run_boundary_tests():
    r = {}
    if not TOOL_MANIFEST["cvc5"]["tried"]:
        return {"skipped": True}
    # trivial unsat in cvc5
    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("QF_NRA")
    R = tm.getRealSort()
    x = tm.mkConst(R, "x")
    def eq(a, b): return tm.mkTerm(Kind.EQUAL, a, b)
    slv.assertFormula(eq(x, tm.mkReal(0)))
    slv.assertFormula(tm.mkTerm(Kind.NOT, eq(x, tm.mkReal(0))))
    r["trivial_unsat"] = (str(slv.checkSat()) == "unsat")
    return r


if __name__ == "__main__":
    pos, neg, bnd = run_positive_tests(), run_negative_tests(), run_boundary_tests()
    def _t(v): return bool(v) is True
    all_pass = (_t(pos.get("orientation_parity")) and _t(pos.get("sp_det_parity"))
                and _t(neg.get("sat_ok")) and _t(bnd.get("trivial_unsat")))
    results = {
        "name": "sim_gtower_cvc5_parity_on_reduction",
        "classification": "canonical",
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md: fence-proof solver parity",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "status": "PASS" if all_pass else "FAIL",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "sim_gtower_cvc5_parity_on_reduction_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{results['name']}: {results['status']}")
