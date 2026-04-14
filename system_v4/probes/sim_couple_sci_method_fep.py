#!/usr/bin/env python3
"""sim_couple_sci_method_fep -- pairwise coupling of {sci_method, fep}.

Coupling axiom: surviving modus tollens under evidence requires that the
blanket CI holds (otherwise observed evidence cannot be cleanly separated
from hidden states, and refutation cannot be assigned).
  coupling := survives_modus_tollens -> markov_blanket_ci
"""
from _couple_common import run_pair, write_results

NAME = "sim_couple_sci_method_fep"

EXTRA = ["evidence_within_blanket"]

def coupling_py(e):
    return (not (e["survives_modus_tollens"] and e["markov_blanket_ci"])) or e["evidence_within_blanket"]

def coupling_z3():
    from z3 import Implies, And
    return [lambda e: Implies(And(e["survives_modus_tollens"], e["markov_blanket_ci"]), e["evidence_within_blanket"])]

if __name__ == "__main__":
    r = run_pair(
        NAME, "sci_method", "fep",
        coupling_py, coupling_z3(),
        "survives_modus_tollens AND markov_blanket_ci => evidence_within_blanket (blanket-external evidence excluded)",
        extra_atoms=EXTRA,
    )
    p = write_results(NAME, r)
    print(f"{NAME}: pass={r['overall_pass']} interacting={r['interacting']} additive={r['additive']} -> {p}")
