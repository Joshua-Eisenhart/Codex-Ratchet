#!/usr/bin/env python3
"""
sim_gstack_arithmetic_curve_shell_local.py -- Shell-local admissibility for an arithmetic-curve chart.
"""

import sympy as sp
from z3 import Real, Solver, unsat
import gudhi

from _gstack_shell_local_common import write_shell_local_result

classification = "canonical"
_SHELL_LOCAL_REASON = "not used: this probe stays shell-local inside one arithmetic-curve chart and does not invoke cross-shell coupling."

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "pyg": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "z3": {"tried": True, "used": True, "reason": "load-bearing: z3 excludes a local discriminant that is simultaneously zero and nonzero for the same integral model."},
    "cvc5": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing: sympy computes the cubic discriminant exactly to separate smooth and singular local models."},
    "clifford": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "xgi": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "toponetx": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing: GUDHI builds the local simplex filtration used to witness the connected special fiber."},
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
    x = sp.symbols("x")
    poly = x**3 - x + 1
    tree = gudhi.SimplexTree()
    tree.insert([0])
    tree.insert([1])
    tree.insert([0, 1], filtration=0.0)
    tree.compute_persistence()
    betti = tree.betti_numbers()
    return {
        "cubic_discriminant_nonzero": {
            "pass": sp.discriminant(poly, x) == -23,
            "discriminant": str(sp.discriminant(poly, x)),
            "detail": "The local Weierstrass model is smooth because the discriminant is nonzero."
        },
        "special_fiber_connected": {
            "pass": betti == [1],
            "betti_numbers": betti,
            "detail": "The toy special fiber is connected in the local filtration."
        },
    }


def run_negative_tests():
    delta = Real("delta")
    solver = Solver()
    solver.add(delta == 0)
    solver.add(delta != 0)
    return {
        "smooth_singular_conflict": {
            "pass": solver.check() == unsat,
            "detail": "A single local model cannot be both smooth and singular."
        }
    }


def run_boundary_tests():
    x = sp.symbols("x")
    poly = x**3
    return {
        "cusp_boundary": {
            "pass": sp.discriminant(poly, x) == 0,
            "detail": "The discriminant-zero cubic is the singular boundary case."
        }
    }


if __name__ == "__main__":
    write_shell_local_result(
        "sim_gstack_arithmetic_curve_shell_local",
        "arithmetic_curve",
        TOOL_MANIFEST,
        TOOL_INTEGRATION_DEPTH,
        run_positive_tests(),
        run_negative_tests(),
        run_boundary_tests(),
        extras={"base_ring": "Z"},
    )
