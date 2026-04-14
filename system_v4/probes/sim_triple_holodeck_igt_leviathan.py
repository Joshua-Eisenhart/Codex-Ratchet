#!/usr/bin/env python3
"""sim_triple_holodeck_igt_leviathan -- triple coupling {holodeck, igt, leviathan}.

Three-way coupling axiom (interacting):
  When holodeck's projection_quotient, igt's pareto_non_minimal, and leviathan's
  coalition_stable are jointly admissible, the carrier-observer must see the
  equilibrium (observer_sees_equilibrium). Pairwise couplings only constrain the
  observer conditional on TWO of these; the three-way conjunction is a strictly
  stronger constraint introduced at step 3 (a candidate admissible pairwise but
  lacking observer_sees_equilibrium under the full triple is 'excluded by triple
  coupling').
"""
from _triple_common import run_triple, write_results

NAME = "sim_triple_holodeck_igt_leviathan"
EXTRA = ["observer_sees_equilibrium"]

def pair_py(e):
    # pairwise couplings are deliberately weaker than the triple:
    # holodeck-igt alone: no observer constraint at pair level here
    # holodeck-leviathan alone: no observer constraint at pair level
    # igt-leviathan: no observer atom involved
    return True

def pair_z3():
    return []

def triple_py(e):
    return (not (e["projection_quotient"] and e["pareto_non_minimal"] and e["coalition_stable"])) \
        or e["observer_sees_equilibrium"]

def triple_z3():
    from z3 import Implies, And
    return [lambda e: Implies(
        And(e["projection_quotient"], e["pareto_non_minimal"], e["coalition_stable"]),
        e["observer_sees_equilibrium"])]

if __name__ == "__main__":
    r = run_triple(
        NAME, "holodeck", "igt", "leviathan",
        pair_py, pair_z3(),
        triple_py, triple_z3(),
        "joint coupling excludes: projection_quotient AND pareto_non_minimal AND coalition_stable "
        "without observer_sees_equilibrium (triple-only structural exclusion)",
        extra_atoms=EXTRA,
    )
    p = write_results(NAME, r)
    print(f"{NAME}: pass={r['overall_pass']} interacting={r['interacting']} additive={r['additive']} -> {p}")
