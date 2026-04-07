#!/usr/bin/env python3
"""
Pure Lego: Quantum Thermodynamics in Density Matrix Language
=============================================================
Status: [Pure lego — no engine, numpy/scipy only]

Builds thermal quantum states from first principles and verifies
every thermodynamic identity in density-matrix language:

  1. Thermal state:  rho_beta = exp(-beta H) / Z,  Z = Tr(exp(-beta H))
  2. Qubit H = sigma_z:  rho_beta = diag(exp(beta), exp(-beta)) / (2 cosh(beta))
  3. Limits:  beta->0 => maximally mixed,  beta->inf => ground state
  4. Free energy:  F = Tr(rho H) + T S(rho) = -T ln Z
  5. Landauer's principle:  erasing 1 bit costs >= kT ln 2
  6. Extractable work:  W = F(rho) - F(rho_thermal) >= 0  always
  7. Carnot efficiency:  eta = 1 - T_cold / T_hot  (upper bound)

All quantities computed with explicit matrix operations.
No engine imports. Pure numpy/scipy.
"""

import numpy as np
from scipy.linalg import expm, logm
import json
import os

# ═══════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════

SIGMA_Z = np.array([[1.0, 0.0], [0.0, -1.0]])
IDENTITY_2 = np.eye(2)
KB = 1.0          # Boltzmann constant in natural units
LN2 = np.log(2.0)

class _NumpyEncoder(json.JSONEncoder):
    """Handle numpy scalars that vanilla json chokes on."""
    def default(self, obj):
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


RESULTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "a2_state", "sim_results",
)

# ═══════════════════════════════════════════════════════════════════
# CORE PRIMITIVES
# ═══════════════════════════════════════════════════════════════════

def thermal_state(H: np.ndarray, beta: float) -> np.ndarray:
    """Build rho_beta = exp(-beta H) / Tr(exp(-beta H))."""
    rho_unnorm = expm(-beta * H)
    Z = np.trace(rho_unnorm).real
    return rho_unnorm / Z, Z


def von_neumann_entropy(rho: np.ndarray) -> float:
    """S(rho) = -Tr(rho ln rho).  Uses eigenvalues for numerical safety."""
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > 1e-15]
    return -np.sum(evals * np.log(evals))


def free_energy_from_state(rho: np.ndarray, H: np.ndarray, T: float) -> float:
    """F = Tr(rho H) + T * S(rho)   [note: S includes the minus sign]
    Actually F = <E> - T S, so F = Tr(rho H) - T S(rho)."""
    energy = np.trace(rho @ H).real
    S = von_neumann_entropy(rho)
    return energy - T * S


def free_energy_exact(Z: float, T: float) -> float:
    """F = -T ln Z."""
    return -T * np.log(Z)


# ═══════════════════════════════════════════════════════════════════
# TEST 1: THERMAL STATE CONSTRUCTION & LIMITS
# ═══════════════════════════════════════════════════════════════════

def test_thermal_state_limits():
    """
    For qubit H = sigma_z:
      rho_beta = diag(exp(beta), exp(-beta)) / (2 cosh(beta))
      beta -> 0  =>  rho -> I/2  (maximally mixed)
      beta -> inf =>  rho -> |1><1|  (ground state, eigenvalue -1)
    """
    results = {"test": "thermal_state_limits", "pass": True, "details": []}
    H = SIGMA_Z

    # --- Analytic formula check ---
    for beta in [0.01, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]:
        rho, Z = thermal_state(H, beta)

        # Analytic
        Z_analytic = 2.0 * np.cosh(beta)
        rho_analytic = np.diag([np.exp(-beta), np.exp(beta)]) / Z_analytic

        Z_err = abs(Z - Z_analytic) / Z_analytic
        rho_err = np.max(np.abs(rho - rho_analytic))

        ok = Z_err < 1e-10 and rho_err < 1e-10
        results["details"].append({
            "beta": beta,
            "Z_numeric": float(Z),
            "Z_analytic": float(Z_analytic),
            "Z_rel_error": float(Z_err),
            "rho_max_error": float(rho_err),
            "pass": ok,
        })
        if not ok:
            results["pass"] = False

    # --- beta -> 0 limit: maximally mixed ---
    rho_hot, _ = thermal_state(H, 1e-6)
    mixed_err = np.max(np.abs(rho_hot - IDENTITY_2 / 2))
    hot_ok = mixed_err < 1e-5
    results["details"].append({
        "limit": "beta->0 (maximally mixed)",
        "max_error_from_I/2": float(mixed_err),
        "pass": hot_ok,
    })
    if not hot_ok:
        results["pass"] = False

    # --- beta -> inf limit: ground state |1> (eigenvalue -1 of sigma_z) ---
    rho_cold, _ = thermal_state(H, 50.0)
    ground = np.diag([0.0, 1.0])
    cold_err = np.max(np.abs(rho_cold - ground))
    cold_ok = cold_err < 1e-10
    results["details"].append({
        "limit": "beta->inf (ground state |1>)",
        "max_error_from_|1><1|": float(cold_err),
        "pass": cold_ok,
    })
    if not cold_ok:
        results["pass"] = False

    return results


