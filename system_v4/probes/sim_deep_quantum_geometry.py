#!/usr/bin/env python3
"""
Deep Quantum Geometry Simulation
=================================
Runs the GeometricEngine for 10 cycles (80 stages) and computes
7 simultaneous geometric objects at EVERY step:

  1. Fubini-Study geodesic tracking (L and R spinors separately)
  2. Quantum Geometric Tensor evolution (metric + Berry curvature)
  3. Bures geometry on the 4x4 mixed state
  4. Steering ellipsoid of the 2-qubit state
  5. Berry phase accumulation with curvature field
  6. Quantum Fisher Information landscape
  7. Hopf fiber tracking (base + fiber + torus)
  8. Cl(3) rotor decomposition and holonomy

Output: a2_state/sim_results/deep_quantum_geometry_results.json
"""

import sys
import os
import json
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import GeometricEngine, EngineState, StageControls
from geometric_operators import (
    partial_trace_A, partial_trace_B,
    SIGMA_X, SIGMA_Y, SIGMA_Z, I2,
)
from hopf_manifold import (
    torus_coordinates, density_to_bloch,
    left_weyl_spinor, right_weyl_spinor,
    von_neumann_entropy_2x2, TORUS_CLIFFORD,
)
from bipartite_spinor_algebra import correlation_tensor as bipartite_correlation_tensor

from clifford import Cl
from scipy.linalg import sqrtm

# ═══════════════════════════════════════════════════════════════════
# CLIFFORD ALGEBRA SETUP
# ═══════════════════════════════════════════════════════════════════
layout, blades = Cl(3)
e1, e2, e3 = blades['e1'], blades['e2'], blades['e3']
e12, e13, e23 = blades['e12'], blades['e13'], blades['e23']
e123 = blades['e123']
cl3_scalar = layout.scalar


# ═══════════════════════════════════════════════════════════════════
# NUMPY SANITIZER
# ═══════════════════════════════════════════════════════════════════

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
        return float(np.real(obj))
    if isinstance(obj, (np.complexfloating,)):
        return float(np.real(obj))
    if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return 0.0
    return obj


# ═══════════════════════════════════════════════════════════════════
# 1. FUBINI-STUDY GEODESIC TRACKING
# ═══════════════════════════════════════════════════════════════════

def fubini_study_distance(psi_a, psi_b):
    """d_FS = arccos|<psi_a|psi_b>| for pure state spinors in C^2."""
    inner = np.abs(np.vdot(psi_a, psi_b))
    inner = np.clip(inner, 0.0, 1.0)
    return float(np.arccos(inner))


def geodesic_curvature_triangle(d_prev_curr, d_curr_next, d_prev_next):
    """Triangle inequality violation as curvature measure.
    kappa = (d_prev_curr + d_curr_next) - d_prev_next
    Zero for geodesic (great circle), positive for curved paths.
    """
    return float(d_prev_curr + d_curr_next - d_prev_next)


# ═══════════════════════════════════════════════════════════════════
# 2. QUANTUM GEOMETRIC TENSOR
# ═══════════════════════════════════════════════════════════════════

PAULI_GENERATORS = [SIGMA_X, SIGMA_Y, SIGMA_Z]


def quantum_geometric_tensor(rho, generators=None):
    """QGT Q_ij = Tr(rho H_i H_j) - Tr(rho H_i) Tr(rho H_j).
    Real part = Fubini-Study metric tensor.
    Imaginary part = Berry curvature tensor.
    """
    if generators is None:
        generators = PAULI_GENERATORS
    n = len(generators)
    Q = np.zeros((n, n), dtype=complex)
    for i in range(n):
        for j in range(n):
            Q[i, j] = (np.trace(rho @ generators[i] @ generators[j])
                        - np.trace(rho @ generators[i]) * np.trace(rho @ generators[j]))
    return Q


def qgt_metric(Q):
    """Extract Fubini-Study metric (real symmetric part)."""
    return np.real((Q + Q.T) / 2)


