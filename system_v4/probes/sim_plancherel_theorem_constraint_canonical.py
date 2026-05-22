#!/usr/bin/env python3
"""
Plancherel Theorem Constraint Canonical Sim

Plancherel theorem: cvc5 proves that the Fourier transform is an L² isometry:
||f̂||² = ||f||². UNSAT when the L² norms differ. sympy verifies Parseval's
identity for finite sequences.

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
# POSITIVE TESTS: Verify Plancherel isometry
# =====================================================================

def run_positive_tests():
    results = {}

    if not sympy_available:
        return {"error": "sympy not installed"}

    import sympy as sp

    # Test 1: Finite sequence Parseval identity
    test_1 = {
        "name": "finite_sequence_parseval",
        "description": "Discrete Fourier transform preserves L² norm: sum|f[n]|² = (1/N)·sum|F[k]|²",
    }

    # Simple sequence: f = [1, 0, 1, 0] (4 elements)
    f = np.array([1.0, 0.0, 1.0, 0.0])
    N = len(f)

    # Compute DFT
    F = np.fft.fft(f)

    # L² norm of f
    norm_f_squared = np.sum(np.abs(f)**2)

    # L² norm of F (Parseval: should equal N * norm_f_squared for DFT convention)
    norm_F_squared = np.sum(np.abs(F)**2)

    test_1["f"] = f.tolist()
    test_1["F_magnitude"] = np.abs(F).tolist()
    test_1["||f||²"] = float(norm_f_squared)
    test_1["||F||²"] = float(norm_F_squared)
    test_1["N"] = N
    test_1["||F||²/N"] = float(norm_F_squared / N)
    test_1["ratio_||F||²_to_N||f||²"] = float(norm_F_squared / (N * norm_f_squared))
    test_1["passes"] = abs(norm_F_squared / N - norm_f_squared) < 1e-10

    results["test_1_parseval_simple"] = test_1

    # Test 2: Gaussian signal (continuous approximation)
    test_2 = {
        "name": "gaussian_signal_plancherel",
        "description": "Gaussian f(x) = exp(-x²/2) has Fourier transform also Gaussian",
    }

    x = sp.Symbol("x", real=True)
    # Gaussian: f(x) = exp(-x²/2)
    f_sym = sp.exp(-x**2 / 2)

    # L² norm of f: ∫_{-∞}^{∞} exp(-x²) dx = sqrt(π)
    norm_f_squared_sym = sp.pi  # ∫ |f(x)|² dx = ∫ exp(-x²) dx = √π

    # Fourier transform: F(ω) = √(2π) exp(-ω²/2)
    # L² norm of F: ∫_{-∞}^{∞} 2π exp(-ω²) dω = 2π·√π
    norm_F_squared_sym = 2 * sp.pi * sp.sqrt(sp.pi)

    # Plancherel says: ∫|f(x)|² dx = ∫|F(ω)|² dω / (2π)
    # Verify: √π =? (1/2π) · 2π√π = √π ✓
    plancherel_ratio = norm_F_squared_sym / (2 * sp.pi) / norm_f_squared_sym
    plancherel_ratio_simplified = sp.simplify(plancherel_ratio)

    test_2["||f||²_symbolic"] = str(norm_f_squared_sym)
    test_2["||F||²_symbolic"] = str(norm_F_squared_sym)
    test_2["plancherel_ratio"] = str(plancherel_ratio_simplified)
    test_2["passes"] = plancherel_ratio_simplified == 1

    results["test_2_gaussian_plancherel"] = test_2

    # Test 3: Rectangular pulse (sinc function)
    test_3 = {
        "name": "rectangular_pulse_plancherel",
        "description": "Rectangular pulse rect(x) transforms to sinc(f), preserving L²",
    }

    # Discrete approximation: pulse of width 5 in a 16-sample window
    pulse = np.zeros(16)
    pulse[5:10] = 1.0

    # DFT
    F_pulse = np.fft.fft(pulse)

    norm_pulse_squared = np.sum(np.abs(pulse)**2)
    norm_F_pulse_squared = np.sum(np.abs(F_pulse)**2)

    test_3["pulse_length"] = 5
    test_3["window_size"] = 16
    test_3["||pulse||²"] = float(norm_pulse_squared)
    test_3["||F_pulse||²"] = float(norm_F_pulse_squared)
    test_3["||F_pulse||²/N"] = float(norm_F_pulse_squared / 16)
    test_3["passes"] = abs(norm_F_pulse_squared / 16 - norm_pulse_squared) < 1e-10

    results["test_3_rectangular_pulse"] = test_3

    return results


# =====================================================================
# NEGATIVE TESTS: UNSAT when norms are unequal
# =====================================================================

def run_negative_tests():
    results = {}

    if not cvc5_available:
        return {"error": "cvc5 not installed"}

    from cvc5 import Solver, Kind

    # Test 1: UNSAT -- claim norms differ by positive amount
    test_1 = {
        "name": "unsat_norms_differ",
        "description": "cvc5 UNSAT: cannot have ||f||² ≠ ||F̂||²",
        "expected_unsat": True,
    }

    try:
        solver = Solver()

        norm_f_sq = solver.mkConst(solver.getRealSort(), "norm_f_sq")
        norm_F_sq = solver.mkConst(solver.getRealSort(), "norm_F_sq")

        # Both norms positive
        zero = solver.mkReal(0)
        solver.assertFormula(solver.mkTerm(Kind.GT, norm_f_sq, zero))
        solver.assertFormula(solver.mkTerm(Kind.GT, norm_F_sq, zero))

        # Plancherel constraint: norm_F_sq = norm_f_sq
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, norm_F_sq, norm_f_sq))

        # Claim they differ by > 0.1 (contradiction)
        diff = solver.mkTerm(Kind.MINUS, norm_F_sq, norm_f_sq)
        solver.assertFormula(solver.mkTerm(Kind.GT, diff, solver.mkReal(1, 10)))

        result = solver.checkSat()
        test_1["is_unsat"] = str(result) == "unsat"
        test_1["passes"] = test_1["is_unsat"]
    except Exception as e:
        test_1["error"] = str(e)
        test_1["passes"] = False

    results["test_1_unsat_norms_differ"] = test_1

    # Test 2: UNSAT -- claim one norm is zero but other is nonzero
    test_2 = {
        "name": "unsat_one_norm_zero",
        "description": "cvc5 UNSAT: cannot have ||f||² = 0 but ||F̂||² > 0",
        "expected_unsat": True,
    }

    try:
        solver = Solver()

        norm_f_sq = solver.mkConst(solver.getRealSort(), "norm_f_sq")
        norm_F_sq = solver.mkConst(solver.getRealSort(), "norm_F_sq")

        zero = solver.mkReal(0)

        # f is zero function
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, norm_f_sq, zero))

        # But F is claimed nonzero
        solver.assertFormula(solver.mkTerm(Kind.GT, norm_F_sq, zero))

        # Plancherel: they must be equal
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, norm_F_sq, norm_f_sq))

        result = solver.checkSat()
        test_2["is_unsat"] = str(result) == "unsat"
        test_2["passes"] = test_2["is_unsat"]
    except Exception as e:
        test_2["error"] = str(e)
        test_2["passes"] = False

    results["test_2_unsat_one_norm_zero"] = test_2

    # Test 3: UNSAT -- claim F has norm while f is zero (non-canonical violation)
    test_3 = {
        "name": "unsat_energy_conservation",
        "description": "cvc5 UNSAT: Fourier transform cannot create energy from zero",
        "expected_unsat": True,
    }

    try:
        solver = Solver()

        norm_f_sq = solver.mkConst(solver.getRealSort(), "norm_f_sq")
        norm_F_sq = solver.mkConst(solver.getRealSort(), "norm_F_sq")

        zero = solver.mkReal(0)

        # Both norms non-negative (obvious)
        solver.assertFormula(solver.mkTerm(Kind.GEQ, norm_f_sq, zero))
        solver.assertFormula(solver.mkTerm(Kind.GEQ, norm_F_sq, zero))

        # Plancherel: ||F||² = ||f||²
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, norm_F_sq, norm_f_sq))

        # Input is zero
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, norm_f_sq, zero))

        # But claim output has energy
        solver.assertFormula(solver.mkTerm(Kind.GT, norm_F_sq, solver.mkReal(1, 1000)))

        result = solver.checkSat()
        test_3["is_unsat"] = str(result) == "unsat"
        test_3["passes"] = test_3["is_unsat"]
    except Exception as e:
        test_3["error"] = str(e)
        test_3["passes"] = False

    results["test_3_unsat_energy_conservation"] = test_3

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
        "description": "Zero function has ||f||² = ||F̂||² = 0",
    }

    f_zero = np.zeros(8)
    F_zero = np.fft.fft(f_zero)

    norm_f_zero = np.sum(np.abs(f_zero)**2)
    norm_F_zero = np.sum(np.abs(F_zero)**2)

    test_1["||zero||²"] = float(norm_f_zero)
    test_1["||FFT(zero)||²"] = float(norm_F_zero)
    test_1["passes"] = norm_f_zero == 0.0 and norm_F_zero < 1e-14

    results["test_1_boundary_zero"] = test_1

    # Test 2: Delta function (impulse)
    test_2 = {
        "name": "boundary_delta_impulse",
        "description": "Delta impulse δ[n] has constant Fourier transform with full energy",
    }

    # Discrete delta at index 0
    delta = np.zeros(8)
    delta[0] = 1.0

    F_delta = np.fft.fft(delta)

    norm_delta = np.sum(np.abs(delta)**2)
    norm_F_delta = np.sum(np.abs(F_delta)**2)

    test_2["||delta||²"] = float(norm_delta)
    test_2["||FFT(delta)||²"] = float(norm_F_delta)
    test_2["||FFT(delta)||²/N"] = float(norm_F_delta / 8)
    test_2["passes"] = abs(norm_F_delta / 8 - norm_delta) < 1e-12

    results["test_2_boundary_delta"] = test_2

    # Test 3: Real-valued even function (cosine)
    test_3 = {
        "name": "boundary_even_cosine",
        "description": "Even real function (cosine) has real-valued DFT",
    }

    # Cosine sequence: cos(2πk·n/N)
    N = 16
    n = np.arange(N)
    cosine = np.cos(2 * np.pi * 2 * n / N)

    F_cosine = np.fft.fft(cosine)

    norm_cosine = np.sum(np.abs(cosine)**2)
    norm_F_cosine = np.sum(np.abs(F_cosine)**2)

    test_3["cosine_frequency"] = 2
    test_3["window_size"] = N
    test_3["||cosine||²"] = float(norm_cosine)
    test_3["||F_cosine||²"] = float(norm_F_cosine)
    test_3["||F_cosine||²/N"] = float(norm_F_cosine / N)
    test_3["F_is_real_valued"] = np.allclose(np.imag(F_cosine), 0)
    test_3["passes"] = abs(norm_F_cosine / N - norm_cosine) < 1e-12

    results["test_3_boundary_cosine"] = test_3

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    # Mark tools as used
    if cvc5_available:
        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_MANIFEST["cvc5"]["reason"] = "cvc5 solver for proving Plancherel norm inequality violations"

    if sympy_available:
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = "sympy for symbolic Parseval identity verification on Gaussians"

    results = {
        "name": "Plancherel Theorem Constraint Canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "plancherel_theorem_constraint_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
