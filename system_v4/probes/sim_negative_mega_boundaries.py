#!/usr/bin/env python3
"""
Negative MEGA Boundary Probe
=============================
15 boundary/failure tests probing where numerical quantum-information
primitives break down.  Pure numpy/scipy -- no engine dependency.

Tests:
  1.  Purity boundary for discord detectability
  2.  Channel composition depth to max-mixed
  3.  Eigenvalue precision gap for eigvalsh
  4.  Fidelity-near-1 vs trace distance noise floor
  5.  Entanglement near threshold (Werner concurrence)
  6.  Berry phase small solid-angle loops
  7.  QFI low-signal breakdown
  8.  Kraus operator count vs numerical rank detection
  9.  Partial trace dimension scaling
  10. Relative entropy asymmetry ratio
  11. Concurrence vs negativity disagreement (2x2)
  12. MI additivity / strong subadditivity (3-qubit)
  13. Channel fixed-point uniqueness
  14. Tomography sample complexity (1/sqrt(N) scaling)
  15. Compression loss vs entanglement correlation
"""

import json
import os
import sys
import time
import warnings
from datetime import datetime, timezone

import numpy as np
from scipy.linalg import sqrtm, logm, expm, eigvalsh
classification = "classical_baseline"  # auto-backfill

warnings.filterwarnings("ignore", category=RuntimeWarning)

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "a2_state", "sim_results")
OUT_FILE = os.path.join(OUT_DIR, "negative_mega_boundaries_results.json")

np.random.seed(42)

# ═══════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════

def random_density(d):
    """Random density matrix of dimension d via Ginibre ensemble."""
    G = (np.random.randn(d, d) + 1j * np.random.randn(d, d)) / np.sqrt(2 * d)
    rho = G @ G.conj().T
    return rho / np.trace(rho)


def partial_trace_B(rho, dA, dB):
    """Trace out subsystem B from a dA*dB dimensional state."""
    rho_r = rho.reshape(dA, dB, dA, dB)
    return np.trace(rho_r, axis1=1, axis2=3)


def partial_trace_A(rho, dA, dB):
    """Trace out subsystem A from a dA*dB dimensional state."""
    rho_r = rho.reshape(dA, dB, dA, dB)
    return np.trace(rho_r, axis1=0, axis2=2)


def von_neumann_entropy(rho):
    """von Neumann entropy S(rho) = -Tr(rho log rho)."""
    evals = eigvalsh(rho)
    evals = evals[evals > 1e-15]
    return -np.sum(evals * np.log2(evals))


def trace_distance(rho, sigma):
    """Trace distance 0.5 * Tr|rho - sigma|."""
    diff = rho - sigma
    evals = eigvalsh(diff @ diff.conj().T)
    evals = np.abs(evals)
    return 0.5 * np.sum(np.sqrt(np.maximum(evals, 0)))


def fidelity(rho, sigma):
    """Quantum fidelity F(rho, sigma)."""
    sq = sqrtm(rho)
    inner = sq @ sigma @ sq
    evals = eigvalsh(inner)
    evals = np.maximum(evals.real, 0)
    return (np.sum(np.sqrt(evals))) ** 2


def werner_state(p, d=2):
    """Werner state rho_W(p) for two qubits."""
    dim = d * d
    I = np.eye(dim)
    psi_bell = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
    proj_bell = np.outer(psi_bell, psi_bell.conj())
    return p * proj_bell + (1 - p) * I / dim


def concurrence_2qubit(rho):
    """Concurrence for a 2-qubit state."""
    sy = np.array([[0, -1j], [1j, 0]])
    sysy = np.kron(sy, sy)
    rho_tilde = sysy @ rho.conj() @ sysy
    product = rho @ rho_tilde
    evals = np.sort(np.abs(np.linalg.eigvals(product)))[::-1]
    sqrt_evals = np.sqrt(np.maximum(evals.real, 0))
    return max(0.0, sqrt_evals[0] - sqrt_evals[1] - sqrt_evals[2] - sqrt_evals[3])


def negativity_2qubit(rho):
    """Negativity via partial transpose for 2 qubits."""
    rho_pt = rho.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)
    evals = eigvalsh(rho_pt)
    return max(0.0, -2.0 * np.sum(evals[evals < 0]))


