#!/usr/bin/env python3
"""
Delzant Polytope Torus Action Constraint Canonical Sim

Tests the Delzant condition: at each vertex, n edge directions must
generate Z^n as a lattice (equivalently, the (n×n) matrix of edge
directions has determinant ±1).

Classification: canonical
Load-bearing tools: cvc5 (constraint satisfaction), sympy (lattice generation)
"""

import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not required for lattice constraints"},
    "pyg": {"tried": False, "used": False, "reason": "not required for lattice constraints"},
    "z3": {"tried": False, "used": False, "reason": "not required for lattice constraints"},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": "not required for lattice constraints"},
    "geomstats": {"tried": False, "used": False, "reason": "not required for lattice constraints"},
    "e3nn": {"tried": False, "used": False, "reason": "not required for lattice constraints"},
    "rustworkx": {"tried": False, "used": False, "reason": "not required for lattice constraints"},
    "xgi": {"tried": False, "used": False, "reason": "not required for lattice constraints"},
    "toponetx": {"tried": False, "used": False, "reason": "not required for lattice constraints"},
    "gudhi": {"tried": False, "used": False, "reason": "not required for lattice constraints"},
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
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    from z3 import *
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
    from clifford import Cl
    TOOL_MANIFEST["clifford"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

try:
    import geomstats
    TOOL_MANIFEST["geomstats"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    import e3nn
    TOOL_MANIFEST["e3nn"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"

try:
    import rustworkx
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

try:
    import xgi
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

try:
    from toponetx.classes import CellComplex
    TOOL_MANIFEST["toponetx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] = "not installed"

try:
    import gudhi
    TOOL_MANIFEST["gudhi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"


# =====================================================================
# POSITIVE TESTS: Valid Delzant vertices
# =====================================================================

def run_positive_tests():
    """
    Positive tests: verify that standard Delzant polytope vertices
    satisfy the lattice generation condition (det = ±1).
    """
    results = {}

    try:
        import cvc5
        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
    except ImportError:
        return {"error": "cvc5 not installed"}

    try:
        import sympy as sp
    except ImportError:
        return {"error": "sympy not installed"}

    # Test 1: Standard 2D simplex vertex with edges (1,0) and (0,1)
    # det([[1,0],[0,1]]) = 1 → generates Z^2 ✓
    solver = cvc5.Solver()
    solver.setLogic("QF_NIA")

    # Edge direction 1: (1, 0)
    e1_0 = solver.mkConst(solver.getIntegerSort(), "e1_0")
    e1_1 = solver.mkConst(solver.getIntegerSort(), "e1_1")

    # Edge direction 2: (0, 1)
    e2_0 = solver.mkConst(solver.getIntegerSort(), "e2_0")
    e2_1 = solver.mkConst(solver.getIntegerSort(), "e2_1")

    # det = e1_0*e2_1 - e1_1*e2_0 = 1*1 - 0*0 = 1
    det_expr = solver.mkTerm(
        cvc5.Kind.SUB,
        solver.mkTerm(cvc5.Kind.MULT, e1_0, e2_1),
        solver.mkTerm(cvc5.Kind.MULT, e1_1, e2_0)
    )

    # Fix edge directions
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, e1_0, solver.mkInteger(1)))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, e1_1, solver.mkInteger(0)))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, e2_0, solver.mkInteger(0)))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, e2_1, solver.mkInteger(1)))

    # Assert det = 1
    constraint = solver.mkTerm(
        cvc5.Kind.EQUAL,
        det_expr,
        solver.mkInteger(1)
    )
    solver.assertFormula(constraint)
    result = solver.checkSat()

    test_1 = {
        "name": "standard_delzant_simplex",
        "description": "Standard 2D simplex vertex with edges (1,0)/(0,1), det=1 (Delzant)",
        "edges": [[1, 0], [0, 1]],
        "cvc5_sat": result.isSat(),
        "passed": result.isSat(),
    }
    results["test_1"] = test_1

    # Test 2: Rotated Delzant vertex with edges (0,1) and (1,-1)
    # det([[0,1],[1,-1]]) = 0*(-1) - 1*1 = -1 → generates Z^2 ✓
    solver2 = cvc5.Solver()
    solver2.setLogic("QF_LIA")

    e1_0_v2 = solver2.mkConst(solver2.getIntegerSort(), "e1_0")
    e1_1_v2 = solver2.mkConst(solver2.getIntegerSort(), "e1_1")
    e2_0_v2 = solver2.mkConst(solver2.getIntegerSort(), "e2_0")
    e2_1_v2 = solver2.mkConst(solver2.getIntegerSort(), "e2_1")

    det_expr2 = solver2.mkTerm(
        cvc5.Kind.SUB,
        solver2.mkTerm(cvc5.Kind.MULT, e1_0_v2, e2_1_v2),
        solver2.mkTerm(cvc5.Kind.MULT, e1_1_v2, e2_0_v2)
    )

    # Edges: (0,1) and (1,-1)
    solver2.assertFormula(solver2.mkTerm(cvc5.Kind.EQUAL, e1_0_v2, solver2.mkInteger(0)))
    solver2.assertFormula(solver2.mkTerm(cvc5.Kind.EQUAL, e1_1_v2, solver2.mkInteger(1)))
    solver2.assertFormula(solver2.mkTerm(cvc5.Kind.EQUAL, e2_0_v2, solver2.mkInteger(1)))
    solver2.assertFormula(solver2.mkTerm(cvc5.Kind.EQUAL, e2_1_v2, solver2.mkInteger(-1)))

    # Assert det = -1
    constraint2 = solver2.mkTerm(
        cvc5.Kind.EQUAL,
        det_expr2,
        solver2.mkInteger(-1)
    )
    solver2.assertFormula(constraint2)
    result2 = solver2.checkSat()

    test_2 = {
        "name": "rotated_delzant_vertex",
        "description": "Delzant vertex with edges (0,1)/(1,-1), det=-1 (generates Z^2)",
        "edges": [[0, 1], [1, -1]],
        "cvc5_sat": result2.isSat(),
        "passed": result2.isSat(),
    }
    results["test_2"] = test_2

    # Test 3: Another Delzant configuration with edges (1,1) and (1,0)
    # det([[1,1],[1,0]]) = 1*0 - 1*1 = -1 → generates Z^2 ✓
    solver3 = cvc5.Solver()
    solver3.setLogic("QF_LIA")

    e1_0_v3 = solver3.mkConst(solver3.getIntegerSort(), "e1_0")
    e1_1_v3 = solver3.mkConst(solver3.getIntegerSort(), "e1_1")
    e2_0_v3 = solver3.mkConst(solver3.getIntegerSort(), "e2_0")
    e2_1_v3 = solver3.mkConst(solver3.getIntegerSort(), "e2_1")

    det_expr3 = solver3.mkTerm(
        cvc5.Kind.SUB,
        solver3.mkTerm(cvc5.Kind.MULT, e1_0_v3, e2_1_v3),
        solver3.mkTerm(cvc5.Kind.MULT, e1_1_v3, e2_0_v3)
    )

    # Edges: (1,1) and (1,0)
    solver3.assertFormula(solver3.mkTerm(cvc5.Kind.EQUAL, e1_0_v3, solver3.mkInteger(1)))
    solver3.assertFormula(solver3.mkTerm(cvc5.Kind.EQUAL, e1_1_v3, solver3.mkInteger(1)))
    solver3.assertFormula(solver3.mkTerm(cvc5.Kind.EQUAL, e2_0_v3, solver3.mkInteger(1)))
    solver3.assertFormula(solver3.mkTerm(cvc5.Kind.EQUAL, e2_1_v3, solver3.mkInteger(0)))

    # Assert det = -1
    constraint3 = solver3.mkTerm(
        cvc5.Kind.EQUAL,
        det_expr3,
        solver3.mkInteger(-1)
    )
    solver3.assertFormula(constraint3)
    result3 = solver3.checkSat()

    test_3 = {
        "name": "delzant_configuration_v3",
        "description": "Delzant vertex with edges (1,1)/(1,0), det=-1",
        "edges": [[1, 1], [1, 0]],
        "cvc5_sat": result3.isSat(),
        "passed": result3.isSat(),
    }
    results["test_3"] = test_3

    return results


