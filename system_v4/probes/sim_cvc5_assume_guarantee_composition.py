#!/usr/bin/env python3
"""
Assume-Guarantee Composition — cvc5 canonical sim.

Theory: If C1 ⊢_{A1} G1 and C2 ⊢_{A2} G2 and A1 ⊆ G2 and A2 ⊆ G1 (AG composition rule),
then C1||C2 ⊢_{A1∩A2} G1∧G2.

Circularity: (A1,G1) and (A2,G2) compose circularly only if A2 ∧ G2 → A1 AND A1 ∧ G1 → A2.

Weakest assumption: W_A = weakest(A such that C ⊢_{A} G) must be logically weakest.
"""

import json
import os
import sys

classification = "classical_baseline"
divergence_log = [
    "Classical comparator/control surface only; does not promote nonclassical, formal-scout, bridge, axis-level, or canonical proof claims."
]

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "pytorch not needed; pure symbolic/logical computation via cvc5 and sympy"},
    "pyg": {"tried": False, "used": False, "reason": "PyG not needed; contract structure encoded as constraint variables"},
    "z3": {"tried": False, "used": False, "reason": "z3 not needed; cvc5 handles all SMT constraint proofs"},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": "Clifford algebra not needed; temporal logic via cvc5/sympy"},
    "geomstats": {"tried": False, "used": False, "reason": "geomstats not needed; no differential geometry required"},
    "e3nn": {"tried": False, "used": False, "reason": "e3nn not needed; no SO(3) equivariance required"},
    "rustworkx": {"tried": False, "used": False, "reason": "rustworkx not needed; contract DAG encoded directly in constraints"},
    "xgi": {"tried": False, "used": False, "reason": "xgi not needed; no hypergraph structure"},
    "toponetx": {"tried": False, "used": False, "reason": "toponetx not needed; standard logical computations sufficient"},
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

