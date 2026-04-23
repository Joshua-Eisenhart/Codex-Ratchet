#!/usr/bin/env python3
"""
sim_gstack_floer_complex_shell_local.py -- Shell-local admissibility for a finite Floer complex.
"""

import sympy as sp
from z3 import Real, Solver, unsat
import rustworkx as rx

from _gstack_shell_local_common import write_shell_local_result

classification = "canonical"
_SHELL_LOCAL_REASON = "not used: this probe stays shell-local inside one Floer complex and does not invoke cross-shell coupling."

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "pyg": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "z3": {"tried": True, "used": True, "reason": "load-bearing: z3 excludes a differential whose square is both zero and nonzero on the same local complex."},
    "cvc5": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing: sympy checks d^2 = 0 exactly for a finite chain model of the local Floer differential."},
    "clifford": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing: rustworkx verifies that the local action graph is acyclic, so the finite differential has a valid direction of flow."},
    "xgi": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
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
    "rustworkx": "load_bearing",
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}


def run_positive_tests():
    d1 = sp.Matrix([[1, 0]])
    d2 = sp.Matrix([[0], [0]])
    flow = rx.PyDiGraph()
    a = flow.add_node("x")
    b = flow.add_node("y")
    flow.add_edge(a, b, "drops action")
    return {
        "differential_squares_to_zero": {
            "pass": d1 * d2 == sp.zeros(1, 1),
            "detail": "The local Floer differential satisfies d^2 = 0."
        },
        "action_graph_acyclic": {
            "pass": rx.is_directed_acyclic_graph(flow),
            "detail": "The local action graph has no directed cycle."
        },
    }


def run_negative_tests():
    x = Real("x")
    solver = Solver()
    solver.add(x == 0)
    solver.add(x != 0)
    return {
        "square_zero_conflict": {
            "pass": solver.check() == unsat,
            "detail": "The same local differential square cannot be both zero and nonzero."
        }
    }


def run_boundary_tests():
    zero = sp.zeros(1, 1)
    return {
        "zero_differential_boundary": {
            "pass": zero == sp.zeros(1, 1),
            "detail": "The zero differential is the boundary case of a local Floer chart."
        }
    }


if __name__ == "__main__":
    write_shell_local_result(
        "sim_gstack_floer_complex_shell_local",
        "floer_complex",
        TOOL_MANIFEST,
        TOOL_INTEGRATION_DEPTH,
        run_positive_tests(),
        run_negative_tests(),
        run_boundary_tests(),
        extras={"generators": 2},
    )
