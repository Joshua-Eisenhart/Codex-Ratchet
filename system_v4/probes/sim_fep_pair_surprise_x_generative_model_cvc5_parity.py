#!/usr/bin/env python3
"""cvc5 parity sibling for sim_fep_pair_surprise_x_generative_model.

scope_note: Re-encodes z3 UNSAT on p in (0,1] ∧ p>1 from parent
system_v4/probes/sim_fep_pair_surprise_x_generative_model.py in cvc5;
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
    p = z3.Real("p")
    s.add(p > 0, p <= 1)
    s.add(p > 1)
    return s.check() == z3.unsat

def cvc5_check():
    s = cvc5.Solver(); s.setLogic("QF_LRA")
    R = s.getRealSort(); zero = s.mkReal(0); one = s.mkReal(1)
    p = s.mkConst(R,"p")
    s.assertFormula(s.mkTerm(Kind.GT, p, zero))
    s.assertFormula(s.mkTerm(Kind.LEQ, p, one))
    s.assertFormula(s.mkTerm(Kind.GT, p, one))
    return str(s.checkSat()) == "unsat"

def run_positive_tests():
    if z3 is None or cvc5 is None: return {"tools_available": False}
    zu, cu = z3_check(), cvc5_check()
    TOOL_MANIFEST["z3"]["used"]=True; TOOL_MANIFEST["z3"]["reason"]="cross-check UNSAT on -log p<0 admissibility"
    TOOL_MANIFEST["cvc5"]["used"]=True; TOOL_MANIFEST["cvc5"]["reason"]="load-bearing UNSAT parity witness"
    TOOL_INTEGRATION_DEPTH["z3"]="supportive"; TOOL_INTEGRATION_DEPTH["cvc5"]="load_bearing"
    return {"z3_unsat": zu, "cvc5_unsat": cu, "parity_both_unsat": zu and cu}

def run_negative_tests():
    if cvc5 is None: return {"skip": False}
    # Drop p<=1: then p>1 with p>0 is SAT
    s = cvc5.Solver(); s.setLogic("QF_LRA")
    R = s.getRealSort(); zero = s.mkReal(0); one = s.mkReal(1)
    p = s.mkConst(R,"p")
    s.assertFormula(s.mkTerm(Kind.GT, p, zero))
    s.assertFormula(s.mkTerm(Kind.GT, p, one))
    return {"drop_upper_bound_becomes_sat": str(s.checkSat()) == "sat"}

def run_boundary_tests():
    if cvc5 is None: return {"skip": False}
    # Boundary p == 1: p>1 UNSAT.
    s = cvc5.Solver(); s.setLogic("QF_LRA")
    R = s.getRealSort(); one = s.mkReal(1)
    p = s.mkConst(R,"p")
    s.assertFormula(s.mkTerm(Kind.EQUAL, p, one))
    s.assertFormula(s.mkTerm(Kind.GT, p, one))
    return {"p_eq_one_boundary_unsat": str(s.checkSat()) == "unsat"}

if __name__ == "__main__":
    results = {
        "name": "sim_fep_pair_surprise_x_generative_model_cvc5_parity",
        "scope_note": "redundant-SMT parity for system_v4/probes/sim_fep_pair_surprise_x_generative_model.py",
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
