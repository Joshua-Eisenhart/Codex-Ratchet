#!/usr/bin/env python3
"""
Negative Geometry Battery
=========================
Tests where quantum-geometric quantities BREAK, degenerate, or give wrong
answers due to numerical noise, domain violations, or topological edge cases.

10 probes, no engine dependency.  numpy / scipy / clifford only.

Output: a2_state/sim_results/negative_geometry_results.json
"""

import sys, os, json
import numpy as np
from scipy.linalg import sqrtm, expm
from clifford import Cl

# ═══════════════════════════════════════════════════════════════════
# SETUP
# ═══════════════════════════════════════════════════════════════════

np.random.seed(42)
RESULTS = {}

layout, blades = Cl(3)
e1, e2, e3 = blades['e1'], blades['e2'], blades['e3']
e12, e13, e23 = blades['e12'], blades['e13'], blades['e23']
e123 = blades['e123']


def sanitize(obj):
    """Recursively convert numpy types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return sanitize(obj.tolist())
    if isinstance(obj, complex):
        return {"re": float(obj.real), "im": float(obj.imag)}
    if isinstance(obj, (np.complexfloating,)):
        return {"re": float(np.real(obj)), "im": float(np.imag(obj))}
    if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return str(obj)
    return obj


# ═══════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════

def random_pure_state(d=2):
    """Random normalised ket in C^d."""
    psi = np.random.randn(d) + 1j * np.random.randn(d)
    return psi / np.linalg.norm(psi)


def ket_to_dm(psi):
    return np.outer(psi, psi.conj())


def fubini_study(psi, phi):
    """Fubini-Study distance between two pure state vectors."""
    overlap = np.abs(np.vdot(psi, phi))
    overlap = np.clip(overlap, 0.0, 1.0)
    return np.arccos(overlap)


def bures_distance(rho, sigma):
    """Bures distance between two density matrices."""
    sqrt_rho = sqrtm(rho)
    inner = sqrtm(sqrt_rho @ sigma @ sqrt_rho)
    fid = np.real(np.trace(inner)) ** 2
    return np.sqrt(np.clip(2.0 * (1.0 - np.sqrt(np.clip(fid, 0, 1))), 0, None))


def fidelity(rho, sigma):
    """Quantum fidelity F(rho, sigma)."""
    sqrt_rho = sqrtm(rho)
    inner = sqrtm(sqrt_rho @ sigma @ sqrt_rho)
    return np.real(np.trace(inner)) ** 2


def trace_distance(rho, sigma):
    """Trace distance 0.5 * Tr|rho - sigma|."""
    diff = rho - sigma
    eigvals = np.linalg.eigvalsh(diff)
    return 0.5 * np.sum(np.abs(eigvals))


def qfi_sld(rho, H):
    """Quantum Fisher Information via SLD for generator H.
    F_Q = 2 sum_{i,j} |<i|H|j>|^2 / (lambda_i + lambda_j)
    where sum is over pairs with lambda_i + lambda_j > 0.
    """
    eigvals, eigvecs = np.linalg.eigh(rho)
    d = len(eigvals)
    H_eig = eigvecs.conj().T @ H @ eigvecs
    qfi = 0.0
    for i in range(d):
        for j in range(d):
            denom = eigvals[i] + eigvals[j]
            if denom > 1e-14:
                qfi += 2.0 * np.abs(H_eig[i, j]) ** 2 / denom
    return np.real(qfi)


def berry_phase_discrete(states):
    """Discrete Berry phase from a sequence of states.
    gamma = -arg( prod <psi_k | psi_{k+1}> )
    """
    prod = 1.0 + 0j
    for k in range(len(states) - 1):
        prod *= np.vdot(states[k], states[k + 1])
    return -np.angle(prod)


# ═══════════════════════════════════════════════════════════════════
# TEST 1: Fubini-Study between identical states
# ═══════════════════════════════════════════════════════════════════

def test_01_fs_identical():
    """FS distance between identical states should be exactly 0.
    Check numerical noise level.  The key finding is HOW MUCH noise
    arccos introduces near the boundary."""
    psi = random_pure_state(4)
    d = fubini_study(psi, psi)
    # Also test with phase-rotated copy (should still be 0)
    phi = psi * np.exp(1j * 0.73)
    d_phase = fubini_study(psi, phi)

    # The noise floor tells us the practical resolution limit of FS
    noise_floor = max(d, d_phase)
    return {
        "test": "FS_identical_states",
        "distance_same": float(d),
        "distance_phase_rotated": float(d_phase),
        "noise_floor": float(noise_floor),
        "expected": 0.0,
        "below_1e7": bool(noise_floor < 1e-7),
        "pass": bool(noise_floor < 1e-7),
        "note": "Noise floor from arccos near boundary; exact 0 not guaranteed by float64"
    }


# ═══════════════════════════════════════════════════════════════════
# TEST 2: Fubini-Study for MIXED states (domain violation)
# ═══════════════════════════════════════════════════════════════════

def test_02_fs_mixed():
    """FS is only defined for pure states.  Feed it mixed density matrices
    and observe what happens when naively applied."""
    psi1 = random_pure_state(2)
    psi2 = random_pure_state(2)
    # Maximally mixed
    rho_mixed = np.eye(2) / 2.0
    # Partially mixed
    rho_partial = 0.7 * ket_to_dm(psi1) + 0.3 * ket_to_dm(psi2)

    # Extract dominant eigenvector and try FS
    def dm_to_dominant_ket(rho):
        eigvals, eigvecs = np.linalg.eigh(rho)
        return eigvecs[:, -1]

    ket_mixed = dm_to_dominant_ket(rho_mixed)
    ket_partial = dm_to_dominant_ket(rho_partial)

    # FS on the eigenvectors (the naive approach)
    d_mixed_pure = fubini_study(psi1, ket_mixed)
    d_partial_pure = fubini_study(psi1, ket_partial)

    # Check: does FS on maximally mixed dominant eigvec give a meaningful
    # result? For maximally mixed, ALL eigenvectors are degenerate so the
    # choice is arbitrary.
    evals_mixed = np.linalg.eigvalsh(rho_mixed)
    degeneracy = float(np.max(evals_mixed) - np.min(evals_mixed))

    return {
        "test": "FS_mixed_state_domain_violation",
        "fs_to_max_mixed_dominant_eigvec": float(d_mixed_pure),
        "fs_to_partial_mixed_dominant_eigvec": float(d_partial_pure),
        "max_mixed_eigenvalue_spread": degeneracy,
        "max_mixed_eigvec_arbitrary": bool(degeneracy < 1e-12),
        "pass": True,  # This is a diagnostic, not a pass/fail
        "note": "FS on mixed states is undefined; dominant eigenvector is arbitrary when degenerate"
    }


# ═══════════════════════════════════════════════════════════════════
# TEST 3: Bures distance for rank-0 / singular states
# ═══════════════════════════════════════════════════════════════════

def test_03_bures_singular():
    """sqrtm on a zero matrix or near-singular matrix.  Does it crash or
    give nonsense?"""
    results = {}

    # Rank 0 (zero matrix)
    rho_zero = np.zeros((2, 2), dtype=complex)
    rho_pure = ket_to_dm(random_pure_state(2))
    try:
        d = bures_distance(rho_zero, rho_pure)
        results["rank0_bures"] = float(np.real(d))
        results["rank0_error"] = None
    except Exception as e:
        results["rank0_bures"] = None
        results["rank0_error"] = str(e)

    # Near-singular (eigenvalue ~ 1e-300)
    rho_near = np.diag([1.0 - 1e-300, 1e-300]).astype(complex)
    try:
        d = bures_distance(rho_near, rho_pure)
        results["near_singular_bures"] = float(np.real(d))
        results["near_singular_error"] = None
    except Exception as e:
        results["near_singular_bures"] = None
        results["near_singular_error"] = str(e)

    # Negative eigenvalue (unphysical)
    rho_neg = np.diag([1.5, -0.5]).astype(complex)
    try:
        d = bures_distance(rho_neg, rho_pure)
        results["negative_eigval_bures"] = float(np.real(d))
        results["negative_eigval_error"] = None
        results["negative_eigval_is_real"] = bool(np.isreal(d))
    except Exception as e:
        results["negative_eigval_bures"] = None
        results["negative_eigval_error"] = str(e)

    results["test"] = "Bures_singular_states"
    results["pass"] = True  # diagnostic
    results["note"] = "sqrtm on zero/near-singular/unphysical matrices"
    return results


# ═══════════════════════════════════════════════════════════════════
# TEST 4: Berry phase for open path (gauge non-invariance)
# ═══════════════════════════════════════════════════════════════════

def test_04_berry_open_path():
    """Berry phase on an open path is NOT gauge-invariant.
    Apply random gauge rotations and verify the phase changes."""
    N = 50
    thetas = np.linspace(0, np.pi / 2, N)  # open: 0 to pi/2 only
    states = [np.array([np.cos(t / 2), np.sin(t / 2) * np.exp(1j * t)])
              for t in thetas]

    # Gauge 1: original
    gamma1 = berry_phase_discrete(states)

    # Gauge 2: multiply each state by a random phase
    phases = np.exp(1j * np.random.uniform(0, 2 * np.pi, N))
    states_g2 = [s * p for s, p in zip(states, phases)]
    gamma2 = berry_phase_discrete(states_g2)

    # Gauge 3: linear ramp phase
    phases_ramp = np.exp(1j * np.linspace(0, 3.0, N))
    states_g3 = [s * p for s, p in zip(states, phases_ramp)]
    gamma3 = berry_phase_discrete(states_g3)

    gauge_invariant = bool(
        np.abs(gamma1 - gamma2) < 1e-10 and np.abs(gamma1 - gamma3) < 1e-10
    )

    return {
        "test": "Berry_phase_open_path_gauge_dependence",
        "gamma_gauge1": float(gamma1),
        "gamma_gauge2": float(gamma2),
        "gamma_gauge3": float(gamma3),
        "spread": float(max(gamma1, gamma2, gamma3) - min(gamma1, gamma2, gamma3)),
        "gauge_invariant": gauge_invariant,
        "pass": not gauge_invariant,
        "note": "SHOULD fail gauge invariance -- open path Berry phase is gauge-dependent"
    }


# ═══════════════════════════════════════════════════════════════════
# TEST 5: QFI at maximally mixed state
# ═══════════════════════════════════════════════════════════════════

def test_05_qfi_max_mixed():
    """QFI for the maximally mixed state under unitary evolution.
    Key physics: rho_mm = I/d is invariant under ANY unitary, so
    d rho / d theta = -i[H, I/d] = 0.  The QFI computed from the
    actual state derivative is therefore 0.

    But the naive SLD formula QFI = 2 sum |H_ij|^2/(lambda_i+lambda_j)
    gives d * Tr(H^2) != 0 because it measures the GENERATOR's norm,
    not the state's sensitivity.  This is the trap.

    We verify BOTH: (a) SLD formula gives nonzero (trap),
    (b) finite-difference QFI on the actual evolved state gives 0."""
    d = 4
    rho = np.eye(d, dtype=complex) / d

    generators = {
        "sigma_z_x_I": np.kron(np.diag([1, -1]), np.eye(2)),
    }
    A = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    generators["random_hermitian"] = (A + A.conj().T) / 2.0

    results_map = {}
    for name, H in generators.items():
        # (a) Naive SLD -- will be nonzero (the trap)
        q_sld = qfi_sld(rho, H)

        # (b) Finite-difference: evolve rho, measure actual distinguishability
        dt = 1e-6
        U = expm(-1j * H * dt)
        rho_evolved = U @ rho @ U.conj().T
        # QFI ~ 8(1 - sqrt(F(rho, rho_evolved))) / dt^2
        f = fidelity(rho, rho_evolved)
        qfi_fd = 8.0 * (1.0 - np.sqrt(np.clip(np.real(f), 0, 1))) / dt**2

        # Ratio: if true QFI were real, fd would scale with sld
        ratio = qfi_fd / q_sld if q_sld > 0 else 0.0
        results_map[name] = {
            "qfi_sld_naive": float(q_sld),
            "qfi_sld_nonzero_TRAP": bool(q_sld > 1e-6),
            "qfi_finite_diff": float(qfi_fd),
            "qfi_fd_ratio_to_sld": float(ratio),
            "qfi_fd_negligible": bool(ratio < 1e-3),
        }

    fd_negligible = all(v["qfi_fd_negligible"] for v in results_map.values())
    sld_all_nonzero = all(v["qfi_sld_nonzero_TRAP"] for v in results_map.values())
    return {
        "test": "QFI_maximally_mixed",
        "generators": results_map,
        "sld_trap_triggered": sld_all_nonzero,
        "fd_negligible_vs_sld": fd_negligible,
        "pass": bool(fd_negligible and sld_all_nonzero),
        "note": "SLD formula gives nonzero (trap); finite-diff shows true QFI is negligible (sqrtm noise floor)"
    }


# ═══════════════════════════════════════════════════════════════════
# TEST 6: Trace distance at machine epsilon
# ═══════════════════════════════════════════════════════════════════

def test_06_trace_distance_epsilon():
    """Two states differing by ~1e-16.  Can we distinguish them?"""
    psi = random_pure_state(4)
    rho = ket_to_dm(psi)

    epsilons = [1e-16, 1e-15, 1e-14, 1e-12, 1e-10, 1e-8]
    results_list = []
    for eps in epsilons:
        # Perturb one diagonal element
        sigma = rho.copy()
        sigma[0, 0] += eps
        sigma[1, 1] -= eps  # keep trace = 1
        td = trace_distance(rho, sigma)
        results_list.append({
            "epsilon": eps,
            "trace_distance": float(td),
            "distinguishable": bool(td > eps * 0.1),
            "ratio_td_over_eps": float(td / eps) if eps > 0 else 0,
        })

    # Find the threshold where trace distance drops below noise
    threshold = None
    for r in results_list:
        if r["trace_distance"] < 1e-15:
            threshold = r["epsilon"]
            break

    return {
        "test": "trace_distance_machine_epsilon",
        "probes": results_list,
        "indistinguishability_threshold": threshold,
        "pass": True,  # diagnostic
        "note": "Probing the floor where numerical noise drowns the signal"
    }


# ═══════════════════════════════════════════════════════════════════
# TEST 7: Fidelity > 1 from numerical error
# ═══════════════════════════════════════════════════════════════════

def test_07_fidelity_overflow():
    """Can fidelity exceed 1.0 due to sqrtm numerical error?
    Test with near-identical states and ill-conditioned states."""
    violations = []

    # Test 1: near-identical pure states
    for trial in range(100):
        psi = random_pure_state(4)
        rho = ket_to_dm(psi)
        sigma = rho + np.random.randn(4, 4) * 1e-15
        sigma = (sigma + sigma.conj().T) / 2
        sigma /= np.trace(sigma)
        f = fidelity(rho, sigma)
        if f > 1.0 + 1e-15:
            violations.append({"trial": trial, "fidelity": float(np.real(f)),
                               "excess": float(np.real(f) - 1.0)})

    # Test 2: ill-conditioned states (eigenvalue ratio > 1e12)
    for trial in range(50):
        eigs = np.array([1.0 - 1e-14, 1e-14, 0, 0])
        eigs = eigs / eigs.sum()
        U = np.linalg.qr(np.random.randn(4, 4) + 1j * np.random.randn(4, 4))[0]
        rho = U @ np.diag(eigs) @ U.conj().T
        sigma = rho + np.random.randn(4, 4) * 1e-14
        sigma = (sigma + sigma.conj().T) / 2
        sigma /= np.trace(sigma)
        f = fidelity(rho, sigma)
        if f > 1.0 + 1e-15:
            violations.append({"trial": f"ill_{trial}", "fidelity": float(np.real(f)),
                               "excess": float(np.real(f) - 1.0)})

    return {
        "test": "fidelity_exceeds_one",
        "num_violations": len(violations),
        "violations_sample": violations[:10],
        "pass": True,  # diagnostic
        "note": "Cataloguing conditions where sqrtm pushes fidelity past 1.0"
    }


# ═══════════════════════════════════════════════════════════════════
# TEST 8: Cl(3) rotor at 0, 2pi, 4pi
# ═══════════════════════════════════════════════════════════════════

def test_08_cl3_rotor_spinor():
    """Rotor R = exp(-theta/2 * e12):
    theta=0   -> R = +1 (identity)
    theta=2pi -> R = -1 (spinor sign flip)
    theta=4pi -> R = +1 (back to identity)
    Verify EXACT values within numerical tolerance."""
    axis_bivector = e12

    def rotor(theta):
        return np.cos(theta / 2) + np.sin(theta / 2) * (-axis_bivector)

    R0 = rotor(0)
    R2pi = rotor(2 * np.pi)
    R4pi = rotor(4 * np.pi)

    # Extract scalar parts
    def scalar_part(mv):
        return float(mv.value[0])

    def grade2_norm(mv):
        # norm of the bivector (grade-2) part via grade extraction
        g2 = mv(2)
        return float(np.sqrt(np.sum(g2.value ** 2)))

    s0 = scalar_part(R0)
    s2pi = scalar_part(R2pi)
    s4pi = scalar_part(R4pi)

    g2_0 = grade2_norm(R0)
    g2_2pi = grade2_norm(R2pi)
    g2_4pi = grade2_norm(R4pi)

    return {
        "test": "Cl3_rotor_spinor_periodicity",
        "R_0_scalar": s0,
        "R_0_bivec_norm": g2_0,
        "R_2pi_scalar": s2pi,
        "R_2pi_bivec_norm": g2_2pi,
        "R_4pi_scalar": s4pi,
        "R_4pi_bivec_norm": g2_4pi,
        "R0_is_identity": bool(abs(s0 - 1.0) < 1e-14 and g2_0 < 1e-14),
        "R2pi_is_minus_one": bool(abs(s2pi - (-1.0)) < 1e-14 and g2_2pi < 1e-14),
        "R4pi_is_plus_one": bool(abs(s4pi - 1.0) < 1e-14 and g2_4pi < 1e-14),
        "spinor_sign_flip_confirmed": bool(abs(s2pi + 1.0) < 1e-14),
        "pass": bool(
            abs(s0 - 1.0) < 1e-14 and
            abs(s2pi + 1.0) < 1e-14 and
            abs(s4pi - 1.0) < 1e-14
        ),
        "note": "Spinor double-cover: 2pi gives -1, 4pi gives +1"
    }


# ═══════════════════════════════════════════════════════════════════
# TEST 9: Berry phase on contractible loop (zero solid angle)
# ═══════════════════════════════════════════════════════════════════

def test_09_berry_contractible():
    """A loop on the Bloch sphere that encloses zero solid angle
    should give Berry phase = 0.  Walk along the equator at theta=pi/2
    with phi from 0 to 2pi (great circle = 2pi solid angle = pi Berry phase),
    then contract to a tiny loop (solid angle -> 0, Berry phase -> 0)."""

    def bloch_state(theta, phi):
        return np.array([np.cos(theta / 2),
                         np.sin(theta / 2) * np.exp(1j * phi)])

    N = 200

    # Great circle (equator): solid angle = 2pi, Berry phase = pi
    thetas_eq = np.full(N, np.pi / 2)
    phis_eq = np.linspace(0, 2 * np.pi, N, endpoint=True)  # closed
    states_eq = [bloch_state(t, p) for t, p in zip(thetas_eq, phis_eq)]
    gamma_equator = berry_phase_discrete(states_eq)

    # Contractible loop: tiny circle around north pole
    delta = 0.001  # very small polar cap
    phis_tiny = np.linspace(0, 2 * np.pi, N, endpoint=True)
    states_tiny = [bloch_state(delta, p) for p in phis_tiny]
    gamma_tiny = berry_phase_discrete(states_tiny)

    # Solid angle of small cap: Omega = 2pi(1 - cos(delta))
    omega_tiny = 2 * np.pi * (1 - np.cos(delta))
    expected_berry_tiny = -omega_tiny / 2.0

    # Degenerate loop: stay at ONE point (zero area trivially)
    states_point = [bloch_state(0.3, 0.7)] * N
    gamma_point = berry_phase_discrete(states_point)

    return {
        "test": "Berry_phase_contractible_loop",
        "equator_berry_phase": float(gamma_equator),
        "equator_expected": float(-np.pi),
        "equator_error": float(abs(gamma_equator - (-np.pi))),
        "tiny_loop_berry_phase": float(gamma_tiny),
        "tiny_loop_solid_angle": float(omega_tiny),
        "tiny_loop_expected_berry": float(expected_berry_tiny),
        "tiny_loop_error": float(abs(gamma_tiny - expected_berry_tiny)),
        "point_loop_berry_phase": float(gamma_point),
        "point_loop_expected": 0.0,
        "pass": bool(
            abs(gamma_tiny - expected_berry_tiny) < 1e-4 and
            abs(gamma_point) < 1e-14
        ),
        "note": "Contractible loop -> 0 solid angle -> 0 Berry phase"
    }


# ═══════════════════════════════════════════════════════════════════
# TEST 10: QGT for maximally mixed state (metric vs curvature)
# ═══════════════════════════════════════════════════════════════════

def test_10_qgt_max_mixed():
    """Quantum Geometric Tensor Q_{mu,nu} = <d_mu psi | (1-|psi><psi|) | d_nu psi>
    For a parameterised family rho(theta) at the maximally mixed point:
    - The metric (Re Q) may be nonzero (distances still exist)
    - The Berry curvature (Im Q) MUST be 0 (no holonomy for fully mixed)

    We parameterise via rho(t1,t2) = exp(-i t_k H_k) rho_mm exp(i t_k H_k)
    and compute the Bures metric tensor + curvature numerically."""

    d = 2
    rho_mm = np.eye(d, dtype=complex) / d
    H1 = np.array([[0, 1], [1, 0]], dtype=complex)   # sigma_x
    H2 = np.array([[0, -1j], [1j, 0]], dtype=complex) # sigma_y

    dt = 1e-6

    def evolve(rho, H, t):
        U = expm(-1j * H * t)
        return U @ rho @ U.conj().T

    # Numerical QGT via finite differences of fidelity
    # g_{mu,nu} = -d^2 F / (d t_mu d t_nu) at t=0
    # Berry curvature = antisymmetric part

    def fid_param(t1, t2):
        rho_t = evolve(evolve(rho_mm, H1, t1), H2, t2)
        return np.sqrt(np.clip(fidelity(rho_mm, rho_t), 0, 1))

    f00 = fid_param(0, 0)

    # Metric tensor components (second derivatives of sqrt-fidelity)
    g11 = -(fid_param(dt, 0) - 2 * f00 + fid_param(-dt, 0)) / dt**2
    g22 = -(fid_param(0, dt) - 2 * f00 + fid_param(0, -dt)) / dt**2
    g12 = -(fid_param(dt, dt) - fid_param(dt, -dt) -
            fid_param(-dt, dt) + fid_param(-dt, -dt)) / (4 * dt**2)

    # Berry curvature = antisymmetric part of QGT
    # For real symmetric finite-difference approach, curvature ~ g12 - g21
    # which is 0 by construction; use a phase-sensitive method instead.
    # Direct approach: commutator-based Berry curvature
    # F_12 = -2 Im Tr(rho [dH1, dH2]) for mixed states
    comm = H1 @ H2 - H2 @ H1
    berry_curv = -2.0 * np.imag(np.trace(rho_mm @ comm))

    # For maximally mixed: Tr(I/d * [H1,H2]) = Tr([H1,H2])/d
    # [sigma_x, sigma_y] = 2i sigma_z, Tr(sigma_z) = 0
    # So Berry curvature = 0.  Verify.

    metric_nonzero = bool(abs(g11) > 1e-12 or abs(g22) > 1e-12)

    return {
        "test": "QGT_maximally_mixed_metric_vs_curvature",
        "metric_g11": float(g11),
        "metric_g22": float(g22),
        "metric_g12": float(g12),
        "berry_curvature_F12": float(berry_curv),
        "metric_exists": metric_nonzero,
        "curvature_is_zero": bool(abs(berry_curv) < 1e-12),
        "pass": bool(abs(berry_curv) < 1e-12),
        "note": "Maximally mixed: metric may exist but Berry curvature must vanish (Tr(rho [H1,H2])=0 when rho ~ I)"
    }


# ═══════════════════════════════════════════════════════════════════
# RUN ALL
# ═══════════════════════════════════════════════════════════════════

def main():
    tests = [
        test_01_fs_identical,
        test_02_fs_mixed,
        test_03_bures_singular,
        test_04_berry_open_path,
        test_05_qfi_max_mixed,
        test_06_trace_distance_epsilon,
        test_07_fidelity_overflow,
        test_08_cl3_rotor_spinor,
        test_09_berry_contractible,
        test_10_qgt_max_mixed,
    ]

    all_results = []
    pass_count = 0
    fail_count = 0

    for fn in tests:
        print(f"Running {fn.__name__} ...", end=" ")
        try:
            result = fn()
            all_results.append(result)
            status = "PASS" if result.get("pass") else "FAIL"
            if result.get("pass"):
                pass_count += 1
            else:
                fail_count += 1
            print(status)
        except Exception as e:
            err_result = {
                "test": fn.__name__,
                "pass": False,
                "error": str(e),
            }
            all_results.append(err_result)
            fail_count += 1
            print(f"ERROR: {e}")

    summary = {
        "battery": "negative_geometry",
        "total_tests": len(tests),
        "passed": pass_count,
        "failed": fail_count,
        "results": all_results,
    }

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "negative_geometry_results.json")
    with open(out_path, "w") as f:
        json.dump(sanitize(summary), f, indent=2)

    print(f"\n{'='*60}")
    print(f"NEGATIVE GEOMETRY BATTERY: {pass_count}/{len(tests)} passed")
    print(f"Output: {out_path}")
    return summary


if __name__ == "__main__":
    main()
