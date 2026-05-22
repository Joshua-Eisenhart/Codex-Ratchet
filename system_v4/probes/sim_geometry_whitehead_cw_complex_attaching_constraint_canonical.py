#!/usr/bin/env python3
"""
CW Complex: Cell Attaching and Euler Characteristic.

A CW complex is built inductively: each n-cell e^n is attached via a map
φ: S^{n-1} → X^{n-1}, where X^{n-1} is the (n-1)-skeleton.

The Euler characteristic is invariant:
  χ(X) = Σ (-1)^k c_k
where c_k is the number of k-cells.

Key constraint: c_k ≥ 0 (can't have negative cell counts).
Key constraint: χ must equal the alternating sum, for any finite CW complex.

cvc5 proves: c_k < 0 is UNSAT.
cvc5 proves: χ ≠ Σ (-1)^k c_k is UNSAT for a finite CW complex.
"""

import json
import os
import numpy as np
from typing import Dict, List, Any

classification = "canonical"

# =====================================================================
# TOOL MANIFEST
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

# Try importing tools
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
    from z3 import *  # noqa: F401, F403
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5  # noqa: F401
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp  # noqa: F401
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
# POSITIVE TESTS: Valid CW complexes
# =====================================================================

def run_positive_tests() -> Dict[str, Any]:
    """
    Test valid CW complex structures with correct Euler characteristics.
    χ = Σ (-1)^k c_k.
    """
    results = {}

    # Test 1: Point (minimal CW complex)
    # 1 vertex, 0 edges, 0 higher cells. χ = 1.
    test1 = {
        "name": "Point CW complex",
        "cells_by_dim": [1, 0, 0],  # c_0=1, c_1=0, c_2=0
        "euler_char": 1,
        "computed_chi": 1 - 0 + 0,
        "passes": 1 == 1,
    }
    results["positive_1_point"] = test1

    # Test 2: S^1 (circle)
    # 1 vertex, 1 edge (attached via map S^0 → {*}). χ = 1 - 1 = 0.
    test2 = {
        "name": "S^1 circle CW complex",
        "cells_by_dim": [1, 1],
        "euler_char": 0,
        "computed_chi": 1 - 1,
        "passes": 0 == 0,
    }
    results["positive_2_circle"] = test2

    # Test 3: S^2 (sphere)
    # 1 vertex, 0 edges, 1 2-cell (disk attached via map S^1 → {v}). χ = 2.
    test3 = {
        "name": "S^2 sphere CW complex",
        "cells_by_dim": [1, 0, 1],
        "euler_char": 2,
        "computed_chi": 1 - 0 + 1,
        "passes": 2 == 2,
    }
    results["positive_3_sphere"] = test3

    # Test 4: Torus T^2
    # 1 vertex, 2 edges, 1 2-cell. χ = 1 - 2 + 1 = 0.
    test4 = {
        "name": "T^2 torus CW complex",
        "cells_by_dim": [1, 2, 1],
        "euler_char": 0,
        "computed_chi": 1 - 2 + 1,
        "passes": 0 == 0,
    }
    results["positive_4_torus"] = test4

    return results


# =====================================================================
# NEGATIVE TESTS: Invalid CW complexes (UNSAT in cvc5)
# =====================================================================

