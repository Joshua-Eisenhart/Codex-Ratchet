#!/usr/bin/env python3
"""sim_cvc5_deep_g_reduction_chain_sat

Scope: cvc5 load-bearing SAT witness for a G-tower reduction chain: integer
levels g0>g1>g2>=0 with step differences d_i in {1,2}. Positive: SAT chain
exists. Negative: forcing an ascending step is UNSAT. Boundary: minimum-length
chain.
"""
import os, json, cvc5
from cvc5 import Kind

NAME = "sim_cvc5_deep_g_reduction_chain_sat"
SCOPE_NOTE = "G-tower reduction chain admissibility; cvc5 SAT/UNSAT under monotone fence."
TOOL_MANIFEST = {"cvc5": {"tried": True, "used": True,
    "reason": "load-bearing QF_LIA SAT witness and ascending-step UNSAT"}}
TOOL_INTEGRATION_DEPTH = {"cvc5": "load_bearing"}

def _solver():
    s = cvc5.Solver(); s.setOption("produce-models","true"); s.setLogic("QF_LIA"); return s

def _chain(ascending=False, min_len=False):
    s = _solver(); I = s.getIntegerSort()
    g = [s.mkConst(I, f"g{i}") for i in range(3)]
    zero = s.mkInteger(0); one = s.mkInteger(1); two = s.mkInteger(2)
    for gi in g:
        s.assertFormula(s.mkTerm(Kind.GEQ, gi, zero))
    for i in range(2):
        d = s.mkTerm(Kind.SUB, g[i], g[i+1])
        # step in {1,2}: enforces descent
        s.assertFormula(s.mkTerm(Kind.OR,
            s.mkTerm(Kind.EQUAL, d, one),
            s.mkTerm(Kind.EQUAL, d, two)))
        if ascending:
            # contradiction: step>0 AND g[i] < g[i+1]
            s.assertFormula(s.mkTerm(Kind.LT, g[i], g[i+1]))
    if min_len:
        s.assertFormula(s.mkTerm(Kind.EQUAL, g[0], s.mkInteger(2)))
        s.assertFormula(s.mkTerm(Kind.EQUAL, g[2], zero))
    return s.checkSat()

def run_positive_tests():
    return {"g_reduction_chain_sat": {"pass": _chain().isSat()}}

def run_negative_tests():
    return {"g_ascending_unsat": {"pass": _chain(ascending=True).isUnsat()}}

def run_boundary_tests():
    return {"g_min_length_chain_sat": {"pass": _chain(min_len=True).isSat()}}

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
