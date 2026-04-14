#!/usr/bin/env python3
"""cvc5 parity sibling for sim_fep_pair_active_inference_x_generative_model.

scope_note: Re-encodes z3 constraint from parent
system_v4/probes/sim_fep_pair_active_inference_x_generative_model.py in cvc5;
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

EPS = 1e-9

def z3_check():
    s = z3.Solver()
    f0, f1 = z3.Reals("f0 f1")
    s.add(f0 >= 0, f1 >= 0, f0 < f1)
    s.add(f1 <= f0 - EPS)
    return s.check() == z3.unsat

def cvc5_check():
    s = cvc5.Solver(); s.setLogic("QF_LRA")
    R = s.getRealSort(); zero = s.mkReal(0)
    f0 = s.mkConst(R,"f0"); f1 = s.mkConst(R,"f1")
    eps = s.mkReal("1/1000000000")
    s.assertFormula(s.mkTerm(Kind.GEQ, f0, zero))
    s.assertFormula(s.mkTerm(Kind.GEQ, f1, zero))
    s.assertFormula(s.mkTerm(Kind.LT, f0, f1))
    s.assertFormula(s.mkTerm(Kind.LEQ, f1, s.mkTerm(Kind.SUB, f0, eps)))
    return str(s.checkSat()) == "unsat"

def run_positive_tests():
    if z3 is None or cvc5 is None: return {"tools_available": False}
    zu, cu = z3_check(), cvc5_check()
    TOOL_MANIFEST["z3"]["used"]=True; TOOL_MANIFEST["z3"]["reason"]="cross-check UNSAT on argmin ordering"
    TOOL_MANIFEST["cvc5"]["used"]=True; TOOL_MANIFEST["cvc5"]["reason"]="load-bearing UNSAT parity witness"
    TOOL_INTEGRATION_DEPTH["z3"]="supportive"; TOOL_INTEGRATION_DEPTH["cvc5"]="load_bearing"
    return {"z3_unsat": zu, "cvc5_unsat": cu, "parity_both_unsat": zu and cu}

def run_negative_tests():
    if cvc5 is None: return {"skip": False}
    # Remove ordering constraint: contradiction vanishes -> SAT
    s = cvc5.Solver(); s.setLogic("QF_LRA")
    R = s.getRealSort(); zero = s.mkReal(0)
    f0 = s.mkConst(R,"f0"); f1 = s.mkConst(R,"f1")
    eps = s.mkReal("1/1000000000")
    s.assertFormula(s.mkTerm(Kind.GEQ, f0, zero))
    s.assertFormula(s.mkTerm(Kind.GEQ, f1, zero))
    s.assertFormula(s.mkTerm(Kind.LEQ, f1, s.mkTerm(Kind.SUB, f0, eps)))
    return {"drop_ordering_becomes_sat": str(s.checkSat()) == "sat"}

def run_boundary_tests():
    if cvc5 is None: return {"skip": False}
    # Boundary: f0 == f1 is SAT on domain f0>=0,f1>=0 alone
    s = cvc5.Solver(); s.setLogic("QF_LRA")
    R = s.getRealSort(); zero = s.mkReal(0)
    f0 = s.mkConst(R,"f0"); f1 = s.mkConst(R,"f1")
    s.assertFormula(s.mkTerm(Kind.GEQ, f0, zero))
    s.assertFormula(s.mkTerm(Kind.GEQ, f1, zero))
    s.assertFormula(s.mkTerm(Kind.EQUAL, f0, f1))
    return {"f0_eq_f1_sat_at_boundary": str(s.checkSat()) == "sat"}

if __name__ == "__main__":
    results = {
        "name": "sim_fep_pair_active_inference_x_generative_model_cvc5_parity",
        "scope_note": "redundant-SMT parity for system_v4/probes/sim_fep_pair_active_inference_x_generative_model.py",
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
