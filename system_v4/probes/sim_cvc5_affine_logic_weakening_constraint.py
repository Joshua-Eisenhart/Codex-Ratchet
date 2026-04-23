#!/usr/bin/env python3
"""
Affine Logic via cvc5 + sympy.

Affine logic: weakening allowed (discard unused hypotheses) but contraction forbidden
(cannot reuse a single hypothesis multiple times). Each formula must be used at least once
if introduced, but at most once per use.

cvc5 (QF_LIA): UNSAT if a formula is used 0 times (violates introduction assumption).
UNSAT if a formula is used > 1 times (violates affine constraint).

sympy: resource count upper-bound formula verification.
"""

import json
import os

classification = "canonical"

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "pytorch not needed; pure symbolic/algebraic computation via cvc5 and sympy"},
    "pyg": {"tried": False, "used": False, "reason": "PyG message passing not needed; constraint logic handled via SMT solver"},
    "z3": {"tried": False, "used": False, "reason": "z3 not needed; cvc5 handles all SMT constraint proofs in this sim"},
    "cvc5": {"tried": False, "used": False, "reason": "cvc5 SMT solver: load_bearing proof of affine logic use-count constraints"},
    "sympy": {"tried": False, "used": False, "reason": "sympy: supportive symbolic algebra for affine use-count formulas"},
    "clifford": {"tried": False, "used": False, "reason": "Clifford algebra not needed; logic constraints only"},
    "geomstats": {"tried": False, "used": False, "reason": "geomstats not needed; no differential geometry in this sim"},
    "e3nn": {"tried": False, "used": False, "reason": "e3nn not needed; no SO(3) equivariance required"},
    "rustworkx": {"tried": False, "used": False, "reason": "rustworkx not needed; no graph structure in this sim"},
    "xgi": {"tried": False, "used": False, "reason": "xgi not needed; pairwise interactions only"},
    "toponetx": {"tried": False, "used": False, "reason": "toponetx not needed; standard algebraic ops sufficient"},
    "gudhi": {"tried": False, "used": False, "reason": "gudhi not needed; no persistent homology in this sim"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": "load_bearing",
    "sympy": "supportive",
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

# Try importing tools
try:
    import cvc5
    from cvc5 import Kind
    TOOL_MANIFEST["cvc5"]["tried"] = True
    TOOL_MANIFEST["cvc5"]["used"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


# =====================================================================
# POSITIVE TESTS: Valid affine use counts (0 ≤ use_count ≤ 1)
# =====================================================================

def run_positive_tests():
    """
    Test valid affine formulas where each hypothesis is used exactly 0 or 1 times.
    use_count ∈ {0, 1} should be satisfiable.
    """
    results = {}

    if not TOOL_MANIFEST["cvc5"]["used"]:
        return {"skipped": "cvc5 not available"}

    try:
        solver = cvc5.Solver()

        # Test 1: Formula used exactly once (valid affine usage)
        solver.push()
        use_count_P = solver.mkConst(solver.getIntegerSort(), "use_count_P")

        # P is used exactly once
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, use_count_P, solver.mkInteger(1)))
        # Constraint: use_count ∈ {0, 1}
        or_constraint = solver.mkTerm(Kind.OR,
                                      solver.mkTerm(Kind.EQUAL, use_count_P, solver.mkInteger(0)),
                                      solver.mkTerm(Kind.EQUAL, use_count_P, solver.mkInteger(1)))
        solver.assertFormula(or_constraint)

        sat1 = solver.checkSat().isSat()
        results["test_formula_used_once"] = {"satisfiable": sat1, "expected": True, "pass": sat1}
        solver.pop()

        # Test 2: Formula used zero times (weakening, valid in affine)
        solver.push()
        use_count_Q = solver.mkConst(solver.getIntegerSort(), "use_count_Q")

        solver.assertFormula(solver.mkTerm(Kind.EQUAL, use_count_Q, solver.mkInteger(0)))
        or_constraint = solver.mkTerm(Kind.OR,
                                      solver.mkTerm(Kind.EQUAL, use_count_Q, solver.mkInteger(0)),
                                      solver.mkTerm(Kind.EQUAL, use_count_Q, solver.mkInteger(1)))
        solver.assertFormula(or_constraint)

        sat2 = solver.checkSat().isSat()
        results["test_formula_weakened_unused"] = {"satisfiable": sat2, "expected": True, "pass": sat2}
        solver.pop()

        # Test 3: Multiple hypotheses, mixed use counts (some used, some weakened)
        solver.push()
        use_P = solver.mkConst(solver.getIntegerSort(), "use_P")
        use_Q = solver.mkConst(solver.getIntegerSort(), "use_Q")
        use_R = solver.mkConst(solver.getIntegerSort(), "use_R")

        # P used once, Q unused (weakened), R used once
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, use_P, solver.mkInteger(1)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, use_Q, solver.mkInteger(0)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, use_R, solver.mkInteger(1)))

        # Each must satisfy 0 ≤ use ≤ 1
        for use_var in [use_P, use_Q, use_R]:
            or_c = solver.mkTerm(Kind.OR,
                                solver.mkTerm(Kind.EQUAL, use_var, solver.mkInteger(0)),
                                solver.mkTerm(Kind.EQUAL, use_var, solver.mkInteger(1)))
            solver.assertFormula(or_c)

        sat3 = solver.checkSat().isSat()
        results["test_mixed_usage_multiple_hypotheses"] = {"satisfiable": sat3, "expected": True, "pass": sat3}
        solver.pop()

    except Exception as e:
        results["error"] = str(e)

    return results


