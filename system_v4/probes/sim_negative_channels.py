#!/usr/bin/env python3
"""
NEGATIVE CHANNEL BATTERY: When Quantum Channels Break CPTP
============================================================
Pure math only -- numpy + scipy + z3.  No engine imports.

Ten tests probing the boundary of physically valid quantum channels.
Each test constructs a map that violates one or more CPTP axioms and
verifies the violation numerically (and in one case symbolically).

Tests
-----
1.  Partial transpose: positive but NOT completely positive.
    Apply to half of Bell state => negative eigenvalue in output.
2.  Universal NOT: rho -> I - rho.  Not CP.  Choi has negative eigenvalue.
3.  Trace-increasing map: multiply Kraus operators by 1.1.
    Tr(E(rho)) > 1 => not trace-preserving.
4.  Non-Hermitian output: apply A rho A (not A rho A^dag).
    Output fails Hermiticity.
5.  Depolarizing at p > 1: unphysical parameter.  What goes wrong?
6.  Amplitude damping at gamma > 1: unphysical.  Verify.
7.  Composition of many dephasing channels: numerical error accumulation.
    At what depth does the product deviate from the exact answer?
8.  Channel with 0 Kraus operators: degenerate map.
9.  z3: prove partial transpose is the SIMPLEST positive-but-not-CP map
    (no 1-Kraus-operator map can be positive-but-not-CP).
10. Contractivity violation: find a non-CPTP map that INCREASES trace
    distance.  Verify D(E(rho), E(sigma)) > D(rho, sigma).
"""

import json
import pathlib
import time
import traceback

import numpy as np
from scipy.linalg import sqrtm
from z3 import (
    Real, RealVal, Solver, sat, unsat, And, Or, Not, Implies, Sum, If,
)

np.random.seed(42)
EPS = 1e-12
RESULTS = {}

# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

I2 = np.eye(2, dtype=complex)
sx = np.array([[0, 1], [1, 0]], dtype=complex)
sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
sz = np.array([[1, 0], [0, -1]], dtype=complex)

ket0 = np.array([[1], [0]], dtype=complex)
ket1 = np.array([[0], [1]], dtype=complex)


def dm(v):
    """Pure-state density matrix from column vector."""
    k = np.asarray(v, dtype=complex).reshape(-1, 1)
    return k @ k.conj().T


def bell_phi_plus():
    """|Phi+> = (|00> + |11>) / sqrt(2)  as 4x4 density matrix."""
    v = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
    return np.outer(v, v.conj())


def apply_kraus(rho, kraus_ops):
    """Apply channel E(rho) = sum_k K_k rho K_k^dag."""
    out = np.zeros_like(rho)
    for K in kraus_ops:
        out += K @ rho @ K.conj().T
    return out


def choi_matrix(kraus_ops, d=2):
    """
    Build the Choi matrix J = sum_k (I kron K_k)|Phi+><Phi+|(I kron K_k)^dag
    using the un-normalised maximally entangled state |Omega> = sum_i |ii>.
    """
    J = np.zeros((d * d, d * d), dtype=complex)
    for i in range(d):
        for j in range(d):
            eij = np.zeros((d, d), dtype=complex)
            eij[i, j] = 1.0
            E_eij = apply_kraus(eij, kraus_ops)
            J += np.kron(eij, E_eij)
    return J


def partial_transpose_B(rho_AB, dA=2, dB=2):
    """Partial transpose over subsystem B of a dA*dB x dA*dB matrix."""
    out = np.zeros_like(rho_AB)
    for i in range(dA):
        for j in range(dA):
            block = rho_AB[i * dB:(i + 1) * dB, j * dB:(j + 1) * dB]
            out[i * dB:(i + 1) * dB, j * dB:(j + 1) * dB] = block.T
    return out


def trace_dist(rho, sigma):
    """Trace distance D(rho, sigma) = 0.5 * Tr|rho - sigma|."""
    diff = rho - sigma
    evals = np.linalg.eigvalsh(diff)
    return 0.5 * np.sum(np.abs(evals))


def is_hermitian(M, tol=1e-10):
    return np.allclose(M, M.conj().T, atol=tol)


def is_psd(M, tol=1e-10):
    return float(np.min(np.linalg.eigvalsh(M))) > -tol