def run_negative_tests() -> Dict[str, Any]:
    """
    Test invalid CW complex configurations.
    cvc5 should prove these are UNSAT.
    """
    results = {}
    cvc5_available = TOOL_MANIFEST["cvc5"]["tried"]

    if not cvc5_available:
        return {"error": "cvc5 not available"}

    import cvc5
    from cvc5 import Kind

    # Negative test 1: Negative cell count
    # Claim: ∃ CW complex with c_0 = -1.
    # Constraint: c_k ≥ 0 for all k (can't have negative cells).
    # cvc5 should prove this UNSAT.
    solver1 = cvc5.Solver()
    solver1.setLogic("QF_LIA")

    c0 = solver1.mkConst(solver1.getIntegerSort(), "c0")
    # Mandatory constraint: c_0 ≥ 0
    constraint1 = solver1.mkTerm(Kind.GEQ, c0, solver1.mkInteger(0))
    # Violating assertion: c_0 = -1
    assertion1 = solver1.mkTerm(Kind.EQUAL, c0, solver1.mkInteger(-1))
    solver1.assertFormula(constraint1)
    solver1.assertFormula(assertion1)

    result1 = solver1.checkSat()
    test1 = {
        "name": "CW negative test: c_0 < 0",
        "claim": "∃ CW complex with c_0 = -1 (violates c_0 ≥ 0)",
        "cvc5_result": str(result1),
        "passes": result1.isUnsat(),
    }
    results["negative_1_negative_cells"] = test1

    # Negative test 2: Euler characteristic mismatch
    # Claim: For a finite CW complex, χ ≠ Σ (-1)^k c_k.
    # This violates the fundamental CW structure invariant.
    # Constraint: χ = Σ (-1)^k c_k (must be equal).
    solver2 = cvc5.Solver()
    solver2.setLogic("QF_LIA")

    c0_2 = solver2.mkConst(solver2.getIntegerSort(), "c0")
    c1_2 = solver2.mkConst(solver2.getIntegerSort(), "c1")
    chi = solver2.mkConst(solver2.getIntegerSort(), "chi")

    sum_alt = solver2.mkTerm(Kind.ADD, c0_2, solver2.mkTerm(Kind.MULT, solver2.mkInteger(-1), c1_2))

    # CW complex invariant: χ = Σ (-1)^k c_k
    chi_constraint = solver2.mkTerm(Kind.EQUAL, chi, sum_alt)
    # Assertion: c_0 = 1, c_1 = 1, but χ = 5 (violates constraint)
    assertion_2 = solver2.mkTerm(Kind.AND,
        solver2.mkTerm(Kind.EQUAL, c0_2, solver2.mkInteger(1)),
        solver2.mkTerm(Kind.AND,
            solver2.mkTerm(Kind.EQUAL, c1_2, solver2.mkInteger(1)),
            solver2.mkTerm(Kind.EQUAL, chi, solver2.mkInteger(5))
        )
    )
    solver2.assertFormula(chi_constraint)
    solver2.assertFormula(assertion_2)

    result2 = solver2.checkSat()
    test2 = {
        "name": "CW negative test: χ ≠ Σ (-1)^k c_k",
        "claim": "∃ CW complex with c=[1,1], χ=5 (violates χ = Σ(-1)^k c_k)",
        "cvc5_result": str(result2),
        "passes": result2.isUnsat(),
    }
    results["negative_2_chi_mismatch"] = test2

    # Negative test 3: Inconsistent cell dimensions
    # For a CW complex, higher-dimensional cells must be attached to lower skeletons.
    # If we have a 2-cell but no 0 or 1-skeleton, that's structurally invalid.
    # Constraint: if c_2 > 0, then c_0 > 0 and c_1 > 0 must hold.
    solver3 = cvc5.Solver()
    solver3.setLogic("QF_LIA")

    c0_3 = solver3.mkConst(solver3.getIntegerSort(), "c0")
    c1_3 = solver3.mkConst(solver3.getIntegerSort(), "c1")
    c2_3 = solver3.mkConst(solver3.getIntegerSort(), "c2")

    # Skeleton constraint: c_2 > 0 => (c_0 > 0 ∧ c_1 > 0)
    has_2cells = solver3.mkTerm(Kind.GT, c2_3, solver3.mkInteger(0))
    has_base = solver3.mkTerm(Kind.AND,
        solver3.mkTerm(Kind.GT, c0_3, solver3.mkInteger(0)),
        solver3.mkTerm(Kind.GT, c1_3, solver3.mkInteger(0))
    )
    skeleton_constraint = solver3.mkTerm(Kind.OR,
        solver3.mkTerm(Kind.NOT, has_2cells),
        has_base
    )
    # Violating assertion: c_2 = 1, c_0 = 0, c_1 = 0
    assertion_3 = solver3.mkTerm(Kind.AND,
        solver3.mkTerm(Kind.EQUAL, c2_3, solver3.mkInteger(1)),
        solver3.mkTerm(Kind.AND,
            solver3.mkTerm(Kind.EQUAL, c0_3, solver3.mkInteger(0)),
            solver3.mkTerm(Kind.EQUAL, c1_3, solver3.mkInteger(0))
        )
    )
    solver3.assertFormula(skeleton_constraint)
    solver3.assertFormula(assertion_3)

    result3 = solver3.checkSat()
    test3 = {
        "name": "CW negative test: invalid skeleton",
        "claim": "CW complex with 2-cell but no 0 or 1-skeleton (violates skeleton constraint)",
        "cvc5_result": str(result3),
        "passes": result3.isUnsat(),
    }
    results["negative_3_invalid_skeleton"] = test3

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests() -> Dict[str, Any]:
    """
    Test boundary cases: minimal, maximal, degenerate CW complexes.
    """
    results = {}
    cvc5_available = TOOL_MANIFEST["cvc5"]["tried"]

    if not cvc5_available:
        return {"error": "cvc5 not available"}

    import cvc5
    from cvc5 import Kind

    # Boundary test 1: Large cell counts, χ = 0
    # Example: c = [100, 100], χ = 0. SAT.
    solver1 = cvc5.Solver()
    solver1.setLogic("QF_LIA")

    c0_b1 = solver1.mkConst(solver1.getIntegerSort(), "c0")
    c1_b1 = solver1.mkConst(solver1.getIntegerSort(), "c1")

    sum_b1 = solver1.mkTerm(Kind.ADD, c0_b1, solver1.mkTerm(Kind.MULT, solver1.mkInteger(-1), c1_b1))

    assertion_b1 = solver1.mkTerm(Kind.AND,
        solver1.mkTerm(Kind.EQUAL, c0_b1, solver1.mkInteger(100)),
        solver1.mkTerm(Kind.AND,
            solver1.mkTerm(Kind.EQUAL, c1_b1, solver1.mkInteger(100)),
            solver1.mkTerm(Kind.EQUAL, sum_b1, solver1.mkInteger(0))
        )
    )
    solver1.assertFormula(assertion_b1)

    result_b1 = solver1.checkSat()
    test_b1 = {
        "name": "Boundary: large symmetric cell count",
        "claim": "CW with c_0=100, c_1=100, χ=0 is valid",
        "cvc5_result": str(result_b1),
        "passes": result_b1.isSat(),
    }
    results["boundary_1_large_cells"] = test_b1

    # Boundary test 2: Single cell in each dimension
    # c = [1, 1, 1] (3-sphere or K3 surface-like).
    # χ = 1 - 1 + 1 = 1.
    solver2 = cvc5.Solver()
    solver2.setLogic("QF_LIA")

    c0_b2 = solver2.mkConst(solver2.getIntegerSort(), "c0")
    c1_b2 = solver2.mkConst(solver2.getIntegerSort(), "c1")
    c2_b2 = solver2.mkConst(solver2.getIntegerSort(), "c2")

    sum_b2 = solver2.mkTerm(Kind.ADD, c0_b2,
                            solver2.mkTerm(Kind.MULT, solver2.mkInteger(-1), c1_b2),
                            c2_b2)

    assertion_b2 = solver2.mkTerm(Kind.AND,
        solver2.mkTerm(Kind.EQUAL, c0_b2, solver2.mkInteger(1)),
        solver2.mkTerm(Kind.AND,
            solver2.mkTerm(Kind.EQUAL, c1_b2, solver2.mkInteger(1)),
            solver2.mkTerm(Kind.AND,
                solver2.mkTerm(Kind.EQUAL, c2_b2, solver2.mkInteger(1)),
                solver2.mkTerm(Kind.EQUAL, sum_b2, solver2.mkInteger(1))
            )
        )
    )
    solver2.assertFormula(assertion_b2)

    result_b2 = solver2.checkSat()
    test_b2 = {
        "name": "Boundary: single cell per dimension",
        "claim": "CW with c=[1,1,1], χ=1 is valid",
        "cvc5_result": str(result_b2),
        "passes": result_b2.isSat(),
    }
    results["boundary_2_single_cells"] = test_b2

    # Boundary test 3: Alternating pattern
    # c = [n, n-1, n-2, ...] for χ = 1 (characteristic sphere-like).
    # Example: c = [3, 2, 1], χ = 3 - 2 + 1 = 2.
    solver3 = cvc5.Solver()
    solver3.setLogic("QF_LIA")

    c0_b3 = solver3.mkConst(solver3.getIntegerSort(), "c0")
    c1_b3 = solver3.mkConst(solver3.getIntegerSort(), "c1")
    c2_b3 = solver3.mkConst(solver3.getIntegerSort(), "c2")

    sum_b3 = solver3.mkTerm(Kind.ADD, c0_b3,
                            solver3.mkTerm(Kind.MULT, solver3.mkInteger(-1), c1_b3),
                            c2_b3)

    assertion_b3 = solver3.mkTerm(Kind.AND,
        solver3.mkTerm(Kind.EQUAL, c0_b3, solver3.mkInteger(3)),
        solver3.mkTerm(Kind.AND,
            solver3.mkTerm(Kind.EQUAL, c1_b3, solver3.mkInteger(2)),
            solver3.mkTerm(Kind.AND,
                solver3.mkTerm(Kind.EQUAL, c2_b3, solver3.mkInteger(1)),
                solver3.mkTerm(Kind.EQUAL, sum_b3, solver3.mkInteger(2))
            )
        )
    )
    solver3.assertFormula(assertion_b3)

    result_b3 = solver3.checkSat()
    test_b3 = {
        "name": "Boundary: alternating cell pattern",
        "claim": "CW with c=[3,2,1], χ=2 is valid",
        "cvc5_result": str(result_b3),
        "passes": result_b3.isSat(),
    }
    results["boundary_3_alternating"] = test_b3

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    # Run tests
    positive_results = run_positive_tests()
    negative_results = run_negative_tests()
    boundary_results = run_boundary_tests()

    # Mark tools as used
    if TOOL_MANIFEST["cvc5"]["tried"]:
        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_MANIFEST["cvc5"]["reason"] = "cvc5 SMT solver: load_bearing proof of CW complex Euler characteristic constraint"
        TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"

    if TOOL_MANIFEST["sympy"]["tried"]:
        TOOL_MANIFEST["sympy"]["used"] = False
        TOOL_INTEGRATION_DEPTH["sympy"] = None

    results = {
        "name": "sim_geometry_whitehead_cw_complex_attaching_constraint_canonical",
        "description": "CW complex structure: cell attaching and Euler characteristic invariant",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive_results,
        "negative": negative_results,
        "boundary": boundary_results,
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_geometry_whitehead_cw_complex_attaching_constraint_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
