#!/usr/bin/env python3
"""sim_triple_holodeck_igt_sci_method -- triple coupling {holodeck, igt, sci_method}.

Three-way coupling axiom:
  A projection_quotient carrying a pareto_non_minimal strategy whose hypothesis
  is falsifiable must survive_modus_tollens under the joint triple -- otherwise
  the observer would see the carrier class falsified by evidence yet still
  admit the strategy. Joint coupling excludes such candidates.
"""
from _triple_common import run_triple, write_results

NAME = "sim_triple_holodeck_igt_sci_method"
EXTRA = ["triple_witness_consistent"]

def pair_py(e):
    return True

def pair_z3():
    return []

def triple_py(e):
    # projection_quotient AND pareto_non_minimal AND falsifiable => triple_witness_consistent
    return (not (e["projection_quotient"] and e["pareto_non_minimal"] and e["falsifiable"])) \
        or e["triple_witness_consistent"]

def triple_z3():
    from z3 import Implies, And
    return [lambda e: Implies(
        And(e["projection_quotient"], e["pareto_non_minimal"], e["falsifiable"]),
        e["triple_witness_consistent"])]

if __name__ == "__main__":
    r = run_triple(
        NAME, "holodeck", "igt", "sci_method",
        pair_py, pair_z3(),
        triple_py, triple_z3(),
        "joint coupling excludes: projection_quotient AND pareto_non_minimal AND falsifiable "
        "without triple_witness_consistent",
        extra_atoms=EXTRA,
    )
    p = write_results(NAME, r)
    print(f"{NAME}: pass={r['overall_pass']} interacting={r['interacting']} additive={r['additive']} -> {p}")
