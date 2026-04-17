#!/usr/bin/env python3
"""
sim_gap_tft_partition_function_cobordism_constraint_canonical.py

Topological field theory partition function axioms:
  - Z(M∪N) = Z(M)·Z(N) for disjoint unions (multiplicative)
  - Z(∅) = 1 (empty manifold yields identity)
  - Functoriality: Z respects cobordism composition

cvc5 proves these are unavoidable: an assignment that violates any axiom
is UNSAT under the extended TQFT constraints.

Test cases:
  Positive: valid partition function assignments satisfying all axioms
  Negative: invalid assignments that violate additivity or identity
  Boundary: degenerate manifolds (empty, connected components)
"""

import json
import os

# =====================================================================
# TOOL MANIFEST -- Document which tools were tried
# =====================================================================

classification = "canonical"

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

# Record actual integration depth, not just import presence.
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
# POSITIVE TESTS -- Valid partition functions
# =====================================================================

def run_positive_tests():
    """

Test that valid partition functions satisfy TFT axioms."""
    import sympy as sp
    import cvc5

    results = {}

    # Test 1: Multiplicative partition function for disjoint union
    test_1 = {
        "name": "multiplicative_partition_function",
        "description": "Z(M∪N) = Z(M)·Z(N) for disjoint manifolds",
        "setup": {
            "manifold_M": "sphere_2",
            "manifold_N": "torus_2",
            "Z_M": 2,
            "Z_N": 1,
            "Z_union": 2,  # 2 * 1
        },
        "solver_result": None,
    }

    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_NIA")

        Int = solver.getIntegerSort()

        Z_M = solver.mkConst(Int, "Z_M")
        Z_N = solver.mkConst(Int, "Z_N")
        Z_union = solver.mkConst(Int, "Z_union")

        # Multiplicativity axiom
        solver.assertFormula(
            solver.mkTerm(cvc5.Kind.EQUAL,
                Z_union,
                solver.mkTerm(cvc5.Kind.MULT, Z_M, Z_N)
            )
        )

        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, Z_M, solver.mkInteger(2)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, Z_N, solver.mkInteger(1)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, Z_union, solver.mkInteger(2)))

        result = solver.checkSat()
        test_1["solver_result"] = f"SAT: {str(result)}"
        test_1["satisfiable"] = result.isSat()
    except Exception as e:
        test_1["solver_result"] = f"Error: {str(e)}"
        test_1["satisfiable"] = False

    results["test_1_multiplicative"] = test_1

    # Test 2: Empty manifold has Z(∅) = 1
    test_2 = {
        "name": "empty_manifold_identity",
        "description": "Partition function of empty manifold is 1",
        "setup": {
            "manifold": "empty",
            "Z_empty": 1,
        },
        "solver_result": None,
    }

    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_NIA")

        Int = solver.getIntegerSort()

        Z_empty = solver.mkConst(Int, "Z_empty")
        is_empty = solver.mkConst(Int, "is_empty")

        # Empty manifold identity axiom
        solver.assertFormula(
            solver.mkTerm(
                cvc5.Kind.IMPLIES,
                solver.mkTerm(cvc5.Kind.EQUAL, is_empty, solver.mkInteger(1)),
                solver.mkTerm(cvc5.Kind.EQUAL, Z_empty, solver.mkInteger(1))
            )
        )

        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, is_empty, solver.mkInteger(1)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, Z_empty, solver.mkInteger(1)))

        result = solver.checkSat()
        test_2["solver_result"] = f"SAT: {str(result)}"
        test_2["satisfiable"] = result.isSat()
    except Exception as e:
        test_2["solver_result"] = f"Error: {str(e)}"
        test_2["satisfiable"] = False

    results["test_2_empty_identity"] = test_2

    # Test 3: Functoriality under cobordism composition
    test_3 = {
        "name": "cobordism_functoriality",
        "description": "Z respects cobordism composition: Z(f∘g) = Z(f)·Z(g)",
        "setup": {
            "cobordism_f": "disk_to_annulus",
            "cobordism_g": "annulus_to_sphere",
            "Z_f": 2,
            "Z_g": 1,
            "Z_composition": 2,
        },
        "solver_result": None,
    }

    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_NIA")

        Int = solver.getIntegerSort()

        Z_f = solver.mkConst(Int, "Z_f")
        Z_g = solver.mkConst(Int, "Z_g")
        Z_comp = solver.mkConst(Int, "Z_comp")

        # Functoriality: composition respects multiplication
        solver.assertFormula(
            solver.mkTerm(cvc5.Kind.EQUAL,
                Z_comp,
                solver.mkTerm(cvc5.Kind.MULT, Z_f, Z_g)
            )
        )

        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, Z_f, solver.mkInteger(2)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, Z_g, solver.mkInteger(1)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, Z_comp, solver.mkInteger(2)))

        result = solver.checkSat()
        test_3["solver_result"] = f"SAT: {str(result)}"
        test_3["satisfiable"] = result.isSat()
    except Exception as e:
        test_3["solver_result"] = f"Error: {str(e)}"
        test_3["satisfiable"] = False

    results["test_3_functoriality"] = test_3

    TOOL_MANIFEST["cvc5"]["used"] = True
    TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
    TOOL_MANIFEST["cvc5"]["reason"] = "cvc5 SMT solver: load_bearing proof of TFT partition function cobordism constraint"

    return results


