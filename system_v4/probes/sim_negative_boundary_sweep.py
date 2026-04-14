#!/usr/bin/env python3
"""
Negative Boundary Sweep
=======================
For each of 10 core quantum-information legos, find the EXACT parameter
value where the measure transitions from "working" to "broken" using
binary search to 6 decimal places.  Compare against known theory values.

No engine dependency.  Pure numpy/scipy.

Tests:
  1. Concurrence:  Werner p where C crosses 0          (theory 1/3)
  2. Negativity:   Werner p where N crosses 0          (theory 1/3)
  3. Bell-CHSH:    Werner p where CHSH crosses 2       (theory 1/sqrt(2))
  4. Steering:     Werner p where CJWR violation starts (theory 1/sqrt(3))
  5. Discord:      Werner p numerical floor for D > 0  (theory any p>0)
  6. QFI witness:  N threshold for QFI > shot noise    (GHZ-like)
  7. Depol. cap.:  p where quantum capacity Q crosses 0
  8. Amp. damp.:   gamma where Q crosses 0             (theory 1/2)
  9. Teleportation: Werner p where fidelity crosses 2/3 (theory 1/2)
 10. Schumacher:   rate where compression fidelity < 0.99
"""

import json
import os
import sys
import warnings
from datetime import datetime, timezone

import numpy as np
from scipy.linalg import sqrtm, logm
classification = "classical_baseline"  # auto-backfill

warnings.filterwarnings("ignore", category=RuntimeWarning)

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "a2_state", "sim_results")

# ═══════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════

BELL_PHI_PLUS = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)

def werner_state(p, d=2):
    """Werner state rho_W(p) = p|Phi+><Phi+| + (1-p)I/4 for 2 qubits."""
    proj = np.outer(BELL_PHI_PLUS, BELL_PHI_PLUS.conj())
    return p * proj + (1 - p) * np.eye(d * d) / (d * d)


def partial_transpose(rho, d=2):
    """Partial transpose over second subsystem."""
    rho_pt = rho.reshape(d, d, d, d)
    rho_pt = rho_pt.transpose(0, 3, 2, 1)
    return rho_pt.reshape(d * d, d * d)


def concurrence_2qubit(rho):
    """Wootters concurrence for a 2-qubit density matrix."""
    sy = np.array([[0, -1j], [1j, 0]])
    sigma_yy = np.kron(sy, sy)
    rho_tilde = sigma_yy @ rho.conj() @ sigma_yy
    M = rho @ rho_tilde
    evals = np.sort(np.real(np.sqrt(np.maximum(np.linalg.eigvals(M), 0))))[::-1]
    return max(0.0, evals[0] - evals[1] - evals[2] - evals[3])


def negativity(rho, d=2):
    """Negativity = (||rho^{T_B}||_1 - 1) / 2."""
    rho_pt = partial_transpose(rho, d)
    evals = np.linalg.eigvalsh(rho_pt)
    return float(np.sum(np.abs(evals) - evals) / 2)


def chsh_value_werner(p):
    """Max CHSH value for Werner state = 2*sqrt(2)*p."""
    return 2 * np.sqrt(2) * p


def cjwr_value_werner(p, n_measurements=2):
    """
    CJWR steering inequality for Werner state.
    For n measurements, violation when p > 1/sqrt(n).
    The steering functional value = sqrt(n)*p.
    Violation when > 1.
    """
    return np.sqrt(n_measurements) * p


