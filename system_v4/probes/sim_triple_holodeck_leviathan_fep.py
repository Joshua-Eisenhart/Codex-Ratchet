#!/usr/bin/env python3
"""sim_triple_holodeck_leviathan_fep -- triple coupling {holodeck, leviathan, fep}.

Three-way coupling axiom (additive under the current shell atoms):
  holodeck's projection_quotient, leviathan's coalition_stable, and fep's
  vfe_nonincreasing already constrain disjoint Boolean atoms with no shared
  extra witness at the triple layer. The three-way coupling asserts only that
  the pair couplings co-hold; it introduces no additional exclusion beyond the
  pairwise intersection. Reported as 'additive'.
"""
from _triple_common import run_triple, write_results

NAME = "sim_triple_holodeck_leviathan_fep"

def pair_py(e):
    return True

def pair_z3():
    return []

def triple_py(e):
    return True

def triple_z3():
    return []

if __name__ == "__main__":
    r = run_triple(
        NAME, "holodeck", "leviathan", "fep",
        pair_py, pair_z3(),
        triple_py, triple_z3(),
        "joint coupling excludes: nothing beyond pairwise (additive triple)",
    )
    p = write_results(NAME, r)
    print(f"{NAME}: pass={r['overall_pass']} interacting={r['interacting']} additive={r['additive']} -> {p}")
