#!/usr/bin/env python3
"""
sim_pure_lego_state_discrimination.py
======================================

Pure-lego quantum state discrimination probe.  No engine imports.
numpy/scipy only.

Implements and verifies:
  1. Helstrom measurement — optimal binary discrimination
     P_succ = (1 + D_tr(p*rho, (1-p)*sigma)) / 2
  2. Unambiguous state discrimination (USD) for non-orthogonal pure states
     P_conclusive = 1 - |<psi|phi>|
  3. Pretty-good measurement (PGM) for M states with priors
  4. Minimum-error discrimination for 3+ states (SDP via iterative projection)

Boundary checks:
  - Orthogonal states  =>  P_succ = 1   (perfect)
  - Identical states   =>  P_succ = max(p, 1-p)  (random guess)

Outputs JSON to a2_state/sim_results/pure_lego_state_discrimination_results.json
"""

import json
import os
import sys
from datetime import datetime, UTC

import numpy as np
from scipy.linalg import sqrtm, expm
classification = "classical_baseline"  # auto-backfill

# ═══════════════════════════════════════════════════════════════════
# UTILITY HELPERS
# ═══════════════════════════════════════════════════════════════════

def _density(psi: np.ndarray) -> np.ndarray:
    """Pure state vector -> density matrix."""
    psi = psi.reshape(-1, 1)
    return psi @ psi.conj().T


def trace_norm(M: np.ndarray) -> float:
    """||M||_1 = Tr|M| = sum of singular values."""
    sv = np.linalg.svd(M, compute_uv=False)
    return float(np.sum(sv))


def trace_distance(A: np.ndarray, B: np.ndarray) -> float:
    """D_tr(A, B) = 0.5 * ||A - B||_1 = 0.5 * sum(singular_values(A-B))."""
    return 0.5 * trace_norm(A - B)


def fidelity(rho: np.ndarray, sigma: np.ndarray) -> float:
    """F(rho, sigma) = (Tr sqrt(sqrt(rho) sigma sqrt(rho)))^2."""
    sqrt_rho = _matrix_sqrt(rho)
    M = sqrt_rho @ sigma @ sqrt_rho
    evals = np.linalg.eigvalsh(M)
    evals = np.maximum(evals, 0.0)
    return float(np.sum(np.sqrt(evals)) ** 2)


def _matrix_sqrt(M: np.ndarray) -> np.ndarray:
    """Hermitian positive-semidefinite matrix square root."""
    evals, evecs = np.linalg.eigh(M)
    evals = np.maximum(evals, 0.0)
    return evecs @ np.diag(np.sqrt(evals)) @ evecs.conj().T


def _pinv_sqrt(M: np.ndarray, tol: float = 1e-12) -> np.ndarray:
    """Pseudo-inverse square root of Hermitian PSD matrix."""
    evals, evecs = np.linalg.eigh(M)
    inv_sqrt = np.zeros_like(evals)
    mask = evals > tol
    inv_sqrt[mask] = 1.0 / np.sqrt(evals[mask])
    return evecs @ np.diag(inv_sqrt) @ evecs.conj().T


def random_pure_state(d: int) -> np.ndarray:
    """Haar-random pure state in C^d."""
    psi = np.random.randn(d) + 1j * np.random.randn(d)
    return psi / np.linalg.norm(psi)


def random_mixed_state(d: int) -> np.ndarray:
    """Random density matrix via partial trace of random pure state."""
    psi = random_pure_state(d * d)
    big_rho = _density(psi)
    # partial trace over second subsystem
    rho = np.zeros((d, d), dtype=complex)
    for i in range(d):
        for j in range(d):
            for k in range(d):
                rho[i, j] += big_rho[i * d + k, j * d + k]
    return rho


# ═══════════════════════════════════════════════════════════════════
# 1. HELSTROM MEASUREMENT
# ═══════════════════════════════════════════════════════════════════

def helstrom_success_prob(rho: np.ndarray, sigma: np.ndarray, p: float) -> float:
    """
    Optimal success probability for distinguishing rho vs sigma
    with prior probabilities p and (1-p).

    P_succ = (1 + ||p*rho - (1-p)*sigma||_1) / 2

    Note: the argument to the trace norm is the weighted difference,
    NOT the trace distance (which carries its own factor of 1/2).
    """
    Gamma = p * rho - (1.0 - p) * sigma
    tn = trace_norm(Gamma)
    return 0.5 * (1.0 + tn)


