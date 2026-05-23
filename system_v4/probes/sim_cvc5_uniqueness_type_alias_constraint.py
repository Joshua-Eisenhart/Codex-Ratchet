#!/usr/bin/env python3
"""
Uniqueness Types (Clean language) — cvc5 canonical sim.

Theory:
  - A unique value u:*T has exactly one reference (alias_count(u) = 1 always).
  - Sharing requires explicit copying, which loses uniqueness.
  - Passing u to a function removes it from the caller's scope.
  - UNSAT for alias_count(u) >= 2 (cannot have multiple aliases).

Encoding:
  - Each unique-typed variable has an alias_count constraint.
  - SAT iff alias_count = 1 for all unique values in scope.
  - Scope removal: after passing to function, u is no longer in caller scope.
"""

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
classification = 'classical_baseline'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import json
import os

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "PyTorch not needed; uniqueness types are symbolic"},
    "pyg": {"tried": False, "used": False, "reason": "PyG not needed; pure constraint verification"},
    "z3": {"tried": False, "used": False, "reason": "z3 not needed; cvc5 handles all constraint solving"},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": "Clifford algebra not needed; uniqueness is algebraic"},
    "geomstats": {"tried": False, "used": False, "reason": "geomstats not needed; no differential geometry"},
    "e3nn": {"tried": False, "used": False, "reason": "e3nn not needed; no SO(3) equivariance"},
    "rustworkx": {"tried": False, "used": False, "reason": "rustworkx not needed; scope is linear, not graph-based"},
    "xgi": {"tried": False, "used": False, "reason": "xgi not needed; no hypergraph structure"},
    "toponetx": {"tried": False, "used": False, "reason": "toponetx not needed; standard constraint verification sufficient"},
    "gudhi": {"tried": False, "used": False, "reason": "gudhi not needed; no persistent homology required"},
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

cvc5_available = False
sympy_available = False

try:
    import cvc5
    TOOL_MANIFEST["cvc5"]["tried"] = True
    cvc5_available = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    sympy_available = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    """Valid uniqueness type patterns (alias_count = 1)."""
    results = {}

    if not cvc5_available:
        results["test_1_single_unique_reference"] = {"status": "skipped", "reason": "cvc5 not available"}
        results["test_2_function_call_removes_from_scope"] = {"status": "skipped", "reason": "cvc5 not available"}
        results["test_3_multiple_unique_values"] = {"status": "skipped", "reason": "cvc5 not available"}
        if sympy_available:
            results["test_sympy_uniqueness_algebra"] = run_sympy_uniqueness_test()
        return results

    # Test 1: Single unique reference (alias_count = 1)
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        alias_count_u = solver.mkConst(solver.getIntegerSort(), "alias_count_u")
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, alias_count_u, solver.mkInteger(1)))

        sat = solver.checkSat()
        results["test_1_single_unique_reference"] = {
            "status": "pass" if sat.isSat() else "fail",
            "formula": "alias_count(u) = 1",
            "expected": "SAT",
            "actual": "SAT" if sat.isSat() else "UNSAT",
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_MANIFEST["cvc5"]["reason"] = "Constraint solving for uniqueness type verification"
    except Exception as e:
        results["test_1_single_unique_reference"] = {"status": "error", "message": str(e)}

    # Test 2: Function call removes u from caller scope, but alias_count = 1 in function
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        # Caller scope: u exists initially
        in_caller_scope_before = solver.mkConst(solver.getBooleanSort(), "in_caller_scope_before")
        in_caller_scope_after = solver.mkConst(solver.getBooleanSort(), "in_caller_scope_after")

        # Function scope: u exists (was passed in)
        in_func_scope = solver.mkConst(solver.getBooleanSort(), "in_func_scope")
        alias_count_func = solver.mkConst(solver.getIntegerSort(), "alias_count_func")

        # Constraints:
        # Initially u is in caller scope
        solver.assertFormula(in_caller_scope_before)

        # After function call: u is in function scope, not in caller
        solver.assertFormula(in_func_scope)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.NOT, in_caller_scope_after))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, alias_count_func, solver.mkInteger(1)))

        sat = solver.checkSat()
        results["test_2_function_call_removes_from_scope"] = {
            "status": "pass" if sat.isSat() else "fail",
            "formula": "u in caller before, u in func after (not in caller), alias=1 in func",
            "expected": "SAT",
            "actual": "SAT" if sat.isSat() else "UNSAT",
        }
    except Exception as e:
        results["test_2_function_call_removes_from_scope"] = {"status": "error", "message": str(e)}

    # Test 3: Multiple unique values in scope, each with alias_count = 1
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        alias_u = solver.mkConst(solver.getIntegerSort(), "alias_u")
        alias_v = solver.mkConst(solver.getIntegerSort(), "alias_v")
        alias_w = solver.mkConst(solver.getIntegerSort(), "alias_w")

        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, alias_u, solver.mkInteger(1)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, alias_v, solver.mkInteger(1)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, alias_w, solver.mkInteger(1)))

        sat = solver.checkSat()
        results["test_3_multiple_unique_values"] = {
            "status": "pass" if sat.isSat() else "fail",
            "formula": "u, v, w all have alias_count=1",
            "expected": "SAT",
            "actual": "SAT" if sat.isSat() else "UNSAT",
        }
    except Exception as e:
        results["test_3_multiple_unique_values"] = {"status": "error", "message": str(e)}

    return results


