#!/usr/bin/env python3
"""cvc5 parity sibling for sim_fep_pair_free_energy_x_engine_coupling.

scope_note: Re-encodes z3 probe-positivity UNSAT from parent
system_v4/probes/sim_fep_pair_free_energy_x_engine_coupling.py in cvc5;
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
    q0, p0_, p1_, k = z3.Reals("q0 p0_ p1_ k")
    s.add(q0>0, q0<1, p0_>0, p0_<1, p1_>0, p1_<1, k>=0, k<=1)
    pk = (1-k)*p0_ + k*p1_
    s.add(pk <= 0)
    return s.check() == z3.unsat

def cvc5_build(s, pk_leq_zero=True):
    R = s.getRealSort(); zero = s.mkReal(0); one = s.mkReal(1)
    q0 = s.mkConst(R,"q0"); p0_ = s.mkConst(R,"p0_"); p1_ = s.mkConst(R,"p1_"); k = s.mkConst(R,"k")
    for v in (q0,p0_,p1_):
        s.assertFormula(s.mkTerm(Kind.GT, v, zero))
        s.assertFormula(s.mkTerm(Kind.LT, v, one))
    s.assertFormula(s.mkTerm(Kind.GEQ, k, zero))
    s.assertFormula(s.mkTerm(Kind.LEQ, k, one))
    one_m_k = s.mkTerm(Kind.SUB, one, k)
    pk = s.mkTerm(Kind.ADD,
                  s.mkTerm(Kind.MULT, one_m_k, p0_),
                  s.mkTerm(Kind.MULT, k, p1_))
    if pk_leq_zero:
        s.assertFormula(s.mkTerm(Kind.LEQ, pk, zero))
    return pk

def cvc5_check():
    s = cvc5.Solver(); s.setLogic("QF_NRA")
    cvc5_build(s, True)
    return str(s.checkSat()) == "unsat"

def run_positive_tests():
    if z3 is None or cvc5 is None: return {"tools_available": False}
    zu, cu = z3_check(), cvc5_check()
    TOOL_MANIFEST["z3"]["used"]=True; TOOL_MANIFEST["z3"]["reason"]="cross-check UNSAT on pk<=0 under convex combo"
    TOOL_MANIFEST["cvc5"]["used"]=True; TOOL_MANIFEST["cvc5"]["reason"]="load-bearing UNSAT parity witness"
    TOOL_INTEGRATION_DEPTH["z3"]="supportive"; TOOL_INTEGRATION_DEPTH["cvc5"]="load_bearing"
    return {"z3_unsat": zu, "cvc5_unsat": cu, "parity_both_unsat": zu and cu}

def run_negative_tests():
    if cvc5 is None: return {"skip": False}
    # Drop p0_,p1_ positivity: then pk<=0 becomes SAT
    s = cvc5.Solver(); s.setLogic("QF_NRA")
    R = s.getRealSort(); zero = s.mkReal(0); one = s.mkReal(1)
    q0 = s.mkConst(R,"q0"); p0_ = s.mkConst(R,"p0_"); p1_ = s.mkConst(R,"p1_"); k = s.mkConst(R,"k")
    s.assertFormula(s.mkTerm(Kind.GT, q0, zero)); s.assertFormula(s.mkTerm(Kind.LT, q0, one))
    s.assertFormula(s.mkTerm(Kind.GEQ, k, zero)); s.assertFormula(s.mkTerm(Kind.LEQ, k, one))
    pk = s.mkTerm(Kind.ADD,
                  s.mkTerm(Kind.MULT, s.mkTerm(Kind.SUB, one, k), p0_),
                  s.mkTerm(Kind.MULT, k, p1_))
    s.assertFormula(s.mkTerm(Kind.LEQ, pk, zero))
    return {"drop_p_positivity_becomes_sat": str(s.checkSat()) == "sat"}

def run_boundary_tests():
    if cvc5 is None: return {"skip": False}
    # k=0 edge -> pk = p0_ > 0; pk<=0 still UNSAT
    s = cvc5.Solver(); s.setLogic("QF_NRA")
    R = s.getRealSort(); zero = s.mkReal(0); one = s.mkReal(1)
    q0 = s.mkConst(R,"q0"); p0_ = s.mkConst(R,"p0_"); p1_ = s.mkConst(R,"p1_"); k = s.mkConst(R,"k")
    for v in (q0,p0_,p1_):
        s.assertFormula(s.mkTerm(Kind.GT, v, zero)); s.assertFormula(s.mkTerm(Kind.LT, v, one))
    s.assertFormula(s.mkTerm(Kind.EQUAL, k, zero))
    pk = s.mkTerm(Kind.ADD,
                  s.mkTerm(Kind.MULT, s.mkTerm(Kind.SUB, one, k), p0_),
                  s.mkTerm(Kind.MULT, k, p1_))
    s.assertFormula(s.mkTerm(Kind.LEQ, pk, zero))
    return {"k_zero_edge_still_unsat": str(s.checkSat()) == "unsat"}

if __name__ == "__main__":
    results = {
        "name": "sim_fep_pair_free_energy_x_engine_coupling_cvc5_parity",
        "scope_note": "redundant-SMT parity for system_v4/probes/sim_fep_pair_free_energy_x_engine_coupling.py",
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
