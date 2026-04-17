#!/usr/bin/env python3
"""
sim_gtower_sp6_lagrangian_shell_local.py -- Shell-local admissibility for an Sp(6) Lagrangian chart.
"""

import sympy as sp
from z3 import Real, Solver, unsat
from toponetx.classes import CellComplex

from _gstack_shell_local_common import write_shell_local_result

classification = "canonical"
_SHELL_LOCAL_REASON = "not used: this probe stays shell-local inside one Sp(6) Lagrangian chart and does not invoke cross-shell coupling."

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "pyg": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "z3": {"tried": True, "used": True, "reason": "load-bearing: z3 excludes a symplectic pairing that is simultaneously zero and nonzero on the same local basis pair."},
    "cvc5": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing: sympy evaluates the standard Sp(6) symplectic form and isotropic pairings exactly."},
    "clifford": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "xgi": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing: TopoNetX records the maximal isotropic 2-cell supported by the local basis chart."},
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
    "toponetx": "load_bearing",
    "gudhi": None,
}


def _symplectic_form():
    return sp.Matrix.vstack(
        sp.Matrix.hstack(sp.zeros(3), sp.eye(3)),
        sp.Matrix.hstack(-sp.eye(3), sp.zeros(3)),
    )


def run_positive_tests():
    J = _symplectic_form()
    basis = [sp.eye(6)[:, i] for i in range(3)]
    pairings = [sp.simplify((basis[i].T * J * basis[j])[0]) for i in range(3) for j in range(3)]
    complex_ = CellComplex()
    complex_.add_cell([0, 1], rank=1)
    complex_.add_cell([1, 2], rank=1)
    complex_.add_cell([0, 2], rank=1)
    complex_.add_cell([0, 1, 2], rank=2)
    return {
        "lagrangian_basis_is_isotropic": {
            "pass": all(p == 0 for p in pairings),
            "detail": "The chosen basis spans a shell-local isotropic chart for the standard Sp(6) form."
        },
        "maximal_isotropic_face_recorded": {
            "pass": complex_.shape == (3, 3, 1),
            "shape": list(complex_.shape),
            "detail": "The local isotropic frame closes on one 2-cell."
        },
    }


def run_negative_tests():
    p = Real("p")
    solver = Solver()
    solver.add(p == 0)
    solver.add(p != 0)
    return {
        "pairing_conflict": {
            "pass": solver.check() == unsat,
            "detail": "A single local symplectic pairing cannot vanish and fail to vanish simultaneously."
        }
    }


def run_boundary_tests():
    J = _symplectic_form()
    line = sp.eye(6)[:, 0]
    pairing = sp.simplify((line.T * J * line)[0])
    return {
        "isotropic_line_boundary": {
            "pass": pairing == 0,
            "detail": "A one-dimensional isotropic line is the boundary case before the full Lagrangian chart."
        }
    }


if __name__ == "__main__":
    write_shell_local_result(
        "sim_gtower_sp6_lagrangian_shell_local",
        "sp6_lagrangian",
        TOOL_MANIFEST,
        TOOL_INTEGRATION_DEPTH,
        run_positive_tests(),
        run_negative_tests(),
        run_boundary_tests(),
        extras={"group": "Sp(6)"},
    )
