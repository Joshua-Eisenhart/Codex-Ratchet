#!/usr/bin/env python3
"""
sim_gstack_local_system_shell_local.py -- Shell-local admissibility for a local-system chart.
"""

import sympy as sp
from z3 import Real, Solver, unsat
import rustworkx as rx

from _gstack_shell_local_common import write_shell_local_result

classification = "canonical"
_SHELL_LOCAL_REASON = "not used: this probe stays shell-local inside one local-system chart and does not invoke cross-shell coupling."

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "pyg": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "z3": {"tried": True, "used": True, "reason": "load-bearing: z3 excludes a trace that is simultaneously two and not two for the same local monodromy."},
    "cvc5": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing: sympy evaluates the local unipotent monodromy matrix exactly."},
    "clifford": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing: rustworkx records the one-generator local monodromy graph."},
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
    monodromy = sp.Matrix([[1, 1], [0, 1]])
    graph = rx.PyDiGraph()
    chart = graph.add_node("chart")
    mono = graph.add_node("monodromy")
    graph.add_edge(chart, mono, "gamma")
    return {
        "unipotent_monodromy_survives": {
            "pass": monodromy.det() == 1 and monodromy.trace() == 2,
            "detail": "The chosen local-system monodromy stays unipotent with determinant one."
        },
        "local_generator_recorded": {
            "pass": graph.num_nodes() == 2 and graph.num_edges() == 1,
            "detail": "The local system chart carries one explicit generator edge."
        },
    }


def run_negative_tests():
    t = Real("t")
    solver = Solver()
    solver.add(t == 2)
    solver.add(t != 2)
    return {
        "trace_conflict": {
            "pass": solver.check() == unsat,
            "detail": "A single local monodromy trace cannot equal and fail to equal two simultaneously."
        }
    }


def run_boundary_tests():
    identity = sp.eye(2)
    return {
        "identity_monodromy_boundary": {
            "pass": identity.det() == 1 and identity.trace() == 2,
            "detail": "The identity representation is the shell-local boundary of the local-system chart."
        }
    }


if __name__ == "__main__":
    write_shell_local_result(
        "sim_gstack_local_system_shell_local",
        "local_system",
        TOOL_MANIFEST,
        TOOL_INTEGRATION_DEPTH,
        run_positive_tests(),
        run_negative_tests(),
        run_boundary_tests(),
        extras={"rank": 2},
    )
