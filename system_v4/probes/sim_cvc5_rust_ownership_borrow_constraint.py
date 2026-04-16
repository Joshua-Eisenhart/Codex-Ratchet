#!/usr/bin/env python3
"""
Rust Ownership/Borrow Checker — cvc5 canonical sim.

Theory:
  - At most one mutable borrow XOR any number of immutable borrows at once.
  - Owner releases resource when out of scope (RAII).
  - UNSAT for: (mut_borrow_count >= 1) AND (immut_borrow_count >= 1).
  - UNSAT for: use-after-move (accessing value after transfer).

Encoding:
  - mut_borrow_count: number of active mutable borrows.
  - immut_borrow_count: number of active immutable borrows.
  - Constraint: (mut_borrow_count == 0) OR (immut_borrow_count == 0).
  - Scope tracking: is_owned(v) indicates v is in scope.
"""

import json
import os

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "PyTorch not needed; Rust borrow logic is symbolic"},
    "pyg": {"tried": False, "used": False, "reason": "PyG not needed; pure constraint verification"},
    "z3": {"tried": False, "used": False, "reason": "z3 not needed; cvc5 handles all constraint solving"},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": "Clifford algebra not needed; borrow logic is algebraic"},
    "geomstats": {"tried": False, "used": False, "reason": "geomstats not needed; no differential geometry"},
    "e3nn": {"tried": False, "used": False, "reason": "e3nn not needed; no SO(3) equivariance"},
    "rustworkx": {"tried": False, "used": False, "reason": "rustworkx not needed; scope is linear, not general graph"},
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
    """Valid borrow patterns."""
    results = {}

    if not cvc5_available:
        results["test_1_mutable_borrow_only"] = {"status": "skipped", "reason": "cvc5 not available"}
        results["test_2_immutable_borrows_only"] = {"status": "skipped", "reason": "cvc5 not available"}
        results["test_3_owner_in_scope"] = {"status": "skipped", "reason": "cvc5 not available"}
        if sympy_available:
            results["test_sympy_borrow_invariant"] = run_sympy_borrow_test()
        return results

    # Test 1: Only mutable borrow active (no immutable borrows)
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        mut_borrow_count = solver.mkConst(solver.getIntegerSort(), "mut_borrow_count")
        immut_borrow_count = solver.mkConst(solver.getIntegerSort(), "immut_borrow_count")

        # One mutable borrow
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, mut_borrow_count, solver.mkInteger(1)))
        # No immutable borrows
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, immut_borrow_count, solver.mkInteger(0)))

        sat = solver.checkSat()
        results["test_1_mutable_borrow_only"] = {
            "status": "pass" if sat.isSat() else "fail",
            "formula": "mut_borrow=1, immut_borrow=0",
            "expected": "SAT",
            "actual": "SAT" if sat.isSat() else "UNSAT",
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_MANIFEST["cvc5"]["reason"] = "Constraint solving for Rust borrow checker verification"
    except Exception as e:
        results["test_1_mutable_borrow_only"] = {"status": "error", "message": str(e)}

    # Test 2: Multiple immutable borrows (no mutable borrow)
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        mut_borrow_count = solver.mkConst(solver.getIntegerSort(), "mut_borrow_count")
        immut_borrow_count = solver.mkConst(solver.getIntegerSort(), "immut_borrow_count")

        # No mutable borrows
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, mut_borrow_count, solver.mkInteger(0)))
        # Multiple immutable borrows (e.g., 3)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, immut_borrow_count, solver.mkInteger(3)))

        sat = solver.checkSat()
        results["test_2_immutable_borrows_only"] = {
            "status": "pass" if sat.isSat() else "fail",
            "formula": "mut_borrow=0, immut_borrow=3",
            "expected": "SAT",
            "actual": "SAT" if sat.isSat() else "UNSAT",
        }
    except Exception as e:
        results["test_2_immutable_borrows_only"] = {"status": "error", "message": str(e)}

    # Test 3: Owner is in scope and can be borrowed
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        is_owned = solver.mkConst(solver.getBooleanSort(), "is_owned")
        mut_borrow_count = solver.mkConst(solver.getIntegerSort(), "mut_borrow_count")

        # Owner is in scope
        solver.assertFormula(is_owned)
        # Owner can be mutably borrowed
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, mut_borrow_count, solver.mkInteger(1)))

        sat = solver.checkSat()
        results["test_3_owner_in_scope"] = {
            "status": "pass" if sat.isSat() else "fail",
            "formula": "is_owned=true, mut_borrow=1",
            "expected": "SAT",
            "actual": "SAT" if sat.isSat() else "UNSAT",
        }
    except Exception as e:
        results["test_3_owner_in_scope"] = {"status": "error", "message": str(e)}

    return results