def quantum_discord_werner(p):
    """
    Analytical quantum discord for 2-qubit Werner state.
    D = S(rho_B) - S(rho) + min_{meas} S(rho|meas)
    For Werner: eigenvalues of rho are (1+3p)/4 (once), (1-p)/4 (thrice).
    """
    if p < 1e-15:
        return 0.0

    # Eigenvalues of Werner state
    lam1 = (1 + 3 * p) / 4.0
    lam2 = (1 - p) / 4.0  # triply degenerate

    # von Neumann entropy S(rho)
    evals = [lam1, lam2, lam2, lam2]
    S_rho = 0.0
    for e in evals:
        if e > 1e-30:
            S_rho -= e * np.log2(e)

    # S(rho_B) = 1 (maximally mixed marginal)
    S_B = 1.0

    # Optimal measurement is along z: conditional entropy
    # After projective measurement on A, post-measurement states have eigenvalues
    # (1+p)/2 and (1-p)/2 for each outcome (equal probability 1/2)
    e_plus = (1 + p) / 2.0
    e_minus = (1 - p) / 2.0
    S_cond = 0.0
    for e in [e_plus, e_minus]:
        if e > 1e-30:
            S_cond -= e * np.log2(e)

    # Classical correlation J = S(B) - S(B|measurement on A) = S_B - S_cond
    # Discord D = I(A:B) - J = S(A) + S(B) - S(AB) - J
    # With S(A)=S(B)=1: D = 1 + 1 - S_rho - (1 - S_cond) = 1 - S_rho + S_cond
    discord = S_B - S_rho + S_cond
    return max(0.0, discord)


def qfi_ghz(n_qubits):
    """
    QFI for GHZ state under collective J_z rotation.
    QFI = n^2 for GHZ(n).  Shot noise limit = n.
    Returns QFI / shot_noise_limit.
    """
    return float(n_qubits)  # QFI/N = N for GHZ


def depolarizing_quantum_capacity(p):
    """
    Quantum capacity of depolarizing channel with parameter p.
    Channel: rho -> (1-p)*rho + p*I/2
    Capacity: Q = max(0, 1 - H(p) - p*log2(3))  (hashing bound, tight for depol.)
    where H(p) = -p*log2(p/3) - (1-p)*log2(1-p) is the entropy of
    the channel eigenvalues ((1-3p/4), (p/4), (p/4), (p/4)).

    Actually, for the depolarizing channel with E(rho) = (1-p)rho + p I/2:
    The coherent information maximized over input states gives
    Q1 = 1 + (1-p)*log2(1-p) + p*log2(p/3)
    for p in [0, some threshold].
    """
    if p <= 0:
        return 1.0
    if p >= 1:
        return 0.0

    # Kraus eigenvalues for depol channel: 1-3p/4, p/4, p/4, p/4
    # Coherent info for maximally mixed input:
    # Q1 = 1 + (1-3p/4)*log2(1-3p/4) + 3*(p/4)*log2(p/4)
    lam0 = 1.0 - 3.0 * p / 4.0
    lam1 = p / 4.0

    if lam0 <= 0 or lam1 <= 0:
        return 0.0

    Q1 = 1.0 + lam0 * np.log2(lam0) + 3.0 * lam1 * np.log2(lam1)
    return max(0.0, Q1)


def amplitude_damping_quantum_capacity(gamma):
    """
    Quantum capacity of amplitude damping channel.
    Q = max_p [ H(p*(1-gamma)) - H(p*gamma) ]
    For gamma < 1/2 there exists capacity > 0.
    We maximize over input parameter p in [0,1].
    """
    if gamma >= 1.0:
        return 0.0
    if gamma <= 0.0:
        return 1.0

    def h2(x):
        """Binary entropy."""
        if x <= 1e-15 or x >= 1.0 - 1e-15:
            return 0.0
        return -x * np.log2(x) - (1 - x) * np.log2(1 - x)

    best = 0.0
    for pp in np.linspace(0, 1, 2000):
        val = h2(pp * (1 - gamma)) - h2(pp * gamma)
        if val > best:
            best = val
    return best


def teleportation_fidelity_werner(p):
    """
    Teleportation fidelity using Werner state as resource.
    F = (2*p + 1) / 3  for standard protocol.
    Classical limit is 2/3.
    """
    return (2 * p + 1) / 3.0


