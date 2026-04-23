#!/usr/bin/env python3
"""cvc5 parity sibling for sim_science_method_refutation_probe.

scope_note: Re-encodes the three refutation-probe claims from parent
system_v4/probes/sim_science_method_refutation_probe.py in cvc5 and
asserts z3<->cvc5 parity (both report same sat/unsat for each claim).
Does not modify parent.
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

# Claims (same as parent):
#  A) square_nonneg: ∃ int x, x*x<0   (expected unsat -> survives)
#  B) positivity_refuted: ∃ int x, ¬(x>0)   (expected sat -> refuted)
#  C) vacuous: False ∧ x==x   (expected unsat)

def z3_claims():
    out = {}
    s = z3.Solver(); x = z3.Int("x"); s.add(x*x < 0); out["A"] = str(s.check())
    s = z3.Solver(); x = z3.Int("x"); s.add(z3.Not(x > 0)); out["B"] = str(s.check())
    s = z3.Solver(); x = z3.Int("x"); s.add(z3.And(z3.BoolVal(False), x == x)); out["C"] = str(s.check())
    return out

def cvc5_claims():
    out = {}
    # A
    s = cvc5.Solver(); s.setLogic("QF_NIA")
    I = s.getIntegerSort(); zero = s.mkInteger(0)
    x = s.mkConst(I, "x")
    s.assertFormula(s.mkTerm(Kind.LT, s.mkTerm(Kind.MULT, x, x), zero))
    out["A"] = str(s.checkSat())
    # B
    s = cvc5.Solver(); s.setLogic("QF_LIA")
    I = s.getIntegerSort(); zero = s.mkInteger(0)
    x = s.mkConst(I, "x")
    s.assertFormula(s.mkTerm(Kind.NOT, s.mkTerm(Kind.GT, x, zero)))
    out["B"] = str(s.checkSat())
    # C
    s = cvc5.Solver(); s.setLogic("QF_LIA")
    I = s.getIntegerSort()
    x = s.mkConst(I, "x")
    s.assertFormula(s.mkTerm(Kind.AND, s.mkBoolean(False),
                             s.mkTerm(Kind.EQUAL, x, x)))
    out["C"] = str(s.checkSat())
    return out

def run_positive_tests():
    if z3 is None or cvc5 is None: return {"tools_available": False}
    z = z3_claims(); c = cvc5_claims()
    TOOL_MANIFEST["z3"]["used"]=True; TOOL_MANIFEST["z3"]["reason"]="cross-check refutation-probe claims"
    TOOL_MANIFEST["cvc5"]["used"]=True; TOOL_MANIFEST["cvc5"]["reason"]="load-bearing parity on refutation-probe claims"
    TOOL_INTEGRATION_DEPTH["z3"]="supportive"; TOOL_INTEGRATION_DEPTH["cvc5"]="load_bearing"
    return {
        "A_z3_unsat": z["A"]=="unsat", "A_cvc5_unsat": c["A"]=="unsat", "A_parity": z["A"]==c["A"]=="unsat",
        "B_z3_sat": z["B"]=="sat",     "B_cvc5_sat": c["B"]=="sat",     "B_parity": z["B"]==c["B"]=="sat",
        "C_z3_unsat": z["C"]=="unsat", "C_cvc5_unsat": c["C"]=="unsat", "C_parity": z["C"]==c["C"]=="unsat",
    }

def run_negative_tests():
    if cvc5 is None: return {"skip": False}
    # Flip claim B to (x>0): over integers ∃x: x>0 is SAT (refutation harness returns same).
    s = cvc5.Solver(); s.setLogic("QF_LIA")
    I = s.getIntegerSort(); zero = s.mkInteger(0)
    x = s.mkConst(I,"x")
    s.assertFormula(s.mkTerm(Kind.GT, x, zero))
    return {"flipped_claim_sat": str(s.checkSat()) == "sat"}

def run_boundary_tests():
    if cvc5 is None: return {"skip": False}
    # True ∧ x==x is trivially SAT on ints.
    s = cvc5.Solver(); s.setLogic("QF_LIA")
    I = s.getIntegerSort()
    x = s.mkConst(I,"x")
    s.assertFormula(s.mkTerm(Kind.AND, s.mkBoolean(True),
                             s.mkTerm(Kind.EQUAL, x, x)))
    return {"true_tautology_sat": str(s.checkSat()) == "sat"}

if __name__ == "__main__":
    results = {
        "name": "sim_science_method_refutation_probe_cvc5_parity",
        "scope_note": "redundant-SMT parity for system_v4/probes/sim_science_method_refutation_probe.py",
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
