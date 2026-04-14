#!/usr/bin/env python3
"""
Sci-method deep -- Popper refutation: a tautology admits NO refuting witness
(z3 load-bearing). Falsifiability-by-probe is EXCLUDED for tautologies; UNSAT
of 'exists w with T(w) = false' is the formal statement.
"""
import json, os
from z3 import Solver, Bool, Bools, And, Or, Not, Implies, sat, unsat

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn",
     "rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_MANIFEST["z3"]["tried"] = True
for k in TOOL_MANIFEST:
    if not TOOL_MANIFEST[k]["tried"]:
        TOOL_MANIFEST[k]["reason"] = "not required for tautology UNSAT"


def run_positive_tests():
    r = {}
    p, q = Bools("p q")
    # Tautology: p OR NOT p
    s = Solver()
    s.add(Not(Or(p, Not(p))))
    r["law_of_excluded_middle_unrefutable"] = {"pass": s.check() == unsat}
    # Modus ponens tautology: (p AND (p -> q)) -> q
    s2 = Solver()
    s2.add(Not(Implies(And(p, Implies(p, q)), q)))
    r["modus_ponens_unrefutable"] = {"pass": s2.check() == unsat}
    return r


def run_negative_tests():
    r = {}
    p, q = Bools("p q")
    # Contingent claim p -> q: refuter exists (p=T, q=F)
    s = Solver()
    s.add(Not(Implies(p, q)))
    r["contingent_refutable"] = {"pass": s.check() == sat}
    return r


def run_boundary_tests():
    r = {}
    p = Bool("p")
    # Contradiction p AND NOT p: Popper says it is 'refuted everywhere' -- every w is a witness.
    s = Solver()
    s.add(And(p, Not(p)))
    r["contradiction_has_no_model"] = {"pass": s.check() == unsat}
    # Trivially true 'True' is unrefutable.
    s2 = Solver()
    s2.add(Not(True))
    r["true_unrefutable"] = {"pass": s2.check() == unsat}
    return r


if __name__ == "__main__":
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "UNSAT of negation proves unfalsifiability of tautology"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    pos, neg, bnd = run_positive_tests(), run_negative_tests(), run_boundary_tests()
    allpass = lambda d: all(v.get("pass", False) for v in d.values())
    ap = allpass(pos) and allpass(neg) and allpass(bnd)
    res = {"name": "sci_method_deep_popper_refutation_unsat_for_tautology",
           "classification": "canonical",
           "scope_note": "OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md",
           "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
           "positive": pos, "negative": neg, "boundary": bnd, "all_pass": ap}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "sci_method_deep_popper_refutation_unsat_for_tautology_results.json")
    with open(out, "w") as f: json.dump(res, f, indent=2, default=str)
    print(f"[{res['name']}] all_pass={ap} -> {out}")
