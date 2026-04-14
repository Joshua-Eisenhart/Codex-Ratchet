#!/usr/bin/env python3
"""
sim_cvc5_capability.py -- Tool-capability isolation sim for cvc5.

Governing rule (durable, owner+Hermes 2026-04-13):
cvc5 acts as an independent second-solver cross-check for z3 claims.
This probe exercises SAT/UNSAT parity on small shared encodings.

Decorative = `import cvc5` without solver.checkSat() used in claim.
Load-bearing = cvc5 verdict used to corroborate (or falsify) z3 verdict.
"""

import json
import os

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "not needed"},
    "pyg":       {"tried": False, "used": False, "reason": "not needed"},
    "z3":        {"tried": False, "used": False, "reason": "separate z3 probe"},
    "cvc5":      {"tried": False, "used": False, "reason": "under test"},
    "sympy":     {"tried": False, "used": False, "reason": "not needed"},
    "clifford":  {"tried": False, "used": False, "reason": "not geometry-relevant"},
    "geomstats": {"tried": False, "used": False, "reason": "not geometry-relevant"},
    "e3nn":      {"tried": False, "used": False, "reason": "not geometry-relevant"},
    "rustworkx": {"tried": False, "used": False, "reason": "not graph-relevant"},
    "xgi":       {"tried": False, "used": False, "reason": "not graph-relevant"},
    "toponetx":  {"tried": False, "used": False, "reason": "not topology-relevant"},
    "gudhi":     {"tried": False, "used": False, "reason": "not topology-relevant"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None, "z3": None,
    "cvc5": "load_bearing",
    "sympy": None,
    "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

try:
    import cvc5
    from cvc5 import Kind
    TOOL_MANIFEST["cvc5"]["tried"] = True
    TOOL_MANIFEST["cvc5"]["used"] = True
    TOOL_MANIFEST["cvc5"]["reason"] = "capability under test -- SAT/UNSAT parity with z3 on shared encodings"
    CVC5_OK = True
    CVC5_VERSION = getattr(cvc5, "__version__", "unknown")
except Exception as exc:
    CVC5_OK = False
    CVC5_VERSION = None
    TOOL_MANIFEST["cvc5"]["reason"] = f"not installed: {exc}"


def _fresh_solver(logic="ALL"):
    s = cvc5.Solver()
    s.setOption("produce-models", "true")
    s.setLogic(logic)
    return s


def run_positive_tests():
    r = {}
    if not CVC5_OK:
        r["cvc5_available"] = {"pass": False, "detail": "cvc5 missing"}
        return r
    r["cvc5_available"] = {"pass": True, "version": CVC5_VERSION}

    # 1. Simple SAT: Bool x and y both true.
    s = _fresh_solver("QF_UF")
    B = s.getBooleanSort()
    x = s.mkConst(B, "x")
    y = s.mkConst(B, "y")
    s.assertFormula(s.mkTerm(Kind.AND, x, y))
    res = s.checkSat()
    r["simple_sat"] = {
        "pass": res.isSat(),
        "result": str(res),
    }

    # 2. Linear integer system x+y=10, x-y=4 => x=7, y=3.
    s = _fresh_solver("QF_LIA")
    I = s.getIntegerSort()
    x = s.mkConst(I, "x")
    y = s.mkConst(I, "y")
    s.assertFormula(s.mkTerm(Kind.EQUAL, s.mkTerm(Kind.ADD, x, y), s.mkInteger(10)))
    s.assertFormula(s.mkTerm(Kind.EQUAL, s.mkTerm(Kind.SUB, x, y), s.mkInteger(4)))
    res = s.checkSat()
    model_ok = False
    if res.isSat():
        vx = int(s.getValue(x).getIntegerValue())
        vy = int(s.getValue(y).getIntegerValue())
        model_ok = (vx == 7 and vy == 3)
    r["linear_system_solution"] = {
        "pass": res.isSat() and model_ok,
        "result": str(res),
    }

    # 3. Parity with z3 on KCBS-like 5-cycle bound: sum>=3 with adjacent-exclusion is UNSAT.
    s = _fresh_solver("QF_LIA")
    I = s.getIntegerSort()
    vs = [s.mkConst(I, f"v{i}") for i in range(5)]
    zero = s.mkInteger(0)
    one = s.mkInteger(1)
    three = s.mkInteger(3)
    for vi in vs:
        s.assertFormula(s.mkTerm(Kind.OR,
                                  s.mkTerm(Kind.EQUAL, vi, zero),
                                  s.mkTerm(Kind.EQUAL, vi, one)))
    for i in range(5):
        a = vs[i]; b = vs[(i + 1) % 5]
        both_one = s.mkTerm(Kind.AND,
                            s.mkTerm(Kind.EQUAL, a, one),
                            s.mkTerm(Kind.EQUAL, b, one))
        s.assertFormula(s.mkTerm(Kind.NOT, both_one))
    total = s.mkTerm(Kind.ADD, *vs)
    s.assertFormula(s.mkTerm(Kind.GEQ, total, three))
    res = s.checkSat()
    r["kcbs_c5_bound_unsat"] = {
        "pass": res.isUnsat(),
        "result": str(res),
        "detail": "C5 max independent set = 2; sum>=3 must be UNSAT (parity with z3 probe)",
    }

    # 4. Real arithmetic: x*x < 0 is UNSAT over reals.
    s = _fresh_solver("QF_NRA")
    R = s.getRealSort()
    xr = s.mkConst(R, "x")
    zero_r = s.mkReal(0)
    s.assertFormula(s.mkTerm(Kind.LT, s.mkTerm(Kind.MULT, xr, xr), zero_r))
    res = s.checkSat()
    r["real_nonnegativity_unsat"] = {
        "pass": res.isUnsat(),
        "result": str(res),
    }
    return r


def run_negative_tests():
    r = {}
    if not CVC5_OK:
        r["cvc5_available"] = {"pass": False, "detail": "cvc5 missing"}
        return r

    # p AND not p is UNSAT.
    s = _fresh_solver("QF_UF")
    B = s.getBooleanSort()
    p = s.mkConst(B, "p")
    s.assertFormula(s.mkTerm(Kind.AND, p, s.mkTerm(Kind.NOT, p)))
    res = s.checkSat()
    r["contradiction_unsat"] = {"pass": res.isUnsat(), "result": str(res)}

    # Tautology SAT.
    s = _fresh_solver("QF_UF")
    p = s.mkConst(s.getBooleanSort(), "p")
    s.assertFormula(s.mkTerm(Kind.OR, p, s.mkTerm(Kind.NOT, p)))
    res = s.checkSat()
    r["tautology_sat"] = {"pass": res.isSat(), "result": str(res)}

    # Ill-formed: adding int sort term where boolean expected should raise.
    raised = False
    err = None
    try:
        s = _fresh_solver("QF_LIA")
        i = s.mkConst(s.getIntegerSort(), "i")
        s.assertFormula(i)  # not a Bool
        s.checkSat()
    except Exception as exc:
        raised = True
        err = type(exc).__name__
    r["ill_formed_raises"] = {
        "pass": raised,
        "error_type": err,
    }
    return r


def run_boundary_tests():
    r = {}
    if not CVC5_OK:
        r["cvc5_available"] = {"pass": False, "detail": "cvc5 missing"}
        return r

    # Empty formula set is SAT (vacuously).
    s = _fresh_solver("QF_UF")
    res = s.checkSat()
    r["empty_assertions_sat"] = {"pass": res.isSat(), "result": str(res)}

    # UNSAT core on slightly larger constraint set: x>0, x<0 is UNSAT.
    s = _fresh_solver("QF_LIA")
    Ix = s.getIntegerSort()
    x = s.mkConst(Ix, "x")
    zero = s.mkInteger(0)
    s.assertFormula(s.mkTerm(Kind.GT, x, zero))
    s.assertFormula(s.mkTerm(Kind.LT, x, zero))
    res = s.checkSat()
    r["contradictory_ranges_unsat"] = {"pass": res.isUnsat(), "result": str(res)}

    # Multi-variable SAT with witness extraction.
    s = _fresh_solver("QF_LIA")
    I = s.getIntegerSort()
    a = s.mkConst(I, "a")
    b = s.mkConst(I, "b")
    s.assertFormula(s.mkTerm(Kind.GEQ, a, s.mkInteger(1)))
    s.assertFormula(s.mkTerm(Kind.GEQ, b, s.mkInteger(1)))
    s.assertFormula(s.mkTerm(Kind.EQUAL,
                             s.mkTerm(Kind.ADD, a, b),
                             s.mkInteger(5)))
    res = s.checkSat()
    witness_ok = False
    if res.isSat():
        va = int(s.getValue(a).getIntegerValue())
        vb = int(s.getValue(b).getIntegerValue())
        witness_ok = (va >= 1 and vb >= 1 and va + vb == 5)
    r["multi_var_witness"] = {
        "pass": res.isSat() and witness_ok,
        "result": str(res),
    }
    return r


def _all_pass(section):
    return all(bool(v.get("pass", False)) for v in section.values())


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    summary = {
        "positive_all_pass": _all_pass(pos),
        "negative_all_pass": _all_pass(neg),
        "boundary_all_pass": _all_pass(bnd),
    }
    summary["all_pass"] = all(summary.values())

    results = {
        "name": "sim_cvc5_capability",
        "purpose": "Tool-capability isolation probe for cvc5 -- SAT/UNSAT parity with z3.",
        "cvc5_version": CVC5_VERSION,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "witness_file": "system_v4/probes/sim_bridge_cvc5_crosscheck.py",
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "cvc5_capability_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {summary['all_pass']}")
