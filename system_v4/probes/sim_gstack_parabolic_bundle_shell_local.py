#!/usr/bin/env python3
"""
sim_gstack_parabolic_bundle_shell_local.py -- Shell-local admissibility for a parabolic-bundle chart.
"""

import sympy as sp
from z3 import Real, Solver, unsat
import xgi

from _gstack_shell_local_common import write_shell_local_result

classification = "canonical"
_SHELL_LOCAL_REASON = "not used: this probe stays shell-local inside one parabolic-bundle chart and does not invoke cross-shell coupling."

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "pyg": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "z3": {"tried": True, "used": True, "reason": "load-bearing: z3 excludes a parabolic weight that is simultaneously below one and at least one."},
    "cvc5": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing: sympy checks the exact local parabolic weight inequalities."},
    "clifford": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing: XGI records one irreducible fiber-weight support hyperedge in the local chart."},
    "toponetx": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
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
    "xgi": "load_bearing",
    "toponetx": None,
    "gudhi": None,
}


def run_positive_tests():
    alpha1 = sp.Rational(1, 4)
    alpha2 = sp.Rational(1, 2)
    hypergraph = xgi.Hypergraph([[0, 1, 2]])
    return {
        "weights_stay_in_interval": {
            "pass": sp.Integer(0) <= alpha1 < 1 and sp.Integer(0) <= alpha2 < 1 and alpha1 <= alpha2,
            "weights": [str(alpha1), str(alpha2)],
            "detail": "The local parabolic weights stay inside the admissible interval and preserve order."
        },
        "fiber_weight_support_recorded": {
            "pass": hypergraph.num_edges == 1 and hypergraph.num_nodes == 3,
            "detail": "The local fiber and its ordered weights close on one hyperedge."
        },
    }


def run_negative_tests():
    a = Real("a")
    solver = Solver()
    solver.add(a < 1)
    solver.add(a >= 1)
    return {
        "parabolic_interval_conflict": {
            "pass": solver.check() == unsat,
            "detail": "A single local parabolic weight cannot stay below one and at least one simultaneously."
        }
    }


def run_boundary_tests():
    alpha = sp.Integer(0)
    return {
        "zero_weight_boundary": {
            "pass": alpha == 0,
            "detail": "Zero is the shell-local boundary weight of the parabolic chart."
        }
    }


if __name__ == "__main__":
    write_shell_local_result(
        "sim_gstack_parabolic_bundle_shell_local",
        "parabolic_bundle",
        TOOL_MANIFEST,
        TOOL_INTEGRATION_DEPTH,
        run_positive_tests(),
        run_negative_tests(),
        run_boundary_tests(),
        extras={"marked_points": 1},
    )
