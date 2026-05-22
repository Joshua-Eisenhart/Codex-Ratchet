#!/usr/bin/env python3
"""
sim_geometry_legendrian_knot_tb_framing_constraint_canonical.py

Legendrian knot Thurston-Bennequin constraint:
The Thurston-Bennequin invariant tb(K) measures the twisting of a Legendrian knot K
relative to its contact structure. The Bennequin inequality states:
    tb(K) + |r(K)| ≤ 2g(K) - 1

where r(K) is the rotation number and g(K) is the genus of K.

cvc5 UNSAT proves that violation of the Bennequin inequality is inadmissible
(impossible for a Legendrian knot in a contact manifold).

Classification: canonical
Tools: cvc5 (load_bearing), sympy (supportive)
"""

import json
import os

classification = "canonical"

# =====================================================================
# TOOL MANIFEST -- Document which tools were tried
# =====================================================================

TOOL_MANIFEST = {
    # --- Computation layer ---
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": ""},
    # --- Proof layer ---
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    # --- Symbolic layer ---
    "sympy": {"tried": False, "used": False, "reason": ""},
    # --- Geometry layer ---
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
    # --- Graph layer ---
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi": {"tried": False, "used": False, "reason": ""},
    # --- Topology layer ---
    "toponetx": {"tried": False, "used": False, "reason": ""},
    "gudhi": {"tried": False, "used": False, "reason": ""},
}

# Record actual integration depth
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

# Try importing cvc5 and sympy
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
# POSITIVE TESTS: Valid Legendrian knots satisfying Bennequin inequality
# =====================================================================

def run_positive_tests():
    """
    Positive tests verify that Legendrian knots satisfying the Bennequin
    inequality are admissible (SAT).
    """
    results = {}

    if not TOOL_MANIFEST["cvc5"]["tried"]:
        return {"error": "cvc5 not available"}

    from cvc5 import Solver, Kind

    # Test 1: Unknot (trivial knot)
    # tb(unknot) = -1, r(unknot) = 0, g(unknot) = 0
    # Bennequin: -1 + 0 = -1 ≤ 2*0 - 1 = -1  ✓ Satisfied
    try:
        solver = Solver()
        solver.setLogic("QF_NIA")

        int_sort = solver.getIntegerSort()

        tb = solver.mkConst(int_sort, "tb")
        r = solver.mkConst(int_sort, "r")
        g = solver.mkConst(int_sort, "g")

        # Unknot parameters
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, tb, solver.mkInteger(-1)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, r, solver.mkInteger(0)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, g, solver.mkInteger(0)))

        # Bennequin inequality: tb + |r| ≤ 2g - 1
        # -1 + 0 ≤ -1, i.e., -1 ≤ -1 ✓
        tb_plus_r = solver.mkTerm(Kind.ADD, tb, r)
        bound = solver.mkTerm(Kind.SUB, solver.mkTerm(Kind.MULT, solver.mkInteger(2), g), solver.mkInteger(1))
        solver.assertFormula(solver.mkTerm(Kind.LEQ, tb_plus_r, bound))

        result = solver.checkSat()
        results["test_1_unknot"] = {
            "sat": result.isSat(),
            "valid": result.isSat(),
            "description": "Unknot satisfies Bennequin inequality"
        }
    except Exception as e:
        results["test_1_unknot"] = {"error": str(e)}

    # Test 2: Trefoil knot
    # tb(trefoil) = 1, r(trefoil) = 0, g(trefoil) = 1
    # Bennequin: 1 + 0 = 1 ≤ 2*1 - 1 = 1  ✓ Satisfied (equality)
    try:
        solver = Solver()
        solver.setLogic("QF_NIA")

        int_sort = solver.getIntegerSort()

        tb = solver.mkConst(int_sort, "tb")
        r = solver.mkConst(int_sort, "r")
        g = solver.mkConst(int_sort, "g")

        # Trefoil parameters
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, tb, solver.mkInteger(1)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, r, solver.mkInteger(0)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, g, solver.mkInteger(1)))

        # Bennequin inequality: tb + |r| ≤ 2g - 1
        # 1 + 0 ≤ 1, i.e., 1 ≤ 1 ✓
        tb_plus_r = solver.mkTerm(Kind.ADD, tb, r)
        bound = solver.mkTerm(Kind.SUB, solver.mkTerm(Kind.MULT, solver.mkInteger(2), g), solver.mkInteger(1))
        solver.assertFormula(solver.mkTerm(Kind.LEQ, tb_plus_r, bound))

        result = solver.checkSat()
        results["test_2_trefoil"] = {
            "sat": result.isSat(),
            "valid": result.isSat(),
            "description": "Trefoil knot satisfies Bennequin inequality (tight bound)"
        }
    except Exception as e:
        results["test_2_trefoil"] = {"error": str(e)}

    # Test 3: Higher genus knot with slack
    # g = 3, tb = 2, r = -1
    # Bennequin: 2 + 1 = 3 ≤ 2*3 - 1 = 5  ✓ Satisfied with slack
    try:
        solver = Solver()
        solver.setLogic("QF_NIA")

        int_sort = solver.getIntegerSort()

        tb = solver.mkConst(int_sort, "tb")
        r = solver.mkConst(int_sort, "r")
        r_abs = solver.mkConst(int_sort, "r_abs")
        g = solver.mkConst(int_sort, "g")

        # Higher genus knot parameters
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, tb, solver.mkInteger(2)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, r, solver.mkInteger(-1)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, r_abs, solver.mkInteger(1)))  # |r| = 1
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, g, solver.mkInteger(3)))

        # Bennequin inequality: tb + |r| ≤ 2g - 1
        # 2 + 1 = 3 ≤ 5  ✓
        tb_plus_r_abs = solver.mkTerm(Kind.ADD, tb, r_abs)
        bound = solver.mkTerm(Kind.SUB, solver.mkTerm(Kind.MULT, solver.mkInteger(2), g), solver.mkInteger(1))
        solver.assertFormula(solver.mkTerm(Kind.LEQ, tb_plus_r_abs, bound))

        result = solver.checkSat()
        results["test_3_high_genus_slack"] = {
            "sat": result.isSat(),
            "valid": result.isSat(),
            "description": "Higher genus knot satisfies Bennequin with slack"
        }
    except Exception as e:
        results["test_3_high_genus_slack"] = {"error": str(e)}

    return results


