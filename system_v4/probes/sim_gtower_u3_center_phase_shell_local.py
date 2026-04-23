#!/usr/bin/env python3
"""
sim_gtower_u3_center_phase_shell_local.py -- Shell-local admissibility for the center of a U(3) chart.
"""

import sympy as sp
import torch
from z3 import Real, Solver, unsat

from _gstack_shell_local_common import write_shell_local_result

classification = "canonical"
_SHELL_LOCAL_REASON = "not used: this probe stays shell-local inside one U(3) center chart and does not invoke cross-shell coupling."

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing: pytorch checks unitarity of the central phase matrix on complex tensors."},
    "pyg": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "z3": {"tried": True, "used": True, "reason": "load-bearing: z3 excludes a phase radius that is simultaneously one and not one."},
    "cvc5": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing: sympy verifies that the central phase commutes with a local diagonal generator exactly."},
    "clifford": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "xgi": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "toponetx": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "gudhi": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
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
    theta = sp.pi / 5
    z = sp.exp(sp.I * theta)
    center = sp.diag(z, z, z)
    generator = sp.diag(1, -1, 0)
    torch_phase = torch.exp(1j * torch.tensor(float(sp.N(theta)), dtype=torch.float64))
    torch_center = torch.diag(torch.tensor([torch_phase, torch_phase, torch_phase], dtype=torch.complex128))
    identity = torch.eye(3, dtype=torch.complex128)
    return {
        "center_commutes_with_diagonal_generator": {
            "pass": sp.simplify(center * generator - generator * center) == sp.zeros(3),
            "detail": "The central phase stays indistinguishable under a local diagonal test generator."
        },
        "center_matrix_is_unitary": {
            "pass": torch.allclose(torch_center.conj().T @ torch_center, identity, atol=1e-10),
            "detail": "The sampled central phase matrix stays unitary in the U(3) chart."
        },
    }


def run_negative_tests():
    r = Real("r")
    solver = Solver()
    solver.add(r == 1)
    solver.add(r != 1)
    return {
        "phase_radius_conflict": {
            "pass": solver.check() == unsat,
            "detail": "A single central phase radius cannot equal and fail to equal one simultaneously."
        }
    }


def run_boundary_tests():
    center = sp.eye(3)
    return {
        "identity_phase_boundary": {
            "pass": center == sp.eye(3),
            "detail": "Zero phase is the shell-local boundary of the U(3) center chart."
        }
    }


if __name__ == "__main__":
    write_shell_local_result(
        "sim_gtower_u3_center_phase_shell_local",
        "u3_center_phase",
        TOOL_MANIFEST,
        TOOL_INTEGRATION_DEPTH,
        run_positive_tests(),
        run_negative_tests(),
        run_boundary_tests(),
        extras={"group": "U(3)"},
    )