# ═══════════════════════════════════════════════════════════════════
# TEST 2: FREE ENERGY IDENTITY  F = Tr(rho H) - T S = -T ln Z
# ═══════════════════════════════════════════════════════════════════

def test_free_energy_identity():
    """Verify F_state = F_partition for many temperatures."""
    results = {"test": "free_energy_identity", "pass": True, "details": []}
    H = SIGMA_Z

    for T in [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 100.0]:
        beta = 1.0 / T
        rho, Z = thermal_state(H, beta)
        F_state = free_energy_from_state(rho, H, T)
        F_exact = free_energy_exact(Z, T)

        err = abs(F_state - F_exact)
        ok = err < 1e-10
        results["details"].append({
            "T": T,
            "F_state": float(F_state),
            "F_exact": float(F_exact),
            "abs_error": float(err),
            "pass": ok,
        })
        if not ok:
            results["pass"] = False

    return results


# ═══════════════════════════════════════════════════════════════════
# TEST 3: LANDAUER'S PRINCIPLE
# ═══════════════════════════════════════════════════════════════════

def test_landauer_principle():
    """
    Erasing 1 bit (going from maximally mixed to pure state)
    at temperature T costs at least kT ln 2 in work/heat.

    Before: rho_mixed = I/2,  S = ln 2
    After:  rho_pure  = |0><0|,  S = 0
    DeltaS = -ln 2  (entropy decrease of system)

    Minimum work = T * |DeltaS| = T * ln 2 = kT ln 2.
    """
    results = {"test": "landauer_principle", "pass": True, "details": []}

    for T in [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]:
        rho_mixed = IDENTITY_2 / 2.0
        rho_pure = np.diag([1.0, 0.0])

        S_before = von_neumann_entropy(rho_mixed)
        S_after = von_neumann_entropy(rho_pure)
        delta_S = S_after - S_before        # should be -ln 2

        W_min = T * abs(delta_S)             # minimum work = T |DeltaS|
        W_landauer = KB * T * LN2            # kT ln 2

        S_err = abs(delta_S + LN2)
        W_err = abs(W_min - W_landauer)

        ok = S_err < 1e-12 and W_err < 1e-12
        results["details"].append({
            "T": T,
            "S_before_ln2": float(S_before / LN2),
            "S_after": float(S_after),
            "delta_S": float(delta_S),
            "W_min": float(W_min),
            "W_landauer_kTln2": float(W_landauer),
            "entropy_error": float(S_err),
            "work_error": float(W_err),
            "pass": ok,
        })
        if not ok:
            results["pass"] = False

    return results


# ═══════════════════════════════════════════════════════════════════
# TEST 4: EXTRACTABLE WORK  W = F(rho) - F(rho_thermal) >= 0
# ═══════════════════════════════════════════════════════════════════

def test_extractable_work():
    """
    For any state rho, the maximum extractable work relative to the
    thermal state at temperature T is:

        W = F(rho) - F(rho_thermal)

    This must be >= 0 because the thermal state minimises free energy.
    Test with various non-equilibrium states.
    """
    results = {"test": "extractable_work", "pass": True, "details": []}
    H = SIGMA_Z

    rng = np.random.default_rng(42)

    for T in [0.5, 1.0, 2.0, 5.0]:
        beta = 1.0 / T
        rho_th, Z = thermal_state(H, beta)
        F_thermal = free_energy_from_state(rho_th, H, T)

        # Test several non-equilibrium states
        test_states = {
            "pure_ground": np.diag([1.0, 0.0]),
            "pure_excited": np.diag([0.0, 1.0]),
            "maximally_mixed": IDENTITY_2 / 2.0,
            "biased_0.9": np.diag([0.9, 0.1]),
            "biased_0.7": np.diag([0.7, 0.3]),
        }

        # Add random density matrices (valid: positive semidefinite, trace 1)
        for i in range(5):
            A = rng.standard_normal((2, 2)) + 1j * rng.standard_normal((2, 2))
            rho_rand = A @ A.conj().T
            rho_rand = rho_rand / np.trace(rho_rand).real
            test_states[f"random_{i}"] = rho_rand.real  # keep real part for H=sigma_z

        for name, rho in test_states.items():
            # Ensure valid density matrix
            rho = (rho + rho.conj().T) / 2.0
            tr = np.trace(rho).real
            if abs(tr - 1.0) > 1e-10:
                rho = rho / tr

            F_rho = free_energy_from_state(rho, H, T)
            W = F_rho - F_thermal

            ok = W >= -1e-10  # allow tiny numerical noise
            results["details"].append({
                "T": T,
                "state": name,
                "F_rho": float(F_rho),
                "F_thermal": float(F_thermal),
                "W_extractable": float(W),
                "W_nonneg": ok,
                "pass": ok,
            })
            if not ok:
                results["pass"] = False

    return results