def qgt_berry_curvature(Q):
    """Extract Berry curvature (imaginary antisymmetric part)."""
    return np.imag((Q - Q.T) / (2j)) if np.any(np.imag(Q) != 0) else np.zeros_like(np.real(Q))


def metric_anisotropy(metric):
    """Ratio of max/min eigenvalue of the metric tensor."""
    evals = np.linalg.eigvalsh(metric)
    evals = np.abs(evals)
    emax = np.max(evals)
    emin = np.min(evals)
    if emin < 1e-15:
        return float(emax / 1e-15) if emax > 1e-15 else 1.0
    return float(emax / emin)


# ═══════════════════════════════════════════════════════════════════
# 3. BURES GEOMETRY
# ═══════════════════════════════════════════════════════════════════

def matrix_sqrt_psd(M):
    """Compute matrix square root for PSD matrix, handling numerics."""
    M = (M + M.conj().T) / 2
    evals, evecs = np.linalg.eigh(M)
    evals = np.maximum(evals, 0.0)
    return evecs @ np.diag(np.sqrt(evals)) @ evecs.conj().T


def fidelity_mixed(rho, sigma):
    """Fidelity F(rho, sigma) = (Tr sqrt(sqrt(rho) sigma sqrt(rho)))^2."""
    sqrt_rho = matrix_sqrt_psd(rho)
    inner = sqrt_rho @ sigma @ sqrt_rho
    inner = (inner + inner.conj().T) / 2
    evals = np.linalg.eigvalsh(inner)
    evals = np.maximum(evals, 0.0)
    return float(np.sum(np.sqrt(evals))) ** 2


def bures_distance(rho, sigma):
    """Bures distance d_B = sqrt(2(1 - sqrt(F(rho, sigma))))."""
    F = fidelity_mixed(rho, sigma)
    F = np.clip(F, 0.0, 1.0)
    return float(np.sqrt(np.maximum(2.0 * (1.0 - np.sqrt(F)), 0.0)))


def su4_generators():
    """15 generators of su(4) as 4x4 traceless Hermitian matrices.
    Uses tensor products of Pauli matrices.
    """
    paulis = [I2, SIGMA_X, SIGMA_Y, SIGMA_Z]
    gens = []
    for i in range(4):
        for j in range(4):
            if i == 0 and j == 0:
                continue  # skip identity x identity
            G = np.kron(paulis[i], paulis[j])
            gens.append(G)
    return gens


def bures_metric_tensor_numerical(rho, perturbations):
    """Compute Bures metric tensor via finite differences on fidelity."""
    eps = 1e-4
    n = len(perturbations)
    g = np.zeros((n, n))
    for i in range(n):
        for j in range(i, n):
            # Forward perturbation
            rho_p = rho + eps * perturbations[i] + eps * perturbations[j]
            rho_p = ensure_valid_4x4(rho_p)
            F_p = fidelity_mixed(rho, rho_p)

            # Mixed perturbation
            rho_m = rho + eps * perturbations[i] - eps * perturbations[j]
            rho_m = ensure_valid_4x4(rho_m)
            F_m = fidelity_mixed(rho, rho_m)

            # Bures metric from fidelity expansion
            # g_ij ~ (1 - sqrt(F_pp)) / eps^2  (symmetrized)
            val = (2.0 - 2.0 * np.sqrt(np.clip(F_p, 0, 1))
                   - 2.0 + 2.0 * np.sqrt(np.clip(F_m, 0, 1))) / (4.0 * eps**2)
            g[i, j] = val
            g[j, i] = val
    return g


def ensure_valid_4x4(rho):
    """Ensure valid 4x4 density matrix."""
    rho = (rho + rho.conj().T) / 2
    evals, evecs = np.linalg.eigh(rho)
    evals = np.maximum(evals, 0.0)
    rho = evecs @ np.diag(evals.astype(complex)) @ evecs.conj().T
    tr = np.real(np.trace(rho))
    if tr > 1e-15:
        rho /= tr
    else:
        rho = np.eye(4, dtype=complex) / 4
    return rho