def schumacher_fidelity(rate, q=0.3):
    """
    Schumacher compression fidelity via typical-subspace probability.

    For n iid copies of a qubit source with eigenvalues (q, 1-q):
    At compression rate R we keep the 2^(nR) highest-probability sequences.
    Work entirely in log2 space to handle large n.

    Uses n=500 for a sharp transition centered near S.
    """
    from scipy.special import gammaln

    n = 500
    log2_codewords = n * rate  # log2 of number of codewords we can store

    # For each type class k (k ones out of n):
    #   log2(count_k) = log2(C(n,k))
    #   log2(prob_each) = k*log2(q) + (n-k)*log2(1-q)
    #   log2(total_prob_class) = log2(count_k) + log2(prob_each)
    log2_q = np.log2(q + 1e-300)
    log2_1mq = np.log2(1 - q + 1e-300)
    ln2 = np.log(2.0)

    # Build arrays: per-sequence log prob, log2 of class count, log2 of class total prob
    ks = np.arange(n + 1)
    log2_prob_each = ks * log2_q + (n - ks) * log2_1mq
    # log2(C(n,k)) = (gammaln(n+1) - gammaln(k+1) - gammaln(n-k+1)) / ln(2)
    log2_count = (gammaln(n + 1) - gammaln(ks + 1) - gammaln(n - ks + 1)) / ln2
    log2_class_prob = log2_count + log2_prob_each

    # Sort classes by per-sequence probability (highest first = greedy optimal)
    order = np.argsort(-log2_prob_each)

    # Greedily include classes until we exhaust codewords.
    # Track remaining budget in log2 space.
    log2_budget = log2_codewords
    fidelity = 0.0

    for idx in order:
        lc = log2_count[idx]
        if lc <= log2_budget:
            # Include entire class
            fidelity += 2.0 ** log2_class_prob[idx]
            # Subtract: log2(budget - count) -- switch to linear for subtraction
            budget_lin = 2.0 ** log2_budget - 2.0 ** lc
            if budget_lin <= 0.5:
                break
            log2_budget = np.log2(budget_lin)
        else:
            # Partial: include only remaining budget worth of sequences
            # fraction = 2^log2_budget / 2^lc
            partial_log2 = log2_budget + log2_prob_each[idx]
            fidelity += 2.0 ** partial_log2
            break

    return min(fidelity, 1.0)


# ═══════════════════════════════════════════════════════════════════
# BINARY SEARCH ENGINE
# ═══════════════════════════════════════════════════════════════════

def binary_search_boundary(func, lo, hi, threshold, tol=1e-7,
                           above_means_working=True):
    """
    Find the parameter value where func(x) crosses threshold.

    If above_means_working=True: func(x) > threshold means "working",
      and we search for the lowest x where func(x) > threshold.
    If above_means_working=False: func(x) > threshold means "broken",
      and we search for the highest x where func(x) <= threshold.

    Returns the boundary value to within tol.
    """
    for _ in range(100):  # enough iterations for 1e-7 precision on [0,1]
        mid = (lo + hi) / 2.0
        val = func(mid)
        if above_means_working:
            # We want: below boundary -> func < threshold, above -> func > threshold
            if val > threshold:
                hi = mid
            else:
                lo = mid
        else:
            if val > threshold:
                lo = mid
            else:
                hi = mid
        if hi - lo < tol * 0.1:
            break
    return (lo + hi) / 2.0


# ═══════════════════════════════════════════════════════════════════
# 10 BOUNDARY TESTS
# ═══════════════════════════════════════════════════════════════════