def depolarizing_channel(rho, p):
    """Apply depolarizing channel: (1-p)*rho + p*I/d."""
    d = rho.shape[0]
    return (1 - p) * rho + p * np.eye(d) / d


def quantum_discord_2qubit(rho):
    """Numerical quantum discord for 2-qubit state (measurement on B)."""
    rhoA = partial_trace_B(rho, 2, 2)
    rhoB = partial_trace_A(rho, 2, 2)
    S_AB = von_neumann_entropy(rho)
    S_A = von_neumann_entropy(rhoA)
    S_B = von_neumann_entropy(rhoB)
    MI = S_A + S_B - S_AB

    # Minimise conditional entropy over projective measurements on B
    min_cond = np.inf
    for theta in np.linspace(0, np.pi, 60):
        for phi in np.linspace(0, 2 * np.pi, 60):
            # measurement basis
            v0 = np.array([np.cos(theta / 2),
                           np.exp(1j * phi) * np.sin(theta / 2)])
            v1 = np.array([-np.exp(-1j * phi) * np.sin(theta / 2),
                           np.cos(theta / 2)])
            projs = [np.outer(v0, v0.conj()), np.outer(v1, v1.conj())]
            cond_ent = 0.0
            for P in projs:
                M = np.kron(np.eye(2), P)
                post = M @ rho @ M.conj().T
                p_k = np.real(np.trace(post))
                if p_k > 1e-15:
                    rho_k = post / p_k
                    rhoA_k = partial_trace_B(rho_k, 2, 2)
                    cond_ent += p_k * von_neumann_entropy(rhoA_k)
            if cond_ent < min_cond:
                min_cond = cond_ent

    return max(0.0, MI - (S_A - min_cond))


# ═══════════════════════════════════════════════════════════════════
# THE 15 TESTS
# ═══════════════════════════════════════════════════════════════════

def test_01_purity_discord_boundary():
    """At what purity does discord become numerically undetectable?"""
    purities = np.linspace(1.0, 0.5, 50)
    results = []
    bell = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
    rho_bell = np.outer(bell, bell.conj())
    I4 = np.eye(4) / 4

    for p in purities:
        rho = p * rho_bell + (1 - p) * I4
        purity_val = np.real(np.trace(rho @ rho))
        disc = quantum_discord_2qubit(rho)
        results.append({
            "mix_param": round(float(p), 4),
            "purity": round(float(purity_val), 8),
            "discord": float(disc),
            "detected": disc > 1e-10
        })

    first_fail = None
    for r in results:
        if not r["detected"]:
            first_fail = r["mix_param"]
            break

    return {
        "test": "purity_discord_boundary",
        "sweep": results,
        "first_undetectable_mix_param": first_fail,
        "verdict": "BOUNDARY_FOUND" if first_fail else "ALWAYS_DETECTABLE"
    }


def test_02_channel_composition_depth():
    """How many depolarizing(p=0.1) compositions to reach max mixed?"""
    rho = np.array([[1, 0], [0, 0]], dtype=complex)
    I2 = np.eye(2) / 2
    threshold = 1e-10
    max_iter = 10000

    distances = []
    for i in range(1, max_iter + 1):
        rho = depolarizing_channel(rho, 0.1)
        td = trace_distance(rho, I2)
        if i <= 200 or i % 100 == 0:
            distances.append({"step": i, "trace_distance": float(td)})
        if td < threshold:
            return {
                "test": "channel_composition_depth",
                "p": 0.1,
                "threshold": threshold,
                "converged_at_step": i,
                "samples": distances,
                "verdict": "CONVERGED"
            }

    return {
        "test": "channel_composition_depth",
        "p": 0.1,
        "threshold": threshold,
        "converged_at_step": None,
        "samples": distances,
        "verdict": "DID_NOT_CONVERGE"
    }


def test_03_eigenvalue_precision():
    """Minimum eigenvalue gap that eigvalsh can resolve reliably."""
    gaps = [10 ** (-k) for k in range(1, 17)]
    results = []
    for gap in gaps:
        M = np.diag([1.0, 1.0 + gap])
        evals = eigvalsh(M)
        measured_gap = float(evals[1] - evals[0])
        rel_err = abs(measured_gap - gap) / gap if gap > 0 else 0
        resolved = rel_err < 0.01
        results.append({
            "target_gap": gap,
            "measured_gap": measured_gap,
            "relative_error": rel_err,
            "resolved": resolved
        })

    first_fail = None
    for r in results:
        if not r["resolved"]:
            first_fail = r["target_gap"]
            break

    return {
        "test": "eigenvalue_precision",
        "sweep": results,
        "first_failure_gap": first_fail,
        "verdict": "BOUNDARY_FOUND" if first_fail else "ALL_RESOLVED"
    }


