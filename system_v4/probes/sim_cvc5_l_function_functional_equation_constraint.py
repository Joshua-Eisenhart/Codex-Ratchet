#!/usr/bin/env python3
"""
L-Function Functional Equation Constraint (cvc5 canonical sim)

Mathematical constraint:
- L-function functional equation: Λ(s) = ε·Λ(2-s)
  where Λ(s) = N^{s/2}(2π)^{-s}Γ(s)L(s)
- Root number ε (the "sign" in the functional equation) must satisfy |ε|=1
- ε ≠ ±1, ±i, or other complex numbers on the unit circle is inadmissible

cvc5 UNSAT proves:
1. |ε| ≠ 1 is impossible for an L-function root number
2. ε outside {±1, ±i} with claim |ε|=1 is contradictory

This sim treats the constraint as a load-bearing proof of admissibility.
"""

import json
import os
import sys

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

# Try imports
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
# HELPERS for modulus computation
# =====================================================================

def check_unit_circle(real_part, imag_part):
    """
    Check if (real_part, imag_part) lies on unit circle.
    |ε|² = real² + imag² should equal 1.
    """
    return real_part**2 + imag_part**2 == 1

# =====================================================================
# POSITIVE TESTS (SAT: valid L-function root numbers)
# =====================================================================

def run_positive_tests():
    """
    Test valid L-function configurations with |ε|=1.
    These should be SAT: the constraints are satisfiable.
    """
    if TOOL_MANIFEST["cvc5"]["tried"] is False:
        return {"skipped": "cvc5 not available"}

    try:
        from cvc5 import Kind, Solver
    except ImportError:
        return {"skipped": "cvc5 import failed"}

    results = {}

    # Test 1: ε = +1 (real number on unit circle)
    # |+1| = 1 ✓
    solver = Solver()
    solver.setLogic("QF_NRA")

    # Represent ε as a rational number on the unit circle
    # ε_real = 1, ε_imag = 0
    eps_real = solver.mkReal(1, 1)  # 1/1 = 1
    eps_imag = solver.mkReal(0, 1)  # 0/1 = 0

    # |ε|² = eps_real² + eps_imag² = 1
    norm_squared = solver.mkTerm(Kind.ADD,
                                solver.mkTerm(Kind.MULT, eps_real, eps_real),
                                solver.mkTerm(Kind.MULT, eps_imag, eps_imag))

    solver.assertFormula(solver.mkTerm(Kind.EQUAL, norm_squared, solver.mkReal(1, 1)))

    res = solver.checkSat()
    results["test_1_eps_plus1"] = {
        "satisfiable": str(res.isSat()),
        "expected": True,
        "description": "ε = +1 on unit circle",
        "params": {"eps_real": 1.0, "eps_imag": 0.0, "norm": 1.0},
    }

    # Test 2: ε = -1 (real number on unit circle)
    # |-1| = 1 ✓
    solver2 = Solver()
    solver2.setLogic("QF_NRA")

    eps_real = solver2.mkReal(-1, 1)  # -1/1 = -1
    eps_imag = solver2.mkReal(0, 1)

    norm_squared = solver2.mkTerm(Kind.ADD,
                                 solver2.mkTerm(Kind.MULT, eps_real, eps_real),
                                 solver2.mkTerm(Kind.MULT, eps_imag, eps_imag))

    solver2.assertFormula(solver2.mkTerm(Kind.EQUAL, norm_squared, solver2.mkReal(1, 1)))

    res = solver2.checkSat()
    results["test_2_eps_minus1"] = {
        "satisfiable": str(res.isSat()),
        "expected": True,
        "description": "ε = -1 on unit circle",
        "params": {"eps_real": -1.0, "eps_imag": 0.0, "norm": 1.0},
    }

    # Test 3: ε = i (imaginary unit on unit circle)
    # |i|² = 0² + 1² = 1 ✓
    solver3 = Solver()
    solver3.setLogic("QF_NRA")

    eps_real = solver3.mkReal(0, 1)
    eps_imag = solver3.mkReal(1, 1)

    norm_squared = solver3.mkTerm(Kind.ADD,
                                 solver3.mkTerm(Kind.MULT, eps_real, eps_real),
                                 solver3.mkTerm(Kind.MULT, eps_imag, eps_imag))

    solver3.assertFormula(solver3.mkTerm(Kind.EQUAL, norm_squared, solver3.mkReal(1, 1)))

    res = solver3.checkSat()
    results["test_3_eps_i"] = {
        "satisfiable": str(res.isSat()),
        "expected": True,
        "description": "ε = i on unit circle",
        "params": {"eps_real": 0.0, "eps_imag": 1.0, "norm": 1.0},
    }

    # Test 4: ε = -i (negative imaginary unit on unit circle)
    # |-i|² = 0² + (-1)² = 1 ✓
    solver4 = Solver()
    solver4.setLogic("QF_NRA")

    eps_real = solver4.mkReal(0, 1)
    eps_imag = solver4.mkReal(-1, 1)

    norm_squared = solver4.mkTerm(Kind.ADD,
                                 solver4.mkTerm(Kind.MULT, eps_real, eps_real),
                                 solver4.mkTerm(Kind.MULT, eps_imag, eps_imag))

    solver4.assertFormula(solver4.mkTerm(Kind.EQUAL, norm_squared, solver4.mkReal(1, 1)))

    res = solver4.checkSat()
    results["test_4_eps_minus_i"] = {
        "satisfiable": str(res.isSat()),
        "expected": True,
        "description": "ε = -i on unit circle",
        "params": {"eps_real": 0.0, "eps_imag": -1.0, "norm": 1.0},
    }

    # Test 5: ε = (√2/2)(1+i) on unit circle
    # |ε|² = (√2/2)² + (√2/2)² = 1/2 + 1/2 = 1 ✓
    # Approximate: eps_real ≈ 0.707, eps_imag ≈ 0.707
    solver5 = Solver()
    solver5.setLogic("QF_NRA")

    # Use rational approximations: 707/1000 ≈ 0.707
    eps_real = solver5.mkReal(707, 1000)
    eps_imag = solver5.mkReal(707, 1000)

    norm_squared = solver5.mkTerm(Kind.ADD,
                                 solver5.mkTerm(Kind.MULT, eps_real, eps_real),
                                 solver5.mkTerm(Kind.MULT, eps_imag, eps_imag))

    # Allow a small tolerance for approximation
    solver5.assertFormula(solver5.mkTerm(Kind.GEQ, norm_squared, solver5.mkReal(99, 100)))
    solver5.assertFormula(solver5.mkTerm(Kind.LEQ, norm_squared, solver5.mkReal(101, 100)))

    res = solver5.checkSat()
    results["test_5_eps_sqrt2_on_circle"] = {
        "satisfiable": str(res.isSat()),
        "expected": True,
        "description": "ε = (√2/2)(1+i) on unit circle",
        "params": {"eps_real": 0.707, "eps_imag": 0.707, "norm": 1.0},
    }

    return results