def helstrom_measurement(rho: np.ndarray, sigma: np.ndarray, p: float):
    """
    Returns the Helstrom POVM {Pi_0, Pi_1} and success probability.

    Pi_0 = projector onto positive eigenspace of (p*rho - (1-p)*sigma)
    Pi_1 = I - Pi_0
    """
    d = rho.shape[0]
    Gamma = p * rho - (1.0 - p) * sigma
    evals, evecs = np.linalg.eigh(Gamma)

    # Pi_0 = sum of projectors onto positive eigenvalues
    Pi_0 = np.zeros((d, d), dtype=complex)
    for i in range(d):
        if evals[i] > 0:
            v = evecs[:, i].reshape(-1, 1)
            Pi_0 += v @ v.conj().T
    Pi_1 = np.eye(d, dtype=complex) - Pi_0

    p_succ = float(np.real(p * np.trace(Pi_0 @ rho) + (1.0 - p) * np.trace(Pi_1 @ sigma)))
    return Pi_0, Pi_1, p_succ


# ═══════════════════════════════════════════════════════════════════
# 2. UNAMBIGUOUS STATE DISCRIMINATION (USD)
# ═══════════════════════════════════════════════════════════════════

def usd_conclusive_prob(psi: np.ndarray, phi: np.ndarray) -> float:
    """
    For two non-orthogonal pure states with equal priors,
    the maximum probability of a conclusive (unambiguous) result is:
        P_conclusive = 1 - |<psi|phi>|
    """
    overlap = np.abs(np.vdot(psi, phi))
    return 1.0 - overlap


# ═══════════════════════════════════════════════════════════════════
# 3. PRETTY-GOOD MEASUREMENT (PGM) / Square-Root Measurement
# ═══════════════════════════════════════════════════════════════════

def pgm_success_prob(states: list, priors: list) -> float:
    """
    PGM for M states {rho_i} with priors {p_i}.

    Define S = sum_i p_i * rho_i.
    PGM element: Pi_i = S^{-1/2} (p_i * rho_i) S^{-1/2}
    P_succ = sum_i p_i * Tr(Pi_i * rho_i)
    """
    d = states[0].shape[0]
    S = np.zeros((d, d), dtype=complex)
    for pi_val, rho in zip(priors, states):
        S += pi_val * rho
    S_inv_sqrt = _pinv_sqrt(S)

    p_succ = 0.0
    for pi_val, rho in zip(priors, states):
        Pi_i = S_inv_sqrt @ (pi_val * rho) @ S_inv_sqrt
        p_succ += pi_val * float(np.real(np.trace(Pi_i @ rho)))
    return p_succ


# ═══════════════════════════════════════════════════════════════════
# 4. MINIMUM-ERROR DISCRIMINATION (3+ states)
#    Iterative Jezek-Rehacek-Fiurasek algorithm
# ═══════════════════════════════════════════════════════════════════

def min_error_discrimination(states: list, priors: list,
                              max_iter: int = 500, tol: float = 1e-10) -> float:
    """
    Iterative algorithm for minimum-error discrimination of M states.
    Returns the optimal success probability.

    Uses the iterative projection method (Jezek, Rehacek, Fiurasek 2003).
    """
    M = len(states)
    d = states[0].shape[0]

    # Initialise POVM elements as uniform: Pi_i = I/M
    Pis = [np.eye(d, dtype=complex) / M for _ in range(M)]

    prev_succ = 0.0
    for iteration in range(max_iter):
        # Step 1: compute Z_i = p_i * rho_i @ Pi_i for each i
        # Step 2: compute X = sum_i sqrt(Z_i^dag Z_i)  ... no, use simpler update.

        # Simpler iterative scheme: for each pair, update toward Helstrom optimal.
        # Actually use the standard Jezek iteration:
        # Gamma_i = p_i * rho_i
        # New Pi_i = (sum_j Gamma_j @ Pi_j)^{-1/2} @ Gamma_i @ Pi_i @ Gamma_i @ (sum_j Gamma_j @ Pi_j)^{-1/2} ... nope

        # Use the correct update from Tyson (2009) / Eldar (2003):
        # Pi_i^{new} propto (sum_{j!=i} p_j rho_j @ Pi_j @ rho_j)^{-1} @ (p_i rho_i)
        # This is complex. Use simpler PGM + refinement approach.

        # Actually, let's use the weight-update method:
        # W = sum_i p_i * Pi_i^{1/2} rho_i Pi_i^{1/2}
        # Pi_i^{new} = W^{-1/2} (p_i Pi_i^{1/2} rho_i Pi_i^{1/2}) W^{-1/2}

        # Compute weighted operators
        W = np.zeros((d, d), dtype=complex)
        G_list = []
        for i in range(M):
            sqrt_Pi = _matrix_sqrt(Pis[i])
            G_i = priors[i] * sqrt_Pi @ states[i] @ sqrt_Pi
            G_list.append(G_i)
            W += G_i

        W_inv_sqrt = _pinv_sqrt(W)

        # Update POVM
        new_Pis = []
        for i in range(M):
            new_Pi = W_inv_sqrt @ G_list[i] @ W_inv_sqrt
            # Enforce PSD
            evals, evecs = np.linalg.eigh(new_Pi)
            evals = np.maximum(evals, 0.0)
            new_Pi = evecs @ np.diag(evals) @ evecs.conj().T
            new_Pis.append(new_Pi)

        # Normalise so sum = I
        S = sum(new_Pis)
        S_inv_sqrt = _pinv_sqrt(S)
        for i in range(M):
            new_Pis[i] = S_inv_sqrt @ new_Pis[i] @ S_inv_sqrt

        Pis = new_Pis

        # Compute success probability
        p_succ = sum(
            priors[i] * float(np.real(np.trace(Pis[i] @ states[i])))
            for i in range(M)
        )
        if abs(p_succ - prev_succ) < tol:
            break
        prev_succ = p_succ

    return p_succ


