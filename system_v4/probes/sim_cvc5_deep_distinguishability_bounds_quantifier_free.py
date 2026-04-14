#!/usr/bin/env python3
"""sim_cvc5_deep_distinguishability_bounds_quantifier_free

Scope: cvc5 load-bearing check of distinguishability admissibility bounds under a
quantifier-free real-arithmetic encoding. Probes whether candidate probe-outcome
vectors (p0,p1) can be jointly indistinguishable (|p0-p1| < eps) while also
satisfying a separation fence (|p0-p1| >= delta). UNSAT is the exclusion claim.

This is not a construction: cvc5 UNSAT excludes the joint admissibility of
"indistinguishable" and "fence-separated" on the same pair. No numpy fallback.
"""
import os, json, cvc5
from cvc5 import Kind

NAME = "sim_cvc5_deep_distinguishability_bounds_quantifier_free"
SCOPE_NOTE = (
    "cvc5 QF_LRA; excludes pairs that are simultaneously indistinguishable "
    "(|p0-p1|<eps) and fence-separated (|p0-p1|>=delta) when delta>=eps."
)

TOOL_MANIFEST = {
    "cvc5": {"tried": True, "used": True,
             "reason": "load-bearing SMT UNSAT proof of joint admissibility exclusion"},
}
TOOL_INTEGRATION_DEPTH = {"cvc5": "load_bearing"}

def _solver():
    s = cvc5.Solver()
    s.setOption("produce-models", "true")
    s.setLogic("QF_LRA")
    return s

def _check(eps, delta):
    s = _solver()
    R = s.getRealSort()
    p0 = s.mkConst(R, "p0"); p1 = s.mkConst(R, "p1")
    diff = s.mkTerm(Kind.SUB, p0, p1)
    neg = s.mkTerm(Kind.NEG, diff)
    # |diff| = ite(diff>=0, diff, -diff)
    zero = s.mkReal(0)
    absd = s.mkTerm(Kind.ITE, s.mkTerm(Kind.GEQ, diff, zero), diff, neg)
    s.assertFormula(s.mkTerm(Kind.LT, absd, s.mkReal(str(eps))))
    s.assertFormula(s.mkTerm(Kind.GEQ, absd, s.mkReal(str(delta))))
    r = s.checkSat()
    return r.isUnsat(), r.isSat()

def run_positive_tests():
    # delta >= eps => must be UNSAT (exclusion)
    u, _ = _check("1/10", "1/10")
    u2, _ = _check("1/100", "1/2")
    return {"fence_equal_eps_unsat": {"pass": u},
            "fence_gt_eps_unsat":    {"pass": u2}}

def run_negative_tests():
    # delta < eps => SAT (no exclusion)
    u, sat = _check("1/2", "1/10")
    return {"fence_lt_eps_sat": {"pass": (not u) and sat}}

def run_boundary_tests():
    # tiny eps, tiny delta equal => UNSAT
    u, _ = _check("1/1000000000", "1/1000000000")
    return {"tiny_equal_unsat": {"pass": u}}

if __name__ == "__main__":
    results = {
        "name": NAME,
        "scope_note": SCOPE_NOTE,
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out}")