def test_04_fidelity_near_one():
    """At what fidelity does trace distance hit the noise floor?"""
    rho = np.array([[1, 0], [0, 0]], dtype=complex)
    epsilons = [10 ** (-k) for k in range(1, 13)]
    results = []

    for eps in epsilons:
        # Slightly rotated state
        c = np.cos(eps)
        s = np.sin(eps)
        psi = np.array([c, s], dtype=complex)
        sigma = np.outer(psi, psi.conj())
        F = fidelity(rho, sigma)
        td = trace_distance(rho, sigma)
        results.append({
            "epsilon": eps,
            "fidelity": float(np.real(F)),
            "trace_distance": float(td),
            "td_distinguishable": td > 1e-14
        })

    first_fail = None
    for r in results:
        if not r["td_distinguishable"]:
            first_fail = r["epsilon"]
            break

    return {
        "test": "fidelity_near_one",
        "sweep": results,
        "noise_floor_epsilon": first_fail,
        "verdict": "BOUNDARY_FOUND" if first_fail else "ALL_DISTINGUISHABLE"
    }


def test_05_entanglement_near_threshold():
    """Werner states at p=1/3 +/- epsilon. Where does concurrence detection fail?"""
    epsilons = [10 ** (-k) for k in range(1, 11)]
    results = []
    for eps in epsilons:
        p_above = 1.0 / 3.0 + eps
        p_below = 1.0 / 3.0 - eps
        rho_above = werner_state(p_above)
        rho_below = werner_state(p_below)
        C_above = concurrence_2qubit(rho_above)
        C_below = concurrence_2qubit(rho_below)
        correct = C_above > 0 and C_below == 0.0
        results.append({
            "epsilon": eps,
            "C_above": float(C_above),
            "C_below": float(C_below),
            "correctly_detected": correct
        })

    first_fail = None
    for r in results:
        if not r["correctly_detected"]:
            first_fail = r["epsilon"]
            break

    return {
        "test": "entanglement_near_threshold",
        "threshold_p": 1.0 / 3.0,
        "sweep": results,
        "detection_failure_epsilon": first_fail,
        "verdict": "BOUNDARY_FOUND" if first_fail else "ALL_CORRECT"
    }


def test_06_berry_phase_small_loop():
    """Berry phase for small solid-angle loops on Bloch sphere."""
    omegas = [0.1, 0.01, 0.001, 0.0001, 0.00001]
    results = []

    for omega in omegas:
        # Circle at colatitude theta around |0>. Solid angle = 2*pi*(1-cos(theta)).
        # Solve for theta: theta = arccos(1 - omega/(2*pi))
        arg = 1 - omega / (2 * np.pi)
        if abs(arg) > 1:
            results.append({"omega": omega, "skipped": True})
            continue
        theta = np.arccos(arg)
        # Berry phase = -omega/2 (for spin-1/2)
        theory_phase = -omega / 2.0

        # Numerical: transport |psi(phi)> around the loop
        N_steps = 2000
        phis = np.linspace(0, 2 * np.pi, N_steps + 1)
        phase_accum = 0.0 + 0j
        psi_prev = np.array([np.cos(theta / 2), np.sin(theta / 2)], dtype=complex)

        for i in range(1, len(phis)):
            phi = phis[i]
            psi_cur = np.array([np.cos(theta / 2),
                                np.exp(1j * phi) * np.sin(theta / 2)],
                               dtype=complex)
            overlap = np.dot(psi_prev.conj(), psi_cur)
            phase_accum += np.log(overlap / abs(overlap)) if abs(overlap) > 1e-15 else 0
            psi_prev = psi_cur

        # Total geometric phase
        final_overlap = np.dot(
            np.array([np.cos(theta / 2), np.sin(theta / 2)], dtype=complex).conj(),
            psi_prev
        )
        berry_numerical = float(np.imag(phase_accum))
        error = abs(berry_numerical - theory_phase)

        results.append({
            "omega": omega,
            "theory_phase": theory_phase,
            "numerical_phase": berry_numerical,
            "abs_error": error,
            "detectable": abs(berry_numerical) > 1e-14
        })

    first_fail = None
    for r in results:
        if "skipped" not in r and not r["detectable"]:
            first_fail = r["omega"]
            break

    return {
        "test": "berry_phase_small_loop",
        "sweep": results,
        "noise_floor_omega": first_fail,
        "verdict": "BOUNDARY_FOUND" if first_fail else "ALL_DETECTABLE"
    }