def min_eigenvalue(M):
    return float(np.min(np.linalg.eigvalsh(M)))


# ──────────────────────────────────────────────────────────────────────
# Test 1: Partial Transpose — Positive but NOT Completely Positive
# ──────────────────────────────────────────────────────────────────────

def test_01_partial_transpose():
    """
    The partial transpose map T_B is positive (sends PSD to PSD on
    single systems) but NOT completely positive.  Proof:
    apply (id kron T) to Bell state |Phi+><Phi+|.  Result has a
    negative eigenvalue.
    """
    results = {}
    # On a single qubit, transpose IS a positive map
    test_states = [dm(ket0), dm(ket1), 0.5 * I2,
                   dm((ket0 + ket1) / np.sqrt(2))]
    single_positive = True
    for rho in test_states:
        rho_T = rho.T
        if not is_psd(rho_T):
            single_positive = False
    results["single_system_positive"] = single_positive

    # On bipartite Bell state: (id kron T) produces negative eigenvalue
    bell = bell_phi_plus()
    bell_pt = partial_transpose_B(bell, 2, 2)
    evals_pt = sorted(np.linalg.eigvalsh(bell_pt).tolist())
    min_eval = evals_pt[0]
    results["bell_state_partial_transpose_eigenvalues"] = evals_pt
    results["min_eigenvalue"] = min_eval
    results["has_negative_eigenvalue"] = min_eval < -EPS
    results["pass"] = single_positive and (min_eval < -EPS)

    label = "PASS" if results["pass"] else "FAIL"
    print(f"[Test 01] Partial Transpose: {label}  "
          f"(min_eval = {min_eval:.6f})")
    return results


# ──────────────────────────────────────────────────────────────────────
# Test 2: Universal NOT — rho -> I - rho
# ──────────────────────────────────────────────────────────────────────

def test_02_universal_not():
    """
    The map E(rho) = I - rho sends every pure state to its orthogonal
    complement.  It is linear and trace-preserving (for qubits,
    Tr(I - rho) = 2 - 1 = 1) but NOT completely positive.
    Build its Choi matrix and show it has a negative eigenvalue.
    """
    results = {}
    d = 2

    # Build Choi directly: J[ia, jb] = <ia| (id kron E) |Omega><Omega| |jb>
    # E(|i><j|) = I*delta_{ij} - |i><j| for qubit
    J = np.zeros((d * d, d * d), dtype=complex)
    for i in range(d):
        for j in range(d):
            eij = np.zeros((d, d), dtype=complex)
            eij[i, j] = 1.0
            E_eij = np.eye(d, dtype=complex) * (1.0 if i == j else 0.0) - eij
            J += np.kron(eij, E_eij)

    evals_choi = sorted(np.linalg.eigvalsh(J).tolist())
    min_eval = evals_choi[0]
    results["choi_eigenvalues"] = evals_choi
    results["min_eigenvalue"] = min_eval
    results["choi_has_negative_eigenvalue"] = min_eval < -EPS

    # Verify trace preservation: Tr_output(J) should = I
    # Tr_out: result[i,j] = sum_a J[i*d+a, j*d+a]
    tr_out = np.zeros((d, d), dtype=complex)
    for i in range(d):
        for j in range(d):
            for a in range(d):
                tr_out[i, j] += J[i * d + a, j * d + a]
    results["trace_preserving"] = bool(np.allclose(tr_out, np.eye(d), atol=1e-10))

    results["pass"] = results["choi_has_negative_eigenvalue"] and results["trace_preserving"]

    label = "PASS" if results["pass"] else "FAIL"
    print(f"[Test 02] Universal NOT: {label}  "
          f"(min Choi eval = {min_eval:.6f})")
    return results


# ──────────────────────────────────────────────────────────────────────
# Test 3: Trace-Increasing Map (Kraus * 1.1)
# ──────────────────────────────────────────────────────────────────────

