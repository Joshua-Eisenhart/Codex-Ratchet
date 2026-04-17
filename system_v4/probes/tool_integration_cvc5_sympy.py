#!/usr/bin/env python3
"""
Tier A A4.6 tool-lego-integration probe for cvc5 + SymPy.

SymPy is load-bearing for exact polynomial expansion, derivative data, and
squarefree/discriminant checks. cvc5 is load-bearing for SAT and UNSAT results
over integer root patterns induced by those symbolic outputs. Each section feeds
SymPy output into cvc5 constraints and, when a model survives, pulls the cvc5
witness back through SymPy for exact roundtrip checks.

Hermes workers save and enqueue this probe but do not execute it directly.
"""

import json
import os
from typing import Any, Dict, List

classification = "canonical"
NAME = "tool_integration_cvc5_sympy"

TOOL_MANIFEST = {
    "cvc5": {
        "tried": False,
        "used": False,
        "reason": "cvc5 is the load-bearing SMT layer that admits or excludes integer root configurations using exact coefficient and derivative data supplied by SymPy.",
    },
    "sympy": {
        "tried": False,
        "used": False,
        "reason": "SymPy is the load-bearing symbolic layer that constructs exact polynomials, derivatives, discriminants, and gcd data whose outputs are fed directly into cvc5 constraints.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
}

try:
    import cvc5
    from cvc5 import Kind

    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    cvc5 = None
    Kind = None
    TOOL_MANIFEST["cvc5"]["reason"] = "cvc5 import failed on this machine; queue execution will decide whether SMT admission and exclusion over SymPy-derived coefficients is available."

try:
    import sympy as sp

    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    sp = None
    TOOL_MANIFEST["sympy"]["reason"] = "SymPy import failed on this machine; queue execution will decide whether exact polynomial and derivative data is available."


def _mark_used(*tools: str) -> None:
    for tool in tools:
        TOOL_MANIFEST[tool]["used"] = True


def _to_serializable(value: Any) -> Any:
    if value is None:
        return None
    if sp is not None and isinstance(value, sp.Basic):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _to_serializable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_serializable(v) for v in value]
    return value


def _gate_results(section: str) -> Dict[str, Any]:
    missing = []
    if not TOOL_MANIFEST["cvc5"]["tried"]:
        missing.append("cvc5")
    if not TOOL_MANIFEST["sympy"]["tried"]:
        missing.append("sympy")
    return {f"{section}_import_gate": {"status": "skipped", "missing": missing}}


def _solver() -> "cvc5.Solver":
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    solver.setOption("produce-models", "true")
    return solver


def _int(solver: "cvc5.Solver", name: str):
    return solver.mkConst(solver.getIntegerSort(), name)


def _integer(solver: "cvc5.Solver", value: int):
    return solver.mkInteger(int(value))


def _add(solver: "cvc5.Solver", *terms):
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.ADD, *terms)


def _mul(solver: "cvc5.Solver", *terms):
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.MULT, *terms)


def _sub(solver: "cvc5.Solver", left, right):
    return solver.mkTerm(Kind.SUB, left, right)


def _eq(solver: "cvc5.Solver", left, right):
    return solver.mkTerm(Kind.EQUAL, left, right)


def _lt(solver: "cvc5.Solver", left, right):
    return solver.mkTerm(Kind.LT, left, right)


def _geq(solver: "cvc5.Solver", left, right):
    return solver.mkTerm(Kind.GEQ, left, right)


def _leq(solver: "cvc5.Solver", left, right):
    return solver.mkTerm(Kind.LEQ, left, right)


def _pow_int(solver: "cvc5.Solver", base, exponent: int):
    if exponent == 0:
        return _integer(solver, 1)
    result = base
    for _ in range(1, exponent):
        result = _mul(solver, result, base)
    return result