def test_01_concurrence_boundary():
    """Find Werner p where concurrence crosses 0. Theory: 1/3."""
    def C_at_p(p):
        rho = werner_state(p)
        return concurrence_2qubit(rho)

    # C > 0 for p > 1/3, C = 0 for p <= 1/3
    boundary = binary_search_boundary(C_at_p, 0.0, 1.0, 0.0,
                                      above_means_working=True)
    theory = 1.0 / 3.0
    return {
        "test": "01_concurrence_boundary",
        "description": "Werner p where concurrence crosses 0",
        "found_boundary": round(boundary, 6),
        "theory_value": round(theory, 6),
        "gap": round(abs(boundary - theory), 8),
        "pass": abs(boundary - theory) < 1e-4,
        "value_at_boundary": round(C_at_p(boundary), 10),
        "value_just_above": round(C_at_p(boundary + 0.01), 10),
        "value_just_below": round(C_at_p(boundary - 0.01), 10),
    }


def test_02_negativity_boundary():
    """Find Werner p where negativity crosses 0. Theory: 1/3 (PPT boundary)."""
    def N_at_p(p):
        rho = werner_state(p)
        return negativity(rho)

    boundary = binary_search_boundary(N_at_p, 0.0, 1.0, 0.0,
                                      above_means_working=True)
    theory = 1.0 / 3.0
    return {
        "test": "02_negativity_boundary",
        "description": "Werner p where negativity crosses 0 (PPT boundary)",
        "found_boundary": round(boundary, 6),
        "theory_value": round(theory, 6),
        "gap": round(abs(boundary - theory), 8),
        "pass": abs(boundary - theory) < 1e-4,
        "concurrence_boundary_match": True,  # updated after comparison
        "value_at_boundary": round(N_at_p(boundary), 10),
    }


def test_03_bell_chsh_boundary():
    """Find Werner p where CHSH crosses 2. Theory: 1/sqrt(2)."""
    def chsh_at_p(p):
        return chsh_value_werner(p)

    boundary = binary_search_boundary(chsh_at_p, 0.0, 1.0, 2.0,
                                      above_means_working=True)
    theory = 1.0 / np.sqrt(2)
    return {
        "test": "03_bell_chsh_boundary",
        "description": "Werner p where CHSH value crosses 2",
        "found_boundary": round(boundary, 6),
        "theory_value": round(theory, 6),
        "gap": round(abs(boundary - theory), 8),
        "pass": abs(boundary - theory) < 1e-4,
        "chsh_at_boundary": round(chsh_at_p(boundary), 10),
    }


def test_04_steering_boundary():
    """Find Werner p where CJWR steering violation starts. Theory: 1/sqrt(3) for 3 settings."""
    # For n=3 measurement settings, violation threshold is 1/sqrt(3)
    n_meas = 3

    def steering_at_p(p):
        return np.sqrt(n_meas) * p  # CJWR functional

    # Violation when functional > 1
    boundary = binary_search_boundary(steering_at_p, 0.0, 1.0, 1.0,
                                      above_means_working=True)
    theory = 1.0 / np.sqrt(3)
    return {
        "test": "04_steering_boundary",
        "description": "Werner p where CJWR steering violation starts (n=3)",
        "found_boundary": round(boundary, 6),
        "theory_value": round(theory, 6),
        "gap": round(abs(boundary - theory), 8),
        "pass": abs(boundary - theory) < 1e-4,
        "functional_at_boundary": round(steering_at_p(boundary), 10),
    }


def test_05_discord_floor():
    """Find the numerical floor where discord > 0. Theory: any p > 0."""
    # Discord is > 0 for any p > 0 for Werner states.
    # Find the smallest p where our numerical computation gives D > machine_eps.
    threshold = 1e-12

    def D_at_p(p):
        return quantum_discord_werner(p)

    # Search for the floor: smallest p where D > threshold
    boundary = binary_search_boundary(D_at_p, 0.0, 1.0, threshold,
                                      above_means_working=True)
    theory = 0.0  # any p > 0 has discord
    return {
        "test": "05_discord_floor",
        "description": "Smallest Werner p where discord > numerical threshold",
        "found_floor": round(boundary, 10),
        "numerical_threshold": threshold,
        "theory_value": "any p > 0",
        "discord_at_floor": round(D_at_p(boundary), 15),
        "discord_at_0.001": round(D_at_p(0.001), 15),
        "discord_at_0.01": round(D_at_p(0.01), 12),
        "pass": boundary < 1e-4,  # should find floor very close to 0
    }


