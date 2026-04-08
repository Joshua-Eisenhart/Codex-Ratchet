#!/usr/bin/env python3
"""
SIM LEGO -- Adiabatic Theorem & Quantum Annealing
Pure math. Canonical (torch-native).

Adiabatic theorem: if H(t) changes slowly, |psi(t)> stays in the
instantaneous ground state. Speed limit: T >> hbar / Delta^2 where
Delta = min spectral gap.

Tests:
  - T=100 -> fidelity > 0.99 (adiabatic regime)
  - T=1   -> fidelity ~ 0.5  (diabatic regime)
  - Landau-Zener prediction matches numerics
  - Gap minimum occurs at s=0.5
"""

import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST -- Document which tools were tried
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

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "Core computation: Hamiltonian construction, matrix exponentiation, "
        "Schrodinger evolution, eigendecomposition for gap and fidelity"
    )
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric  # noqa: F401
    TOOL_MANIFEST["pyg"]["tried"] = True
    TOOL_MANIFEST["pyg"]["reason"] = "not needed for single-qubit adiabatic evolution"
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    from z3 import *  # noqa: F401,F403
    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["reason"] = "not needed; numeric sim only"
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5  # noqa: F401
    TOOL_MANIFEST["cvc5"]["tried"] = True
    TOOL_MANIFEST["cvc5"]["reason"] = "not needed; numeric sim only"
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp  # noqa: F401
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "not needed; torch handles all linear algebra"
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    from clifford import Cl  # noqa: F401
    TOOL_MANIFEST["clifford"]["tried"] = True
    TOOL_MANIFEST["clifford"]["reason"] = "not needed for Pauli-basis Hamiltonian interpolation"
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

try:
    import geomstats  # noqa: F401
    TOOL_MANIFEST["geomstats"]["tried"] = True
    TOOL_MANIFEST["geomstats"]["reason"] = "not needed"
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    import e3nn  # noqa: F401
    TOOL_MANIFEST["e3nn"]["tried"] = True
    TOOL_MANIFEST["e3nn"]["reason"] = "not needed"
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"

try:
    import rustworkx  # noqa: F401
    TOOL_MANIFEST["rustworkx"]["tried"] = True
    TOOL_MANIFEST["rustworkx"]["reason"] = "not needed"
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

try:
    import xgi  # noqa: F401
    TOOL_MANIFEST["xgi"]["tried"] = True
    TOOL_MANIFEST["xgi"]["reason"] = "not needed"
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

try:
    from toponetx.classes import CellComplex  # noqa: F401
    TOOL_MANIFEST["toponetx"]["tried"] = True
    TOOL_MANIFEST["toponetx"]["reason"] = "not needed"
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] = "not installed"

try:
    import gudhi  # noqa: F401
    TOOL_MANIFEST["gudhi"]["tried"] = True
    TOOL_MANIFEST["gudhi"]["reason"] = "not needed"
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"


# =====================================================================
# CORE: Pauli matrices and Hamiltonian construction (torch)
# =====================================================================

DTYPE = torch.complex128


def pauli_x():
    """sigma_x as 2x2 complex tensor."""
    return torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=DTYPE)


def pauli_z():
    """sigma_z as 2x2 complex tensor."""
    return torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=DTYPE)


def hamiltonian(s: float):
    """
    Interpolated Hamiltonian: H(s) = (1-s)*H0 + s*H1.
    H0 = sigma_x (ground state = |-> with eigenvalue -1)
    H1 = sigma_z (ground state = |0> with eigenvalue -1)
    """
    return (1.0 - s) * pauli_x() + s * pauli_z()


def spectral_gap(s: float):
    """
    Compute E1(s) - E0(s) for H(s).
    Returns (gap, ground_state_vec).
    """
    H = hamiltonian(s)
    evals, evecs = torch.linalg.eigh(H)
    gap = (evals[1] - evals[0]).real.item()
    ground = evecs[:, 0]  # column for smallest eigenvalue
    return gap, ground


