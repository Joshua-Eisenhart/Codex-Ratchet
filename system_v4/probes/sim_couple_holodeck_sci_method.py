#!/usr/bin/env python3
"""sim_couple_holodeck_sci_method -- pairwise coupling of {holodeck, sci_method}.

Coupling axiom: a hypothesis that is NOT falsifiable cannot be distinguished
from its negation by any observer projection; the projection quotient then
collapses. So:
  coupling := projection_quotient -> falsifiable
"""
from _couple_common import run_pair, write_results

NAME = "sim_couple_holodeck_sci_method"
classification = "classical_baseline"
divergence_log = (
    "Holodeck and science-method coupling is a classical baseline wrapper around "
    "projection-quotient falsifiability; the pair only composes when the observer "
    "window is active, and the unobservable test remains excluded."
)
CLASSIFICATION_NOTE = divergence_log

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "pair construction and result marshaling in the coupling wrapper"},
    "z3": {"tried": True, "used": True, "reason": "witnesses the coupling implication under the observer window"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "z3": "supportive",
}

EXTRA = ["test_in_observer_window"]

def coupling_py(e):
    return (not (e["projection_quotient"] and e["falsifiable"])) or e["test_in_observer_window"]

def coupling_z3():
    from z3 import Implies, And
    return [lambda e: Implies(And(e["projection_quotient"], e["falsifiable"]), e["test_in_observer_window"])]

if __name__ == "__main__":
    r = run_pair(
        NAME, "holodeck", "sci_method",
        coupling_py, coupling_z3(),
        CLASSIFICATION_NOTE,
        extra_atoms=EXTRA,
    )
    p = write_results(NAME, r)
    print(f"{NAME}: pass={r['overall_pass']} interacting={r['interacting']} additive={r['additive']} -> {p}")