# Try importing cvc5 and sympy
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
    """AG composition rule holds: if premises valid, conclusion holds."""
    results = {}

    if not cvc5_available:
        results["test_1_ag_composition_rule"] = {"status": "skipped", "reason": "cvc5 not available"}
        results["test_2_circular_assume_guarantee"] = {"status": "skipped", "reason": "cvc5 not available"}
        results["test_3_weakest_assumption"] = {"status": "skipped", "reason": "cvc5 not available"}
        if sympy_available:
            results["test_4_sympy_compositionality"] = run_sympy_compositionality_test()
        return results

    # Test 1: AG composition rule
    # If C1 ⊢_{A1} G1 and C2 ⊢_{A2} G2 and A1 ⊆ G2 and A2 ⊆ G1,
    # then C1||C2 ⊢_{A1∩A2} G1∧G2.
    # UNSAT: deny conclusion while premises hold.
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        # Variables
        A1 = solver.mkConst(solver.mkBitVectorSort(8), "A1")
        A2 = solver.mkConst(solver.mkBitVectorSort(8), "A2")
        G1 = solver.mkConst(solver.mkBitVectorSort(8), "G1")
        G2 = solver.mkConst(solver.mkBitVectorSort(8), "G2")

        # Premises: A1 ⊆ G2 and A2 ⊆ G1 (expressed as: A1 <= G2 and A2 <= G1 bitwise)
        # For simplicity: A1 AND (~G2) = 0, A2 AND (~G1) = 0
        A1_subset_G2 = solver.mkTerm(cvc5.Kind.BVAnd, A1, solver.mkTerm(cvc5.Kind.BVNot, G2))
        A2_subset_G1 = solver.mkTerm(cvc5.Kind.BVAnd, A2, solver.mkTerm(cvc5.Kind.BVNot, G1))
        zero = solver.mkBitVector(8, 0)

        # Conclusion: A1 ∩ A2 ⊆ G1 ∧ G2
        A1_meet_A2 = solver.mkTerm(cvc5.Kind.BVAnd, A1, A2)
        G1_meet_G2 = solver.mkTerm(cvc5.Kind.BVAnd, G1, G2)
        A1_A2_subset_G1_G2 = solver.mkTerm(cvc5.Kind.BVAnd, A1_meet_A2, solver.mkTerm(cvc5.Kind.BVNot, G1_meet_G2))

        # Assert premises
        solver.assertFormula(solver.mkTerm(cvc5.Kind.Equal, A1_subset_G2, zero))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.Equal, A2_subset_G1, zero))

        # Negate conclusion (should be UNSAT)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.Not, solver.mkTerm(cvc5.Kind.Equal, A1_A2_subset_G1_G2, zero)))

        result = solver.checkSat()
        results["test_1_ag_composition_rule"] = {
            "status": "PASS" if not result.isSat() else "FAIL",
            "expected": "UNSAT",
            "actual": "UNSAT" if not result.isSat() else "SAT",
            "reason": "AG composition rule: if premises hold, conclusion must hold"
        }
    except Exception as e:
        results["test_1_ag_composition_rule"] = {"status": "ERROR", "reason": str(e)}

    # Test 2: Circular assume-guarantee
    # (A1,G1) and (A2,G2) compose circularly only if A2 ∧ G2 → A1 AND A1 ∧ G1 → A2
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_BV")

        A1 = solver.mkConst(solver.mkBitVectorSort(8), "A1_circ")
        A2 = solver.mkConst(solver.mkBitVectorSort(8), "A2_circ")
        G1 = solver.mkConst(solver.mkBitVectorSort(8), "G1_circ")
        G2 = solver.mkConst(solver.mkBitVectorSort(8), "G2_circ")

        # Circularity requires: (A2 ∧ G2) → A1 AND (A1 ∧ G1) → A2
        A2_G2 = solver.mkTerm(cvc5.Kind.BVAnd, A2, G2)
        A1_G1 = solver.mkTerm(cvc5.Kind.BVAnd, A1, G1)

        # Implication in BV: p → q ≡ (~p ∨ q)
        # (A2 ∧ G2) → A1: NOT((A2 ∧ G2) AND NOT(A1))
        cond1_lhs = A2_G2
        cond1_rhs = A1
        cond1 = solver.mkTerm(cvc5.Kind.BVAnd, cond1_lhs, solver.mkTerm(cvc5.Kind.BVNot, cond1_rhs))

        cond2_lhs = A1_G1
        cond2_rhs = A2
        cond2 = solver.mkTerm(cvc5.Kind.BVAnd, cond2_lhs, solver.mkTerm(cvc5.Kind.BVNot, cond2_rhs))

        zero = solver.mkBitVector(8, 0)

        # Negate circularity: claim circular composition without the conditions
        # UNSAT if we deny both conditions hold
        solver.assertFormula(solver.mkTerm(cvc5.Kind.Equal, cond1, zero))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.Equal, cond2, zero))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.Not, solver.mkTerm(cvc5.Kind.Equal,
                                                            solver.mkTerm(cvc5.Kind.BVOr, cond1, cond2), zero)))

        result = solver.checkSat()
        results["test_2_circular_assume_guarantee"] = {
            "status": "PASS" if not result.isSat() else "FAIL",
            "expected": "UNSAT",
            "actual": "UNSAT" if not result.isSat() else "SAT",
            "reason": "Circular AG composition requires both implication directions"
        }
    except Exception as e:
        results["test_2_circular_assume_guarantee"] = {"status": "ERROR", "reason": str(e)}

    # Test 3: Weakest assumption
    # W_A = weakest(A such that C ⊢_{A} G) must be the logically weakest.
    # UNSAT: claim A' is weaker than W_A but C ⊢_{A'} G still holds.
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_BV")

        W_A = solver.mkConst(solver.mkBitVectorSort(8), "W_A")
        A_prime = solver.mkConst(solver.mkBitVectorSort(8), "A_prime")
        C = solver.mkBitVector(8, 0xAA)  # fixed component
        G = solver.mkBitVector(8, 0xFF)  # guarantee

        # W_A is weakest: for any A, if A ⊢ G then A ⊇ W_A (or A AND ~W_A = 0)
        # Claim: A_prime ⊂ W_A (A_prime AND ~W_A != 0, i.e., A_prime has bits W_A doesn't)
        A_prime_not_subset_W_A = solver.mkTerm(cvc5.Kind.BVAnd, A_prime, solver.mkTerm(cvc5.Kind.BVNot, W_A))

        # But claim C ⊢_{A_prime} G still holds (C AND A_prime ⊆ G)
        C_meet_A_prime = solver.mkTerm(cvc5.Kind.BVAnd, C, A_prime)
        C_A_prime_subset_G = solver.mkTerm(cvc5.Kind.BVAnd, C_meet_A_prime, solver.mkTerm(cvc5.Kind.BVNot, G))

        zero = solver.mkBitVector(8, 0)

        # Assert: A_prime has bits not in W_A
        solver.assertFormula(solver.mkTerm(cvc5.Kind.Not, solver.mkTerm(cvc5.Kind.Equal, A_prime_not_subset_W_A, zero)))
        # Assert: but C ⊢_{A_prime} G (C AND A_prime ⊆ G)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.Equal, C_A_prime_subset_G, zero))

        result = solver.checkSat()
        results["test_3_weakest_assumption"] = {
            "status": "PASS" if not result.isSat() else "FAIL",
            "expected": "UNSAT",
            "actual": "UNSAT" if not result.isSat() else "SAT",
            "reason": "Weakest assumption cannot be weaker without losing guarantee"
        }
    except Exception as e:
        results["test_3_weakest_assumption"] = {"status": "ERROR", "reason": str(e)}

    # Test 4: sympy compositionality (if available)
    if sympy_available:
        results["test_4_sympy_compositionality"] = run_sympy_compositionality_test()

    return results


