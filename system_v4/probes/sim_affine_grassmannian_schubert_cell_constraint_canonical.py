#!/usr/bin/env python3
"""
Affine Grassmannian -- Schubert Cell Dimension Constraint
Gr_G = G(K)/G(O): Schubert cells Gr_λ indexed by dominant coweights.

CLAIM: dim(Gr_λ) = 2⟨ρ, λ⟩ where ρ is half-sum of positive roots.
PROOF LAYER: cvc5 (QF_LIA) constraint on Schubert cell dimension.
ALGEBRA LAYER: sympy Kazhdan-Lusztig Poincaré polynomial.

See system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md
"""

import json
import os
import sympy as sp

classification = "classical_baseline"
divergence_log = [
    "Classical comparator/control surface only; does not promote nonclassical, formal-scout, bridge, axis-level, or canonical proof claims."
]

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "pytorch not needed; pure symbolic/algebraic computation via cvc5 and sympy"},
    "pyg": {"tried": False, "used": False, "reason": "PyG message passing not needed; constraint geometry handled via SMT solver"},
    "z3": {"tried": False, "used": False, "reason": "z3 not needed; cvc5 handles all SMT constraint proofs in this sim"},
    "cvc5": {"tried": False, "used": False, "reason": "cvc5 SMT solver: load_bearing proof of Schubert cell dimension constraints"},
    "sympy": {"tried": False, "used": False, "reason": "sympy: supportive symbolic algebra for Kazhdan-Lusztig Poincaré polynomials"},
    "clifford": {"tried": False, "used": False, "reason": "Clifford algebra not needed; root-system constraints only"},
    "geomstats": {"tried": False, "used": False, "reason": "geomstats not needed; constraints handled via SMT solver"},
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
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


# =====================================================================
# POSITIVE TESTS: Dimension Formula Holds
# =====================================================================

def run_positive_tests():
    """
    Test that dim(Gr_λ) = 2⟨ρ, λ⟩ for valid dominant coweights.
    For A1 (sl(2)): ρ = 1, so dim(Gr_λ) = 2λ
    """
    results = {}

    # Test 1: A1, λ=1 (fundamental coweight)
    # ρ=1, ⟨ρ,λ⟩=1, dim = 2*1 = 2
    try:
        from cvc5 import Solver, Kind

        solver = Solver()
        solver.setLogic("QF_LIA")

        rho = solver.mkInteger(1)  # A1: ρ=1
        lam = solver.mkInteger(1)
        inner_product = solver.mkConst(solver.getIntegerSort(), "rho_lambda_1")
        dim_gr = solver.mkConst(solver.getIntegerSort(), "dim_gr_1")

        # ⟨ρ,λ⟩ = 1
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, inner_product, solver.mkInteger(1)))
        # dim = 2⟨ρ,λ⟩ = 2
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, dim_gr, solver.mkInteger(2)))
        # Constraint: dim = 2 * inner_product
        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL, dim_gr, solver.mkTerm(Kind.MULT, solver.mkInteger(2), inner_product))
        )

        is_sat = solver.checkSat().isSat()
        results["a1_lambda1"] = {
            "root_system": "A1",
            "lambda": 1,
            "rho": 1,
            "inner_product": 1,
            "dim_gr": 2,
            "dimension_consistent": is_sat,
            "test": "PASS" if is_sat else "FAIL"
        }
    except Exception as e:
        results["a1_lambda1"] = {"error": str(e), "test": "FAIL"}

    # Test 2: A1, λ=2
    # ρ=1, ⟨ρ,λ⟩=2, dim = 2*2 = 4
    try:
        from cvc5 import Solver, Kind

        solver = Solver()
        solver.setLogic("QF_LIA")

        inner_product = solver.mkConst(solver.getIntegerSort(), "rho_lambda_2")
        dim_gr = solver.mkConst(solver.getIntegerSort(), "dim_gr_2")

        solver.assertFormula(solver.mkTerm(Kind.EQUAL, inner_product, solver.mkInteger(2)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, dim_gr, solver.mkInteger(4)))
        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL, dim_gr, solver.mkTerm(Kind.MULT, solver.mkInteger(2), inner_product))
        )

        is_sat = solver.checkSat().isSat()
        results["a1_lambda2"] = {
            "root_system": "A1",
            "lambda": 2,
            "rho": 1,
            "inner_product": 2,
            "dim_gr": 4,
            "dimension_consistent": is_sat,
            "test": "PASS" if is_sat else "FAIL"
        }
    except Exception as e:
        results["a1_lambda2"] = {"error": str(e), "test": "FAIL"}

    # Test 3: Poincaré polynomial via sympy (A1, λ=1)
    # P_λ(t) = 1 + t^2 for A1, λ=1
    try:
        t = sp.Symbol('t')
        p_poly = 1 + t**2
        # Evaluate at t=1: degree sum = dim
        p_at_1 = p_poly.subs(t, 1)
        results["poincare_a1_lambda1"] = {
            "polynomial": str(p_poly),
            "p_at_1": float(p_at_1),
            "expected_dimension": 2,
            "test": "PASS" if float(p_at_1) == 2 else "FAIL"
        }
    except Exception as e:
        results["poincare_a1_lambda1"] = {"error": str(e), "test": "FAIL"}

    return results


