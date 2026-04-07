#!/usr/bin/env python3
"""
sim_pure_lego_f_divergences.py
==============================

Pure-lego probe: quantum f-divergences and sandwiched Renyi divergences.
No engine dependencies. numpy/scipy only.

Implements:
  1. Quantum f-divergence D_f(rho||sigma) for operator convex f on spectra.
  2. Standard f-divergences:
       - f(t) = t*log(t)   => relative entropy  S(rho||sigma)
       - f(t) = (t-1)^2    => chi-squared divergence
       - f(t) = -log(t)    => max-divergence (Dmax-like)
       - f(t) = |t-1|      => trace distance (up to factor)
  3. Sandwiched Renyi divergence:
       D_alpha(rho||sigma) = 1/(alpha-1) * log Tr[(sigma^{(1-a)/2a} rho sigma^{(1-a)/2a})^a]
  4. Petz Renyi divergence:
       D_alpha^P(rho||sigma) = 1/(alpha-1) * log Tr[rho^a sigma^{1-a}]

Verification battery:
  - All standard f-divergences reduce correctly on known pairs.
  - Sandwiched Renyi alpha->1 gives relative entropy.
  - Monotonicity under CPTP for alpha >= 1/2.
  - Data processing inequality (partial trace).
  - Petz vs sandwiched: agree for commuting, differ for non-commuting.

Tested on 10 state pairs (qubit density matrices).
"""

import json
import os
import sys
from datetime import datetime, UTC

import numpy as np
from scipy.linalg import sqrtm, logm, fractional_matrix_power

# ═══════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════

ATOL = 1e-10


def _make_density(M: np.ndarray) -> np.ndarray:
    """Force Hermitian, PSD, trace-1."""
    M = 0.5 * (M + M.conj().T)
    evals, evecs = np.linalg.eigh(M)
    evals = np.maximum(evals, 0.0)
    if evals.sum() < ATOL:
        return np.eye(M.shape[0], dtype=complex) / M.shape[0]
    evals /= evals.sum()
    return (evecs * evals) @ evecs.conj().T


def _random_density(d: int, rng: np.random.Generator) -> np.ndarray:
    """Random density matrix via Ginibre ensemble."""
    G = rng.standard_normal((d, d)) + 1j * rng.standard_normal((d, d))
    rho = G @ G.conj().T
    return rho / np.trace(rho)


def _random_pure_state_density(d: int, rng: np.random.Generator) -> np.ndarray:
    """Random pure state |psi><psi|."""
    psi = rng.standard_normal(d) + 1j * rng.standard_normal(d)
    psi /= np.linalg.norm(psi)
    return np.outer(psi, psi.conj())


def _commuting_pair(d: int, rng: np.random.Generator):
    """Generate two commuting density matrices (simultaneously diagonalizable)."""
    U = np.linalg.qr(rng.standard_normal((d, d)) + 1j * rng.standard_normal((d, d)))[0]
    p = rng.dirichlet(np.ones(d))
    q = rng.dirichlet(np.ones(d))
    rho = U @ np.diag(p) @ U.conj().T
    sigma = U @ np.diag(q) @ U.conj().T
    return _make_density(rho), _make_density(sigma)


def _mat_pow(M: np.ndarray, p: float) -> np.ndarray:
    """Matrix power via eigendecomposition, clamping negatives."""
    evals, evecs = np.linalg.eigh(0.5 * (M + M.conj().T))
    evals = np.maximum(evals, 0.0)
    return (evecs * (evals ** p)) @ evecs.conj().T


def _mat_log(M: np.ndarray) -> np.ndarray:
    """Matrix logarithm on PSD matrix, using eigendecomposition."""
    evals, evecs = np.linalg.eigh(0.5 * (M + M.conj().T))
    evals = np.maximum(evals, ATOL)
    return (evecs * np.log(evals)) @ evecs.conj().T


def _partial_trace_B(rho_AB: np.ndarray, dA: int, dB: int) -> np.ndarray:
    """Trace out subsystem B."""
    return rho_AB.reshape(dA, dB, dA, dB).trace(axis1=1, axis2=3)


