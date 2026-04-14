#!/usr/bin/env python3
"""sim_couple_holodeck_leviathan -- pairwise coupling of {holodeck, leviathan}.

Coupling axiom: a non-monotone coalition aggregation breaks carrier
equivalence (distinct coalitions with equal total power would be
distinguishable to the observer). So:
  coupling := carrier_equiv -> monotone_aggregation
"""
from _couple_common import run_pair, write_results

NAME = "sim_couple_holodeck_leviathan"

EXTRA = ["observer_aligned_with_sovereign"]

def coupling_py(e):
    return (not (e["carrier_equiv"] and e["coalition_stable"])) or e["observer_aligned_with_sovereign"]

def coupling_z3():
    from z3 import Implies, And
    return [lambda e: Implies(And(e["carrier_equiv"], e["coalition_stable"]), e["observer_aligned_with_sovereign"])]

if __name__ == "__main__":
    r = run_pair(
        NAME, "holodeck", "leviathan",
        coupling_py, coupling_z3(),
        "carrier_equiv AND coalition_stable => observer_aligned_with_sovereign (unaligned observer excluded)",
        extra_atoms=EXTRA,
    )
    p = write_results(NAME, r)
    print(f"{NAME}: pass={r['overall_pass']} interacting={r['interacting']} additive={r['additive']} -> {p}")