def _coefficients_from_roots(root_list: List[int]) -> Dict[str, Any]:
    x = sp.symbols("x", integer=True)
    poly = sp.expand(sp.prod(x - root for root in root_list))
    derivative = sp.expand(sp.diff(poly, x))
    coeffs = [int(c) for c in sp.Poly(poly, x).all_coeffs()]
    deriv_coeffs = [int(c) for c in sp.Poly(derivative, x).all_coeffs()]
    discriminant = sp.simplify(sp.discriminant(poly, x))
    gcd_expr = sp.gcd(sp.Poly(poly, x), sp.Poly(derivative, x)).as_expr()
    return {
        "symbol": x,
        "roots": list(root_list),
        "polynomial": poly,
        "derivative": derivative,
        "coefficients": coeffs,
        "derivative_coefficients": deriv_coeffs,
        "discriminant": discriminant,
        "gcd": sp.expand(gcd_expr),
    }


def _eval_from_coeffs(solver: "cvc5.Solver", coeffs: List[int], variable):
    degree = len(coeffs) - 1
    terms = []
    for index, coeff in enumerate(coeffs):
        power = degree - index
        coeff_term = _integer(solver, coeff)
        if power == 0:
            term = coeff_term
        else:
            term = _mul(solver, coeff_term, _pow_int(solver, variable, power))
        terms.append(term)
    return _add(solver, *terms)


def _ordered_integer_roots_from_coeffs(coeff_data: Dict[str, Any]) -> Dict[str, Any]:
    solver = _solver()
    r0 = _int(solver, "r0")
    r1 = _int(solver, "r1")
    r2 = _int(solver, "r2")
    coeffs = coeff_data["coefficients"]

    solver.assertFormula(_lt(solver, r0, r1))
    solver.assertFormula(_lt(solver, r1, r2))
    solver.assertFormula(_eq(solver, _add(solver, r0, r1, r2), _integer(solver, -coeffs[1])))
    solver.assertFormula(
        _eq(
            solver,
            _add(solver, _mul(solver, r0, r1), _mul(solver, r0, r2), _mul(solver, r1, r2)),
            _integer(solver, coeffs[2]),
        )
    )
    solver.assertFormula(_eq(solver, _mul(solver, r0, r1, r2), _integer(solver, -coeffs[3])))

    status = solver.checkSat()
    _mark_used("sympy", "cvc5")
    result = {
        "status": str(status),
        "coefficients_from_sympy": coeffs,
        "expected_roots": coeff_data["roots"],
    }
    if status.isSat():
        result["solver_roots"] = [int(str(solver.getValue(root))) for root in [r0, r1, r2]]
    return result


def _repeated_root_from_sympy_data(coeff_data: Dict[str, Any]) -> Dict[str, Any]:
    solver = _solver()
    r = _int(solver, "r_repeat")
    solver.assertFormula(_eq(solver, _eval_from_coeffs(solver, coeff_data["coefficients"], r), _integer(solver, 0)))
    solver.assertFormula(_eq(solver, _eval_from_coeffs(solver, coeff_data["derivative_coefficients"], r), _integer(solver, 0)))
    status = solver.checkSat()
    _mark_used("sympy", "cvc5")
    result = {
        "status": str(status),
        "polynomial_from_sympy": str(coeff_data["polynomial"]),
        "derivative_from_sympy": str(coeff_data["derivative"]),
    }
    if status.isSat():
        result["repeated_root"] = int(str(solver.getValue(r)))
    return result