# ═══════════════════════════════════════════════════════════════════
# 4. STEERING ELLIPSOID
# ═══════════════════════════════════════════════════════════════════

def steering_ellipsoid(rho_AB):
    """Compute the quantum steering ellipsoid for a 2-qubit state.
    Returns center (Bloch A), semi-axes, volume, singular values of T, orientation.
    """
    r_L, r_R, C_excess = bipartite_correlation_tensor(rho_AB)

    # Full correlation matrix T_ij = Tr(rho sigma_i x sigma_j)
    T = C_excess + np.outer(r_L, r_R)

    # Steering ellipsoid shape: eigenvalues of T T^T give semi-axes squared
    TTt = T @ T.T
    TTt = (TTt + TTt.T) / 2  # ensure symmetric
    evals = np.linalg.eigvalsh(TTt)
    semi_axes = np.sqrt(np.maximum(evals, 0.0))

    # Volume of the ellipsoid
    volume = (4.0 * np.pi / 3.0) * np.prod(semi_axes)

    # Singular values of T
    sv = np.linalg.svd(T, compute_uv=False)

    # Orientation (eigenvectors of T T^T)
    _, evecs = np.linalg.eigh(TTt)

    return {
        'center': r_L.tolist(),
        'semi_axes': sorted(semi_axes.tolist()),
        'volume': float(volume),
        'T_singular_values': sorted(sv.tolist()),
        'orientation': evecs.tolist(),
    }


# ═══════════════════════════════════════════════════════════════════
# 5. BERRY CURVATURE FIELD
# ═══════════════════════════════════════════════════════════════════

def berry_curvature_at_state(rho, generators=None):
    """F_ij = -2 Im(Q_ij) — Berry curvature tensor from QGT."""
    Q = quantum_geometric_tensor(rho, generators)
    return -2.0 * np.imag(Q)


# ═══════════════════════════════════════════════════════════════════
# 6. QUANTUM FISHER INFORMATION
# ═══════════════════════════════════════════════════════════════════

def qfi(rho, H):
    """Quantum Fisher Information F_Q(rho, H).
    F_Q = 2 sum_{i,j} (lambda_i - lambda_j)^2 / (lambda_i + lambda_j) |<i|H|j>|^2
    """
    evals, evecs = np.linalg.eigh(rho)
    d = len(evals)
    F = 0.0
    for i in range(d):
        for j in range(d):
            denom = evals[i] + evals[j]
            if denom > 1e-15:
                hij = abs(evecs[:, i].conj() @ H @ evecs[:, j])**2
                F += 2.0 * (evals[i] - evals[j])**2 / denom * hij
    return float(F)


# ═══════════════════════════════════════════════════════════════════
# 7. HOPF FIBER TRACKING
# ═══════════════════════════════════════════════════════════════════

def hopf_fiber_decompose(psi):
    """Decompose a C^2 spinor into Hopf coordinates.
    Returns (theta, phi, alpha) where:
      theta, phi = base point on S^2 (Bloch sphere angles)
      alpha = fiber angle (global phase)
    """
    z1, z2 = psi[0], psi[1]
    r1 = np.abs(z1)
    r2 = np.abs(z2)

    # Bloch sphere angles
    norm = np.sqrt(r1**2 + r2**2)
    if norm < 1e-15:
        return 0.0, 0.0, 0.0

    # theta = 2 * arccos(|z1|/norm)
    theta = 2.0 * np.arccos(np.clip(r1 / norm, 0.0, 1.0))
    # phi = arg(z2) - arg(z1)
    phi = float(np.angle(z2) - np.angle(z1))
    # alpha = arg(z1) (global phase = fiber coordinate)
    alpha = float(np.angle(z1))

    return float(theta), float(phi % (2 * np.pi)), float(alpha % (2 * np.pi))


def purity_from_rho(rho):
    """Tr(rho^2) — purity of a density matrix."""
    return float(np.real(np.trace(rho @ rho)))