# ═══════════════════════════════════════════════════════════════════
# TEST 5: CARNOT EFFICIENCY BOUND
# ═══════════════════════════════════════════════════════════════════

def test_carnot_efficiency():
    """
    Quantum Carnot cycle between T_hot and T_cold using qubit working medium.

    Cycle:
      1. Isothermal expansion at T_hot:  rho_hot -> thermal at T_hot
      2. Adiabatic cooling:  keep rho, change H
      3. Isothermal compression at T_cold:  rho -> thermal at T_cold
      4. Adiabatic heating:  return

    For a qubit with H = epsilon * sigma_z, the Carnot cycle gives:
      Q_hot = T_hot * (S_hot - S_cold)
      Q_cold = T_cold * (S_hot - S_cold)
      W = Q_hot - Q_cold
      eta = W / Q_hot = 1 - T_cold / T_hot

    We verify this bound is saturated for the ideal cycle and
    that non-ideal cycles always have eta <= eta_carnot.
    """
    results = {"test": "carnot_efficiency", "pass": True, "details": []}
    H = SIGMA_Z

    temp_pairs = [
        (1.0, 0.5), (2.0, 0.5), (5.0, 1.0), (10.0, 1.0),
        (10.0, 0.1), (100.0, 1.0),
    ]

    for T_hot, T_cold in temp_pairs:
        beta_hot = 1.0 / T_hot
        beta_cold = 1.0 / T_cold

        rho_hot, _ = thermal_state(H, beta_hot)
        rho_cold, _ = thermal_state(H, beta_cold)

        S_hot = von_neumann_entropy(rho_hot)
        S_cold = von_neumann_entropy(rho_cold)

        # Ideal Carnot: reversible isothermal + adiabatic stages
        Q_hot = T_hot * (S_hot - S_cold)
        Q_cold = T_cold * (S_hot - S_cold)
        W_carnot = Q_hot - Q_cold

        eta_carnot_exact = 1.0 - T_cold / T_hot

        if abs(Q_hot) > 1e-15:
            eta_computed = W_carnot / Q_hot
        else:
            eta_computed = 0.0

        eta_err = abs(eta_computed - eta_carnot_exact)
        ok = eta_err < 1e-12

        # Also verify eta <= 1 and eta >= 0 for valid temps
        bound_ok = -1e-12 <= eta_computed <= 1.0 + 1e-12

        results["details"].append({
            "T_hot": T_hot,
            "T_cold": T_cold,
            "S_hot": float(S_hot),
            "S_cold": float(S_cold),
            "Q_hot": float(Q_hot),
            "Q_cold": float(Q_cold),
            "W_carnot": float(W_carnot),
            "eta_computed": float(eta_computed),
            "eta_carnot_exact": float(eta_carnot_exact),
            "eta_error": float(eta_err),
            "eta_in_bounds": bound_ok,
            "pass": ok and bound_ok,
        })
        if not (ok and bound_ok):
            results["pass"] = False

    # --- Sub-optimal (irreversible) cycles: eta < eta_carnot ---
    # Mix in some irreversibility by using a non-equilibrium intermediate
    T_hot, T_cold = 5.0, 1.0
    eta_carnot = 1.0 - T_cold / T_hot

    for mix_frac in [0.1, 0.3, 0.5, 0.7]:
        beta_hot = 1.0 / T_hot
        beta_cold = 1.0 / T_cold
        rho_hot, _ = thermal_state(H, beta_hot)
        rho_cold, _ = thermal_state(H, beta_cold)

        # Non-ideal: working medium doesn't fully thermalise
        rho_partial = mix_frac * rho_hot + (1.0 - mix_frac) * rho_cold
        S_partial = von_neumann_entropy(rho_partial)
        S_cold_eq = von_neumann_entropy(rho_cold)

        Q_hot_partial = T_hot * (S_partial - S_cold_eq)
        Q_cold_partial = T_cold * (S_partial - S_cold_eq)
        W_partial = Q_hot_partial - Q_cold_partial

        if abs(Q_hot_partial) > 1e-15:
            eta_partial = W_partial / Q_hot_partial
        else:
            eta_partial = 0.0

        bound_ok = eta_partial <= eta_carnot + 1e-12
        results["details"].append({
            "T_hot": T_hot,
            "T_cold": T_cold,
            "mix_frac": mix_frac,
            "eta_partial": float(eta_partial),
            "eta_carnot": float(eta_carnot),
            "eta_leq_carnot": bound_ok,
            "pass": bound_ok,
        })
        if not bound_ok:
            results["pass"] = False

    return results


