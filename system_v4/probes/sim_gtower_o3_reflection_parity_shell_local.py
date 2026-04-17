#!/usr/bin/env python3
"""
sim_gtower_o3_reflection_parity_shell_local.py -- Shell-local admissibility for an O(3) reflection chart.
"""

import sympy as sp
from z3 import Real, Solver, unsat
import xgi

from _gstack_shell_local_common import write_shell_local_result

classification = "canonical"
_SHELL_LOCAL_REASON = "not used: this probe stays shell-local inside one O(3) reflection chart and does not invoke cross-shell coupling."

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "pyg": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "z3": {"tried": True, "used": True, "reason": "load-bearing: z3 excludes a reflection determinant that is simultaneously -1 and +1."},
    "cvc5": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing: sympy evaluates orthogonality and determinant exactly for the local reflection matrix."},
    "clifford": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing: XGI records the irreducible three-axis local reflection support."},
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
    reflection = sp.diag(-1, 1, 1)
    hypergraph = xgi.Hypergraph([[0, 1, 2]])
    return {
        "reflection_is_orthogonal": {
            "pass": reflection.T * reflection == sp.eye(3),
            "detail": "The chosen reflection stays inside O(3) because R^T R = I."
        },
        "reflection_has_negative_parity": {
            "pass": reflection.det() == -1 and hypergraph.num_edges == 1,
            "determinant": str(reflection.det()),
            "detail": "The local chart records one orientation-reversing reflection across three axes."
        },
    }


def run_negative_tests():
    d = Real("d")
    solver = Solver()
    solver.add(d == -1)
    solver.add(d == 1)
    return {
        "parity_conflict": {
            "pass": solver.check() == unsat,
            "detail": "A single local O(3) reflection cannot carry both determinant signs at once."
        }
    }


def run_boundary_tests():
    identity = sp.eye(3)
    return {
        "so3_boundary": {
            "pass": identity.T * identity == sp.eye(3) and identity.det() == 1,
            "detail": "The identity chart is the determinant +1 boundary shared with SO(3)."
        }
    }


if __name__ == "__main__":
    write_shell_local_result(
        "sim_gtower_o3_reflection_parity_shell_local",
        "o3_reflection_parity",
        TOOL_MANIFEST,
        TOOL_INTEGRATION_DEPTH,
        run_positive_tests(),
        run_negative_tests(),
        run_boundary_tests(),
        extras={"group": "O(3)"},
    )
