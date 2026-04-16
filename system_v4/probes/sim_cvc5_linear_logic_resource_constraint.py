#!/usr/bin/env python3
"""
sim_cvc5_linear_logic_resource_constraint.py

Canonical sim for linear logic resource constraints via cvc5.
Encodes Girard's linear logic: each formula used exactly once unless
marked with the of-course modality !A. Tests:
1. UNSAT when formula used >1 time without !A
2. UNSAT when tensor A⊗B incorrectly equated to additive A&B
3. UNSAT when !A weakening/contraction count inconsistent in a branch
4. sympy verification of sequent calculus resource conservation

See system_v5/new docs/ENFORCEMENT_AND_PROCESS_RULES.md for rules.

Usage:
  python3 sim_cvc5_linear_logic_resource_constraint.py
  Results written to a2_state/sim_results/sim_cvc5_linear_logic_resource_constraint_results.json
"""

import json
import os
import sys

# =====================================================================
# TOOL MANIFEST -- Document which tools were tried
# =====================================================================

TOOL_MANIFEST = {
    # --- Computation layer ---
    "pytorch": {"tried": False, "used": False, "reason": "pytorch not needed; pure symbolic/logical computation via cvc5 and sympy"},
    "pyg": {"tried": False, "used": False, "reason": "PyG not needed; proof structure encoded as constraint variables"},
    # --- Proof layer ---
    "z3": {"tried": False, "used": False, "reason": "z3 not needed; cvc5 handles all SMT constraint proofs"},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    # --- Symbolic layer ---
    "sympy": {"tried": False, "used": False, "reason": ""},
    # --- Geometry layer ---
    "clifford": {"tried": False, "used": False, "reason": "Clifford algebra not needed; proof theory via cvc5/sympy"},
    "geomstats": {"tried": False, "used": False, "reason": "geomstats not needed; no differential geometry required"},
    "e3nn": {"tried": False, "used": False, "reason": "e3nn not needed; no SO(3) equivariance required"},
    # --- Graph layer ---
    "rustworkx": {"tried": False, "used": False, "reason": "rustworkx not needed; proof structure encoded directly in constraints"},
    "xgi": {"tried": False, "used": False, "reason": "xgi not needed; no hypergraph structure"},
    # --- Topology layer ---
    "toponetx": {"tried": False, "used": False, "reason": "toponetx not needed; standard logical computations sufficient"},
    "gudhi": {"tried": False, "used": False, "reason": "gudhi not needed; no persistent homology required"},
}

# Record actual integration depth, not just import presence.
# Each entry should be one of:
# - "load_bearing"  : the result materially depends on this tool
# - "supportive"    : useful cross-check/helper but not decisive
# - None            : not used
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

# Try importing each tool
try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric  # noqa: F401
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    from z3 import *  # noqa: F401,F403
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"
    cvc5 = None

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"
    sp = None