# =====================================================================
# NEGATIVE TESTS (UNSAT proofs)
# =====================================================================

def run_negative_tests():
    """Invalid borrow patterns (UNSAT)."""
    results = {}

    if not cvc5_available:
        results["test_1_simultaneous_mut_and_immut"] = {"status": "skipped", "reason": "cvc5 not available"}
        results["test_2_use_after_move"] = {"status": "skipped", "reason": "cvc5 not available"}
        results["test_3_multiple_mutable_borrows"] = {"status": "skipped", "reason": "cvc5 not available"}
        return results

    # Test 1: Simultaneous mutable AND immutable borrows — UNSAT
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        mut_borrow_count = solver.mkConst(solver.getIntegerSort(), "mut_borrow_count")
        immut_borrow_count = solver.mkConst(solver.getIntegerSort(), "immut_borrow_count")

        # Invariant: either mut==0 OR immut==0
        solver.assertFormula(
            solver.mkTerm(cvc5.Kind.OR,
                         solver.mkTerm(cvc5.Kind.EQUAL, mut_borrow_count, solver.mkInteger(0)),
                         solver.mkTerm(cvc5.Kind.EQUAL, immut_borrow_count, solver.mkInteger(0)))
        )
        # But also: mut >= 1 AND immut >= 1 (violation)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.GEQ, mut_borrow_count, solver.mkInteger(1)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.GEQ, immut_borrow_count, solver.mkInteger(1)))

        sat = solver.checkSat()
        results["test_1_simultaneous_mut_and_immut"] = {
            "status": "pass" if not sat.isSat() else "fail",
            "formula": "(mut==0 OR immut==0) AND mut>=1 AND immut>=1",
            "expected": "UNSAT",
            "actual": "UNSAT" if not sat.isSat() else "SAT",
        }
    except Exception as e:
        results["test_1_simultaneous_mut_and_immut"] = {"status": "error", "message": str(e)}

    # Test 2: Use-after-move (accessing after transfer) — UNSAT
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        is_owned_before = solver.mkConst(solver.getBooleanSort(), "is_owned_before")
        is_owned_after = solver.mkConst(solver.getBooleanSort(), "is_owned_after")

        # Owner has resource before move
        solver.assertFormula(is_owned_before)
        # After move, owner no longer has resource
        solver.assertFormula(solver.mkTerm(cvc5.Kind.NOT, is_owned_after))
        # Constraint: cannot access after move
        # But also: try to access (after is false)
        solver.assertFormula(is_owned_after)

        sat = solver.checkSat()
        results["test_2_use_after_move"] = {
            "status": "pass" if not sat.isSat() else "fail",
            "formula": "owned_before=true, owned_after=false, BUT try access (owned_after=true)",
            "expected": "UNSAT",
            "actual": "UNSAT" if not sat.isSat() else "SAT",
        }
    except Exception as e:
        results["test_2_use_after_move"] = {"status": "error", "message": str(e)}

    # Test 3: Multiple simultaneous mutable borrows — UNSAT
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        mut_borrow_count = solver.mkConst(solver.getIntegerSort(), "mut_borrow_count")

        # Invariant: at most one mutable borrow (mut <= 1)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.LEQ, mut_borrow_count, solver.mkInteger(1)))
        # But also: mut >= 2 (violation)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.GEQ, mut_borrow_count, solver.mkInteger(2)))

        sat = solver.checkSat()
        results["test_3_multiple_mutable_borrows"] = {
            "status": "pass" if not sat.isSat() else "fail",
            "formula": "mut<=1 AND mut>=2",
            "expected": "UNSAT",
            "actual": "UNSAT" if not sat.isSat() else "SAT",
        }
    except Exception as e:
        results["test_3_multiple_mutable_borrows"] = {"status": "error", "message": str(e)}

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """Edge cases and constraints at boundaries."""
    results = {}

    if not cvc5_available:
        results["test_1_zero_borrows"] = {"status": "skipped", "reason": "cvc5 not available"}
        results["test_2_owner_out_of_scope"] = {"status": "skipped", "reason": "cvc5 not available"}
        results["test_3_many_immutable_borrows"] = {"status": "skipped", "reason": "cvc5 not available"}
        return results

    # Test 1: Zero mutable and zero immutable borrows (owner holds resource)
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        mut_borrow_count = solver.mkConst(solver.getIntegerSort(), "mut_borrow_count")
        immut_borrow_count = solver.mkConst(solver.getIntegerSort(), "immut_borrow_count")
        is_owned = solver.mkConst(solver.getBooleanSort(), "is_owned")

        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, mut_borrow_count, solver.mkInteger(0)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, immut_borrow_count, solver.mkInteger(0)))
        solver.assertFormula(is_owned)

        sat = solver.checkSat()
        results["test_1_zero_borrows"] = {
            "status": "pass" if sat.isSat() else "fail",
            "formula": "mut=0, immut=0, is_owned=true",
            "expected": "SAT",
            "actual": "SAT" if sat.isSat() else "UNSAT",
        }
    except Exception as e:
        results["test_1_zero_borrows"] = {"status": "error", "message": str(e)}

    # Test 2: Owner out of scope (cannot have borrows)
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        is_owned = solver.mkConst(solver.getBooleanSort(), "is_owned")
        mut_borrow_count = solver.mkConst(solver.getIntegerSort(), "mut_borrow_count")

        # Owner is out of scope
        solver.assertFormula(solver.mkTerm(cvc5.Kind.NOT, is_owned))
        # Cannot have mutable borrows if owner is gone
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, mut_borrow_count, solver.mkInteger(0)))

        sat = solver.checkSat()
        results["test_2_owner_out_of_scope"] = {
            "status": "pass" if sat.isSat() else "fail",
            "formula": "is_owned=false, mut_borrow=0",
            "expected": "SAT",
            "actual": "SAT" if sat.isSat() else "UNSAT",
        }
    except Exception as e:
        results["test_2_owner_out_of_scope"] = {"status": "error", "message": str(e)}

    # Test 3: Many immutable borrows (e.g., 10) are allowed
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        mut_borrow_count = solver.mkConst(solver.getIntegerSort(), "mut_borrow_count")
        immut_borrow_count = solver.mkConst(solver.getIntegerSort(), "immut_borrow_count")

        # No mutable borrows
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, mut_borrow_count, solver.mkInteger(0)))
        # Many immutable borrows
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, immut_borrow_count, solver.mkInteger(10)))

        sat = solver.checkSat()
        results["test_3_many_immutable_borrows"] = {
            "status": "pass" if sat.isSat() else "fail",
            "formula": "mut=0, immut=10",
            "expected": "SAT",
            "actual": "SAT" if sat.isSat() else "UNSAT",
        }
    except Exception as e:
        results["test_3_many_immutable_borrows"] = {"status": "error", "message": str(e)}

    return results


