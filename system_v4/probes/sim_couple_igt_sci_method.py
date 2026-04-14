#!/usr/bin/env python3
"""sim_couple_igt_sci_method -- pairwise coupling of {igt, sci_method}.

Additive coupling: igt payoff admissibility and sci_method falsifiability
operate on disjoint atom sets with no cross-clause required under the
minimal shell-local axioms. Coupling clause is TRUE (vacuous); test that
this is genuinely additive (admissible_joint == intersection).
"""
from _couple_common import run_pair, write_results

NAME = "sim_couple_igt_sci_method"

def coupling_py(e):
    return True  # no cross-clause under minimal axioms

def coupling_z3():
    from z3 import BoolVal
    return [lambda e: BoolVal(True)]

if __name__ == "__main__":
    r = run_pair(
        NAME, "igt", "sci_method",
        coupling_py, coupling_z3(),
        "vacuous coupling clause; pair is additive under minimal axioms",
    )
    p = write_results(NAME, r)
    print(f"{NAME}: pass={r['overall_pass']} interacting={r['interacting']} additive={r['additive']} -> {p}")
