#!/usr/bin/env python3
"""sim_triple_igt_leviathan_fep -- triple coupling {igt, leviathan, fep}.

Three-way coupling axiom:
  A strategy that is pareto_non_minimal under igt, supported by a
  coalition_stable aggregation under leviathan, AND sits at a vfe_nonincreasing
  point under fep must satisfy markov_blanket_ci -- joint coupling excludes any
  candidate where stable pareto-active coalitions leak information across the
  Markov blanket.
"""
from _triple_common import run_triple, write_results

classification = "canonical"

TOOL_MANIFEST = {
    "z3": {"tried": True, "used": True, "reason": "load-bearing: triple-coupling SAT/UNSAT witness for three-way exclusion"},
    "sympy": {"tried": True, "used": False, "reason": "supportive only; Boolean admissibility does not require symbolic algebra"},
    "clifford": {"tried": True, "used": False, "reason": "not applicable at triple-level Boolean coupling layer"},
    "pytorch": {"tried": True, "used": False, "reason": "no gradient surface at this Boolean triple-admissibility layer"},
}

TOOL_INTEGRATION_DEPTH = {
    "z3": "load_bearing",
    "sympy": "supportive",
    "clifford": None,
    "pytorch": None,
}

NAME = "sim_triple_igt_leviathan_fep"
EXTRA = ["triple_markov_consistent"]

def pair_py(e):
    return True

def pair_z3():
    return []

def triple_py(e):
    return (not (e["pareto_non_minimal"] and e["coalition_stable"] and e["vfe_nonincreasing"])) \
        or e["triple_markov_consistent"]

def triple_z3():
    from z3 import Implies, And
    return [lambda e: Implies(
        And(e["pareto_non_minimal"], e["coalition_stable"], e["vfe_nonincreasing"]),
        e["triple_markov_consistent"])]

if __name__ == "__main__":
    r = run_triple(
        NAME, "igt", "leviathan", "fep",
        pair_py, pair_z3(),
        triple_py, triple_z3(),
        "joint coupling excludes: pareto_non_minimal AND coalition_stable AND vfe_nonincreasing "
        "without triple_markov_consistent",
        extra_atoms=EXTRA,
    )
    p = write_results(NAME, r)
    print(f"{NAME}: pass={r['overall_pass']} interacting={r['interacting']} additive={r['additive']} -> {p}")