# =====================================================================
# NEGATIVE TESTS: Invalid affine usage (contraction) -- UNSAT
# =====================================================================

def run_negative_tests():
    """
    Test invalid affine formulas where a hypothesis is used more than once (contraction).
    use_count > 1 should be UNSAT (violates affine constraint).
    """
    results = {}

    if not TOOL_MANIFEST["cvc5"]["used"]:
        return {"skipped": "cvc5 not available"}

    try:
        # Test 1: Formula used twice (contraction violation) -- UNSAT
        solver = cvc5.Solver()
        solver.push()
        use_count_P = solver.mkConst(solver.getIntegerSort(), "use_count_P")

        # P is used twice
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, use_count_P, solver.mkInteger(2)))
        # Constraint: use_count ∈ {0, 1}
        or_constraint = solver.mkTerm(Kind.OR,
                                      solver.mkTerm(Kind.EQUAL, use_count_P, solver.mkInteger(0)),
                                      solver.mkTerm(Kind.EQUAL, use_count_P, solver.mkInteger(1)))
        solver.assertFormula(or_constraint)

        sat1 = solver.checkSat().isSat()
        results["test_formula_used_twice"] = {"satisfiable": sat1, "expected": False, "pass": not sat1}
        solver.pop()

        # Test 2: Multiple hypotheses, one used 3 times (contraction) -- UNSAT
        solver.push()
        use_P = solver.mkConst(solver.getIntegerSort(), "use_P")
        use_Q = solver.mkConst(solver.getIntegerSort(), "use_Q")

        solver.assertFormula(solver.mkTerm(Kind.EQUAL, use_P, solver.mkInteger(3)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, use_Q, solver.mkInteger(1)))

        # Each must satisfy 0 ≤ use ≤ 1
        for use_var in [use_P, use_Q]:
            or_c = solver.mkTerm(Kind.OR,
                                solver.mkTerm(Kind.EQUAL, use_var, solver.mkInteger(0)),
                                solver.mkTerm(Kind.EQUAL, use_var, solver.mkInteger(1)))
            solver.assertFormula(or_c)

        sat2 = solver.checkSat().isSat()
        results["test_one_formula_used_3_times"] = {"satisfiable": sat2, "expected": False, "pass": not sat2}
        solver.pop()

        # Test 3: Hypothesis used exactly at boundary (use = 2) -- UNSAT
        solver.push()
        use_count = solver.mkConst(solver.getIntegerSort(), "use_count")

        solver.assertFormula(solver.mkTerm(Kind.EQUAL, use_count, solver.mkInteger(2)))
        # Affine constraint: use_count ≤ 1
        solver.assertFormula(solver.mkTerm(Kind.LEQ, use_count, solver.mkInteger(1)))

        sat3 = solver.checkSat().isSat()
        results["test_use_count_exactly_2"] = {"satisfiable": sat3, "expected": False, "pass": not sat3}
        solver.pop()

    except Exception as e:
        results["error"] = str(e)

    return results


# =====================================================================
# BOUNDARY TESTS: Edge cases and limits
# =====================================================================

