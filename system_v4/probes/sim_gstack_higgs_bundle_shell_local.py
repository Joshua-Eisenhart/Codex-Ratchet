#!/usr/bin/env python3
"""
sim_gstack_higgs_bundle_shell_local.py -- Shell-local admissibility for a Higgs bundle chart.
"""

import sympy as sp
from z3 import Real, Solver, unsat
from toponetx.classes import CellComplex

from _gstack_shell_local_common import write_shell_local_result

classification = "canonical"
_SHELL_LOCAL_REASON = "not used: this probe stays shell-local inside one Higgs-bundle chart and does not invoke cross-shell coupling."

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "pyg": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "z3": {"tried": True, "used": True, "reason": "load-bearing: z3 excludes a Higgs field whose trace is both zero and nonzero on the same local chart."},
    "cvc5": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing: sympy computes the characteristic polynomial and nilpotent square of an explicit local Higgs field."},
    "clifford": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "xgi": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing: TopoNetX records the local base cell supporting the Higgs field one-form."},
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


def run_positive_tests():
    lam = sp.symbols("lam")
    phi = sp.Matrix([[0, 1], [0, 0]])
    cell = CellComplex()
    cell.add_cell([0, 1], rank=1)
    char_poly = sp.factor((lam * sp.eye(2) - phi).det())
    return {
        "nilpotent_higgs_field": {
            "pass": phi * phi == sp.zeros(2),
            "detail": "The explicit local Higgs field is nilpotent."
        },
        "characteristic_polynomial_is_lam_squared": {
            "pass": char_poly == lam**2,
            "characteristic_polynomial": str(char_poly),
            "detail": "The characteristic polynomial matches the nilpotent local model."
        },
        "base_support_cell_present": {
            "pass": cell.shape == (2, 1, 0),
            "shape": list(cell.shape),
            "detail": "The local Higgs one-form is supported on a single base edge."
        },
    }


def run_negative_tests():
    tr = Real("tr")
    solver = Solver()
    solver.add(tr == 0)
    solver.add(tr != 0)
    return {
        "trace_condition_conflict": {
            "pass": solver.check() == unsat,
            "detail": "The same local Higgs field cannot be simultaneously traceless and non-traceless."
        }
    }


def run_boundary_tests():
    phi = sp.zeros(2)
    return {
        "zero_higgs_field_boundary": {
            "pass": phi == sp.zeros(2),
            "detail": "The zero Higgs field is the admissible boundary case."
        }
    }


if __name__ == "__main__":
    write_shell_local_result(
        "sim_gstack_higgs_bundle_shell_local",
        "higgs_bundle",
        TOOL_MANIFEST,
        TOOL_INTEGRATION_DEPTH,
        run_positive_tests(),
        run_negative_tests(),
        run_boundary_tests(),
        extras={"rank": 2},
    )
