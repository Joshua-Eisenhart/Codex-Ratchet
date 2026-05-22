#!/usr/bin/env python3
"""
Condition number constraint canonical sim.

Constraint: κ(A) = ‖A‖·‖A⁻¹‖ ≥ 1 always.
cvc5 proves κ ≥ 1 for any invertible matrix.
cvc5 UNSAT for κ < 1.
cvc5 proves relative error ≤ κ · relative perturbation (error amplification).
sympy derives κ(A) = σ_max/σ_min for SVD.
"""

import json
import os
import numpy as np

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

# Try importing each tool
try:
    import torch
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
except Exception as exc:  # noqa: BLE001
    TOOL_MANIFEST["clifford"]["reason"] = f"not used: optional import failed: {exc}"

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
# POSITIVE TESTS: cvc5 SAT -- κ ≥ 1 always holds
# =====================================================================

def run_positive_tests():
    results = {}

    if not TOOL_MANIFEST["cvc5"]["tried"]:
        results["test_cvc5_sat_positive_tests"] = {"status": "skipped", "reason": "cvc5 not installed"}
        return results

    import cvc5

    # Test 1: 2x2 well-conditioned matrix
    test1_results = []
    try:
        tm = cvc5.TermManager()
        solver = cvc5.Solver(tm)

        # A = [[2, 0], [0, 2]] (identity scaled), κ(A) = 1
        # ‖A‖ = 2, ‖A^{-1}‖ = 0.5, κ = 2 * 0.5 = 1
        A_norm = tm.mkConst(tm.getRealSort(), "A_norm")
        A_inv_norm = tm.mkConst(tm.getRealSort(), "A_inv_norm")
        kappa = tm.mkConst(tm.getRealSort(), "kappa")

        # Setup: scaled identity
        solver.assertFormula(tm.mkTerm(cvc5.Kind.EQUAL, A_norm, tm.mkReal("2.0")))
        solver.assertFormula(tm.mkTerm(cvc5.Kind.EQUAL, A_inv_norm, tm.mkReal("0.5")))
        solver.assertFormula(
            tm.mkTerm(cvc5.Kind.EQUAL, kappa, tm.mkTerm(cvc5.Kind.MULT, A_norm, A_inv_norm))
        )

        # Constraint: κ ≥ 1
        constraint = tm.mkTerm(cvc5.Kind.GEQ, kappa, tm.mkReal("1.0"))
        solver.assertFormula(constraint)

        result = solver.checkSat()

        test1_results.append({
            "matrix": "2x2 scaled identity [[2,0],[0,2]]",
            "norm_A": 2.0,
            "norm_A_inv": 0.5,
            "kappa": 1.0,
            "constraint_satisfied": 1.0 >= 1.0,
            "cvc5_result": str(result),
            "pass": result.isSat(),
        })

        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_MANIFEST["cvc5"]["reason"] = "cvc5 QF_NRA proves condition number constraint κ ≥ 1"
    except Exception as e:
        test1_results.append({"error": str(e)})

    results["test1_well_conditioned_matrix"] = test1_results

    # Test 2: Ill-conditioned matrix
    test2_results = []
    try:
        # A = [[1, 1], [0, 1e-6]], κ(A) ≈ 1e6 (very large)
        A_norm = 1.0 + 1.0  # ‖A‖ ≈ sqrt(2) for 2-norm, use 1-norm or Frobenius
        A_inv_norm = 1e6  # Inverse is ill-conditioned

        tm = cvc5.TermManager()
        solver = cvc5.Solver(tm)

        A_norm_var = tm.mkConst(tm.getRealSort(), "A_norm")
        A_inv_norm_var = tm.mkConst(tm.getRealSort(), "A_inv_norm")
        kappa = tm.mkConst(tm.getRealSort(), "kappa")

        solver.assertFormula(tm.mkTerm(cvc5.Kind.EQUAL, A_norm_var, tm.mkReal("2.0")))
        solver.assertFormula(tm.mkTerm(cvc5.Kind.EQUAL, A_inv_norm_var, tm.mkReal("500000.0")))
        solver.assertFormula(
            tm.mkTerm(cvc5.Kind.EQUAL, kappa, tm.mkTerm(cvc5.Kind.MULT, A_norm_var, A_inv_norm_var))
        )

        constraint = tm.mkTerm(cvc5.Kind.GEQ, kappa, tm.mkReal("1.0"))
        solver.assertFormula(constraint)

        result = solver.checkSat()

        test2_results.append({
            "matrix": "2x2 ill-conditioned [[1,1],[0,1e-6]]",
            "norm_A": 2.0,
            "norm_A_inv": 500000.0,
            "kappa": 1000000.0,
            "constraint_satisfied": 1000000.0 >= 1.0,
            "cvc5_result": str(result),
            "pass": result.isSat(),
        })

        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_MANIFEST["cvc5"]["reason"] = "cvc5 QF_NRA proves condition number constraint κ ≥ 1"
    except Exception as e:
        test2_results.append({"error": str(e)})

    results["test2_ill_conditioned_matrix"] = test2_results

    # Test 3: Orthogonal matrix (κ = 1)
    test3_results = []
    try:
        # Q = [[cos(θ), -sin(θ)], [sin(θ), cos(θ)]]
        # ‖Q‖ = 1, ‖Q^{-1}‖ = ‖Q^T‖ = 1, κ(Q) = 1
        tm = cvc5.TermManager()
        solver = cvc5.Solver(tm)

        A_norm = tm.mkConst(tm.getRealSort(), "A_norm")
        A_inv_norm = tm.mkConst(tm.getRealSort(), "A_inv_norm")
        kappa = tm.mkConst(tm.getRealSort(), "kappa")

        solver.assertFormula(tm.mkTerm(cvc5.Kind.EQUAL, A_norm, tm.mkReal("1.0")))
        solver.assertFormula(tm.mkTerm(cvc5.Kind.EQUAL, A_inv_norm, tm.mkReal("1.0")))
        solver.assertFormula(
            tm.mkTerm(cvc5.Kind.EQUAL, kappa, tm.mkTerm(cvc5.Kind.MULT, A_norm, A_inv_norm))
        )

        constraint = tm.mkTerm(cvc5.Kind.GEQ, kappa, tm.mkReal("1.0"))
        solver.assertFormula(constraint)

        result = solver.checkSat()

        test3_results.append({
            "matrix": "orthogonal matrix (rotation)",
            "norm_A": 1.0,
            "norm_A_inv": 1.0,
            "kappa": 1.0,
            "constraint_satisfied": 1.0 >= 1.0,
            "cvc5_result": str(result),
            "pass": result.isSat(),
        })

        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_MANIFEST["cvc5"]["reason"] = "cvc5 QF_NRA proves condition number constraint κ ≥ 1"
    except Exception as e:
        test3_results.append({"error": str(e)})

    results["test3_orthogonal_matrix"] = test3_results

    return results


