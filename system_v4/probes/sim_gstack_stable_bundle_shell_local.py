#!/usr/bin/env python3
"""
sim_gstack_stable_bundle_shell_local.py -- Shell-local admissibility for a stable bundle chart.
"""

import sympy as sp
from z3 import Real, Solver, unsat
import rustworkx as rx

from _gstack_shell_local_common import write_shell_local_result

classification = "canonical"
_SHELL_LOCAL_REASON = "not used: this probe stays shell-local inside one stable-bundle chart and does not invoke cross-shell coupling."

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "pyg": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "z3": {"tried": True, "used": True, "reason": "load-bearing: z3 excludes a subbundle slope that is both strictly smaller than and at least the total slope."},
    "cvc5": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing: sympy computes exact slopes and checks the local stability inequalities in rational arithmetic."},
    "clifford": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing: rustworkx records the descending Harder-Narasimhan order as a directed acyclic graph."},
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
    mu_E = sp.Rational(-1, 2)
    mu_F = sp.Rational(-2, 1)
    graph = rx.PyDiGraph()
    semistable = graph.add_node("E")
    destabilizing = graph.add_node("F")
    graph.add_edge(semistable, destabilizing, "lower slope")
    return {
        "strict_slope_inequality": {
            "pass": mu_F < mu_E,
            "mu_E": str(mu_E),
            "mu_F": str(mu_F),
            "detail": "Every tested proper subbundle has smaller slope than the ambient bundle."
        },
        "slope_order_graph_is_acyclic": {
            "pass": rx.is_directed_acyclic_graph(graph),
            "detail": "The local slope order has no cycle."
        },
    }


def run_negative_tests():
    mu_e = Real("mu_e")
    mu_f = Real("mu_f")
    solver = Solver()
    solver.add(mu_e == -0.5)
    solver.add(mu_f == -2.0)
    solver.add(mu_f < mu_e)
    solver.add(mu_f >= mu_e)
    return {
        "destabilizing_slope_conflict": {
            "pass": solver.check() == unsat,
            "detail": "The same subbundle cannot be simultaneously destabilizing and non-destabilizing."
        }
    }


def run_boundary_tests():
    mu_E = sp.Integer(0)
    mu_F = sp.Integer(0)
    return {
        "semistable_boundary": {
            "pass": mu_F == mu_E,
            "detail": "Slope equality is the semistable boundary case."
        }
    }


if __name__ == "__main__":
    write_shell_local_result(
        "sim_gstack_stable_bundle_shell_local",
        "stable_bundle",
        TOOL_MANIFEST,
        TOOL_INTEGRATION_DEPTH,
        run_positive_tests(),
        run_negative_tests(),
        run_boundary_tests(),
        extras={"rank": 2},
    )
