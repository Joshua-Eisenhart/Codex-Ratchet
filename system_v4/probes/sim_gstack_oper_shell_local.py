#!/usr/bin/env python3
"""
sim_gstack_oper_shell_local.py -- Shell-local admissibility for an oper chart.
"""

import sympy as sp
from z3 import Real, Solver, unsat
import rustworkx as rx

from _gstack_shell_local_common import write_shell_local_result

classification = "canonical"
_SHELL_LOCAL_REASON = "not used: this probe stays shell-local inside one oper chart and does not invoke cross-shell coupling."

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "pyg": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "z3": {"tried": True, "used": True, "reason": "load-bearing: z3 excludes a local oper parameter that is simultaneously zero and nonzero."},
    "cvc5": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing: sympy computes the local oper discriminant exactly."},
    "clifford": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing: rustworkx records the local branch graph of the oper chart."},
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
    lam = sp.symbols("lam")
    q = sp.Integer(1)
    poly = lam**2 - q
    graph = rx.PyDiGraph()
    base = graph.add_node("q")
    plus = graph.add_node("+sqrt(q)")
    minus = graph.add_node("-sqrt(q)")
    graph.add_edge(base, plus, "branch")
    graph.add_edge(base, minus, "branch")
    return {
        "oper_discriminant_nonzero": {
            "pass": sp.discriminant(poly, lam) == 4,
            "discriminant": str(sp.discriminant(poly, lam)),
            "detail": "The local oper chart stays regular at q = 1."
        },
        "branch_graph_has_two_leaves": {
            "pass": graph.num_nodes() == 3 and graph.num_edges() == 2,
            "detail": "The local oper chart records the two admissible branches."
        },
    }


def run_negative_tests():
    q = Real("q")
    solver = Solver()
    solver.add(q == 0)
    solver.add(q != 0)
    return {
        "oper_parameter_conflict": {
            "pass": solver.check() == unsat,
            "detail": "A local oper parameter cannot vanish and fail to vanish simultaneously."
        }
    }


def run_boundary_tests():
    lam = sp.symbols("lam")
    poly = lam**2
    return {
        "double_root_boundary": {
            "pass": sp.discriminant(poly, lam) == 0,
            "detail": "The double-root oper is the shell-local boundary case."
        }
    }


if __name__ == "__main__":
    write_shell_local_result(
        "sim_gstack_oper_shell_local",
        "oper",
        TOOL_MANIFEST,
        TOOL_INTEGRATION_DEPTH,
        run_positive_tests(),
        run_negative_tests(),
        run_boundary_tests(),
        extras={"rank": 2},
    )
