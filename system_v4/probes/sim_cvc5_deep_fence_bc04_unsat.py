#!/usr/bin/env python3
"""sim_cvc5_deep_fence_bc04_unsat

Scope: cvc5 load-bearing UNSAT proof of the BC04 fence (boundary-condition 4:
"no probe outcome may simultaneously commit to both polar branches"). Models
two boolean commitments b_pos, b_neg and a consistency fence b_pos XOR b_neg;
attempts to assert (b_pos AND b_neg). Exclusion = UNSAT.
"""
import os, json, cvc5
from cvc5 import Kind

NAME = "sim_cvc5_deep_fence_bc04_unsat"
SCOPE_NOTE = "BC04 polar-branch exclusion; cvc5 UNSAT certifies admissibility fence."

TOOL_MANIFEST = {"cvc5": {"tried": True, "used": True,
    "reason": "load-bearing UNSAT certificate of BC04 branch-exclusion fence"}}
TOOL_INTEGRATION_DEPTH = {"cvc5": "load_bearing"}

def _solver():
    s = cvc5.Solver(); s.setLogic("QF_UF"); return s

def _bc04(assert_both):
    s = _solver()
    B = s.getBooleanSort()
    bp = s.mkConst(B, "bp"); bn = s.mkConst(B, "bn")
    # fence: bp XOR bn  (exactly one branch)
    s.assertFormula(s.mkTerm(Kind.XOR, bp, bn))
    if assert_both:
        s.assertFormula(s.mkTerm(Kind.AND, bp, bn))
    return s.checkSat()

def run_positive_tests():
    r = _bc04(assert_both=True)
    return {"bc04_both_branches_unsat": {"pass": r.isUnsat()}}

def run_negative_tests():
    r = _bc04(assert_both=False)
    return {"bc04_single_branch_sat": {"pass": r.isSat()}}

def run_boundary_tests():
    # three-branch exactly-one fence with all three forced -> unsat
    s = _solver(); B = s.getBooleanSort()
    bp = s.mkConst(B,"bp"); bn = s.mkConst(B,"bn"); bm = s.mkConst(B,"bm")
    # exactly-one: (bp|bn|bm) AND pairwise not-both
    s.assertFormula(s.mkTerm(Kind.OR, bp, bn, bm))
    nbp_nbn = s.mkTerm(Kind.NOT, s.mkTerm(Kind.AND, bp, bn))
    nbp_nbm = s.mkTerm(Kind.NOT, s.mkTerm(Kind.AND, bp, bm))
    nbn_nbm = s.mkTerm(Kind.NOT, s.mkTerm(Kind.AND, bn, bm))
    s.assertFormula(nbp_nbn); s.assertFormula(nbp_nbm); s.assertFormula(nbn_nbm)
    s.assertFormula(bp); s.assertFormula(bn); s.assertFormula(bm)
    return {"bc04_three_branch_forced_unsat": {"pass": s.checkSat().isUnsat()}}

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
