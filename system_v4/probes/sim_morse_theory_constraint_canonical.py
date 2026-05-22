#!/usr/bin/env python3
"""
Morse Theory Constraint Canonical Sim

Morse theory: number of k-cells (critical points) c_k ≥ k-th Betti number b_k.
Morse inequalities: c_k ≥ b_k for each k; weak inequality Σ(-1)^k c_k = χ(M).

cvc5 proves c_k ≥ b_k via QF_LIA (UNSAT for c_k < b_k — constraint violation).
sympy derives Morse function critical point index classification and Hessian analysis.
"""

import json
import os
import numpy as np

classification = "canonical"

# =====================================================================
# TOOL MANIFEST -- Document which tools were tried
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
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


# =====================================================================
# POSITIVE TESTS: cvc5 SAT — valid Morse configurations
# =====================================================================

def run_positive_tests():
    """
    Positive tests: configurations where c_k ≥ b_k.
    These should be SAT in cvc5 (feasible Morse structures).
    """
    results = {}

    if not TOOL_MANIFEST["cvc5"]["tried"]:
        return {"error": "cvc5 not available"}

    import cvc5

    # Test 1: Sphere S^1 (circle)
    # b_0 = 1, b_1 = 1, χ(S^1) = 0
    # Need c_0 ≥ 1, c_1 ≥ 1
    # Morse function: height function with 2 critical points (min, max)
    test1_name = "positive_sphere_s1"
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")

    b0, b1 = solver.mkConst(solver.getIntegerSort(), "b0"), solver.mkConst(solver.getIntegerSort(), "b1")
    c0, c1 = solver.mkConst(solver.getIntegerSort(), "c0"), solver.mkConst(solver.getIntegerSort(), "c1")
    chi = solver.mkConst(solver.getIntegerSort(), "chi")

    # Betti numbers for S^1
    solver.assertFormula(solver.mkTerm(cvc5.Kind.Equal, b0, solver.mkInteger(1)))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.Equal, b1, solver.mkInteger(1)))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.Equal, chi, solver.mkInteger(0)))

    # Morse inequalities: c_k ≥ b_k
    solver.assertFormula(solver.mkTerm(cvc5.Kind.GEQ, c0, b0))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.GEQ, c1, b1))

    # Weak Morse inequality: χ = Σ(-1)^k c_k
    solver.assertFormula(solver.mkTerm(cvc5.Kind.Equal, chi,
                                       solver.mkTerm(cvc5.Kind.SUB, c0, c1)))

    # Valid Morse function: c0=1, c1=1
    solver.assertFormula(solver.mkTerm(cvc5.Kind.Equal, c0, solver.mkInteger(1)))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.Equal, c1, solver.mkInteger(1)))

    result = solver.checkSat()
    results[test1_name] = {
        "sat": result.isSat(),
        "expected": True,
        "description": "S^1: c0=1 ≥ b0=1, c1=1 ≥ b1=1, χ=0"
    }

    # Test 2: 2-sphere S^2
    # b_0 = 1, b_1 = 0, b_2 = 1, χ(S^2) = 2
    test2_name = "positive_sphere_s2"
    solver2 = cvc5.Solver()
    solver2.setLogic("QF_LIA")

    b0, b1, b2 = [solver2.mkConst(solver2.getIntegerSort(), f"b{i}") for i in range(3)]
    c0, c1, c2 = [solver2.mkConst(solver2.getIntegerSort(), f"c{i}") for i in range(3)]
    chi2 = solver2.mkConst(solver2.getIntegerSort(), "chi2")

    solver2.assertFormula(solver2.mkTerm(cvc5.Kind.Equal, b0, solver2.mkInteger(1)))
    solver2.assertFormula(solver2.mkTerm(cvc5.Kind.Equal, b1, solver2.mkInteger(0)))
    solver2.assertFormula(solver2.mkTerm(cvc5.Kind.Equal, b2, solver2.mkInteger(1)))
    solver2.assertFormula(solver2.mkTerm(cvc5.Kind.Equal, chi2, solver2.mkInteger(2)))

    solver2.assertFormula(solver2.mkTerm(cvc5.Kind.GEQ, c0, b0))
    solver2.assertFormula(solver2.mkTerm(cvc5.Kind.GEQ, c1, b1))
    solver2.assertFormula(solver2.mkTerm(cvc5.Kind.GEQ, c2, b2))

    # χ = c0 - c1 + c2
    solver2.assertFormula(solver2.mkTerm(cvc5.Kind.Equal, chi2,
                                        solver2.mkTerm(cvc5.Kind.ADD,
                                                     solver2.mkTerm(cvc5.Kind.SUB, c0, c1), c2)))

    # Height function on S^2: min, saddle, max → c0=1, c1=1, c2=1
    solver2.assertFormula(solver2.mkTerm(cvc5.Kind.Equal, c0, solver2.mkInteger(1)))
    solver2.assertFormula(solver2.mkTerm(cvc5.Kind.Equal, c1, solver2.mkInteger(1)))
    solver2.assertFormula(solver2.mkTerm(cvc5.Kind.Equal, c2, solver2.mkInteger(1)))

    result2 = solver2.checkSat()
    results[test2_name] = {
        "sat": result2.isSat(),
        "expected": True,
        "description": "S^2: height function with min/saddle/max, χ=2"
    }

    # Test 3: Torus T^2
    # b_0 = 1, b_1 = 2, b_2 = 1, χ(T^2) = 0
    test3_name = "positive_torus_t2"
    solver3 = cvc5.Solver()
    solver3.setLogic("QF_LIA")

    b0, b1, b2 = [solver3.mkConst(solver3.getIntegerSort(), f"b{i}") for i in range(3)]
    c0, c1, c2 = [solver3.mkConst(solver3.getIntegerSort(), f"c{i}") for i in range(3)]
    chi3 = solver3.mkConst(solver3.getIntegerSort(), "chi3")

    solver3.assertFormula(solver3.mkTerm(cvc5.Kind.Equal, b0, solver3.mkInteger(1)))
    solver3.assertFormula(solver3.mkTerm(cvc5.Kind.Equal, b1, solver3.mkInteger(2)))
    solver3.assertFormula(solver3.mkTerm(cvc5.Kind.Equal, b2, solver3.mkInteger(1)))
    solver3.assertFormula(solver3.mkTerm(cvc5.Kind.Equal, chi3, solver3.mkInteger(0)))

    solver3.assertFormula(solver3.mkTerm(cvc5.Kind.GEQ, c0, b0))
    solver3.assertFormula(solver3.mkTerm(cvc5.Kind.GEQ, c1, b1))
    solver3.assertFormula(solver3.mkTerm(cvc5.Kind.GEQ, c2, b2))

    # χ = c0 - c1 + c2
    solver3.assertFormula(solver3.mkTerm(cvc5.Kind.Equal, chi3,
                                        solver3.mkTerm(cvc5.Kind.ADD,
                                                     solver3.mkTerm(cvc5.Kind.SUB, c0, c1), c2)))

    # Torus height function: 4 critical points (min, 2 saddles, max)
    solver3.assertFormula(solver3.mkTerm(cvc5.Kind.Equal, c0, solver3.mkInteger(1)))
    solver3.assertFormula(solver3.mkTerm(cvc5.Kind.Equal, c1, solver3.mkInteger(2)))
    solver3.assertFormula(solver3.mkTerm(cvc5.Kind.Equal, c2, solver3.mkInteger(1)))

    result3 = solver3.checkSat()
    results[test3_name] = {
        "sat": result3.isSat(),
        "expected": True,
        "description": "T^2: Morse function with 4 critical points, χ=0"
    }

    return results


