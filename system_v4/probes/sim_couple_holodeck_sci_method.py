#!/usr/bin/env python3
"""sim_couple_holodeck_sci_method -- pairwise coupling of {holodeck, sci_method}.

Coupling axiom: a hypothesis that is NOT falsifiable cannot be distinguished
from its negation by any observer projection; the projection quotient then
collapses. So:
  coupling := projection_quotient -> falsifiable
"""
from _couple_common import run_pair, write_results

NAME = "sim_couple_holodeck_sci_method"

EXTRA = ["test_in_observer_window"]

def coupling_py(e):
    return (not (e["projection_quotient"] and e["falsifiable"])) or e["test_in_observer_window"]

def coupling_z3():
    from z3 import Implies, And
    return [lambda e: Implies(And(e["projection_quotient"], e["falsifiable"]), e["test_in_observer_window"])]

if __name__ == "__main__":
    r = run_pair(
        NAME, "holodeck", "sci_method",
        coupling_py, coupling_z3(),
        "projection_quotient AND falsifiable => test_in_observer_window (unobservable test excluded)",
        extra_atoms=EXTRA,
    )
    p = write_results(NAME, r)
    print(f"{NAME}: pass={r['overall_pass']} interacting={r['interacting']} additive={r['additive']} -> {p}")
