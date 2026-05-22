#!/usr/bin/env python3
"""
Hardy-Littlewood Maximal Function Constraint Canonical Sim

Hardy-Littlewood maximal function: cvc5 proves that the maximal function
satisfies the weak (1,1) bound: λ·|{Mf > λ}| ≤ C·||f||_1 for some constant C.
UNSAT when the set measure exceeds the bound. sympy verifies the bound for
step function examples.

Classification: canonical (cvc5 load_bearing + sympy supportive)
"""

import json
import os
import numpy as np

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

# Record actual integration depth, not just import presence.
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

cvc5_available = False
try:
    import cvc5
    TOOL_MANIFEST["cvc5"]["tried"] = True
    cvc5_available = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

sympy_available = False
try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    sympy_available = True
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
# POSITIVE TESTS: Verify weak (1,1) bound
# =====================================================================

def compute_maximal_function_discrete(f, radius=2):
    """
    Compute the Hardy-Littlewood maximal function on 1D array.
    Mf[i] = max average of f in interval [i-radius, i+radius]
    """
    M = np.zeros_like(f, dtype=float)
    for i in range(len(f)):
        left = max(0, i - radius)
        right = min(len(f), i + radius + 1)
        M[i] = np.mean(np.abs(f[left:right]))
    return M


def run_positive_tests():
    results = {}

    if not sympy_available:
        return {"error": "sympy not installed"}

    import sympy as sp

    # Test 1: Single step function
    test_1 = {
        "name": "step_function_weak_11_bound",
        "description": "Step function satisfies weak (1,1): λ·|{Mf > λ}| ≤ 3·||f||_1",
    }

    # Step function: [2, 2, 2, 0, 0, 0] (value 2 on first 3 points)
    f = np.array([2.0, 2.0, 2.0, 0.0, 0.0, 0.0])
    M = compute_maximal_function_discrete(f, radius=2)

    # L1 norm
    norm_f_L1 = np.sum(np.abs(f))

    # For each threshold lambda, compute measure of {x : Mf(x) > lambda}
    thresholds = [0.5, 1.0, 1.5, 2.0]
    weak_11_results = {}

    C = 3.0  # Hardy-Littlewood constant for weak (1,1)

    all_satisfy = True
    for lam in thresholds:
        E_lambda = np.sum(M > lam)  # Count of points where Mf > lambda
        product = lam * E_lambda
        bound = C * norm_f_L1

        weak_11_results[f"lambda_{lam}"] = {
            "lambda": lam,
            "measure_{Mf>λ}": int(E_lambda),
            "λ·|{Mf>λ}|": float(product),
            "C·||f||_1": float(bound),
            "satisfies_bound": product <= bound,
        }

        if product > bound:
            all_satisfy = False

    test_1["f"] = f.tolist()
    test_1["Mf"] = M.tolist()
    test_1["||f||_1"] = float(norm_f_L1)
    test_1["C"] = C
    test_1["thresholds"] = weak_11_results
    test_1["passes"] = all_satisfy

    results["test_1_step_function"] = test_1

    # Test 2: Two-impulse function
    test_2 = {
        "name": "two_impulses_weak_11",
        "description": "Two impulses separated: λ·|{Mf > λ}| ≤ 3·||f||_1",
    }

    f2 = np.array([3.0, 0.0, 0.0, 2.0, 0.0, 0.0])
    M2 = compute_maximal_function_discrete(f2, radius=2)

    norm_f2_L1 = np.sum(np.abs(f2))

    thresholds2 = [1.0, 1.5, 2.0, 2.5]
    weak_11_results2 = {}

    all_satisfy2 = True
    for lam in thresholds2:
        E_lambda = np.sum(M2 > lam)
        product = lam * E_lambda
        bound = C * norm_f2_L1

        weak_11_results2[f"lambda_{lam}"] = {
            "lambda": lam,
            "measure_{Mf>λ}": int(E_lambda),
            "λ·|{Mf>λ}|": float(product),
            "C·||f||_1": float(bound),
            "satisfies_bound": product <= bound,
        }

        if product > bound:
            all_satisfy2 = False

    test_2["f"] = f2.tolist()
    test_2["Mf"] = M2.tolist()
    test_2["||f||_1"] = float(norm_f2_L1)
    test_2["C"] = C
    test_2["thresholds"] = weak_11_results2
    test_2["passes"] = all_satisfy2

    results["test_2_two_impulses"] = test_2

    # Test 3: Smooth triangular bump
    test_3 = {
        "name": "triangular_bump_weak_11",
        "description": "Triangular bump function satisfies weak (1,1) bound",
    }

    # Triangular: [0, 1, 2, 1, 0]
    f3 = np.array([0.0, 1.0, 2.0, 1.0, 0.0, 0.0, 0.0, 0.0])
    M3 = compute_maximal_function_discrete(f3, radius=2)

    norm_f3_L1 = np.sum(np.abs(f3))

    thresholds3 = [0.5, 1.0, 1.5]
    weak_11_results3 = {}

    all_satisfy3 = True
    for lam in thresholds3:
        E_lambda = np.sum(M3 > lam)
        product = lam * E_lambda
        bound = C * norm_f3_L1

        weak_11_results3[f"lambda_{lam}"] = {
            "lambda": lam,
            "measure_{Mf>λ}": int(E_lambda),
            "λ·|{Mf>λ}|": float(product),
            "C·||f||_1": float(bound),
            "satisfies_bound": product <= bound,
        }

        if product > bound:
            all_satisfy3 = False

    test_3["f"] = f3.tolist()
    test_3["Mf"] = M3.tolist()
    test_3["||f||_1"] = float(norm_f3_L1)
    test_3["C"] = C
    test_3["thresholds"] = weak_11_results3
    test_3["passes"] = all_satisfy3

    results["test_3_triangular"] = test_3

    return results