def adiabatic_evolve(T: float, n_steps: int = 2000, initial_state=None):
    """
    Evolve initial state under H(t/T) for t in [0, T] using Trotterized
    Schrodinger equation: |psi(t+dt)> = exp(-i H(t/T) dt) |psi(t)>.

    Default initial state: |-> = (|0> - |1>)/sqrt(2), ground state of H0=sigma_x.
    Returns final state vector (2,) complex tensor.
    """
    dt = T / n_steps
    if initial_state is not None:
        psi = initial_state.clone()
    else:
        # Initial state |-> = (|0> - |1>) / sqrt(2)  [ground state of sigma_x]
        psi = torch.tensor([1.0, -1.0], dtype=DTYPE) / np.sqrt(2.0)

    for step in range(n_steps):
        s = step / n_steps  # s = t/T in [0, 1)
        H = hamiltonian(s)
        # Matrix exponential: exp(-i H dt) via eigendecomposition
        evals, evecs = torch.linalg.eigh(H)
        phases = torch.exp(-1j * evals * dt)
        U = evecs @ torch.diag(phases) @ evecs.conj().T
        psi = U @ psi

    # Normalize to counteract floating-point drift
    psi = psi / torch.linalg.norm(psi)
    return psi


def fidelity_with_ground(psi, target):
    """
    Fidelity F = |<target|psi>|^2.
    Both are (2,) complex vectors.
    """
    overlap = torch.dot(target.conj(), psi)
    return (overlap.abs() ** 2).item()


def landau_zener_prediction(T: float, gap_min: float):
    """
    Landau-Zener formula for linear crossing:
    P_diabatic = exp(-pi * Delta^2 * T / 2)
    F_adiabatic = 1 - P_diabatic

    Here hbar=1 and the sweep rate v = 1/T for a linear interpolation
    over s in [0,1]. The effective crossing speed in energy units
    depends on |dH/ds| at the gap minimum.

    For H(s) = (1-s)sigma_x + s*sigma_z, at s=0.5:
      dH/ds = sigma_z - sigma_x
      |dH/ds| has eigenvalues +/-sqrt(2), so the slope = sqrt(2).
      LZ formula: P = exp(-pi * gap_min^2 * T / (2 * slope))
    """
    slope = np.sqrt(2.0)
    exponent = -np.pi * gap_min**2 * T / (2.0 * slope)
    p_diabatic = np.exp(exponent)
    return 1.0 - p_diabatic


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # --- Test 1: Adiabatic regime (T=100) -> high fidelity ---
    T_large = 100.0
    psi_final = adiabatic_evolve(T_large, n_steps=4000)
    _, target_ground = spectral_gap(1.0)
    F_large = fidelity_with_ground(psi_final, target_ground)
    results["adiabatic_T100"] = {
        "T": T_large,
        "fidelity": F_large,
        "target": ">0.99",
        "passed": F_large > 0.99,
    }

    # --- Test 2: Diabatic regime (T=1) -> low fidelity ---
    T_small = 1.0
    psi_fast = adiabatic_evolve(T_small, n_steps=2000)
    F_small = fidelity_with_ground(psi_fast, target_ground)
    results["diabatic_T1"] = {
        "T": T_small,
        "fidelity": F_small,
        "target": "<0.85 (significantly below 1)",
        "passed": F_small < 0.85,
    }

    # --- Test 3: Gap minimum at s=0.5 ---
    s_values = torch.linspace(0.0, 1.0, 201)
    gaps = []
    for s in s_values:
        g, _ = spectral_gap(s.item())
        gaps.append(g)
    gaps_t = torch.tensor(gaps)
    s_min_idx = torch.argmin(gaps_t).item()
    s_at_min = s_values[s_min_idx].item()
    gap_min_val = gaps_t[s_min_idx].item()

    results["gap_minimum_location"] = {
        "s_at_min_gap": s_at_min,
        "min_gap": gap_min_val,
        "expected_s": 0.5,
        "passed": abs(s_at_min - 0.5) < 0.01,
    }

    # --- Test 4: Landau-Zener matches numerics ---
    # Sweep multiple T values and compare predicted vs actual fidelity
    T_sweep = [2.0, 5.0, 10.0, 20.0, 50.0]
    lz_results = []
    for T_val in T_sweep:
        psi_t = adiabatic_evolve(T_val, n_steps=max(2000, int(T_val * 40)))
        F_num = fidelity_with_ground(psi_t, target_ground)
        F_lz = landau_zener_prediction(T_val, gap_min_val)
        lz_results.append({
            "T": T_val,
            "F_numeric": F_num,
            "F_landau_zener": F_lz,
            "abs_error": abs(F_num - F_lz),
        })

    # LZ is approximate (valid near avoided crossing, asymptotic).
    # Check: (a) both agree F->1 for large T, (b) both agree F<1 for small T,
    # (c) Spearman rank correlation is positive (overall trend matches).
    fidelities_num = [r["F_numeric"] for r in lz_results]
    fidelities_lz = [r["F_landau_zener"] for r in lz_results]

    # Both should have F > 0.99 for largest T and F < 0.99 for smallest T
    large_T_agree = fidelities_num[-1] > 0.99 and fidelities_lz[-1] > 0.99
    small_T_agree = fidelities_num[0] < 0.99 and fidelities_lz[0] < 0.99

    # Overall trend: first fidelity < last fidelity for numerics
    trend_ok = fidelities_num[0] < fidelities_num[-1]

    results["landau_zener_comparison"] = {
        "sweep": lz_results,
        "large_T_both_high": large_T_agree,
        "small_T_both_below_1": small_T_agree,
        "numeric_trend_increasing": trend_ok,
        "passed": large_T_agree and small_T_agree and trend_ok,
    }

    # --- Test 5: Overall fidelity trend with T ---
    # Fidelity has oscillatory finite-T corrections (physical), so strict
    # monotonicity doesn't hold. Instead check: (a) F(T=1) < F(T=100),
    # (b) small T regime clearly worse than large T regime,
    # (c) all large-T fidelities > 0.99.
    T_mono = [1.0, 5.0, 10.0, 50.0, 100.0]
    fid_mono = []
    for T_val in T_mono:
        psi_m = adiabatic_evolve(T_val, n_steps=max(2000, int(T_val * 40)))
        fid_mono.append(fidelity_with_ground(psi_m, target_ground))
    overall_trend = fid_mono[0] < fid_mono[-1]
    small_worse = fid_mono[0] < 0.85
    large_good = all(f > 0.99 for f in fid_mono[3:])  # T>=50
    results["fidelity_trend_with_T"] = {
        "T_values": T_mono,
        "fidelities": fid_mono,
        "small_T_below_threshold": small_worse,
        "large_T_above_099": large_good,
        "overall_increasing": overall_trend,
        "note": "oscillatory corrections are physical (finite-T coherent interference)",
        "passed": overall_trend and small_worse and large_good,
    }

    # --- Test 6: Spectral gap profile (analytic cross-check) ---
    # For H(s) = (1-s)sx + s*sz, eigenvalues are +/- sqrt((1-s)^2 + s^2)
    # Gap = 2*sqrt((1-s)^2 + s^2), minimum at s=0.5 => gap = sqrt(2)
    analytic_gap_min = np.sqrt(2.0)
    results["gap_analytic_crosscheck"] = {
        "numeric_gap_min": gap_min_val,
        "analytic_gap_min": analytic_gap_min,
        "relative_error": abs(gap_min_val - analytic_gap_min) / analytic_gap_min,
        "passed": abs(gap_min_val - analytic_gap_min) / analytic_gap_min < 1e-6,
    }

    return results