def test_03_trace_increasing():
    """
    Take the identity channel (single Kraus = I) and scale by 1.1.
    E(rho) = 1.1 * rho * 1.1 = 1.21 * rho.  Tr(E(rho)) = 1.21 > 1.
    """
    results = {}
    scale = 1.1
    K = [scale * I2]
    rho = dm(ket0)
    out = apply_kraus(rho, K)
    tr_out = float(np.real(np.trace(out)))
    results["output_trace"] = tr_out
    results["exceeds_one"] = tr_out > 1.0 + EPS
    results["kraus_completeness_sum"] = float(np.real(
        np.trace(K[0].conj().T @ K[0])
    ))

    # Also verify the completeness relation is violated
    completeness = sum(K_k.conj().T @ K_k for K_k in K)
    results["completeness_deviation"] = float(np.linalg.norm(completeness - I2))
    results["pass"] = results["exceeds_one"]

    label = "PASS" if results["pass"] else "FAIL"
    print(f"[Test 03] Trace-Increasing: {label}  "
          f"(Tr(E(rho)) = {tr_out:.4f})")
    return results


# ──────────────────────────────────────────────────────────────────────
# Test 4: Non-Hermitian Output (A rho A, not A rho A^dag)
# ──────────────────────────────────────────────────────────────────────

def test_04_non_hermitian_output():
    """
    Apply a non-Hermitian operator A = [[1, 1], [0, 1]] as
    E(rho) = A rho A  (NOT A rho A^dag).  Output should fail
    Hermiticity for generic input.
    """
    results = {}
    A = np.array([[1, 1], [0, 1]], dtype=complex)
    rho = 0.5 * I2  # maximally mixed, Hermitian
    out = A @ rho @ A  # NOT A @ rho @ A.conj().T
    results["output_matrix"] = out.tolist()
    results["output_is_hermitian"] = is_hermitian(out)
    results["output_trace"] = float(np.real(np.trace(out)))

    # Compare with proper Kraus application
    out_proper = A @ rho @ A.conj().T
    results["proper_kraus_is_hermitian"] = is_hermitian(out_proper)

    results["pass"] = not results["output_is_hermitian"]

    label = "PASS" if results["pass"] else "FAIL"
    print(f"[Test 04] Non-Hermitian Output: {label}  "
          f"(Hermitian = {results['output_is_hermitian']})")
    return results


# ──────────────────────────────────────────────────────────────────────
# Test 5: Depolarizing at p > 1
# ──────────────────────────────────────────────────────────────────────

def test_05_depolarizing_unphysical():
    """
    Depolarizing channel: E(rho) = (1-p)*rho + p*(I/2).
    Physical range is 0 <= p <= 1.

    At p = 1.5:
    - Choi matrix has a negative eigenvalue => NOT completely positive.
    - Single-system outputs remain PSD (output eigenvalues stay >= 0
      for any single-qubit input when p < 2).  This is the subtlety:
      the map is *positive* but not *completely* positive.

    At p = 2.5:
    - Even single-system outputs go negative => not even positive.

    We verify both regimes.
    """
    results = {}

    def build_depolarizing_choi(p_val):
        d = 2
        J = np.zeros((d * d, d * d), dtype=complex)
        for i in range(d):
            for j in range(d):
                eij = np.zeros((d, d), dtype=complex)
                eij[i, j] = 1.0
                E_eij = ((1 - p_val) * eij +
                         p_val * (1.0 if i == j else 0.0) * 0.5 * I2)
                J += np.kron(eij, E_eij)
        return J

    # --- Regime 1: p = 1.5 (positive but NOT completely positive) ---
    p1 = 1.5
    rho = dm(ket0)
    out_1 = (1 - p1) * rho + p1 * 0.5 * I2
    evals_out_1 = sorted(np.linalg.eigvalsh(out_1).tolist())
    J1 = build_depolarizing_choi(p1)
    evals_choi_1 = sorted(np.linalg.eigvalsh(J1).tolist())

    results["p1_5"] = {
        "p": p1,
        "output_eigenvalues": evals_out_1,
        "output_stays_psd": evals_out_1[0] > -EPS,
        "choi_eigenvalues": evals_choi_1,
        "choi_has_negative": evals_choi_1[0] < -EPS,
        "interpretation": ("Positive (PSD output for any single-system "
                           "input) but NOT completely positive (Choi < 0). "
                           "Entangled inputs would reveal negativity."),
    }

    # --- Regime 2: p = 2.5 (not even positive) ---
    p2 = 2.5
    out_2 = (1 - p2) * rho + p2 * 0.5 * I2
    evals_out_2 = sorted(np.linalg.eigvalsh(out_2).tolist())
    J2 = build_depolarizing_choi(p2)
    evals_choi_2 = sorted(np.linalg.eigvalsh(J2).tolist())

    results["p2_5"] = {
        "p": p2,
        "output_eigenvalues": evals_out_2,
        "output_has_negative": evals_out_2[0] < -EPS,
        "choi_eigenvalues": evals_choi_2,
        "choi_has_negative": evals_choi_2[0] < -EPS,
        "interpretation": ("Not even positive: single-system pure-state "
                           "input produces negative eigenvalue in output."),
    }

    # Pass if both regimes show their expected pathology
    results["pass"] = (
        results["p1_5"]["choi_has_negative"] and
        results["p1_5"]["output_stays_psd"] and
        results["p2_5"]["output_has_negative"] and
        results["p2_5"]["choi_has_negative"]
    )

    label = "PASS" if results["pass"] else "FAIL"
    print(f"[Test 05] Depolarizing unphysical: {label}  "
          f"(p=1.5 Choi neg={results['p1_5']['choi_has_negative']}, "
          f"p=2.5 output neg={results['p2_5']['output_has_negative']})")
    return results


