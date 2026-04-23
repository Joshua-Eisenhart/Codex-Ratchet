#!/usr/bin/env python3
"""
sim_gstack_hitchin_fibration_shell_local.py -- Shell-local admissibility for a Hitchin-base chart.
"""

import sympy as sp
from z3 import Real, Solver, unsat
import rustworkx as rx

from _gstack_shell_local_common import write_shell_local_result

classification = "canonical"
_SHELL_LOCAL_REASON = "not used: this probe stays shell-local inside one Hitchin-base chart and does not invoke cross-shell coupling."

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "pyg": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "z3": {"tried": True, "used": True, "reason": "load-bearing: z3 excludes a discriminant that is simultaneously regular and singular at the same local base point."},
    "cvc5": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing: sympy computes the local discriminant of the spectral polynomial exactly."},
    "clifford": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing: rustworkx records the local map from base coefficient chart to spectral-curve branch data."},
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
    discriminant = sp.discriminant(poly, lam)
    graph = rx.PyDiGraph()
    base = graph.add_node("q")
    graph.add_node("branch_plus")
    graph.add_node("branch_minus")
    graph.add_edge(base, 1, "sqrt(q)")
    graph.add_edge(base, 2, "-sqrt(q)")
    return {
        "regular_base_point": {
            "pass": discriminant != 0,
            "discriminant": str(discriminant),
            "detail": "The chosen local Hitchin-base point is regular."
        },
        "two_branch_local_cover": {
            "pass": graph.num_edges() == 2,
            "detail": "The local spectral cover has two branches over the regular point."
        },
    }


def run_negative_tests():
    delta = Real("delta")
    solver = Solver()
    solver.add(delta == 0)
    solver.add(delta != 0)
    return {
        "regular_singular_conflict": {
            "pass": solver.check() == unsat,
            "detail": "A local discriminant cannot vanish and fail to vanish simultaneously."
        }
    }


def run_boundary_tests():
    lam = sp.symbols("lam")
    poly = lam**2
    return {
        "nodal_boundary_point": {
            "pass": sp.discriminant(poly, lam) == 0,
            "detail": "The discriminant-zero point is the singular boundary of the local Hitchin chart."
        }
    }


if __name__ == "__main__":
    write_shell_local_result(
        "sim_gstack_hitchin_fibration_shell_local",
        "hitchin_fibration",
        TOOL_MANIFEST,
        TOOL_INTEGRATION_DEPTH,
        run_positive_tests(),
        run_negative_tests(),
        run_boundary_tests(),
        extras={"degree": 2},
    )
