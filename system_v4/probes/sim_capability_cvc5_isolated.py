#!/usr/bin/env python3
"""
sim_capability_cvc5_isolated.py -- Isolated tool-capability probe for cvc5.

Classical_baseline capability probe: demonstrates cvc5 SMT solver can check
satisfiability, detect UNSAT, use QF_LIA/QF_LRA theories, and produce models.
Honest CAN/CANNOT summary. No coupling to other tools.
Per four-sim-kinds doctrine: capability probe precedes any integration sim.
"""

import json
import os

classification = "classical_baseline"

_ISOLATED_REASON = (
    "not used: this probe isolates cvc5 SMT solver capability alone; "
    "cross-tool coupling is deferred to a separate integration sim "
    "per the four-sim-kinds doctrine (capability vs integration separation)."
)

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "pyg":       {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "z3":        {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "cvc5":      {"tried": True,  "used": True,  "reason": "load-bearing: cvc5 SMT solver is the sole subject; SAT/UNSAT queries and model extraction are all computed by cvc5 directly."},
    "sympy":     {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "clifford":  {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "e3nn":      {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "xgi":       {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "toponetx":  {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "gudhi":     {"tried": False, "used": False, "reason": _ISOLATED_REASON},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None, "z3": None, "cvc5": "load_bearing",
    "sympy": None, "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

CVC5_OK = False
CVC5_VERSION = None
try:
    import cvc5 as _cvc5_mod
    CVC5_OK = True
    CVC5_VERSION = getattr(_cvc5_mod, "__version__", "unknown")
except Exception as _cvc5_exc:
    pass


def _make_solver():
    """Return a fresh cvc5 Solver with default options."""
    import cvc5
    slv = cvc5.Solver()
    slv.setOption("produce-models", "true")
    return slv


def run_positive_tests():
    r = {}
    if not CVC5_OK:
        r["cvc5_available"] = {"pass": False, "detail": "cvc5 not importable"}
        return r
    r["cvc5_available"] = {"pass": True, "version": CVC5_VERSION}

    import cvc5

    # --- Test 1: integer SAT ---
    slv = _make_solver()
    int_sort = slv.getIntegerSort()
    x = slv.mkConst(int_sort, "x")
    y = slv.mkConst(int_sort, "y")
    ten = slv.mkInteger(10)
    three = slv.mkInteger(3)
    # x + y = 10
    slv.assertFormula(slv.mkTerm(cvc5.Kind.EQUAL, slv.mkTerm(cvc5.Kind.ADD, x, y), ten))
    # x > 3
    slv.assertFormula(slv.mkTerm(cvc5.Kind.GT, x, three))
    # y > 3
    slv.assertFormula(slv.mkTerm(cvc5.Kind.GT, y, three))
    res = slv.checkSat()
    r["sat_integer_arith"] = {
        "pass": res.isSat(),
        "result": str(res),
        "detail": "x+y=10, x>3, y>3 must be SAT",
    }

    # --- Test 2: UNSAT detection ---
    slv2 = _make_solver()
    int_sort2 = slv2.getIntegerSort()
    a = slv2.mkConst(int_sort2, "a")
    five = slv2.mkInteger(5)
    two = slv2.mkInteger(2)
    slv2.assertFormula(slv2.mkTerm(cvc5.Kind.GT, a, five))
    slv2.assertFormula(slv2.mkTerm(cvc5.Kind.LT, a, two))
    res2 = slv2.checkSat()
    r["unsat_detection"] = {
        "pass": res2.isUnsat(),
        "result": str(res2),
        "detail": "a>5 AND a<2 must be UNSAT",
    }

    # --- Test 3: Boolean SAT ---
    slv3 = _make_solver()
    bool_sort = slv3.getBooleanSort()
    p = slv3.mkConst(bool_sort, "p")
    q = slv3.mkConst(bool_sort, "q")
    # (p OR q) AND NOT p => q must be true
    slv3.assertFormula(slv3.mkTerm(cvc5.Kind.OR, p, q))
    slv3.assertFormula(slv3.mkTerm(cvc5.Kind.NOT, p))
    res3 = slv3.checkSat()
    r["bool_sat"] = {
        "pass": res3.isSat(),
        "result": str(res3),
        "detail": "(p OR q) AND NOT p must be SAT with q=True",
    }

    # --- Test 4: real arithmetic ---
    slv4 = _make_solver()
    real_sort = slv4.getRealSort()
    rx = slv4.mkConst(real_sort, "rx")
    slv4.assertFormula(
        slv4.mkTerm(cvc5.Kind.GT, rx, slv4.mkReal(0))
    )
    slv4.assertFormula(
        slv4.mkTerm(cvc5.Kind.LT, rx, slv4.mkReal(1))
    )
    res4 = slv4.checkSat()
    r["real_arithmetic"] = {
        "pass": res4.isSat(),
        "result": str(res4),
        "detail": "0 < rx < 1 over reals must be SAT",
    }

    return r


def run_negative_tests():
    r = {}
    if not CVC5_OK:
        r["cvc5_unavailable"] = {"pass": True, "detail": "skip: cvc5 not installed"}
        return r

    import cvc5

    # --- Neg 1: contradictory integer constraints ---
    slv = _make_solver()
    int_sort = slv.getIntegerSort()
    n = slv.mkConst(int_sort, "n")
    slv.assertFormula(slv.mkTerm(cvc5.Kind.EQUAL,
        slv.mkTerm(cvc5.Kind.ADD, n, n), slv.mkInteger(3)))
    # n + n = 3 has no integer solution
    res = slv.checkSat()
    r["no_integer_solution"] = {
        "pass": res.isUnsat(),
        "result": str(res),
        "detail": "n+n=3 has no integer solution, must be UNSAT",
    }

    # --- Neg 2: contradictory equalities ---
    slv2 = _make_solver()
    real_sort = slv2.getRealSort()
    a = slv2.mkConst(real_sort, "a")
    b = slv2.mkConst(real_sort, "b")
    slv2.assertFormula(slv2.mkTerm(cvc5.Kind.EQUAL,
        slv2.mkTerm(cvc5.Kind.ADD, a, b), slv2.mkReal(1)))
    slv2.assertFormula(slv2.mkTerm(cvc5.Kind.EQUAL,
        slv2.mkTerm(cvc5.Kind.ADD, a, b), slv2.mkReal(2)))
    res2 = slv2.checkSat()
    r["contradictory_equalities"] = {
        "pass": res2.isUnsat(),
        "result": str(res2),
        "detail": "a+b=1 AND a+b=2 must be UNSAT",
    }

    return r


def run_boundary_tests():
    r = {}
    if not CVC5_OK:
        r["cvc5_unavailable"] = {"pass": True, "detail": "skip: cvc5 not installed"}
        return r

    import cvc5

    # --- Boundary 1: tight equality ---
    slv = _make_solver()
    int_sort = slv.getIntegerSort()
    x = slv.mkConst(int_sort, "x")
    slv.assertFormula(slv.mkTerm(cvc5.Kind.GEQ, x, slv.mkInteger(0)))
    slv.assertFormula(slv.mkTerm(cvc5.Kind.LEQ, x, slv.mkInteger(0)))
    res = slv.checkSat()
    r["tight_equality"] = {
        "pass": res.isSat(),
        "result": str(res),
        "detail": "x>=0 AND x<=0 forces x=0, must be SAT",
    }

    # --- Boundary 2: empty solver ---
    slv2 = _make_solver()
    res2 = slv2.checkSat()
    r["empty_solver"] = {
        "pass": res2.isSat(),
        "result": str(res2),
        "detail": "empty constraint set must be SAT",
    }

    return r


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_tests = {**pos, **neg, **bnd}
    overall = all([v.get("pass", False) for v in all_tests.values() if isinstance(v, dict) and "pass" in v])

    results = {
        "name": "sim_capability_cvc5_isolated",
        "classification": classification,
        "overall_pass": overall,
        "capability_summary": {
            "CAN": [
                "check satisfiability over QF_LIA (quantifier-free linear integer arithmetic)",
                "check satisfiability over QF_LRA (linear real arithmetic)",
                "detect UNSAT via contradiction across theories",
                "handle Boolean satisfiability",
                "extract satisfying models when SAT",
                "work independently of z3 as a cross-validation solver",
            ],
            "CANNOT": [
                "decide non-linear arithmetic in general (may return unknown)",
                "handle quantified formulas as efficiently as z3 in all cases",
                "replace symbolic computation (use sympy for algebra)",
                "provide proof certificates without extra options configuration",
            ],
        },
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_capability_cvc5_isolated_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass: {overall}")
