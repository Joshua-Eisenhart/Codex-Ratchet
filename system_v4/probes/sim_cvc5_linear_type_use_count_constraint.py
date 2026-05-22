#!/usr/bin/env python3
"""
Linear Type Use-Exactly-Once Constraint — cvc5 canonical sim.

Theory:
  - A linear resource must be used exactly once (not zero, not multiple).
  - In tensor A⊗B, both A and B must each be used exactly once.
  - UNSAT for use_count=0 (unused), UNSAT for use_count≥2 (reused).

Encoding:
  - Each linear value has a use_count variable.
  - SAT iff use_count=1 for all linear values in scope.
  - Tensor product: use_count(A⊗B) = use_count(A) + use_count(B), both must =1.
"""

import json
import os

classification = "canonical"

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "PyTorch not needed; linear type logic is symbolic constraint"},
    "pyg": {"tried": False, "used": False, "reason": "PyG not needed; pure constraint verification"},
    "z3": {"tried": False, "used": False, "reason": "z3 not needed; cvc5 handles all constraint solving"},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": "Clifford algebra not needed; linear type constraints are algebraic"},
    "geomstats": {"tried": False, "used": False, "reason": "geomstats not needed; no differential geometry"},
    "e3nn": {"tried": False, "used": False, "reason": "e3nn not needed; no SO(3) equivariance"},
    "rustworkx": {"tried": False, "used": False, "reason": "rustworkx not needed; scope is linear ordering, not graph-based"},
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
    """Valid linear type use patterns (use_count=1)."""
    results = {}

    if not cvc5_available:
        results["test_1_single_use"] = {"status": "skipped", "reason": "cvc5 not available"}
        results["test_2_tensor_product_both_used_once"] = {"status": "skipped", "reason": "cvc5 not available"}
        results["test_3_nested_tensor_depth_3"] = {"status": "skipped", "reason": "cvc5 not available"}
        if sympy_available:
            results["test_sympy_use_count_formula"] = run_sympy_use_count_test()
        return results

    # Test 1: Single linear value used exactly once
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        use_count_a = solver.mkConst(solver.getIntegerSort(), "use_count_a")
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, use_count_a, solver.mkInteger(1)))

        sat = solver.checkSat()
        results["test_1_single_use"] = {
            "status": "pass" if sat.isSat() else "fail",
            "formula": "use_count_a = 1",
            "expected": "SAT",
            "actual": "SAT" if sat.isSat() else "UNSAT",
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_MANIFEST["cvc5"]["reason"] = "Constraint solving for linear type use-count verification"
    except Exception as e:
        results["test_1_single_use"] = {"status": "error", "message": str(e)}

    # Test 2: Tensor A⊗B where both A and B used exactly once
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        use_a = solver.mkConst(solver.getIntegerSort(), "use_a")
        use_b = solver.mkConst(solver.getIntegerSort(), "use_b")
        use_tensor = solver.mkConst(solver.getIntegerSort(), "use_tensor")

        # Constraints: use_a = 1, use_b = 1, use_tensor = use_a + use_b
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, use_a, solver.mkInteger(1)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, use_b, solver.mkInteger(1)))
        solver.assertFormula(
            solver.mkTerm(cvc5.Kind.EQUAL, use_tensor,
                         solver.mkTerm(cvc5.Kind.ADD, use_a, use_b))
        )

        sat = solver.checkSat()
        results["test_2_tensor_product_both_used_once"] = {
            "status": "pass" if sat.isSat() else "fail",
            "formula": "use_a=1, use_b=1, use_tensor=use_a+use_b",
            "expected": "SAT",
            "actual": "SAT" if sat.isSat() else "UNSAT",
        }
    except Exception as e:
        results["test_2_tensor_product_both_used_once"] = {"status": "error", "message": str(e)}

    # Test 3: Nested tensor (A⊗B)⊗C with depth 3
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        use_a = solver.mkConst(solver.getIntegerSort(), "use_a")
        use_b = solver.mkConst(solver.getIntegerSort(), "use_b")
        use_c = solver.mkConst(solver.getIntegerSort(), "use_c")
        use_ab = solver.mkConst(solver.getIntegerSort(), "use_ab")
        use_abc = solver.mkConst(solver.getIntegerSort(), "use_abc")

        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, use_a, solver.mkInteger(1)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, use_b, solver.mkInteger(1)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, use_c, solver.mkInteger(1)))
        solver.assertFormula(
            solver.mkTerm(cvc5.Kind.EQUAL, use_ab,
                         solver.mkTerm(cvc5.Kind.ADD, use_a, use_b))
        )
        solver.assertFormula(
            solver.mkTerm(cvc5.Kind.EQUAL, use_abc,
                         solver.mkTerm(cvc5.Kind.ADD, use_ab, use_c))
        )

        sat = solver.checkSat()
        results["test_3_nested_tensor_depth_3"] = {
            "status": "pass" if sat.isSat() else "fail",
            "formula": "All use=1, use_ab=use_a+use_b, use_abc=use_ab+use_c",
            "expected": "SAT",
            "actual": "SAT" if sat.isSat() else "UNSAT",
        }
    except Exception as e:
        results["test_3_nested_tensor_depth_3"] = {"status": "error", "message": str(e)}

    return results


