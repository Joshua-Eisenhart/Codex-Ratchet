#!/usr/bin/env python3
"""sim_couple_holodeck_fep -- pairwise coupling of {holodeck, fep}.

Coupling axiom: Markov blanket CI is the observer/world separation that
makes a projection quotient well-defined; without CI, the quotient leaks.
  coupling := projection_quotient -> markov_blanket_ci
"""
from _couple_common import run_pair, write_results

NAME = "sim_couple_holodeck_fep"
classification = "canonical"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "pairwise coupling enumeration and local predicate checks"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing witness for projection_quotient AND markov_blanket_ci -> boundary"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "z3": "load_bearing",
}

EXTRA = ["blanket_matches_projection_boundary"]

def coupling_py(e):
    return (not (e["projection_quotient"] and e["markov_blanket_ci"])) or e["blanket_matches_projection_boundary"]

def coupling_z3():
    from z3 import Implies, And
    return [lambda e: Implies(And(e["projection_quotient"], e["markov_blanket_ci"]), e["blanket_matches_projection_boundary"])]

if __name__ == "__main__":
    r = run_pair(
        NAME, "holodeck", "fep",
        coupling_py, coupling_z3(),
        "projection_quotient AND markov_blanket_ci => blanket_matches_projection_boundary (misaligned blanket excluded)",
        extra_atoms=EXTRA,
    )
    r["classification"] = classification
    r["tool_manifest"] = TOOL_MANIFEST
    r["tool_integration_depth"] = TOOL_INTEGRATION_DEPTH
    p = write_results(NAME, r)
    print(f"{NAME}: pass={r['overall_pass']} interacting={r['interacting']} additive={r['additive']} -> {p}")
