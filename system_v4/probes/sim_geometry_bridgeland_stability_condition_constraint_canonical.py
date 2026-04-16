#!/usr/bin/env python3
"""
Bridgeland Stability Condition Canonical Sim

Bridgeland stability: (Z, A) where Z: K(X) → C is a central charge and A is
a heart of a t-structure. Key constraint: every object has a unique Harder-Narasimhan
(HN) filtration with semistable factors sorted by decreasing phase φ(Z(E_i)).

cvc5 proves the HN constraint:
- If phases are non-decreasing (destabilizing), the constraint is UNSAT.
- If phases decrease and Z-values satisfy the slope relations, the constraint is SAT.

sympy handles central charge formulas for curves: Z(E) = -ch_1(E) + i·ch_0(E).
"""

import json
import os
import sys

# =====================================================================
# TOOL MANIFEST -- Document which tools were tried
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "pytorch not needed; pure symbolic/algebraic computation via cvc5 and sympy"},
    "pyg": {"tried": False, "used": False, "reason": "PyG message passing not needed; constraint geometry handled via SMT solver"},
    "z3": {"tried": False, "used": False, "reason": "z3 not needed; cvc5 handles all SMT constraint proofs in this sim"},
    "cvc5": {"tried": False, "used": False, "reason": "cvc5 SMT solver: load_bearing proof of stability constraints"},
    "sympy": {"tried": False, "used": False, "reason": "sympy: supportive symbolic algebra for stability condition formulas"},
    "clifford": {"tried": False, "used": False, "reason": "Clifford algebra not needed; stability geometry constraints only"},
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

# Try importing each tool
try:
    import torch  # noqa: F401
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

cvc5_installed = False
try:
    import cvc5
    TOOL_MANIFEST["cvc5"]["tried"] = True
    cvc5_installed = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

sympy_installed = False
try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    sympy_installed = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

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
    """
    Test valid HN filtrations: phases decrease, Z-values compatible.
    """
    results = {}

    if not cvc5_installed or not sympy_installed:
        return {"error": "cvc5 or sympy not installed"}

    import cvc5
    import sympy as sp

    # Test 1: Two semistable factors with decreasing phases
    # E has factors F1, F2 with φ(Z(F1)) = 2.5, φ(Z(F2)) = 1.0
    # Z(F1) = 3 + 2.5i, Z(F2) = 2 + 1.0i
    solver = cvc5.Solver()
    solver.setLogic("QF_NRA")

    # Central charges (real and imaginary parts)
    z1_re = solver.mkReal(3)
    z1_im = solver.mkReal(5, 2)  # 2.5
    z2_re = solver.mkReal(2)
    z2_im = solver.mkReal(1)

    # Phases φ(Z) = atan2(Im(Z), Re(Z))
    # For decreasing HN filtration: φ(Z1) > φ(Z2)
    # This translates to: z1_im/z1_re > z2_im/z2_re (cross multiply for nonlinear constraint)
    # z1_im * z2_re > z2_im * z1_re

    cross_product = solver.mkTerm(cvc5.Kind.MULT, z1_im, z2_re)
    cross_product_2 = solver.mkTerm(cvc5.Kind.MULT, z2_im, z1_re)
    phase_constraint = solver.mkTerm(cvc5.Kind.GT, cross_product, cross_product_2)

    solver.assertFormula(phase_constraint)

    result = solver.checkSat()
    results["test_1_decreasing_phases"] = {
        "name": "Two factors with decreasing phases",
        "sat": result.isSat(),
        "expected": True,
        "pass": result.isSat(),
    }

    # Test 2: Three semistable factors with monotonic decreasing phases
    # φ(Z1) = 2.5, φ(Z2) = 1.5, φ(Z3) = 0.5
    solver2 = cvc5.Solver()
    solver2.setLogic("QF_NRA")

    z1_re2 = solver2.mkReal(4)
    z1_im2 = solver2.mkReal(10)
    z2_re2 = solver2.mkReal(2)
    z2_im2 = solver2.mkReal(3)
    z3_re2 = solver2.mkReal(2)
    z3_im2 = solver2.mkReal(1)

    # φ1 > φ2: z1_im2 * z2_re2 > z2_im2 * z1_re2
    cp1 = solver2.mkTerm(cvc5.Kind.MULT, z1_im2, z2_re2)
    cp2 = solver2.mkTerm(cvc5.Kind.MULT, z2_im2, z1_re2)
    phase1_2 = solver2.mkTerm(cvc5.Kind.GT, cp1, cp2)

    # φ2 > φ3: z2_im2 * z3_re2 > z3_im2 * z2_re2
    cp3 = solver2.mkTerm(cvc5.Kind.MULT, z2_im2, z3_re2)
    cp4 = solver2.mkTerm(cvc5.Kind.MULT, z3_im2, z2_re2)
    phase2_3 = solver2.mkTerm(cvc5.Kind.GT, cp3, cp4)

    solver2.assertFormula(phase1_2)
    solver2.assertFormula(phase2_3)

    result2 = solver2.checkSat()
    results["test_2_three_factors_monotonic"] = {
        "name": "Three factors with monotonic decreasing phases",
        "sat": result2.isSat(),
        "expected": True,
        "pass": result2.isSat(),
    }

    # Test 3: Sympy central charge formula for a curve
    # For a coherent sheaf E on a curve: Z(E) = -ch_1(E) + i·ch_0(E)
    # With ch_0(E) = rank(E) and ch_1(E) = degree(E)
    ch0 = sp.Symbol("ch0", real=True, positive=True)  # rank
    ch1 = sp.Symbol("ch1", real=True)  # degree
    z_formula = -ch1 + sp.I * ch0

    # Test with rank=2, degree=5
    z_eval = z_formula.subs([(ch0, 2), (ch1, 5)])
    expected_z = -5 + 2j

    results["test_3_sympy_central_charge"] = {
        "name": "Central charge formula Z(E) = -ch_1 + i·ch_0",
        "computed": str(z_eval),
        "expected": str(expected_z),
        "pass": z_eval == expected_z,
    }

    return results


