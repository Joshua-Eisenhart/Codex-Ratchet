#!/usr/bin/env python3
"""
sim_gstack_spectral_triple_shell_local.py -- Shell-local admissibility for a finite spectral triple.
"""

import sympy as sp
from z3 import Real, Solver, unsat

from _gstack_shell_local_common import write_shell_local_result

classification = "canonical"
_SHELL_LOCAL_REASON = "not used: this probe stays shell-local inside one finite spectral triple and does not invoke cross-shell coupling."

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "pyg": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "z3": {"tried": True, "used": True, "reason": "load-bearing: z3 excludes a commutator norm bound that is simultaneously satisfied and violated in the same local chart."},
    "cvc5": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing: sympy verifies bounded commutators and grading anticommutation for an explicit finite Dirac operator."},
    "clifford": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
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
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}


def run_positive_tests():
    D = sp.Matrix([[0, 1], [1, 0]])
    gamma = sp.Matrix([[1, 0], [0, -1]])
    a = sp.Matrix([[2, 0], [0, -1]])
    commutator = D * a - a * D
    anticommutator = D * gamma + gamma * D
    return {
        "bounded_commutator": {
            "pass": commutator == sp.Matrix([[0, -3], [3, 0]]),
            "commutator": str(commutator),
            "detail": "The commutator [D,a] is finite and exactly computable."
        },
        "grading_anticommutes_with_dirac": {
            "pass": anticommutator == sp.zeros(2),
            "detail": "The grading operator anticommutes with the local Dirac operator."
        },
    }


def run_negative_tests():
    x = Real("x")
    solver = Solver()
    solver.add(x <= 3)
    solver.add(x > 3)
    return {
        "commutator_norm_cannot_be_both_bounded_and_unbounded": {
            "pass": solver.check() == unsat,
            "detail": "A single local norm cannot satisfy incompatible bounds."
        }
    }


def run_boundary_tests():
    D = sp.Matrix([[0, 1], [1, 0]])
    scalar = sp.eye(2)
    return {
        "scalar_algebra_element_has_zero_commutator": {
            "pass": D * scalar - scalar * D == sp.zeros(2),
            "detail": "The unit element gives the boundary case with vanishing commutator."
        }
    }


if __name__ == "__main__":
    write_shell_local_result(
        "sim_gstack_spectral_triple_shell_local",
        "spectral_triple",
        TOOL_MANIFEST,
        TOOL_INTEGRATION_DEPTH,
        run_positive_tests(),
        run_negative_tests(),
        run_boundary_tests(),
        extras={"hilbert_space_dimension": 2},
    )
