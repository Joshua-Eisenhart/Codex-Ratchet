#!/usr/bin/env python3
"""cvc5 parity sibling for sim_fep_pair_surprise_x_precision.

scope_note: Re-encodes the z3 admissibility constraint from the parent
system_v4/probes/sim_fep_pair_surprise_x_precision.py in cvc5 and asserts
z3<->cvc5 parity (both UNSAT). Strengthens UNSAT evidence by
redundant-SMT cross-check. Does not modify the parent.
"""
import os, sys
from _cvc5_parity_helper import write_results, all_pass

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "z3":   {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {"pytorch": None, "z3": None, "cvc5": None}

try:
    import z3
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    z3 = None
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5
    from cvc5 import Kind
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    cvc5 = None
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"


def z3_check():
    s = z3.Solver()
    pi_v, ee = z3.Reals("pi_v ee")
    s.add(pi_v > 0, ee*ee >= 0)
    s.add(pi_v * ee*ee < 0)
    return s.check() == z3.unsat

def cvc5_check():
    s = cvc5.Solver(); s.setLogic("QF_NRA")
    R = s.getRealSort(); zero = s.mkReal(0)
    pi_v = s.mkConst(R, "pi_v"); ee = s.mkConst(R, "ee")
    ee2 = s.mkTerm(Kind.MULT, ee, ee)
    s.assertFormula(s.mkTerm(Kind.GT, pi_v, zero))
    s.assertFormula(s.mkTerm(Kind.GEQ, ee2, zero))
    s.assertFormula(s.mkTerm(Kind.LT, s.mkTerm(Kind.MULT, pi_v, ee2), zero))
    return str(s.checkSat()) == "unsat"

def run_positive_tests():
    r = {}
    if z3 is None or cvc5 is None:
        r["tools_available"] = False
        return r
    zu = z3_check(); cu = cvc5_check()
    r["z3_unsat"] = zu
    r["cvc5_unsat"] = cu
    r["parity_both_unsat"] = (zu and cu)
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "cross-check: UNSAT on pi*e^2<0 under pi>0"
    TOOL_MANIFEST["cvc5"]["used"] = True
    TOOL_MANIFEST["cvc5"]["reason"] = "load-bearing UNSAT on same encoding, parity witness"
    TOOL_INTEGRATION_DEPTH["z3"] = "supportive"
    TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
    return r

def run_negative_tests():
    r = {}
    if cvc5 is None: return {"skip": False}
    # Drop the admissibility fence pi>0: then pi*e^2<0 becomes SAT (take pi<0, e!=0).
    s = cvc5.Solver(); s.setLogic("QF_NRA")
    R = s.getRealSort(); zero = s.mkReal(0)
    pi_v = s.mkConst(R, "pi_v"); ee = s.mkConst(R, "ee")
    ee2 = s.mkTerm(Kind.MULT, ee, ee)
    s.assertFormula(s.mkTerm(Kind.GEQ, ee2, zero))
    s.assertFormula(s.mkTerm(Kind.LT, s.mkTerm(Kind.MULT, pi_v, ee2), zero))
    r["dropping_pi_positive_becomes_sat"] = str(s.checkSat()) == "sat"
    return r

def run_boundary_tests():
    r = {}
    if cvc5 is None: return {"skip": False}
    # Boundary: pi*e^2 == 0 is SAT (e=0 witness) but pi*e^2<0 still UNSAT under pi>0.
    s = cvc5.Solver(); s.setLogic("QF_NRA")
    R = s.getRealSort(); zero = s.mkReal(0)
    pi_v = s.mkConst(R, "pi_v"); ee = s.mkConst(R, "ee")
    s.assertFormula(s.mkTerm(Kind.GT, pi_v, zero))
    s.assertFormula(s.mkTerm(Kind.EQUAL,
        s.mkTerm(Kind.MULT, pi_v, s.mkTerm(Kind.MULT, ee, ee)), zero))
    r["pi_e2_eq_zero_sat_at_boundary"] = str(s.checkSat()) == "sat"
    return r

if __name__ == "__main__":
    results = {
        "name": "sim_fep_pair_surprise_x_precision_cvc5_parity",
        "scope_note": "redundant-SMT parity for system_v4/probes/sim_fep_pair_surprise_x_precision.py",
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