# =====================================================================
# NEGATIVE TESTS: Non-Delzant vertices (det ≠ ±1)
# =====================================================================

def run_negative_tests():
    """
    Negative tests: verify that non-Delzant vertices (det ≠ ±1)
    cannot satisfy the Delzant constraint.
    """
    results = {}

    try:
        import cvc5
    except ImportError:
        return {"error": "cvc5 not installed"}

    try:
        import sympy as sp
    except ImportError:
        return {"error": "sympy not installed"}

    # Test 1: Non-Delzant edges (2,0) and (0,1) → det=2
    # Assert det=1 AND these edges simultaneously → UNSAT
    solver = cvc5.Solver()
    solver.setLogic("QF_NIA")

    e1_0 = solver.mkConst(solver.getIntegerSort(), "e1_0")
    e1_1 = solver.mkConst(solver.getIntegerSort(), "e1_1")
    e2_0 = solver.mkConst(solver.getIntegerSort(), "e2_0")
    e2_1 = solver.mkConst(solver.getIntegerSort(), "e2_1")

    det_expr = solver.mkTerm(
        cvc5.Kind.SUB,
        solver.mkTerm(cvc5.Kind.MULT, e1_0, e2_1),
        solver.mkTerm(cvc5.Kind.MULT, e1_1, e2_0)
    )

    # Fix edges: (2,0) and (0,1) → det=2
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, e1_0, solver.mkInteger(2)))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, e1_1, solver.mkInteger(0)))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, e2_0, solver.mkInteger(0)))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, e2_1, solver.mkInteger(1)))

    # Assert det = 1 (Delzant constraint)
    constraint = solver.mkTerm(
        cvc5.Kind.EQUAL,
        det_expr,
        solver.mkInteger(1)
    )
    solver.assertFormula(constraint)
    result = solver.checkSat()

    test_1 = {
        "name": "non_delzant_det_2",
        "description": "Edges (2,0)/(0,1) have det=2, cannot satisfy det=1 (UNSAT)",
        "edges": [[2, 0], [0, 1]],
        "actual_det": 2,
        "cvc5_unsat": not result.isSat(),
        "passed": not result.isSat(),
    }
    results["test_1"] = test_1

    # Test 2: Non-Delzant edges (3,1) and (1,1) → det=2
    solver2 = cvc5.Solver()
    solver2.setLogic("QF_LIA")

    e1_0_v2 = solver2.mkConst(solver2.getIntegerSort(), "e1_0")
    e1_1_v2 = solver2.mkConst(solver2.getIntegerSort(), "e1_1")
    e2_0_v2 = solver2.mkConst(solver2.getIntegerSort(), "e2_0")
    e2_1_v2 = solver2.mkConst(solver2.getIntegerSort(), "e2_1")

    det_expr2 = solver2.mkTerm(
        cvc5.Kind.SUB,
        solver2.mkTerm(cvc5.Kind.MULT, e1_0_v2, e2_1_v2),
        solver2.mkTerm(cvc5.Kind.MULT, e1_1_v2, e2_0_v2)
    )

    solver2.assertFormula(solver2.mkTerm(cvc5.Kind.EQUAL, e1_0_v2, solver2.mkInteger(3)))
    solver2.assertFormula(solver2.mkTerm(cvc5.Kind.EQUAL, e1_1_v2, solver2.mkInteger(1)))
    solver2.assertFormula(solver2.mkTerm(cvc5.Kind.EQUAL, e2_0_v2, solver2.mkInteger(1)))
    solver2.assertFormula(solver2.mkTerm(cvc5.Kind.EQUAL, e2_1_v2, solver2.mkInteger(1)))

    # det = 3*1 - 1*1 = 2, assert det=1 → UNSAT
    constraint2 = solver2.mkTerm(
        cvc5.Kind.EQUAL,
        det_expr2,
        solver2.mkInteger(1)
    )
    solver2.assertFormula(constraint2)
    result2 = solver2.checkSat()

    test_2 = {
        "name": "non_delzant_det_2_v2",
        "description": "Edges (3,1)/(1,1) have det=2, cannot be Delzant (UNSAT)",
        "edges": [[3, 1], [1, 1]],
        "actual_det": 2,
        "cvc5_unsat": not result2.isSat(),
        "passed": not result2.isSat(),
    }
    results["test_2"] = test_2

    # Test 3: Singular matrix (det=0) cannot be Delzant
    solver3 = cvc5.Solver()
    solver3.setLogic("QF_LIA")

    e1_0_v3 = solver3.mkConst(solver3.getIntegerSort(), "e1_0")
    e1_1_v3 = solver3.mkConst(solver3.getIntegerSort(), "e1_1")
    e2_0_v3 = solver3.mkConst(solver3.getIntegerSort(), "e2_0")
    e2_1_v3 = solver3.mkConst(solver3.getIntegerSort(), "e2_1")

    det_expr3 = solver3.mkTerm(
        cvc5.Kind.SUB,
        solver3.mkTerm(cvc5.Kind.MULT, e1_0_v3, e2_1_v3),
        solver3.mkTerm(cvc5.Kind.MULT, e1_1_v3, e2_0_v3)
    )

    # Proportional edges (1,1) and (2,2) → det=0
    solver3.assertFormula(solver3.mkTerm(cvc5.Kind.EQUAL, e1_0_v3, solver3.mkInteger(1)))
    solver3.assertFormula(solver3.mkTerm(cvc5.Kind.EQUAL, e1_1_v3, solver3.mkInteger(1)))
    solver3.assertFormula(solver3.mkTerm(cvc5.Kind.EQUAL, e2_0_v3, solver3.mkInteger(2)))
    solver3.assertFormula(solver3.mkTerm(cvc5.Kind.EQUAL, e2_1_v3, solver3.mkInteger(2)))

    # Assert det = ±1
    constraint3_pos = solver3.mkTerm(
        cvc5.Kind.EQUAL,
        det_expr3,
        solver3.mkInteger(1)
    )
    constraint3_neg = solver3.mkTerm(
        cvc5.Kind.EQUAL,
        det_expr3,
        solver3.mkInteger(-1)
    )
    constraint3_or = solver3.mkTerm(
        cvc5.Kind.OR,
        constraint3_pos,
        constraint3_neg
    )
    solver3.assertFormula(constraint3_or)
    result3 = solver3.checkSat()

    test_3 = {
        "name": "singular_matrix_non_delzant",
        "description": "Proportional edges (1,1)/(2,2) have det=0, cannot be Delzant (UNSAT)",
        "edges": [[1, 1], [2, 2]],
        "actual_det": 0,
        "cvc5_unsat": not result3.isSat(),
        "passed": not result3.isSat(),
    }
    results["test_3"] = test_3

    return results