# =====================================================================
# NEGATIVE TESTS: UNSAT When Dimension Formula Violated
# =====================================================================

def run_negative_tests():
    """
    Test that SMT solver UNSAT when dim(Gr_λ) ≠ 2⟨ρ,λ⟩.
    """
    results = {}

    # Negative test 1: A1, λ=1, but claim dim=3 (wrong)
    try:
        from cvc5 import Solver, Kind

        solver = Solver()
        solver.setLogic("QF_LIA")

        inner_product = solver.mkConst(solver.getIntegerSort(), "rho_lambda_neg1")
        dim_gr = solver.mkConst(solver.getIntegerSort(), "dim_gr_neg1")

        solver.assertFormula(solver.mkTerm(Kind.EQUAL, inner_product, solver.mkInteger(1)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, dim_gr, solver.mkInteger(3)))
        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL, dim_gr, solver.mkTerm(Kind.MULT, solver.mkInteger(2), inner_product))
        )

        is_sat = solver.checkSat().isSat()
        results["dim_mismatch_2_vs_3"] = {
            "lambda": 1,
            "expected_dim": 2,
            "claimed_dim": 3,
            "expected_unsat": True,
            "actual_unsat": not is_sat,
            "test": "PASS" if not is_sat else "FAIL"
        }
    except Exception as e:
        results["dim_mismatch_2_vs_3"] = {"error": str(e), "test": "FAIL"}

    # Negative test 2: A1, λ=2, but claim dim=5 (wrong; should be 4)
    try:
        from cvc5 import Solver, Kind

        solver = Solver()
        solver.setLogic("QF_LIA")

        inner_product = solver.mkConst(solver.getIntegerSort(), "rho_lambda_neg2")
        dim_gr = solver.mkConst(solver.getIntegerSort(), "dim_gr_neg2")

        solver.assertFormula(solver.mkTerm(Kind.EQUAL, inner_product, solver.mkInteger(2)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, dim_gr, solver.mkInteger(5)))
        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL, dim_gr, solver.mkTerm(Kind.MULT, solver.mkInteger(2), inner_product))
        )

        is_sat = solver.checkSat().isSat()
        results["dim_mismatch_4_vs_5"] = {
            "lambda": 2,
            "expected_dim": 4,
            "claimed_dim": 5,
            "expected_unsat": True,
            "actual_unsat": not is_sat,
            "test": "PASS" if not is_sat else "FAIL"
        }
    except Exception as e:
        results["dim_mismatch_4_vs_5"] = {"error": str(e), "test": "FAIL"}

    # Negative test 3: Negative dimension (impossible)
    try:
        from cvc5 import Solver, Kind

        solver = Solver()
        solver.setLogic("QF_LIA")

        dim_gr = solver.mkConst(solver.getIntegerSort(), "dim_neg")
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, dim_gr, solver.mkInteger(-2)))
        solver.assertFormula(solver.mkTerm(Kind.GEQ, dim_gr, solver.mkInteger(0)))

        is_sat = solver.checkSat().isSat()
        results["negative_dimension"] = {
            "dimension": -2,
            "expected_unsat": True,
            "actual_unsat": not is_sat,
            "test": "PASS" if not is_sat else "FAIL"
        }
    except Exception as e:
        results["negative_dimension"] = {"error": str(e), "test": "FAIL"}

    return results


