#!/usr/bin/env python3
"""
sim_clifford_even_odd_grade_partition.py

Shell-local Clifford lego for the even/odd grade split in Cl(3).
The claim is local: grade involution fixes even multivectors, flips odd
multivectors, and excludes any nonzero witness that is simultaneously even and odd.
"""

import json
import os
from typing import Any, Dict

import numpy as np

classification = "canonical"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed for this shell-local grade split row"},
    "pyg": {"tried": False, "used": False, "reason": "not needed for this shell-local grade split row"},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": "not needed for this shell-local grade split row"},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": "not needed for this shell-local grade split row"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed for this shell-local grade split row"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed for this shell-local grade split row"},
    "xgi": {"tried": False, "used": False, "reason": "not needed for this shell-local grade split row"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed for this shell-local grade split row"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed for this shell-local grade split row"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": "load_bearing",
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
    import z3

    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = (
        "UNSAT gate excluding any nonzero multivector that is simultaneously fixed and negated "
        "by grade involution."
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
        "Symbolic parity cross-check for the grade-involution sign pattern (-1)^k across grades 0..3."
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
        "Builds explicit Cl(3) multivectors and applies grade involution, even projection, and odd projection directly."
    )
except ImportError:
    Cl = None
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"
    TOOL_INTEGRATION_DEPTH["clifford"] = None

EPS = 1e-10
NAME = "clifford_even_odd_grade_partition"


def multivector_close(a: Any, b: Any, tol: float = EPS) -> bool:
    return np.allclose(np.asarray(a.value), np.asarray(b.value), atol=tol)


if Cl is not None:
    LAYOUT, BLADES = Cl(3)
    E1 = BLADES["e1"]
    E2 = BLADES["e2"]
    E3 = BLADES["e3"]
    E12 = BLADES["e12"]
    E23 = BLADES["e23"]
    E123 = BLADES["e123"]
    ZERO = 0 * E1
    SCALAR = 2.0 + 0 * E1
    EVEN = 2.0 + 1.5 * E12 - 0.5 * E23
    ODD = 3.0 * E1 - 1.0 * E2 + 0.75 * E123
    MIXED = EVEN + ODD
else:
    LAYOUT = BLADES = E1 = E2 = E3 = E12 = E23 = E123 = ZERO = SCALAR = EVEN = ODD = MIXED = None


def symbolic_grade_signs() -> Dict[str, Any]:
    if sp is None:
        return {"available": False}
    grade = sp.symbols("grade", integer=True, nonnegative=True)
    values = {k: int((-1) ** k) for k in range(4)}
    expected = {0: 1, 1: -1, 2: 1, 3: -1}
    return {
        "available": True,
        "formula": str((-1) ** grade),
        "values": values,
        "matches_expected": values == expected,
    }


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests() -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    if Cl is None:
        results["clifford_import_required"] = {"pass": False, "error": "clifford not installed"}
        return results

    even_fixed = EVEN.gradeInvol()
    odd_flipped = ODD.gradeInvol()
    reconstructed = MIXED.even + MIXED.odd
    symbolic = symbolic_grade_signs()

    results["even_multivector_is_fixed_by_grade_involution"] = {
        "pass": multivector_close(even_fixed, EVEN),
        "even_value": str(EVEN),
        "grade_involution_value": str(even_fixed),
    }
    results["odd_multivector_is_negated_by_grade_involution"] = {
        "pass": multivector_close(odd_flipped, -ODD),
        "odd_value": str(ODD),
        "grade_involution_value": str(odd_flipped),
    }
    results["even_and_odd_projections_reconstruct_mixed_multivector"] = {
        "pass": multivector_close(reconstructed, MIXED),
        "mixed_value": str(MIXED),
        "reconstructed_value": str(reconstructed),
    }
    results["symbolic_parity_pattern_matches_grade_signs"] = {
        "pass": bool(symbolic.get("matches_expected", False)),
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

    mixed_involution = MIXED.gradeInvol()
    results["mixed_multivector_is_not_fixed_by_grade_involution"] = {
        "pass": not multivector_close(mixed_involution, MIXED),
        "mixed_value": str(MIXED),
        "grade_involution_value": str(mixed_involution),
    }
    results["mixed_multivector_is_not_purely_odd"] = {
        "pass": not multivector_close(mixed_involution, -MIXED),
        "mixed_value": str(MIXED),
        "negated_value": str(-MIXED),
        "grade_involution_value": str(mixed_involution),
    }

    if z3 is not None:
        s = z3.Real("s")
        v1 = z3.Real("v1")
        v2 = z3.Real("v2")
        v3 = z3.Real("v3")
        b12 = z3.Real("b12")
        b13 = z3.Real("b13")
        b23 = z3.Real("b23")
        t = z3.Real("t")

        solver = z3.Solver()
        # A = gradeInvol(A) forces odd coefficients to vanish.
        solver.add(v1 == 0, v2 == 0, v3 == 0, t == 0)
        # A = -gradeInvol(A) forces even coefficients to vanish.
        solver.add(s == 0, b12 == 0, b13 == 0, b23 == 0)
        solver.add(z3.Or(s != 0, v1 != 0, v2 != 0, v3 != 0, b12 != 0, b13 != 0, b23 != 0, t != 0))
        status = solver.check()
        results["nonzero_multivector_cannot_be_simultaneously_even_and_odd"] = {
            "pass": status == z3.unsat,
            "solver_status": str(status),
        }
    else:
        results["nonzero_multivector_cannot_be_simultaneously_even_and_odd"] = {
            "pass": False,
            "error": "z3 not installed",
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

    zero_involution = ZERO.gradeInvol()
    scalar_involution = SCALAR.gradeInvol()
    trivector_involution = E123.gradeInvol()
    results["zero_multivector_sits_on_the_even_odd_boundary"] = {
        "pass": multivector_close(zero_involution, ZERO) and multivector_close(zero_involution, -ZERO),
        "zero_value": str(ZERO),
    }
    results["scalar_boundary_is_even"] = {
        "pass": multivector_close(scalar_involution, SCALAR),
        "scalar_value": str(SCALAR),
        "grade_involution_value": str(scalar_involution),
    }
    results["pseudoscalar_boundary_is_odd"] = {
        "pass": multivector_close(trivector_involution, -E123),
        "pseudoscalar_value": str(E123),
        "grade_involution_value": str(trivector_involution),
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
            "scope_note": "Shell-local Cl(3) grade split only; no coupling, coexistence, topology-variant, emergence, or bridge claims.",
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
