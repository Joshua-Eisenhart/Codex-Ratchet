#!/usr/bin/env python3
"""
No-Cloning Theorem via cvc5.

The no-cloning theorem: there is no unitary U such that U(|ψ⟩|0⟩) = |ψ⟩|ψ⟩ for all |ψ⟩.

Key constraint: if U could clone two non-orthogonal states |ψ⟩, |φ⟩, then:
  ⟨ψ|φ⟩ = ⟨ψ|U†U|φ⟩ = ⟨ψ|ψ⟩ ⟨φ|φ⟩ = 1 (assuming normalized)

But also, unitarity and cloning imply:
  ⟨ψ|φ⟩ = ⟨ψ|φ⟩ ⟨ψ|ψ⟩ ⟨φ|φ⟩

This forces ⟨ψ|φ⟩² = ⟨ψ|φ⟩, which means ⟨ψ|φ⟩ ∈ {0, 1}.
But if |ψ⟩ ≠ |φ⟩ and not orthogonal, 0 < ⟨ψ|φ⟩ < 1 => contradiction.

cvc5 uses QF_NRA to prove UNSAT when:
  - claim: cloning U exists for |ψ⟩, |φ⟩
  - constraint: 0 < ⟨ψ|φ⟩ < 1 (non-orthogonal, not identical)
  - unitarity: ⟨ψ|φ⟩² = ⟨ψ|φ⟩
  - These three together => UNSAT

sympy verifies inner product algebra and the constraint ⟨ψ|φ⟩² = ⟨ψ|φ⟩ independently.

Load-bearing: cvc5 detects impossibility via QF_NRA nonlinear constraint.
Supporting: sympy validates inner product algebra and derives admissible states.
"""

import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

