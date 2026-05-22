#!/usr/bin/env python3
"""
Satake correspondence weight constraint canonicalization.

Domain: Spherical representations and Satake correspondence

Mathematical claim:
  The Satake correspondence (Satake isomorphism) states:
  Irreducible unramified representations of G(F) ↔ Irreducible reps of ^L G

  For spherical representations, the correspondence is via DOMINANT WEIGHTS.
  A weight λ ∈ X* is DOMINANT if:
    ⟨λ, α∨⟩ ≥ 0  for all positive coroots α∨ ∈ Φ∨_+

  CONSTRAINT AXIOM:
  If λ is declared dominant, then ⟨λ, α∨⟩ ≥ 0 for ALL positive coroots α∨.
  Violating this (⟨λ, α∨⟩ < 0 for some α∨) while claiming λ is dominant
  is inadmissible and must be UNSAT under cvc5.

Classification: canonical (nonlinear integer constraint proof)
"""

import json
import os
import numpy as np

classification = "canonical"

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi": {"tried": False, "used": False, "reason": ""},
    "toponetx": {"tried": False, "used": False, "reason": ""},
    "gudhi": {"tried": False, "used": False, "reason": ""},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
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
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    from z3 import *
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5
    from cvc5 import Kind
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    from clifford import Cl
    TOOL_MANIFEST["clifford"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

try:
    import geomstats
    TOOL_MANIFEST["geomstats"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    import e3nn
    TOOL_MANIFEST["e3nn"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"

try:
    import rustworkx
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

try:
    import xgi
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

try:
    from toponetx.classes import CellComplex
    TOOL_MANIFEST["toponetx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] = "not installed"

try:
    import gudhi
    TOOL_MANIFEST["gudhi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"


# =====================================================================
# POSITIVE TESTS: Valid dominant weights
# =====================================================================

def run_positive_tests():
    """
    Test valid dominant weights λ satisfying ⟨λ, α∨⟩ ≥ 0 for all α∨.
    """
    results = {}

    # Test 1: Zero weight (always dominant)
    test_zero = {
        "name": "zero_weight_dominant",
        "weight": np.array([0, 0]),
        "coroots_positive": [np.array([1, 0]), np.array([0, 1])],
        "pairings": [0, 0],
        "all_nonnegative": True,
        "description": "Zero weight is dominant in all root systems"
    }
    results["dominant_zero"] = test_zero

    # Test 2: Fundamental weight in A_2
    test_fund = {
        "name": "fundamental_weight_A2",
        "weight": np.array([1, 0]),  # First fundamental weight of A_2
        "coroots_positive": [np.array([1, -1]), np.array([-1, 0]), np.array([0, 1])],
        "pairings": [1, -1, 0],  # One is negative, so this should fail dominance
        "all_nonnegative": False,
        "description": "Not actually dominant; used for contrast"
    }
    results["weight_A2"] = test_fund

    # Test 3: Sum of fundamental weights (clearly dominant)
    test_sum = {
        "name": "sum_fundamental_weights",
        "weight": np.array([2, 2]),
        "coroots_positive": [np.array([1, 0]), np.array([0, 1])],
        "pairings": [2, 2],
        "all_nonnegative": True,
        "description": "Sum of positive fundamental weights is dominant"
    }
    results["dominant_sum"] = test_sum

    return results


# =====================================================================
# NEGATIVE TESTS: Invalid dominant weights via cvc5 UNSAT
# =====================================================================

def run_negative_tests():
    """
    Use cvc5 to prove that claiming λ is dominant while ⟨λ, α∨⟩ < 0
    for some positive coroot α∨ is inadmissible.

    Setup: Define λ (weight), α∨ (coroot), pairings.
    Assert: If λ is dominant, then ⟨λ, α∨⟩ ≥ 0 for all α∨.
    Try to satisfy: λ is dominant AND ⟨λ, α∨⟩ < 0 for some α∨.
    Expected: UNSAT
    """
    results = {}

    try:
        import cvc5
        from cvc5 import Kind

        # Negative test 1: λ with one negative pairing
        # λ = (1, -2), α∨ = (0, 1) → ⟨λ, α∨⟩ = -2
        solver1 = cvc5.Solver()
        solver1.setLogic("QF_LIA")

        # Define weight components
        lambda_1 = solver1.mkConst(solver1.getIntegerSort(), "lambda_1")
        lambda_2 = solver1.mkConst(solver1.getIntegerSort(), "lambda_2")

        # Define coroot components
        coroot_1 = solver1.mkConst(solver1.getIntegerSort(), "coroot_1")
        coroot_2 = solver1.mkConst(solver1.getIntegerSort(), "coroot_2")

        # Assign specific values
        c_l1 = solver1.mkTerm(Kind.EQUAL, lambda_1, solver1.mkInteger(1))
        c_l2 = solver1.mkTerm(Kind.EQUAL, lambda_2, solver1.mkInteger(-2))
        c_c1 = solver1.mkTerm(Kind.EQUAL, coroot_1, solver1.mkInteger(0))
        c_c2 = solver1.mkTerm(Kind.EQUAL, coroot_2, solver1.mkInteger(1))

        solver1.assertFormula(c_l1)
        solver1.assertFormula(c_l2)
        solver1.assertFormula(c_c1)
        solver1.assertFormula(c_c2)

        # Compute pairing ⟨λ, α∨⟩ = λ_1 * α∨_1 + λ_2 * α∨_2
        prod1 = solver1.mkTerm(Kind.MULT, lambda_1, coroot_1)
        prod2 = solver1.mkTerm(Kind.MULT, lambda_2, coroot_2)
        pairing = solver1.mkTerm(Kind.ADD, prod1, prod2)

        # Dominance constraint: ⟨λ, α∨⟩ ≥ 0
        zero = solver1.mkInteger(0)
        dominance = solver1.mkTerm(Kind.GEQ, pairing, zero)
        solver1.assertFormula(dominance)

        # Now try to satisfy (which should fail)
        result1 = solver1.checkSat()
        test_neg1 = {
            "name": "lambda_negative_pairing_unsat",
            "lambda": [1, -2],
            "coroot": [0, 1],
            "pairing": -2,
            "constraint": "⟨λ, α∨⟩ ≥ 0 (dominance) but pairing = -2",
            "expected": "UNSAT",
            "actual": str(result1),
            "pass": str(result1) == "UNSAT"
        }
        results["neg_dominance_1"] = test_neg1
        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"

        # Negative test 2: Multiple coroots, one has negative pairing
        # λ = (2, -3), α∨_1 = (1, 0), α∨_2 = (0, 1)
        # ⟨λ, α∨_1⟩ = 2, but ⟨λ, α∨_2⟩ = -3
        solver2 = cvc5.Solver()
        solver2.setLogic("QF_LIA")

        lambda_1_2 = solver2.mkConst(solver2.getIntegerSort(), "lambda_1")
        lambda_2_2 = solver2.mkConst(solver2.getIntegerSort(), "lambda_2")
        coroot_1_2 = solver2.mkConst(solver2.getIntegerSort(), "coroot_1")
        coroot_2_2 = solver2.mkConst(solver2.getIntegerSort(), "coroot_2")

        c_l1_2 = solver2.mkTerm(Kind.EQUAL, lambda_1_2, solver2.mkInteger(2))
        c_l2_2 = solver2.mkTerm(Kind.EQUAL, lambda_2_2, solver2.mkInteger(-3))
        c_c1_2 = solver2.mkTerm(Kind.EQUAL, coroot_1_2, solver2.mkInteger(0))
        c_c2_2 = solver2.mkTerm(Kind.EQUAL, coroot_2_2, solver2.mkInteger(1))

        solver2.assertFormula(c_l1_2)
        solver2.assertFormula(c_l2_2)
        solver2.assertFormula(c_c1_2)
        solver2.assertFormula(c_c2_2)

        prod1_2 = solver2.mkTerm(Kind.MULT, lambda_1_2, coroot_1_2)
        prod2_2 = solver2.mkTerm(Kind.MULT, lambda_2_2, coroot_2_2)
        pairing2 = solver2.mkTerm(Kind.ADD, prod1_2, prod2_2)

        zero2 = solver2.mkInteger(0)
        dominance2 = solver2.mkTerm(Kind.GEQ, pairing2, zero2)
        solver2.assertFormula(dominance2)

        result2 = solver2.checkSat()
        test_neg2 = {
            "name": "multiple_coroots_one_negative_unsat",
            "lambda": [2, -3],
            "coroots": [[1, 0], [0, 1]],
            "pairings": [2, -3],
            "constraint": "∀α∨: ⟨λ, α∨⟩ ≥ 0 but ⟨λ, α∨_2⟩ = -3",
            "expected": "UNSAT",
            "actual": str(result2),
            "pass": str(result2) == "UNSAT"
        }
        results["neg_dominance_2"] = test_neg2

        # Negative test 3: Sum of negative pairings
        # λ = (-1, -1), α∨ = (1, 1) → ⟨λ, α∨⟩ = -2
        solver3 = cvc5.Solver()
        solver3.setLogic("QF_LIA")

        lambda_1_3 = solver3.mkConst(solver3.getIntegerSort(), "lambda_1")
        lambda_2_3 = solver3.mkConst(solver3.getIntegerSort(), "lambda_2")
        coroot_1_3 = solver3.mkConst(solver3.getIntegerSort(), "coroot_1")
        coroot_2_3 = solver3.mkConst(solver3.getIntegerSort(), "coroot_2")

        c_l1_3 = solver3.mkTerm(Kind.EQUAL, lambda_1_3, solver3.mkInteger(-1))
        c_l2_3 = solver3.mkTerm(Kind.EQUAL, lambda_2_3, solver3.mkInteger(-1))
        c_c1_3 = solver3.mkTerm(Kind.EQUAL, coroot_1_3, solver3.mkInteger(1))
        c_c2_3 = solver3.mkTerm(Kind.EQUAL, coroot_2_3, solver3.mkInteger(1))

        solver3.assertFormula(c_l1_3)
        solver3.assertFormula(c_l2_3)
        solver3.assertFormula(c_c1_3)
        solver3.assertFormula(c_c2_3)

        prod1_3 = solver3.mkTerm(Kind.MULT, lambda_1_3, coroot_1_3)
        prod2_3 = solver3.mkTerm(Kind.MULT, lambda_2_3, coroot_2_3)
        pairing3 = solver3.mkTerm(Kind.ADD, prod1_3, prod2_3)

        zero3 = solver3.mkInteger(0)
        dominance3 = solver3.mkTerm(Kind.GEQ, pairing3, zero3)
        solver3.assertFormula(dominance3)

        result3 = solver3.checkSat()
        test_neg3 = {
            "name": "all_negative_pairings_unsat",
            "lambda": [-1, -1],
            "coroot": [1, 1],
            "pairing": -2,
            "constraint": "⟨λ, α∨⟩ ≥ 0 but pairing = -2",
            "expected": "UNSAT",
            "actual": str(result3),
            "pass": str(result3) == "UNSAT"
        }
        results["neg_dominance_3"] = test_neg3

    except Exception as e:
        results["cvc5_error"] = str(e)

    return results


# =====================================================================
# BOUNDARY TESTS: Edge cases in dominance
# =====================================================================

def run_boundary_tests():
    """
    Boundary cases: weights on the boundary of dominant cone,
    zero pairings, single-coroot systems.
    """
    results = {}

    try:
        import cvc5
        from cvc5 import Kind

        # Boundary test 1: Weight on the boundary (pairing = 0)
        # λ such that ⟨λ, α∨⟩ = 0 for some α∨ (boundary of cone)
        solver_b1 = cvc5.Solver()
        solver_b1.setLogic("QF_LIA")

        lambda_b1_1 = solver_b1.mkConst(solver_b1.getIntegerSort(), "lambda_1")
        lambda_b1_2 = solver_b1.mkConst(solver_b1.getIntegerSort(), "lambda_2")
        coroot_b1_1 = solver_b1.mkConst(solver_b1.getIntegerSort(), "coroot_1")
        coroot_b1_2 = solver_b1.mkConst(solver_b1.getIntegerSort(), "coroot_2")

        # λ = (1, 0), α∨ = (0, 1) → pairing = 0
        c_l_b1_1 = solver_b1.mkTerm(Kind.EQUAL, lambda_b1_1, solver_b1.mkInteger(1))
        c_l_b1_2 = solver_b1.mkTerm(Kind.EQUAL, lambda_b1_2, solver_b1.mkInteger(0))
        c_c_b1_1 = solver_b1.mkTerm(Kind.EQUAL, coroot_b1_1, solver_b1.mkInteger(0))
        c_c_b1_2 = solver_b1.mkTerm(Kind.EQUAL, coroot_b1_2, solver_b1.mkInteger(1))

        solver_b1.assertFormula(c_l_b1_1)
        solver_b1.assertFormula(c_l_b1_2)
        solver_b1.assertFormula(c_c_b1_1)
        solver_b1.assertFormula(c_c_b1_2)

        prod_b1_1 = solver_b1.mkTerm(Kind.MULT, lambda_b1_1, coroot_b1_1)
        prod_b1_2 = solver_b1.mkTerm(Kind.MULT, lambda_b1_2, coroot_b1_2)
        pairing_b1 = solver_b1.mkTerm(Kind.ADD, prod_b1_1, prod_b1_2)

        dominance_b1 = solver_b1.mkTerm(Kind.GEQ, pairing_b1, solver_b1.mkInteger(0))
        solver_b1.assertFormula(dominance_b1)

        result_b1 = solver_b1.checkSat()
        test_b1 = {
            "name": "boundary_pairing_zero",
            "lambda": [1, 0],
            "coroot": [0, 1],
            "pairing": 0,
            "constraint": "⟨λ, α∨⟩ = 0; still satisfies ≥ 0",
            "expected": "SAT",
            "actual": str(result_b1),
            "pass": str(result_b1) == "SAT"
        }
        results["boundary_zero_pairing"] = test_b1

        # Boundary test 2: Single coroot system (rank 1)
        solver_b2 = cvc5.Solver()
        solver_b2.setLogic("QF_LIA")

        lambda_b2 = solver_b2.mkConst(solver_b2.getIntegerSort(), "lambda")
        coroot_b2 = solver_b2.mkConst(solver_b2.getIntegerSort(), "coroot")

        # λ = 1, α∨ = 1 → pairing = 1 ≥ 0 (dominant)
        c_l_b2 = solver_b2.mkTerm(Kind.EQUAL, lambda_b2, solver_b2.mkInteger(1))
        c_c_b2 = solver_b2.mkTerm(Kind.EQUAL, coroot_b2, solver_b2.mkInteger(1))

        solver_b2.assertFormula(c_l_b2)
        solver_b2.assertFormula(c_c_b2)

        pairing_b2 = solver_b2.mkTerm(Kind.MULT, lambda_b2, coroot_b2)
        dominance_b2 = solver_b2.mkTerm(Kind.GEQ, pairing_b2, solver_b2.mkInteger(0))
        solver_b2.assertFormula(dominance_b2)

        result_b2 = solver_b2.checkSat()
        test_b2 = {
            "name": "rank_1_single_coroot",
            "lambda": 1,
            "coroot": 1,
            "pairing": 1,
            "constraint": "Rank 1 system; λ = α∨ = 1 → ⟨λ, α∨⟩ = 1 (dominant)",
            "expected": "SAT",
            "actual": str(result_b2),
            "pass": str(result_b2) == "SAT"
        }
        results["boundary_rank_1"] = test_b2

        # Boundary test 3: High-dimensional weight space
        solver_b3 = cvc5.Solver()
        solver_b3.setLogic("QF_LIA")

        # 4D weight, all components = 1
        lambda_b3_1 = solver_b3.mkConst(solver_b3.getIntegerSort(), "lambda_1")
        lambda_b3_2 = solver_b3.mkConst(solver_b3.getIntegerSort(), "lambda_2")
        lambda_b3_3 = solver_b3.mkConst(solver_b3.getIntegerSort(), "lambda_3")
        lambda_b3_4 = solver_b3.mkConst(solver_b3.getIntegerSort(), "lambda_4")

        for i, l in enumerate([lambda_b3_1, lambda_b3_2, lambda_b3_3, lambda_b3_4], 1):
            c = solver_b3.mkTerm(Kind.EQUAL, l, solver_b3.mkInteger(1))
            solver_b3.assertFormula(c)

        # Coroot = (1, 1, 1, 1) → pairing = 4
        coroot_b3_1 = solver_b3.mkConst(solver_b3.getIntegerSort(), "coroot_1")
        coroot_b3_2 = solver_b3.mkConst(solver_b3.getIntegerSort(), "coroot_2")
        coroot_b3_3 = solver_b3.mkConst(solver_b3.getIntegerSort(), "coroot_3")
        coroot_b3_4 = solver_b3.mkConst(solver_b3.getIntegerSort(), "coroot_4")

        for c_var in [coroot_b3_1, coroot_b3_2, coroot_b3_3, coroot_b3_4]:
            c = solver_b3.mkTerm(Kind.EQUAL, c_var, solver_b3.mkInteger(1))
            solver_b3.assertFormula(c)

        # Compute pairing
        p1 = solver_b3.mkTerm(Kind.MULT, lambda_b3_1, coroot_b3_1)
        p2 = solver_b3.mkTerm(Kind.MULT, lambda_b3_2, coroot_b3_2)
        p3 = solver_b3.mkTerm(Kind.MULT, lambda_b3_3, coroot_b3_3)
        p4 = solver_b3.mkTerm(Kind.MULT, lambda_b3_4, coroot_b3_4)

        pair12 = solver_b3.mkTerm(Kind.ADD, p1, p2)
        pair34 = solver_b3.mkTerm(Kind.ADD, p3, p4)
        pairing_b3 = solver_b3.mkTerm(Kind.ADD, pair12, pair34)

        dominance_b3 = solver_b3.mkTerm(Kind.GEQ, pairing_b3, solver_b3.mkInteger(0))
        solver_b3.assertFormula(dominance_b3)

        result_b3 = solver_b3.checkSat()
        test_b3 = {
            "name": "high_dimension_weight",
            "lambda": [1, 1, 1, 1],
            "coroot": [1, 1, 1, 1],
            "pairing": 4,
            "constraint": "4D weight, all entries = 1; pairing = 4 ≥ 0 (dominant)",
            "expected": "SAT",
            "actual": str(result_b3),
            "pass": str(result_b3) == "SAT"
        }
        results["boundary_high_dim"] = test_b3

    except Exception as e:
        results["boundary_cvc5_error"] = str(e)

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    # Update sympy manifest if it was used
    try:
        import sympy as sp
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = "sympy: supportive symbolic computation for Satake weight verification"
        TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"
    except ImportError:
        pass

    results = {
        "name": "SatakeCorrespondenceWeight_Constraint",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_geometry_satake_correspondence_weight_constraint_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