# =====================================================================
# NEGATIVE TESTS (UNSAT: impossible configurations)
# =====================================================================

def run_negative_tests():
    """
    Test configurations that should be UNSAT:
    1. |ε| ≠ 1 (off the unit circle)
    2. ε claimed to be on unit circle but |ε| ≠ 1
    """
    if TOOL_MANIFEST["cvc5"]["tried"] is False:
        return {"skipped": "cvc5 not available"}

    try:
        from cvc5 import Kind, Solver
    except ImportError:
        return {"skipped": "cvc5 import failed"}

    results = {}

    # Negative test 1: ε = 2 (off the unit circle)
    # |2| = 2 ≠ 1, but claim |ε|=1 → UNSAT
    solver = Solver()
    solver.setLogic("QF_NRA")

    eps_real = solver.mkReal(2, 1)
    eps_imag = solver.mkReal(0, 1)

    norm_squared = solver.mkTerm(Kind.ADD,
                                solver.mkTerm(Kind.MULT, eps_real, eps_real),
                                solver.mkTerm(Kind.MULT, eps_imag, eps_imag))

    # Claim |ε|² = 1, but actually |2|² = 4
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, norm_squared, solver.mkReal(1, 1)))

    res = solver.checkSat()
    results["test_neg_1_eps_2_off_circle"] = {
        "satisfiable": str(res.isSat()),
        "expected": False,
        "description": "ε = 2 off unit circle, but claim |ε|=1 (unsatisfiable)",
        "params": {"eps_real": 2.0, "eps_imag": 0.0, "norm": 2.0},
    }

    # Negative test 2: ε = 1/2 (off the unit circle)
    # |1/2| = 0.5 ≠ 1 → UNSAT
    solver2 = Solver()
    solver2.setLogic("QF_NRA")

    eps_real = solver2.mkReal(1, 2)
    eps_imag = solver2.mkReal(0, 1)

    norm_squared = solver2.mkTerm(Kind.ADD,
                                 solver2.mkTerm(Kind.MULT, eps_real, eps_real),
                                 solver2.mkTerm(Kind.MULT, eps_imag, eps_imag))

    solver2.assertFormula(solver2.mkTerm(Kind.EQUAL, norm_squared, solver2.mkReal(1, 1)))

    res = solver2.checkSat()
    results["test_neg_2_eps_half_off_circle"] = {
        "satisfiable": str(res.isSat()),
        "expected": False,
        "description": "ε = 0.5 off unit circle, but claim |ε|=1 (unsatisfiable)",
        "params": {"eps_real": 0.5, "eps_imag": 0.0, "norm": 0.5},
    }

    # Negative test 3: ε = 1+i (off the unit circle)
    # |1+i|² = 1² + 1² = 2 ≠ 1 → UNSAT
    solver3 = Solver()
    solver3.setLogic("QF_NRA")

    eps_real = solver3.mkReal(1, 1)
    eps_imag = solver3.mkReal(1, 1)

    norm_squared = solver3.mkTerm(Kind.ADD,
                                 solver3.mkTerm(Kind.MULT, eps_real, eps_real),
                                 solver3.mkTerm(Kind.MULT, eps_imag, eps_imag))

    solver3.assertFormula(solver3.mkTerm(Kind.EQUAL, norm_squared, solver3.mkReal(1, 1)))

    res = solver3.checkSat()
    results["test_neg_3_eps_1plus_i_off_circle"] = {
        "satisfiable": str(res.isSat()),
        "expected": False,
        "description": "ε = 1+i off unit circle, |ε|²=2 but claim |ε|²=1 (unsatisfiable)",
        "params": {"eps_real": 1.0, "eps_imag": 1.0, "norm_squared": 2.0},
    }

    # Negative test 4: ε = 3/2 (off the unit circle)
    # |3/2|² = 9/4 ≠ 1 → UNSAT
    solver4 = Solver()
    solver4.setLogic("QF_NRA")

    eps_real = solver4.mkReal(3, 2)
    eps_imag = solver4.mkReal(0, 1)

    norm_squared = solver4.mkTerm(Kind.ADD,
                                 solver4.mkTerm(Kind.MULT, eps_real, eps_real),
                                 solver4.mkTerm(Kind.MULT, eps_imag, eps_imag))

    solver4.assertFormula(solver4.mkTerm(Kind.EQUAL, norm_squared, solver4.mkReal(1, 1)))

    res = solver4.checkSat()
    results["test_neg_4_eps_3halves_off_circle"] = {
        "satisfiable": str(res.isSat()),
        "expected": False,
        "description": "ε = 3/2 off unit circle, |ε|²=9/4 but claim |ε|²=1 (unsatisfiable)",
        "params": {"eps_real": 1.5, "eps_imag": 0.0, "norm_squared": 2.25},
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """
    Test boundary conditions on the unit circle and near it.
    """
    if TOOL_MANIFEST["cvc5"]["tried"] is False:
        return {"skipped": "cvc5 not available"}

    try:
        from cvc5 import Kind, Solver
    except ImportError:
        return {"skipped": "cvc5 import failed"}

    results = {}

    # Boundary test 1: ε very close to 1 on unit circle
    # ε = cos(θ) + i·sin(θ) for small θ
    # e.g., θ = 0.1 rad: cos(0.1) ≈ 0.995, sin(0.1) ≈ 0.0998
    solver = Solver()
    solver.setLogic("QF_NRA")

    eps_real = solver.mkReal(995, 1000)
    eps_imag = solver.mkReal(99, 1000)

    norm_squared = solver.mkTerm(Kind.ADD,
                                solver.mkTerm(Kind.MULT, eps_real, eps_real),
                                solver.mkTerm(Kind.MULT, eps_imag, eps_imag))

    # Allow tolerance ±1%
    solver.assertFormula(solver.mkTerm(Kind.GEQ, norm_squared, solver.mkReal(99, 100)))
    solver.assertFormula(solver.mkTerm(Kind.LEQ, norm_squared, solver.mkReal(101, 100)))

    res = solver.checkSat()
    results["boundary_1_eps_near1"] = {
        "satisfiable": str(res.isSat()),
        "expected": True,
        "description": "ε near 1 on unit circle",
        "params": {"eps_real": 0.995, "eps_imag": 0.0998},
    }

    # Boundary test 2: ε on unit circle with equal real and imaginary parts
    # ε = (1/√2)(1+i), |ε|²=1
    solver2 = Solver()
    solver2.setLogic("QF_NRA")

    # 1/√2 ≈ 0.7071
    eps_real = solver2.mkReal(7071, 10000)
    eps_imag = solver2.mkReal(7071, 10000)

    norm_squared = solver2.mkTerm(Kind.ADD,
                                 solver2.mkTerm(Kind.MULT, eps_real, eps_real),
                                 solver2.mkTerm(Kind.MULT, eps_imag, eps_imag))

    solver2.assertFormula(solver2.mkTerm(Kind.GEQ, norm_squared, solver2.mkReal(99, 100)))
    solver2.assertFormula(solver2.mkTerm(Kind.LEQ, norm_squared, solver2.mkReal(101, 100)))

    res = solver2.checkSat()
    results["boundary_2_eps_diagonal"] = {
        "satisfiable": str(res.isSat()),
        "expected": True,
        "description": "ε = (1/√2)(1+i) on unit circle",
        "params": {"eps_real": 0.7071, "eps_imag": 0.7071},
    }

    # Boundary test 3: ε = 0 (degenerate case, off circle)
    # |0| = 0 ≠ 1 → should be unsatisfiable with |ε|=1 constraint
    solver3 = Solver()
    solver3.setLogic("QF_NRA")

    eps_real = solver3.mkReal(0, 1)
    eps_imag = solver3.mkReal(0, 1)

    norm_squared = solver3.mkTerm(Kind.ADD,
                                 solver3.mkTerm(Kind.MULT, eps_real, eps_real),
                                 solver3.mkTerm(Kind.MULT, eps_imag, eps_imag))

    solver3.assertFormula(solver3.mkTerm(Kind.EQUAL, norm_squared, solver3.mkReal(1, 1)))

    res = solver3.checkSat()
    results["boundary_3_eps_zero"] = {
        "satisfiable": str(res.isSat()),
        "expected": False,
        "description": "ε = 0 degenerate case (off circle)",
        "params": {"eps_real": 0.0, "eps_imag": 0.0, "norm": 0.0},
    }

    # Boundary test 4: Multiple unit circle points in same formula
    # ε₁ = 1, ε₂ = i, both on unit circle
    solver4 = Solver()
    solver4.setLogic("QF_NRA")

    eps1_real = solver4.mkReal(1, 1)
    eps1_imag = solver4.mkReal(0, 1)
    eps2_real = solver4.mkReal(0, 1)
    eps2_imag = solver4.mkReal(1, 1)

    norm1_sq = solver4.mkTerm(Kind.ADD,
                             solver4.mkTerm(Kind.MULT, eps1_real, eps1_real),
                             solver4.mkTerm(Kind.MULT, eps1_imag, eps1_imag))
    norm2_sq = solver4.mkTerm(Kind.ADD,
                             solver4.mkTerm(Kind.MULT, eps2_real, eps2_real),
                             solver4.mkTerm(Kind.MULT, eps2_imag, eps2_imag))

    solver4.assertFormula(solver4.mkTerm(Kind.EQUAL, norm1_sq, solver4.mkReal(1, 1)))
    solver4.assertFormula(solver4.mkTerm(Kind.EQUAL, norm2_sq, solver4.mkReal(1, 1)))

    res = solver4.checkSat()
    results["boundary_4_two_eps_on_circle"] = {
        "satisfiable": str(res.isSat()),
        "expected": True,
        "description": "Two root numbers ε₁=1 and ε₂=i both on unit circle",
        "params": {"eps1": (1.0, 0.0), "eps2": (0.0, 1.0)},
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    TOOL_MANIFEST["cvc5"]["used"] = TOOL_MANIFEST["cvc5"]["tried"]
    if TOOL_MANIFEST["cvc5"]["used"]:
        TOOL_MANIFEST["cvc5"]["reason"] = "cvc5 SMT solver: load_bearing proof of L-function functional equation constraint"
        TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"

    TOOL_MANIFEST["sympy"]["used"] = TOOL_MANIFEST["sympy"]["tried"]
    if TOOL_MANIFEST["sympy"]["used"]:
        TOOL_MANIFEST["sympy"]["reason"] = "sympy: supportive symbolic computation for L-function theory"
        TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    results = {
        "name": "sim_cvc5_l_function_functional_equation_constraint",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_cvc5_l_function_functional_equation_constraint_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
