#!/usr/bin/env python3
"""sim_pent_all_five_frameworks -- 5-shell coexistence {holodeck, igt, leviathan,
sci_method, fep}.

Five-way coexistence axiom (interacting):
  When holodeck.projection_quotient, igt.pareto_non_minimal, leviathan.coalition_stable,
  sci_method.survives_modus_tollens, and fep.vfe_nonincreasing are jointly admissible,
  the five-way coexistence forces self_similar_consensus_pent -- the atom named by the
  self-similar-frameworks doctrine. A candidate admissible at every embedded 4-way
  (quad) layer but lacking this atom is 'excluded by 5-way coexistence coupling'.
"""
from _quad_common import run_kwise, write_results

NAME = "sim_pent_all_five_frameworks"
SHELLS = ["holodeck", "igt", "leviathan", "sci_method", "fep"]
EXTRA = ["self_similar_consensus_pent"]

def pair_py(e): return True
def pair_z3(): return []

def triple_py(e): return True
def triple_z3(): return []

def pent_py(e):
    ante = (e["projection_quotient"] and e["pareto_non_minimal"]
            and e["coalition_stable"] and e["survives_modus_tollens"]
            and e["vfe_nonincreasing"])
    return (not ante) or e["self_similar_consensus_pent"]

def pent_z3():
    from z3 import Implies, And
    return [lambda e: Implies(
        And(e["projection_quotient"], e["pareto_non_minimal"],
            e["coalition_stable"], e["survives_modus_tollens"],
            e["vfe_nonincreasing"]),
        e["self_similar_consensus_pent"])]

if __name__ == "__main__":
    r = run_kwise(
        NAME, SHELLS,
        pair_py, pair_z3(),
        triple_py, triple_z3(),
        pent_py, pent_z3(),
        "5-way coupling excludes: projection_quotient AND pareto_non_minimal AND "
        "coalition_stable AND survives_modus_tollens AND vfe_nonincreasing without "
        "self_similar_consensus_pent (five-way structural exclusion beyond all "
        "embedded quad-joints)",
        extra_atoms=EXTRA,
    )
    p = write_results(NAME, r)
    print(f"{NAME}: pass={r['overall_pass']} interacting={r['interacting']} additive={r['additive']} -> {p}")
