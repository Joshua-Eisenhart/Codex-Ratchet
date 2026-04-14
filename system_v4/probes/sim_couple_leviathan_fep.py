#!/usr/bin/env python3
"""sim_couple_leviathan_fep -- pairwise coupling of {leviathan, fep}.

Additive coupling: monotone aggregation and markov blanket CI operate on
disjoint structural atoms under the minimal shell-local axioms. Vacuous
coupling clause; pair is additive.
"""
from _couple_common import run_pair, write_results

NAME = "sim_couple_leviathan_fep"

def coupling_py(e):
    return True

def coupling_z3():
    from z3 import BoolVal
    return [lambda e: BoolVal(True)]

if __name__ == "__main__":
    r = run_pair(
        NAME, "leviathan", "fep",
        coupling_py, coupling_z3(),
        "vacuous coupling clause; pair is additive under minimal axioms",
    )
    p = write_results(NAME, r)
    print(f"{NAME}: pass={r['overall_pass']} interacting={r['interacting']} additive={r['additive']} -> {p}")