def test_06_qfi_witness():
    """Find N threshold where QFI exceeds shot noise. For GHZ: always above for N>=2."""
    # QFI for GHZ(N) = N^2, shot noise = N.  Ratio = N.
    # QFI > shot noise iff N > 1, i.e., any N >= 2.
    # With noise (depolarizing p_noise), find the threshold.
    # GHZ under depolarizing: QFI ~ N^2 * (1 - p_noise)^N approximately.
    # We search for N where QFI/N > 1 under fixed noise.

    p_noise = 0.05  # 5% depolarizing per qubit

    def qfi_ratio(n):
        """QFI / shot_noise for noisy GHZ(n)."""
        # Simplified model: each qubit depolarizes independently
        # Effective purity factor ~ (1-p_noise)^n
        # QFI ~ n^2 * (1-p_noise)^(2*n)  (approximate for product decoherence)
        effective = n * n * (1 - p_noise) ** (2 * n)
        return effective / n  # = n * (1-p_noise)^(2n)

    # Find N where qfi_ratio crosses 1 (from above to below as N increases)
    # For small N, ratio >> 1; for large N, exponential kills it
    boundary_n = binary_search_boundary(qfi_ratio, 1.0, 500.0, 1.0,
                                        above_means_working=False)
    return {
        "test": "06_qfi_witness_threshold",
        "description": "N where QFI/shot_noise crosses 1 under 5% depolarizing noise",
        "found_boundary_N": round(boundary_n, 6),
        "qfi_ratio_at_boundary": round(qfi_ratio(boundary_n), 10),
        "qfi_ratio_at_N_2": round(qfi_ratio(2), 10),
        "qfi_ratio_at_N_10": round(qfi_ratio(10), 10),
        "qfi_ratio_at_N_20": round(qfi_ratio(20), 10),
        "pass": True,  # informational boundary
        "note": "Above this N, noise kills the quantum advantage",
    }


def test_07_depolarizing_capacity():
    """Find p where quantum capacity Q crosses 0."""
    boundary = binary_search_boundary(depolarizing_quantum_capacity, 0.0, 1.0, 0.0,
                                      above_means_working=False)
    # Theoretical threshold for depol channel:
    # Q = 0 when 1 + (1-3p/4)log2(1-3p/4) + 3(p/4)log2(p/4) = 0
    # This is approximately p ~ 0.25268 (known numerically)
    theory_approx = 0.25268

    return {
        "test": "07_depolarizing_capacity_boundary",
        "description": "Depolarizing p where quantum capacity crosses 0",
        "found_boundary": round(boundary, 6),
        "theory_approx": theory_approx,
        "gap": round(abs(boundary - theory_approx), 8),
        "pass": abs(boundary - theory_approx) < 1e-3,
        "capacity_at_boundary": round(depolarizing_quantum_capacity(boundary), 10),
        "capacity_at_0.1": round(depolarizing_quantum_capacity(0.1), 10),
        "capacity_at_0.3": round(depolarizing_quantum_capacity(0.3), 10),
    }


def test_08_amplitude_damping_capacity():
    """Find gamma where amplitude damping Q crosses 0. Theory: 1/2."""
    boundary = binary_search_boundary(amplitude_damping_quantum_capacity,
                                      0.0, 1.0, 0.0,
                                      above_means_working=False)
    theory = 0.5
    return {
        "test": "08_amplitude_damping_boundary",
        "description": "Gamma where amplitude damping capacity crosses 0",
        "found_boundary": round(boundary, 6),
        "theory_value": theory,
        "gap": round(abs(boundary - theory), 8),
        "pass": abs(boundary - theory) < 1e-3,
        "capacity_at_boundary": round(amplitude_damping_quantum_capacity(boundary), 10),
        "capacity_at_0.4": round(amplitude_damping_quantum_capacity(0.4), 10),
        "capacity_at_0.6": round(amplitude_damping_quantum_capacity(0.6), 10),
    }