# ═══════════════════════════════════════════════════════════════════
# 8. Cl(3) ROTOR DECOMPOSITION
# ═══════════════════════════════════════════════════════════════════

def find_connecting_rotor(r_old, r_new):
    """Find the Cl(3) rotor R such that R * v_old * ~R = v_new.
    v = r[0]*e1 + r[1]*e2 + r[2]*e3 (Bloch vector as grade-1 multivector).
    R = (1 + v_new * v_old) / |1 + v_new * v_old|
    """
    n_old = np.linalg.norm(r_old)
    n_new = np.linalg.norm(r_new)
    if n_old < 1e-12 or n_new < 1e-12:
        # Degenerate — return identity rotor
        return cl3_scalar * 1.0, 0.0, np.array([0, 0, 1.0])

    # Normalize
    r_old_n = r_old / n_old
    r_new_n = r_new / n_new

    mv_old = r_old_n[0] * e1 + r_old_n[1] * e2 + r_old_n[2] * e3
    mv_new = r_new_n[0] * e1 + r_new_n[1] * e2 + r_new_n[2] * e3

    R = 1.0 + mv_new * mv_old
    R_norm = float(abs(R))
    if R_norm < 1e-12:
        # Anti-parallel vectors: 180 degree rotation
        # Pick any perpendicular axis
        if abs(r_old_n[0]) < 0.9:
            perp = np.cross(r_old_n, [1, 0, 0])
        else:
            perp = np.cross(r_old_n, [0, 1, 0])
        perp = perp / np.linalg.norm(perp)
        return perp[0] * e12 + perp[1] * e13 + perp[2] * e23, np.pi, perp

    R = R / R_norm

    # Extract rotation angle: R = cos(angle/2) + sin(angle/2) * B
    # where B is a unit bivector (rotation plane)
    scalar_part = float(R(0))
    bivector_part = R(2)
    biv_norm = float(abs(bivector_part))

    angle = 2.0 * np.arctan2(biv_norm, abs(scalar_part))

    # Rotation axis from bivector: e12 -> e3, e13 -> -e2, e23 -> e1
    if biv_norm > 1e-12:
        axis = np.array([
            float(bivector_part[e23]),
            -float(bivector_part[e13]),
            float(bivector_part[e12]),
        ])
        ax_norm = np.linalg.norm(axis)
        if ax_norm > 1e-12:
            axis = axis / ax_norm
        else:
            axis = np.array([0, 0, 1.0])
    else:
        axis = np.array([0, 0, 1.0])

    return R, float(angle), axis


def compose_rotors(rotor_list):
    """Compose a sequence of Cl(3) rotors: R_total = R_n * ... * R_1."""
    R = cl3_scalar * 1.0
    for Ri in rotor_list:
        R = Ri * R
    # Normalize
    R_norm = float(abs(R))
    if R_norm > 1e-12:
        R = R / R_norm
    return R


def rotor_to_angle_axis(R):
    """Extract rotation angle and axis from a Cl(3) rotor."""
    scalar_part = float(R(0))
    bivector_part = R(2)
    biv_norm = float(abs(bivector_part))
    angle = 2.0 * np.arctan2(biv_norm, abs(scalar_part))
    if biv_norm > 1e-12:
        axis = np.array([
            float(bivector_part[e23]),
            -float(bivector_part[e13]),
            float(bivector_part[e12]),
        ])
        ax_norm = np.linalg.norm(axis)
        if ax_norm > 1e-12:
            axis = axis / ax_norm
        else:
            axis = np.array([0, 0, 1.0])
    else:
        axis = np.array([0, 0, 1.0])
    return float(angle), axis.tolist()


# ═══════════════════════════════════════════════════════════════════
# MAIN SIMULATION
# ═══════════════════════════════════════════════════════════════════