def test_07_qfi_low_signal():
    """QFI for rotation angle theta. At what theta does computation fail?"""
    thetas = [10 ** (-k) for k in range(1, 11)]
    results = []

    # Generator: sigma_z for single qubit
    sz = np.array([[1, 0], [0, -1]], dtype=complex)
    psi0 = np.array([1, 1], dtype=complex) / np.sqrt(2)  # |+> state

    for theta in thetas:
        # Evolved state
        U = expm(-1j * theta / 2 * sz)
        psi = U @ psi0
        rho = np.outer(psi, psi.conj())

        # QFI = 4 * Var(H) for pure states
        H_exp = np.real(psi.conj() @ sz @ psi)
        H2_exp = np.real(psi.conj() @ sz @ sz @ psi)
        qfi = 4 * (H2_exp - H_exp ** 2)

        # Theory: QFI = 4 for |+> rotated by sigma_z (constant)
        rel_err = abs(qfi - 4.0) / 4.0

        results.append({
            "theta": theta,
            "qfi": float(qfi),
            "theory_qfi": 4.0,
            "relative_error": float(rel_err),
            "reliable": rel_err < 0.01
        })

    first_fail = None
    for r in results:
        if not r["reliable"]:
            first_fail = r["theta"]
            break

    return {
        "test": "qfi_low_signal",
        "sweep": results,
        "failure_theta": first_fail,
        "verdict": "BOUNDARY_FOUND" if first_fail else "ALL_RELIABLE"
    }


def test_08_kraus_operator_count():
    """Random channel with 1..32 Kraus operators. When does rank detection fail?"""
    d = 4  # 2-qubit system
    counts = [1, 2, 4, 8, 16, 32]
    results = []

    for K in counts:
        # Generate random Kraus operators
        kraus_ops = []
        for _ in range(K):
            M = (np.random.randn(d, d) + 1j * np.random.randn(d, d)) / np.sqrt(2 * K * d)
            kraus_ops.append(M)

        # Normalise to valid CPTP
        S = sum(M.conj().T @ M for M in kraus_ops)
        S_inv_sqrt = np.linalg.inv(sqrtm(S))
        kraus_ops = [M @ S_inv_sqrt for M in kraus_ops]

        # Build Choi matrix
        choi = np.zeros((d * d, d * d), dtype=complex)
        for M in kraus_ops:
            vec = M.flatten(order='F')
            choi += np.outer(vec, vec.conj())
        choi /= d

        # Detect rank from Choi
        evals = eigvalsh(choi)
        detected_rank = int(np.sum(evals > 1e-10))
        correct = detected_rank == K

        results.append({
            "num_kraus": K,
            "detected_rank": detected_rank,
            "correct": correct,
            "choi_eigenvalues_top5": sorted(evals.tolist(), reverse=True)[:5]
        })

    first_fail = None
    for r in results:
        if not r["correct"]:
            first_fail = r["num_kraus"]
            break

    return {
        "test": "kraus_operator_count",
        "dimension": d,
        "sweep": results,
        "first_failure_K": first_fail,
        "verdict": "BOUNDARY_FOUND" if first_fail else "ALL_CORRECT"
    }


def test_09_partial_trace_dimension():
    """Partial trace on d x d system. Timing and correctness at growing d."""
    dims = [2, 4, 8, 16, 32, 64]
    results = []

    for d in dims:
        rho = random_density(d * d)
        t0 = time.perf_counter()
        rhoA = partial_trace_B(rho, d, d)
        dt = time.perf_counter() - t0

        # Check valid density matrix
        tr = np.real(np.trace(rhoA))
        evals = eigvalsh(rhoA)
        min_eval = float(np.min(evals))
        valid = abs(tr - 1.0) < 1e-8 and min_eval > -1e-8

        results.append({
            "d": d,
            "joint_dim": d * d,
            "time_sec": round(dt, 6),
            "trace": round(float(tr), 10),
            "min_eigenvalue": min_eval,
            "valid": valid
        })

    return {
        "test": "partial_trace_dimension",
        "sweep": results,
        "verdict": "SCALING_DOCUMENTED"
    }


