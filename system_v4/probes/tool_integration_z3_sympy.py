#!/usr/bin/env python3
"""
Tool-lego-integration probe for z3 + SymPy.

The integration claim is simple and load-bearing:
- SymPy builds exact polynomials and derivative data.
- z3 consumes those exact coefficients and derivative values to admit or exclude
  integer root patterns.
- The admitted z3 model is then pulled back into SymPy for exact factor checks.

This is not parallel tool usage. Each section feeds one tool's output into the other.
Hermes workers save and enqueue the probe but do not execute the sim.
"""

import json
import os

from receipt_boundary import apply_default_receipt_boundary

classification = "canonical"
NAME = "tool_integration_z3_sympy"

_NOT_USED_REASON = (
    "not used: this integration probe isolates SymPy polynomial data feeding "
    "z3 integer root constraints; other tools and promotion surfaces are out of scope."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "pyg": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "z3": {
        "tried": False,
        "used": False,
        "reason": "z3 is the load-bearing solver for SAT and UNSAT checks over integer root patterns induced by exact SymPy polynomial data.",
    },
    "cvc5": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "sympy": {
        "tried": False,
        "used": False,
        "reason": "SymPy is the load-bearing symbolic layer that constructs exact polynomials, derivatives, and factor forms whose outputs are fed into z3 constraints.",
    },
    "clifford": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "xgi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "toponetx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "gudhi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
}

TOOL_INTEGRATION_DEPTH = {
    "z3": "load_bearing",
    "sympy": "load_bearing",
}

try:
    import sympy as sp

    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    sp = None
    TOOL_MANIFEST["sympy"]["reason"] = "sympy import failed on this machine; queued execution will resolve availability."

try:
    from z3 import Int, SolverFor, sat, unsat

    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    Int = SolverFor = None
    sat = unsat = None
    TOOL_MANIFEST["z3"]["reason"] = "z3 import failed on this machine; queued execution will resolve availability."


def _integration_ready():
    return TOOL_MANIFEST["sympy"]["tried"] and TOOL_MANIFEST["z3"]["tried"]


def _solver():
    solver = SolverFor("QF_NIA")
    solver.set(timeout=2000)
    return solver


def _mark_used():
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["z3"]["used"] = True


def _serialize(value):
    if sp is not None and isinstance(value, sp.Basic):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _serialize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(v) for v in value]
    return value


def _case_passed(case):
    if case.get("status") == "skipped":
        return False
    if "roundtrip_exact" in case:
        return bool(case["roundtrip_exact"])
    if "gcd_matches_expected" in case:
        return bool(case["gcd_matches_expected"])
    if "root_matches_expected_boundary" in case:
        return bool(case["root_matches_expected_boundary"])
    if "expected" in case and "status" in case:
        expected = str(case["expected"])
        observed = str(case["status"])
        extra_ok = True
        if "squarefree_under_sympy" in case:
            extra_ok = extra_ok and bool(case["squarefree_under_sympy"])
        return observed == expected and extra_ok
    return False


def _summarize(*sections):
    cases = []
    for section in sections:
        cases.extend(section.values())
    passed = sum(1 for case in cases if isinstance(case, dict) and _case_passed(case))
    total = len(cases)
    return {"passed": passed, "total": total, "all_pass": passed == total}


def _coefficients_from_roots(root_list):
    x = sp.symbols("x", integer=True)
    poly = sp.expand(sp.prod(x - root for root in root_list))
    derivative = sp.expand(sp.diff(poly, x))
    coeffs = sp.Poly(poly, x).all_coeffs()
    deriv_coeffs = sp.Poly(derivative, x).all_coeffs()
    return {
        "symbol": x,
        "roots": list(root_list),
        "polynomial": poly,
        "derivative": derivative,
        "coefficients": [int(c) for c in coeffs],
        "derivative_coefficients": [int(c) for c in deriv_coeffs],
    }


def _eval_from_coeffs(coeffs, variable):
    degree = len(coeffs) - 1
    expr = 0
    for index, coeff in enumerate(coeffs):
        power = degree - index
        if power == 0:
            expr += coeff
        else:
            expr += coeff * (variable ** power)
    return expr


def _solve_ordered_integer_roots(coeff_data):
    r0 = Int("r0")
    r1 = Int("r1")
    r2 = Int("r2")
    solver = _solver()
    roots = [r0, r1, r2]
    coeffs = coeff_data["coefficients"]
    solver.add(r0 < r1, r1 < r2)
    solver.add(r0 + r1 + r2 == -coeffs[1])
    solver.add(r0 * r1 + r0 * r2 + r1 * r2 == coeffs[2])
    solver.add(r0 * r1 * r2 == -coeffs[3])
    status = solver.check()
    _mark_used()
    result = {
        "status": str(status),
        "coefficients_from_sympy": coeffs,
        "expected_roots": coeff_data["roots"],
    }
    if status == sat:
        model = solver.model()
        result["solver_roots"] = [model.eval(root).as_long() for root in roots]
    return result