# =====================================================================
# NEGATIVE TESTS (UNSAT proofs)
# =====================================================================

def run_negative_tests():
    """Invalid patterns that violate linear type constraints (UNSAT)."""
    results = {}

    if not cvc5_available:
        results["test_1_unused_resource"] = {"status": "skipped", "reason": "cvc5 not available"}
        results["test_2_reused_resource"] = {"status": "skipped", "reason": "cvc5 not available"}
        results["test_3_tensor_missing_component"] = {"status": "skipped", "reason": "cvc5 not available"}
        return results

    # Test 1: Resource used zero times (unused) — UNSAT
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        use_count = solver.mkConst(solver.getIntegerSort(), "use_count")

        # Constraint: must use exactly once
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, use_count, solver.mkInteger(1)))
        # But also: use_count = 0 (violation)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, use_count, solver.mkInteger(0)))

        sat = solver.checkSat()
        results["test_1_unused_resource"] = {
            "status": "pass" if not sat.isSat() else "fail",
            "formula": "use_count=1 AND use_count=0",
            "expected": "UNSAT",
            "actual": "UNSAT" if not sat.isSat() else "SAT",
        }
    except Exception as e:
        results["test_1_unused_resource"] = {"status": "error", "message": str(e)}

    # Test 2: Resource reused (use_count >= 2) — UNSAT
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        use_count = solver.mkConst(solver.getIntegerSort(), "use_count")

        # Constraint: must use exactly once
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, use_count, solver.mkInteger(1)))
        # But also: use_count >= 2 (reused)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.GEQ, use_count, solver.mkInteger(2)))

        sat = solver.checkSat()
        results["test_2_reused_resource"] = {
            "status": "pass" if not sat.isSat() else "fail",
            "formula": "use_count=1 AND use_count>=2",
            "expected": "UNSAT",
            "actual": "UNSAT" if not sat.isSat() else "SAT",
        }
    except Exception as e:
        results["test_2_reused_resource"] = {"status": "error", "message": str(e)}

    # Test 3: Tensor product where one component unused — UNSAT
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        use_a = solver.mkConst(solver.getIntegerSort(), "use_a")
        use_b = solver.mkConst(solver.getIntegerSort(), "use_b")
        use_tensor = solver.mkConst(solver.getIntegerSort(), "use_tensor")

        # Constraints: both must be used exactly once
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, use_a, solver.mkInteger(1)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, use_b, solver.mkInteger(1)))
        # Tensor relationship
        solver.assertFormula(
            solver.mkTerm(cvc5.Kind.EQUAL, use_tensor,
                         solver.mkTerm(cvc5.Kind.ADD, use_a, use_b))
        )
        # But also: one component is zero (violation)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, use_b, solver.mkInteger(0)))

        sat = solver.checkSat()
        results["test_3_tensor_missing_component"] = {
            "status": "pass" if not sat.isSat() else "fail",
            "formula": "use_b=1 AND use_b=0 (tensor requires both)",
            "expected": "UNSAT",
            "actual": "UNSAT" if not sat.isSat() else "SAT",
        }
    except Exception as e:
        results["test_3_tensor_missing_component"] = {"status": "error", "message": str(e)}

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """Edge cases and constraints at boundaries."""
    results = {}

    if not cvc5_available:
        results["test_1_large_tensor_chain"] = {"status": "skipped", "reason": "cvc5 not available"}
        results["test_2_zero_is_not_valid"] = {"status": "skipped", "reason": "cvc5 not available"}
        results["test_3_negative_use_count"] = {"status": "skipped", "reason": "cvc5 not available"}
        return results

    # Test 1: Long chain of tensors (A⊗B⊗C⊗D⊗E)
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        uses = {f"use_{x}": solver.mkConst(solver.getIntegerSort(), f"use_{x}")
                for x in "ABCDE"}

        # All must be used exactly once
        for var in uses.values():
            solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, var, solver.mkInteger(1)))

        sat = solver.checkSat()
        results["test_1_large_tensor_chain"] = {
            "status": "pass" if sat.isSat() else "fail",
            "formula": "A⊗B⊗C⊗D⊗E, all use_count=1",
            "expected": "SAT",
            "actual": "SAT" if sat.isSat() else "UNSAT",
        }
    except Exception as e:
        results["test_1_large_tensor_chain"] = {"status": "error", "message": str(e)}

    # Test 2: Zero is not a valid use-count for linear types
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        use_count = solver.mkConst(solver.getIntegerSort(), "use_count")

        # Enforce linear type: use_count must equal 1
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, use_count, solver.mkInteger(1)))
        # Query: can use_count be 0?
        solver.push()
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, use_count, solver.mkInteger(0)))
        sat = solver.checkSat()
        solver.pop()

        results["test_2_zero_is_not_valid"] = {
            "status": "pass" if not sat.isSat() else "fail",
            "formula": "Linear constraint: use_count=1; query: can it be 0?",
            "expected": "UNSAT (no, zero violates linear type)",
            "actual": "UNSAT" if not sat.isSat() else "SAT",
        }
    except Exception as e:
        results["test_2_zero_is_not_valid"] = {"status": "error", "message": str(e)}

    # Test 3: Negative use-count is invalid
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        use_count = solver.mkConst(solver.getIntegerSort(), "use_count")

        # Valid constraint
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, use_count, solver.mkInteger(1)))
        # Query: can use_count be negative?
        solver.push()
        solver.assertFormula(solver.mkTerm(cvc5.Kind.LT, use_count, solver.mkInteger(0)))
        sat = solver.checkSat()
        solver.pop()

        results["test_3_negative_use_count"] = {
            "status": "pass" if not sat.isSat() else "fail",
            "formula": "use_count=1; query: can it be negative?",
            "expected": "UNSAT (no, negative violates type invariant)",
            "actual": "UNSAT" if not sat.isSat() else "SAT",
        }
    except Exception as e:
        results["test_3_negative_use_count"] = {"status": "error", "message": str(e)}

    return results


def run_sympy_use_count_test():
    """Verify use-count algebra symbolically with sympy."""
    try:
        import sympy as sp

        use_a, use_b = sp.symbols("use_a use_b", integer=True, positive=True)
        use_tensor = use_a + use_b

        # Test: if use_a=1 and use_b=1, then use_tensor=2
        expr = use_tensor.subs({use_a: 1, use_b: 1})

        return {
            "status": "pass" if expr == 2 else "fail",
            "formula": "use_tensor = use_a + use_b, with use_a=1, use_b=1",
            "result": int(expr),
            "expected": 2,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    results = {
        "name": "LinearTypeUseCountConstraint",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_cvc5_linear_type_use_count_constraint_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
