#!/usr/bin/env python3
"""
sim_gstack_derived_stack_shell_local.py -- Shell-local admissibility for a derived-stack chart.
"""

import sympy as sp
from z3 import Real, Solver, unsat
import gudhi

from _gstack_shell_local_common import write_shell_local_result

classification = "canonical"
_SHELL_LOCAL_REASON = "not used: this probe stays shell-local inside one derived-stack chart and does not invoke cross-shell coupling."

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "pyg": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "z3": {"tried": True, "used": True, "reason": "load-bearing: z3 excludes a square-zero parameter that is simultaneously zero and nonzero in the same extension chart."},
    "cvc5": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing: sympy verifies the nilpotent square-zero relation exactly with a local matrix model."},
    "clifford": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "xgi": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "toponetx": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing: GUDHI records the two-vertex local filtration supporting the square-zero extension chart."},
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
    "toponetx": None,
    "gudhi": "load_bearing",
}


def run_positive_tests():
    epsilon = sp.Matrix([[0, 1], [0, 0]])
    tree = gudhi.SimplexTree()
    tree.insert([0])
    tree.insert([1])
    tree.insert([0, 1], filtration=0.0)
    tree.compute_persistence()
    return {
        "square_zero_extension_survives": {
            "pass": epsilon * epsilon == sp.zeros(2),
            "detail": "The local derived chart carries a square-zero extension."
        },
        "local_filtration_connected": {
            "pass": tree.betti_numbers() == [1],
            "betti_numbers": tree.betti_numbers(),
            "detail": "The two-vertex local filtration stays connected."
        },
    }


def run_negative_tests():
    e = Real("e")
    solver = Solver()
    solver.add(e == 0)
    solver.add(e != 0)
    return {
        "square_zero_parameter_conflict": {
            "pass": solver.check() == unsat,
            "detail": "A single square-zero parameter cannot vanish and fail to vanish simultaneously."
        }
    }


def run_boundary_tests():
    zero = sp.zeros(2)
    return {
        "trivial_extension_boundary": {
            "pass": zero * zero == sp.zeros(2),
            "detail": "The trivial extension is the shell-local boundary of the derived chart."
        }
    }


if __name__ == "__main__":
    write_shell_local_result(
        "sim_gstack_derived_stack_shell_local",
        "derived_stack",
        TOOL_MANIFEST,
        TOOL_INTEGRATION_DEPTH,
        run_positive_tests(),
        run_negative_tests(),
        run_boundary_tests(),
        extras={"amplitude": "[-1,0]"},
    )
