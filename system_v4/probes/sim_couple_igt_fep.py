#!/usr/bin/env python3
"""sim_couple_igt_fep -- pairwise coupling of {igt, fep}.

Coupling axiom: a strategy with non-decreasing VFE is in a region of rising
surprise; it cannot be pareto_non_minimal in the joint game (the surprise
gradient dominates the payoff margin). So:
  coupling := pareto_non_minimal -> vfe_nonincreasing
"""
from _couple_common import run_pair, write_results

NAME = "sim_couple_igt_fep"

EXTRA = ["payoff_gradient_aligned_with_surprise_gradient"]

def coupling_py(e):
    return (not (e["pareto_non_minimal"] and e["vfe_nonincreasing"])) or e["payoff_gradient_aligned_with_surprise_gradient"]

def coupling_z3():
    from z3 import Implies, And
    return [lambda e: Implies(And(e["pareto_non_minimal"], e["vfe_nonincreasing"]), e["payoff_gradient_aligned_with_surprise_gradient"])]

if __name__ == "__main__":
    r = run_pair(
        NAME, "igt", "fep",
        coupling_py, coupling_z3(),
        "pareto_non_minimal AND vfe_nonincreasing => payoff/surprise gradient alignment (misaligned gradient excluded)",
        extra_atoms=EXTRA,
    )
    p = write_results(NAME, r)
    print(f"{NAME}: pass={r['overall_pass']} interacting={r['interacting']} additive={r['additive']} -> {p}")
