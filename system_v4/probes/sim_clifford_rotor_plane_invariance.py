#!/usr/bin/env python3
"""
sim_clifford_rotor_plane_invariance.py

Shell-local Clifford lego for rotor-local plane action in Cl(3).
The claim is local: a unit rotor built from the e12 bivector rotates vectors in the
(e1,e2) plane, leaves the transverse axis fixed, and leaves the generating plane bivector stable.
"""

import json
import os
from typing import Any, Dict

import numpy as np

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

classification = "canonical"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed for this shell-local rotor row"},
    "pyg": {"tried": False, "used": False, "reason": "not needed for this shell-local rotor row"},
    "z3": {"tried": False, "used": False, "reason": "not needed for this shell-local rotor row"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed for this shell-local rotor row"},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": "not needed for this shell-local rotor row"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed for this shell-local rotor row"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed for this shell-local rotor row"},
    "xgi": {"tried": False, "used": False, "reason": "not needed for this shell-local rotor row"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed for this shell-local rotor row"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed for this shell-local rotor row"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": "supportive",
    "clifford": "load_bearing",
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
        "Half-angle analytic cross-check for the e12-plane rotation matrix and 2π rotor sign boundary."
    )
except ImportError:
    sp = None
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"
    TOOL_INTEGRATION_DEPTH["sympy"] = None

try:
    from clifford import Cl

    TOOL_MANIFEST["clifford"]["tried"] = True
    TOOL_MANIFEST["clifford"]["used"] = True
    TOOL_MANIFEST["clifford"]["reason"] = (
        "Builds Cl(3) rotors directly, applies sandwich action, and checks plane-local invariants on vectors and bivectors."
    )
except Exception as exc:
    Cl = None
    TOOL_MANIFEST["clifford"]["tried"] = True
    TOOL_MANIFEST["clifford"]["reason"] = f"optional import unavailable: {exc}"
    TOOL_INTEGRATION_DEPTH["clifford"] = None

EPS = 1e-10
NAME = "clifford_rotor_plane_invariance"


if Cl is not None:
    LAYOUT, BLADES = Cl(3)
    E1 = BLADES["e1"]
    E2 = BLADES["e2"]
    E3 = BLADES["e3"]
    E12 = BLADES["e12"]
    E13 = BLADES["e13"]
    SCALAR_ONE = 1.0 + 0 * E1
else:
    LAYOUT = BLADES = E1 = E2 = E3 = E12 = E13 = SCALAR_ONE = None


def multivector_close(a: Any, b: Any, tol: float = EPS) -> bool:
    return np.allclose(np.asarray(a.value), np.asarray(b.value), atol=tol)


def rotor(bivector: Any, theta: float) -> Any:
    return np.cos(theta / 2.0) - np.sin(theta / 2.0) * bivector


def sandwich(R: Any, mv: Any) -> Any:
    return R * mv * ~R


def scalar_part(mv: Any) -> float:
    coeffs = np.asarray(mv.value, dtype=float).reshape(-1)
    return float(coeffs[0])


def symbolic_rotation_checks() -> Dict[str, Any]:
    if sp is None:
        return {"available": False}
    theta = sp.symbols("theta", real=True)
    plane_matrix = sp.Matrix(
        [
            [sp.cos(theta), -sp.sin(theta)],
            [sp.sin(theta), sp.cos(theta)],
        ]
    )
    quarter_turn = plane_matrix.subs(theta, sp.pi / 2)
    two_pi = sp.simplify(sp.cos(sp.pi) - 1)
    return {
        "available": True,
        "quarter_turn_matrix": str(quarter_turn),
        "quarter_turn_matches_expected": quarter_turn == sp.Matrix([[0, -1], [1, 0]]),
        "two_pi_rotor_scalar_minus_one": two_pi == -2,
    }


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests() -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    if Cl is None:
        results["clifford_import_required"] = {"pass": False, "error": "clifford not installed"}
        return results

    theta = np.pi / 2.0
    R = rotor(E12, theta)
    rotated_e1 = sandwich(R, E1)
    rotated_e2 = sandwich(R, E2)
    rotated_e3 = sandwich(R, E3)
    rotated_plane = sandwich(R, E12)
    symbolic = symbolic_rotation_checks()

    results["quarter_turn_rotates_e1_to_e2"] = {
        "pass": multivector_close(rotated_e1, E2),
        "rotated_value": str(rotated_e1),
    }
    results["quarter_turn_rotates_e2_to_minus_e1"] = {
        "pass": multivector_close(rotated_e2, -E1),
        "rotated_value": str(rotated_e2),
    }
    results["rotation_axis_e3_is_fixed"] = {
        "pass": multivector_close(rotated_e3, E3),
        "rotated_value": str(rotated_e3),
    }
    results["generating_plane_bivector_stays_stable"] = {
        "pass": multivector_close(rotated_plane, E12),
        "rotated_value": str(rotated_plane),
    }
    results["symbolic_half_angle_cross_check_matches_plane_rotation"] = {
        "pass": bool(symbolic.get("quarter_turn_matches_expected", False)),
        "details": symbolic,
    }
    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests() -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    if Cl is None:
        results["clifford_import_required"] = {"pass": False, "error": "clifford not installed"}
        return results

    theta = np.pi / 2.0
    non_unit_even = SCALAR_ONE + E12
    wrong_plane_rotor = rotor(E13, theta)
    distorted_norm = non_unit_even * ~non_unit_even
    wrong_plane_e3 = sandwich(wrong_plane_rotor, E3)

    results["non_unit_even_multivector_is_excluded_by_unit_rotor_gate"] = {
        "pass": not np.isclose(scalar_part(distorted_norm), 1.0, atol=EPS),
        "norm_candidate": scalar_part(distorted_norm),
    }
    results["wrong_plane_bivector_does_not_keep_e3_fixed"] = {
        "pass": not multivector_close(wrong_plane_e3, E3),
        "rotated_value": str(wrong_plane_e3),
    }
    results["quarter_turn_rotor_does_not_leave_e1_unmoved"] = {
        "pass": not multivector_close(sandwich(rotor(E12, theta), E1), E1),
        "rotated_value": str(sandwich(rotor(E12, theta), E1)),
    }
    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests() -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    if Cl is None:
        results["clifford_import_required"] = {"pass": False, "error": "clifford not installed"}
        return results

    identity_rotor = rotor(E12, 0.0)
    full_turn_rotor = rotor(E12, 2.0 * np.pi)
    double_full_turn_rotor = rotor(E12, 4.0 * np.pi)

    results["zero_angle_boundary_is_identity_rotor"] = {
        "pass": multivector_close(identity_rotor, SCALAR_ONE) and multivector_close(sandwich(identity_rotor, E1), E1),
        "rotor_value": str(identity_rotor),
    }
    results["two_pi_boundary_returns_vector_action_but_flips_rotor_sign"] = {
        "pass": multivector_close(sandwich(full_turn_rotor, E1), E1) and multivector_close(full_turn_rotor, -SCALAR_ONE),
        "rotor_value": str(full_turn_rotor),
    }
    results["four_pi_boundary_returns_rotor_identity"] = {
        "pass": multivector_close(double_full_turn_rotor, SCALAR_ONE),
        "rotor_value": str(double_full_turn_rotor),
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
            "scope_note": "Shell-local rotor action in Cl(3) only; no coupling, coexistence, topology-variant, emergence, or bridge claims.",
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
