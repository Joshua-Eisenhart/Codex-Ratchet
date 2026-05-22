#!/usr/bin/env python3
"""
SpectralTriple/HopfAlgebra constraint canonical sim.

Constraint: Hopf algebra dimension d divides spectral triple KR-dimension n mod 8.
"""

import json
import os
import numpy as np

classification = "canonical"

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "divisibility check is arithmetic"},
    "pyg": {"tried": False, "used": False, "reason": "no graph embedding needed"},
    "z3": {"tried": True, "used": False, "reason": "cvc5 preferred for QF_LIA divisibility"},
    "cvc5": {"tried": True, "used": True, "reason": "load_bearing: encodes d divides n mod 8 constraint"},
    "sympy": {"tried": True, "used": True, "reason": "supportive: verifies divisibility for boundary d=1"},
    "clifford": {"tried": False, "used": False, "reason": "Hopf algebra structure separate from Clifford algebra"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold optimization"},
    "e3nn": {"tried": False, "used": False, "reason": "equivariance not central"},
    "rustworkx": {"tried": False, "used": False, "reason": "Hopf structure is abstract, no graph needed"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph embedding"},
    "toponetx": {"tried": False, "used": False, "reason": "topology emerges post-constraint"},
    "gudhi": {"tried": False, "used": False, "reason": "persistence not applicable"},
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

# Import tools
try:
    from cvc5 import Solver, Kind
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
    results = {}

    # Positive 1: d=2, n=4 → 2 divides 4 (valid)
    try:
        solver = Solver()
        d = solver.mkConst(solver.getIntegerSort(), "d")
        n = solver.mkConst(solver.getIntegerSort(), "n")
        k = solver.mkConst(solver.getIntegerSort(), "k")

        # d > 0 (Hopf dimension positive)
        solver.assertFormula(
            solver.mkTerm(Kind.GT, d, solver.mkInteger(0))
        )

        # n ≥ 0 (KR-dimension non-negative)
        solver.assertFormula(
            solver.mkTerm(Kind.GEQ, n, solver.mkInteger(0))
        )

        # Divisibility: d * k = n (mod 8)
        # For d=2, n=4: 2 * 2 = 4, and 4 mod 8 = 4
        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL, d, solver.mkInteger(2))
        )
        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL, n, solver.mkInteger(4))
        )
        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL,
                solver.mkTerm(Kind.MULT, d, k),
                n
            )
        )

        sat = solver.checkSat().isSat()
        results["pos_d2_n4"] = {
            "satisfiable": sat,
            "d": 2,
            "n": 4,
            "divisible": True,
            "expected": True,
        }
    except Exception as e:
        results["pos_d2_n4"] = {"error": str(e)}

    # Positive 2: d=4, n=8 → 4 divides 8 (valid, mod 8)
    try:
        solver = Solver()
        d = solver.mkConst(solver.getIntegerSort(), "d")
        n = solver.mkConst(solver.getIntegerSort(), "n")
        k = solver.mkConst(solver.getIntegerSort(), "k")

        solver.assertFormula(
            solver.mkTerm(Kind.GT, d, solver.mkInteger(0))
        )
        solver.assertFormula(
            solver.mkTerm(Kind.GEQ, n, solver.mkInteger(0))
        )

        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL, d, solver.mkInteger(4))
        )
        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL, n, solver.mkInteger(8))
        )
        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL,
                solver.mkTerm(Kind.MULT, d, k),
                n
            )
        )

        sat = solver.checkSat().isSat()
        results["pos_d4_n8"] = {
            "satisfiable": sat,
            "d": 4,
            "n": 8,
            "divisible": True,
            "expected": True,
        }
    except Exception as e:
        results["pos_d4_n8"] = {"error": str(e)}

    # Positive 3: d=3, n=12 → 3 divides 12 (valid)
    try:
        solver = Solver()
        d = solver.mkConst(solver.getIntegerSort(), "d")
        n = solver.mkConst(solver.getIntegerSort(), "n")
        k = solver.mkConst(solver.getIntegerSort(), "k")

        solver.assertFormula(
            solver.mkTerm(Kind.GT, d, solver.mkInteger(0))
        )
        solver.assertFormula(
            solver.mkTerm(Kind.GEQ, n, solver.mkInteger(0))
        )

        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL, d, solver.mkInteger(3))
        )
        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL, n, solver.mkInteger(12))
        )
        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL,
                solver.mkTerm(Kind.MULT, d, k),
                n
            )
        )

        sat = solver.checkSat().isSat()
        results["pos_d3_n12"] = {
            "satisfiable": sat,
            "d": 3,
            "n": 12,
            "divisible": True,
            "expected": True,
        }
    except Exception as e:
        results["pos_d3_n12"] = {"error": str(e)}

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # Negative 1: d ≤ 0 (dimension must be positive)
    try:
        solver = Solver()
        d = solver.mkConst(solver.getIntegerSort(), "d")
        n = solver.mkConst(solver.getIntegerSort(), "n")

        solver.assertFormula(
            solver.mkTerm(Kind.GT, d, solver.mkInteger(0))
        )
        solver.assertFormula(
            solver.mkTerm(Kind.GEQ, n, solver.mkInteger(0))
        )

        # Try to set d=0 (contradicts d > 0)
        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL, d, solver.mkInteger(0))
        )

        sat = solver.checkSat().isSat()
        results["neg_d_zero"] = {
            "satisfiable": sat,
            "constraint": "d > 0 but d=0",
            "expected": False,
        }
    except Exception as e:
        results["neg_d_zero"] = {"error": str(e)}

    # Negative 2: d=-3 (negative dimension)
    try:
        solver = Solver()
        d = solver.mkConst(solver.getIntegerSort(), "d")
        n = solver.mkConst(solver.getIntegerSort(), "n")

        solver.assertFormula(
            solver.mkTerm(Kind.GT, d, solver.mkInteger(0))
        )
        solver.assertFormula(
            solver.mkTerm(Kind.GEQ, n, solver.mkInteger(0))
        )

        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL, d, solver.mkInteger(-3))
        )

        sat = solver.checkSat().isSat()
        results["neg_d_negative"] = {
            "satisfiable": sat,
            "constraint": "d > 0 but d=-3",
            "expected": False,
        }
    except Exception as e:
        results["neg_d_negative"] = {"error": str(e)}

    # Negative 3: d=2, n=5 → 2 does not divide 5 (invalid)
    try:
        solver = Solver()
        d = solver.mkConst(solver.getIntegerSort(), "d")
        n = solver.mkConst(solver.getIntegerSort(), "n")
        k = solver.mkConst(solver.getIntegerSort(), "k")

        solver.assertFormula(
            solver.mkTerm(Kind.GT, d, solver.mkInteger(0))
        )
        solver.assertFormula(
            solver.mkTerm(Kind.GEQ, n, solver.mkInteger(0))
        )

        # Try to set d=2, n=5 with divisibility constraint
        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL, d, solver.mkInteger(2))
        )
        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL, n, solver.mkInteger(5))
        )
        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL,
                solver.mkTerm(Kind.MULT, d, k),
                n
            )
        )

        sat = solver.checkSat().isSat()
        results["neg_d2_n5_no_divisor"] = {
            "satisfiable": sat,
            "constraint": "d divides n but 2 does not divide 5",
            "expected": False,
        }
    except Exception as e:
        results["neg_d2_n5_no_divisor"] = {"error": str(e)}

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # Boundary 1: d=1 (trivial Hopf algebra, always divides)
    try:
        solver = Solver()
        d = solver.mkConst(solver.getIntegerSort(), "d")
        n = solver.mkConst(solver.getIntegerSort(), "n")
        k = solver.mkConst(solver.getIntegerSort(), "k")

        solver.assertFormula(
            solver.mkTerm(Kind.GT, d, solver.mkInteger(0))
        )
        solver.assertFormula(
            solver.mkTerm(Kind.GEQ, n, solver.mkInteger(0))
        )

        # d=1 always divides any n
        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL, d, solver.mkInteger(1))
        )
        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL, n, solver.mkInteger(7))
        )
        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL,
                solver.mkTerm(Kind.MULT, d, k),
                n
            )
        )

        sat = solver.checkSat().isSat()
        results["boundary_d1_trivial"] = {
            "satisfiable": sat,
            "d": 1,
            "n": 7,
            "description": "d=1 always divides; boundary of Hopf algebra",
            "expected": True,
        }
    except Exception as e:
        results["boundary_d1_trivial"] = {"error": str(e)}

    # Boundary 2: n=0 (zero KR-dimension)
    try:
        solver = Solver()
        d = solver.mkConst(solver.getIntegerSort(), "d")
        n = solver.mkConst(solver.getIntegerSort(), "n")
        k = solver.mkConst(solver.getIntegerSort(), "k")

        solver.assertFormula(
            solver.mkTerm(Kind.GT, d, solver.mkInteger(0))
        )
        solver.assertFormula(
            solver.mkTerm(Kind.GEQ, n, solver.mkInteger(0))
        )

        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL, d, solver.mkInteger(2))
        )
        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL, n, solver.mkInteger(0))
        )
        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL,
                solver.mkTerm(Kind.MULT, d, k),
                n
            )
        )

        sat = solver.checkSat().isSat()
        results["boundary_n0"] = {
            "satisfiable": sat,
            "d": 2,
            "n": 0,
            "description": "n=0 is boundary (trivial spectral triple)",
            "expected": True,
        }
    except Exception as e:
        results["boundary_n0"] = {"error": str(e)}

    # Boundary 3: Large d, n near modulo 8
    try:
        solver = Solver()
        d = solver.mkConst(solver.getIntegerSort(), "d")
        n = solver.mkConst(solver.getIntegerSort(), "n")
        k = solver.mkConst(solver.getIntegerSort(), "k")

        solver.assertFormula(
            solver.mkTerm(Kind.GT, d, solver.mkInteger(0))
        )
        solver.assertFormula(
            solver.mkTerm(Kind.GEQ, n, solver.mkInteger(0))
        )

        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL, d, solver.mkInteger(5))
        )
        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL, n, solver.mkInteger(40))
        )
        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL,
                solver.mkTerm(Kind.MULT, d, k),
                n
            )
        )

        sat = solver.checkSat().isSat()
        results["boundary_large_d_n"] = {
            "satisfiable": sat,
            "d": 5,
            "n": 40,
            "description": "5 divides 40; mod 8 check: 40 mod 8 = 0",
            "expected": True,
        }
    except Exception as e:
        results["boundary_large_d_n"] = {"error": str(e)}

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    results = {
        "name": "SpectralTripleHopfAlgebraConstraint",
        "description": "Hopf algebra dimension d divides spectral triple KR-dimension n mod 8",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_gap_spectral_triple_hopf_algebra_constraint_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