def _repeated_root_solver(coeff_data):
    r = Int("r_repeated")
    solver = _solver()
    solver.add(_eval_from_coeffs(coeff_data["coefficients"], r) == 0)
    solver.add(_eval_from_coeffs(coeff_data["derivative_coefficients"], r) == 0)
    status = solver.check()
    _mark_used()
    result = {
        "status": str(status),
        "polynomial_from_sympy": str(coeff_data["polynomial"]),
        "derivative_from_sympy": str(coeff_data["derivative"]),
    }
    if status == sat:
        model = solver.model()
        result["repeated_root"] = model.eval(r).as_long()
    return result


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    if not _integration_ready():
        results["integration_import_gate"] = {
            "status": "skipped",
            "reason": "z3 and sympy must both import for this integration probe",
        }
        return results

    coeff_data = _coefficients_from_roots([-3, -1, 2])
    root_solve = _solve_ordered_integer_roots(coeff_data)
    if root_solve["status"] == "sat":
        x = coeff_data["symbol"]
        solver_poly = sp.expand(sp.prod(x - root for root in root_solve["solver_roots"]))
        residual = sp.expand(solver_poly - coeff_data["polynomial"])
        root_solve["sympy_roundtrip_polynomial"] = str(solver_poly)
        root_solve["roundtrip_residual"] = str(residual)
        root_solve["roundtrip_exact"] = residual == 0
        root_solve["sympy_factorization"] = str(sp.factor(solver_poly))
    results["sympy_coefficients_feed_z3_vieta_solver"] = root_solve

    repeated_data = _coefficients_from_roots([1, 1, -2])
    repeated_root = _repeated_root_solver(repeated_data)
    if repeated_root["status"] == "sat":
        x = repeated_data["symbol"]
        repeated_root["sympy_gcd"] = str(
            sp.gcd(
                sp.Poly(repeated_data["polynomial"], x),
                sp.Poly(repeated_data["derivative"], x),
            ).as_expr()
        )
        repeated_root["expected_shared_factor"] = str(x - 1)
        repeated_root["gcd_matches_expected"] = repeated_root["sympy_gcd"] == str(x - 1)
    results["sympy_derivative_feed_z3_repeated_root_witness"] = repeated_root

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    if not _integration_ready():
        results["integration_import_gate"] = {
            "status": "skipped",
            "reason": "z3 and sympy must both import for this integration probe",
        }
        return results

    coeff_data = _coefficients_from_roots([0, 1, 2])
    forced_root = Int("forced_root")
    solver = _solver()
    solver.add(_eval_from_coeffs(coeff_data["coefficients"], forced_root) == 0)
    solver.add(forced_root == 5)
    status = solver.check()
    _mark_used()
    results["sympy_polynomial_excludes_nonroot_in_z3"] = {
        "status": str(status),
        "expected": "unsat",
        "polynomial_from_sympy": str(coeff_data["polynomial"]),
        "coefficients_from_sympy": coeff_data["coefficients"],
        "forced_candidate": 5,
    }

    squarefree_data = _coefficients_from_roots([-2, 0, 3])
    no_repeat = _repeated_root_solver(squarefree_data)
    no_repeat["expected"] = "unsat"
    no_repeat["sympy_discriminant"] = str(sp.discriminant(squarefree_data["polynomial"], squarefree_data["symbol"]))
    no_repeat["squarefree_under_sympy"] = sp.discriminant(squarefree_data["polynomial"], squarefree_data["symbol"]) != 0
    results["squarefree_sympy_data_blocks_repeated_root_in_z3"] = no_repeat

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    if not _integration_ready():
        results["integration_import_gate"] = {
            "status": "skipped",
            "reason": "z3 and sympy must both import for this integration probe",
        }
        return results

    repeated_boundary = _coefficients_from_roots([2, 2])
    repeated_root = _repeated_root_solver(repeated_boundary)
    repeated_root["expected"] = "sat"
    results["double_root_boundary_survives"] = repeated_root

    linear_boundary = _coefficients_from_roots([0, 4, 7])
    root = Int("boundary_root")
    solver = _solver()
    solver.add(_eval_from_coeffs(linear_boundary["coefficients"], root) == 0)
    solver.add(root >= 0, root <= 0)
    status = solver.check()
    _mark_used()
    boundary_result = {
        "status": str(status),
        "expected": "sat",
        "polynomial_from_sympy": str(linear_boundary["polynomial"]),
        "coefficients_from_sympy": linear_boundary["coefficients"],
        "interval": [0, 0],
    }
    if status == sat:
        model = solver.model()
        root_value = model.eval(root).as_long()
        boundary_result["root"] = root_value
        boundary_result["sympy_factorization_at_boundary"] = str(sp.factor(linear_boundary["polynomial"]))
        boundary_result["root_matches_expected_boundary"] = root_value == 0
    results["singleton_interval_boundary_root"] = boundary_result

    return results


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    summary = _summarize(positive, negative, boundary)
    results = {
        "name": NAME,
        "probe_family": "z3_sympy_polynomial_root_integration",
        "constraint_set": "exact_polynomial_coefficients_to_integer_root_constraints",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "surviving_alternatives": [
            "This receipt covers only exact SymPy polynomial coefficient and derivative data feeding z3 integer root constraints; it does not prove broad symbolic-SMT equivalence."
        ],
        "demotion_condition": (
            "Demote this integration surface if SymPy polynomial coefficients no longer "
            "roundtrip through z3 root constraints, if nonroots or squarefree repeated-root "
            "claims are admitted, or if singleton interval boundary roots fail."
        ),
        "out_of_scope": [
            "no broad solver equivalence",
            "no nonlinear completeness claim",
            "no lego promotion",
            "no bridge claim",
            "no axis claim",
            "no GStack claim",
        ],
        "criteria_checked": [
            "SymPy polynomial coefficients feed z3 Vieta root solver",
            "SymPy derivative coefficients feed z3 repeated-root witness",
            "SymPy polynomial excludes a forced nonroot in z3",
            "squarefree SymPy data blocks repeated-root witness in z3",
            "double-root and singleton-interval boundary behavior survive",
        ],
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
    }
    results = apply_default_receipt_boundary(
        results,
        source_name=NAME,
        target=(
            "Use as bounded z3 plus SymPy polynomial-root tool-integration evidence "
            "before constraint-probe lego-fit or later solver-coupling packets."
        ),
    )

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(_serialize(results), handle, indent=2, sort_keys=True)
    print(f"Results written to {out_path}")
