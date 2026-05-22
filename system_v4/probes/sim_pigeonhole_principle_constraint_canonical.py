#!/usr/bin/env python3
"""
Pigeonhole Principle Constraint Canonical Sim
"""

import json
import os
import cvc5

classification = "canonical"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not used; cvc5 preferred"},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": "not applicable"},
    "geomstats": {"tried": False, "used": False, "reason": "not applicable"},
    "e3nn": {"tried": False, "used": False, "reason": "not applicable"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    TOOL_MANIFEST["cvc5"]["tried"] = True
    TOOL_MANIFEST["cvc5"]["used"] = True
    TOOL_MANIFEST["cvc5"]["reason"] = "QF_LIA for pigeonhole distribution"
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "ceil(n/m) bound derivation"
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


def sum_terms(solver, terms):
    """Helper: sum a list of terms via nested ADD."""
    if len(terms) == 1:
        return terms[0]
    result = terms[0]
    for term in terms[1:]:
        result = solver.mkTerm(cvc5.Kind.ADD, result, term)
    return result


def run_positive_tests():
    results = {}
    if not TOOL_MANIFEST["cvc5"]["tried"]:
        return results

    # Test 1: 11 items in 10 boxes is satisfiable
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    box_counts = [solver.mkConst(int_sort, f"box_{i}") for i in range(10)]
    total = sum_terms(solver, box_counts)
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, total, solver.mkInteger(11)))
    for count in box_counts:
        solver.assertFormula(solver.mkTerm(cvc5.Kind.GEQ, count, solver.mkInteger(0)))
    result = solver.checkSat()
    results["test_11_in_10_sat"] = {
        "constraint": "11 items in 10 boxes",
        "result": str(result),
        "passed": result.isSat()
    }

    # Test 2: 100 items in 10 boxes with average >= 10
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    box_counts = [solver.mkConst(int_sort, f"box_{i}") for i in range(10)]
    total = sum_terms(solver, box_counts)
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, total, solver.mkInteger(100)))
    for count in box_counts:
        solver.assertFormula(solver.mkTerm(cvc5.Kind.GEQ, count, solver.mkInteger(0)))
    at_least_one = solver.mkTerm(cvc5.Kind.OR, *[
        solver.mkTerm(cvc5.Kind.GEQ, count, solver.mkInteger(10))
        for count in box_counts
    ])
    solver.assertFormula(at_least_one)
    result = solver.checkSat()
    results["test_100_in_10_sat"] = {
        "constraint": "100 items in 10 boxes with avg check",
        "result": str(result),
        "passed": result.isSat()
    }

    # Test 3: 5 items in 4 boxes
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    box_counts = [solver.mkConst(int_sort, f"box_{i}") for i in range(4)]
    total = sum_terms(solver, box_counts)
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, total, solver.mkInteger(5)))
    for count in box_counts:
        solver.assertFormula(solver.mkTerm(cvc5.Kind.GEQ, count, solver.mkInteger(0)))
    result = solver.checkSat()
    results["test_5_in_4_sat"] = {
        "constraint": "5 items in 4 boxes",
        "result": str(result),
        "passed": result.isSat()
    }

    return results


def run_negative_tests():
    results = {}
    if not TOOL_MANIFEST["cvc5"]["tried"]:
        return results

    # Test 1: 11 items in 10 boxes, all <= 1 is UNSAT
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    box_counts = [solver.mkConst(int_sort, f"box_{i}") for i in range(10)]
    total = sum_terms(solver, box_counts)
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, total, solver.mkInteger(11)))
    for count in box_counts:
        solver.assertFormula(solver.mkTerm(cvc5.Kind.LEQ, count, solver.mkInteger(1)))
    result = solver.checkSat()
    results["test_11_in_10_all_leq_1_unsat"] = {
        "constraint": "11 items, 10 boxes, all <= 1",
        "result": str(result),
        "passed": result.isUnsat()
    }

    # Test 2: 25 items in 5 boxes, all <= 4 is UNSAT
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    box_counts = [solver.mkConst(int_sort, f"box_{i}") for i in range(5)]
    total = sum_terms(solver, box_counts)
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, total, solver.mkInteger(25)))
    for count in box_counts:
        solver.assertFormula(solver.mkTerm(cvc5.Kind.LEQ, count, solver.mkInteger(4)))
    result = solver.checkSat()
    results["test_25_in_5_all_leq_4_unsat"] = {
        "constraint": "25 items, 5 boxes, all <= 4",
        "result": str(result),
        "passed": result.isUnsat()
    }

    # Test 3: 13 items in 4 boxes, all = 3 is UNSAT
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    box_counts = [solver.mkConst(int_sort, f"box_{i}") for i in range(4)]
    total = sum_terms(solver, box_counts)
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, total, solver.mkInteger(13)))
    for count in box_counts:
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, count, solver.mkInteger(3)))
    result = solver.checkSat()
    results["test_13_in_4_all_eq_3_unsat"] = {
        "constraint": "13 items, 4 boxes, all = 3",
        "result": str(result),
        "passed": result.isUnsat()
    }

    return results


def run_boundary_tests():
    results = {}
    if not TOOL_MANIFEST["sympy"]["tried"]:
        return results

    import sympy as sp

    n = sp.Symbol('n', integer=True, positive=True)
    m = sp.Symbol('m', integer=True, positive=True)
    ceil_formula = sp.ceiling(n / m)

    result_11_10 = ceil_formula.subs([(n, 11), (m, 10)])
    results["test_ceil_11_10"] = {
        "description": "ceil(11/10)",
        "value": int(result_11_10),
        "passed": result_11_10 == 2
    }

    result_100_10 = ceil_formula.subs([(n, 100), (m, 10)])
    results["test_ceil_100_10"] = {
        "description": "ceil(100/10)",
        "value": int(result_100_10),
        "passed": result_100_10 == 10
    }

    result_5_4 = ceil_formula.subs([(n, 5), (m, 4)])
    results["test_ceil_5_4"] = {
        "description": "ceil(5/4)",
        "value": int(result_5_4),
        "passed": result_5_4 == 2
    }

    return results


if __name__ == "__main__":
    results = {
        "name": "sim_pigeonhole_principle_constraint_canonical",
        "description": "Pigeonhole principle: n+1 items in n boxes; cvc5 QF_LIA proves necessity",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }

    if TOOL_MANIFEST["cvc5"]["used"]:
        TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
    if TOOL_MANIFEST["sympy"]["used"]:
        TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"

    results["tool_integration_depth"] = TOOL_INTEGRATION_DEPTH

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_pigeonhole_principle_constraint_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