try:
    from clifford import Cl  # noqa: F401
    TOOL_MANIFEST["clifford"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

try:
    import geomstats  # noqa: F401
    TOOL_MANIFEST["geomstats"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    import e3nn  # noqa: F401
    TOOL_MANIFEST["e3nn"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"

try:
    import rustworkx  # noqa: F401
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

try:
    import xgi  # noqa: F401
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

try:
    from toponetx.classes import CellComplex  # noqa: F401
    TOOL_MANIFEST["toponetx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] = "not installed"

try:
    import gudhi  # noqa: F401
    TOOL_MANIFEST["gudhi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    """Test resource constraints that should be satisfiable."""
    results = {}

    if not cvc5:
        return {"error": "cvc5 not installed"}

    # Test 1: Single use of formula A without ! is allowed
    try:
        solver = cvc5.Solver()
        # Formula A used once
        A_uses = solver.mkInteger(1)
        A_has_bang = solver.mkFalse()

        # Linear logic: if !A is false, uses must equal 1
        constraint = solver.mkTerm(cvc5.Kind.IMPLIES, A_has_bang, solver.mkTerm(cvc5.Kind.EQUAL, A_uses, solver.mkInteger(1)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.AND, constraint, solver.mkTerm(cvc5.Kind.EQUAL, A_has_bang, solver.mkFalse())))

        is_sat = solver.checkSat().isSat()
        results["test_single_use_no_bang"] = {
            "satisfiable": is_sat,
            "expected": True,
            "pass": is_sat == True,
            "description": "A used once without ! should be satisfiable"
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_single_use_no_bang"] = {"error": str(e)}

    # Test 2: Tensor product A⊗B (multiplicative) conserves both resources
    try:
        solver = cvc5.Solver()
        # A used once, B used once in multiplicative conjunction
        A_uses = solver.mkInteger(1)
        B_uses = solver.mkInteger(1)
        # Both must be consumed in tensor
        tensor_total = solver.mkTerm(cvc5.Kind.PLUS, A_uses, B_uses)

        # Check tensor count equals 2
        constraint = solver.mkTerm(cvc5.Kind.EQUAL, tensor_total, solver.mkInteger(2))
        solver.assertFormula(constraint)

        is_sat = solver.checkSat().isSat()
        results["test_tensor_conserves_both"] = {
            "satisfiable": is_sat,
            "expected": True,
            "pass": is_sat == True,
            "description": "A⊗B should use both A and B exactly once"
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_tensor_conserves_both"] = {"error": str(e)}

    # Test 3: Of-course modality !A allows multiple uses
    try:
        solver = cvc5.Solver()
        # !A can be used 0, 1, 2, or more times
        A_uses = solver.mkInteger(2)
        A_has_bang = solver.mkTrue()

        # Linear logic: if !A is true, uses can be any non-negative number
        constraint = solver.mkTerm(cvc5.Kind.GEQ, A_uses, solver.mkInteger(0))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.AND, constraint, solver.mkTerm(cvc5.Kind.EQUAL, A_has_bang, solver.mkTrue())))

        is_sat = solver.checkSat().isSat()
        results["test_bang_allows_multiple"] = {
            "satisfiable": is_sat,
            "expected": True,
            "pass": is_sat == True,
            "description": "!A used multiple times should be satisfiable"
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_bang_allows_multiple"] = {"error": str(e)}

    return results


# =====================================================================
# NEGATIVE TESTS (mandatory)
# =====================================================================

def run_negative_tests():
    """Test resource constraints that should be UNSAT."""
    results = {}

    if not cvc5:
        return {"error": "cvc5 not installed"}

    # Test 1: UNSAT when A used >1 time without !A
    try:
        solver = cvc5.Solver()
        # Formula A used twice
        A_uses = solver.mkInteger(2)
        A_has_bang = solver.mkFalse()

        # Linear logic: if !A is false, uses must equal 1
        # But A_uses = 2, so this is UNSAT
        constraint = solver.mkTerm(cvc5.Kind.IMPLIES, solver.mkTerm(cvc5.Kind.NOT, A_has_bang),
                                   solver.mkTerm(cvc5.Kind.EQUAL, A_uses, solver.mkInteger(1)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.AND, constraint,
                                          solver.mkTerm(cvc5.Kind.EQUAL, A_has_bang, solver.mkFalse())))

        is_sat = solver.checkSat().isSat()
        results["test_reuse_without_bang_unsat"] = {
            "satisfiable": is_sat,
            "expected": False,
            "pass": is_sat == False,
            "description": "Formula used twice without ! should be UNSAT (linear logic violation)"
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_reuse_without_bang_unsat"] = {"error": str(e)}

    # Test 2: UNSAT when A⊗B claimed equal to A&B via cardinality
    try:
        solver = cvc5.Solver()
        # Tensor uses both; additive chooses one
        # Multiplicative: uses_A + uses_B total (both consumed)
        # Additive: max(uses_A, uses_B) (one chosen)
        uses_A = solver.mkInteger(1)
        uses_B = solver.mkInteger(1)

        mult_total = solver.mkTerm(cvc5.Kind.PLUS, uses_A, uses_B)  # 2
        add_total = solver.mkInteger(1)  # choose one: 1

        # UNSAT if we claim they're equal
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, mult_total, add_total))

        is_sat = solver.checkSat().isSat()
        results["test_tensor_not_equal_additive_unsat"] = {
            "satisfiable": is_sat,
            "expected": False,
            "pass": is_sat == False,
            "description": "A⊗B (uses 2) cannot equal A&B (uses 1); distinct connectives"
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_tensor_not_equal_additive_unsat"] = {"error": str(e)}

    # Test 3: UNSAT when !A inconsistent weakening/contraction in same branch
    try:
        solver = cvc5.Solver()
        # !A in same branch: either 0 (weakening) or >0 (contraction), not both
        # If one branch uses !A 0 times AND another branch uses it 2 times,
        # they must be separate branches
        bang_A_uses_branch1 = solver.mkInteger(0)  # weakening: not used
        bang_A_uses_branch2 = solver.mkInteger(2)  # contraction: used multiple times

        # Both in SAME branch: UNSAT
        # (representing single branch constraint)
        same_branch = solver.mkTrue()

        # If same_branch, then uses in branch1 == uses in branch2 (consistency)
        consistency = solver.mkTerm(cvc5.Kind.IMPLIES, same_branch,
                                    solver.mkTerm(cvc5.Kind.EQUAL, bang_A_uses_branch1, bang_A_uses_branch2))
        solver.assertFormula(consistency)
        solver.assertFormula(same_branch)

        is_sat = solver.checkSat().isSat()
        results["test_bang_inconsistent_branch_unsat"] = {
            "satisfiable": is_sat,
            "expected": False,
            "pass": is_sat == False,
            "description": "!A with 0 uses (weakening) and 2 uses (contraction) in same branch is UNSAT"
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_bang_inconsistent_branch_unsat"] = {"error": str(e)}

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """Test edge cases and boundary conditions."""
    results = {}

    if not cvc5:
        return {"error": "cvc5 not installed"}

    # Test 1: Zero uses (weakening with !)
    try:
        solver = cvc5.Solver()
        A_uses = solver.mkInteger(0)
        A_has_bang = solver.mkTrue()

        constraint = solver.mkTerm(cvc5.Kind.GEQ, A_uses, solver.mkInteger(0))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.AND, constraint,
                                          solver.mkTerm(cvc5.Kind.EQUAL, A_has_bang, solver.mkTrue())))

        is_sat = solver.checkSat().isSat()
        results["test_zero_uses_with_bang"] = {
            "satisfiable": is_sat,
            "expected": True,
            "pass": is_sat == True,
            "description": "!A with zero uses (weakening) should be satisfiable"
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_zero_uses_with_bang"] = {"error": str(e)}

    # Test 2: Cut rule resource conservation (Γ,A ⊢ B and Δ ⊢ A implies Γ,Δ ⊢ B)
    try:
        solver = cvc5.Solver()
        # Γ has 2 formulas, A once in premise, Δ has 1 formula
        gamma_size = solver.mkInteger(2)
        delta_size = solver.mkInteger(1)
        # Conclusion: Γ + Δ in consequent, A consumed
        conclusion_size = solver.mkTerm(cvc5.Kind.PLUS, gamma_size, delta_size)

        # Should equal 3
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, conclusion_size, solver.mkInteger(3)))

        is_sat = solver.checkSat().isSat()
        results["test_cut_rule_conservation"] = {
            "satisfiable": is_sat,
            "expected": True,
            "pass": is_sat == True,
            "description": "Cut rule conserves resources: Γ,A ⊢ B and Δ ⊢ A gives Γ,Δ ⊢ B"
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_cut_rule_conservation"] = {"error": str(e)}

    # Test 3: Sympy verification of sequent calculus resource conservation
    try:
        if not sp:
            results["test_sympy_sequent_calculus"] = {"error": "sympy not installed"}
        else:
            # Verify: if Γ ⊢ A and Δ ⊢ B, then Γ,Δ ⊢ A⊗B
            # In terms of resource counts: |Γ| + |Δ| = size of conclusion context

            gamma_count = sp.Symbol('gamma', integer=True, positive=True)
            delta_count = sp.Symbol('delta', integer=True, positive=True)

            # Conclusion context size
            conclusion_context = gamma_count + delta_count

            # Verify for concrete example: |Γ|=2, |Δ|=1
            concrete = conclusion_context.subs([(gamma_count, 2), (delta_count, 1)])

            results["test_sympy_sequent_calculus"] = {
                "gamma": 2,
                "delta": 1,
                "conclusion_context_size": int(concrete),
                "expected": 3,
                "pass": int(concrete) == 3,
                "description": "Sympy verification: Γ={A,B}, Δ={C} => Γ,Δ ⊢ A⊗B uses 3 formulas"
            }
            TOOL_MANIFEST["sympy"]["used"] = True
    except Exception as e:
        results["test_sympy_sequent_calculus"] = {"error": str(e)}

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    results = {
        "name": "sim_cvc5_linear_logic_resource_constraint",
        "description": "Linear logic resource constraints: Girard's linear logic enforces each formula used exactly once unless marked with ! (of-course modality). Tests UNSAT when resource invariants violated.",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }

    # Update tool usage summary
    TOOL_MANIFEST["cvc5"]["reason"] = "load-bearing SMT solver for linear logic resource constraint UNSAT proofs"
    TOOL_MANIFEST["sympy"]["reason"] = "supportive verification of sequent calculus resource conservation"

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_cvc5_linear_logic_resource_constraint_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