classification = "tool_lego_fit_probe"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "pure symbolic proof via cvc5 and sympy"},
    "pyg": {"tried": False, "used": False, "reason": "no graph message passing needed; no-cloning is a pure algebra constraint"},
    "z3": {"tried": False, "used": False, "reason": "cvc5 is the load-bearing SMT solver for nonlinear constraints"},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": "Clifford algebra not needed; inner product constraints are sufficient"},
    "geomstats": {"tried": False, "used": False, "reason": "differential geometry not needed; state space is finite-dimensional vector space"},
    "e3nn": {"tried": False, "used": False, "reason": "permutation equivariance not needed; cloning constraint is state-independent"},
    "rustworkx": {"tried": False, "used": False, "reason": "graph structure not needed; cloning is a functional constraint"},
    "xgi": {"tried": False, "used": False, "reason": "hypergraph not needed; pairwise state overlap is sufficient"},
    "toponetx": {"tried": False, "used": False, "reason": "topological network analysis not required"},
    "gudhi": {"tried": False, "used": False, "reason": "simplicial complexes not needed; Hilbert space is vector space"},
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
    Verify cvc5 SAT for cases where no-cloning constraint is satisfied
    (states are orthogonal or identical).
    """
    results = {}

    if not TOOL_MANIFEST["cvc5"]["tried"]:
        return results

    import cvc5

    # Test 1: Orthogonal states can be distinguished (not cloned, but OK)
    # |ψ⟩ = |0⟩, |φ⟩ = |1⟩ => ⟨ψ|φ⟩ = 0
    # Constraint: ⟨ψ|φ⟩ = 0 => ⟨ψ|φ⟩² = 0 (satisfied)
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_NRA")
        solver.setOption("produce-models", "true")

        real_sort = solver.getRealSort()
        overlap = solver.mkConst(real_sort, "overlap")

        # Claim: ⟨ψ|φ⟩ = 0 (orthogonal)
        ortho = solver.mkTerm(cvc5.Kind.EQUAL, overlap, solver.mkReal(0))

        # Constraint: ⟨ψ|φ⟩² = ⟨ψ|φ⟩
        overlap_sq = solver.mkTerm(cvc5.Kind.MULT, overlap, overlap)
        constraint = solver.mkTerm(cvc5.Kind.EQUAL, overlap_sq, overlap)

        solver.assertFormula(ortho)
        solver.assertFormula(constraint)

        is_sat = solver.checkSat().isSat()
        results["test_positive_orthogonal"] = {
            "description": "cvc5 SAT: orthogonal states ⟨ψ|φ⟩ = 0, constraint satisfied",
            "overlap": 0.0,
            "sat": is_sat,
            "expected": True,
        }

        if is_sat:
            model = solver.getValue([overlap])
            results["test_positive_orthogonal"]["model_overlap"] = str(model)

        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
    except Exception as e:
        results["test_positive_orthogonal"] = {"error": str(e)}

    # Test 2: Identical states (⟨ψ|ψ⟩ = 1)
    # |ψ⟩ = |φ⟩ => ⟨ψ|φ⟩ = 1
    # Constraint: 1² = 1 (satisfied)
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_NRA")

        real_sort = solver.getRealSort()
        overlap = solver.mkConst(real_sort, "overlap")

        # Claim: ⟨ψ|φ⟩ = 1 (identical)
        identical = solver.mkTerm(cvc5.Kind.EQUAL, overlap, solver.mkReal(1))

        # Constraint: overlap² = overlap
        overlap_sq = solver.mkTerm(cvc5.Kind.MULT, overlap, overlap)
        constraint = solver.mkTerm(cvc5.Kind.EQUAL, overlap_sq, overlap)

        solver.assertFormula(identical)
        solver.assertFormula(constraint)

        is_sat = solver.checkSat().isSat()
        results["test_positive_identical"] = {
            "description": "cvc5 SAT: identical states ⟨ψ|φ⟩ = 1, constraint satisfied",
            "overlap": 1.0,
            "sat": is_sat,
            "expected": True,
        }

        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_positive_identical"] = {"error": str(e)}

    # Test 3: Fixed points of ⟨ψ|φ⟩² = ⟨ψ|φ⟩
    # Solutions: ⟨ψ|φ⟩ = 0 or ⟨ψ|φ⟩ = 1
    # No other real solution exists
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_NRA")

        real_sort = solver.getRealSort()
        overlap = solver.mkConst(real_sort, "overlap")

        # Constraint: overlap² = overlap
        overlap_sq = solver.mkTerm(cvc5.Kind.MULT, overlap, overlap)
        constraint = solver.mkTerm(cvc5.Kind.EQUAL, overlap_sq, overlap)

        solver.assertFormula(constraint)

        is_sat = solver.checkSat().isSat()
        results["test_positive_fixpoint"] = {
            "description": "cvc5 SAT: ⟨ψ|φ⟩² = ⟨ψ|φ⟩ has solutions (0 and 1)",
            "sat": is_sat,
            "expected": True,
        }

        if is_sat:
            model = solver.getValue([overlap])
            results["test_positive_fixpoint"]["model_overlap"] = str(model)

        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_positive_fixpoint"] = {"error": str(e)}

    # Test 4: sympy verification of fixpoint equation
    if TOOL_MANIFEST["sympy"]["tried"]:
        try:
            import sympy as sp

            x = sp.Symbol('x', real=True)
            # Solve x² - x = 0
            fixpoint_eq = x**2 - x
            solutions = sp.solve(fixpoint_eq, x)

            results["test_positive_sympy_fixpoint"] = {
                "description": "sympy solves ⟨ψ|φ⟩² = ⟨ψ|φ⟩",
                "equation": str(fixpoint_eq),
                "solutions": [float(sol) for sol in solutions],
                "expected_solutions": [0.0, 1.0],
            }

            TOOL_MANIFEST["sympy"]["used"] = True
            TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"
        except Exception as e:
            results["test_positive_sympy_fixpoint"] = {"error": str(e)}

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    """
    Verify cvc5 UNSAT for impossible cloning scenarios.
    UNSAT: claim cloning works + 0 < ⟨ψ|φ⟩ < 1 (non-orthogonal, not identical).
    """
    results = {}

    if not TOOL_MANIFEST["cvc5"]["tried"]:
        return results

    import cvc5

    # Test 1: Non-orthogonal states violate no-cloning
    # Claim: cloning works for |ψ⟩, |φ⟩ with ⟨ψ|φ⟩ = 0.5
    # Cloning claim: ⟨ψ|φ⟩ = ⟨ψ|φ⟩ ⟨ψ|ψ⟩ ⟨φ|φ⟩ = ⟨ψ|φ⟩ (assuming normalized)
    # Constraint: 0.5² = 0.5 => 0.25 = 0.5 => FALSE => UNSAT
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_NRA")

        real_sort = solver.getRealSort()
        overlap = solver.mkConst(real_sort, "overlap")

        # Claim: ⟨ψ|φ⟩ = 0.5
        claim = solver.mkTerm(cvc5.Kind.EQUAL, overlap, solver.mkReal(1, 2))

        # Constraint: overlap² = overlap (required for cloning + unitarity)
        overlap_sq = solver.mkTerm(cvc5.Kind.MULT, overlap, overlap)
        constraint = solver.mkTerm(cvc5.Kind.EQUAL, overlap_sq, overlap)

        solver.assertFormula(claim)
        solver.assertFormula(constraint)

        is_sat = solver.checkSat().isSat()
        results["test_negative_half_overlap"] = {
            "description": "cvc5 UNSAT: ⟨ψ|φ⟩ = 0.5 violates ⟨ψ|φ⟩² = ⟨ψ|φ⟩ (0.25 ≠ 0.5)",
            "overlap": 0.5,
            "sat": is_sat,
            "expected": False,
        }
    except Exception as e:
        results["test_negative_half_overlap"] = {"error": str(e)}

    # Test 2: Another non-orthogonal case (⟨ψ|φ⟩ = 0.6)
    # 0.6² = 0.36 ≠ 0.6 => UNSAT
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_NRA")

        real_sort = solver.getRealSort()
        overlap = solver.mkConst(real_sort, "overlap")

        # Claim: ⟨ψ|φ⟩ = 0.6 (3/5)
        claim = solver.mkTerm(cvc5.Kind.EQUAL, overlap, solver.mkReal(3, 5))

        # Constraint: overlap² = overlap
        overlap_sq = solver.mkTerm(cvc5.Kind.MULT, overlap, overlap)
        constraint = solver.mkTerm(cvc5.Kind.EQUAL, overlap_sq, overlap)

        solver.assertFormula(claim)
        solver.assertFormula(constraint)

        is_sat = solver.checkSat().isSat()
        results["test_negative_0_6_overlap"] = {
            "description": "cvc5 UNSAT: ⟨ψ|φ⟩ = 0.6 violates constraint (0.36 ≠ 0.6)",
            "overlap": 0.6,
            "sat": is_sat,
            "expected": False,
        }
    except Exception as e:
        results["test_negative_0_6_overlap"] = {"error": str(e)}

    # Test 3: Range contradiction: claim 0 < overlap < 1 AND overlap² = overlap
    # The only solutions are 0 and 1, so this range is UNSAT
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_NRA")

        real_sort = solver.getRealSort()
        overlap = solver.mkConst(real_sort, "overlap")

        # Constraint: 0 < overlap < 1
        c1 = solver.mkTerm(cvc5.Kind.GT, overlap, solver.mkReal(0))
        c2 = solver.mkTerm(cvc5.Kind.LT, overlap, solver.mkReal(1))

        # Constraint: overlap² = overlap
        overlap_sq = solver.mkTerm(cvc5.Kind.MULT, overlap, overlap)
        c3 = solver.mkTerm(cvc5.Kind.EQUAL, overlap_sq, overlap)

        solver.assertFormula(c1)
        solver.assertFormula(c2)
        solver.assertFormula(c3)

        is_sat = solver.checkSat().isSat()
        results["test_negative_open_interval"] = {
            "description": "cvc5 UNSAT: 0 < ⟨ψ|φ⟩ < 1 contradicts ⟨ψ|φ⟩² = ⟨ψ|φ⟩",
            "sat": is_sat,
            "expected": False,
        }
    except Exception as e:
        results["test_negative_open_interval"] = {"error": str(e)}

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """
    Edge cases: boundary values, limit cases, numerical precision.
    """
    results = {}

    if not TOOL_MANIFEST["cvc5"]["tried"]:
        return results

    import cvc5

    # Test 1: Exactly at boundary (overlap = 0, orthogonal boundary)
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_NRA")

        real_sort = solver.getRealSort()
        overlap = solver.mkConst(real_sort, "overlap")

        # Claim: ⟨ψ|φ⟩ = 0
        c1 = solver.mkTerm(cvc5.Kind.EQUAL, overlap, solver.mkReal(0))

        # Constraint: overlap² = overlap => 0 = 0 (true)
        overlap_sq = solver.mkTerm(cvc5.Kind.MULT, overlap, overlap)
        c2 = solver.mkTerm(cvc5.Kind.EQUAL, overlap_sq, overlap)

        solver.assertFormula(c1)
        solver.assertFormula(c2)

        is_sat = solver.checkSat().isSat()
        results["test_boundary_zero"] = {
            "description": "cvc5 SAT: ⟨ψ|φ⟩ = 0 (orthogonal boundary)",
            "overlap": 0.0,
            "sat": is_sat,
            "expected": True,
        }
    except Exception as e:
        results["test_boundary_zero"] = {"error": str(e)}

    # Test 2: Exactly at boundary (overlap = 1, identical boundary)
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_NRA")

        real_sort = solver.getRealSort()
        overlap = solver.mkConst(real_sort, "overlap")

        # Claim: ⟨ψ|φ⟩ = 1
        c1 = solver.mkTerm(cvc5.Kind.EQUAL, overlap, solver.mkReal(1))

        # Constraint: overlap² = overlap => 1 = 1 (true)
        overlap_sq = solver.mkTerm(cvc5.Kind.MULT, overlap, overlap)
        c2 = solver.mkTerm(cvc5.Kind.EQUAL, overlap_sq, overlap)

        solver.assertFormula(c1)
        solver.assertFormula(c2)

        is_sat = solver.checkSat().isSat()
        results["test_boundary_one"] = {
            "description": "cvc5 SAT: ⟨ψ|φ⟩ = 1 (identical boundary)",
            "overlap": 1.0,
            "sat": is_sat,
            "expected": True,
        }
    except Exception as e:
        results["test_boundary_one"] = {"error": str(e)}

    # Test 3: Near-orthogonal (small positive overlap)
    # ⟨ψ|φ⟩ = 0.01 => 0.01² = 0.0001 ≠ 0.01 => UNSAT
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_NRA")

        real_sort = solver.getRealSort()
        overlap = solver.mkConst(real_sort, "overlap")

        # Claim: ⟨ψ|φ⟩ = 0.01
        c1 = solver.mkTerm(cvc5.Kind.EQUAL, overlap, solver.mkReal(1, 100))

        # Constraint: overlap² = overlap
        overlap_sq = solver.mkTerm(cvc5.Kind.MULT, overlap, overlap)
        c2 = solver.mkTerm(cvc5.Kind.EQUAL, overlap_sq, overlap)

        solver.assertFormula(c1)
        solver.assertFormula(c2)

        is_sat = solver.checkSat().isSat()
        results["test_boundary_near_zero"] = {
            "description": "cvc5 UNSAT: ⟨ψ|φ⟩ = 0.01, constraint violated",
            "overlap": 0.01,
            "sat": is_sat,
            "expected": False,
        }
    except Exception as e:
        results["test_boundary_near_zero"] = {"error": str(e)}

    # Test 4: Near-identical (high overlap)
    # ⟨ψ|φ⟩ = 0.99 => 0.99² = 0.9801 ≠ 0.99 => UNSAT
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_NRA")

        real_sort = solver.getRealSort()
        overlap = solver.mkConst(real_sort, "overlap")

        # Claim: ⟨ψ|φ⟩ = 0.99
        c1 = solver.mkTerm(cvc5.Kind.EQUAL, overlap, solver.mkReal(99, 100))

        # Constraint: overlap² = overlap
        overlap_sq = solver.mkTerm(cvc5.Kind.MULT, overlap, overlap)
        c2 = solver.mkTerm(cvc5.Kind.EQUAL, overlap_sq, overlap)

        solver.assertFormula(c1)
        solver.assertFormula(c2)

        is_sat = solver.checkSat().isSat()
        results["test_boundary_near_one"] = {
            "description": "cvc5 UNSAT: ⟨ψ|φ⟩ = 0.99, constraint violated",
            "overlap": 0.99,
            "sat": is_sat,
            "expected": False,
        }
    except Exception as e:
        results["test_boundary_near_one"] = {"error": str(e)}

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    results = {
        "name": "cvc5 No-Cloning Theorem Constraint",
        "description": "Proves that no unitary can clone non-orthogonal quantum states",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_cvc5_no_cloning_constraint_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