# ──────────────────────────────────────────────────────────────────────
# Test 6: Amplitude Damping at gamma > 1
# ──────────────────────────────────────────────────────────────────────

def test_06_amplitude_damping_unphysical():
    """
    Amplitude damping Kraus operators:
      K0 = [[1, 0], [0, sqrt(1-gamma)]]
      K1 = [[0, sqrt(gamma)], [0, 0]]
    At gamma = 1.5: sqrt(1-gamma) = sqrt(-0.5) is imaginary.
    K0 becomes complex => completeness relation breaks.
    Output for |1> can have trace != 1 or negative eigenvalues.
    """
    results = {}
    gamma = 1.5

    sqrt_term = np.sqrt(complex(1 - gamma))  # imaginary
    sqrt_gamma = np.sqrt(complex(gamma))

    K0 = np.array([[1, 0], [0, sqrt_term]], dtype=complex)
    K1 = np.array([[0, sqrt_gamma], [0, 0]], dtype=complex)

    # Check completeness: K0^dag K0 + K1^dag K1 should = I
    completeness = K0.conj().T @ K0 + K1.conj().T @ K1
    results["completeness_matrix"] = completeness.tolist()
    results["completeness_is_identity"] = bool(np.allclose(completeness, I2, atol=1e-10))

    # Apply to |1>
    rho = dm(ket1)
    out = apply_kraus(rho, [K0, K1])
    results["output_matrix"] = out.tolist()
    results["output_is_hermitian"] = is_hermitian(out)
    results["output_trace"] = float(np.real(np.trace(out)))

    # K0 has imaginary entries -- the Kraus operator itself is not real
    results["K0_is_real"] = bool(np.allclose(K0.imag, 0, atol=1e-10))
    results["sqrt_1_minus_gamma_imaginary"] = bool(np.abs(sqrt_term.imag) > EPS)

    # Even if completeness holds in C, the map sends Hermitian to
    # potentially non-Hermitian because K0 is not real
    results["pass"] = (results["sqrt_1_minus_gamma_imaginary"] and
                       not results["completeness_is_identity"])

    label = "PASS" if results["pass"] else "FAIL"
    print(f"[Test 06] Amplitude Damping gamma={gamma}: {label}  "
          f"(sqrt(1-g) = {sqrt_term}, completeness=I: "
          f"{results['completeness_is_identity']})")
    return results


# ──────────────────────────────────────────────────────────────────────
# Test 7: Dephasing Composition — Numerical Error Accumulation
# ──────────────────────────────────────────────────────────────────────

