#!/usr/bin/env python3
"""sim_triple_igt_leviathan_sci_method -- triple coupling {igt, leviathan, sci_method}.

Three-way coupling axiom:
  A pareto_non_minimal strategy carried by a coalition_stable aggregation whose
  hypothesis is falsifiable must satisfy triple_epistemic_closure -- otherwise
  joint coupling excludes the candidate as epistemically open while politically
  and game-theoretically stable.
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

NAME = "sim_triple_igt_leviathan_sci_method"
EXTRA = ["triple_epistemic_closure"]

def pair_py(e):
    return True

def pair_z3():
    return []

def triple_py(e):
    return (not (e["pareto_non_minimal"] and e["coalition_stable"] and e["falsifiable"])) \
        or e["triple_epistemic_closure"]

def triple_z3():
    from z3 import Implies, And
    return [lambda e: Implies(
        And(e["pareto_non_minimal"], e["coalition_stable"], e["falsifiable"]),
        e["triple_epistemic_closure"])]

if __name__ == "__main__":
    r = run_triple(
        NAME, "igt", "leviathan", "sci_method",
        pair_py, pair_z3(),
        triple_py, triple_z3(),
        "joint coupling excludes: pareto_non_minimal AND coalition_stable AND falsifiable "
        "without triple_epistemic_closure",
        extra_atoms=EXTRA,
    )
    p = write_results(NAME, r)
    print(f"{NAME}: pass={r['overall_pass']} interacting={r['interacting']} additive={r['additive']} -> {p}")