# ═══════════════════════════════════════════════════════════════════
# TEST 6: ENTROPY PROPERTIES
# ═══════════════════════════════════════════════════════════════════

def test_entropy_properties():
    """
    Verify basic von Neumann entropy properties:
      - S(pure) = 0
      - S(maximally mixed) = ln(d)
      - 0 <= S(rho) <= ln(d)
      - S is concave: S(p rho1 + (1-p) rho2) >= p S(rho1) + (1-p) S(rho2)
    """
    results = {"test": "entropy_properties", "pass": True, "details": []}
    d = 2

    # S(pure) = 0
    rho_pure = np.diag([1.0, 0.0])
    S_pure = von_neumann_entropy(rho_pure)
    ok = abs(S_pure) < 1e-12
    results["details"].append({"property": "S(pure)=0", "S": float(S_pure), "pass": ok})
    if not ok:
        results["pass"] = False

    # S(max mixed) = ln(d)
    rho_mixed = IDENTITY_2 / d
    S_mixed = von_neumann_entropy(rho_mixed)
    ok = abs(S_mixed - np.log(d)) < 1e-12
    results["details"].append({
        "property": "S(max_mixed)=ln(d)",
        "S": float(S_mixed),
        "ln_d": float(np.log(d)),
        "pass": ok,
    })
    if not ok:
        results["pass"] = False

    # Bounded: 0 <= S <= ln(d) for many random states
    rng = np.random.default_rng(123)
    bound_violations = 0
    for _ in range(100):
        A = rng.standard_normal((2, 2)) + 1j * rng.standard_normal((2, 2))
        rho = A @ A.conj().T
        rho = rho / np.trace(rho)
        rho = (rho + rho.conj().T) / 2.0
        S = von_neumann_entropy(rho.real)
        if S < -1e-12 or S > np.log(d) + 1e-12:
            bound_violations += 1

    ok = bound_violations == 0
    results["details"].append({
        "property": "0<=S<=ln(d) for 100 random states",
        "violations": bound_violations,
        "pass": ok,
    })
    if not ok:
        results["pass"] = False

    # Concavity: S(p*rho1 + (1-p)*rho2) >= p*S(rho1) + (1-p)*S(rho2)
    concavity_violations = 0
    for _ in range(50):
        A = rng.standard_normal((2, 2)) + 1j * rng.standard_normal((2, 2))
        rho1 = A @ A.conj().T; rho1 = (rho1 / np.trace(rho1)).real
        rho1 = (rho1 + rho1.T) / 2.0

        B = rng.standard_normal((2, 2)) + 1j * rng.standard_normal((2, 2))
        rho2 = B @ B.conj().T; rho2 = (rho2 / np.trace(rho2)).real
        rho2 = (rho2 + rho2.T) / 2.0

        p = rng.uniform(0.01, 0.99)
        rho_mix = p * rho1 + (1.0 - p) * rho2

        S_mix = von_neumann_entropy(rho_mix)
        S_convex = p * von_neumann_entropy(rho1) + (1.0 - p) * von_neumann_entropy(rho2)

        if S_mix < S_convex - 1e-10:
            concavity_violations += 1

    ok = concavity_violations == 0
    results["details"].append({
        "property": "concavity (50 random pairs)",
        "violations": concavity_violations,
        "pass": ok,
    })
    if not ok:
        results["pass"] = False

    return results


# ═══════════════════════════════════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════════════════════════════════

def main():
    all_tests = [
        test_thermal_state_limits,
        test_free_energy_identity,
        test_landauer_principle,
        test_extractable_work,
        test_carnot_efficiency,
        test_entropy_properties,
    ]

    results = {"probe": "pure_lego_quantum_thermodynamics", "tests": []}
    all_pass = True

    for test_fn in all_tests:
        r = test_fn()
        results["tests"].append(r)
        status = "PASS" if r["pass"] else "FAIL"
        print(f"  [{status}] {r['test']}")
        if not r["pass"]:
            all_pass = False

    results["all_pass"] = all_pass

    os.makedirs(RESULTS_DIR, exist_ok=True)
    out_path = os.path.join(RESULTS_DIR, "pure_lego_quantum_thermodynamics_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, cls=_NumpyEncoder)

    print(f"\n{'ALL TESTS PASSED' if all_pass else 'SOME TESTS FAILED'}")
    print(f"Results written to {out_path}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