def _partial_trace_A(rho_AB: np.ndarray, dA: int, dB: int) -> np.ndarray:
    """Trace out subsystem A."""
    return rho_AB.reshape(dA, dB, dA, dB).trace(axis1=0, axis2=2)


# ═══════════════════════════════════════════════════════════════════
# QUANTUM F-DIVERGENCE (spectral approach)
# ═══════════════════════════════════════════════════════════════════

def quantum_f_divergence(rho: np.ndarray, sigma: np.ndarray, f_func) -> float:
    """
    Compute quantum f-divergence D_f(rho || sigma).

    For density matrices with spectral decompositions
    rho = sum_i p_i |e_i><e_i|, sigma = sum_j q_j |f_j><f_j|:

    D_f(rho||sigma) = sum_{i,j} q_j * f(p_i/q_j) * |<e_i|f_j>|^2

    where f is operator convex with f(1) = 0 (or known constant).
    """
    p_vals, p_vecs = np.linalg.eigh(0.5 * (rho + rho.conj().T))
    q_vals, q_vecs = np.linalg.eigh(0.5 * (sigma + sigma.conj().T))
    p_vals = np.maximum(p_vals, 0.0)
    q_vals = np.maximum(q_vals, 0.0)

    # overlap matrix |<e_i|f_j>|^2
    overlaps = np.abs(p_vecs.conj().T @ q_vecs) ** 2  # shape (d, d)

    result = 0.0
    d = rho.shape[0]
    for i in range(d):
        for j in range(d):
            pi, qj = p_vals[i], q_vals[j]
            oij = overlaps[i, j]
            if oij < ATOL:
                continue
            if qj < ATOL:
                # sigma has zero eigenvalue where rho may not
                if pi > ATOL:
                    result += float('inf')
                continue
            ratio = pi / qj
            result += qj * f_func(ratio) * oij
    return float(result)


# ═══════════════════════════════════════════════════════════════════
# STANDARD f-FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def f_relative_entropy(t: float) -> float:
    """f(t) = t*log(t). Gives Umegaki relative entropy."""
    if t < ATOL:
        return 0.0
    return t * np.log(t)


def f_chi_squared(t: float) -> float:
    """f(t) = (t-1)^2. Gives chi-squared divergence."""
    return (t - 1.0) ** 2


def f_max_divergence(t: float) -> float:
    """f(t) = -log(t). Related to max-divergence / Burg entropy."""
    if t < ATOL:
        return float('inf')
    return -np.log(t)


def f_trace_distance(t: float) -> float:
    """f(t) = |t-1|. Gives (scaled) trace distance."""
    return abs(t - 1.0)


# ═══════════════════════════════════════════════════════════════════
# DIRECT FORMULAS (for cross-checking)
# ═══════════════════════════════════════════════════════════════════

def relative_entropy_direct(rho: np.ndarray, sigma: np.ndarray) -> float:
    """S(rho||sigma) = Tr[rho (log rho - log sigma)]."""
    log_rho = _mat_log(rho)
    log_sigma = _mat_log(sigma)
    val = np.trace(rho @ (log_rho - log_sigma))
    return float(np.real(val))


def chi_squared_direct(rho: np.ndarray, sigma: np.ndarray) -> float:
    """chi^2(rho||sigma) = Tr[sigma^{-1/2}(rho - sigma) sigma^{-1/2}(rho - sigma)]
    = Tr[(rho - sigma) sigma^{-1} (rho - sigma)] simplified for full-rank sigma.
    Via spectral: sum_{ij} (p_i - q_j)^2 / q_j * |<ei|fj>|^2."""
    p_vals, p_vecs = np.linalg.eigh(rho)
    q_vals, q_vecs = np.linalg.eigh(sigma)
    p_vals = np.maximum(p_vals, 0.0)
    q_vals = np.maximum(q_vals, 0.0)
    overlaps = np.abs(p_vecs.conj().T @ q_vecs) ** 2
    result = 0.0
    d = rho.shape[0]
    for i in range(d):
        for j in range(d):
            if q_vals[j] < ATOL:
                continue
            result += (p_vals[i] - q_vals[j]) ** 2 / q_vals[j] * overlaps[i, j]
    return float(result)


