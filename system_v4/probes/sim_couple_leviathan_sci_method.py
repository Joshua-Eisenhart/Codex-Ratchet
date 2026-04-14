#!/usr/bin/env python3
"""sim_couple_leviathan_sci_method -- pairwise coupling of {leviathan, sci_method}.

Coupling axiom: a non-falsifiable legitimation claim cannot ground a stable
coalition (Popperian constraint on political epistemics).
  coupling := coalition_stable -> falsifiable
"""
from _couple_common import run_pair, write_results

NAME = "sim_couple_leviathan_sci_method"

EXTRA = ["legitimation_open_to_refutation"]

def coupling_py(e):
    return (not (e["coalition_stable"] and e["falsifiable"])) or e["legitimation_open_to_refutation"]

def coupling_z3():
    from z3 import Implies, And
    return [lambda e: Implies(And(e["coalition_stable"], e["falsifiable"]), e["legitimation_open_to_refutation"])]

if __name__ == "__main__":
    r = run_pair(
        NAME, "leviathan", "sci_method",
        coupling_py, coupling_z3(),
        "coalition_stable AND falsifiable => legitimation_open_to_refutation (closed legitimation excluded)",
        extra_atoms=EXTRA,
    )
    p = write_results(NAME, r)
    print(f"{NAME}: pass={r['overall_pass']} interacting={r['interacting']} additive={r['additive']} -> {p}")
