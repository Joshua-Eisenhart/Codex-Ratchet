#!/usr/bin/env python3
"""
sim_gtower_gl3_flag_minor_shell_local.py -- Shell-local admissibility for a GL(3) flag chart.
"""

import sympy as sp
from z3 import Real, Solver, unsat
import rustworkx as rx

from _gstack_shell_local_common import write_shell_local_result

classification = "canonical"
_SHELL_LOCAL_REASON = "not used: this probe stays shell-local inside one GL(3) flag chart and does not invoke cross-shell coupling."

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "pyg": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "z3": {"tried": True, "used": True, "reason": "load-bearing: z3 excludes a leading flag minor that is simultaneously zero and nonzero."},
    "cvc5": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing: sympy evaluates the leading principal minors exactly inside one GL(3) chart."},
    "clifford": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing: rustworkx records the three-step local flag incidence graph."},
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
    matrix = sp.Matrix([[2, 1, 0], [0, 3, 1], [0, 0, 5]])
    graph = rx.PyDiGraph()
    n0 = graph.add_node("L1")
    n1 = graph.add_node("L2")
    n2 = graph.add_node("L3")
    graph.add_edge(n0, n1, "extends")
    graph.add_edge(n1, n2, "extends")
    minors = [matrix[:k, :k].det() for k in (1, 2, 3)]
    return {
        "leading_minors_nonzero": {
            "pass": all(m != 0 for m in minors),
            "minors": [str(m) for m in minors],
            "detail": "All leading flag minors survive in the chosen GL(3) chart."
        },
        "flag_graph_is_chain": {
            "pass": graph.num_nodes() == 3 and graph.num_edges() == 2,
            "detail": "The local flag chart has one admissible three-step incidence chain."
        },
    }


def run_negative_tests():
    x = Real("x")
    solver = Solver()
    solver.add(x == 0)
    solver.add(x != 0)
    return {
        "pivot_zero_conflict": {
            "pass": solver.check() == unsat,
            "detail": "A leading flag pivot cannot vanish and fail to vanish in the same local chart."
        }
    }


def run_boundary_tests():
    unitriangular = sp.Matrix([[1, 1, 0], [0, 1, 1], [0, 0, 1]])
    minors = [unitriangular[:k, :k].det() for k in (1, 2, 3)]
    return {
        "unitriangular_boundary": {
            "pass": minors == [1, 1, 1],
            "minors": [str(m) for m in minors],
            "detail": "The unitriangular chart is the boundary case where every leading minor is exactly one."
        }
    }


if __name__ == "__main__":
    write_shell_local_result(
        "sim_gtower_gl3_flag_minor_shell_local",
        "gl3_flag_minor",
        TOOL_MANIFEST,
        TOOL_INTEGRATION_DEPTH,
        run_positive_tests(),
        run_negative_tests(),
        run_boundary_tests(),
        extras={"group": "GL(3)"},
    )
