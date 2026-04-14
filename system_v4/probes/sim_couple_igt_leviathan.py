#!/usr/bin/env python3
"""sim_couple_igt_leviathan -- pairwise coupling of {igt, leviathan}.

Coupling axiom: a coalition that is NOT stable admits a blocking subcoalition
with a strictly dominating payoff, so 'coalition_stable' requires
'not_strictly_dominated' for at least the equilibrium strategy.
  coupling := coalition_stable -> not_strictly_dominated
"""
from _couple_common import run_pair, write_results

NAME = "sim_couple_igt_leviathan"

EXTRA = ["no_blocking_subcoalition"]

def coupling_py(e):
    return (not (e["coalition_stable"] and e["not_strictly_dominated"])) or e["no_blocking_subcoalition"]

def coupling_z3():
    from z3 import Implies, And
    return [lambda e: Implies(And(e["coalition_stable"], e["not_strictly_dominated"]), e["no_blocking_subcoalition"])]

if __name__ == "__main__":
    r = run_pair(
        NAME, "igt", "leviathan",
        coupling_py, coupling_z3(),
        "coalition_stable AND not_strictly_dominated => no_blocking_subcoalition (blocking subcoalition excludes the joint survival)",
        extra_atoms=EXTRA,
    )
    p = write_results(NAME, r)
    print(f"{NAME}: pass={r['overall_pass']} interacting={r['interacting']} additive={r['additive']} -> {p}")
