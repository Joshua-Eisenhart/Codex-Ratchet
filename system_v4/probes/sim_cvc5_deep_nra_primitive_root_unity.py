#!/usr/bin/env python3
"""
sim_cvc5_deep_nra_primitive_root_unity.py

Deep cvc5 integration. Lego: quantifier-free nonlinear real arithmetic.
Claim: r^2 + r + 1 = 0 has no real solution (the cube roots of unity
other than 1 are non-real). cvc5 QF_NRA must return UNSAT.
Boundary: r^2 - 1 = 0 is SAT (r in {-1,+1}). Negative: r^2 + r = 0 is SAT.

Classification: canonical (cvc5 is the decision procedure for QF_NRA here;
numerical evaluation cannot certify "no real root" without an argument).
"""
import json, os

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "numeric search cannot certify no-solution"},
    "pyg":     {"tried": False, "used": False, "reason": "no graph"},
    "z3":      {"tried": False, "used": False, "reason": ""},
    "cvc5":    {"tried": False, "used": False, "reason": ""},
    "sympy":   {"tried": False, "used": False, "reason": "sympy could solve symbolically but claim is SMT-style UNSAT"},
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
try:
    import z3 as z3mod
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    z3mod = None


def _solver():
    tm = cvc5.TermManager(); s = cvc5.Solver(tm)
    s.setOption("produce-models", "true"); s.setLogic("QF_NRA")
    return tm, s


def _poly(tm, r, coeffs):
    """coeffs low->high, e.g. [1,1,1] for r^2+r+1."""
    terms = []
    mul = lambda a,b: tm.mkTerm(Kind.MULT, a, b)
    power = r
    terms.append(tm.mkReal(str(coeffs[0])))
    if len(coeffs) > 1:
        terms.append(mul(tm.mkReal(str(coeffs[1])), r))
        if len(coeffs) > 2:
            r2 = mul(r, r)
            terms.append(mul(tm.mkReal(str(coeffs[2])), r2))
    return tm.mkTerm(Kind.ADD, *terms)


def cvc5_rsq_plus_r_plus_1_unsat():
    tm, s = _solver()
    R = tm.getRealSort()
    r = tm.mkConst(R, "r")
    p = _poly(tm, r, [1, 1, 1])
    s.assertFormula(tm.mkTerm(Kind.EQUAL, p, tm.mkReal("0")))
    res = s.checkSat()
    return res.isUnsat(), str(res)


def z3_rsq_plus_r_plus_1_unsat():
    r = z3mod.Real("r")
    s = z3mod.Solver()
    s.add(r*r + r + 1 == 0)
    return s.check() == z3mod.unsat, str(s.check())


def cvc5_rsq_plus_r_sat():
    """Negative: r^2 + r = 0 is SAT (r=0 or r=-1)."""
    tm, s = _solver()
    R = tm.getRealSort()
    r = tm.mkConst(R, "r")
    p = _poly(tm, r, [0, 1, 1])
    s.assertFormula(tm.mkTerm(Kind.EQUAL, p, tm.mkReal("0")))
    res = s.checkSat()
    return res.isSat(), str(res)


def cvc5_rsq_minus_1_sat():
    """Boundary: r^2 - 1 = 0 is SAT (r in {-1,1})."""
    tm, s = _solver()
    R = tm.getRealSort()
    r = tm.mkConst(R, "r")
    p = _poly(tm, r, [-1, 0, 1])
    s.assertFormula(tm.mkTerm(Kind.EQUAL, p, tm.mkReal("0")))
    res = s.checkSat()
    return res.isSat(), str(res)


def run_positive_tests():
    ok, v = cvc5_rsq_plus_r_plus_1_unsat()
    TOOL_MANIFEST["cvc5"]["used"] = True
    TOOL_MANIFEST["cvc5"]["reason"] = "cvc5 QF_NRA UNSAT on r^2+r+1=0 IS the no-real-root proof"
    TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
    out = {"cvc5_nra_unsat": {"pass": ok, "verdict": v}}
    if z3mod is not None:
        ok2, v2 = z3_rsq_plus_r_plus_1_unsat()
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = "z3 NRA parity UNSAT"
        TOOL_INTEGRATION_DEPTH["z3"] = "supportive"
        out["z3_parity_unsat"] = {"pass": ok2, "verdict": v2}
    return out

def run_negative_tests():
    ok, v = cvc5_rsq_plus_r_sat()
    return {"cvc5_rsq_plus_r_sat": {"pass": ok, "verdict": v}}

def run_boundary_tests():
    ok, v = cvc5_rsq_minus_1_sat()
    return {"cvc5_rsq_minus_1_sat": {"pass": ok, "verdict": v}}


if __name__ == "__main__":
    if cvc5 is None:
        print("BLOCKER: cvc5 not importable"); raise SystemExit(2)
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(v["pass"] for v in {**pos,**neg,**bnd}.values())
    results = {
        "name": "sim_cvc5_deep_nra_primitive_root_unity",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "overall_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_cvc5_deep_nra_primitive_root_unity_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {out_path}")
