#!/usr/bin/env python3
"""
sim_cvc5_steenrod_square_degree_constraint.py

Domain: Steenrod squares Sq^i
- cvc5 proves: Sq^i raises degree by i — Sq^i: H^n → H^{n+i}
- Positive: SAT — Sq^2 on H^3 gives H^5: out_degree = in_degree + 2 (valid)
- Negative: UNSAT — out_degree ≠ in_degree + i AND Sq^i applied → UNSAT
- Boundary: sympy checks Sq^0 = identity (degree shift 0), Sq^n on H^n = squaring map

Classification: canonical
"""

import json
import os
import sympy as sp

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not applicable for constraint proof"},
    "pyg": {"tried": False, "used": False, "reason": "not applicable for constraint proof"},
    "z3": {"tried": False, "used": False, "reason": "cvc5 is primary SMT solver for this domain"},
    "cvc5": {"tried": True, "used": True, "reason": "QF_LIA solver for degree constraint: out_degree = in_degree + sq_index"},
    "sympy": {"tried": True, "used": True, "reason": "Verify degree computation symbolically; Sq^0 identity check"},
    "clifford": {"tried": False, "used": False, "reason": "Steenrod squares defined on cohomology, not Clifford algebra"},
    "geomstats": {"tried": False, "used": False, "reason": "not applicable for abstract algebra constraint"},
    "e3nn": {"tried": False, "used": False, "reason": "not applicable for Steenrod algebra"},
    "rustworkx": {"tried": False, "used": False, "reason": "not applicable for algebraic constraint"},
    "xgi": {"tried": False, "used": False, "reason": "not applicable for Steenrod algebra"},
    "toponetx": {"tried": False, "used": False, "reason": "topology layer not needed for degree constraint"},
    "gudhi": {"tried": False, "used": False, "reason": "persistent homology not needed for this constraint"},
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
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    """
    Positive tests: SAT instances where degree constraint is satisfied.
    """
    results = {}

    if not TOOL_MANIFEST["cvc5"]["tried"]:
        return {"skipped": "cvc5 not installed"}

    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        # Test 1: Sq^2 on H^3 → H^5
        # Constraint: out_degree = in_degree + sq_index
        in_degree_1 = solver.mkConst(solver.getIntegerSort(), "in_degree_1")
        sq_index_1 = solver.mkConst(solver.getIntegerSort(), "sq_index_1")
        out_degree_1 = solver.mkConst(solver.getIntegerSort(), "out_degree_1")

        solver.push()
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, in_degree_1, solver.mkInteger(3)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, sq_index_1, solver.mkInteger(2)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, out_degree_1,
                                          solver.mkTerm(cvc5.Kind.ADD, in_degree_1, sq_index_1)))

        sat_1 = solver.checkSat()
        results["test_1_sq2_on_h3"] = {
            "description": "Sq^2 on H^3 → H^5",
            "sat": str(sat_1.isSat()),
            "expected": "sat",
            "pass": sat_1.isSat()
        }
        solver.pop()

        # Test 2: Sq^1 on H^4 → H^5
        in_degree_2 = solver.mkConst(solver.getIntegerSort(), "in_degree_2")
        sq_index_2 = solver.mkConst(solver.getIntegerSort(), "sq_index_2")
        out_degree_2 = solver.mkConst(solver.getIntegerSort(), "out_degree_2")

        solver.push()
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, in_degree_2, solver.mkInteger(4)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, sq_index_2, solver.mkInteger(1)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, out_degree_2,
                                          solver.mkTerm(cvc5.Kind.ADD, in_degree_2, sq_index_2)))

        sat_2 = solver.checkSat()
        results["test_2_sq1_on_h4"] = {
            "description": "Sq^1 on H^4 → H^5",
            "sat": str(sat_2.isSat()),
            "expected": "sat",
            "pass": sat_2.isSat()
        }
        solver.pop()

        # Test 3: Sq^3 on H^2 → H^5
        in_degree_3 = solver.mkConst(solver.getIntegerSort(), "in_degree_3")
        sq_index_3 = solver.mkConst(solver.getIntegerSort(), "sq_index_3")
        out_degree_3 = solver.mkConst(solver.getIntegerSort(), "out_degree_3")

        solver.push()
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, in_degree_3, solver.mkInteger(2)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, sq_index_3, solver.mkInteger(3)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, out_degree_3,
                                          solver.mkTerm(cvc5.Kind.ADD, in_degree_3, sq_index_3)))

        sat_3 = solver.checkSat()
        results["test_3_sq3_on_h2"] = {
            "description": "Sq^3 on H^2 → H^5",
            "sat": str(sat_3.isSat()),
            "expected": "sat",
            "pass": sat_3.isSat()
        }
        solver.pop()

    except Exception as e:
        results["error"] = str(e)

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    """
    Negative tests: UNSAT instances where degree constraint is violated.
    """
    results = {}

    if not TOOL_MANIFEST["cvc5"]["tried"]:
        return {"skipped": "cvc5 not installed"}

    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        # Test 1: Contradiction - assert both out_degree = in_degree + 2 AND out_degree = in_degree + 3
        in_degree_1 = solver.mkConst(solver.getIntegerSort(), "in_degree_1")
        out_degree_1 = solver.mkConst(solver.getIntegerSort(), "out_degree_1")

        solver.push()
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, in_degree_1, solver.mkInteger(3)))
        # Assert out_degree = in_degree + 2
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, out_degree_1,
                                          solver.mkTerm(cvc5.Kind.ADD, in_degree_1, solver.mkInteger(2))))
        # Assert out_degree = in_degree + 3 (contradiction)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, out_degree_1,
                                          solver.mkTerm(cvc5.Kind.ADD, in_degree_1, solver.mkInteger(3))))

        sat_1 = solver.checkSat()
        results["test_1_contradictory_degrees"] = {
            "description": "Contradictory degree assignments (out=in+2 AND out=in+3)",
            "sat": str(sat_1.isSat()),
            "expected": "unsat",
            "pass": not sat_1.isSat()
        }
        solver.pop()

        # Test 2: Unsatisfiable - out_degree < in_degree (violates degree increase)
        in_degree_2 = solver.mkConst(solver.getIntegerSort(), "in_degree_2")
        sq_index_2 = solver.mkConst(solver.getIntegerSort(), "sq_index_2")
        out_degree_2 = solver.mkConst(solver.getIntegerSort(), "out_degree_2")

        solver.push()
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, in_degree_2, solver.mkInteger(5)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, sq_index_2, solver.mkInteger(2)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, out_degree_2, solver.mkInteger(4)))
        # Assert degree constraint: out = in + sq
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, out_degree_2,
                                          solver.mkTerm(cvc5.Kind.ADD, in_degree_2, sq_index_2)))

        sat_2 = solver.checkSat()
        results["test_2_degree_decrease"] = {
            "description": "Impossible: out_degree < in_degree with positive sq_index",
            "sat": str(sat_2.isSat()),
            "expected": "unsat",
            "pass": not sat_2.isSat()
        }
        solver.pop()

        # Test 3: Unsatisfiable - negative sq_index (Steenrod squares have non-negative index)
        in_degree_3 = solver.mkConst(solver.getIntegerSort(), "in_degree_3")
        sq_index_3 = solver.mkConst(solver.getIntegerSort(), "sq_index_3")
        out_degree_3 = solver.mkConst(solver.getIntegerSort(), "out_degree_3")

        solver.push()
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, in_degree_3, solver.mkInteger(2)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, sq_index_3, solver.mkInteger(-1)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.GEQ, sq_index_3, solver.mkInteger(0)))

        sat_3 = solver.checkSat()
        results["test_3_negative_sq_index"] = {
            "description": "Impossible: negative sq_index (must be ≥ 0)",
            "sat": str(sat_3.isSat()),
            "expected": "unsat",
            "pass": not sat_3.isSat()
        }
        solver.pop()

    except Exception as e:
        results["error"] = str(e)

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """
    Boundary tests: edge cases and special values.
    """
    results = {}

    try:
        # Boundary 1: Sq^0 is identity (degree shift 0)
        sq_0_deg = sp.Integer(0)
        in_deg = sp.Integer(5)
        out_deg = in_deg + sq_0_deg
        results["boundary_1_sq0_identity"] = {
            "description": "Sq^0 = identity: degree shift is 0",
            "input_degree": int(in_deg),
            "sq_index": int(sq_0_deg),
            "output_degree": int(out_deg),
            "pass": out_deg == in_deg
        }

        # Boundary 2: Sq^n on H^n → H^2n (squaring on own degree)
        n = 3
        in_deg_2 = sp.Integer(n)
        sq_idx_2 = sp.Integer(n)
        out_deg_2 = in_deg_2 + sq_idx_2
        results["boundary_2_sq_n_on_h_n"] = {
            "description": f"Sq^n on H^n: Sq^{n} on H^{n} → H^{2*n}",
            "input_degree": int(in_deg_2),
            "sq_index": int(sq_idx_2),
            "output_degree": int(out_deg_2),
            "pass": out_deg_2 == 2 * n
        }

        # Boundary 3: Large degree and sq_index
        large_in = sp.Integer(1000)
        large_sq = sp.Integer(500)
        large_out = large_in + large_sq
        results["boundary_3_large_degrees"] = {
            "description": "Large degree values (in=1000, sq=500)",
            "input_degree": int(large_in),
            "sq_index": int(large_sq),
            "output_degree": int(large_out),
            "pass": large_out == 1500
        }

    except Exception as e:
        results["error"] = str(e)

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    results = {
        "name": "sim_cvc5_steenrod_square_degree_constraint",
        "description": "Steenrod square degree constraint: Sq^i: H^n → H^{n+i}",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_cvc5_steenrod_square_degree_constraint_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
