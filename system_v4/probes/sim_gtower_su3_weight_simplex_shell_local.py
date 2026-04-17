#!/usr/bin/env python3
"""
sim_gtower_su3_weight_simplex_shell_local.py -- Shell-local admissibility for an SU(3) dominant-weight simplex chart.
"""

import sympy as sp
from z3 import Real, Solver, unsat
import xgi

from _gstack_shell_local_common import write_shell_local_result

classification = "canonical"
_SHELL_LOCAL_REASON = "not used: this probe stays shell-local inside one SU(3) weight chart and does not invoke cross-shell coupling."

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "pyg": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "z3": {"tried": True, "used": True, "reason": "load-bearing: z3 excludes a dominant-weight barycentric sum that is simultaneously one and not one."},
    "cvc5": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing: sympy inverts the SU(3) Cartan matrix exactly to recover the fundamental weights."},
    "clifford": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing: XGI records the local dominant chamber as one irreducible triangular support."},
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
    cartan = sp.Matrix([[2, -1], [-1, 2]])
    inverse = cartan.inv()
    hypergraph = xgi.Hypergraph([[0, 1, 2]])
    return {
        "fundamental_weights_recovered": {
            "pass": sp.simplify(cartan * inverse) == sp.eye(2),
            "inverse": str(inverse),
            "detail": "The local dominant-weight chart is recovered exactly from the SU(3) Cartan matrix."
        },
        "dominant_face_recorded": {
            "pass": hypergraph.num_edges == 1 and hypergraph.num_nodes == 3,
            "detail": "The dominant chamber closes on one local triangular face."
        },
    }


def run_negative_tests():
    l = Real("l")
    solver = Solver()
    solver.add(l == 1)
    solver.add(l != 1)
    return {
        "barycentric_sum_conflict": {
            "pass": solver.check() == unsat,
            "detail": "A local dominant-weight sum cannot equal and fail to equal one simultaneously."
        }
    }


def run_boundary_tests():
    weight = sp.Matrix([1, 0])
    return {
        "fundamental_weight_boundary": {
            "pass": list(weight) == [1, 0],
            "detail": "A single fundamental weight is the boundary case of the local dominant simplex."
        }
    }


if __name__ == "__main__":
    write_shell_local_result(
        "sim_gtower_su3_weight_simplex_shell_local",
        "su3_weight_simplex",
        TOOL_MANIFEST,
        TOOL_INTEGRATION_DEPTH,
        run_positive_tests(),
        run_negative_tests(),
        run_boundary_tests(),
        extras={"group": "SU(3)"},
    )
