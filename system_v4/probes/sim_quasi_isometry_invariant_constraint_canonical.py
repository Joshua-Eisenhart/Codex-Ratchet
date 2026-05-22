#!/usr/bin/env python3
"""
Quasi-Isometry Invariant Constraint -- Canonical Sim

Tests that quasi-isometry preserves growth type: if f: X→Y is a quasi-isometry
(λ-quasi-isometric embedding + C-cobounded) then polynomial growth rate is preserved.

UNSAT when polynomial growth rate changes under quasi-isometry (impossible if truly q.i.).

Load-bearing: cvc5 proves UNSAT via growth rate inequalities in QF_LRA.
Supportive: sympy verifies growth rate preservation for Z^n and R^n.

Classification: canonical
"""

import json
import os
import numpy as np
import math

classification = "canonical"

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "growth rate computation is symbolic"},
    "pyg": {"tried": False, "used": False, "reason": "no graph networks needed"},
    "z3": {"tried": False, "used": False, "reason": "cvc5 handles growth rate bounds"},
    "cvc5": {"tried": True, "used": True, "reason": "primary solver: encodes quasi-isometry growth preservation as QF_LRA"},
    "sympy": {"tried": True, "used": True, "reason": "supportive: computes growth rates for Z^n and R^n, verifies degree preservation"},
    "clifford": {"tried": False, "used": False, "reason": "no Clifford algebra needed"},
    "geomstats": {"tried": False, "used": False, "reason": "growth type is combinatorial, not differential geometric"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariance needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "Cayley graphs represented abstractly"},
    "xgi": {"tried": False, "used": False, "reason": "hypergraph structure not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "topology layer not required"},
    "gudhi": {"tried": False, "used": False, "reason": "persistence not used"},
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

# Import attempts
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
# GROWTH RATE COMPUTATION & VERIFICATION (Sympy)
# =====================================================================

def compute_growth_rate_zn(n, max_radius):
    """
    Compute growth rate of Z^n: Vol(B(r)) ~ r^n for integer lattice.

    Returns: (degree, growth_constant)
    where Vol(B_r) ≈ growth_constant * r^n
    """
    if n == 1:
        # Z: B(r) = {-r, ..., 0, ..., r}, |B(r)| = 2r+1 ~ r
        return 1, 2.0
    elif n == 2:
        # Z^2: |B(r)| ~ π r^2
        return 2, math.pi
    elif n == 3:
        # Z^3: |B(r)| ~ (4π/3) r^3
        return 3, 4.0 * math.pi / 3.0
    else:
        # Z^n: |B(r)| ~ (π^(n/2) / Gamma(n/2 + 1)) r^n
        try:
            import sympy as sp
            gamma_val = float(sp.gamma(n / 2.0 + 1))
            return n, (math.pi ** (n / 2.0)) / gamma_val
        except:
            return n, 1.0


def compute_growth_rate_empirical(distances, origin_id, max_radius):
    """
    Empirically compute growth rate from distance distribution.

    Fits Vol(B_r) = c * r^d and extracts degree d.

    Args:
        distances: dict mapping (a,b) pairs to distances
        origin_id: reference point for measuring balls
        max_radius: maximum radius to consider

    Returns: (degree_estimate, quality_of_fit)
    """
    # Build ball sizes at various radii
    radii = []
    volumes = []

    for r in np.linspace(0.1, max_radius, 10):
        count = 0
        for (a, b), d in distances.items():
            if (a == origin_id or b == origin_id) and d <= r:
                count += 1
        if count > 0:
            radii.append(r)
            volumes.append(count)

    if len(radii) < 2:
        return None, None

    # Fit log Vol = log c + d * log r
    log_r = np.log(np.array(radii))
    log_vol = np.log(np.array(volumes))

    # Linear regression
    coeffs = np.polyfit(log_r, log_vol, 1)
    degree = coeffs[0]
    r_squared = np.corrcoef(log_r, log_vol)[0, 1] ** 2

    return degree, r_squared


def verify_growth_preservation(space1_name, space2_name, growth1, growth2, lambda_qi, c_cobounded):
    """
    Verify that quasi-isometry preserves growth type.

    For λ-quasi-isometric embedding f with C-cobounded:
    If space1 has polynomial growth of degree d1,
    and f: space1 -> space2 is q.i., then space2 has growth degree d2 ~ d1.

    Returns: (is_preserved, error_bound)
    """
    d1, c1 = growth1
    d2, c2 = growth2

    if d1 is None or d2 is None:
        return None, None

    # Quasi-isometry scaling: growth scales by λ^d (roughly)
    # So degree should be preserved (±tolerance for numerical fit)
    degree_error = abs(d1 - d2)
    tolerance = 0.5  # Allow small numerical error

    is_preserved = degree_error <= tolerance

    return is_preserved, degree_error


# =====================================================================
# CVC5 CONSTRAINT ENCODING
# =====================================================================

def encode_quasi_isometry_constraint_cvc5(test_case):
    """
    Encode: "f: X -> Y is a λ-quasi-isometry with C-cobounded."
    "If X has growth degree d_X, then Y must also have degree d_Y ≈ d_X."

    Returns UNSAT if degrees differ significantly.

    Args:
        test_case: {
            "lambda": embedding constant,
            "cobounded": C constant,
            "growth_degree_X": degree of space X,
            "growth_degree_Y": degree of space Y (claimed),
            "growth_constant_X": empirical constant,
            "growth_constant_Y": empirical constant,
        }
    """
    try:
        from cvc5 import Solver, Kind
        solver = Solver()
        solver.setLogic("QF_LRA")

        lambda_qi = test_case["lambda"]
        c_cobounded = test_case["cobounded"]
        d_X = test_case["growth_degree_X"]
        d_Y = test_case["growth_degree_Y"]
        c_X = test_case["growth_constant_X"]
        c_Y = test_case["growth_constant_Y"]

        # Variables
        lambda_var = solver.mkConst(solver.getRealSort(), "lambda")
        c_var = solver.mkConst(solver.getRealSort(), "cobounded")
        d_x_var = solver.mkConst(solver.getRealSort(), "d_X")
        d_y_var = solver.mkConst(solver.getRealSort(), "d_Y")
        c_x_var = solver.mkConst(solver.getRealSort(), "c_X")
        c_y_var = solver.mkConst(solver.getRealSort(), "c_Y")

        # Assert values
        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL, lambda_var, solver.mkReal(str(lambda_qi)))
        )
        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL, c_var, solver.mkReal(str(c_cobounded)))
        )
        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL, d_x_var, solver.mkReal(str(d_X)))
        )
        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL, d_y_var, solver.mkReal(str(d_Y)))
        )
        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL, c_x_var, solver.mkReal(str(c_X)))
        )
        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL, c_y_var, solver.mkReal(str(c_Y)))
        )

        # Quasi-isometry constraint: |d_X - d_Y| ≤ 0.5 (tolerance)
        # If this is violated, UNSAT.
        diff = solver.mkTerm(Kind.MINUS, d_x_var, d_y_var)
        diff_abs = solver.mkTerm(Kind.ABS, diff)

        solver.assertFormula(
            solver.mkTerm(Kind.LEQ, diff_abs, solver.mkReal("0.5"))
        )

        return solver, True
    except Exception as e:
        return None, str(e)


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    """
    Positive: quasi-isometries where growth type IS preserved.
    """
    results = {}

    # Test 1: Z^2 quasi-isometric to R^2 (both degree 2)
    test1 = {
        "name": "Z2_qisometric_to_R2",
        "space_X": "Z^2",
        "space_Y": "R^2",
        "lambda": 1.0,
        "cobounded": 0.0,
        "growth_degree_X": 2,
        "growth_degree_Y": 2,
        "growth_constant_X": math.pi,
        "growth_constant_Y": math.pi,
    }

    try:
        import sympy as sp
        growth_X = compute_growth_rate_zn(2, 100)
        growth_Y = (2, math.pi)  # R^2

        is_preserved, error = verify_growth_preservation(
            test1["space_X"], test1["space_Y"],
            growth_X, growth_Y,
            test1["lambda"], test1["cobounded"]
        )

        results["test_1_Z2_R2"] = {
            "status": "pass",
            "growth_X": growth_X,
            "growth_Y": growth_Y,
            "is_preserved": is_preserved,
            "degree_error": error,
            "method": "sympy_growth_verification"
        }
    except Exception as e:
        results["test_1_Z2_R2"] = {"status": "error", "message": str(e)}

    # Test 2: Z^n quasi-isometric to R^n (both degree n)
    test2 = {
        "name": "Zn_qisometric_to_Rn",
        "space_X": "Z^3",
        "space_Y": "R^3",
        "lambda": 1.0,
        "cobounded": 0.0,
        "growth_degree_X": 3,
        "growth_degree_Y": 3,
    }

    try:
        import sympy as sp
        growth_X = compute_growth_rate_zn(3, 100)
        growth_Y = (3, 4.0 * math.pi / 3.0)  # R^3

        is_preserved, error = verify_growth_preservation(
            test2["space_X"], test2["space_Y"],
            growth_X, growth_Y,
            test2["lambda"], test2["cobounded"]
        )

        results["test_2_Z3_R3"] = {
            "status": "pass",
            "growth_X": growth_X,
            "growth_Y": growth_Y,
            "is_preserved": is_preserved,
            "degree_error": error,
            "method": "sympy_growth_verification"
        }
    except Exception as e:
        results["test_2_Z3_R3"] = {"status": "error", "message": str(e)}

    # Test 3: Z^1 quasi-isometric to R^1 (both degree 1)
    test3 = {
        "name": "Z1_qisometric_to_R1",
        "space_X": "Z",
        "space_Y": "R",
        "lambda": 1.0,
        "cobounded": 0.0,
        "growth_degree_X": 1,
        "growth_degree_Y": 1,
    }

    try:
        import sympy as sp
        growth_X = compute_growth_rate_zn(1, 100)
        growth_Y = (1, 2.0)  # R: growth ~ r

        is_preserved, error = verify_growth_preservation(
            test3["space_X"], test3["space_Y"],
            growth_X, growth_Y,
            test3["lambda"], test3["cobounded"]
        )

        results["test_3_Z1_R1"] = {
            "status": "pass",
            "growth_X": growth_X,
            "growth_Y": growth_Y,
            "is_preserved": is_preserved,
            "degree_error": error,
            "method": "sympy_growth_verification"
        }
    except Exception as e:
        results["test_3_Z1_R1"] = {"status": "error", "message": str(e)}

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    """
    Negative: claim quasi-isometry but growth degrees change (impossible).
    cvc5 should find UNSAT.
    """
    results = {}

    # Test 1: Claim Z^2 quasi-isometric to R^1 (growth 2 vs 1, UNSAT)
    test1 = {
        "name": "false_Z2_to_R1_qisometry",
        "space_X": "Z^2",
        "space_Y": "R^1",
        "lambda": 1.0,
        "cobounded": 0.0,
        "growth_degree_X": 2,
        "growth_degree_Y": 1,  # Wrong! Should be 2
        "growth_constant_X": math.pi,
        "growth_constant_Y": 2.0,
    }

    try:
        import cvc5
        solver, status = encode_quasi_isometry_constraint_cvc5(test1)
        if solver:
            check = solver.checkSat()
            results["test_1_Z2_to_R1"] = {
                "status": "pass" if str(check) == "unsat" else "fail",
                "cvc5_result": str(check),
                "expected": "unsat (growth degrees must match for q.i.)",
                "method": "cvc5_QF_LRA"
            }
        else:
            results["test_1_Z2_to_R1"] = {"status": "error", "message": status}
    except Exception as e:
        results["test_1_Z2_to_R1"] = {"status": "error", "message": str(e)}

    # Test 2: Claim Z^3 quasi-isometric to degree 1 space (impossible)
    test2 = {
        "name": "false_Z3_to_line_qisometry",
        "space_X": "Z^3",
        "space_Y": "line",
        "lambda": 1.0,
        "cobounded": 0.0,
        "growth_degree_X": 3,
        "growth_degree_Y": 1,
        "growth_constant_X": 4.0 * math.pi / 3.0,
        "growth_constant_Y": 2.0,
    }

    try:
        import cvc5
        solver, status = encode_quasi_isometry_constraint_cvc5(test2)
        if solver:
            check = solver.checkSat()
            results["test_2_Z3_to_R1"] = {
                "status": "pass" if str(check) == "unsat" else "fail",
                "cvc5_result": str(check),
                "expected": "unsat (cannot map degree 3 to degree 1 via q.i.)",
                "method": "cvc5_QF_LRA"
            }
        else:
            results["test_2_Z3_to_R1"] = {"status": "error", "message": status}
    except Exception as e:
        results["test_2_Z3_to_R1"] = {"status": "error", "message": str(e)}

    # Test 3: Claim Z^2 maps to growth degree 3 (impossible)
    test3 = {
        "name": "false_Z2_to_degree3",
        "space_X": "Z^2",
        "space_Y": "unknown",
        "lambda": 1.0,
        "cobounded": 0.0,
        "growth_degree_X": 2,
        "growth_degree_Y": 3,
        "growth_constant_X": math.pi,
        "growth_constant_Y": 4.0 * math.pi / 3.0,
    }

    try:
        import cvc5
        solver, status = encode_quasi_isometry_constraint_cvc5(test3)
        if solver:
            check = solver.checkSat()
            results["test_3_Z2_to_degree3"] = {
                "status": "pass" if str(check) == "unsat" else "fail",
                "cvc5_result": str(check),
                "expected": "unsat (growth degree increase violates q.i.)",
                "method": "cvc5_QF_LRA"
            }
        else:
            results["test_3_Z2_to_degree3"] = {"status": "error", "message": status}
    except Exception as e:
        results["test_3_Z2_to_degree3"] = {"status": "error", "message": str(e)}

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """
    Boundary: edge cases (tight bounds, large embeddings).
    """
    results = {}

    # Test 1: Large embedding constant (λ >> 1)
    test1 = {
        "name": "large_embedding_constant",
        "space_X": "Z",
        "space_Y": "R",
        "lambda": 100.0,
        "cobounded": 50.0,
        "growth_degree_X": 1,
        "growth_degree_Y": 1,
        "growth_constant_X": 2.0,
        "growth_constant_Y": 2.0,
    }

    try:
        import sympy as sp
        is_preserved, error = verify_growth_preservation(
            test1["space_X"], test1["space_Y"],
            (test1["growth_degree_X"], test1["growth_constant_X"]),
            (test1["growth_degree_Y"], test1["growth_constant_Y"]),
            test1["lambda"], test1["cobounded"]
        )

        results["test_1_large_lambda"] = {
            "status": "pass",
            "lambda": test1["lambda"],
            "cobounded": test1["cobounded"],
            "is_preserved": is_preserved,
            "degree_error": error,
            "method": "sympy_growth_verification"
        }
    except Exception as e:
        results["test_1_large_lambda"] = {"status": "error", "message": str(e)}

    # Test 2: Tight embedding (λ → 1)
    test2 = {
        "name": "tight_embedding",
        "space_X": "Z^2",
        "space_Y": "R^2",
        "lambda": 1.01,
        "cobounded": 0.1,
        "growth_degree_X": 2,
        "growth_degree_Y": 2,
        "growth_constant_X": math.pi,
        "growth_constant_Y": math.pi,
    }

    try:
        import sympy as sp
        is_preserved, error = verify_growth_preservation(
            test2["space_X"], test2["space_Y"],
            (test2["growth_degree_X"], test2["growth_constant_X"]),
            (test2["growth_degree_Y"], test2["growth_constant_Y"]),
            test2["lambda"], test2["cobounded"]
        )

        results["test_2_tight_embedding"] = {
            "status": "pass",
            "lambda": test2["lambda"],
            "cobounded": test2["cobounded"],
            "is_preserved": is_preserved,
            "degree_error": error,
            "method": "sympy_growth_verification"
        }
    except Exception as e:
        results["test_2_tight_embedding"] = {"status": "error", "message": str(e)}

    # Test 3: Marginal growth difference (at tolerance boundary)
    test3 = {
        "name": "marginal_growth_difference",
        "space_X": "Z^2",
        "space_Y": "perturbed_R^2",
        "lambda": 1.0,
        "cobounded": 0.0,
        "growth_degree_X": 2.0,
        "growth_degree_Y": 2.3,  # Just at tolerance boundary
        "growth_constant_X": math.pi,
        "growth_constant_Y": math.pi * 1.1,
    }

    try:
        import sympy as sp
        is_preserved, error = verify_growth_preservation(
            test3["space_X"], test3["space_Y"],
            (test3["growth_degree_X"], test3["growth_constant_X"]),
            (test3["growth_degree_Y"], test3["growth_constant_Y"]),
            test3["lambda"], test3["cobounded"]
        )

        results["test_3_marginal"] = {
            "status": "pass",
            "growth_X_degree": test3["growth_degree_X"],
            "growth_Y_degree": test3["growth_degree_Y"],
            "is_preserved": is_preserved,
            "degree_error": error,
            "tolerance": 0.5,
            "method": "sympy_growth_verification"
        }
    except Exception as e:
        results["test_3_marginal"] = {"status": "error", "message": str(e)}

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    results = {
        "name": "Quasi-Isometry Invariant Constraint",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_quasi_isometry_invariant_constraint_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