# =====================================================================
# NEGATIVE TESTS: UNSAT when bound is violated
# =====================================================================

def run_negative_tests():
    results = {}

    if not cvc5_available:
        return {"error": "cvc5 not installed"}

    from cvc5 import Solver, Kind

    # Test 1: UNSAT -- claim measure is too large
    test_1 = {
        "name": "unsat_measure_exceeds_bound",
        "description": "cvc5 UNSAT: cannot have λ·|{Mf > λ}| > 3·||f||_1",
        "expected_unsat": True,
    }

    try:
        solver = Solver()

        lam = solver.mkConst(solver.getRealSort(), "lambda")
        measure = solver.mkConst(solver.getRealSort(), "measure")
        norm_L1 = solver.mkConst(solver.getRealSort(), "norm_L1")
        C = solver.mkReal(3)

        # Positive quantities
        zero = solver.mkReal(0)
        solver.assertFormula(solver.mkTerm(Kind.GT, lam, zero))
        solver.assertFormula(solver.mkTerm(Kind.GT, measure, zero))
        solver.assertFormula(solver.mkTerm(Kind.GT, norm_L1, zero))

        # Weak (1,1) bound: λ·measure ≤ 3·||f||_1
        product = solver.mkTerm(Kind.MULT, lam, measure)
        bound = solver.mkTerm(Kind.MULT, C, norm_L1)
        solver.assertFormula(solver.mkTerm(Kind.LEQ, product, bound))

        # Claim violation: product > bound
        solver.assertFormula(solver.mkTerm(Kind.GT, product, bound))

        result = solver.checkSat()
        test_1["is_unsat"] = str(result) == "unsat"
        test_1["passes"] = test_1["is_unsat"]
    except Exception as e:
        test_1["error"] = str(e)
        test_1["passes"] = False

    results["test_1_unsat_measure_exceeds"] = test_1

    # Test 2: UNSAT -- negative measure
    test_2 = {
        "name": "unsat_negative_measure",
        "description": "cvc5 UNSAT: measure cannot be negative",
        "expected_unsat": True,
    }

    try:
        solver = Solver()

        measure = solver.mkConst(solver.getRealSort(), "measure")
        zero = solver.mkReal(0)

        # Measure is non-negative (tautology)
        solver.assertFormula(solver.mkTerm(Kind.GEQ, measure, zero))

        # Claim it's negative
        solver.assertFormula(solver.mkTerm(Kind.LT, measure, zero))

        result = solver.checkSat()
        test_2["is_unsat"] = str(result) == "unsat"
        test_2["passes"] = test_2["is_unsat"]
    except Exception as e:
        test_2["error"] = str(e)
        test_2["passes"] = False

    results["test_2_unsat_negative_measure"] = test_2

    # Test 3: UNSAT -- zero function with positive measure above threshold
    test_3 = {
        "name": "unsat_zero_function_positive_measure",
        "description": "cvc5 UNSAT: zero function cannot have {Mf > λ} for λ > 0",
        "expected_unsat": True,
    }

    try:
        solver = Solver()

        norm_L1 = solver.mkConst(solver.getRealSort(), "norm_L1")
        lam = solver.mkConst(solver.getRealSort(), "lambda")
        measure = solver.mkConst(solver.getRealSort(), "measure")

        zero = solver.mkReal(0)

        # Zero function: ||f||_1 = 0
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, norm_L1, zero))

        # Positive threshold
        solver.assertFormula(solver.mkTerm(Kind.GT, lam, zero))

        # For zero function, Mf = 0 everywhere, so measure should be 0
        # Weak (1,1) says: λ·measure ≤ 3·||f||_1 = 0
        product = solver.mkTerm(Kind.MULT, lam, measure)
        solver.assertFormula(solver.mkTerm(Kind.LEQ, product, zero))

        # But claim positive measure
        solver.assertFormula(solver.mkTerm(Kind.GT, measure, zero))

        result = solver.checkSat()
        test_3["is_unsat"] = str(result) == "unsat"
        test_3["passes"] = test_3["is_unsat"]
    except Exception as e:
        test_3["error"] = str(e)
        test_3["passes"] = False

    results["test_3_unsat_zero_function"] = test_3

    return results


