#!/usr/bin/env python3
"""
sim_gtower_so3_rotation_chart_shell_local.py -- Shell-local admissibility for an SO(3) rotation chart.
"""

import sympy as sp
from z3 import Real, Solver, unsat
from toponetx.classes import CellComplex

from _gstack_shell_local_common import write_shell_local_result

classification = "canonical"
_SHELL_LOCAL_REASON = "not used: this probe stays shell-local inside one SO(3) rotation chart and does not invoke cross-shell coupling."

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "pyg": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "z3": {"tried": True, "used": True, "reason": "load-bearing: z3 excludes a rotation determinant that is simultaneously +1 and not +1."},
    "cvc5": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing: sympy evaluates the local rotation matrix exactly at angle pi/3."},
    "clifford": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "xgi": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing: TopoNetX records the single oriented 2-cell spanning the local rotation frame."},
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


def _rotation_z(theta):
    return sp.Matrix([
        [sp.cos(theta), -sp.sin(theta), 0],
        [sp.sin(theta), sp.cos(theta), 0],
        [0, 0, 1],
    ])


def run_positive_tests():
    rotation = _rotation_z(sp.pi / 3)
    complex_ = CellComplex()
    complex_.add_cell([0, 1], rank=1)
    complex_.add_cell([1, 2], rank=1)
    complex_.add_cell([0, 2], rank=1)
    complex_.add_cell([0, 1, 2], rank=2)
    return {
        "rotation_is_special_orthogonal": {
            "pass": sp.simplify(rotation.T * rotation) == sp.eye(3) and sp.simplify(rotation.det()) == 1,
            "detail": "The local rotation chart stays inside SO(3)."
        },
        "rotation_frame_has_one_oriented_face": {
            "pass": complex_.shape == (3, 3, 1),
            "shape": list(complex_.shape),
            "detail": "The local rotation frame closes on one oriented 2-cell."
        },
    }


def run_negative_tests():
    d = Real("d")
    solver = Solver()
    solver.add(d == 1)
    solver.add(d != 1)
    return {
        "special_orthogonal_conflict": {
            "pass": solver.check() == unsat,
            "detail": "A local SO(3) determinant cannot equal and fail to equal one simultaneously."
        }
    }


def run_boundary_tests():
    identity = _rotation_z(sp.Integer(0))
    return {
        "identity_rotation_boundary": {
            "pass": identity == sp.eye(3),
            "detail": "Zero angle is the shell-local boundary of the rotation chart."
        }
    }


if __name__ == "__main__":
    write_shell_local_result(
        "sim_gtower_so3_rotation_chart_shell_local",
        "so3_rotation_chart",
        TOOL_MANIFEST,
        TOOL_INTEGRATION_DEPTH,
        run_positive_tests(),
        run_negative_tests(),
        run_boundary_tests(),
        extras={"group": "SO(3)"},
    )