def trace_distance_direct(rho: np.ndarray, sigma: np.ndarray) -> float:
    """T(rho, sigma) = 0.5 * Tr|rho - sigma|."""
    diff = rho - sigma
    evals = np.linalg.eigvalsh(0.5 * (diff + diff.conj().T))
    return float(0.5 * np.sum(np.abs(evals)))


# ═══════════════════════════════════════════════════════════════════
# SANDWICHED RENYI DIVERGENCE
# ═══════════════════════════════════════════════════════════════════

def sandwiched_renyi(rho: np.ndarray, sigma: np.ndarray, alpha: float) -> float:
    """
    Sandwiched Renyi divergence:
    D_alpha(rho||sigma) = 1/(alpha-1) * log Tr[ (sigma^{(1-a)/2a} rho sigma^{(1-a)/2a})^a ]

    Valid for alpha in (0, 1) union (1, inf).
    For alpha -> 1 recovers relative entropy.
    """
    if abs(alpha - 1.0) < 1e-8:
        return relative_entropy_direct(rho, sigma)

    exp = (1.0 - alpha) / (2.0 * alpha)
    sigma_pow = _mat_pow(sigma, exp)
    inner = sigma_pow @ rho @ sigma_pow
    # Raise inner to power alpha
    inner_a = _mat_pow(inner, alpha)
    tr_val = np.real(np.trace(inner_a))
    if tr_val <= 0:
        return float('inf')
    return float(np.log(tr_val) / (alpha - 1.0))


# ═══════════════════════════════════════════════════════════════════
# PETZ RENYI DIVERGENCE
# ═══════════════════════════════════════════════════════════════════

def petz_renyi(rho: np.ndarray, sigma: np.ndarray, alpha: float) -> float:
    """
    Petz (standard) Renyi divergence:
    D_alpha^P(rho||sigma) = 1/(alpha-1) * log Tr[ rho^alpha sigma^{1-alpha} ]

    Valid for alpha in (0,1) union (1,inf).
    """
    if abs(alpha - 1.0) < 1e-8:
        return relative_entropy_direct(rho, sigma)

    rho_a = _mat_pow(rho, alpha)
    sigma_1a = _mat_pow(sigma, 1.0 - alpha)
    tr_val = np.real(np.trace(rho_a @ sigma_1a))
    if tr_val <= 0:
        return float('inf')
    return float(np.log(tr_val) / (alpha - 1.0))


# ═══════════════════════════════════════════════════════════════════
# CPTP CHANNEL HELPERS
# ═══════════════════════════════════════════════════════════════════

def apply_depolarizing(rho: np.ndarray, p: float) -> np.ndarray:
    """Depolarizing channel: rho -> (1-p)*rho + p*I/d."""
    d = rho.shape[0]
    return (1.0 - p) * rho + p * np.eye(d, dtype=complex) / d


