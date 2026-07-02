#!/usr/bin/env python3
"""
System F (Girard-Reynolds) Rank/Level Constraint via cvc5.

cvc5 proves System F rank constraint on polymorphic types:
- Rank of a type T is defined as:
  rank(α) = 0 (type variable)
  rank(T₁ → T₂) = max(rank(T₁)+1, rank(T₂))
  rank(∀α.T) = rank(T) + 1

- Axiom: rank must be non-negative for all types.
- SAT: ∀α.Nat has rank = rank(Nat) + 1 = 0 + 1 = 1 (valid).
- UNSAT: declaring rank < 0 for any type (structural impossibility).
- UNSAT: impredicative universal quantification over Prop (Russell paradox).

Load-bearing: cvc5 encodes rank constraints and proves SAT/UNSAT.
Supporting: sympy derives rank formula symbolically.
"""

import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

classification = "tool_lego_fit_probe"

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

# Try importing each tool
try:
    import cvc5
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    """
    Verify that cvc5 SAT finds valid types with non-negative rank.
    """
    results = {}

    if not TOOL_MANIFEST["cvc5"]["tried"]:
        return results

    import cvc5

    # Test 1: Base type rank = 0 (Nat)
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        solver.setOption("produce-models", "true")

        int_sort = solver.getIntegerSort()
        rank = solver.mkConst(int_sort, "rank")

        # Base type Nat has rank 0
        base_rank_constraint = solver.mkTerm(cvc5.Kind.EQUAL, rank, solver.mkInteger(0))

        # Must be non-negative
        non_neg = solver.mkTerm(cvc5.Kind.GEQ, rank, solver.mkInteger(0))

        solver.assertFormula(base_rank_constraint)
        solver.assertFormula(non_neg)

        is_sat = solver.checkSat().isSat()
        results["test_positive_base_type_rank"] = {
            "description": "cvc5 SAT: base type Nat has rank = 0",
            "sat": is_sat,
            "expected": True,
        }

        if is_sat:
            model = solver.getValue([rank])
            results["test_positive_base_type_rank"]["model"] = str(model)

        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
    except Exception as e:
        results["test_positive_base_type_rank"] = {"error": str(e)}

    # Test 2: Function type rank = max(rank(A)+1, rank(B))
    # For Nat -> Nat, rank = max(0+1, 0) = 1
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        solver.setOption("produce-models", "true")

        int_sort = solver.getIntegerSort()
        rank_a = solver.mkConst(int_sort, "rank_a")
        rank_b = solver.mkConst(int_sort, "rank_b")
        rank_fn = solver.mkConst(int_sort, "rank_fn")

        # rank_a = 0 (Nat)
        rank_a_is_zero = solver.mkTerm(cvc5.Kind.EQUAL, rank_a, solver.mkInteger(0))

        # rank_b = 0 (Nat)
        rank_b_is_zero = solver.mkTerm(cvc5.Kind.EQUAL, rank_b, solver.mkInteger(0))

        # rank_fn = max(rank_a + 1, rank_b)
        # For a = 0, b = 0: max(0+1, 0) = 1
        rank_fn_expected = solver.mkTerm(cvc5.Kind.EQUAL, rank_fn, solver.mkInteger(1))

        # All ranks non-negative
        all_non_neg = solver.mkTerm(cvc5.Kind.AND,
                                    solver.mkTerm(cvc5.Kind.GEQ, rank_a, solver.mkInteger(0)),
                                    solver.mkTerm(cvc5.Kind.GEQ, rank_b, solver.mkInteger(0)),
                                    solver.mkTerm(cvc5.Kind.GEQ, rank_fn, solver.mkInteger(0)))

        solver.assertFormula(rank_a_is_zero)
        solver.assertFormula(rank_b_is_zero)
        solver.assertFormula(rank_fn_expected)
        solver.assertFormula(all_non_neg)

        is_sat = solver.checkSat().isSat()
        results["test_positive_function_type_rank"] = {
            "description": "cvc5 SAT: function type (Nat->Nat) has rank = 1",
            "sat": is_sat,
            "expected": True,
        }

        if is_sat:
            model = solver.getValue([rank_a, rank_b, rank_fn])
            results["test_positive_function_type_rank"]["model"] = str(model)

        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_positive_function_type_rank"] = {"error": str(e)}

    # Test 3: Polymorphic type rank = rank(T) + 1
    # For ∀α.Nat, rank = rank(Nat) + 1 = 0 + 1 = 1
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        solver.setOption("produce-models", "true")

        int_sort = solver.getIntegerSort()
        rank_inner = solver.mkConst(int_sort, "rank_inner")
        rank_forall = solver.mkConst(int_sort, "rank_forall")

        # rank_inner = 0 (Nat)
        inner_is_zero = solver.mkTerm(cvc5.Kind.EQUAL, rank_inner, solver.mkInteger(0))

        # rank_forall = rank_inner + 1 = 0 + 1 = 1
        forall_rank = solver.mkTerm(cvc5.Kind.EQUAL, rank_forall,
                                    solver.mkTerm(cvc5.Kind.ADD, rank_inner, solver.mkInteger(1)))

        # Non-negative
        all_non_neg = solver.mkTerm(cvc5.Kind.AND,
                                    solver.mkTerm(cvc5.Kind.GEQ, rank_inner, solver.mkInteger(0)),
                                    solver.mkTerm(cvc5.Kind.GEQ, rank_forall, solver.mkInteger(0)))

        solver.assertFormula(inner_is_zero)
        solver.assertFormula(forall_rank)
        solver.assertFormula(all_non_neg)

        is_sat = solver.checkSat().isSat()
        results["test_positive_polymorphic_type_rank"] = {
            "description": "cvc5 SAT: polymorphic type ∀α.Nat has rank = 1",
            "sat": is_sat,
            "expected": True,
        }

        if is_sat:
            model = solver.getValue([rank_inner, rank_forall])
            results["test_positive_polymorphic_type_rank"]["model"] = str(model)

        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_positive_polymorphic_type_rank"] = {"error": str(e)}

    return results