def run_deep_geometry_sim(n_cycles=10):
    """Run the full deep quantum geometry simulation."""
    engine = GeometricEngine(engine_type=1)
    state = engine.init_state()

    n_steps = n_cycles * 8  # 8 stages per cycle

    # Storage
    # 1. Fubini-Study
    fs_distances_L = []
    fs_distances_R = []
    fs_curvature = []

    # 2. QGT
    qgt_metric_norms = []
    qgt_berry_norms = []
    qgt_anisotropy = []

    # 3. Bures
    bures_distances = []
    bures_metric_norms = []

    # 4. Steering
    steer_volumes = []
    steer_semi_axes = []
    steer_centers = []

    # 5. Berry curvature
    berry_F_xy = []
    berry_F_xz = []
    berry_F_yz = []

    # 6. QFI
    qfi_x_vals = []
    qfi_y_vals = []
    qfi_z_vals = []
    qfi_anisotropy = []

    # 7. Hopf fiber
    hopf_theta = []
    hopf_phi = []
    hopf_alpha = []
    hopf_purity = []

    # 8. Rotors
    rotor_angles = []
    rotor_axes = []
    rotor_objects = []  # actual Cl(3) rotors for holonomy composition

    # Previous states for distances
    prev_psi_L = left_weyl_spinor(state.q())
    prev_psi_R = right_weyl_spinor(state.q())
    prev_rho_AB = state.rho_AB.copy()
    prev_bloch_L = density_to_bloch(state.rho_L)

    # Two-step-back for curvature
    prev_prev_psi_L = prev_psi_L.copy()
    prev_prev_psi_R = prev_psi_R.copy()

    # Pre-compute su(4) generators for Bures (use a subset of 6 for speed)
    su4_gens_full = su4_generators()
    # Use only 6 representative generators for Bures metric (speed)
    su4_subset = su4_gens_full[:6]

    print(f"Running deep quantum geometry simulation: {n_cycles} cycles, {n_steps} steps")
    print("=" * 70)

    for step_i in range(n_steps):
        cycle = step_i // 8
        stage_in_cycle = step_i % 8

        # Run engine step
        state = engine.step(state, stage_idx=state.stage_idx % 8)

        # Extract current states
        q_now = state.q()
        psi_L = left_weyl_spinor(q_now)
        psi_R = right_weyl_spinor(q_now)
        rho_AB = state.rho_AB.copy()
        rho_L = state.rho_L.copy()
        rho_R = state.rho_R.copy()
        bloch_L = density_to_bloch(rho_L)
        bloch_R = density_to_bloch(rho_R)

        # ── 1. FUBINI-STUDY ────────────────────────────────────────
        d_L = fubini_study_distance(prev_psi_L, psi_L)
        d_R = fubini_study_distance(prev_psi_R, psi_R)
        fs_distances_L.append(d_L)
        fs_distances_R.append(d_R)

        # Curvature requires 3 consecutive points
        if step_i >= 2:
            d_L_prev_curr = fs_distances_L[-1]
            d_L_prev_prev = fubini_study_distance(prev_prev_psi_L, prev_psi_L)
            d_L_prev_next = fubini_study_distance(prev_prev_psi_L, psi_L)
            kappa = geodesic_curvature_triangle(d_L_prev_prev, d_L_prev_curr, d_L_prev_next)
            fs_curvature.append(kappa)
        else:
            fs_curvature.append(0.0)

        prev_prev_psi_L = prev_psi_L.copy()
        prev_prev_psi_R = prev_psi_R.copy()

        # ── 2. QGT ─────────────────────────────────────────────────
        Q_L = quantum_geometric_tensor(rho_L)
        metric_L = qgt_metric(Q_L)
        berry_L = berry_curvature_at_state(rho_L)

        qgt_metric_norms.append(float(np.linalg.norm(metric_L)))
        qgt_berry_norms.append(float(np.linalg.norm(berry_L)))
        qgt_anisotropy.append(metric_anisotropy(metric_L))

        # ── 3. BURES ───────────────────────────────────────────────
        d_bures = bures_distance(prev_rho_AB, rho_AB)
        bures_distances.append(d_bures)

        # Bures metric tensor (numerical, on su(4) subset)
        bm = bures_metric_tensor_numerical(rho_AB, su4_subset)
        bures_metric_norms.append(float(np.linalg.norm(bm)))

        # ── 4. STEERING ELLIPSOID ──────────────────────────────────
        steer = steering_ellipsoid(rho_AB)
        steer_volumes.append(steer['volume'])
        steer_semi_axes.append(steer['semi_axes'])
        steer_centers.append(steer['center'])

        # ── 5. BERRY CURVATURE FIELD ───────────────────────────────
        F = berry_curvature_at_state(rho_L)
        berry_F_xy.append(float(F[0, 1]))
        berry_F_xz.append(float(F[0, 2]))
        berry_F_yz.append(float(F[1, 2]))

        # ── 6. QFI ─────────────────────────────────────────────────
        qfi_x = qfi(rho_L, SIGMA_X)
        qfi_y = qfi(rho_L, SIGMA_Y)
        qfi_z = qfi(rho_L, SIGMA_Z)
        qfi_x_vals.append(qfi_x)
        qfi_y_vals.append(qfi_y)
        qfi_z_vals.append(qfi_z)
        qfi_max = max(qfi_x, qfi_y, qfi_z)
        qfi_min = min(qfi_x, qfi_y, qfi_z)
        qfi_anisotropy.append(qfi_max / qfi_min if qfi_min > 1e-15 else qfi_max / 1e-15)

        # ── 7. HOPF FIBER ──────────────────────────────────────────
        theta_h, phi_h, alpha_h = hopf_fiber_decompose(psi_L)
        hopf_theta.append(theta_h)
        hopf_phi.append(phi_h)
        hopf_alpha.append(alpha_h)
        hopf_purity.append(purity_from_rho(rho_L))

        # ── 8. ROTOR ───────────────────────────────────────────────
        R, angle, axis = find_connecting_rotor(prev_bloch_L, bloch_L)
        rotor_angles.append(angle)
        rotor_axes.append(axis.tolist() if isinstance(axis, np.ndarray) else axis)
        rotor_objects.append(R)

        # Update previous states
        prev_psi_L = psi_L.copy()
        prev_psi_R = psi_R.copy()
        prev_rho_AB = rho_AB.copy()
        prev_bloch_L = bloch_L.copy()

        if (step_i + 1) % 8 == 0:
            print(f"  Cycle {cycle + 1}/{n_cycles} complete | "
                  f"d_FS_L={d_L:.4f} d_FS_R={d_R:.4f} | "
                  f"steer_vol={steer['volume']:.6f} | "
                  f"QFI_x={qfi_x:.3f} QFI_y={qfi_y:.3f} QFI_z={qfi_z:.3f}")

    # ── HOLONOMY PER CYCLE ─────────────────────────────────────────
    holonomy_per_cycle = []
    for c in range(n_cycles):
        start = c * 8
        end = start + 8
        cycle_rotors = [r for r in rotor_objects[start:end]
                        if not isinstance(r, (int, float))]
        if len(cycle_rotors) > 0:
            R_total = compose_rotors(cycle_rotors)
            angle_h, axis_h = rotor_to_angle_axis(R_total)
            holonomy_per_cycle.append({
                'angle': angle_h,
                'axis': axis_h,
            })
        else:
            holonomy_per_cycle.append({'angle': 0.0, 'axis': [0, 0, 1]})

    # ── ASSEMBLE RESULTS ───────────────────────────────────────────
    results = {
        "name": "deep_quantum_geometry",
        "n_cycles": n_cycles,
        "n_steps": n_steps,
        "fubini_study": {
            "geodesic_distances_L": fs_distances_L,
            "geodesic_distances_R": fs_distances_R,
            "accumulated_length_L": float(sum(fs_distances_L)),
            "accumulated_length_R": float(sum(fs_distances_R)),
            "curvature_trajectory": fs_curvature,
        },
        "qgt_evolution": {
            "metric_norms": qgt_metric_norms,
            "berry_norms": qgt_berry_norms,
            "metric_anisotropy": qgt_anisotropy,
        },
        "bures_geometry": {
            "distances": bures_distances,
            "accumulated_distance": float(sum(bures_distances)),
            "metric_norms": bures_metric_norms,
        },
        "steering_ellipsoid": {
            "volumes": steer_volumes,
            "semi_axes_trajectory": steer_semi_axes,
            "center_trajectory": steer_centers,
        },
        "berry_curvature_field": {
            "F_xy": berry_F_xy,
            "F_xz": berry_F_xz,
            "F_yz": berry_F_yz,
        },
        "qfi_landscape": {
            "qfi_x": qfi_x_vals,
            "qfi_y": qfi_y_vals,
            "qfi_z": qfi_z_vals,
            "anisotropy": qfi_anisotropy,
        },
        "hopf_fiber": {
            "theta": hopf_theta,
            "phi": hopf_phi,
            "alpha": hopf_alpha,
            "eta_purity": hopf_purity,
        },
        "rotor_sequence": {
            "angles": rotor_angles,
            "axes": rotor_axes,
            "holonomy_per_cycle": holonomy_per_cycle,
        },
    }

    # ── SUMMARY STATISTICS ─────────────────────────────────────────
    summary = {
        "fubini_study": {
            "total_geodesic_L": float(sum(fs_distances_L)),
            "total_geodesic_R": float(sum(fs_distances_R)),
            "mean_step_L": float(np.mean(fs_distances_L)),
            "mean_step_R": float(np.mean(fs_distances_R)),
            "max_curvature": float(np.max(fs_curvature)) if fs_curvature else 0.0,
            "chirality_ratio_L_over_R": (
                float(sum(fs_distances_L) / sum(fs_distances_R))
                if sum(fs_distances_R) > 1e-15 else float('inf')
            ),
        },
        "qgt": {
            "mean_metric_norm": float(np.mean(qgt_metric_norms)),
            "mean_berry_norm": float(np.mean(qgt_berry_norms)),
            "max_anisotropy": float(np.max(qgt_anisotropy)),
            "mean_anisotropy": float(np.mean(qgt_anisotropy)),
        },
        "bures": {
            "total_distance": float(sum(bures_distances)),
            "mean_step": float(np.mean(bures_distances)),
            "max_step": float(np.max(bures_distances)),
        },
        "steering": {
            "mean_volume": float(np.mean(steer_volumes)),
            "max_volume": float(np.max(steer_volumes)),
            "min_volume": float(np.min(steer_volumes)),
            "volume_range": float(np.max(steer_volumes) - np.min(steer_volumes)),
        },
        "berry_curvature": {
            "mean_abs_F_xy": float(np.mean(np.abs(berry_F_xy))),
            "mean_abs_F_xz": float(np.mean(np.abs(berry_F_xz))),
            "mean_abs_F_yz": float(np.mean(np.abs(berry_F_yz))),
            "max_component": float(np.max([np.max(np.abs(berry_F_xy)),
                                            np.max(np.abs(berry_F_xz)),
                                            np.max(np.abs(berry_F_yz))])),
        },
        "qfi": {
            "mean_qfi_x": float(np.mean(qfi_x_vals)),
            "mean_qfi_y": float(np.mean(qfi_y_vals)),
            "mean_qfi_z": float(np.mean(qfi_z_vals)),
            "max_anisotropy": float(np.max(qfi_anisotropy)),
            "mean_anisotropy": float(np.mean(qfi_anisotropy)),
        },
        "hopf_fiber": {
            "theta_range": float(np.max(hopf_theta) - np.min(hopf_theta)),
            "phi_range": float(np.max(hopf_phi) - np.min(hopf_phi)),
            "alpha_range": float(np.max(hopf_alpha) - np.min(hopf_alpha)),
            "mean_purity": float(np.mean(hopf_purity)),
        },
        "holonomy": {
            "mean_cycle_angle": float(np.mean([h['angle'] for h in holonomy_per_cycle])),
            "angles_per_cycle": [h['angle'] for h in holonomy_per_cycle],
        },
    }
    results["summary"] = summary

    return sanitize(results)