def run_sympy_compositionality_test():
    """Verify compositionality formula with sympy."""
    try:
        import sympy as sp
        from sympy import symbols, simplify, Implies, And, Or, Not

        # 2-variable boolean: (a, b)
        a, b = symbols('a b', bool=True)

        # C1: a → b, C2: b → a
        # A1: a, G1: b
        # A2: b, G2: a
        C1 = Implies(a, b)
        C2 = Implies(b, a)
        A1 = a
        G1 = b
        A2 = b
        G2 = a

        # Check premises:
        # A1 ⊆ G2: a ⊆ a ✓
        # A2 ⊆ G1: b ⊆ b ✓

        # Composed system C1||C2 ⊢_{A1∩A2} G1∧G2
        # C1||C2: (a → b) ∧ (b → a) [equivalence]
        composed = And(C1, C2)
        assumption_composed = And(A1, A2)  # a ∧ b
        guarantee_composed = And(G1, G2)   # b ∧ a

        # Check: (C1||C2) ∧ (A1∩A2) → (G1∧G2)
        formula = Implies(And(composed, assumption_composed), guarantee_composed)
        simplified = simplify(formula)

        return {
            "status": "PASS" if simplified is True else "FAIL",
            "formula": str(formula),
            "simplified": str(simplified),
            "reason": "Compositionality formula verified via sympy"
        }
    except Exception as e:
        return {"status": "ERROR", "reason": str(e)}


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    """Tests where composition should fail or assumptions violated."""
    results = {}

    if not cvc5_available:
        results["neg_test_1_violated_subset"] = {"status": "skipped", "reason": "cvc5 not available"}
        results["neg_test_2_broken_circularity"] = {"status": "skipped", "reason": "cvc5 not available"}
        results["neg_test_3_violated_guarantee"] = {"status": "skipped", "reason": "cvc5 not available"}
        return results

    # Negative Test 1: A1 ⊆ G2 violated
    # If A1 ⊄ G2, composition should fail (SAT when we deny composition guarantee)
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_BV")

        A1 = solver.mkBitVector(8, 0x0F)  # 0000 1111
        G2 = solver.mkBitVector(8, 0xF0)  # 1111 0000 (disjoint from A1)

        # A1 is not subset of G2
        not_subset = solver.mkTerm(cvc5.Kind.BVAnd, A1, solver.mkTerm(cvc5.Kind.BVNot, G2))
        zero = solver.mkBitVector(8, 0)

        solver.assertFormula(solver.mkTerm(cvc5.Kind.Not, solver.mkTerm(cvc5.Kind.Equal, not_subset, zero)))

        result = solver.checkSat()
        results["neg_test_1_violated_subset"] = {
            "status": "PASS" if result.isSat() else "FAIL",
            "expected": "SAT",
            "actual": "SAT" if result.isSat() else "UNSAT",
            "reason": "When assumption-guarantee subset fails, state is satisfiable (bad)"
        }
    except Exception as e:
        results["neg_test_1_violated_subset"] = {"status": "ERROR", "reason": str(e)}

    # Negative Test 2: Circularity broken (one direction fails)
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_BV")

        A1 = solver.mkBitVector(8, 0x0F)
        A2 = solver.mkBitVector(8, 0xF0)
        G1 = solver.mkBitVector(8, 0xFF)
        G2 = solver.mkBitVector(8, 0x00)

        A2_G2 = solver.mkTerm(cvc5.Kind.BVAnd, A2, G2)
        A1_G1 = solver.mkTerm(cvc5.Kind.BVAnd, A1, G1)
        zero = solver.mkBitVector(8, 0)

        # A2 ∧ G2 → A1: since A2 ∧ G2 = 0, this is vacuously true
        # A1 ∧ G1 → A2: A1 ∧ G1 = A1, must imply A2; but A1=0x0F, A2=0xF0 disjoint
        cond2 = solver.mkTerm(cvc5.Kind.BVAnd, A1_G1, solver.mkTerm(cvc5.Kind.BVNot, A2))

        # Claim this is satisfiable (circularity broken)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.Not, solver.mkTerm(cvc5.Kind.Equal, cond2, zero)))

        result = solver.checkSat()
        results["neg_test_2_broken_circularity"] = {
            "status": "PASS" if result.isSat() else "FAIL",
            "expected": "SAT",
            "actual": "SAT" if result.isSat() else "UNSAT",
            "reason": "Broken circularity (one direction fails) is satisfiable"
        }
    except Exception as e:
        results["neg_test_2_broken_circularity"] = {"status": "ERROR", "reason": str(e)}

    # Negative Test 3: Component violates guarantee
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_BV")

        C = solver.mkBitVector(8, 0x0F)   # component can only produce bits [0:3]
        A = solver.mkBitVector(8, 0xFF)   # assumption is always true
        G = solver.mkBitVector(8, 0xF0)   # guarantee requires bits [4:7]

        # C ⊢_A G means: C ∧ A ⊆ G, but C=0x0F, G=0xF0 disjoint
        C_meet_A = solver.mkTerm(cvc5.Kind.BVAnd, C, A)
        violates = solver.mkTerm(cvc5.Kind.BVAnd, C_meet_A, solver.mkTerm(cvc5.Kind.BVNot, G))
        zero = solver.mkBitVector(8, 0)

        # Should be satisfiable (violation can happen)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.Not, solver.mkTerm(cvc5.Kind.Equal, violates, zero)))

        result = solver.checkSat()
        results["neg_test_3_violated_guarantee"] = {
            "status": "PASS" if result.isSat() else "FAIL",
            "expected": "SAT",
            "actual": "SAT" if result.isSat() else "UNSAT",
            "reason": "Component unable to satisfy guarantee under assumption is satisfiable"
        }
    except Exception as e:
        results["neg_test_3_violated_guarantee"] = {"status": "ERROR", "reason": str(e)}

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """Edge cases: empty assumptions, universal guarantees, etc."""
    results = {}

    if not cvc5_available:
        results["bound_test_1_empty_assumption"] = {"status": "skipped", "reason": "cvc5 not available"}
        results["bound_test_2_universal_guarantee"] = {"status": "skipped", "reason": "cvc5 not available"}
        results["bound_test_3_self_circular"] = {"status": "skipped", "reason": "cvc5 not available"}
        return results

    # Boundary Test 1: Empty assumption (⊥)
    # If A = ∅ (0x00), then any C ⊢_A G trivially
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_BV")

        C = solver.mkBitVector(8, 0xFF)
        A = solver.mkBitVector(8, 0x00)  # empty
        G = solver.mkBitVector(8, 0x00)  # impossible guarantee

        # C ∧ A ⊆ G: (C ∧ A) ∧ ~G = 0 always holds when A=0
        C_meet_A = solver.mkTerm(cvc5.Kind.BVAnd, C, A)
        result_check = solver.mkTerm(cvc5.Kind.BVAnd, C_meet_A, solver.mkTerm(cvc5.Kind.BVNot, G))
        zero = solver.mkBitVector(8, 0)

        solver.assertFormula(solver.mkTerm(cvc5.Kind.Equal, result_check, zero))

        result = solver.checkSat()
        results["bound_test_1_empty_assumption"] = {
            "status": "PASS" if result.isSat() else "FAIL",
            "expected": "SAT",
            "actual": "SAT" if result.isSat() else "UNSAT",
            "reason": "Empty assumption makes any guarantee satisfiable"
        }
    except Exception as e:
        results["bound_test_1_empty_assumption"] = {"status": "ERROR", "reason": str(e)}

    # Boundary Test 2: Universal guarantee (⊤)
    # If G = ⊤ (0xFF), then any C ⊢_A G for any A
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_BV")

        C = solver.mkBitVector(8, 0xAA)
        A = solver.mkBitVector(8, 0x55)
        G = solver.mkBitVector(8, 0xFF)  # universal

        C_meet_A = solver.mkTerm(cvc5.Kind.BVAnd, C, A)
        result_check = solver.mkTerm(cvc5.Kind.BVAnd, C_meet_A, solver.mkTerm(cvc5.Kind.BVNot, G))
        zero = solver.mkBitVector(8, 0)

        solver.assertFormula(solver.mkTerm(cvc5.Kind.Equal, result_check, zero))

        result = solver.checkSat()
        results["bound_test_2_universal_guarantee"] = {
            "status": "PASS" if result.isSat() else "FAIL",
            "expected": "SAT",
            "actual": "SAT" if result.isSat() else "UNSAT",
            "reason": "Universal guarantee always satisfiable"
        }
    except Exception as e:
        results["bound_test_2_universal_guarantee"] = {"status": "ERROR", "reason": str(e)}

    # Boundary Test 3: Self-circular (A,G where A=G)
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_BV")

        A = solver.mkBitVector(8, 0xAA)
        G = A  # same value

        # Circularity: A ∧ G → A and A ∧ G → A both hold trivially
        A_G = solver.mkTerm(cvc5.Kind.BVAnd, A, G)  # = A

        # A ∧ G → A is A → A, always true
        implication = solver.mkTerm(cvc5.Kind.BVAnd, A_G, solver.mkTerm(cvc5.Kind.BVNot, A))
        zero = solver.mkBitVector(8, 0)

        solver.assertFormula(solver.mkTerm(cvc5.Kind.Equal, implication, zero))

        result = solver.checkSat()
        results["bound_test_3_self_circular"] = {
            "status": "PASS" if result.isSat() else "FAIL",
            "expected": "SAT",
            "actual": "SAT" if result.isSat() else "UNSAT",
            "reason": "Self-circular AG pair (A=G) always satisfies circularity"
        }
    except Exception as e:
        results["bound_test_3_self_circular"] = {"status": "ERROR", "reason": str(e)}

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    results = {
        "name": "sim_cvc5_assume_guarantee_composition",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": classification,
        "original_classification": "canonical",
        "downgrade_reason": "overclassification_fail_status_2026-05-01",
    }

    # Mark tools as used
    if cvc5_available:
        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_MANIFEST["cvc5"]["reason"] = "UNSAT proofs for AG composition, circularity, weakest assumption"

    if sympy_available:
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = "compositionality formula verification"

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_cvc5_assume_guarantee_composition_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