# =====================================================================
# BOUNDARY TESTS: Lattice generation via sympy
# =====================================================================

def run_boundary_tests():
    """
    Boundary tests: verify lattice generation properties symbolically.
    """
    results = {}

    try:
        import sympy as sp
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"
    except ImportError:
        return {"error": "sympy not installed"}

    # Test 1: Standard basis vectors generate Z^2
    e1 = sp.Matrix([1, 0])
    e2 = sp.Matrix([0, 1])
    M1 = sp.Matrix.hstack(e1, e2)
    det1 = M1.det()

    test_1 = {
        "name": "standard_basis_generates_Z2",
        "description": "Standard basis (1,0)/(0,1) generates Z^2 (det=1)",
        "edges": [[1, 0], [0, 1]],
        "det": int(det1),
        "generates_lattice": abs(det1) == 1,
        "passed": abs(det1) == 1,
    }
    results["test_1"] = test_1

    # Test 2: Lattice spanned by Delzant edges
    e1_d = sp.Matrix([1, 1])
    e2_d = sp.Matrix([1, 0])
    M2 = sp.Matrix.hstack(e1_d, e2_d)
    det2 = M2.det()

    test_2 = {
        "name": "delzant_lattice_span",
        "description": "Edges (1,1)/(1,0) span Z^2 (det=-1)",
        "edges": [[1, 1], [1, 0]],
        "det": int(det2),
        "generates_lattice": abs(det2) == 1,
        "passed": abs(det2) == 1,
    }
    results["test_2"] = test_2

    # Test 3: Lattice index of non-Delzant configuration
    e1_nd = sp.Matrix([2, 0])
    e2_nd = sp.Matrix([0, 1])
    M3 = sp.Matrix.hstack(e1_nd, e2_nd)
    det3 = M3.det()

    # det=2 means index [Z^2 : lattice] = 2
    test_3 = {
        "name": "non_delzant_lattice_index",
        "description": "Edges (2,0)/(0,1) have det=2 (index 2 sublattice of Z^2)",
        "edges": [[2, 0], [0, 1]],
        "det": int(det3),
        "is_delzant": abs(det3) == 1,
        "lattice_index": int(abs(det3)),
        "passed": int(abs(det3)) > 1,  # Passes because it's non-Delzant as expected
    }
    results["test_3"] = test_3

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    results = {
        "name": "sim_geometry_delzant_polytope_torus_action_constraint_canonical",
        "description": "Delzant polytope condition: lattice generation at vertices",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_geometry_delzant_polytope_torus_action_constraint_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