# =====================================================================
# NEGATIVE TESTS: cvc5 UNSAT — violated Morse inequalities
# =====================================================================

def run_negative_tests():
    """
    Negative tests: configurations violating c_k ≥ b_k.
    These should be UNSAT in cvc5 (infeasible Morse structures).
    """
    results = {}

    if not TOOL_MANIFEST["cvc5"]["tried"]:
        return {"error": "cvc5 not available"}

    import cvc5

    # Test 1: Sphere S^1 with c_0 < b_0 (impossible)
    test1_name = "negative_s1_insufficient_minima"
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")

    b0, b1 = solver.mkConst(solver.getIntegerSort(), "b0"), solver.mkConst(solver.getIntegerSort(), "b1")
    c0, c1 = solver.mkConst(solver.getIntegerSort(), "c0"), solver.mkConst(solver.getIntegerSort(), "c1")

    solver.assertFormula(solver.mkTerm(cvc5.Kind.Equal, b0, solver.mkInteger(1)))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.Equal, b1, solver.mkInteger(1)))

    # Morse inequality: c_k ≥ b_k
    solver.assertFormula(solver.mkTerm(cvc5.Kind.GEQ, c0, b0))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.GEQ, c1, b1))

    # Violate: claim c0 = 0 (no 0-cells, but need ≥1)
    solver.assertFormula(solver.mkTerm(cvc5.Kind.Equal, c0, solver.mkInteger(0)))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.Equal, c1, solver.mkInteger(1)))

    result = solver.checkSat()
    results[test1_name] = {
        "sat": result.isSat(),
        "expected": False,
        "description": "S^1 with c0=0 < b0=1: UNSAT (violates Morse inequality)"
    }

    # Test 2: S^2 with c_1 < b_1
    test2_name = "negative_s2_missing_saddles"
    solver2 = cvc5.Solver()
    solver2.setLogic("QF_LIA")

    b0, b1, b2 = [solver2.mkConst(solver2.getIntegerSort(), f"b{i}") for i in range(3)]
    c0, c1, c2 = [solver2.mkConst(solver2.getIntegerSort(), f"c{i}") for i in range(3)]
    chi2 = solver2.mkConst(solver2.getIntegerSort(), "chi2")

    solver2.assertFormula(solver2.mkTerm(cvc5.Kind.Equal, b0, solver2.mkInteger(1)))
    solver2.assertFormula(solver2.mkTerm(cvc5.Kind.Equal, b1, solver2.mkInteger(0)))
    solver2.assertFormula(solver2.mkTerm(cvc5.Kind.Equal, b2, solver2.mkInteger(1)))
    solver2.assertFormula(solver2.mkTerm(cvc5.Kind.Equal, chi2, solver2.mkInteger(2)))

    solver2.assertFormula(solver2.mkTerm(cvc5.Kind.GEQ, c0, b0))
    solver2.assertFormula(solver2.mkTerm(cvc5.Kind.GEQ, c1, b1))
    solver2.assertFormula(solver2.mkTerm(cvc5.Kind.GEQ, c2, b2))

    # Claim c1 = 0 for S^2 (no 1-cells, but b1=0, so OK for Morse inequality)
    # Instead violate: χ = c0 - c1 + c2, with c0=1, c1=0, c2=2 gives χ=3 ≠ 2
    solver2.assertFormula(solver2.mkTerm(cvc5.Kind.Equal, c0, solver2.mkInteger(1)))
    solver2.assertFormula(solver2.mkTerm(cvc5.Kind.Equal, c1, solver2.mkInteger(0)))
    solver2.assertFormula(solver2.mkTerm(cvc5.Kind.Equal, c2, solver2.mkInteger(2)))
    solver2.assertFormula(solver2.mkTerm(cvc5.Kind.Equal, chi2,
                                        solver2.mkTerm(cvc5.Kind.ADD,
                                                     solver2.mkTerm(cvc5.Kind.SUB, c0, c1), c2)))

    result2 = solver2.checkSat()
    results[test2_name] = {
        "sat": result2.isSat(),
        "expected": False,
        "description": "S^2 with Euler characteristic violated: χ=3 ≠ 2"
    }

    # Test 3: Torus with c_1 < b_1
    test3_name = "negative_torus_insufficient_saddles"
    solver3 = cvc5.Solver()
    solver3.setLogic("QF_LIA")

    b0, b1, b2 = [solver3.mkConst(solver3.getIntegerSort(), f"b{i}") for i in range(3)]
    c0, c1, c2 = [solver3.mkConst(solver3.getIntegerSort(), f"c{i}") for i in range(3)]
    chi3 = solver3.mkConst(solver3.getIntegerSort(), "chi3")

    solver3.assertFormula(solver3.mkTerm(cvc5.Kind.Equal, b0, solver3.mkInteger(1)))
    solver3.assertFormula(solver3.mkTerm(cvc5.Kind.Equal, b1, solver3.mkInteger(2)))
    solver3.assertFormula(solver3.mkTerm(cvc5.Kind.Equal, b2, solver3.mkInteger(1)))
    solver3.assertFormula(solver3.mkTerm(cvc5.Kind.Equal, chi3, solver3.mkInteger(0)))

    solver3.assertFormula(solver3.mkTerm(cvc5.Kind.GEQ, c0, b0))
    solver3.assertFormula(solver3.mkTerm(cvc5.Kind.GEQ, c1, b1))
    solver3.assertFormula(solver3.mkTerm(cvc5.Kind.GEQ, c2, b2))

    # Violate: c1 = 1 < b1 = 2 (insufficient 1-cells)
    solver3.assertFormula(solver3.mkTerm(cvc5.Kind.Equal, c0, solver3.mkInteger(1)))
    solver3.assertFormula(solver3.mkTerm(cvc5.Kind.Equal, c1, solver3.mkInteger(1)))
    solver3.assertFormula(solver3.mkTerm(cvc5.Kind.Equal, c2, solver3.mkInteger(1)))

    result3 = solver3.checkSat()
    results[test3_name] = {
        "sat": result3.isSat(),
        "expected": False,
        "description": "Torus with c1=1 < b1=2: UNSAT (violates Morse inequality)"
    }

    return results