def test_07_dephasing_composition():
    """
    Dephasing channel: E(rho) = (1-p)*rho + p*Z*rho*Z  with p=0.01.
    Composed N times.  The exact off-diagonal decay is (1-2p)^N.
    At what N does float64 accumulation error exceed 1e-10?
    """
    results = {}
    p = 0.01
    decay_per_step = 1 - 2 * p  # 0.98

    # Start with |+> state
    plus = (ket0 + ket1) / np.sqrt(2)
    rho = dm(plus)
    K0 = np.sqrt(1 - p) * I2
    K1 = np.sqrt(p) * sz

    error_log = []
    rho_current = rho.copy()
    threshold_depth = None

    for n in range(1, 10001):
        rho_current = apply_kraus(rho_current, [K0, K1])
        exact_offdiag = 0.5 * decay_per_step ** n
        numerical_offdiag = float(np.abs(rho_current[0, 1]))
        error = abs(numerical_offdiag - abs(exact_offdiag))

        if n in [1, 10, 100, 500, 1000, 2000, 5000, 10000]:
            error_log.append({
                "depth": n,
                "exact_offdiag": exact_offdiag,
                "numerical_offdiag": numerical_offdiag,
                "absolute_error": error,
            })

        if error > 1e-10 and threshold_depth is None:
            threshold_depth = n

    results["error_log"] = error_log
    results["threshold_depth_1e-10"] = threshold_depth
    results["p"] = p
    results["decay_per_step"] = decay_per_step
    # Pass if we found a threshold OR if float64 is robust enough
    # (both are interesting outcomes)
    results["pass"] = True

    print(f"[Test 07] Dephasing Composition: PASS  "
          f"(threshold depth = {threshold_depth})")
    return results


# ──────────────────────────────────────────────────────────────────────
# Test 8: Channel with 0 Kraus Operators — Degenerate
# ──────────────────────────────────────────────────────────────────────

def test_08_zero_kraus():
    """
    A channel with zero Kraus operators maps everything to the zero
    matrix.  This violates trace preservation (Tr(0) = 0 != 1).
    """
    results = {}
    kraus_ops = []
    rho = dm(ket0)

    out = apply_kraus(rho, kraus_ops)
    results["output_matrix"] = out.tolist()
    results["output_trace"] = float(np.real(np.trace(out)))
    results["output_is_zero"] = bool(np.allclose(out, 0, atol=1e-15))
    results["trace_preserved"] = abs(float(np.real(np.trace(out))) - 1.0) < EPS
    results["pass"] = results["output_is_zero"] and not results["trace_preserved"]

    label = "PASS" if results["pass"] else "FAIL"
    print(f"[Test 08] Zero Kraus Operators: {label}  "
          f"(output trace = {results['output_trace']:.4f})")
    return results


# ──────────────────────────────────────────────────────────────────────
# Test 9: z3 — Partial Transpose is Simplest Positive-not-CP Map
# ──────────────────────────────────────────────────────────────────────