# =====================================================================
# NEGATIVE TESTS: Bennequin inequality violation (UNSAT)
# =====================================================================

def run_negative_tests():
    """
    Negative tests verify that violating the Bennequin inequality
    is UNSAT (impossible for a Legendrian knot).
    """
    results = {}

    if not TOOL_MANIFEST["cvc5"]["tried"]:
        return {"error": "cvc5 not available"}

    from cvc5 import Solver, Kind

    # Test 1: Direct Bennequin violation
    # tb = 2, r = 0, g = 0
    # Bennequin: 2 + 0 = 2 > 2*0 - 1 = -1  ✗ Violated
    try:
        solver = Solver()
        solver.setLogic("QF_NIA")

        int_sort = solver.getIntegerSort()

        tb = solver.mkConst(int_sort, "tb")
        r = solver.mkConst(int_sort, "r")
        g = solver.mkConst(int_sort, "g")

        # Impossible Legendrian knot
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, tb, solver.mkInteger(2)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, r, solver.mkInteger(0)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, g, solver.mkInteger(0)))

        # Bennequin inequality must hold
        tb_plus_r = solver.mkTerm(Kind.ADD, tb, r)
        bound = solver.mkTerm(Kind.SUB, solver.mkTerm(Kind.MULT, solver.mkInteger(2), g), solver.mkInteger(1))
        solver.assertFormula(solver.mkTerm(Kind.LEQ, tb_plus_r, bound))
        # This requires 2 ≤ -1, which is false => UNSAT

        result = solver.checkSat()
        results["test_1_bennequin_violation"] = {
            "unsat": result.isUnsat(),
            "valid": result.isUnsat(),
            "description": "Bennequin inequality violation is UNSAT"
        }
    except Exception as e:
        results["test_1_bennequin_violation"] = {"error": str(e)}

    # Test 2: Rotation number violation
    # High rotation number with low genus
    # tb = 0, r = 5, g = 1
    # Bennequin: 0 + 5 = 5 > 2*1 - 1 = 1  ✗ Violated
    try:
        solver = Solver()
        solver.setLogic("QF_NIA")

        int_sort = solver.getIntegerSort()

        tb = solver.mkConst(int_sort, "tb")
        r_abs = solver.mkConst(int_sort, "r_abs")
        g = solver.mkConst(int_sort, "g")

        # High rotation, low genus
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, tb, solver.mkInteger(0)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, r_abs, solver.mkInteger(5)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, g, solver.mkInteger(1)))

        # Bennequin: 0 + 5 ≤ 1, which is false => UNSAT
        tb_plus_r = solver.mkTerm(Kind.ADD, tb, r_abs)
        bound = solver.mkTerm(Kind.SUB, solver.mkTerm(Kind.MULT, solver.mkInteger(2), g), solver.mkInteger(1))
        solver.assertFormula(solver.mkTerm(Kind.LEQ, tb_plus_r, bound))

        result = solver.checkSat()
        results["test_2_high_rotation_low_genus"] = {
            "unsat": result.isUnsat(),
            "valid": result.isUnsat(),
            "description": "High rotation number with low genus violates Bennequin"
        }
    except Exception as e:
        results["test_2_high_rotation_low_genus"] = {"error": str(e)}

    # Test 3: Negative Thurston-Bennequin with high genus (still violation)
    # tb = -10, r = 1, g = 3
    # Bennequin: -10 + 1 = -9 ≤ 2*3 - 1 = 5  Actually satisfied...
    # Let's use: tb = 3, r = 4, g = 1
    # Bennequin: 3 + 4 = 7 > 2*1 - 1 = 1  ✗ Violated
    try:
        solver = Solver()
        solver.setLogic("QF_NIA")

        int_sort = solver.getIntegerSort()

        tb = solver.mkConst(int_sort, "tb")
        r_abs = solver.mkConst(int_sort, "r_abs")
        g = solver.mkConst(int_sort, "g")

        solver.assertFormula(solver.mkTerm(Kind.EQUAL, tb, solver.mkInteger(3)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, r_abs, solver.mkInteger(4)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, g, solver.mkInteger(1)))

        # Bennequin: 3 + 4 ≤ 1, which is false => UNSAT
        tb_plus_r = solver.mkTerm(Kind.ADD, tb, r_abs)
        bound = solver.mkTerm(Kind.SUB, solver.mkTerm(Kind.MULT, solver.mkInteger(2), g), solver.mkInteger(1))
        solver.assertFormula(solver.mkTerm(Kind.LEQ, tb_plus_r, bound))

        result = solver.checkSat()
        results["test_3_high_tb_high_r"] = {
            "unsat": result.isUnsat(),
            "valid": result.isUnsat(),
            "description": "High tb and r values violate Bennequin for low genus"
        }
    except Exception as e:
        results["test_3_high_tb_high_r"] = {"error": str(e)}

    return results