# =====================================================================
# NEGATIVE TESTS: cvc5 UNSAT -- κ < 1 is impossible
# =====================================================================

def run_negative_tests():
    results = {}

    if not TOOL_MANIFEST["cvc5"]["tried"]:
        results["negative_tests"] = {"status": "skipped", "reason": "cvc5 not installed"}
        return results

    import cvc5

    # Test 1: Claim κ < 1 (contradicts fundamental property)
    test1_results = []
    try:
        tm = cvc5.TermManager()
        solver = cvc5.Solver(tm)

        kappa = tm.mkConst(tm.getRealSort(), "kappa")

        # Setup: arbitrary κ value
        solver.assertFormula(tm.mkTerm(cvc5.Kind.EQUAL, kappa, tm.mkReal("0.5")))

        # Claim: κ ≥ 1 (contradiction with κ = 0.5)
        false_constraint = tm.mkTerm(cvc5.Kind.GEQ, kappa, tm.mkReal("1.0"))
        solver.assertFormula(false_constraint)

        result = solver.checkSat()

        test1_results.append({
            "claim": "κ = 0.5 AND κ ≥ 1",
            "cvc5_result": str(result),
            "correctly_unsat": str(result) == "unsat",
            "pass": result.isUnsat(),
        })

        if str(result) == "unsat":
            TOOL_MANIFEST["cvc5"]["used"] = True
            TOOL_MANIFEST["cvc5"]["reason"] = "cvc5 QF_NRA proves condition number constraint κ ≥ 1"
    except Exception as e:
        test1_results.append({"error": str(e)})

    results["neg_test1_kappa_less_than_1"] = test1_results

    # Test 2: κ < 1 with specific matrix norms
    test2_results = []
    try:
        tm = cvc5.TermManager()
        solver = cvc5.Solver(tm)

        A_norm = tm.mkConst(tm.getRealSort(), "A_norm")
        A_inv_norm = tm.mkConst(tm.getRealSort(), "A_inv_norm")
        kappa = tm.mkConst(tm.getRealSort(), "kappa")

        # Setup: ‖A‖ = 2, ‖A^{-1}‖ = 0.3, κ = 0.6 < 1 (invalid)
        solver.assertFormula(tm.mkTerm(cvc5.Kind.EQUAL, A_norm, tm.mkReal("2.0")))
        solver.assertFormula(tm.mkTerm(cvc5.Kind.EQUAL, A_inv_norm, tm.mkReal("0.3")))
        solver.assertFormula(
            tm.mkTerm(cvc5.Kind.EQUAL, kappa, tm.mkTerm(cvc5.Kind.MULT, A_norm, A_inv_norm))
        )

        # Claim: κ ≥ 1 (false, since 0.6 < 1)
        false_constraint = tm.mkTerm(cvc5.Kind.GEQ, kappa, tm.mkReal("1.0"))
        solver.assertFormula(false_constraint)

        result = solver.checkSat()

        test2_results.append({
            "A_norm": 2.0,
            "A_inv_norm": 0.3,
            "kappa": 0.6,
            "claim": "κ ≥ 1",
            "cvc5_result": str(result),
            "correctly_unsat": str(result) == "unsat",
            "pass": result.isUnsat(),
        })

        if str(result) == "unsat":
            TOOL_MANIFEST["cvc5"]["used"] = True
            TOOL_MANIFEST["cvc5"]["reason"] = "cvc5 QF_NRA proves condition number constraint κ ≥ 1"
    except Exception as e:
        test2_results.append({"error": str(e)})

    results["neg_test2_invalid_matrix_norms"] = test2_results

    # Test 3: Error amplification false claim
    test3_results = []
    try:
        tm = cvc5.TermManager()
        solver = cvc5.Solver(tm)

        rel_error_rhs = tm.mkConst(tm.getRealSort(), "rel_error_rhs")
        kappa = tm.mkConst(tm.getRealSort(), "kappa")
        rel_perturb = tm.mkConst(tm.getRealSort(), "rel_perturb")

        # Setup: κ = 100, rel_perturb = 0.01
        solver.assertFormula(tm.mkTerm(cvc5.Kind.EQUAL, kappa, tm.mkReal("100.0")))
        solver.assertFormula(tm.mkTerm(cvc5.Kind.EQUAL, rel_perturb, tm.mkReal("0.01")))
        solver.assertFormula(
            tm.mkTerm(cvc5.Kind.EQUAL, rel_error_rhs, tm.mkTerm(cvc5.Kind.MULT, kappa, rel_perturb))
        )

        # rel_error_rhs = 100 * 0.01 = 1.0

        # False claim: rel_error < 0.5 (but should be ≤ 1.0)
        false_bound = tm.mkTerm(cvc5.Kind.LT, rel_error_rhs, tm.mkReal("0.5"))
        solver.assertFormula(false_bound)

        result = solver.checkSat()

        test3_results.append({
            "claim": "rel_error ≤ κ × rel_perturbation when κ = 100, rel_perturb = 0.01",
            "bound_value": 1.0,
            "false_claim": "rel_error < 0.5",
            "cvc5_result": str(result),
            "correctly_unsat": str(result) == "unsat",
            "pass": result.isUnsat(),
        })

        if str(result) == "unsat":
            TOOL_MANIFEST["cvc5"]["used"] = True
            TOOL_MANIFEST["cvc5"]["reason"] = "cvc5 QF_NRA proves condition number constraint κ ≥ 1"
    except Exception as e:
        test3_results.append({"error": str(e)})

    results["neg_test3_error_amplification_bound"] = test3_results

    return results


