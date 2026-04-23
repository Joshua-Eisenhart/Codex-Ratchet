#!/usr/bin/env python3
"""cvc5 parity sibling for sim_fep_pair_free_energy_x_markov_blanket.

scope_note: Re-encodes z3 Gibbs tangent lower-bound UNSAT from parent
system_v4/probes/sim_fep_pair_free_energy_x_markov_blanket.py in cvc5;
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

# F_lb = qi*(1 - pi/qi) + (1-qi)*(1 - (1-pi)/(1-qi))
#      = qi - pi + (1-qi) - (1-pi) = 0   (identically)
# So F_lb < -1e-9 is UNSAT. We verify in both.

def z3_check():
    s = z3.Solver()
    qi, pi_, qe, pe = z3.Reals("qi pi_ qe pe")
    s.add(qi>0, qi<1, pi_>0, pi_<1, qe>0, qe<1, pe>0, pe<1)
    F_lb = qi*(1 - pi_/qi) + (1 - qi)*(1 - (1 - pi_)/(1 - qi))
    s.add(F_lb < -1e-9)
    return s.check() == z3.unsat

def cvc5_check():
    s = cvc5.Solver(); s.setLogic("QF_NRA")
    R = s.getRealSort(); zero = s.mkReal(0); one = s.mkReal(1)
    qi = s.mkConst(R,"qi"); pi_ = s.mkConst(R,"pi_")
    s.assertFormula(s.mkTerm(Kind.GT, qi, zero)); s.assertFormula(s.mkTerm(Kind.LT, qi, one))
    s.assertFormula(s.mkTerm(Kind.GT, pi_, zero)); s.assertFormula(s.mkTerm(Kind.LT, pi_, one))
    one_m_qi = s.mkTerm(Kind.SUB, one, qi)
    one_m_pi = s.mkTerm(Kind.SUB, one, pi_)
    # term1 = qi*(1 - pi_/qi) = qi - pi_
    term1 = s.mkTerm(Kind.SUB, qi, pi_)
    # term2 = (1-qi)*(1 - (1-pi_)/(1-qi)) = (1-qi) - (1-pi_)
    term2 = s.mkTerm(Kind.SUB, one_m_qi, one_m_pi)
    F_lb = s.mkTerm(Kind.ADD, term1, term2)
    neg_eps = s.mkReal("-1/1000000000")
    s.assertFormula(s.mkTerm(Kind.LT, F_lb, neg_eps))
    return str(s.checkSat()) == "unsat"

def run_positive_tests():
    if z3 is None or cvc5 is None: return {"tools_available": False}
    zu, cu = z3_check(), cvc5_check()
    TOOL_MANIFEST["z3"]["used"]=True; TOOL_MANIFEST["z3"]["reason"]="cross-check UNSAT on Gibbs LB negativity"
    TOOL_MANIFEST["cvc5"]["used"]=True; TOOL_MANIFEST["cvc5"]["reason"]="load-bearing UNSAT parity witness"
    TOOL_INTEGRATION_DEPTH["z3"]="supportive"; TOOL_INTEGRATION_DEPTH["cvc5"]="load_bearing"
    return {"z3_unsat": zu, "cvc5_unsat": cu, "parity_both_unsat": zu and cu}

def run_negative_tests():
    if cvc5 is None: return {"skip": False}
    # Replace F_lb with pi_ - qi (valid sign reversal): F_lb < 0 now SAT.
    s = cvc5.Solver(); s.setLogic("QF_NRA")
    R = s.getRealSort(); zero = s.mkReal(0); one = s.mkReal(1)
    qi = s.mkConst(R,"qi"); pi_ = s.mkConst(R,"pi_")
    s.assertFormula(s.mkTerm(Kind.GT, qi, zero)); s.assertFormula(s.mkTerm(Kind.LT, qi, one))
    s.assertFormula(s.mkTerm(Kind.GT, pi_, zero)); s.assertFormula(s.mkTerm(Kind.LT, pi_, one))
    bad = s.mkTerm(Kind.SUB, pi_, qi)
    s.assertFormula(s.mkTerm(Kind.LT, bad, s.mkReal("-1/1000000000")))
    return {"wrong_sign_form_becomes_sat": str(s.checkSat()) == "sat"}

def run_boundary_tests():
    if cvc5 is None: return {"skip": False}
    # Boundary qi=pi_: F_lb identically 0, so F_lb < -eps UNSAT.
    s = cvc5.Solver(); s.setLogic("QF_NRA")
    R = s.getRealSort(); zero = s.mkReal(0); one = s.mkReal(1)
    qi = s.mkConst(R,"qi"); pi_ = s.mkConst(R,"pi_")
    s.assertFormula(s.mkTerm(Kind.GT, qi, zero)); s.assertFormula(s.mkTerm(Kind.LT, qi, one))
    s.assertFormula(s.mkTerm(Kind.EQUAL, qi, pi_))
    term1 = s.mkTerm(Kind.SUB, qi, pi_)
    term2 = s.mkTerm(Kind.SUB, s.mkTerm(Kind.SUB, one, qi), s.mkTerm(Kind.SUB, one, pi_))
    F_lb = s.mkTerm(Kind.ADD, term1, term2)
    s.assertFormula(s.mkTerm(Kind.LT, F_lb, s.mkReal("-1/1000000000")))
    return {"qi_eq_pi_boundary_still_unsat": str(s.checkSat()) == "unsat"}

if __name__ == "__main__":
    results = {
        "name": "sim_fep_pair_free_energy_x_markov_blanket_cvc5_parity",
        "scope_note": "redundant-SMT parity for system_v4/probes/sim_fep_pair_free_energy_x_markov_blanket.py",
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