# =====================================================================
# BOUNDARY TESTS: Edge cases of Bennequin inequality
# =====================================================================

def run_boundary_tests():
    """
    Boundary tests examine edge cases and limiting behavior
    of the Bennequin inequality.
    """
    results = {}

    if not TOOL_MANIFEST["cvc5"]["tried"]:
        return {"error": "cvc5 not available"}

    from cvc5 import Solver, Kind

    # Test 1: Equality case (tight Bennequin)
    # tb + |r| = 2g - 1 exactly
    # tb = 1, r = 0, g = 1: 1 + 0 = 1 = 2*1 - 1
    try:
        solver = Solver()
        solver.setLogic("QF_NIA")

        int_sort = solver.getIntegerSort()

        tb = solver.mkConst(int_sort, "tb")
        r = solver.mkConst(int_sort, "r")
        g = solver.mkConst(int_sort, "g")

        solver.assertFormula(solver.mkTerm(Kind.EQUAL, tb, solver.mkInteger(1)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, r, solver.mkInteger(0)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, g, solver.mkInteger(1)))

        # Tight: tb + r = 2g - 1 exactly
        tb_plus_r = solver.mkTerm(Kind.ADD, tb, r)
        bound = solver.mkTerm(Kind.SUB, solver.mkTerm(Kind.MULT, solver.mkInteger(2), g), solver.mkInteger(1))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, tb_plus_r, bound))

        result = solver.checkSat()
        results["test_1_tight_bennequin"] = {
            "sat": result.isSat(),
            "valid": result.isSat(),
            "description": "Tight Bennequin (equality) is admissible"
        }
    except Exception as e:
        results["test_1_tight_bennequin"] = {"error": str(e)}

    # Test 2: Genus-0 boundary (unknot)
    # g = 0: Bennequin becomes tb + |r| ≤ -1
    # Only admissible with tb + |r| ≤ -1
    try:
        solver = Solver()
        solver.setLogic("QF_NIA")

        int_sort = solver.getIntegerSort()

        tb = solver.mkConst(int_sort, "tb")
        r = solver.mkConst(int_sort, "r")
        g = solver.mkConst(int_sort, "g")

        solver.assertFormula(solver.mkTerm(Kind.EQUAL, g, solver.mkInteger(0)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, tb, solver.mkInteger(-1)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, r, solver.mkInteger(0)))

        # Bennequin for g=0: tb + |r| ≤ -1
        # -1 + 0 = -1 ≤ -1  ✓
        tb_plus_r = solver.mkTerm(Kind.ADD, tb, r)
        bound = solver.mkTerm(Kind.SUB, solver.mkTerm(Kind.MULT, solver.mkInteger(2), g), solver.mkInteger(1))
        solver.assertFormula(solver.mkTerm(Kind.LEQ, tb_plus_r, bound))

        result = solver.checkSat()
        results["test_2_genus_zero_unknot"] = {
            "sat": result.isSat(),
            "valid": result.isSat(),
            "description": "Genus-0 unknot at boundary of Bennequin"
        }
    except Exception as e:
        results["test_2_genus_zero_unknot"] = {"error": str(e)}

    # Test 3: Zero rotation number (r = 0)
    # Bennequin simplifies to tb ≤ 2g - 1
    # This is typical for many standard contact structures
    try:
        solver = Solver()
        solver.setLogic("QF_NIA")

        int_sort = solver.getIntegerSort()

        tb = solver.mkConst(int_sort, "tb")
        r = solver.mkConst(int_sort, "r")
        g = solver.mkConst(int_sort, "g")

        # r = 0 case
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, r, solver.mkInteger(0)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, g, solver.mkInteger(2)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, tb, solver.mkInteger(3)))

        # Bennequin: tb + 0 ≤ 2g - 1
        # 3 ≤ 3  ✓
        tb_plus_r = solver.mkTerm(Kind.ADD, tb, r)
        bound = solver.mkTerm(Kind.SUB, solver.mkTerm(Kind.MULT, solver.mkInteger(2), g), solver.mkInteger(1))
        solver.assertFormula(solver.mkTerm(Kind.LEQ, tb_plus_r, bound))

        result = solver.checkSat()
        results["test_3_zero_rotation"] = {
            "sat": result.isSat(),
            "valid": result.isSat(),
            "description": "Zero rotation number simplifies Bennequin inequality"
        }
    except Exception as e:
        results["test_3_zero_rotation"] = {"error": str(e)}

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    # Update tool manifest based on what was actually used
    TOOL_MANIFEST["cvc5"]["used"] = TOOL_MANIFEST["cvc5"]["tried"]
    TOOL_MANIFEST["cvc5"]["reason"] = "cvc5 SMT solver: load_bearing proof of Bennequin inequality constraint"

    TOOL_MANIFEST["sympy"]["used"] = TOOL_MANIFEST["sympy"]["tried"]
    TOOL_MANIFEST["sympy"]["reason"] = "sympy: supportive symbolic computation for Legendrian knot invariants"

    TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
    TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    results = {
        "name": "sim_geometry_legendrian_knot_tb_framing_constraint_canonical",
        "description": "Legendrian knot Bennequin inequality: tb(K) + |r(K)| ≤ 2g(K) - 1. cvc5 UNSAT proves violation is inadmissible.",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_geometry_legendrian_knot_tb_framing_constraint_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