def test_10_relative_entropy_asymmetry():
    """D(rho||sigma) vs D(sigma||rho) asymmetry as states approach each other."""
    results = []
    rho = random_density(4)

    for k in range(1, 11):
        eps = 10 ** (-k)
        # Perturb
        delta = (np.random.randn(4, 4) + 1j * np.random.randn(4, 4)) * eps
        delta = delta + delta.conj().T
        sigma = rho + delta
        # Re-normalise to valid density
        evals, evecs = np.linalg.eigh(sigma)
        evals = np.maximum(evals, 1e-15)
        sigma = evecs @ np.diag(evals) @ evecs.conj().T
        sigma /= np.trace(sigma)

        # Relative entropy D(rho||sigma) = Tr[rho(log rho - log sigma)]
        try:
            log_rho = logm(rho)
            log_sigma = logm(sigma)
            D_rs = np.real(np.trace(rho @ (log_rho - log_sigma)))
            D_sr = np.real(np.trace(sigma @ (log_sigma - log_rho)))
            ratio = abs(D_rs / D_sr) if abs(D_sr) > 1e-20 else float('inf')
        except Exception:
            D_rs = D_sr = ratio = float('nan')

        results.append({
            "epsilon": eps,
            "D_rho_sigma": float(D_rs),
            "D_sigma_rho": float(D_sr),
            "asymmetry_ratio": float(ratio)
        })

    return {
        "test": "relative_entropy_asymmetry",
        "sweep": results,
        "verdict": "ASYMMETRY_DOCUMENTED"
    }


def test_11_concurrence_negativity_disagreement():
    """Search for 2-qubit states where C>0 but N=0 or vice versa (should not exist)."""
    N_samples = 500
    disagreements = []

    for i in range(N_samples):
        rho = random_density(4)
        C = concurrence_2qubit(rho)
        N = negativity_2qubit(rho)
        if (C > 1e-8 and N < 1e-10) or (N > 1e-8 and C < 1e-10):
            disagreements.append({
                "sample": i,
                "concurrence": float(C),
                "negativity": float(N)
            })

    return {
        "test": "concurrence_negativity_disagreement",
        "num_samples": N_samples,
        "num_disagreements": len(disagreements),
        "disagreements": disagreements[:10],
        "verdict": "CONSISTENT" if len(disagreements) == 0 else "DISAGREEMENT_FOUND"
    }


def test_12_mi_strong_subadditivity():
    """Verify strong subadditivity: S(AB)+S(BC) >= S(ABC)+S(B) at 100 random 3-qubit states."""
    N_samples = 100
    violations = []

    for i in range(N_samples):
        rho_ABC = random_density(8)
        rho_AB = partial_trace_B(rho_ABC, 4, 2)   # trace out C (d=2)
        rho_BC = partial_trace_A(rho_ABC, 2, 4)    # trace out A (d=2)
        rho_B_from_AB = partial_trace_A(rho_AB, 2, 2)  # trace out A from AB

        S_ABC = von_neumann_entropy(rho_ABC)
        S_AB = von_neumann_entropy(rho_AB)
        S_BC = von_neumann_entropy(rho_BC)
        S_B = von_neumann_entropy(rho_B_from_AB)

        # Strong subadditivity: S(AB) + S(BC) >= S(ABC) + S(B)
        lhs = S_AB + S_BC
        rhs = S_ABC + S_B
        gap = lhs - rhs

        if gap < -1e-8:
            violations.append({
                "sample": i,
                "S_AB": float(S_AB),
                "S_BC": float(S_BC),
                "S_ABC": float(S_ABC),
                "S_B": float(S_B),
                "gap": float(gap)
            })

    return {
        "test": "mi_strong_subadditivity",
        "num_samples": N_samples,
        "num_violations": len(violations),
        "violations": violations[:10],
        "verdict": "SSA_HOLDS" if len(violations) == 0 else "SSA_VIOLATED"
    }