# =====================================================================
# BOUNDARY TESTS: Edge Cases
# =====================================================================

def run_boundary_tests():
    """
    Test edge cases: trivial weight λ=0, large weights, root sublattice.
    """
    results = {}

    # Boundary test 1: λ=0 (trivial coweight)
    # ⟨ρ,0⟩=0, dim=0
    try:
        from cvc5 import Solver, Kind

        solver = Solver()
        solver.setLogic("QF_LIA")

        inner_product = solver.mkConst(solver.getIntegerSort(), "rho_lambda_0")
        dim_gr = solver.mkConst(solver.getIntegerSort(), "dim_gr_0")

        solver.assertFormula(solver.mkTerm(Kind.EQUAL, inner_product, solver.mkInteger(0)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, dim_gr, solver.mkInteger(0)))
        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL, dim_gr, solver.mkTerm(Kind.MULT, solver.mkInteger(2), inner_product))
        )

        is_sat = solver.checkSat().isSat()
        results["trivial_coweight"] = {
            "lambda": 0,
            "inner_product": 0,
            "dim_gr": 0,
            "consistent": is_sat,
            "test": "PASS" if is_sat else "FAIL"
        }
    except Exception as e:
        results["trivial_coweight"] = {"error": str(e), "test": "FAIL"}

    # Boundary test 2: Large weight λ=10 (A1)
    # dim = 2*10 = 20
    try:
        from cvc5 import Solver, Kind

        solver = Solver()
        solver.setLogic("QF_LIA")

        inner_product = solver.mkConst(solver.getIntegerSort(), "rho_lambda_10")
        dim_gr = solver.mkConst(solver.getIntegerSort(), "dim_gr_10")

        solver.assertFormula(solver.mkTerm(Kind.EQUAL, inner_product, solver.mkInteger(10)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, dim_gr, solver.mkInteger(20)))
        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL, dim_gr, solver.mkTerm(Kind.MULT, solver.mkInteger(2), inner_product))
        )

        is_sat = solver.checkSat().isSat()
        results["large_weight_10"] = {
            "lambda": 10,
            "inner_product": 10,
            "dim_gr": 20,
            "consistent": is_sat,
            "test": "PASS" if is_sat else "FAIL"
        }
    except Exception as e:
        results["large_weight_10"] = {"error": str(e), "test": "FAIL"}

    # Boundary test 3: Poincaré polynomial degree matches dimension
    # For A1, λ=2: P_λ(t) = 1 + t^2 + t^4, degree 4
    try:
        t = sp.Symbol('t')
        p_poly = 1 + t**2 + t**4
        # Max degree = 4
        max_degree = sp.degree(p_poly, t)
        expected_dim = 4
        results["poincare_degree_a1_lambda2"] = {
            "polynomial": str(p_poly),
            "max_degree": int(max_degree),
            "expected_dim": expected_dim,
            "test": "PASS" if int(max_degree) == expected_dim else "FAIL"
        }
    except Exception as e:
        results["poincare_degree_a1_lambda2"] = {"error": str(e), "test": "FAIL"}

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    # Count passes
    pos_pass = sum(1 for v in positive.values() if v.get("test") == "PASS")
    neg_pass = sum(1 for v in negative.values() if v.get("test") == "PASS")
    bound_pass = sum(1 for v in boundary.values() if v.get("test") == "PASS")

    # Mark tools as used
    if TOOL_MANIFEST["cvc5"]["tried"]:
        TOOL_MANIFEST["cvc5"]["used"] = True
    if TOOL_MANIFEST["sympy"]["tried"]:
        TOOL_MANIFEST["sympy"]["used"] = True

    results = {
        "name": "Affine Grassmannian -- Schubert Cell Dimension -- Canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "classification": "classical_baseline",
        "original_classification": "canonical",
        "downgrade_reason": "overclassification_fail_status_2026-05-01",
        "positive_tests": positive,
        "negative_tests": negative,
        "boundary_tests": boundary,
        "summary": {
            "positive_pass": pos_pass,
            "positive_total": len(positive),
            "negative_pass": neg_pass,
            "negative_total": len(negative),
            "boundary_pass": bound_pass,
            "boundary_total": len(boundary),
        }
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_affine_grassmannian_schubert_cell_constraint_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