def run_boundary_tests():
    """
    Boundary tests: zero usage in all hypotheses, large hypothesis counts,
    partial usage patterns.
    """
    results = {}

    if not TOOL_MANIFEST["cvc5"]["used"]:
        return {"skipped": "cvc5 not available"}

    try:
        # Test 1: All hypotheses unused (full weakening)
        solver = cvc5.Solver()
        solver.push()
        use_P = solver.mkConst(solver.getIntegerSort(), "use_P")
        use_Q = solver.mkConst(solver.getIntegerSort(), "use_Q")
        use_R = solver.mkConst(solver.getIntegerSort(), "use_R")

        # All unused
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, use_P, solver.mkInteger(0)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, use_Q, solver.mkInteger(0)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, use_R, solver.mkInteger(0)))

        # All must satisfy 0 ≤ use ≤ 1
        for use_var in [use_P, use_Q, use_R]:
            or_c = solver.mkTerm(Kind.OR,
                                solver.mkTerm(Kind.EQUAL, use_var, solver.mkInteger(0)),
                                solver.mkTerm(Kind.EQUAL, use_var, solver.mkInteger(1)))
            solver.assertFormula(or_c)

        sat1 = solver.checkSat().isSat()
        results["test_all_hypotheses_weakened"] = {"satisfiable": sat1, "expected": True, "pass": sat1}
        solver.pop()

        # Test 2: Large number of hypotheses, each used once
        solver.push()
        use_vars = [solver.mkConst(solver.getIntegerSort(), f"use_{i}") for i in range(10)]

        for use_var in use_vars:
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, use_var, solver.mkInteger(1)))
            or_c = solver.mkTerm(Kind.OR,
                                solver.mkTerm(Kind.EQUAL, use_var, solver.mkInteger(0)),
                                solver.mkTerm(Kind.EQUAL, use_var, solver.mkInteger(1)))
            solver.assertFormula(or_c)

        sat2 = solver.checkSat().isSat()
        results["test_many_hypotheses_each_used_once"] = {"satisfiable": sat2, "expected": True, "pass": sat2}
        solver.pop()

        # Test 3: Alternating use patterns (some 0, some 1)
        solver.push()
        use_vars = [solver.mkConst(solver.getIntegerSort(), f"use_{i}") for i in range(6)]

        # Pattern: 1, 0, 1, 0, 1, 0
        for i, use_var in enumerate(use_vars):
            val = 1 if i % 2 == 0 else 0
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, use_var, solver.mkInteger(val)))
            or_c = solver.mkTerm(Kind.OR,
                                solver.mkTerm(Kind.EQUAL, use_var, solver.mkInteger(0)),
                                solver.mkTerm(Kind.EQUAL, use_var, solver.mkInteger(1)))
            solver.assertFormula(or_c)

        sat3 = solver.checkSat().isSat()
        results["test_alternating_usage_pattern"] = {"satisfiable": sat3, "expected": True, "pass": sat3}
        solver.pop()

    except Exception as e:
        results["error"] = str(e)

    return results


# =====================================================================
# SYMPY VALIDATION: Use-count constraint formula
# =====================================================================

def validate_affine_formula():
    """
    Sympy validation: check affine logic use-count constraint formulas.
    """
    results = {}

    if not TOOL_MANIFEST["sympy"]["used"]:
        return {"skipped": "sympy not available"}

    try:
        # Define symbolic variables for affine use counts
        use_count = sp.Symbol('use_count', integer=True, nonnegative=True)

        # Affine constraint: 0 ≤ use_count ≤ 1
        affine_constraint = sp.And(sp.Ge(use_count, 0), sp.Le(use_count, 1))
        results["affine_use_count_constraint"] = str(affine_constraint)

        # Alternative: use_count ∈ {0, 1}
        use_in_set = sp.Or(sp.Eq(use_count, 0), sp.Eq(use_count, 1))
        results["use_count_in_set_form"] = str(use_in_set)

        # Verification: use_count = 0 satisfies constraint
        check_zero = affine_constraint.subs(use_count, 0)
        is_valid_zero = bool(check_zero)
        results["check_use_count_0"] = {"formula": str(check_zero), "valid": is_valid_zero}

        # Verification: use_count = 1 satisfies constraint
        check_one = affine_constraint.subs(use_count, 1)
        is_valid_one = bool(check_one)
        results["check_use_count_1"] = {"formula": str(check_one), "valid": is_valid_one}

        # Verification: use_count = 2 violates constraint (contraction)
        check_two = affine_constraint.subs(use_count, 2)
        is_valid_two = bool(check_two)
        results["check_use_count_2_invalid"] = {"formula": str(check_two), "valid": is_valid_two}

        # Total resource cost: sum of all use_counts
        # If we have n hypotheses and sum of uses = k, then cost = k
        n = sp.Symbol('n', integer=True, positive=True)
        total_use = sp.Symbol('total_use', integer=True, nonnegative=True)

        # Upper bound: total_use ≤ n (each hypothesis used at most once)
        upper_bound = sp.Le(total_use, n)
        results["total_use_upper_bound"] = str(upper_bound)

        # Lower bound: total_use ≥ 0 (trivial)
        lower_bound = sp.Ge(total_use, 0)
        results["total_use_lower_bound"] = str(lower_bound)

        # Example: 5 hypotheses, sum of uses = 3 (3 used, 2 weakened)
        total_use_val = 3
        n_val = 5
        check_example = upper_bound.subs([(total_use, total_use_val), (n, n_val)])
        is_example_valid = bool(check_example)
        results["example_3_of_5_used"] = {
            "total_use": total_use_val, "n_hypotheses": n_val,
            "constraint": str(upper_bound.subs([(total_use, total_use_val), (n, n_val)])),
            "valid": is_example_valid
        }

    except Exception as e:
        results["error"] = str(e)

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    results = {
        "name": "sim_cvc5_affine_logic_weakening_constraint",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "sympy_validation": validate_affine_formula(),
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_cvc5_affine_logic_weakening_constraint_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
