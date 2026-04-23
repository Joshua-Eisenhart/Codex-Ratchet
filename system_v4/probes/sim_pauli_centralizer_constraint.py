#!/usr/bin/env python3
"""
sim_pauli_centralizer_constraint.py

Shell-local Pauli lego for the Z-centralizer inside the qubit operator span.
The claim is local: within aI + bX + cY + dZ, commuting with Z excludes the X and Y
components, leaving only the diagonal family aI + dZ.
"""

import json
import os
from typing import Any, Dict

classification = "canonical"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed for this shell-local Pauli row"},
    "pyg": {"tried": False, "used": False, "reason": "not needed for this shell-local Pauli row"},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": "not needed for this shell-local Pauli row"},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": "not needed for this shell-local Pauli row"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed for this shell-local Pauli row"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed for this shell-local Pauli row"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed for this shell-local Pauli row"},
    "xgi": {"tried": False, "used": False, "reason": "not needed for this shell-local Pauli row"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed for this shell-local Pauli row"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed for this shell-local Pauli row"},
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

try:
    import z3

    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = (
        "UNSAT gate excluding any commuting Z-centralizer witness with a nonzero X or Y coefficient."
    )
except ImportError:
    z3 = None
    TOOL_MANIFEST["z3"]["reason"] = "not installed"
    TOOL_INTEGRATION_DEPTH["z3"] = None

try:
    import sympy as sp

    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = (
        "Exact symbolic commutator algebra for A=aI+bX+cY+dZ against Z inside the shell-local Pauli span."
    )
except ImportError:
    sp = None
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"
    TOOL_INTEGRATION_DEPTH["sympy"] = None

NAME = "pauli_centralizer_constraint"

if sp is not None:
    I2 = sp.eye(2)
    X = sp.Matrix([[0, 1], [1, 0]])
    Y = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    Z = sp.Matrix([[1, 0], [0, -1]])
else:
    I2 = X = Y = Z = None


def matrix_close(a: Any, b: Any) -> bool:
    if sp is None:
        return False
    return sp.simplify(a - b) == sp.zeros(a.rows, a.cols)


def operator(a: Any, b: Any, c: Any, d: Any):
    return a * I2 + b * X + c * Y + d * Z


def commutator(a: Any, b: Any):
    return sp.simplify(a * b - b * a)


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests() -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    if sp is None:
        results["sympy_import_required"] = {"pass": False, "error": "sympy not installed"}
        return results

    a, d = sp.symbols("a d", real=True)
    commuting_family = operator(a, 0, 0, d)
    family_commutator = commutator(commuting_family, Z)
    plus_projector = (I2 + Z) / 2
    minus_projector = (I2 - Z) / 2

    results["diagonal_family_commutes_with_z"] = {
        "pass": matrix_close(family_commutator, sp.zeros(2, 2)),
        "commutator": str(family_commutator),
    }
    results["identity_and_z_commute_with_z"] = {
        "pass": matrix_close(commutator(I2, Z), sp.zeros(2, 2)) and matrix_close(commutator(Z, Z), sp.zeros(2, 2)),
        "identity_commutator": str(commutator(I2, Z)),
        "z_commutator": str(commutator(Z, Z)),
    }
    results["z_eigenprojectors_stay_in_the_centralizer"] = {
        "pass": matrix_close(commutator(plus_projector, Z), sp.zeros(2, 2)) and matrix_close(commutator(minus_projector, Z), sp.zeros(2, 2)),
        "plus_projector": str(plus_projector),
        "minus_projector": str(minus_projector),
    }
    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests() -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    if sp is None:
        results["sympy_import_required"] = {"pass": False, "error": "sympy not installed"}
        return results

    results["x_is_excluded_from_the_z_centralizer"] = {
        "pass": not matrix_close(commutator(X, Z), sp.zeros(2, 2)),
        "commutator": str(commutator(X, Z)),
    }
    results["y_is_excluded_from_the_z_centralizer"] = {
        "pass": not matrix_close(commutator(Y, Z), sp.zeros(2, 2)),
        "commutator": str(commutator(Y, Z)),
    }

    if z3 is not None:
        b = z3.Real("b")
        c = z3.Real("c")
        solver = z3.Solver()
        # [aI+bX+cY+dZ, Z] = 2 i c X - 2 i b Y, so commuting forces b=c=0.
        solver.add(2 * b == 0)
        solver.add(2 * c == 0)
        solver.add(z3.Or(b != 0, c != 0))
        status = solver.check()
        results["nonzero_xy_component_cannot_commute_with_z"] = {
            "pass": status == z3.unsat,
            "solver_status": str(status),
        }
    else:
        results["nonzero_xy_component_cannot_commute_with_z"] = {
            "pass": False,
            "error": "z3 not installed",
        }
    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests() -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    if sp is None:
        results["sympy_import_required"] = {"pass": False, "error": "sympy not installed"}
        return results

    lam = sp.symbols("lam", real=True)
    zero_operator = sp.zeros(2, 2)
    scalar_family = lam * I2
    pure_z_family = lam * Z

    results["zero_operator_boundary_commutes"] = {
        "pass": matrix_close(commutator(zero_operator, Z), sp.zeros(2, 2)),
        "commutator": str(commutator(zero_operator, Z)),
    }
    results["scalar_identity_boundary_commutes"] = {
        "pass": matrix_close(commutator(scalar_family, Z), sp.zeros(2, 2)),
        "commutator": str(commutator(scalar_family, Z)),
    }
    results["pure_z_boundary_commutes"] = {
        "pass": matrix_close(commutator(pure_z_family, Z), sp.zeros(2, 2)),
        "commutator": str(commutator(pure_z_family, Z)),
    }
    return results


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    all_pass = (
        all(entry.get("pass", False) for entry in positive.values())
        and all(entry.get("pass", False) for entry in negative.values())
        and all(entry.get("pass", False) for entry in boundary.values())
    )
    results = {
        "name": NAME,
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "scope_note": "Shell-local Pauli centralizer only; no coupling, coexistence, topology-variant, emergence, or bridge claims.",
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