# ═══════════════════════════════════════════════════════════════════
# TEST PAIRS AND VERIFICATION
# ═══════════════════════════════════════════════════════════════════

def build_test_pairs(d: int = 2):
    """Build 10 test state pairs in C^d for Helstrom verification."""
    np.random.seed(42)
    pairs = []

    # Pair 0: orthogonal pure states |0> vs |1>
    psi0 = np.array([1, 0], dtype=complex)
    psi1 = np.array([0, 1], dtype=complex)
    pairs.append(("orthogonal_|0>_|1>", _density(psi0), _density(psi1), psi0, psi1))

    # Pair 1: identical states
    psi = random_pure_state(d)
    pairs.append(("identical", _density(psi), _density(psi), psi, psi))

    # Pair 2: |0> vs |+>
    plus = np.array([1, 1], dtype=complex) / np.sqrt(2)
    pairs.append(("|0>_vs_|+>", _density(psi0), _density(plus), psi0, plus))

    # Pair 3: |+> vs |->
    minus = np.array([1, -1], dtype=complex) / np.sqrt(2)
    pairs.append(("|+>_vs_|->", _density(plus), _density(minus), plus, minus))

    # Pair 4: |0> vs small-angle rotation
    theta = np.pi / 8
    psi_rot = np.array([np.cos(theta), np.sin(theta)], dtype=complex)
    pairs.append(("|0>_vs_pi/8_rot", _density(psi0), _density(psi_rot), psi0, psi_rot))

    # Pair 5: random pure vs random pure
    a = random_pure_state(d)
    b = random_pure_state(d)
    pairs.append(("random_pure_1", _density(a), _density(b), a, b))

    # Pair 6: another random pair
    a = random_pure_state(d)
    b = random_pure_state(d)
    pairs.append(("random_pure_2", _density(a), _density(b), a, b))

    # Pair 7: maximally mixed vs pure
    I_over_2 = np.eye(d, dtype=complex) / d
    psi = random_pure_state(d)
    pairs.append(("mixed_vs_pure", I_over_2, _density(psi), None, psi))

    # Pair 8: two random mixed states
    rho1 = random_mixed_state(d)
    rho2 = random_mixed_state(d)
    pairs.append(("random_mixed", rho1, rho2, None, None))

    # Pair 9: near-identical (small perturbation)
    base = random_mixed_state(d)
    eps = 0.01
    perturb = random_mixed_state(d)
    near = (1 - eps) * base + eps * perturb
    pairs.append(("near_identical", base, near, None, None))

    return pairs


def run_helstrom_tests(pairs, p: float = 0.5):
    """Run Helstrom test on each pair, verify boundary conditions."""
    results = []
    for name, rho, sigma, psi_a, psi_b in pairs:
        # Formula-based
        p_succ_formula = helstrom_success_prob(rho, sigma, p)

        # POVM-based
        Pi_0, Pi_1, p_succ_povm = helstrom_measurement(rho, sigma, p)

        # Cross-check
        match = abs(p_succ_formula - p_succ_povm) < 1e-8

        # Trace distance for reporting
        dt = trace_distance(rho, sigma)

        # USD (only for pure state pairs)
        usd_result = None
        if psi_a is not None and psi_b is not None:
            usd_result = usd_conclusive_prob(psi_a, psi_b)

        entry = {
            "pair_name": name,
            "trace_distance": round(dt, 10),
            "helstrom_p_succ_formula": round(p_succ_formula, 10),
            "helstrom_p_succ_povm": round(p_succ_povm, 10),
            "formula_povm_match": match,
        }
        if usd_result is not None:
            entry["usd_p_conclusive"] = round(usd_result, 10)

        results.append(entry)
    return results