def test_13_channel_fixed_point_uniqueness():
    """Random CPTP, iterate from 10 initial states. Do they converge to the same fixed point?"""
    d = 4
    # Build random CPTP with 4 Kraus operators
    K = 4
    kraus_ops = []
    for _ in range(K):
        M = (np.random.randn(d, d) + 1j * np.random.randn(d, d)) / np.sqrt(2 * K * d)
        kraus_ops.append(M)
    S = sum(M.conj().T @ M for M in kraus_ops)
    S_inv_sqrt = np.linalg.inv(sqrtm(S))
    kraus_ops = [M @ S_inv_sqrt for M in kraus_ops]

    def apply_channel(rho):
        return sum(M @ rho @ M.conj().T for M in kraus_ops)

    fixed_points = []
    for trial in range(10):
        rho = random_density(d)
        for _ in range(1000):
            rho = apply_channel(rho)
            # re-normalise for stability
            rho /= np.trace(rho)
        fixed_points.append(rho)

    # Check pairwise trace distances
    max_td = 0.0
    for i in range(len(fixed_points)):
        for j in range(i + 1, len(fixed_points)):
            td = trace_distance(fixed_points[i], fixed_points[j])
            max_td = max(max_td, td)

    return {
        "test": "channel_fixed_point_uniqueness",
        "num_kraus": K,
        "num_trials": 10,
        "iterations": 1000,
        "max_pairwise_trace_distance": float(max_td),
        "unique": max_td < 1e-6,
        "verdict": "UNIQUE_FIXED_POINT" if max_td < 1e-6 else "MULTIPLE_FIXED_POINTS"
    }


def test_14_tomography_sample_complexity():
    """Reconstruction fidelity vs N measurements. Check 1/sqrt(N) scaling."""
    d = 2
    # True state: random pure state
    psi = np.random.randn(d) + 1j * np.random.randn(d)
    psi /= np.linalg.norm(psi)
    rho_true = np.outer(psi, psi.conj())

    # Measurement bases: X, Y, Z
    bases = [
        np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2),  # X
        np.array([[1, 1j], [1, -1j]], dtype=complex) / np.sqrt(2),  # Y
        np.eye(2, dtype=complex),  # Z
    ]

    sample_sizes = [10, 50, 100, 500, 1000, 5000]
    results = []

    for N in sample_sizes:
        # Simulate measurements
        freq_data = {}
        N_per_basis = N // 3
        for b_idx, U in enumerate(bases):
            for outcome in range(d):
                proj = np.outer(U[:, outcome], U[:, outcome].conj())
                prob = max(0.0, np.real(np.trace(proj @ rho_true)))
                counts = np.random.binomial(N_per_basis, prob)
                freq_data[(b_idx, outcome)] = counts / N_per_basis if N_per_basis > 0 else 0

        # Linear inversion tomography
        rho_est = np.zeros((d, d), dtype=complex)
        for b_idx, U in enumerate(bases):
            for outcome in range(d):
                proj = np.outer(U[:, outcome], U[:, outcome].conj())
                f = freq_data.get((b_idx, outcome), 0)
                rho_est += f * proj
        rho_est /= len(bases)

        # Force valid density matrix
        evals, evecs = np.linalg.eigh(rho_est)
        evals = np.maximum(evals, 0)
        rho_est = evecs @ np.diag(evals) @ evecs.conj().T
        rho_est /= np.trace(rho_est)

        F = fidelity(rho_est, rho_true)
        infidelity = 1.0 - np.real(F)

        results.append({
            "N_measurements": N,
            "fidelity": float(np.real(F)),
            "infidelity": float(max(0, infidelity)),
            "sqrt_N": float(np.sqrt(N))
        })

    # Fit log(infidelity) ~ -0.5 * log(N) + const
    valid = [(r["N_measurements"], r["infidelity"]) for r in results if r["infidelity"] > 1e-15]
    if len(valid) >= 3:
        log_N = np.log([v[0] for v in valid])
        log_inf = np.log([v[1] for v in valid])
        slope, intercept = np.polyfit(log_N, log_inf, 1)
    else:
        slope = float('nan')

    return {
        "test": "tomography_sample_complexity",
        "sweep": results,
        "fitted_slope": float(slope),
        "expected_slope": -0.5,
        "scaling_consistent": abs(slope - (-0.5)) < 0.3 if not np.isnan(slope) else False,
        "verdict": "SCALING_VERIFIED" if (not np.isnan(slope) and abs(slope + 0.5) < 0.3) else "SCALING_ANOMALOUS"
    }