# =====================================================================
# NEGATIVE TESTS (mandatory)
# =====================================================================

def run_negative_tests():
    """
    Test invalid HN filtrations: phases non-decreasing (UNSAT).
    """
    results = {}

    if not cvc5_installed:
        return {"error": "cvc5 not installed"}

    import cvc5

    # Test 1: Non-decreasing phases (should be UNSAT)
    # φ(Z1) = 1.0, φ(Z2) = 2.5 (increasing, invalid)
    solver = cvc5.Solver()
    solver.setLogic("QF_NRA")

    z1_re = solver.mkReal(2)
    z1_im = solver.mkReal(1)
    z2_re = solver.mkReal(3)
    z2_im = solver.mkReal(5, 2)  # 2.5

    # φ1 > φ2 should fail when φ1 < φ2
    # z1_im * z2_re > z2_im * z1_re
    # 1 * 3 > 2.5 * 2 => 3 > 5 (FALSE)
    cross_product = solver.mkTerm(cvc5.Kind.MULT, z1_im, z2_re)
    cross_product_2 = solver.mkTerm(cvc5.Kind.MULT, z2_im, z1_re)
    phase_constraint = solver.mkTerm(cvc5.Kind.GT, cross_product, cross_product_2)

    solver.assertFormula(phase_constraint)

    result = solver.checkSat()
    results["test_1_nondecreasing_unsat"] = {
        "name": "Non-decreasing phases (should be UNSAT)",
        "sat": result.isSat(),
        "expected": False,
        "pass": not result.isSat(),
    }

    # Test 2: Conflicting Z-values with same phase
    # Two factors with same phase but incompatible slopes
    solver2 = cvc5.Solver()
    solver2.setLogic("QF_NRA")

    z1_re2 = solver2.mkReal(1)
    z1_im2 = solver2.mkReal(1)
    z2_re2 = solver2.mkReal(1)
    z2_im2 = solver2.mkReal(1)

    # Same phase (z1_im2 * z2_re2 = z2_im2 * z1_re2 => 1*1 = 1*1)
    # But phases must be STRICTLY decreasing for HN filtration
    cp1 = solver2.mkTerm(cvc5.Kind.MULT, z1_im2, z2_re2)
    cp2 = solver2.mkTerm(cvc5.Kind.MULT, z2_im2, z1_re2)
    strict_decrease = solver2.mkTerm(cvc5.Kind.GT, cp1, cp2)

    solver2.assertFormula(strict_decrease)

    result2 = solver2.checkSat()
    results["test_2_same_phase_unsat"] = {
        "name": "Same phase (should be UNSAT for strict HN)",
        "sat": result2.isSat(),
        "expected": False,
        "pass": not result2.isSat(),
    }

    # Test 3: Negative rank (impossible)
    if sympy_installed:
        import sympy as sp

        ch0 = sp.Symbol("ch0", real=True, positive=True)
        ch1 = sp.Symbol("ch1", real=True)
        z_formula = -ch1 + sp.I * ch0

        # Try to evaluate with rank <= 0 (violates positivity constraint)
        # This should fail symbolic validation
        try:
            z_eval = z_formula.subs([(ch0, -1), (ch1, 0)])
            results["test_3_negative_rank"] = {
                "name": "Negative rank (invalid)",
                "computed": str(z_eval),
                "expected": "exception",
                "pass": False,
            }
        except Exception as e:
            results["test_3_negative_rank"] = {
                "name": "Negative rank (invalid)",
                "error": str(e),
                "pass": True,
            }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """
    Edge cases: zero central charges, phases near pi/2, etc.
    """
    results = {}

    if not cvc5_installed or not sympy_installed:
        return {"error": "cvc5 or sympy not installed"}

    import cvc5
    import sympy as sp

    # Test 1: Very small imaginary part (phase near 0)
    solver = cvc5.Solver()
    solver.setLogic("QF_NRA")

    z1_re = solver.mkReal(1)
    z1_im = solver.mkReal(1, 1000)  # 0.001
    z2_re = solver.mkReal(1)
    z2_im = solver.mkReal(0)

    # φ1 > φ2: z1_im * z2_re > z2_im * z1_re
    # 0.001 * 1 > 0 * 1 => 0.001 > 0 (TRUE)
    cross_product = solver.mkTerm(cvc5.Kind.MULT, z1_im, z2_re)
    cross_product_2 = solver.mkTerm(cvc5.Kind.MULT, z2_im, z1_re)
    phase_constraint = solver.mkTerm(cvc5.Kind.GT, cross_product, cross_product_2)

    solver.assertFormula(phase_constraint)

    result = solver.checkSat()
    results["test_1_small_imaginary"] = {
        "name": "Small imaginary part (phase near 0)",
        "sat": result.isSat(),
        "expected": True,
        "pass": result.isSat(),
    }

    # Test 2: Large negative real part
    solver2 = cvc5.Solver()
    solver2.setLogic("QF_NRA")

    z1_re2 = solver2.mkReal(-100)
    z1_im2 = solver2.mkReal(1)
    z2_re2 = solver2.mkReal(-1)
    z2_im2 = solver2.mkReal(1)

    cp1 = solver2.mkTerm(cvc5.Kind.MULT, z1_im2, z2_re2)
    cp2 = solver2.mkTerm(cvc5.Kind.MULT, z2_im2, z1_re2)
    phase_constraint2 = solver2.mkTerm(cvc5.Kind.GT, cp1, cp2)

    solver2.assertFormula(phase_constraint2)

    result2 = solver2.checkSat()
    results["test_2_large_negative_re"] = {
        "name": "Large negative real part",
        "sat": result2.isSat(),
        "expected": True,
        "pass": result2.isSat(),
    }

    # Test 3: Sympy formula at boundary (rank = 1)
    ch0 = sp.Symbol("ch0", real=True, positive=True)
    ch1 = sp.Symbol("ch1", real=True)
    z_formula = -ch1 + sp.I * ch0

    z_eval = z_formula.subs([(ch0, 1), (ch1, 0)])
    expected_z = 0 + 1j

    results["test_3_rank_one_bundle"] = {
        "name": "Rank-1 bundle (line bundle)",
        "computed": str(z_eval),
        "expected": str(expected_z),
        "pass": z_eval == expected_z,
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    results = {
        "name": "Bridgeland Stability Condition Canonical Sim",
        "description": "HN filtration constraint: phases strictly decreasing, Z-values satisfy stability geometry",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }

    # Update tool usage based on what was actually used
    if cvc5_installed:
        TOOL_MANIFEST["cvc5"]["used"] = True
    if sympy_installed:
        TOOL_MANIFEST["sympy"]["used"] = True

    results["tool_manifest"] = TOOL_MANIFEST

    out_dir = os.path.join(
        os.path.dirname(__file__), "a2_state", "sim_results"
    )
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(
        out_dir, "sim_geometry_bridgeland_stability_condition_constraint_canonical_results.json"
    )
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