# ═══════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    results = run_deep_geometry_sim(n_cycles=10)

    # Save
    out_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "a2_state", "sim_results", "deep_quantum_geometry_results.json"
    )
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 70)
    print(f"Results saved to: {out_path}")
    print("=" * 70)

    # Print summary
    s = results["summary"]
    print("\n=== SUMMARY ===\n")

    print("FUBINI-STUDY GEODESICS:")
    print(f"  Total geodesic length L: {s['fubini_study']['total_geodesic_L']:.6f}")
    print(f"  Total geodesic length R: {s['fubini_study']['total_geodesic_R']:.6f}")
    print(f"  Mean step L: {s['fubini_study']['mean_step_L']:.6f}")
    print(f"  Mean step R: {s['fubini_study']['mean_step_R']:.6f}")
    print(f"  Chirality ratio (L/R): {s['fubini_study']['chirality_ratio_L_over_R']:.4f}")
    print(f"  Max curvature: {s['fubini_study']['max_curvature']:.6f}")

    print("\nQUANTUM GEOMETRIC TENSOR:")
    print(f"  Mean metric norm: {s['qgt']['mean_metric_norm']:.6f}")
    print(f"  Mean Berry norm: {s['qgt']['mean_berry_norm']:.6f}")
    print(f"  Mean anisotropy: {s['qgt']['mean_anisotropy']:.4f}")
    print(f"  Max anisotropy: {s['qgt']['max_anisotropy']:.4f}")

    print("\nBURES GEOMETRY:")
    print(f"  Total Bures distance: {s['bures']['total_distance']:.6f}")
    print(f"  Mean step: {s['bures']['mean_step']:.6f}")
    print(f"  Max step: {s['bures']['max_step']:.6f}")

    print("\nSTEERING ELLIPSOID:")
    print(f"  Mean volume: {s['steering']['mean_volume']:.6f}")
    print(f"  Volume range: [{s['steering']['min_volume']:.6f}, {s['steering']['max_volume']:.6f}]")

    print("\nBERRY CURVATURE FIELD:")
    print(f"  Mean |F_xy|: {s['berry_curvature']['mean_abs_F_xy']:.6f}")
    print(f"  Mean |F_xz|: {s['berry_curvature']['mean_abs_F_xz']:.6f}")
    print(f"  Mean |F_yz|: {s['berry_curvature']['mean_abs_F_yz']:.6f}")
    print(f"  Max component: {s['berry_curvature']['max_component']:.6f}")

    print("\nQUANTUM FISHER INFORMATION:")
    print(f"  Mean QFI_x: {s['qfi']['mean_qfi_x']:.4f}")
    print(f"  Mean QFI_y: {s['qfi']['mean_qfi_y']:.4f}")
    print(f"  Mean QFI_z: {s['qfi']['mean_qfi_z']:.4f}")
    print(f"  Mean anisotropy: {s['qfi']['mean_anisotropy']:.4f}")

    print("\nHOPF FIBER TRACKING:")
    print(f"  Theta range: {s['hopf_fiber']['theta_range']:.6f}")
    print(f"  Phi range: {s['hopf_fiber']['phi_range']:.6f}")
    print(f"  Alpha range: {s['hopf_fiber']['alpha_range']:.6f}")
    print(f"  Mean purity: {s['hopf_fiber']['mean_purity']:.6f}")

    print("\nHOLONOMY (Cl(3) ROTORS):")
    print(f"  Mean cycle holonomy angle: {s['holonomy']['mean_cycle_angle']:.6f} rad")
    for i, a in enumerate(s['holonomy']['angles_per_cycle']):
        print(f"    Cycle {i+1}: {a:.6f} rad ({np.degrees(a):.2f} deg)")

    print("\n=== SIMULATION COMPLETE ===")