def run_positive_tests() -> Dict[str, Any]:
    if cvc5 is None or sp is None:
        return _gate_results("positive")

    results = {}

    coeff_data = _coefficients_from_roots([-3, -1, 2])
    ordered_roots = _ordered_integer_roots_from_coeffs(coeff_data)
    if ordered_roots["status"] == "sat":
        x = coeff_data["symbol"]
        roundtrip_poly = sp.expand(sp.prod(x - root for root in ordered_roots["solver_roots"]))
        residual = sp.expand(roundtrip_poly - coeff_data["polynomial"])
        ordered_roots["sympy_roundtrip_polynomial"] = str(roundtrip_poly)
        ordered_roots["sympy_factorization"] = str(sp.factor(roundtrip_poly))
        ordered_roots["roundtrip_residual"] = str(residual)
        ordered_roots["roundtrip_exact"] = residual == 0
    results["sympy_coefficients_feed_cvc5_vieta_solver"] = ordered_roots

    repeated_data = _coefficients_from_roots([1, 1, -2])
    repeated_root = _repeated_root_from_sympy_data(repeated_data)
    if repeated_root["status"] == "sat":
        x = repeated_data["symbol"]
        repeated_root["sympy_gcd"] = str(repeated_data["gcd"])
        repeated_root["expected_shared_factor"] = str(x - 1)
        repeated_root["gcd_matches_expected"] = sp.expand(repeated_data["gcd"] - (x - 1)) == 0
    results["sympy_derivative_feed_cvc5_repeated_root_witness"] = repeated_root

    return results


def run_negative_tests() -> Dict[str, Any]:
    if cvc5 is None or sp is None:
        return _gate_results("negative")

    results = {}

    coeff_data = _coefficients_from_roots([0, 1, 2])
    solver = _solver()
    forced_root = _int(solver, "forced_root")
    solver.assertFormula(_eq(solver, _eval_from_coeffs(solver, coeff_data["coefficients"], forced_root), _integer(solver, 0)))
    solver.assertFormula(_eq(solver, forced_root, _integer(solver, 5)))
    forced_status = solver.checkSat()
    _mark_used("sympy", "cvc5")
    results["sympy_polynomial_excludes_nonroot_in_cvc5"] = {
        "status": str(forced_status),
        "expected": "unsat",
        "polynomial_from_sympy": str(coeff_data["polynomial"]),
        "coefficients_from_sympy": coeff_data["coefficients"],
        "forced_candidate": 5,
    }

    squarefree_data = _coefficients_from_roots([-2, 0, 3])
    no_repeat = _repeated_root_from_sympy_data(squarefree_data)
    no_repeat["expected"] = "unsat"
    no_repeat["sympy_discriminant"] = str(squarefree_data["discriminant"])
    no_repeat["squarefree_under_sympy"] = squarefree_data["discriminant"] != 0
    results["squarefree_sympy_data_blocks_repeated_root_in_cvc5"] = no_repeat

    return results


def run_boundary_tests() -> Dict[str, Any]:
    if cvc5 is None or sp is None:
        return _gate_results("boundary")

    results = {}

    repeated_boundary = _coefficients_from_roots([2, 2])
    repeated_root = _repeated_root_from_sympy_data(repeated_boundary)
    repeated_root["expected"] = "sat"
    repeated_root["sympy_gcd"] = str(repeated_boundary["gcd"])
    results["double_root_boundary_survives"] = repeated_root

    interval_data = _coefficients_from_roots([0, 4, 7])
    solver = _solver()
    root = _int(solver, "boundary_root")
    solver.assertFormula(_eq(solver, _eval_from_coeffs(solver, interval_data["coefficients"], root), _integer(solver, 0)))
    solver.assertFormula(_geq(solver, root, _integer(solver, 0)))
    solver.assertFormula(_leq(solver, root, _integer(solver, 0)))
    interval_status = solver.checkSat()
    _mark_used("sympy", "cvc5")
    boundary_result = {
        "status": str(interval_status),
        "expected": "sat",
        "polynomial_from_sympy": str(interval_data["polynomial"]),
        "coefficients_from_sympy": interval_data["coefficients"],
        "interval": [0, 0],
    }
    if interval_status.isSat():
        root_value = int(str(solver.getValue(root)))
        boundary_result["root"] = root_value
        boundary_result["sympy_factorization_at_boundary"] = str(sp.factor(interval_data["polynomial"]))
        boundary_result["boundary_exact"] = root_value == 0
    results["singleton_interval_boundary_survives"] = boundary_result

    return results


if __name__ == "__main__":
    results = {
        "name": NAME,
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(_to_serializable(results), handle, indent=2, sort_keys=True)
    print(f"Results written to {out_path}")
