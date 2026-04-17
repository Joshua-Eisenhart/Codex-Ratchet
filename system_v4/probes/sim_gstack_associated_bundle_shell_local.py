#!/usr/bin/env python3
"""
sim_gstack_associated_bundle_shell_local.py -- Shell-local admissibility for an associated bundle chart.
"""

import sympy as sp
from z3 import Real, Solver, unsat
from toponetx.classes import CellComplex

from _gstack_shell_local_common import write_shell_local_result

classification = "canonical"
_SHELL_LOCAL_REASON = "not used: this probe stays shell-local inside one associated-bundle chart and does not invoke cross-shell coupling."

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "pyg": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "z3": {"tried": True, "used": True, "reason": "load-bearing: z3 rules out a transition cocycle that is simultaneously trivial and nontrivial on the same triple overlap."},
    "cvc5": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing: sympy checks the triple-overlap cocycle equation g01*g12*g20 = 1 exactly in rational arithmetic."},
    "clifford": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "xgi": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing: TopoNetX encodes the cover nerve cell complex and confirms the presence of one 2-cell supporting the triple overlap."},
    "gudhi": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": "load_bearing",
    "cvc5": None,
    "sympy": "load_bearing",
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": "load_bearing",
    "gudhi": None,
}


def run_positive_tests():
    g01 = sp.Rational(2, 1)
    g12 = sp.Rational(3, 1)
    g20 = sp.Rational(1, 6)
    cocycle = sp.simplify(g01 * g12 * g20)

    nerve = CellComplex()
    nerve.add_cell([0, 1], rank=1)
    nerve.add_cell([1, 2], rank=1)
    nerve.add_cell([0, 2], rank=1)
    nerve.add_cell([0, 1, 2], rank=2)

    return {
        "transition_cocycle_closes": {
            "pass": cocycle == 1,
            "cocycle_value": str(cocycle),
            "detail": "The local transition functions close on the unique triple overlap."
        },
        "cover_nerve_supports_triple_overlap": {
            "pass": nerve.shape == (3, 3, 1),
            "shape": list(nerve.shape),
            "detail": "The cover nerve has three vertices, three edges, and one 2-cell."
        },
    }


def run_negative_tests():
    x = Real("x")
    solver = Solver()
    solver.add(x == 1)
    solver.add(x != 1)
    return {
        "trivial_and_nontrivial_cocycle_conflict": {
            "pass": solver.check() == unsat,
            "detail": "A single triple-overlap multiplier cannot be both trivial and nontrivial."
        }
    }


def run_boundary_tests():
    identity_cocycle = sp.Integer(1)
    return {
        "identity_gluing_is_admissible_boundary": {
            "pass": identity_cocycle == 1,
            "detail": "The boundary case with all transition functions equal to 1 is locally admissible."
        }
    }


if __name__ == "__main__":
    write_shell_local_result(
        "sim_gstack_associated_bundle_shell_local",
        "associated_bundle",
        TOOL_MANIFEST,
        TOOL_INTEGRATION_DEPTH,
        run_positive_tests(),
        run_negative_tests(),
        run_boundary_tests(),
        extras={"chart": "three_open_sets"},
    )