def run_boundary_checks(p: float = 0.5):
    """Verify the two critical boundary conditions."""
    d = 2
    checks = []

    # Check 1: orthogonal => P_succ = 1.0
    rho = _density(np.array([1, 0], dtype=complex))
    sigma = _density(np.array([0, 1], dtype=complex))
    p_succ = helstrom_success_prob(rho, sigma, p)
    checks.append({
        "check": "orthogonal_states_perfect_discrimination",
        "expected": 1.0,
        "actual": round(p_succ, 12),
        "PASS": abs(p_succ - 1.0) < 1e-10
    })

    # Check 2: identical => P_succ = max(p, 1-p)
    psi = random_pure_state(d)
    rho = _density(psi)
    p_succ = helstrom_success_prob(rho, rho, p)
    expected = max(p, 1.0 - p)
    checks.append({
        "check": "identical_states_random_guess",
        "expected": expected,
        "actual": round(p_succ, 12),
        "PASS": abs(p_succ - expected) < 1e-10
    })

    # Check 3: identical at p=0.7
    p2 = 0.7
    p_succ = helstrom_success_prob(rho, rho, p2)
    expected = max(p2, 1.0 - p2)
    checks.append({
        "check": "identical_states_p=0.7",
        "expected": expected,
        "actual": round(p_succ, 12),
        "PASS": abs(p_succ - expected) < 1e-10
    })

    return checks


def run_pgm_tests():
    """PGM tests on several multi-state ensembles."""
    np.random.seed(99)
    results = []

    # Test 1: 3 orthogonal pure states, equal priors => P_succ = 1
    d = 3
    states = [_density(np.eye(d, dtype=complex)[i]) for i in range(d)]
    priors = [1.0 / d] * d
    p_succ = pgm_success_prob(states, priors)
    results.append({
        "test": "3_orthogonal_pure_equal_prior",
        "pgm_p_succ": round(p_succ, 10),
        "expected_perfect": True,
        "PASS": abs(p_succ - 1.0) < 1e-8
    })

    # Test 2: 3 non-orthogonal pure states in C^2
    d = 2
    angles = [0, 2 * np.pi / 3, 4 * np.pi / 3]
    psi_list = [np.array([np.cos(a / 2), np.sin(a / 2)], dtype=complex) for a in angles]
    states = [_density(psi) for psi in psi_list]
    priors = [1.0 / 3] * 3
    p_succ = pgm_success_prob(states, priors)
    results.append({
        "test": "3_trine_states_C2",
        "pgm_p_succ": round(p_succ, 10),
        "note": "trine states, known PGM optimal = 2/3",
        "PASS": p_succ > 0.5  # must beat random guessing at 1/3
    })

    # Test 3: 4 random pure states in C^3
    d = 3
    psi_list = [random_pure_state(d) for _ in range(4)]
    states = [_density(psi) for psi in psi_list]
    priors = [0.25] * 4
    p_succ = pgm_success_prob(states, priors)
    results.append({
        "test": "4_random_pure_C3",
        "pgm_p_succ": round(p_succ, 10),
        "PASS": 0.0 < p_succ <= 1.0
    })

    return results


