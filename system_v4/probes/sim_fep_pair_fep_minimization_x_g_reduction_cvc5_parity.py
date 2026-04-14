#!/usr/bin/env python3
"""cvc5 parity sibling for sim_fep_pair_fep_minimization_x_g_reduction.

scope_note: Re-encodes z3 direct-contradiction UNSAT from parent
system_v4/probes/sim_fep_pair_fep_minimization_x_g_reduction.py in cvc5;
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
    qa, qb, qab = z3.Reals("qa qb qab")
    s.add(qa > 0, qa < 1, qb > 0, qb < 1)
    s.add(qab == qa*qb)
    s.add(qab != qa*qb)
    return s.check() == z3.unsat

def cvc5_check():
    s = cvc5.Solver(); s.setLogic("QF_NRA")
    R = s.getRealSort(); zero = s.mkReal(0); one = s.mkReal(1)
    qa = s.mkConst(R,"qa"); qb = s.mkConst(R,"qb"); qab = s.mkConst(R,"qab")
    s.assertFormula(s.mkTerm(Kind.GT, qa, zero)); s.assertFormula(s.mkTerm(Kind.LT, qa, one))
    s.assertFormula(s.mkTerm(Kind.GT, qb, zero)); s.assertFormula(s.mkTerm(Kind.LT, qb, one))
    prod = s.mkTerm(Kind.MULT, qa, qb)
    s.assertFormula(s.mkTerm(Kind.EQUAL, qab, prod))
    s.assertFormula(s.mkTerm(Kind.NOT, s.mkTerm(Kind.EQUAL, qab, prod)))
    return str(s.checkSat()) == "unsat"

def run_positive_tests():
    if z3 is None or cvc5 is None: return {"tools_available": False}
    zu, cu = z3_check(), cvc5_check()
    TOOL_MANIFEST["z3"]["used"]=True; TOOL_MANIFEST["z3"]["reason"]="cross-check UNSAT on G-reduction contradiction"
    TOOL_MANIFEST["cvc5"]["used"]=True; TOOL_MANIFEST["cvc5"]["reason"]="load-bearing UNSAT parity witness"
    TOOL_INTEGRATION_DEPTH["z3"]="supportive"; TOOL_INTEGRATION_DEPTH["cvc5"]="load_bearing"
    return {"z3_unsat": zu, "cvc5_unsat": cu, "parity_both_unsat": zu and cu}

def run_negative_tests():
    if cvc5 is None: return {"skip": False}
    # Drop the equality clause: the disequality alone is SAT.
    s = cvc5.Solver(); s.setLogic("QF_NRA")
    R = s.getRealSort(); zero = s.mkReal(0); one = s.mkReal(1)
    qa = s.mkConst(R,"qa"); qb = s.mkConst(R,"qb"); qab = s.mkConst(R,"qab")
    s.assertFormula(s.mkTerm(Kind.GT, qa, zero)); s.assertFormula(s.mkTerm(Kind.LT, qa, one))
    s.assertFormula(s.mkTerm(Kind.GT, qb, zero)); s.assertFormula(s.mkTerm(Kind.LT, qb, one))
    s.assertFormula(s.mkTerm(Kind.NOT,
        s.mkTerm(Kind.EQUAL, qab, s.mkTerm(Kind.MULT, qa, qb))))
    return {"drop_equality_becomes_sat": str(s.checkSat()) == "sat"}

def run_boundary_tests():
    if cvc5 is None: return {"skip": False}
    # Boundary qa=qb=0.5 consistent with qab=0.25; contradiction clause still UNSAT.
    s = cvc5.Solver(); s.setLogic("QF_NRA")
    R = s.getRealSort()
    half = s.mkReal("1/2"); quarter = s.mkReal("1/4")
    qa = s.mkConst(R,"qa"); qb = s.mkConst(R,"qb"); qab = s.mkConst(R,"qab")
    s.assertFormula(s.mkTerm(Kind.EQUAL, qa, half))
    s.assertFormula(s.mkTerm(Kind.EQUAL, qb, half))
    s.assertFormula(s.mkTerm(Kind.EQUAL, qab, quarter))
    s.assertFormula(s.mkTerm(Kind.NOT,
        s.mkTerm(Kind.EQUAL, qab, s.mkTerm(Kind.MULT, qa, qb))))
    return {"half_half_boundary_still_unsat": str(s.checkSat()) == "unsat"}

if __name__ == "__main__":
    results = {
        "name": "sim_fep_pair_fep_minimization_x_g_reduction_cvc5_parity",
        "scope_note": "redundant-SMT parity for system_v4/probes/sim_fep_pair_fep_minimization_x_g_reduction.py",
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