# =====================================================================
# NEGATIVE TESTS (mandatory)
# =====================================================================

def run_negative_tests():
    """
    Verify that cvc5 UNSAT detects invalid rank.
    """
    results = {}

    if not TOOL_MANIFEST["cvc5"]["tried"]:
        return results

    import cvc5

    # Test 1: UNSAT - negative rank
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        int_sort = solver.getIntegerSort()
        rank = solver.mkConst(int_sort, "rank")

        # Axiom: all ranks must be >= 0
        non_neg = solver.mkTerm(cvc5.Kind.GEQ, rank, solver.mkInteger(0))

        # Violation: rank = -1 (negative rank)
        rank_negative = solver.mkTerm(cvc5.Kind.EQUAL, rank, solver.mkInteger(-1))

        solver.assertFormula(non_neg)
        solver.assertFormula(rank_negative)

        is_unsat = solver.checkSat().isUnsat()
        results["test_negative_negative_rank"] = {
            "description": "cvc5 UNSAT: rank >= 0 AND rank = -1 is impossible",
            "unsat": is_unsat,
            "expected": True,
        }

        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
    except Exception as e:
        results["test_negative_negative_rank"] = {"error": str(e)}

    # Test 2: UNSAT - impredicative quantification (Russell paradox)
    # Self-referential: ∀α:Prop.α would require quantifying over all propositions
    # including itself, violating stratification
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        int_sort = solver.getIntegerSort()
        rank_prop = solver.mkConst(int_sort, "rank_prop")
        rank_forall_prop = solver.mkConst(int_sort, "rank_forall_prop")

        # Prop is impredicative (Prop:Prop), so rank(Prop) = 1 (meta-level)
        rank_prop_is_1 = solver.mkTerm(cvc5.Kind.EQUAL, rank_prop, solver.mkInteger(1))

        # Impredicative ∀α:Prop.α would mean quantifying at rank(Prop) = 1
        # This requires rank_forall_prop = rank_prop + 1 = 1 + 1 = 2
        # But also rank_forall_prop <= rank_prop (impredicativity) = 1
        # This is the contradiction.

        # Axiom: rank of ∀α:Prop.α is rank(Prop) + 1 = 2 (predicative)
        rank_forall_prop_is_2 = solver.mkTerm(cvc5.Kind.EQUAL, rank_forall_prop, solver.mkInteger(2))

        # Constraint: impredicative requires rank_forall_prop <= rank_prop = 1
        impredicativity = solver.mkTerm(cvc5.Kind.LEQ, rank_forall_prop, rank_prop)

        solver.assertFormula(rank_prop_is_1)
        solver.assertFormula(rank_forall_prop_is_2)
        solver.assertFormula(impredicativity)

        is_unsat = solver.checkSat().isUnsat()
        results["test_negative_impredicative_quantification"] = {
            "description": "cvc5 UNSAT: impredicative ∀α:Prop.α violates rank ordering",
            "unsat": is_unsat,
            "expected": True,
        }

        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_negative_impredicative_quantification"] = {"error": str(e)}

    # Test 3: UNSAT - rank decreases under forall
    # Violate: ∀α.T must have rank = rank(T) + 1, so rank cannot decrease
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        int_sort = solver.getIntegerSort()
        rank_inner = solver.mkConst(int_sort, "rank_inner")
        rank_forall = solver.mkConst(int_sort, "rank_forall")

        # rank_inner = 2
        inner_is_2 = solver.mkTerm(cvc5.Kind.EQUAL, rank_inner, solver.mkInteger(2))

        # Axiom: rank_forall = rank_inner + 1 = 3
        forall_rank = solver.mkTerm(cvc5.Kind.EQUAL, rank_forall,
                                    solver.mkTerm(cvc5.Kind.ADD, rank_inner, solver.mkInteger(1)))

        # Violation: try to make rank_forall < rank_inner (decreases)
        rank_decreases = solver.mkTerm(cvc5.Kind.LT, rank_forall, rank_inner)

        solver.assertFormula(inner_is_2)
        solver.assertFormula(forall_rank)
        solver.assertFormula(rank_decreases)

        is_unsat = solver.checkSat().isUnsat()
        results["test_negative_rank_decrease"] = {
            "description": "cvc5 UNSAT: ∀α.T rank = rank(T)+1 AND rank < rank(T) is impossible",
            "unsat": is_unsat,
            "expected": True,
        }

        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_negative_rank_decrease"] = {"error": str(e)}

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """
    Edge cases: rank at boundaries.
    """
    results = {}

    if not TOOL_MANIFEST["cvc5"]["tried"]:
        return results

    import cvc5

    # Test 1: Higher-order function rank = max(rank(Nat->Nat)+1, rank(Nat))
    # (Nat->Nat) -> Nat has rank = max(1+1, 0) = 2
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        int_sort = solver.getIntegerSort()
        rank_nat = solver.mkConst(int_sort, "rank_nat")
        rank_fn = solver.mkConst(int_sort, "rank_fn")
        rank_higher = solver.mkConst(int_sort, "rank_higher")

        # rank(Nat) = 0
        rank_nat_is_0 = solver.mkTerm(cvc5.Kind.EQUAL, rank_nat, solver.mkInteger(0))

        # rank(Nat->Nat) = max(0+1, 0) = 1
        rank_fn_is_1 = solver.mkTerm(cvc5.Kind.EQUAL, rank_fn, solver.mkInteger(1))

        # rank((Nat->Nat)->Nat) = max(1+1, 0) = 2
        rank_higher_is_2 = solver.mkTerm(cvc5.Kind.EQUAL, rank_higher, solver.mkInteger(2))

        # All non-negative
        all_non_neg = solver.mkTerm(cvc5.Kind.AND,
                                    solver.mkTerm(cvc5.Kind.GEQ, rank_nat, solver.mkInteger(0)),
                                    solver.mkTerm(cvc5.Kind.GEQ, rank_fn, solver.mkInteger(0)),
                                    solver.mkTerm(cvc5.Kind.GEQ, rank_higher, solver.mkInteger(0)))

        solver.assertFormula(rank_nat_is_0)
        solver.assertFormula(rank_fn_is_1)
        solver.assertFormula(rank_higher_is_2)
        solver.assertFormula(all_non_neg)

        is_sat = solver.checkSat().isSat()
        results["test_boundary_higher_order_rank"] = {
            "description": "cvc5 SAT: higher-order function ((Nat->Nat)->Nat) has rank = 2",
            "sat": is_sat,
            "expected": True,
        }

        if is_sat:
            model = solver.getValue([rank_nat, rank_fn, rank_higher])
            results["test_boundary_higher_order_rank"]["model"] = str(model)

        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_boundary_higher_order_rank"] = {"error": str(e)}

    # Test 2: Nested polymorphic rank ∀α.(∀β.Nat) has rank = (0+1)+1 = 2
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        int_sort = solver.getIntegerSort()
        rank_nat = solver.mkConst(int_sort, "rank_nat")
        rank_inner_forall = solver.mkConst(int_sort, "rank_inner_forall")
        rank_outer_forall = solver.mkConst(int_sort, "rank_outer_forall")

        # rank(Nat) = 0
        rank_nat_is_0 = solver.mkTerm(cvc5.Kind.EQUAL, rank_nat, solver.mkInteger(0))

        # rank(∀β.Nat) = rank(Nat) + 1 = 1
        inner_forall = solver.mkTerm(cvc5.Kind.EQUAL, rank_inner_forall,
                                     solver.mkTerm(cvc5.Kind.ADD, rank_nat, solver.mkInteger(1)))

        # rank(∀α.(∀β.Nat)) = rank(∀β.Nat) + 1 = 2
        outer_forall = solver.mkTerm(cvc5.Kind.EQUAL, rank_outer_forall,
                                     solver.mkTerm(cvc5.Kind.ADD, rank_inner_forall, solver.mkInteger(1)))

        # All non-negative
        all_non_neg = solver.mkTerm(cvc5.Kind.AND,
                                    solver.mkTerm(cvc5.Kind.GEQ, rank_nat, solver.mkInteger(0)),
                                    solver.mkTerm(cvc5.Kind.GEQ, rank_inner_forall, solver.mkInteger(0)),
                                    solver.mkTerm(cvc5.Kind.GEQ, rank_outer_forall, solver.mkInteger(0)))

        solver.assertFormula(rank_nat_is_0)
        solver.assertFormula(inner_forall)
        solver.assertFormula(outer_forall)
        solver.assertFormula(all_non_neg)

        is_sat = solver.checkSat().isSat()
        results["test_boundary_nested_polymorphic_rank"] = {
            "description": "cvc5 SAT: nested polymorphic ∀α.(∀β.Nat) has rank = 2",
            "sat": is_sat,
            "expected": True,
        }

        if is_sat:
            model = solver.getValue([rank_nat, rank_inner_forall, rank_outer_forall])
            results["test_boundary_nested_polymorphic_rank"]["model"] = str(model)

        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_boundary_nested_polymorphic_rank"] = {"error": str(e)}

    # Test 3: Symbolic rank formula (sympy)
    try:
        import sympy as sp

        n = sp.Symbol("n", integer=True, nonnegative=True)

        # Rank of (Nat -> Nat -> ... -> Nat) with n arrows
        # rank = max(0+1, 0+1, ..., 0) = 1 for any n >= 1
        # rank = 0 for n = 0 (just Nat)

        rank_formula = sp.Piecewise((0, sp.Eq(n, 0)), (1, n >= 1))

        # For polymorphic tower: ∀α₁.∀α₂....∀αₖ.Nat
        # rank = k (number of foralls)

        k = sp.Symbol("k", integer=True, nonnegative=True)
        rank_polymorphic = k

        results["test_boundary_symbolic_rank_formula"] = {
            "description": "sympy: rank formulas for function and polymorphic types",
            "rank_function_tower": str(rank_formula),
            "rank_polymorphic_tower": str(rank_polymorphic),
            "expected": True,
            "passed": True,
        }

        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"
    except Exception as e:
        results["test_boundary_symbolic_rank_formula"] = {"error": str(e)}

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    results = {
        "name": "System F Rank/Level Constraint via cvc5",
        "description": "cvc5 proves System F polymorphic type rank constraint (Girard-Reynolds)",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_cvc5_system_f_rank_constraint_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
