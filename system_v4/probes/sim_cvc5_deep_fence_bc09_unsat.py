#!/usr/bin/env python3
"""sim_cvc5_deep_fence_bc09_unsat

Scope: cvc5 load-bearing UNSAT on BC09 fence ("sum of probe weights across a
coupled pair cannot exceed unit budget while each stays non-negative and both
are simultaneously saturated at w>=0.6"). Encodes QF_LRA constraints; UNSAT is
the exclusion claim on over-saturated coupled pairs.
"""
import os, json, cvc5
from cvc5 import Kind

NAME = "sim_cvc5_deep_fence_bc09_unsat"
SCOPE_NOTE = "BC09 weight-budget fence; cvc5 UNSAT excludes over-saturated coupled pairs."
TOOL_MANIFEST = {"cvc5": {"tried": True, "used": True,
    "reason": "load-bearing QF_LRA UNSAT of BC09 saturation fence"}}
TOOL_INTEGRATION_DEPTH = {"cvc5": "load_bearing"}

def _solver():
    s = cvc5.Solver(); s.setLogic("QF_LRA"); return s

def _check(sat_thresh, budget):
    s = _solver(); R = s.getRealSort()
    w1 = s.mkConst(R,"w1"); w2 = s.mkConst(R,"w2")
    zero = s.mkReal(0)
    s.assertFormula(s.mkTerm(Kind.GEQ, w1, zero))
    s.assertFormula(s.mkTerm(Kind.GEQ, w2, zero))
    s.assertFormula(s.mkTerm(Kind.LEQ, s.mkTerm(Kind.ADD, w1, w2), s.mkReal(str(budget))))
    s.assertFormula(s.mkTerm(Kind.GEQ, w1, s.mkReal(str(sat_thresh))))
    s.assertFormula(s.mkTerm(Kind.GEQ, w2, s.mkReal(str(sat_thresh))))
    return s.checkSat()

def run_positive_tests():
    # 0.6 + 0.6 > 1.0  => UNSAT
    return {"bc09_double_sat_unsat": {"pass": _check("0.6","1.0").isUnsat()},
            "bc09_large_thresh_unsat": {"pass": _check("0.9","1.0").isUnsat()}}

def run_negative_tests():
    # 0.4 + 0.4 <= 1.0  => SAT
    return {"bc09_moderate_sat_sat": {"pass": _check("0.4","1.0").isSat()}}

def run_boundary_tests():
    # threshold exactly half of budget => SAT (boundary equality)
    return {"bc09_exact_half_sat": {"pass": _check("0.5","1.0").isSat()}}

if __name__ == "__main__":
    results = {"name": NAME, "scope_note": SCOPE_NOTE, "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(), "negative": run_negative_tests(),
        "boundary": run_boundary_tests()}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out,"w") as f: json.dump(results,f,indent=2,default=str)
    print(f"Results written to {out}")