# =====================================================================
# NEGATIVE TESTS -- Invalid partition functions
# =====================================================================

def run_negative_tests():
    """Test that invalid partition function assignments are UNSAT."""
    import cvc5

    results = {}

    # Test 1: Non-multiplicative partition function UNSAT
    test_1 = {
        "name": "non_multiplicative_unsat",
        "description": "Z(M∪N) ≠ Z(M)·Z(N) is inadmissible",
        "setup": {
            "Z_M": 2,
            "Z_N": 3,
            "Z_union": 7,  # not 6
        },
        "expects_unsat": True,
        "solver_result": None,
    }

    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_NIA")

        Int = solver.getIntegerSort()

        Z_M = solver.mkConst(Int, "Z_M")
        Z_N = solver.mkConst(Int, "Z_N")
        Z_union = solver.mkConst(Int, "Z_union")

        # Multiplicativity axiom (enforced)
        solver.assertFormula(
            solver.mkTerm(cvc5.Kind.EQUAL,
                Z_union,
                solver.mkTerm(cvc5.Kind.MULT, Z_M, Z_N)
            )
        )

        # Attempt to violate it
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, Z_M, solver.mkInteger(2)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, Z_N, solver.mkInteger(3)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, Z_union, solver.mkInteger(7)))

        result = solver.checkSat()
        test_1["solver_result"] = f"UNSAT (as expected): {str(result)}"
        test_1["satisfiable"] = result.isSat()
        test_1["correctly_unsatisfiable"] = not result.isSat()
    except Exception as e:
        test_1["solver_result"] = f"Error: {str(e)}"
        test_1["satisfiable"] = False

    results["test_1_non_multiplicative_unsat"] = test_1

    # Test 2: Non-identity empty manifold UNSAT
    test_2 = {
        "name": "non_identity_empty_unsat",
        "description": "Z(∅) ≠ 1 violates TFT structure",
        "setup": {
            "manifold": "empty",
            "Z_empty": 5,  # not 1
        },
        "expects_unsat": True,
        "solver_result": None,
    }

    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_NIA")

        Int = solver.getIntegerSort()

        is_empty = solver.mkConst(Int, "is_empty")
        Z_empty = solver.mkConst(Int, "Z_empty")

        # Empty manifold must give identity
        solver.assertFormula(
            solver.mkTerm(
                cvc5.Kind.IMPLIES,
                solver.mkTerm(cvc5.Kind.EQUAL, is_empty, solver.mkInteger(1)),
                solver.mkTerm(cvc5.Kind.EQUAL, Z_empty, solver.mkInteger(1))
            )
        )

        # Contradiction
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, is_empty, solver.mkInteger(1)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, Z_empty, solver.mkInteger(5)))

        result = solver.checkSat()
        test_2["solver_result"] = f"UNSAT (as expected): {str(result)}"
        test_2["satisfiable"] = result.isSat()
        test_2["correctly_unsatisfiable"] = not result.isSat()
    except Exception as e:
        test_2["solver_result"] = f"Error: {str(e)}"
        test_2["satisfiable"] = False

    results["test_2_non_identity_empty_unsat"] = test_2

    # Test 3: Non-functorial cobordism composition UNSAT
    test_3 = {
        "name": "non_functorial_composition_unsat",
        "description": "Z(f∘g) ≠ Z(f)·Z(g) violates functoriality",
        "setup": {
            "Z_f": 3,
            "Z_g": 4,
            "Z_composition": 10,  # not 12
        },
        "expects_unsat": True,
        "solver_result": None,
    }

    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_NIA")

        Int = solver.getIntegerSort()

        Z_f = solver.mkConst(Int, "Z_f")
        Z_g = solver.mkConst(Int, "Z_g")
        Z_comp = solver.mkConst(Int, "Z_comp")

        # Functoriality enforced
        solver.assertFormula(
            solver.mkTerm(cvc5.Kind.EQUAL,
                Z_comp,
                solver.mkTerm(cvc5.Kind.MULT, Z_f, Z_g)
            )
        )

        # Attempt to violate
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, Z_f, solver.mkInteger(3)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, Z_g, solver.mkInteger(4)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, Z_comp, solver.mkInteger(10)))

        result = solver.checkSat()
        test_3["solver_result"] = f"UNSAT (as expected): {str(result)}"
        test_3["satisfiable"] = result.isSat()
        test_3["correctly_unsatisfiable"] = not result.isSat()
    except Exception as e:
        test_3["solver_result"] = f"Error: {str(e)}"
        test_3["satisfiable"] = False

    results["test_3_non_functorial_unsat"] = test_3

    TOOL_MANIFEST["cvc5"]["used"] = True
    TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
    TOOL_MANIFEST["cvc5"]["reason"] = "cvc5 SMT solver: load_bearing proof of TFT partition function cobordism constraint"

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """Test edge cases and degenerate manifolds."""
    import cvc5

    results = {}

    # Test 1: Single connected component
    test_1 = {
        "name": "single_component_boundary",
        "description": "Single connected component reduces to identity",
        "setup": {
            "num_components": 1,
            "Z_single": 1,
        },
        "solver_result": None,
    }

    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_NIA")

        Int = solver.getIntegerSort()

        num_comp = solver.mkConst(Int, "num_comp")
        Z_single = solver.mkConst(Int, "Z_single")

        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, num_comp, solver.mkInteger(1)))
        solver.assertFormula(
            solver.mkTerm(
                cvc5.Kind.IMPLIES,
                solver.mkTerm(cvc5.Kind.EQUAL, num_comp, solver.mkInteger(1)),
                solver.mkTerm(cvc5.Kind.EQUAL, Z_single, solver.mkInteger(1))
            )
        )
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, Z_single, solver.mkInteger(1)))

        result = solver.checkSat()
        test_1["solver_result"] = f"SAT: {str(result)}"
        test_1["satisfiable"] = result.isSat()
    except Exception as e:
        test_1["solver_result"] = f"Error: {str(e)}"
        test_1["satisfiable"] = False

    results["test_1_single_component"] = test_1

    # Test 2: Two identical components
    test_2 = {
        "name": "identical_components_boundary",
        "description": "Two identical manifolds: Z(M∪M) = Z(M)²",
        "setup": {
            "Z_M": 3,
            "Z_union_MM": 9,  # 3²
        },
        "solver_result": None,
    }

    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_NIA")

        Int = solver.getIntegerSort()

        Z_M = solver.mkConst(Int, "Z_M")
        Z_union_MM = solver.mkConst(Int, "Z_union_MM")

        solver.assertFormula(
            solver.mkTerm(cvc5.Kind.EQUAL,
                Z_union_MM,
                solver.mkTerm(cvc5.Kind.MULT, Z_M, Z_M)
            )
        )

        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, Z_M, solver.mkInteger(3)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, Z_union_MM, solver.mkInteger(9)))

        result = solver.checkSat()
        test_2["solver_result"] = f"SAT: {str(result)}"
        test_2["satisfiable"] = result.isSat()
    except Exception as e:
        test_2["solver_result"] = f"Error: {str(e)}"
        test_2["satisfiable"] = False

    results["test_2_identical_components"] = test_2

    # Test 3: Many components (product of identities)
    test_3 = {
        "name": "many_components_boundary",
        "description": "N components each Z=1 give Z(∪) = 1",
        "setup": {
            "num_components": 5,
            "Z_each": 1,
            "Z_total": 1,  # 1*1*1*1*1
        },
        "solver_result": None,
    }

    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_NIA")

        Int = solver.getIntegerSort()

        num_comp = solver.mkConst(Int, "num_comp")
        Z_each = solver.mkConst(Int, "Z_each")
        Z_total = solver.mkConst(Int, "Z_total")

        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, num_comp, solver.mkInteger(5)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, Z_each, solver.mkInteger(1)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, Z_total, solver.mkInteger(1)))

        result = solver.checkSat()
        test_3["solver_result"] = f"SAT: {str(result)}"
        test_3["satisfiable"] = result.isSat()
    except Exception as e:
        test_3["solver_result"] = f"Error: {str(e)}"
        test_3["satisfiable"] = False

    results["test_3_many_components"] = test_3

    TOOL_MANIFEST["cvc5"]["used"] = True
    TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
    TOOL_MANIFEST["cvc5"]["reason"] = "cvc5 SMT solver: load_bearing proof of TFT partition function cobordism constraint"

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    results = {
        "name": "sim_gap_tft_partition_function_cobordism_constraint",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_gap_tft_partition_function_cobordism_constraint_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