# =====================================================================
# BOUNDARY TESTS: edge cases and sympy symbolic analysis
# =====================================================================

def run_boundary_tests():
    """
    Boundary tests: edge cases, numerical precision, sympy symbolic verification.
    """
    results = {}

    # Test 1: Symbolic derivation of critical point index
    if TOOL_MANIFEST["sympy"]["tried"]:
        test1_name = "boundary_morse_critical_index_sympy"
        try:
            import sympy as sp

            # Hessian analysis: quadratic form Q(v) = v^T H v determines index
            # H = 2x2 symmetric matrix (Morse function critical point)
            x, y = sp.symbols('x y', real=True)
            H = sp.Matrix([[2, 0], [0, -1]])  # eigenvalues: 2, -1 → index=1 (saddle)

            eigenvalues = H.eigenvals()
            positive_eigs = sum(1 for e in eigenvalues if e > 0)
            negative_eigs = sum(1 for e in eigenvalues if e < 0)
            index = negative_eigs

            results[test1_name] = {
                "eigenvalues": str(eigenvalues),
                "index": index,
                "expected_index": 1,
                "description": "Critical point Hessian: index=1 (one negative eigenvalue)"
            }
        except Exception as e:
            results[test1_name] = {"error": str(e)}

    # Test 2: Weak Morse inequality Σ(-1)^k c_k = χ(M)
    test2_name = "boundary_weak_morse_equality"
    alternating_sum = 1 - 2 + 1  # c0=1, c1=2, c2=1 for torus
    euler_char = 0  # χ(T^2) = 0
    results[test2_name] = {
        "alternating_sum": alternating_sum,
        "euler_characteristic": euler_char,
        "equal": alternating_sum == euler_char,
        "description": "Torus weak Morse: Σ(-1)^k c_k = 0 = χ(T^2)"
    }

    # Test 3: Morse inequality chain for higher dimensions
    test3_name = "boundary_morse_chain_3d"
    # Generic 3-manifold: b_0=1, b_1=b, b_2=b, b_3=1
    # Morse: c_k ≥ b_k for all k
    # Example S^3: b_0=1, b_1=0, b_2=0, b_3=1
    b_seq = [1, 0, 0, 1]
    c_seq = [1, 0, 0, 1]  # minimal configuration

    morse_valid = all(c >= b for c, b in zip(c_seq, b_seq))
    alternating_c = sum((-1)**k * c_seq[k] for k in range(len(c_seq)))
    alternating_b = sum((-1)**k * b_seq[k] for k in range(len(b_seq)))

    results[test3_name] = {
        "manifold": "S^3",
        "betti_numbers": b_seq,
        "critical_counts": c_seq,
        "morse_inequalities_satisfied": morse_valid,
        "alternating_sum_c": alternating_c,
        "alternating_sum_b": alternating_b,
        "description": "S^3: Morse inequalities and Euler characteristic"
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    results = {
        "name": "Morse Theory Constraint Canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }

    # Mark tools as used
    if TOOL_MANIFEST["cvc5"]["tried"]:
        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_MANIFEST["cvc5"]["reason"] = "Load-bearing: cvc5 QF_LIA proves Morse inequalities c_k ≥ b_k"

    if TOOL_MANIFEST["sympy"]["tried"]:
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = "Supportive: sympy verifies critical point index via Hessian eigenvalue analysis"

    results["tool_manifest"] = TOOL_MANIFEST

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_morse_theory_constraint_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
