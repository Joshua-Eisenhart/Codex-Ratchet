#!/usr/bin/env python3
"""
sim_cvc5_deep_chsh_nolhv.py

Deep cvc5 integration. Lego: CHSH no-LHV.
Claim: no assignment of {A0,A1,B0,B1} in {-1,+1} yields
  S = A0*B0 + A0*B1 + A1*B0 - A1*B1 > 2.
Encode in QF_LIA over integer {-1,+1} variables and check
  S >= 3 (UNSAT) -> the Bell bound 2 is tight classically.
cvc5 returns UNSAT; z3 supportive parity.

Classification: canonical (cvc5 UNSAT IS the no-LHV evidence).
"""
import json, os

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed; combinatorial SMT claim"},
    "pyg":     {"tried": False, "used": False, "reason": "no graph content"},
    "z3":      {"tried": False, "used": False, "reason": ""},
    "cvc5":    {"tried": False, "used": False, "reason": ""},
    "sympy":   {"tried": False, "used": False, "reason": "not algebraic-simplification work"},
    "clifford":{"tried": False, "used": False, "reason": "no GA"},
    "geomstats":{"tried": False, "used": False, "reason": "no manifold"},
    "e3nn":    {"tried": False, "used": False, "reason": "no equivariance"},
    "rustworkx":{"tried": False, "used": False, "reason": "no graph"},
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
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed -- BLOCKER"

try:
    import z3 as z3mod
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    z3mod = None


def _solver():
    tm = cvc5.TermManager(); s = cvc5.Solver(tm)
    s.setOption("produce-models", "true"); s.setLogic("QF_NIA")
    return tm, s

def _pm1(tm, s, name):
    Int = tm.getIntegerSort()
    v = tm.mkConst(Int, name)
    one = tm.mkInteger(1); neg1 = tm.mkInteger(-1)
    s.assertFormula(tm.mkTerm(Kind.OR,
        tm.mkTerm(Kind.EQUAL, v, one),
        tm.mkTerm(Kind.EQUAL, v, neg1)))
    return v

def _chsh_S(tm, A0, A1, B0, B1):
    mul = lambda a,b: tm.mkTerm(Kind.MULT, a, b)
    add = lambda *xs: tm.mkTerm(Kind.ADD, *xs)
    sub = lambda a,b: tm.mkTerm(Kind.SUB, a, b)
    return add(mul(A0,B0), mul(A0,B1), mul(A1,B0), tm.mkTerm(Kind.NEG, mul(A1,B1)))


def cvc5_chsh_unsat():
    tm, s = _solver()
    A0 = _pm1(tm,s,"A0"); A1 = _pm1(tm,s,"A1")
    B0 = _pm1(tm,s,"B0"); B1 = _pm1(tm,s,"B1")
    S = _chsh_S(tm, A0,A1,B0,B1)
    s.assertFormula(tm.mkTerm(Kind.GEQ, S, tm.mkInteger(3)))
    r = s.checkSat()
    return r.isUnsat(), str(r)

def z3_chsh_unsat():
    A0,A1,B0,B1 = [z3mod.Int(n) for n in ("A0","A1","B0","B1")]
    s = z3mod.Solver()
    for v in (A0,A1,B0,B1):
        s.add(z3mod.Or(v==1, v==-1))
    S = A0*B0 + A0*B1 + A1*B0 - A1*B1
    s.add(S >= 3)
    return s.check() == z3mod.unsat, str(s.check())

def cvc5_chsh_tight_sat():
    """Negative: S == 2 must be SAT (classical bound achievable)."""
    tm, s = _solver()
    A0 = _pm1(tm,s,"A0"); A1 = _pm1(tm,s,"A1")
    B0 = _pm1(tm,s,"B0"); B1 = _pm1(tm,s,"B1")
    S = _chsh_S(tm, A0,A1,B0,B1)
    s.assertFormula(tm.mkTerm(Kind.EQUAL, S, tm.mkInteger(2)))
    r = s.checkSat()
    return r.isSat(), str(r)

def cvc5_chsh_boundary_S_eq_2():
    """Boundary: S > 2 (strict) is UNSAT."""
    tm, s = _solver()
    A0 = _pm1(tm,s,"A0"); A1 = _pm1(tm,s,"A1")
    B0 = _pm1(tm,s,"B0"); B1 = _pm1(tm,s,"B1")
    S = _chsh_S(tm, A0,A1,B0,B1)
    s.assertFormula(tm.mkTerm(Kind.GT, S, tm.mkInteger(2)))
    r = s.checkSat()
    return r.isUnsat(), str(r)


def run_positive_tests():
    ok, v = cvc5_chsh_unsat()
    TOOL_MANIFEST["cvc5"]["used"] = True
    TOOL_MANIFEST["cvc5"]["reason"] = "cvc5 UNSAT on S>=3 with +/-1 hidden variables IS the no-LHV proof"
    TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
    out = {"cvc5_chsh_S_ge_3_unsat": {"pass": ok, "verdict": v}}
    if z3mod is not None:
        ok2, v2 = z3_chsh_unsat()
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = "z3 parity UNSAT matches cvc5"
        TOOL_INTEGRATION_DEPTH["z3"] = "supportive"
        out["z3_parity_unsat"] = {"pass": ok2, "verdict": v2}
    return out

def run_negative_tests():
    ok, v = cvc5_chsh_tight_sat()
    return {"cvc5_S_eq_2_sat": {"pass": ok, "verdict": v}}

def run_boundary_tests():
    ok, v = cvc5_chsh_boundary_S_eq_2()
    return {"cvc5_S_gt_2_unsat": {"pass": ok, "verdict": v}}


if __name__ == "__main__":
    if cvc5 is None:
        print("BLOCKER: cvc5 not importable")
        raise SystemExit(2)
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(v["pass"] for v in {**pos,**neg,**bnd}.values())
    results = {
        "name": "sim_cvc5_deep_chsh_nolhv",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "overall_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_cvc5_deep_chsh_nolhv_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {out_path}")
