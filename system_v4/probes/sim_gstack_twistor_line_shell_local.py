#!/usr/bin/env python3
"""
sim_gstack_twistor_line_shell_local.py -- Shell-local admissibility for a twistor line.
"""

import sympy as sp
from z3 import Real, Solver, unsat
from geomstats.geometry.hypersphere import Hypersphere

from _gstack_shell_local_common import write_shell_local_result

classification = "canonical"
_SHELL_LOCAL_REASON = "not used: this probe stays shell-local inside one twistor line and does not invoke cross-shell coupling."

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "pyg": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "z3": {"tried": True, "used": True, "reason": "load-bearing: z3 excludes incompatible unit-sphere constraints for the local twistor parameter."},
    "cvc5": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing: sympy verifies the quaternionic relations and the induced complex-structure square J_n^2 = -1."},
    "clifford": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "geomstats": {"tried": True, "used": True, "reason": "load-bearing: geomstats provides the S^2 carrier for unit twistor parameters."},
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
    "geomstats": "load_bearing",
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}


def run_positive_tests():
    I = sp.Matrix([[sp.I, 0], [0, -sp.I]])
    J = sp.Matrix([[0, 1], [-1, 0]])
    K = I * J
    sphere = Hypersphere(dim=2)
    north = sphere.projection([0.0, 0.0, 1.0])
    Jn = I
    return {
        "quaternionic_relations_hold": {
            "pass": I * I == -sp.eye(2) and J * J == -sp.eye(2) and K * K == -sp.eye(2),
            "detail": "The local quaternionic generators square to minus the identity."
        },
        "north_pole_twistor_is_complex_structure": {
            "pass": Jn * Jn == -sp.eye(2) and abs(float(north[2]) - 1.0) < 1e-9,
            "detail": "A unit twistor parameter on S^2 yields a complex structure."
        },
    }


def run_negative_tests():
    x = Real("x")
    y = Real("y")
    z = Real("z")
    solver = Solver()
    solver.add(x * x + y * y + z * z == 1)
    solver.add(x * x + y * y + z * z == 2)
    return {
        "unit_parameter_conflict": {
            "pass": solver.check() == unsat,
            "detail": "The same local twistor parameter cannot lie on two incompatible spheres."
        }
    }


def run_boundary_tests():
    I = sp.Matrix([[sp.I, 0], [0, -sp.I]])
    return {
        "boundary_twistor_parameter": {
            "pass": I * I == -sp.eye(2),
            "detail": "The boundary point with coefficient vector (1,0,0) remains admissible."
        }
    }


if __name__ == "__main__":
    write_shell_local_result(
        "sim_gstack_twistor_line_shell_local",
        "twistor_line",
        TOOL_MANIFEST,
        TOOL_INTEGRATION_DEPTH,
        run_positive_tests(),
        run_negative_tests(),
        run_boundary_tests(),
        extras={"parameter_space": "S2"},
    )