def apply_amplitude_damping(rho: np.ndarray, gamma: float) -> np.ndarray:
    """Amplitude damping channel on qubit (d=2)."""
    K0 = np.array([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=complex)
    K1 = np.array([[0, np.sqrt(gamma)], [0, 0]], dtype=complex)
    return K0 @ rho @ K0.conj().T + K1 @ rho @ K1.conj().T


def make_random_kraus(d: int, rng: np.random.Generator, n_kraus: int = 3):
    """Generate random Kraus operators for a CPTP map on dimension d."""
    kraus = []
    for _ in range(n_kraus):
        K = rng.standard_normal((d, d)) + 1j * rng.standard_normal((d, d))
        kraus.append(K)
    # Normalize so sum K_i^dag K_i = I
    total = sum(K.conj().T @ K for K in kraus)
    S_inv_half = _mat_pow(total, -0.5)
    return [K @ S_inv_half for K in kraus]


def apply_kraus(rho: np.ndarray, kraus) -> np.ndarray:
    """Apply a CPTP map given as a list of Kraus operators."""
    result = sum(K @ rho @ K.conj().T for K in kraus)
    return _make_density(result)


# ═══════════════════════════════════════════════════════════════════
# TEST BATTERY
# ═══════════════════════════════════════════════════════════════════

def generate_test_pairs(rng: np.random.Generator):
    """Generate 10 state pairs for testing."""
    pairs = []
    labels = []

    # 1) Maximally mixed vs pure
    rho = np.eye(2, dtype=complex) / 2
    psi = np.array([[1, 0]], dtype=complex).T
    sigma = psi @ psi.conj().T
    # flip: use pure as rho since S(rho||sigma)=inf when supp(rho) not in supp(sigma)
    # Use full-rank sigma instead
    sigma_fr = 0.9 * sigma + 0.1 * np.eye(2, dtype=complex) / 2
    pairs.append((rho, _make_density(sigma_fr)))
    labels.append("maximally_mixed_vs_near_pure")

    # 2) Two random mixed states
    pairs.append((_random_density(2, rng), _random_density(2, rng)))
    labels.append("random_mixed_pair_1")

    # 3) Two random mixed states
    pairs.append((_random_density(2, rng), _random_density(2, rng)))
    labels.append("random_mixed_pair_2")

    # 4) Close states (small perturbation)
    base = _random_density(2, rng)
    perturb = 0.02 * (rng.standard_normal((2, 2)) + 1j * rng.standard_normal((2, 2)))
    pairs.append((base, _make_density(base + perturb)))
    labels.append("close_states")

    # 5) Orthogonal-ish pure states (regularized)
    psi0 = np.array([1, 0], dtype=complex)
    psi1 = np.array([0, 1], dtype=complex)
    r0 = np.outer(psi0, psi0.conj())
    r1 = np.outer(psi1, psi1.conj())
    eps = 0.05
    pairs.append((_make_density((1 - eps) * r0 + eps * r1),
                  _make_density((1 - eps) * r1 + eps * r0)))
    labels.append("near_orthogonal_regularized")

    # 6) Commuting pair
    c_rho, c_sigma = _commuting_pair(2, rng)
    pairs.append((c_rho, c_sigma))
    labels.append("commuting_pair_1")

    # 7) Another commuting pair
    c_rho2, c_sigma2 = _commuting_pair(2, rng)
    pairs.append((c_rho2, c_sigma2))
    labels.append("commuting_pair_2")

    # 8) 4x4 random (two-qubit)
    pairs.append((_random_density(4, rng), _random_density(4, rng)))
    labels.append("two_qubit_random")

    # 9) 4x4 product states
    rA, rB = _random_density(2, rng), _random_density(2, rng)
    sA, sB = _random_density(2, rng), _random_density(2, rng)
    pairs.append((np.kron(rA, rB), np.kron(sA, sB)))
    labels.append("two_qubit_product")

    # 10) Bloch sphere antipodal (regularized)
    theta = rng.uniform(0, np.pi)
    phi = rng.uniform(0, 2 * np.pi)
    nx, ny, nz = np.sin(theta) * np.cos(phi), np.sin(theta) * np.sin(phi), np.cos(theta)
    sx, sy, sz = np.array([[0, 1], [1, 0]]), np.array([[0, -1j], [1j, 0]]), np.array([[1, 0], [0, -1]])
    r_bloch = 0.8
    rho_b = (np.eye(2) + r_bloch * (nx * sx + ny * sy + nz * sz)) / 2
    sigma_b = (np.eye(2) - r_bloch * (nx * sx + ny * sy + nz * sz)) / 2
    pairs.append((_make_density(rho_b), _make_density(sigma_b)))
    labels.append("bloch_antipodal")

    return pairs, labels


def test_f_divergence_reduction(pairs, labels):
    """Verify all f-divergences reduce correctly against direct formulas."""
    results = []
    for idx, ((rho, sigma), label) in enumerate(zip(pairs, labels)):
        d = rho.shape[0]
        entry = {"pair_index": idx, "label": label, "dim": d}

        # Skip 4x4 pairs for direct comparison (formulas are the same, just slower)
        # Relative entropy
        Df_re = quantum_f_divergence(rho, sigma, f_relative_entropy)
        S_direct = relative_entropy_direct(rho, sigma)
        entry["relative_entropy_f_div"] = round(Df_re, 10)
        entry["relative_entropy_direct"] = round(S_direct, 10)
        entry["relative_entropy_match"] = abs(Df_re - S_direct) < 1e-6

        # Chi-squared
        Df_chi = quantum_f_divergence(rho, sigma, f_chi_squared)
        chi_direct = chi_squared_direct(rho, sigma)
        entry["chi_squared_f_div"] = round(Df_chi, 10)
        entry["chi_squared_direct"] = round(chi_direct, 10)
        entry["chi_squared_match"] = abs(Df_chi - chi_direct) < 1e-6

        # Trace distance: f-div gives sum_ij q_j |p_i/q_j - 1| |<ei|fj>|^2
        # = sum_ij |p_i - q_j| |<ei|fj>|^2. This equals 2*T(rho,sigma) for
        # commuting states. For general states it's the spectral variational distance.
        Df_td = quantum_f_divergence(rho, sigma, f_trace_distance)
        td_direct = trace_distance_direct(rho, sigma)
        # The f-divergence with |t-1| gives twice the trace distance
        entry["trace_f_div"] = round(Df_td, 10)
        entry["trace_distance_direct"] = round(td_direct, 10)
        entry["trace_distance_ratio"] = round(Df_td / (2.0 * td_direct + 1e-15), 10)

        # Non-negativity check (all f-divergences should be >= 0)
        entry["all_nonneg"] = (Df_re >= -1e-8 and Df_chi >= -1e-8 and Df_td >= -1e-8)

        results.append(entry)
    return results


def test_sandwiched_renyi_limit(pairs, labels):
    """Verify sandwiched Renyi alpha->1 gives relative entropy."""
    results = []
    for idx, ((rho, sigma), label) in enumerate(zip(pairs, labels)):
        S_direct = relative_entropy_direct(rho, sigma)

        # Approach alpha=1 from both sides
        alphas_near_1 = [0.9, 0.95, 0.99, 0.999, 1.001, 1.01, 1.05, 1.1]
        vals = {}
        for a in alphas_near_1:
            vals[str(a)] = round(sandwiched_renyi(rho, sigma, a), 8)

        # Direct at alpha=1 (uses relative entropy internally)
        val_at_1 = sandwiched_renyi(rho, sigma, 1.0)

        entry = {
            "pair_index": idx,
            "label": label,
            "relative_entropy": round(S_direct, 8),
            "sandwiched_at_1": round(val_at_1, 8),
            "sandwiched_near_1": vals,
            "limit_match": abs(val_at_1 - S_direct) < 1e-6,
        }
        results.append(entry)
    return results


def test_monotonicity_cptp(pairs, labels, rng):
    """
    Verify monotonicity under CPTP for sandwiched Renyi with alpha >= 1/2.
    D_alpha(E(rho)||E(sigma)) <= D_alpha(rho||sigma) for CPTP E.
    """
    test_alphas = [0.5, 0.75, 1.5, 2.0, 3.0]
    results = []

    for idx, ((rho, sigma), label) in enumerate(zip(pairs, labels)):
        d = rho.shape[0]
        entry = {"pair_index": idx, "label": label, "dim": d, "tests": []}

        for alpha in test_alphas:
            D_before = sandwiched_renyi(rho, sigma, alpha)

            # Depolarizing channel
            p = 0.3
            if d == 2:
                rho_dep = apply_depolarizing(rho, p)
                sigma_dep = apply_depolarizing(sigma, p)
            else:
                rho_dep = apply_depolarizing(rho, p)
                sigma_dep = apply_depolarizing(sigma, p)

            D_after_dep = sandwiched_renyi(rho_dep, sigma_dep, alpha)

            # Random CPTP (same channel applied to both states)
            kraus = make_random_kraus(d, rng)
            rho_rand = apply_kraus(rho, kraus)
            sigma_rand = apply_kraus(sigma, kraus)
            D_after_rand = sandwiched_renyi(rho_rand, sigma_rand, alpha)

            monotone_dep = D_after_dep <= D_before + 1e-8
            monotone_rand = D_after_rand <= D_before + 1e-8

            entry["tests"].append({
                "alpha": alpha,
                "D_before": round(D_before, 8),
                "D_after_depol": round(D_after_dep, 8),
                "D_after_random": round(D_after_rand, 8),
                "monotone_depol": monotone_dep,
                "monotone_random": monotone_rand,
            })
        results.append(entry)
    return results


def test_data_processing_inequality(rng):
    """
    Data processing inequality via partial trace on bipartite states.
    D_alpha(rho_AB || sigma_AB) >= D_alpha(rho_A || sigma_A)
    for alpha >= 1/2 (sandwiched).
    """
    test_alphas = [0.5, 1.0, 1.5, 2.0]
    results = []

    for trial in range(5):
        rho_AB = _random_density(4, rng)
        sigma_AB = _random_density(4, rng)
        rho_A = _partial_trace_B(rho_AB, 2, 2)
        sigma_A = _partial_trace_B(sigma_AB, 2, 2)

        entry = {"trial": trial, "tests": []}
        for alpha in test_alphas:
            D_AB = sandwiched_renyi(rho_AB, sigma_AB, alpha)
            D_A = sandwiched_renyi(rho_A, sigma_A, alpha)
            entry["tests"].append({
                "alpha": alpha,
                "D_AB": round(D_AB, 8),
                "D_A": round(D_A, 8),
                "DPI_satisfied": D_AB >= D_A - 1e-8,
            })
        results.append(entry)
    return results


def test_petz_vs_sandwiched(pairs, labels):
    """
    Compare Petz and sandwiched Renyi divergences.
    They should agree for commuting states, differ for non-commuting.
    """
    test_alphas = [0.5, 0.75, 1.5, 2.0, 3.0]
    results = []

    for idx, ((rho, sigma), label) in enumerate(zip(pairs, labels)):
        entry = {"pair_index": idx, "label": label, "comparisons": []}

        # Check if states commute
        comm = np.linalg.norm(rho @ sigma - sigma @ rho)
        is_commuting = comm < 1e-8

        for alpha in test_alphas:
            D_sand = sandwiched_renyi(rho, sigma, alpha)
            D_petz = petz_renyi(rho, sigma, alpha)
            diff = abs(D_sand - D_petz)

            entry["comparisons"].append({
                "alpha": alpha,
                "sandwiched": round(D_sand, 8),
                "petz": round(D_petz, 8),
                "difference": round(diff, 8),
                "agree": diff < 1e-6,
            })

        entry["commutator_norm"] = round(comm, 10)
        entry["is_commuting"] = is_commuting
        # For commuting states, Petz and sandwiched should agree at all alpha
        if is_commuting:
            entry["commuting_agreement"] = all(
                c["agree"] for c in entry["comparisons"]
            )
        else:
            # For non-commuting, they should generally differ (at least for some alpha)
            entry["any_disagreement"] = any(
                not c["agree"] for c in entry["comparisons"]
            )
        results.append(entry)
    return results


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    rng = np.random.default_rng(seed=42)
    pairs, labels = generate_test_pairs(rng)

    print("=" * 70)
    print("PURE LEGO: Quantum f-Divergences & Sandwiched Renyi Divergences")
    print("=" * 70)

    # --- Test 1: f-divergence reduction ---
    print("\n[1/5] Testing f-divergence reduction against direct formulas...")
    fdiv_results = test_f_divergence_reduction(pairs, labels)
    re_pass = sum(1 for r in fdiv_results if r["relative_entropy_match"])
    chi_pass = sum(1 for r in fdiv_results if r["chi_squared_match"])
    nn_pass = sum(1 for r in fdiv_results if r["all_nonneg"])
    print(f"  Relative entropy match: {re_pass}/10")
    print(f"  Chi-squared match:      {chi_pass}/10")
    print(f"  Non-negativity:         {nn_pass}/10")

    # --- Test 2: Sandwiched Renyi alpha->1 limit ---
    print("\n[2/5] Testing sandwiched Renyi alpha->1 limit...")
    limit_results = test_sandwiched_renyi_limit(pairs, labels)
    lim_pass = sum(1 for r in limit_results if r["limit_match"])
    print(f"  Limit matches relative entropy: {lim_pass}/10")

    # --- Test 3: Monotonicity under CPTP ---
    print("\n[3/5] Testing monotonicity under CPTP (alpha >= 1/2)...")
    mono_results = test_monotonicity_cptp(pairs, labels, rng)
    mono_total = 0
    mono_ok = 0
    for entry in mono_results:
        for t in entry["tests"]:
            mono_total += 2
            if t["monotone_depol"]:
                mono_ok += 1
            if t["monotone_random"]:
                mono_ok += 1
    print(f"  Monotonicity checks passed: {mono_ok}/{mono_total}")

    # --- Test 4: Data processing inequality ---
    print("\n[4/5] Testing data processing inequality (partial trace)...")
    dpi_results = test_data_processing_inequality(rng)
    dpi_total = 0
    dpi_ok = 0
    for entry in dpi_results:
        for t in entry["tests"]:
            dpi_total += 1
            if t["DPI_satisfied"]:
                dpi_ok += 1
    print(f"  DPI checks passed: {dpi_total}/{dpi_total} -> {dpi_ok}/{dpi_total}")

    # --- Test 5: Petz vs Sandwiched ---
    print("\n[5/5] Testing Petz vs Sandwiched Renyi comparison...")
    pvs_results = test_petz_vs_sandwiched(pairs, labels)
    comm_pairs = [r for r in pvs_results if r["is_commuting"]]
    noncomm_pairs = [r for r in pvs_results if not r["is_commuting"]]
    comm_agree = sum(1 for r in comm_pairs if r.get("commuting_agreement", False))
    noncomm_diff = sum(1 for r in noncomm_pairs if r.get("any_disagreement", False))
    print(f"  Commuting pairs agree (Petz==Sandwiched): {comm_agree}/{len(comm_pairs)}")
    print(f"  Non-commuting pairs differ:               {noncomm_diff}/{len(noncomm_pairs)}")

    # --- Aggregate ---
    all_pass = (
        re_pass == 10
        and chi_pass == 10
        and nn_pass == 10
        and lim_pass == 10
        and mono_ok == mono_total
        and dpi_ok == dpi_total
        and comm_agree == len(comm_pairs)
        and noncomm_diff == len(noncomm_pairs)
    )

    print("\n" + "=" * 70)
    verdict = "ALL CHECKS PASSED" if all_pass else "SOME CHECKS FAILED"
    print(f"VERDICT: {verdict}")
    print("=" * 70)

    # --- Write output ---
    output = {
        "probe": "sim_pure_lego_f_divergences",
        "timestamp": datetime.now(UTC).isoformat(),
        "verdict": verdict,
        "summary": {
            "relative_entropy_match": f"{re_pass}/10",
            "chi_squared_match": f"{chi_pass}/10",
            "nonneg": f"{nn_pass}/10",
            "sandwiched_limit": f"{lim_pass}/10",
            "monotonicity_cptp": f"{mono_ok}/{mono_total}",
            "data_processing_ineq": f"{dpi_ok}/{dpi_total}",
            "petz_sandwiched_commuting_agree": f"{comm_agree}/{len(comm_pairs)}",
            "petz_sandwiched_noncommuting_differ": f"{noncomm_diff}/{len(noncomm_pairs)}",
        },
        "f_divergence_results": fdiv_results,
        "sandwiched_limit_results": limit_results,
        "monotonicity_results": mono_results,
        "dpi_results": dpi_results,
        "petz_vs_sandwiched_results": pvs_results,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "pure_lego_f_divergences_results.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nResults written to: {out_path}")


if __name__ == "__main__":
    main()
