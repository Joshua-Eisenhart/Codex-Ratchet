#!/usr/bin/env python3
"""
sim_pauli_projector_reconstruction.py

Shell-local Pauli lego for recovering qubit projectors from Bloch-axis data.
The claim is local: rho(n) = (I + n·sigma)/2 gives rank-1 projectors on unit axes,
rejects overlong Bloch witnesses, and has the maximally mixed boundary at n = 0.
"""

import json
import os
from typing import Any, Dict, Tuple

classification = "canonical"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed for this shell-local Pauli row"},
    "pyg": {"tried": False, "used": False, "reason": "not needed for this shell-local Pauli row"},
    "z3": {"tried": False, "used": False, "reason": "not needed for this shell-local Pauli row"},
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
    "z3": None,
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
    import sympy as sp

    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = (
        "Exact symbolic projector algebra for rho(n)=(I+n·sigma)/2, including idempotency, trace, determinant, and axis recovery."
    )
except ImportError:
    sp = None
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"
    TOOL_INTEGRATION_DEPTH["sympy"] = None

NAME = "pauli_projector_reconstruction"

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
    return (sp.simplify(a - b) == sp.zeros(a.rows, a.cols))


def bloch_projector(nx: Any, ny: Any, nz: Any):
    return sp.simplify((I2 + nx * X + ny * Y + nz * Z) / 2)


def projector_summary(rho: Any, axis: Tuple[Any, Any, Any]) -> Dict[str, Any]:
    rho_sq = sp.simplify(rho * rho)
    return {
        "axis": [str(v) for v in axis],
        "trace": str(sp.simplify(rho.trace())),
        "det": str(sp.simplify(rho.det())),
        "idempotent": matrix_close(rho_sq, rho),
        "hermitian": rho.H == rho,
        "matrix": str(rho),
    }


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests() -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    if sp is None:
        results["sympy_import_required"] = {"pass": False, "error": "sympy not installed"}
        return results

    rho_z_plus = bloch_projector(0, 0, 1)
    rho_x_plus = bloch_projector(1, 0, 0)
    rho_y_plus = bloch_projector(0, 1, 0)

    ket0_projector = sp.Matrix([[1, 0], [0, 0]])
    x_plus_expected = sp.Matrix([[sp.Rational(1, 2), sp.Rational(1, 2)], [sp.Rational(1, 2), sp.Rational(1, 2)]])
    y_plus_expected = sp.Matrix(
        [
            [sp.Rational(1, 2), -sp.I / 2],
            [sp.I / 2, sp.Rational(1, 2)],
        ]
    )

    results["z_axis_projector_matches_ket0"] = {
        "pass": matrix_close(rho_z_plus, ket0_projector),
        "details": projector_summary(rho_z_plus, (0, 0, 1)),
    }
    results["x_axis_projector_matches_plus_state"] = {
        "pass": matrix_close(rho_x_plus, x_plus_expected),
        "details": projector_summary(rho_x_plus, (1, 0, 0)),
    }
    results["y_axis_projector_matches_plus_i_state"] = {
        "pass": matrix_close(rho_y_plus, y_plus_expected),
        "details": projector_summary(rho_y_plus, (0, 1, 0)),
    }
    results["unit_axis_projectors_are_rank_one"] = {
        "pass": all(projector_summary(rho, axis)["idempotent"] and projector_summary(rho, axis)["trace"] == "1" and projector_summary(rho, axis)["det"] == "0" for rho, axis in [
            (rho_z_plus, (0, 0, 1)),
            (rho_x_plus, (1, 0, 0)),
            (rho_y_plus, (0, 1, 0)),
        ]),
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

    rho_overlong = bloch_projector(2, 0, 0)
    rho_wrong_sign = bloch_projector(0, 0, -1)
    ket0_projector = sp.Matrix([[1, 0], [0, 0]])

    results["overlong_bloch_vector_is_not_idempotent"] = {
        "pass": not matrix_close(sp.simplify(rho_overlong * rho_overlong), rho_overlong),
        "details": projector_summary(rho_overlong, (2, 0, 0)),
    }
    results["south_pole_projector_is_not_ket0"] = {
        "pass": not matrix_close(rho_wrong_sign, ket0_projector),
        "details": projector_summary(rho_wrong_sign, (0, 0, -1)),
    }
    results["overlong_bloch_vector_has_negative_determinant"] = {
        "pass": sp.simplify(rho_overlong.det()) < 0,
        "det": str(sp.simplify(rho_overlong.det())),
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

    rho_mixed = bloch_projector(0, 0, 0)
    rho_z_minus = bloch_projector(0, 0, -1)
    expected_mixed = I2 / 2
    ket1_projector = sp.Matrix([[0, 0], [0, 1]])

    results["zero_vector_boundary_is_maximally_mixed"] = {
        "pass": matrix_close(rho_mixed, expected_mixed) and not matrix_close(sp.simplify(rho_mixed * rho_mixed), rho_mixed),
        "details": projector_summary(rho_mixed, (0, 0, 0)),
    }
    results["south_pole_boundary_matches_ket1"] = {
        "pass": matrix_close(rho_z_minus, ket1_projector),
        "details": projector_summary(rho_z_minus, (0, 0, -1)),
    }
    results["north_and_south_poles_partition_z_measurement"] = {
        "pass": matrix_close(bloch_projector(0, 0, 1) + rho_z_minus, I2),
        "sum_matrix": str(sp.simplify(bloch_projector(0, 0, 1) + rho_z_minus)),
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
            "scope_note": "Shell-local Pauli projector reconstruction only; no coupling, coexistence, topology-variant, emergence, or bridge claims.",
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