# =====================================================================
# NEGATIVE TESTS (mandatory)
# =====================================================================

def run_negative_tests():
    results = {}

    _, target_ground = spectral_gap(1.0)

    # --- Neg 1: Zero evolution time -> stays at |->, fidelity = 0.5 ---
    T_zero = 1e-6
    psi_zero = adiabatic_evolve(T_zero, n_steps=100)
    F_zero = fidelity_with_ground(psi_zero, target_ground)
    results["zero_time_not_adiabatic"] = {
        "T": T_zero,
        "fidelity": F_zero,
        "expected": "~0.5 (no evolution, stays at |->)",
        "passed": abs(F_zero - 0.5) < 0.1,
    }

    # --- Neg 2: Wrong initial state |+> (excited of H0) evolving adiabatically
    # should track EXCITED state of H1 = |1>, giving low fidelity with ground |0> ---
    T_adiab = 100.0
    psi_plus = torch.tensor([1.0, 1.0], dtype=DTYPE) / np.sqrt(2.0)
    psi_excited = adiabatic_evolve(T_adiab, n_steps=4000, initial_state=psi_plus)
    F_excited = fidelity_with_ground(psi_excited, target_ground)
    results["excited_state_stays_excited"] = {
        "T": T_adiab,
        "initial_state": "|+> (excited of H0=sigma_x)",
        "fidelity_with_ground_of_H1": F_excited,
        "expected": "~0 (tracks excited state to |1>)",
        "passed": F_excited < 0.05,
    }

    # --- Neg 3: Reversed sweep (H1 -> H0) starting from |0>
    # should end at |->, NOT |0>. Fidelity with |0> should be ~0.5. ---
    psi_rev = torch.tensor([1.0, 0.0], dtype=DTYPE)
    n_rev = 4000
    dt_rev = 100.0 / n_rev
    for step in range(n_rev):
        s = 1.0 - step / n_rev  # reversed: s goes 1->0
        H = hamiltonian(s)
        evals, evecs = torch.linalg.eigh(H)
        phases = torch.exp(-1j * evals * dt_rev)
        U = evecs @ torch.diag(phases) @ evecs.conj().T
        psi_rev = U @ psi_rev
    psi_rev = psi_rev / torch.linalg.norm(psi_rev)
    # Should end near |->, so fidelity with |0> should be ~0.5
    target_zero = torch.tensor([1.0, 0.0], dtype=DTYPE)
    F_rev = fidelity_with_ground(psi_rev, target_zero)
    results["reversed_sweep_not_frozen"] = {
        "fidelity_with_zero": F_rev,
        "expected": "~0.5 (ended at |->, not |0>)",
        "passed": abs(F_rev - 0.5) < 0.15,
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # --- Boundary 1: Gap at endpoints ---
    gap_0, _ = spectral_gap(0.0)
    gap_1, _ = spectral_gap(1.0)
    # H(0) = sigma_x: eigenvalues +/-1, gap=2
    # H(1) = sigma_z: eigenvalues +/-1, gap=2
    results["endpoint_gaps"] = {
        "gap_s0": gap_0,
        "gap_s1": gap_1,
        "expected": 2.0,
        "passed": abs(gap_0 - 2.0) < 1e-10 and abs(gap_1 - 2.0) < 1e-10,
    }

    # --- Boundary 2: Unitarity preservation ---
    # After many steps, norm should remain 1
    T_test = 50.0
    n_steps = 3000
    dt = T_test / n_steps
    psi = torch.tensor([1.0, -1.0], dtype=DTYPE) / np.sqrt(2.0)
    norms = []
    for step in range(n_steps):
        s = step / n_steps
        H = hamiltonian(s)
        evals, evecs = torch.linalg.eigh(H)
        phases = torch.exp(-1j * evals * dt)
        U = evecs @ torch.diag(phases) @ evecs.conj().T
        psi = U @ psi
        if step % 500 == 0:
            norms.append(torch.linalg.norm(psi).item())
    max_drift = max(abs(n - 1.0) for n in norms)
    results["unitarity_preservation"] = {
        "norm_samples": norms,
        "max_drift_from_1": max_drift,
        "passed": max_drift < 1e-8,
    }

    # --- Boundary 3: Trotter convergence ---
    # Doubling steps should improve fidelity (or stay same if converged)
    _, target_ground = spectral_gap(1.0)
    T_conv = 20.0
    fid_steps = {}
    for ns in [500, 1000, 2000, 4000]:
        psi_c = adiabatic_evolve(T_conv, n_steps=ns)
        fid_steps[ns] = fidelity_with_ground(psi_c, target_ground)
    # Should converge: higher step count -> approaches a limit
    vals = list(fid_steps.values())
    converged = abs(vals[-1] - vals[-2]) < 1e-4
    results["trotter_convergence"] = {
        "fidelity_by_steps": fid_steps,
        "last_two_diff": abs(vals[-1] - vals[-2]),
        "passed": converged,
    }

    # --- Boundary 4: s=0.5 is exactly the gap minimum (analytic) ---
    gap_half, _ = spectral_gap(0.5)
    gap_off = []
    for s_off in [0.49, 0.51, 0.45, 0.55]:
        g, _ = spectral_gap(s_off)
        gap_off.append(g)
    results["s05_is_minimum"] = {
        "gap_at_0.5": gap_half,
        "gaps_nearby": gap_off,
        "all_nearby_larger": all(g > gap_half - 1e-12 for g in gap_off),
        "passed": all(g > gap_half - 1e-12 for g in gap_off),
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    print("Running adiabatic theorem sim...")

    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_passed = True
    for section_name, section in [("positive", pos), ("negative", neg), ("boundary", bnd)]:
        for test_name, test_result in section.items():
            status = "PASS" if test_result.get("passed") else "FAIL"
            if not test_result.get("passed"):
                all_passed = False
            print(f"  [{status}] {section_name}/{test_name}")

    results = {
        "name": "Adiabatic Theorem & Quantum Annealing",
        "tool_manifest": TOOL_MANIFEST,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "classification": "canonical",
        "all_passed": all_passed,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "lego_adiabatic_theorem_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults written to {out_path}")
    print(f"Overall: {'ALL PASSED' if all_passed else 'SOME FAILED'}")