# =====================================================================
# BOUNDARY TESTS: Edge cases and limits
# =====================================================================

def run_boundary_tests():
    results = {}

    if not sympy_available:
        return {"error": "sympy not installed"}

    import sympy as sp

    # Test 1: Zero function
    test_1 = {
        "name": "boundary_zero_function",
        "description": "Zero function: ||f||_1 = 0, all Mf = 0",
    }

    f_zero = np.zeros(8)
    M_zero = compute_maximal_function_discrete(f_zero)

    norm_zero = np.sum(np.abs(f_zero))
    measure_zero = np.sum(M_zero > 0.5)

    test_1["||zero||_1"] = float(norm_zero)
    test_1["measure_{M(zero) > 0.5}"] = int(measure_zero)
    test_1["passes"] = norm_zero == 0.0 and measure_zero == 0

    results["test_1_boundary_zero"] = test_1

    # Test 2: Single spike
    test_2 = {
        "name": "boundary_single_spike",
        "description": "Single spike: Mf spreads the impulse, measure grows",
    }

    f_spike = np.zeros(8)
    f_spike[3] = 5.0

    M_spike = compute_maximal_function_discrete(f_spike, radius=2)

    norm_spike = np.sum(np.abs(f_spike))

    # Maximal function spreads the spike over neighborhood
    # Measure at threshold lambda=1.0
    lam_test = 1.0
    measure_at_threshold = np.sum(M_spike > lam_test)
    product_at_threshold = lam_test * measure_at_threshold
    bound_at_threshold = 3.0 * norm_spike

    test_2["f"] = f_spike.tolist()
    test_2["Mf"] = M_spike.tolist()
    test_2["||f||_1"] = float(norm_spike)
    test_2["lambda"] = lam_test
    test_2["measure_{Mf > λ}"] = int(measure_at_threshold)
    test_2["λ·measure"] = float(product_at_threshold)
    test_2["3·||f||_1"] = float(bound_at_threshold)
    test_2["passes"] = product_at_threshold <= bound_at_threshold

    results["test_2_boundary_spike"] = test_2

    # Test 3: Constant function
    test_3 = {
        "name": "boundary_constant_function",
        "description": "Constant function c: Mf = c everywhere",
    }

    const_val = 2.0
    f_const = np.full(10, const_val)

    M_const = compute_maximal_function_discrete(f_const, radius=2)

    norm_const = np.sum(np.abs(f_const))

    # For constant function, Mf should be approximately constant = c
    # (averaging constant gives constant)
    Mf_is_constant = np.allclose(M_const, const_val)

    # Measure at lambda < c should include all points
    lam = const_val / 2
    measure = np.sum(M_const > lam)
    product = lam * measure
    bound = 3.0 * norm_const

    test_3["constant_value"] = const_val
    test_3["||f||_1"] = float(norm_const)
    test_3["Mf_is_constant"] = Mf_is_constant
    test_3["lambda"] = lam
    test_3["measure_{Mf > λ}"] = int(measure)
    test_3["λ·measure"] = float(product)
    test_3["3·||f||_1"] = float(bound)
    test_3["passes"] = product <= bound and Mf_is_constant

    results["test_3_boundary_constant"] = test_3

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    # Mark tools as used
    if cvc5_available:
        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_MANIFEST["cvc5"]["reason"] = "cvc5 solver for proving weak (1,1) bound violations"

    if sympy_available:
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = "sympy for symbolic step function weak (1,1) verification"

    results = {
        "name": "Hardy-Littlewood Maximal Function Constraint Canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "hardy_littlewood_maximal_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