def test_15_compression_vs_entanglement():
    """Rank-1 compression loss vs initial concurrence for 100 random 2-qubit states."""
    N_samples = 100
    data = []

    for _ in range(N_samples):
        rho = random_density(4)
        C_orig = concurrence_2qubit(rho)

        # Compress to rank 1: keep largest eigenvector
        evals, evecs = np.linalg.eigh(rho)
        idx = np.argmax(evals)
        psi = evecs[:, idx]
        rho_compressed = np.outer(psi, psi.conj())

        C_compressed = concurrence_2qubit(rho_compressed)
        loss = abs(C_orig - C_compressed)

        data.append({
            "C_original": float(C_orig),
            "C_compressed": float(C_compressed),
            "C_loss": float(loss)
        })

    # Correlation between C_original and C_loss
    C_orig_arr = np.array([d["C_original"] for d in data])
    C_loss_arr = np.array([d["C_loss"] for d in data])
    if np.std(C_orig_arr) > 1e-10 and np.std(C_loss_arr) > 1e-10:
        correlation = float(np.corrcoef(C_orig_arr, C_loss_arr)[0, 1])
    else:
        correlation = 0.0

    return {
        "test": "compression_vs_entanglement",
        "num_samples": N_samples,
        "correlation_C_orig_vs_loss": correlation,
        "mean_C_original": float(np.mean(C_orig_arr)),
        "mean_C_loss": float(np.mean(C_loss_arr)),
        "verdict": "CORRELATED" if abs(correlation) > 0.3 else "UNCORRELATED"
    }


# ═══════════════════════════════════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════════════════════════════════

ALL_TESTS = [
    ("01_purity_discord_boundary", test_01_purity_discord_boundary),
    ("02_channel_composition_depth", test_02_channel_composition_depth),
    ("03_eigenvalue_precision", test_03_eigenvalue_precision),
    ("04_fidelity_near_one", test_04_fidelity_near_one),
    ("05_entanglement_near_threshold", test_05_entanglement_near_threshold),
    ("06_berry_phase_small_loop", test_06_berry_phase_small_loop),
    ("07_qfi_low_signal", test_07_qfi_low_signal),
    ("08_kraus_operator_count", test_08_kraus_operator_count),
    ("09_partial_trace_dimension", test_09_partial_trace_dimension),
    ("10_relative_entropy_asymmetry", test_10_relative_entropy_asymmetry),
    ("11_concurrence_negativity_disagreement", test_11_concurrence_negativity_disagreement),
    ("12_mi_strong_subadditivity", test_12_mi_strong_subadditivity),
    ("13_channel_fixed_point_uniqueness", test_13_channel_fixed_point_uniqueness),
    ("14_tomography_sample_complexity", test_14_tomography_sample_complexity),
    ("15_compression_vs_entanglement", test_15_compression_vs_entanglement),
]


def main():
    print(f"NEGATIVE MEGA BOUNDARY PROBE — {len(ALL_TESTS)} tests")
    print("=" * 60)

    tests = {}
    t_total = time.perf_counter()

    for test_name, test_func in ALL_TESTS:
        print(f"  Running {test_name} ...", end=" ", flush=True)
        t0 = time.perf_counter()
        try:
            result = test_func()
            dt = time.perf_counter() - t0
            result["runtime_sec"] = round(dt, 3)
            tests[test_name] = result
            print(f"{result['verdict']}  ({dt:.1f}s)")
        except Exception as e:
            dt = time.perf_counter() - t0
            tests[test_name] = {
                "test": test_name,
                "verdict": "ERROR",
                "error": str(e),
                "runtime_sec": round(dt, 3)
            }
            print(f"ERROR: {e}")

    total_time = time.perf_counter() - t_total
    verdicts = {k: v["verdict"] for k, v in tests.items()}
    num_errors = sum(1 for v in verdicts.values() if v == "ERROR")

    envelope = {
        "probe": "negative_mega_boundaries",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_tests": len(ALL_TESTS),
        "num_errors": num_errors,
        "total_runtime_sec": round(total_time, 2),
        "verdict_summary": verdicts,
        "tests": tests
    }

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_FILE, "w") as f:
        json.dump(envelope, f, indent=2, default=str)

    print("=" * 60)
    print(f"Done in {total_time:.1f}s — {num_errors} errors")
    print(f"Results → {OUT_FILE}")
    return 0 if num_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