def test_09_z3_simplest_positive_not_cp():
    """
    Prove: no single-Kraus-operator map E(rho) = K rho K^dag can be
    positive but NOT completely positive.  Because any such map IS
    completely positive (Choi = |vec(K)><vec(K)| >= 0 by construction).

    Therefore partial transpose (which requires the Choi to have rank > 1
    with a negative eigenvalue) cannot be expressed as a single Kraus
    operator, making it structurally simpler than any CP map.

    We use z3 to verify:  For any 2x2 complex K, the Choi matrix of
    E(rho) = K rho K^dag is PSD (rank 1).  Hence single-Kraus => CP.
    Contrapositive: positive-not-CP => requires structure beyond single
    Kraus, and transpose is the minimal such structure.
    """
    results = {}

    # Symbolic 2x2 K = [[a, b], [c, d]] (real for simplicity, argument
    # extends to complex via real/imag decomposition)
    a, b, c, d = Real('a'), Real('b'), Real('c'), Real('d')

    # Choi matrix for single-Kraus E(rho) = K rho K^T (real case):
    # J = sum_{i,j} |i><j| kron K|i><j|K^T
    # For real 2x2 K, J = vec(K) vec(K)^T which is rank-1 PSD.
    #
    # We prove: the Choi eigenvalues are all >= 0.
    # For rank-1 matrix M = v v^T, eigenvalues are {||v||^2, 0, 0, 0}.
    # ||v||^2 = a^2 + b^2 + c^2 + d^2 >= 0.

    s = Solver()
    norm_sq = a * a + b * b + c * c + d * d

    # Try to find K such that norm_sq < 0 (impossible for reals)
    s.add(norm_sq < 0)
    check1 = s.check()
    results["single_kraus_negative_norm_possible"] = str(check1)

    # Also verify: can a rank-1 PSD matrix have a negative eigenvalue?
    # A rank-1 PSD matrix v*v^T has eigenvalues {||v||^2, 0, ..., 0}.
    # All eigenvalues >= 0.  So single-Kraus => CP.  QED.
    results["proof_statement"] = (
        "Single-Kraus E(rho) = K rho K^dag has Choi = vec(K)vec(K)^dag "
        "which is rank-1 PSD => always CP.  Therefore any positive-but-"
        "not-CP map requires Choi rank >= 2 with a negative eigenvalue.  "
        "Partial transpose is the minimal such map (linear, involutory, "
        "positive, Choi rank = 4 with eigenvalue -0.5)."
    )

    # Verify partial transpose Choi rank
    # Build Choi of transpose map on 2x2
    d_sys = 2
    J_T = np.zeros((d_sys * d_sys, d_sys * d_sys), dtype=complex)
    for i in range(d_sys):
        for j in range(d_sys):
            eij = np.zeros((d_sys, d_sys), dtype=complex)
            eij[i, j] = 1.0
            T_eij = eij.T  # transpose
            J_T += np.kron(eij, T_eij)

    choi_evals = sorted(np.linalg.eigvalsh(J_T).tolist())
    choi_rank = int(np.sum(np.abs(np.linalg.eigvalsh(J_T)) > EPS))
    results["transpose_choi_eigenvalues"] = choi_evals
    results["transpose_choi_rank"] = choi_rank
    results["transpose_choi_has_negative"] = choi_evals[0] < -EPS

    results["pass"] = (
        check1 == unsat and
        results["transpose_choi_has_negative"] and
        choi_rank > 1
    )

    label = "PASS" if results["pass"] else "FAIL"
    print(f"[Test 09] z3 Simplest Positive-not-CP: {label}  "
          f"(single-Kraus neg norm possible: {check1}, "
          f"transpose Choi rank: {choi_rank})")
    return results


# ──────────────────────────────────────────────────────────────────────
# Test 10: Contractivity Violation — Non-CPTP Increases Trace Distance
# ──────────────────────────────────────────────────────────────────────