# =====================================================================
# NEGATIVE TESTS (UNSAT proofs)
# =====================================================================

def run_negative_tests():
    """Invalid patterns that violate uniqueness constraints (UNSAT)."""
    results = {}

    if not cvc5_available:
        results["test_1_multiple_aliases"] = {"status": "skipped", "reason": "cvc5 not available"}
        results["test_2_sharing_without_copy"] = {"status": "skipped", "reason": "cvc5 not available"}
        results["test_3_use_after_function_pass"] = {"status": "skipped", "reason": "cvc5 not available"}
        return results

    # Test 1: Unique value with multiple aliases — UNSAT
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        alias_count = solver.mkConst(solver.getIntegerSort(), "alias_count")

        # Constraint: must have exactly one alias (unique type)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, alias_count, solver.mkInteger(1)))
        # But also: alias_count >= 2 (multiple aliases)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.GEQ, alias_count, solver.mkInteger(2)))

        sat = solver.checkSat()
        results["test_1_multiple_aliases"] = {
            "status": "pass" if not sat.isSat() else "fail",
            "formula": "alias_count=1 AND alias_count>=2",
            "expected": "UNSAT",
            "actual": "UNSAT" if not sat.isSat() else "SAT",
        }
    except Exception as e:
        results["test_1_multiple_aliases"] = {"status": "error", "message": str(e)}

    # Test 2: Sharing u without explicit copy (loses uniqueness) — UNSAT
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        alias_original = solver.mkConst(solver.getIntegerSort(), "alias_original")
        alias_shared = solver.mkConst(solver.getIntegerSort(), "alias_shared")

        # Original u is unique (alias=1)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, alias_original, solver.mkInteger(1)))
        # After sharing (without copy), it's still supposed to be unique
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, alias_shared, solver.mkInteger(1)))
        # But sharing creates multiple aliases (contradiction)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.GEQ, alias_shared, solver.mkInteger(2)))

        sat = solver.checkSat()
        results["test_2_sharing_without_copy"] = {
            "status": "pass" if not sat.isSat() else "fail",
            "formula": "unique(u) then share(u) without copy -> alias=1 AND alias>=2",
            "expected": "UNSAT",
            "actual": "UNSAT" if not sat.isSat() else "SAT",
        }
    except Exception as e:
        results["test_2_sharing_without_copy"] = {"status": "error", "message": str(e)}

    # Test 3: Using u in caller scope after passing to function — UNSAT
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        in_caller = solver.mkConst(solver.getBooleanSort(), "in_caller")
        in_func = solver.mkConst(solver.getBooleanSort(), "in_func")

        # After passing u to function, it's in function scope
        solver.assertFormula(in_func)
        # Constraint: unique value cannot be in both scopes
        # If in_func is true, in_caller must be false
        solver.assertFormula(
            solver.mkTerm(cvc5.Kind.NOT, in_caller)
        )
        # But also: u is in caller (violation)
        solver.assertFormula(in_caller)

        sat = solver.checkSat()
        results["test_3_use_after_function_pass"] = {
            "status": "pass" if not sat.isSat() else "fail",
            "formula": "u in func scope AND NOT in_caller AND in_caller (contradiction)",
            "expected": "UNSAT",
            "actual": "UNSAT" if not sat.isSat() else "SAT",
        }
    except Exception as e:
        results["test_3_use_after_function_pass"] = {"status": "error", "message": str(e)}

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """Edge cases and constraints at boundaries."""
    results = {}

    if not cvc5_available:
        results["test_1_alias_count_zero"] = {"status": "skipped", "reason": "cvc5 not available"}
        results["test_2_copy_preserves_uniqueness"] = {"status": "skipped", "reason": "cvc5 not available"}
        results["test_3_nested_function_calls"] = {"status": "skipped", "reason": "cvc5 not available"}
        return results

    # Test 1: Unique type with alias_count = 0 is invalid (garbage value)
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        alias_count = solver.mkConst(solver.getIntegerSort(), "alias_count")

        # Constraint: unique type must have alias_count = 1
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, alias_count, solver.mkInteger(1)))
        # Query: can alias_count be 0?
        solver.push()
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, alias_count, solver.mkInteger(0)))
        sat = solver.checkSat()
        solver.pop()

        results["test_1_alias_count_zero"] = {
            "status": "pass" if not sat.isSat() else "fail",
            "formula": "unique: alias_count=1; query: can it be 0?",
            "expected": "UNSAT (no, zero = dangling pointer)",
            "actual": "UNSAT" if not sat.isSat() else "SAT",
        }
    except Exception as e:
        results["test_1_alias_count_zero"] = {"status": "error", "message": str(e)}

    # Test 2: Explicit copy creates a non-unique value, original keeps alias_count=1
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        alias_original = solver.mkConst(solver.getIntegerSort(), "alias_original")
        alias_copied = solver.mkConst(solver.getIntegerSort(), "alias_copied")

        # Original is unique
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, alias_original, solver.mkInteger(1)))
        # Copy is NOT unique (alias_count=2: original + copy)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, alias_copied, solver.mkInteger(2)))
        # After copy: original still has alias_count=1, copy has alias_count=2
        sum_aliases = solver.mkTerm(cvc5.Kind.ADD, alias_original, alias_copied)
        # But both reference the same data, so total is 2
        solver.assertFormula(
            solver.mkTerm(cvc5.Kind.EQUAL, sum_aliases, solver.mkInteger(3))
        )

        sat = solver.checkSat()
        results["test_2_copy_preserves_uniqueness"] = {
            "status": "pass" if sat.isSat() else "fail",
            "formula": "copy(u) -> original alias=1, copied alias=2, total=3",
            "expected": "SAT",
            "actual": "SAT" if sat.isSat() else "UNSAT",
        }
    except Exception as e:
        results["test_2_copy_preserves_uniqueness"] = {"status": "error", "message": str(e)}

    # Test 3: Nested function calls maintain uniqueness invariant
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        alias_f = solver.mkConst(solver.getIntegerSort(), "alias_in_f")
        alias_g = solver.mkConst(solver.getIntegerSort(), "alias_in_g")

        # f calls g, passing unique u
        # In f: u is unique
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, alias_f, solver.mkInteger(1)))
        # In g: u is still unique (passed as unique parameter)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, alias_g, solver.mkInteger(1)))

        sat = solver.checkSat()
        results["test_3_nested_function_calls"] = {
            "status": "pass" if sat.isSat() else "fail",
            "formula": "f -> g(u), u unique in f and g, alias_count=1 both",
            "expected": "SAT",
            "actual": "SAT" if sat.isSat() else "UNSAT",
        }
    except Exception as e:
        results["test_3_nested_function_calls"] = {"status": "error", "message": str(e)}

    return results


def run_sympy_uniqueness_test():
    """Verify uniqueness algebra symbolically with sympy."""
    try:
        import sympy as sp

        alias_count = sp.Symbol("alias_count", integer=True, positive=True)

        # Unique type constraint: alias_count = 1
        expr = sp.Eq(alias_count, 1)

        # Check if alias_count can be anything other than 1
        non_one = sp.Eq(alias_count, 2)
        is_contradictory = sp.satisfiable(sp.And(expr, non_one))

        return {
            "status": "pass" if not is_contradictory else "fail",
            "formula": "alias_count = 1 contradicts alias_count = 2",
            "is_contradictory": not is_contradictory,
            "expected_contradictory": True,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    results = {
        "name": "UniquenessTypeAliasConstraint",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "classical_baseline",
        "original_classification": "canonical",
        "downgrade_reason": "overclassification_fail_status_2026-05-01",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_cvc5_uniqueness_type_alias_constraint_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
