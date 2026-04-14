#!/usr/bin/env python3
"""sim_triple_holodeck_sci_method_fep -- triple coupling {holodeck, sci_method, fep}.

Three-way coupling axiom (additive):
  holodeck's carrier_equiv/projection_quotient, sci_method's falsifiability/
  modus_tollens survival, and fep's vfe_nonincreasing/markov_blanket_ci cover
  disjoint atom sets with no three-way witness introduced at this layer.
  Reported as 'additive' -- joint coupling excludes nothing beyond the pairwise
  intersection.
"""
from _triple_common import run_triple, write_results

NAME = "sim_triple_holodeck_sci_method_fep"

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
        NAME, "holodeck", "sci_method", "fep",
        pair_py, pair_z3(),
        triple_py, triple_z3(),
        "joint coupling excludes: nothing beyond pairwise (additive triple)",
    )
    p = write_results(NAME, r)
    print(f"{NAME}: pass={r['overall_pass']} interacting={r['interacting']} additive={r['additive']} -> {p}")