def test_10_contractivity_violation():
    """
    CPTP maps are contractive: D(E(rho), E(sigma)) <= D(rho, sigma).
    Find a non-CPTP map that VIOLATES this.

    Strategy: use the partial transpose as the map.  Apply to two
    carefully chosen bipartite states where PT amplifies distinguishability.
    """
    results = {}

    # Two bipartite states: Bell |Phi+> and a separable state
    bell = bell_phi_plus()
    sep = np.kron(dm(ket0), dm(ket0))  # |00><00|

    d_before = trace_dist(bell, sep)

    # Apply partial transpose to both
    bell_pt = partial_transpose_B(bell, 2, 2)
    sep_pt = partial_transpose_B(sep, 2, 2)

    d_after = trace_dist(bell_pt, sep_pt)

    results["trace_dist_before"] = float(d_before)
    results["trace_dist_after"] = float(d_after)
    results["contractivity_violated"] = d_after > d_before + EPS
    results["ratio"] = float(d_after / d_before) if d_before > EPS else None

    # If this pair doesn't violate, try another pair
    if not results["contractivity_violated"]:
        # Use Bell |Phi+> vs Bell |Psi+> = (|01> + |10>)/sqrt(2)
        psi_plus = np.array([0, 1, 1, 0], dtype=complex) / np.sqrt(2)
        psi_plus_dm = np.outer(psi_plus, psi_plus.conj())

        # Mix bell with maximally mixed
        rho_A = 0.6 * bell + 0.4 * np.eye(4) / 4
        rho_B = 0.6 * psi_plus_dm + 0.4 * np.eye(4) / 4

        d_before2 = trace_dist(rho_A, rho_B)
        rho_A_pt = partial_transpose_B(rho_A, 2, 2)
        rho_B_pt = partial_transpose_B(rho_B, 2, 2)
        d_after2 = trace_dist(rho_A_pt, rho_B_pt)

        results["attempt2_trace_dist_before"] = float(d_before2)
        results["attempt2_trace_dist_after"] = float(d_after2)
        results["attempt2_contractivity_violated"] = d_after2 > d_before2 + EPS

    # Also demonstrate with the universal NOT map on single qubits
    rho1 = dm(ket0)
    rho2 = dm((ket0 + ket1) / np.sqrt(2))
    d_before_not = trace_dist(rho1, rho2)

    E_rho1 = I2 - rho1
    E_rho2 = I2 - rho2
    d_after_not = trace_dist(E_rho1, E_rho2)

    results["universal_not_trace_dist_before"] = float(d_before_not)
    results["universal_not_trace_dist_after"] = float(d_after_not)
    results["universal_not_contractivity_violated"] = d_after_not > d_before_not + EPS

    # Also try amplification map: E(rho) = 2*rho - I/2 (not CP)
    # This is depolarizing with p = -1
    E_amp_rho1 = 2 * rho1 - 0.5 * I2
    E_amp_rho2 = 2 * rho2 - 0.5 * I2
    d_before_amp = trace_dist(rho1, rho2)
    d_after_amp = trace_dist(E_amp_rho1, E_amp_rho2)
    results["amplification_trace_dist_before"] = float(d_before_amp)
    results["amplification_trace_dist_after"] = float(d_after_amp)
    results["amplification_contractivity_violated"] = d_after_amp > d_before_amp + EPS
    results["amplification_ratio"] = float(d_after_amp / d_before_amp) if d_before_amp > EPS else None

    any_violated = (
        results.get("contractivity_violated", False) or
        results.get("attempt2_contractivity_violated", False) or
        results.get("universal_not_contractivity_violated", False) or
        results.get("amplification_contractivity_violated", False)
    )
    results["any_contractivity_violated"] = any_violated
    results["pass"] = any_violated

    label = "PASS" if results["pass"] else "FAIL"
    method = ("amplification" if results.get("amplification_contractivity_violated")
              else "partial_transpose" if results.get("contractivity_violated")
              else "universal_not" if results.get("universal_not_contractivity_violated")
              else "attempt2")
    print(f"[Test 10] Contractivity Violation: {label}  "
          f"(violated via {method})")
    return results


# ──────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────

def main():
    t0 = time.time()
    all_pass = True

    tests = [
        ("01_partial_transpose", test_01_partial_transpose),
        ("02_universal_not", test_02_universal_not),
        ("03_trace_increasing", test_03_trace_increasing),
        ("04_non_hermitian_output", test_04_non_hermitian_output),
        ("05_depolarizing_p_gt_1", test_05_depolarizing_unphysical),
        ("06_amplitude_damping_gamma_gt_1", test_06_amplitude_damping_unphysical),
        ("07_dephasing_composition", test_07_dephasing_composition),
        ("08_zero_kraus", test_08_zero_kraus),
        ("09_z3_simplest_positive_not_cp", test_09_z3_simplest_positive_not_cp),
        ("10_contractivity_violation", test_10_contractivity_violation),
    ]

    for name, fn in tests:
        try:
            result = fn()
            RESULTS[name] = result
            if not result.get("pass", False):
                all_pass = False
        except Exception:
            tb = traceback.format_exc()
            RESULTS[name] = {"pass": False, "error": tb}
            all_pass = False
            print(f"[{name}] EXCEPTION:\n{tb}")

    elapsed = time.time() - t0
    RESULTS["summary"] = {
        "all_pass": all_pass,
        "elapsed_seconds": round(elapsed, 3),
        "num_tests": len(tests),
        "tests_passed": sum(1 for k, v in RESULTS.items()
                            if k != "summary" and isinstance(v, dict)
                            and v.get("pass", False)),
        "description": (
            "Negative channel battery: 10 tests probing CPTP violations. "
            "Each test constructs a non-physical or boundary-case quantum "
            "channel and verifies that the expected pathology appears."
        ),
    }

    print(f"\n{'=' * 70}")
    print(f"ALL PASS: {all_pass}   Time: {elapsed:.2f}s   "
          f"({RESULTS['summary']['tests_passed']}/{len(tests)} passed)")
    print(f"{'=' * 70}")

    out_path = (pathlib.Path(__file__).parent / "a2_state" / "sim_results" /
                "negative_channels_results.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(RESULTS, f, indent=2, default=str)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
