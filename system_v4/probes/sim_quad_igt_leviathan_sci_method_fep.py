#!/usr/bin/env python3
"""sim_quad_igt_leviathan_sci_method_fep -- 4-shell coexistence.

Four-way coexistence axiom (interacting):
  When igt.pareto_non_minimal, leviathan.coalition_stable,
  sci_method.survives_modus_tollens, and fep.vfe_nonincreasing are jointly admissible,
  the four-way coexistence forces strategic_inference_consensus_quad. A candidate
  admissible at the triple-joint layer but lacking this atom is 'excluded by 4-way
  coexistence coupling'.
"""
from _quad_common import run_kwise, write_results

NAME = "sim_quad_igt_leviathan_sci_method_fep"
SHELLS = ["igt", "leviathan", "sci_method", "fep"]
EXTRA = ["strategic_inference_consensus_quad"]

def pair_py(e): return True
def pair_z3(): return []

def triple_py(e): return True
def triple_z3(): return []

def quad_py(e):
    ante = (e["pareto_non_minimal"] and e["coalition_stable"]
            and e["survives_modus_tollens"] and e["vfe_nonincreasing"])
    return (not ante) or e["strategic_inference_consensus_quad"]

def quad_z3():
    from z3 import Implies, And
    return [lambda e: Implies(
        And(e["pareto_non_minimal"], e["coalition_stable"],
            e["survives_modus_tollens"], e["vfe_nonincreasing"]),
        e["strategic_inference_consensus_quad"])]

if __name__ == "__main__":
    r = run_kwise(
        NAME, SHELLS,
        pair_py, pair_z3(),
        triple_py, triple_z3(),
        quad_py, quad_z3(),
        "4-way coupling excludes: pareto_non_minimal AND coalition_stable AND "
        "survives_modus_tollens AND vfe_nonincreasing without "
        "strategic_inference_consensus_quad",
        extra_atoms=EXTRA,
    )
    p = write_results(NAME, r)
    print(f"{NAME}: pass={r['overall_pass']} interacting={r['interacting']} additive={r['additive']} -> {p}")
