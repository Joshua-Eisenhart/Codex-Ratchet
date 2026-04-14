#!/usr/bin/env python3
"""sim_couple_holodeck_igt -- pairwise coupling of {holodeck, igt}.

Coupling axiom: under joint coupling, a strategy that is strictly dominated
in igt CANNOT be carried by a holodeck projection quotient (observer would
distinguish the dominated branch from the carrier class). So:
  coupling := projection_quotient -> not_strictly_dominated
Candidates violating this are 'excluded'; remainder 'survived'.
"""
from _couple_common import run_pair, write_results

NAME = "sim_couple_holodeck_igt"

EXTRA = ["observer_sees_equilibrium"]

def coupling_py(e):
    # If the projection is a quotient AND the strategy is pareto-survivable,
    # the observer must see it as an equilibrium (no hidden payoff asymmetry).
    return (not (e["projection_quotient"] and e["pareto_non_minimal"])) or e["observer_sees_equilibrium"]

def coupling_z3():
    from z3 import Implies, And
    return [lambda e: Implies(And(e["projection_quotient"], e["pareto_non_minimal"]), e["observer_sees_equilibrium"])]

if __name__ == "__main__":
    r = run_pair(
        NAME, "holodeck", "igt",
        coupling_py, coupling_z3(),
        "projection_quotient AND pareto_non_minimal => observer_sees_equilibrium (hidden payoff asymmetry excluded)",
        extra_atoms=EXTRA,
    )
    p = write_results(NAME, r)
    print(f"{NAME}: pass={r['overall_pass']} interacting={r['interacting']} additive={r['additive']} -> {p}")