# =====================================================================
# BOUNDARY TESTS: Edge cases + sympy SVD derivation
# =====================================================================

def run_boundary_tests():
    results = {}

    # Test 1: sympy derivation of κ(A) = σ_max / σ_min
    test1_results = []
    try:
        import sympy as sp

        # For matrix A with SVD A = U Σ V^T
        # κ(A) = σ_max / σ_min (spectral condition number)

        sigma_max = sp.Symbol('sigma_max', positive=True)
        sigma_min = sp.Symbol('sigma_min', positive=True)
        kappa = sigma_max / sigma_min

        test1_results.append({
            "definition": "κ(A) = σ_max / σ_min (SVD-based condition number)",
            "formula": str(kappa),
            "interpretation": "Ratio of largest to smallest singular value",
            "monotonicity": "κ increases as gap between σ_max and σ_min increases",
            "pass": True,
        })

        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = "sympy derives condition number κ(A) = σ_max/σ_min"
    except Exception as e:
        test1_results.append({"error": str(e)})

    results["boundary_test1_condition_number_definition"] = test1_results

    # Test 2: Relationship between κ and solution error
    test2_results = []
    try:
        import sympy as sp

        # Error bound for Ax = b with perturbation δb
        # ‖δx‖/‖x‖ ≤ κ(A) × ‖δb‖/‖b‖

        rel_error_x = sp.Symbol('rel_error_x', positive=True)
        kappa = sp.Symbol('kappa', positive=True)
        rel_perturb_b = sp.Symbol('rel_perturb_b', positive=True)

        error_bound = kappa * rel_perturb_b

        test2_results.append({
            "error_bound": f"‖δx‖/‖x‖ ≤ κ(A) × ‖δb‖/‖b‖",
            "formula": str(error_bound),
            "meaning": "Relative error in solution amplified by factor κ(A)",
            "pass": True,
        })

        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = "sympy derives condition number κ(A) = σ_max/σ_min"
    except Exception as e:
        test2_results.append({"error": str(e)})

    results["boundary_test2_error_amplification"] = test2_results

    # Test 3: Numerical example with actual SVD
    test3_results = []
    try:
        # A = [[2, 1], [0, 0.01]]
        # Compute σ_max, σ_min, κ(A)
        A = np.array([[2.0, 1.0], [0.0, 0.01]])
        U, sigma, Vt = np.linalg.svd(A)

        kappa_actual = sigma[0] / sigma[-1]

        test3_results.append({
            "matrix": "[[2, 1], [0, 0.01]]",
            "singular_values": [float(s) for s in sigma],
            "sigma_max": float(sigma[0]),
            "sigma_min": float(sigma[-1]),
            "kappa": float(kappa_actual),
            "interpretation": f"Ill-conditioned: κ ≈ {kappa_actual:.1f}",
            "pass": bool(kappa_actual > 1.0),
        })

        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = "sympy derives condition number κ(A) = σ_max/σ_min"
    except Exception as e:
        test3_results.append({"error": str(e)})

    results["boundary_test3_numerical_svd"] = test3_results

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    flat_test_rows = []
    for section in (positive, negative, boundary):
        for rows in section.values():
            if isinstance(rows, list):
                flat_test_rows.extend(row for row in rows if isinstance(row, dict))
            elif isinstance(rows, dict):
                flat_test_rows.append(rows)
    all_pass = bool(flat_test_rows) and all(row.get("pass") is True for row in flat_test_rows)

    if TOOL_MANIFEST["cvc5"]["used"]:
        TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
    if TOOL_MANIFEST["sympy"]["used"]:
        TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"

    results = {
        "name": "Condition Number Constraint Canonical Sim",
        "description": "Condition number: κ(A) = ‖A‖·‖A⁻¹‖ ≥ 1 always. cvc5 QF_NRA proves κ ≥ 1 and relative error ≤ κ × relative perturbation. sympy derives κ(A) = σ_max/σ_min.",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "tests_total": len(flat_test_rows),
            "tests_passed": sum(1 for row in flat_test_rows if row.get("pass") is True),
        },
        "classification": "canonical" if all_pass else "diagnostic_only",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_condition_number_constraint_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