def test_09_teleportation_boundary():
    """Find Werner p where teleportation fidelity crosses 2/3. Theory: 1/2."""
    def fid_at_p(p):
        return teleportation_fidelity_werner(p)

    boundary = binary_search_boundary(fid_at_p, 0.0, 1.0, 2.0 / 3.0,
                                      above_means_working=True)
    theory = 0.5
    return {
        "test": "09_teleportation_fidelity_boundary",
        "description": "Werner p where teleportation fidelity crosses 2/3",
        "found_boundary": round(boundary, 6),
        "theory_value": theory,
        "gap": round(abs(boundary - theory), 8),
        "pass": abs(boundary - theory) < 1e-4,
        "fidelity_at_boundary": round(fid_at_p(boundary), 10),
        "fidelity_at_0.4": round(fid_at_p(0.4), 10),
        "fidelity_at_0.6": round(fid_at_p(0.6), 10),
    }


def test_10_schumacher_boundary():
    """Find rate where Schumacher compression fidelity crosses 0.99."""
    # Source: qubit with eigenvalues (0.7, 0.3), entropy S = H(0.3)
    q = 0.3
    S = -q * np.log2(q) - (1 - q) * np.log2(1 - q)

    def fid_at_rate(r):
        return schumacher_fidelity(r, q=q)

    # Fidelity > 0.99 when rate >= S (approximately)
    boundary = binary_search_boundary(fid_at_rate, 0.0, 1.0, 0.99,
                                      above_means_working=True)
    return {
        "test": "10_schumacher_compression_boundary",
        "description": "Rate where Schumacher fidelity crosses 0.99",
        "found_boundary_rate": round(boundary, 6),
        "source_entropy": round(S, 6),
        "gap_from_entropy": round(abs(boundary - S), 8),
        "pass": abs(boundary - S) < 0.05,  # should be very close to S
        "fidelity_at_boundary": round(fid_at_rate(boundary), 10),
        "fidelity_at_entropy": round(fid_at_rate(S), 10),
        "note": "Boundary should match source entropy (Shannon limit)",
    }


# ═══════════════════════════════════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════════════════════════════════

def main():
    np.random.seed(42)
    ts = datetime.now(timezone.utc).isoformat()

    tests = [
        test_01_concurrence_boundary,
        test_02_negativity_boundary,
        test_03_bell_chsh_boundary,
        test_04_steering_boundary,
        test_05_discord_floor,
        test_06_qfi_witness,
        test_07_depolarizing_capacity,
        test_08_amplitude_damping_capacity,
        test_09_teleportation_boundary,
        test_10_schumacher_boundary,
    ]

    results = []
    pass_count = 0
    for fn in tests:
        print(f"  Running {fn.__name__} ...")
        try:
            r = fn()
            results.append(r)
            passed = r.get("pass", False)
            if passed:
                pass_count += 1
            tag = "PASS" if passed else "FAIL"
            print(f"    [{tag}] {r.get('description', '')}")
        except Exception as exc:
            results.append({
                "test": fn.__name__,
                "pass": False,
                "error": str(exc),
            })
            print(f"    [ERROR] {exc}")

    # Cross-check: concurrence and negativity boundaries should match
    if len(results) >= 2:
        c_bound = results[0].get("found_boundary", 0)
        n_bound = results[1].get("found_boundary", 0)
        results[1]["concurrence_boundary_match"] = abs(c_bound - n_bound) < 1e-4

    total = len(tests)
    report = {
        "probe": "negative_boundary_sweep",
        "timestamp": ts,
        "summary": f"{pass_count}/{total} boundaries match theory",
        "all_pass": pass_count == total,
        "results": results,
    }

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, "negative_boundary_sweep_results.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n  Output -> {out_path}")
    print(f"  Summary: {pass_count}/{total} PASS")
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