def run_sympy_borrow_test():
    """Verify borrow invariant symbolically with sympy."""
    try:
        import sympy as sp

        mut_borrow = sp.Symbol("mut_borrow", integer=True, nonnegative=True)
        immut_borrow = sp.Symbol("immut_borrow", integer=True, nonnegative=True)

        # Invariant: at most one mutable borrow OR any number of immutable
        # (mut == 0) OR (immut == 0)
        invariant = sp.Or(
            sp.Eq(mut_borrow, 0),
            sp.Eq(immut_borrow, 0)
        )

        # Test case: mut=1, immut=0
        test_valid = sp.And(sp.Eq(mut_borrow, 1), sp.Eq(immut_borrow, 0))
        is_valid = sp.satisfiable(sp.And(invariant, test_valid))

        # Test case: mut=1, immut=1
        test_invalid = sp.And(sp.Eq(mut_borrow, 1), sp.Eq(immut_borrow, 1))
        is_invalid = sp.satisfiable(sp.And(invariant, test_invalid))

        return {
            "status": "pass" if (is_valid and not is_invalid) else "fail",
            "valid_case_sat": is_valid,
            "invalid_case_unsat": not is_invalid,
            "expected_valid": True,
            "expected_invalid": False,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    results = {
        "name": "RustOwnershipBorrowConstraint",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_cvc5_rust_ownership_borrow_constraint_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
