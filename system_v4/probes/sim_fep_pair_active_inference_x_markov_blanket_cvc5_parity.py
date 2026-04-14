#!/usr/bin/env python3
"""cvc5 parity sibling for sim_fep_pair_active_inference_x_markov_blanket.

scope_note: Re-encodes z3 tautology check from parent
system_v4/probes/sim_fep_pair_active_inference_x_markov_blanket.py in cvc5;
asserts z3<->cvc5 UNSAT parity. Does not modify parent.
"""
import os, sys
from _cvc5_parity_helper import write_results, all_pass

TOOL_MANIFEST = {"z3":{"tried":False,"used":False,"reason":""},
                 "cvc5":{"tried":False,"used":False,"reason":""}}
TOOL_INTEGRATION_DEPTH = {"z3": None, "cvc5": None}

try:
    import z3; TOOL_MANIFEST["z3"]["tried"]=True
except ImportError:
    z3=None; TOOL_MANIFEST["z3"]["reason"]="not installed"
try:
    import cvc5; from cvc5 import Kind; TOOL_MANIFEST["cvc5"]["tried"]=True
except ImportError:
    cvc5=None; TOOL_MANIFEST["cvc5"]["reason"]="not installed"

def z3_check():
    s = z3.Solver()
    a, b_, c, d = z3.Reals("a b_ c d")
    pol = z3.Real("pol")
    s.add(a > 0, b_ > 0, c > 0, d > 0, pol > 0)
    s.add(pol*a*c*pol*b_*d != (pol*a*c)*(pol*b_*d))
    return s.check() == z3.unsat

def cvc5_check():
    s = cvc5.Solver(); s.setLogic("QF_NRA")
    R = s.getRealSort(); zero = s.mkReal(0)
    a = s.mkConst(R,"a"); b_ = s.mkConst(R,"b_"); c = s.mkConst(R,"c"); d = s.mkConst(R,"d")
    pol = s.mkConst(R,"pol")
    for v in (a,b_,c,d,pol):
        s.assertFormula(s.mkTerm(Kind.GT, v, zero))
    lhs = s.mkTerm(Kind.MULT, pol, a, c, pol, b_, d)
    rhs = s.mkTerm(Kind.MULT, s.mkTerm(Kind.MULT, pol, a, c), s.mkTerm(Kind.MULT, pol, b_, d))
    s.assertFormula(s.mkTerm(Kind.NOT, s.mkTerm(Kind.EQUAL, lhs, rhs)))
    return str(s.checkSat()) == "unsat"

def run_positive_tests():
    if z3 is None or cvc5 is None: return {"tools_available": False}
    zu, cu = z3_check(), cvc5_check()
    TOOL_MANIFEST["z3"]["used"]=True; TOOL_MANIFEST["z3"]["reason"]="cross-check UNSAT on factorization tautology"
    TOOL_MANIFEST["cvc5"]["used"]=True; TOOL_MANIFEST["cvc5"]["reason"]="load-bearing UNSAT parity witness"
    TOOL_INTEGRATION_DEPTH["z3"]="supportive"; TOOL_INTEGRATION_DEPTH["cvc5"]="load_bearing"
    return {"z3_unsat": zu, "cvc5_unsat": cu, "parity_both_unsat": zu and cu}

def run_negative_tests():
    if cvc5 is None: return {"skip": False}
    # Change tautology LHS (drop a factor): now LHS != RHS is SAT
    s = cvc5.Solver(); s.setLogic("QF_NRA")
    R = s.getRealSort(); zero = s.mkReal(0)
    a = s.mkConst(R,"a"); b_ = s.mkConst(R,"b_"); c = s.mkConst(R,"c"); d = s.mkConst(R,"d"); pol = s.mkConst(R,"pol")
    for v in (a,b_,c,d,pol):
        s.assertFormula(s.mkTerm(Kind.GT, v, zero))
    lhs = s.mkTerm(Kind.MULT, a, c, b_, d)   # pol removed -> no longer equal
    rhs = s.mkTerm(Kind.MULT, s.mkTerm(Kind.MULT, pol, a, c), s.mkTerm(Kind.MULT, pol, b_, d))
    s.assertFormula(s.mkTerm(Kind.NOT, s.mkTerm(Kind.EQUAL, lhs, rhs)))
    return {"broken_tautology_becomes_sat": str(s.checkSat()) == "sat"}

def run_boundary_tests():
    if cvc5 is None: return {"skip": False}
    # pol == 1 degenerate boundary: tautology still holds
    s = cvc5.Solver(); s.setLogic("QF_NRA")
    R = s.getRealSort(); zero = s.mkReal(0); one = s.mkReal(1)
    a = s.mkConst(R,"a"); b_ = s.mkConst(R,"b_"); c = s.mkConst(R,"c"); d = s.mkConst(R,"d"); pol = s.mkConst(R,"pol")
    for v in (a,b_,c,d):
        s.assertFormula(s.mkTerm(Kind.GT, v, zero))
    s.assertFormula(s.mkTerm(Kind.EQUAL, pol, one))
    lhs = s.mkTerm(Kind.MULT, pol, a, c, pol, b_, d)
    rhs = s.mkTerm(Kind.MULT, s.mkTerm(Kind.MULT, pol, a, c), s.mkTerm(Kind.MULT, pol, b_, d))
    s.assertFormula(s.mkTerm(Kind.NOT, s.mkTerm(Kind.EQUAL, lhs, rhs)))
    return {"pol_eq_one_still_unsat": str(s.checkSat()) == "unsat"}

if __name__ == "__main__":
    results = {
        "name": "sim_fep_pair_active_inference_x_markov_blanket_cvc5_parity",
        "scope_note": "redundant-SMT parity for system_v4/probes/sim_fep_pair_active_inference_x_markov_blanket.py",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    results["PASS"] = all_pass(results)
    out = write_results(results["name"], results)
    print(f"PASS={results['PASS']}  ->  {out}")
    sys.exit(0 if results["PASS"] else 1)
