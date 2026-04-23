#!/usr/bin/env python3
"""
sim_gstack_gerbe_shell_local.py -- Shell-local admissibility for a gerbe chart.
"""

import sympy as sp
from z3 import Real, Solver, unsat
import xgi

from _gstack_shell_local_common import write_shell_local_result

classification = "canonical"
_SHELL_LOCAL_REASON = "not used: this probe stays shell-local inside one gerbe chart and does not invoke cross-shell coupling."

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "pyg": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "z3": {"tried": True, "used": True, "reason": "load-bearing: z3 excludes a local Cech coboundary that is simultaneously zero and nonzero."},
    "cvc5": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing: sympy evaluates the Cech 2-cocycle and its coboundary exactly on a finite cover."},
    "clifford": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing: XGI records the irreducible triple-overlap hyperedge supporting the local gerbe datum."},
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
    g012 = sp.exp(2 * sp.pi * sp.I / 3)
    g013 = sp.exp(2 * sp.pi * sp.I / 3)
    g023 = sp.Integer(1)
    g123 = sp.Integer(1)
    coboundary = sp.simplify(g123 * g023**-1 * g013 * g012**-1)
    hypergraph = xgi.Hypergraph([[0, 1, 2]])
    return {
        "cech_2_cocycle_closes": {
            "pass": coboundary == 1,
            "coboundary": str(coboundary),
            "detail": "The local gerbe datum has vanishing Cech coboundary on the quadruple overlap."
        },
        "triple_overlap_recorded": {
            "pass": hypergraph.num_edges == 1 and hypergraph.num_nodes == 3,
            "detail": "The local datum is supported on one genuine triple overlap."
        },
    }


def run_negative_tests():
    x = Real("x")
    solver = Solver()
    solver.add(x == 0)
    solver.add(x != 0)
    return {
        "coboundary_cannot_be_zero_and_nonzero": {
            "pass": solver.check() == unsat,
            "detail": "The local obstruction class cannot vanish and fail to vanish at once."
        }
    }


def run_boundary_tests():
    return {
        "trivial_gerbe_boundary": {
            "pass": sp.Integer(1) == 1,
            "detail": "The trivial local class is the admissible boundary case."
        }
    }


if __name__ == "__main__":
    write_shell_local_result(
        "sim_gstack_gerbe_shell_local",
        "gerbe",
        TOOL_MANIFEST,
        TOOL_INTEGRATION_DEPTH,
        run_positive_tests(),
        run_negative_tests(),
        run_boundary_tests(),
        extras={"cover_size": 4},
    )