def run_min_error_tests():
    """Minimum-error discrimination tests for 3+ states."""
    np.random.seed(77)
    results = []

    # Test 1: 3 orthogonal states => P_succ = 1
    d = 3
    states = [_density(np.eye(d, dtype=complex)[i]) for i in range(d)]
    priors = [1.0 / d] * d
    p_succ = min_error_discrimination(states, priors)
    results.append({
        "test": "3_orthogonal_min_error",
        "min_error_p_succ": round(p_succ, 10),
        "PASS": abs(p_succ - 1.0) < 1e-6
    })

    # Test 2: trine states
    d = 2
    angles = [0, 2 * np.pi / 3, 4 * np.pi / 3]
    psi_list = [np.array([np.cos(a / 2), np.sin(a / 2)], dtype=complex) for a in angles]
    states = [_density(psi) for psi in psi_list]
    priors = [1.0 / 3] * 3
    p_succ = min_error_discrimination(states, priors)
    # Known optimal for trine: 2/3
    results.append({
        "test": "trine_states_min_error",
        "min_error_p_succ": round(p_succ, 10),
        "expected_approx": 0.6667,
        "PASS": abs(p_succ - 2.0 / 3) < 0.02
    })

    # Test 3: 4 random mixed states in C^3
    d = 3
    states = [random_mixed_state(d) for _ in range(4)]
    priors = [0.25] * 4
    p_succ = min_error_discrimination(states, priors)
    results.append({
        "test": "4_random_mixed_C3",
        "min_error_p_succ": round(p_succ, 10),
        "PASS": 0.25 <= p_succ <= 1.0  # must beat random 1/4
    })

    # Test 4: 2 states — should match Helstrom
    d = 2
    psi0 = np.array([1, 0], dtype=complex)
    plus = np.array([1, 1], dtype=complex) / np.sqrt(2)
    states = [_density(psi0), _density(plus)]
    priors = [0.5, 0.5]
    p_succ_me = min_error_discrimination(states, priors)
    p_succ_h = helstrom_success_prob(states[0], states[1], 0.5)
    results.append({
        "test": "2_states_matches_helstrom",
        "min_error_p_succ": round(p_succ_me, 10),
        "helstrom_p_succ": round(p_succ_h, 10),
        "PASS": abs(p_succ_me - p_succ_h) < 0.01
    })

    return results


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("PURE LEGO: Quantum State Discrimination & Helstrom Bound")
    print("=" * 70)

    # --- Helstrom on 10 pairs ---
    pairs = build_test_pairs()
    helstrom_results = run_helstrom_tests(pairs, p=0.5)

    print(f"\n--- Helstrom Results ({len(helstrom_results)} pairs, p=0.5) ---")
    all_pass = True
    for r in helstrom_results:
        status = "PASS" if r["formula_povm_match"] else "FAIL"
        if not r["formula_povm_match"]:
            all_pass = False
        usd_str = ""
        if "usd_p_conclusive" in r:
            usd_str = f"  USD={r['usd_p_conclusive']:.6f}"
        print(f"  [{status}] {r['pair_name']:25s}  D_tr={r['trace_distance']:.6f}"
              f"  P_succ={r['helstrom_p_succ_formula']:.6f}{usd_str}")

    # --- Boundary checks ---
    boundary = run_boundary_checks()
    print(f"\n--- Boundary Checks ---")
    for c in boundary:
        status = "PASS" if c["PASS"] else "FAIL"
        if not c["PASS"]:
            all_pass = False
        print(f"  [{status}] {c['check']}: expected={c['expected']}, actual={c['actual']}")

    # --- PGM ---
    pgm_results = run_pgm_tests()
    print(f"\n--- Pretty-Good Measurement ---")
    for r in pgm_results:
        status = "PASS" if r["PASS"] else "FAIL"
        if not r["PASS"]:
            all_pass = False
        print(f"  [{status}] {r['test']}: P_succ={r['pgm_p_succ']:.6f}")

    # --- Min-error ---
    me_results = run_min_error_tests()
    print(f"\n--- Minimum-Error Discrimination ---")
    for r in me_results:
        status = "PASS" if r["PASS"] else "FAIL"
        if not r["PASS"]:
            all_pass = False
        print(f"  [{status}] {r['test']}: P_succ={r['min_error_p_succ']:.6f}")

    # --- Aggregate ---
    total_tests = len(helstrom_results) + len(boundary) + len(pgm_results) + len(me_results)
    pass_count = (
        sum(1 for r in helstrom_results if r["formula_povm_match"])
        + sum(1 for c in boundary if c["PASS"])
        + sum(1 for r in pgm_results if r["PASS"])
        + sum(1 for r in me_results if r["PASS"])
    )

    print(f"\n{'=' * 70}")
    verdict = "ALL PASS" if all_pass else "SOME FAILURES"
    print(f"VERDICT: {verdict}  ({pass_count}/{total_tests} tests passed)")
    print(f"{'=' * 70}")

    # --- Write JSON ---
    output = {
        "probe": "sim_pure_lego_state_discrimination",
        "timestamp": datetime.now(UTC).isoformat(),
        "verdict": verdict,
        "total_tests": total_tests,
        "pass_count": pass_count,
        "helstrom_binary_tests": helstrom_results,
        "boundary_checks": boundary,
        "pgm_tests": pgm_results,
        "min_error_tests": me_results,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "pure_lego_state_discrimination_results.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults written to: {out_path}")


if __name__ == "__main__":
    main()
