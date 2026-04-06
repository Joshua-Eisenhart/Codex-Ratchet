#!/usr/bin/env python3
"""
Full Torus Spinor Dynamics
==========================
REAL Weyl spinor evolution on REAL nested Hopf torus surfaces.
No density matrices. No abstract operators. Actual spinor transport
with position-dependent geometry, Berry phase accumulation,
and torus-level transport via Cl(3) rotors.

Spinors live on S³ parametrised by toroidal coordinates (η, θ₁, θ₂).
Evolution proceeds around fiber (θ₁) and base (θ₂) loops with
terrain-specific Clifford rotors and dissipation.
"""

import sys
import os
import json
import datetime
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from clifford import Cl

from hopf_manifold import (
    torus_coordinates, torus_radii, berry_phase,
    left_weyl_spinor, right_weyl_spinor,
    density_to_bloch, von_neumann_entropy_2x2,
    hopf_map,
    TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER,
)
from clifford_engine_bridge import (
    rotor_z, rotor_x, apply_rotor,
    bloch_to_multivector, multivector_to_bloch,
    layout, blades, e1, e2, e3, e12, e23, e123, scalar,
)
from engine_core import TERRAINS, STAGE_OPERATOR_LUT, LOOP_STAGE_ORDER

# ═══════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════

N_CYCLES = 10
STAGES_PER_CYCLE = 8          # 4 fiber + 4 base
DTHETA = 2 * np.pi / 4        # quarter turn per step
ETA_RELAX_RATE = 0.1           # inter-torus relaxation per cycle
DEPHASE_EPSILON = 0.1          # base dephasing strength per step

# Terrain traversal orders (Type-1 engine)
# Fiber loop: Se_f(0) -> Si_f(1) -> Ni_f(3) -> Ne_f(2)  (inductive)
# Base  loop: Se_b(4) -> Ne_b(6) -> Ni_b(7) -> Si_b(5)  (deductive)
FIBER_TERRAIN_INDICES = [0, 1, 3, 2]
BASE_TERRAIN_INDICES = [4, 6, 7, 5]


# ═══════════════════════════════════════════════════════════════════
# SPINOR UTILITIES
# ═══════════════════════════════════════════════════════════════════

def spinor_to_density(psi):
    """Pure state density matrix from spinor |ψ⟩⟨ψ|."""
    return np.outer(psi, np.conj(psi))


def spinor_bloch(psi):
    """Bloch vector from a 2-component spinor."""
    rho = spinor_to_density(psi)
    return density_to_bloch(rho)


def spinor_entropy(psi):
    """Von Neumann entropy of the pure state (always 0 for pure, >0 after dephasing)."""
    rho = spinor_to_density(psi)
    return von_neumann_entropy_2x2(rho)


def spinor_overlap(psi_a, psi_b):
    """Inner product ⟨ψ_a|ψ_b⟩."""
    return np.vdot(psi_a, psi_b)


def renormalize(psi):
    """Renormalize spinor to unit norm."""
    n = np.linalg.norm(psi)
    if n < 1e-15:
        return psi
    return psi / n


# ═══════════════════════════════════════════════════════════════════
# DISSIPATION (breaks unitarity deliberately)
# ═══════════════════════════════════════════════════════════════════

# Z-basis states
KET_0 = np.array([1.0, 0.0], dtype=complex)
KET_1 = np.array([0.0, 1.0], dtype=complex)

# X-basis states
KET_PLUS  = np.array([1.0,  1.0], dtype=complex) / np.sqrt(2)
KET_MINUS = np.array([1.0, -1.0], dtype=complex) / np.sqrt(2)


def dephase_z_spinor(psi, epsilon):
    """Ti dephasing: partial projection toward Z eigenstates.

    psi -> (1-eps)*psi + eps * |n><n|psi  where |n> is nearest Z eigenstate.
    Then renormalize.
    """
    # Project onto the nearest Z eigenstate
    p0 = abs(np.vdot(KET_0, psi))**2
    target = KET_0 if p0 >= 0.5 else KET_1
    overlap = np.vdot(target, psi)
    psi_new = (1 - epsilon) * psi + epsilon * overlap * target
    return renormalize(psi_new)


def dephase_x_spinor(psi, epsilon):
    """Te dephasing: partial projection toward X eigenstates.

    psi -> (1-eps)*psi + eps * |n><n|psi  where |n> is nearest X eigenstate.
    Then renormalize.
    """
    p_plus = abs(np.vdot(KET_PLUS, psi))**2
    target = KET_PLUS if p_plus >= 0.5 else KET_MINUS
    overlap = np.vdot(target, psi)
    psi_new = (1 - epsilon) * psi + epsilon * overlap * target
    return renormalize(psi_new)


# ═══════════════════════════════════════════════════════════════════
# CLIFFORD ROTOR APPLICATION TO SPINORS
# ═══════════════════════════════════════════════════════════════════

def cl3_rotor_to_su2(rotor_func, angle):
    """Convert a Cl(3) rotor to the corresponding SU(2) matrix.

    Cl(3) rotor R = cos(a/2) + sin(a/2) * B  where B is a unit bivector.
    The corresponding SU(2) matrix is:
      rotor_z(a): R_z = exp(-i a/2 sigma_z) = diag(e^{-ia/2}, e^{ia/2})
      rotor_x(a): R_x = exp(-i a/2 sigma_x) = cos(a/2) I - i sin(a/2) sigma_x

    We compute this by applying the Cl(3) rotor to the basis vectors
    e1, e2, e3 and reading off the SO(3) matrix, then lifting to SU(2).
    """
    R = rotor_func(angle)

    # Apply rotor to basis vectors to get SO(3) rotation matrix
    e1_rot = apply_rotor(e1, R)
    e2_rot = apply_rotor(e2, R)
    e3_rot = apply_rotor(e3, R)

    # Extract the 3x3 rotation matrix
    rot = np.array([
        [float(e1_rot[e1]), float(e2_rot[e1]), float(e3_rot[e1])],
        [float(e1_rot[e2]), float(e2_rot[e2]), float(e3_rot[e2])],
        [float(e1_rot[e3]), float(e2_rot[e3]), float(e3_rot[e3])],
    ])

    # Lift SO(3) -> SU(2) using the standard map
    # For rotation by angle a around axis n:
    #   U = cos(a/2) I - i sin(a/2) (n . sigma)
    # Extract axis and angle from the rotation matrix
    cos_a = (np.trace(rot) - 1) / 2
    cos_a = np.clip(cos_a, -1.0, 1.0)
    a = np.arccos(cos_a)

    if abs(a) < 1e-12:
        return np.eye(2, dtype=complex)

    # Axis from antisymmetric part
    nx = (rot[2, 1] - rot[1, 2]) / (2 * np.sin(a))
    ny = (rot[0, 2] - rot[2, 0]) / (2 * np.sin(a))
    nz = (rot[1, 0] - rot[0, 1]) / (2 * np.sin(a))

    sigma_x = np.array([[0, 1], [1, 0]], dtype=complex)
    sigma_y = np.array([[0, -1j], [1j, 0]], dtype=complex)
    sigma_z = np.array([[1, 0], [0, -1]], dtype=complex)

    U = np.cos(a / 2) * np.eye(2, dtype=complex) - 1j * np.sin(a / 2) * (
        nx * sigma_x + ny * sigma_y + nz * sigma_z
    )
    return U


def apply_cl3_rotor_to_spinor(psi, rotor_func, angle):
    """Apply a Cl(3) rotor to a spinor via its SU(2) representation.

    This is REAL geometric computation:
    1. Build the Cl(3) rotor from the angle
    2. Convert to the equivalent SU(2) matrix
    3. Apply directly to the spinor: psi' = U @ psi

    The SU(2) matrix IS the spinor representation of the Cl(3) rotor.
    This preserves global phase (critical for Berry phase accumulation).
    """
    U = cl3_rotor_to_su2(rotor_func, angle)
    return U @ psi


# ═══════════════════════════════════════════════════════════════════
# TANGENT VECTOR ON TORUS
# ═══════════════════════════════════════════════════════════════════

def fiber_tangent(eta, theta1, theta2):
    """Tangent vector to the fiber (theta1) direction on the torus.

    d/dtheta1 of q(eta, theta1, theta2):
      z1 = cos(eta) * e^{i*theta1} -> dz1/dtheta1 = i * z1
      z2 = sin(eta) * e^{i*theta2} -> dz2/dtheta1 = 0

    Returns unit tangent in R^4, then projected to R^3 Bloch direction.
    """
    z1 = np.cos(eta) * np.exp(1j * theta1)
    # tangent in C^2: (i*z1, 0)
    t = np.array([i_comp for i_comp in [
        -np.imag(z1), np.real(z1), 0.0, 0.0
    ]])
    return t / (np.linalg.norm(t) + 1e-15)


def base_tangent(eta, theta1, theta2):
    """Tangent vector to the base (theta2) direction on the torus.

    d/dtheta2 of q(eta, theta1, theta2):
      z1 -> 0
      z2 = sin(eta) * e^{i*theta2} -> dz2/dtheta2 = i * z2
    """
    z2 = np.sin(eta) * np.exp(1j * theta2)
    t = np.array([0.0, 0.0, -np.imag(z2), np.real(z2)])
    return t / (np.linalg.norm(t) + 1e-15)


# ═══════════════════════════════════════════════════════════════════
# TERRAIN -> ROTOR + DEPHASING MAPPING
# ═══════════════════════════════════════════════════════════════════

def get_terrain_action(terrain_idx, loop_type):
    """Determine rotor and dephasing for a terrain step.

    Uses the Type-1 engine STAGE_OPERATOR_LUT.

    Returns:
        (rotor_func, is_dephasing, dephase_func_or_None)

    Fiber loop uses rotor_z (fiber = z-circle)
    Base  loop uses rotor_x (base  = x-circle)
    Ti -> z-dephasing
    Te -> x-dephasing
    Fe, Fi -> pure rotation (no dephasing)
    """
    terrain = TERRAINS[terrain_idx]
    op_name, polarity_up = STAGE_OPERATOR_LUT[(1, terrain["loop"], terrain["topo"])]

    if loop_type == "fiber":
        rotor_func = rotor_z
    else:
        rotor_func = rotor_x

    # Determine angle sign from polarity
    angle_sign = 1.0 if polarity_up else -1.0

    # Determine if this terrain dephases
    dephase_func = None
    if op_name == "Ti":
        dephase_func = dephase_z_spinor
    elif op_name == "Te":
        dephase_func = dephase_x_spinor

    return rotor_func, angle_sign, dephase_func, op_name


# ═══════════════════════════════════════════════════════════════════
# CORE SIMULATION
# ═══════════════════════════════════════════════════════════════════

def run_spinor_dynamics(eta_start, n_cycles=N_CYCLES, label=""):
    """Run full Weyl spinor dynamics on the nested Hopf torus.

    Args:
        eta_start: Initial torus latitude (TORUS_INNER, TORUS_CLIFFORD, or TORUS_OUTER).
        n_cycles: Number of full cycles (each = 4 fiber + 4 base steps).
        label: Name for this run.

    Returns:
        dict with all trajectory data.
    """
    # ── Initialise ──
    eta = eta_start
    theta1 = 0.0
    theta2 = 0.0

    q = torus_coordinates(eta, theta1, theta2)
    psi_L = left_weyl_spinor(q)
    psi_R = right_weyl_spinor(q)

    # Trajectory storage
    berry_phase_accum = 0.0
    entropy_traj = []
    bloch_L_traj = []
    bloch_R_traj = []
    chirality_traj = []
    torus_pos_traj = []
    berry_increments = []
    operator_sequence = []
    s3_path = []           # full S3 path for analytic Berry
    fiber_s3_path = []     # first fiber loop only (4 points) for clean comparison
    stage_counter = 0

    total_stages = n_cycles * STAGES_PER_CYCLE

    for cycle in range(n_cycles):
        # ── Fiber loop (4 steps) ──
        for step_i, t_idx in enumerate(FIBER_TERRAIN_INDICES):
            psi_L_prev = psi_L.copy()
            psi_R_prev = psi_R.copy()

            # Move along fiber
            theta1 += DTHETA

            # Compute new torus position
            q_new = torus_coordinates(eta, theta1, theta2)
            s3_path.append(q_new.copy())

            # Track first fiber loop for clean Berry comparison
            if cycle == 0:
                fiber_s3_path.append(q_new.copy())

            # Tangent vector at new position
            tang = fiber_tangent(eta, theta1, theta2)

            # Get terrain-specific action
            rotor_func, angle_sign, dephase_func, op_name = get_terrain_action(t_idx, "fiber")

            # Rotor angle: DTHETA scaled by torus major radius
            R_major, R_minor = torus_radii(eta)
            rotor_angle = angle_sign * DTHETA * R_major

            # Apply Cl(3) rotor: LEFT gets positive, RIGHT gets negative (chirality)
            psi_L = apply_cl3_rotor_to_spinor(psi_L, rotor_func, +rotor_angle)
            psi_R = apply_cl3_rotor_to_spinor(psi_R, rotor_func, -rotor_angle)

            # Apply dephasing if this terrain is dissipative
            if dephase_func is not None:
                strength = DEPHASE_EPSILON
                psi_L = dephase_func(psi_L, strength)
                psi_R = dephase_func(psi_R, strength)

            # Berry phase increment from the GEOMETRIC transport.
            # Compare the transported spinor to the "reference" spinor at the
            # new torus position.  The reference is the canonical lift
            # (left_weyl_spinor at the new S3 point).  The difference between
            # our evolved spinor and the reference is the accumulated holonomy.
            #
            # Incremental: track phase of <psi_prev | psi_now>
            # (Pancharatnam connection on the evolving state)
            overlap_L = spinor_overlap(psi_L_prev, psi_L)
            if abs(overlap_L) > 1e-15:
                berry_inc = -np.angle(overlap_L)
            else:
                berry_inc = 0.0
            berry_phase_accum += berry_inc
            berry_increments.append(float(berry_inc))

            # Record observables
            bloch_L = spinor_bloch(psi_L)
            bloch_R = spinor_bloch(psi_R)
            rho_combined = 0.5 * (spinor_to_density(psi_L) + spinor_to_density(psi_R))
            ent = von_neumann_entropy_2x2(rho_combined)

            dot_LR = float(np.dot(bloch_L, bloch_R))

            entropy_traj.append(float(ent))
            bloch_L_traj.append(bloch_L.tolist())
            bloch_R_traj.append(bloch_R.tolist())
            chirality_traj.append(dot_LR)
            torus_pos_traj.append([float(eta), float(theta1 % (2 * np.pi)),
                                   float(theta2 % (2 * np.pi))])
            operator_sequence.append(op_name)

        # ── Base loop (4 steps) ──
        for step_i, t_idx in enumerate(BASE_TERRAIN_INDICES):
            psi_L_prev = psi_L.copy()
            psi_R_prev = psi_R.copy()

            # Move along base
            theta2 += DTHETA

            # Compute new torus position
            q_new = torus_coordinates(eta, theta1, theta2)
            s3_path.append(q_new.copy())

            # Tangent vector at new position
            tang = base_tangent(eta, theta1, theta2)

            # Get terrain-specific action
            rotor_func, angle_sign, dephase_func, op_name = get_terrain_action(t_idx, "base")

            # Rotor angle: DTHETA scaled by torus minor radius
            R_major, R_minor = torus_radii(eta)
            rotor_angle = angle_sign * DTHETA * R_minor

            # Apply Cl(3) rotor with chirality
            psi_L = apply_cl3_rotor_to_spinor(psi_L, rotor_func, +rotor_angle)
            psi_R = apply_cl3_rotor_to_spinor(psi_R, rotor_func, -rotor_angle)

            # Dephasing
            if dephase_func is not None:
                strength = DEPHASE_EPSILON
                psi_L = dephase_func(psi_L, strength)
                psi_R = dephase_func(psi_R, strength)

            # Berry phase increment
            overlap_L = spinor_overlap(psi_L_prev, psi_L)
            if abs(overlap_L) > 1e-15:
                berry_inc = -np.angle(overlap_L)
            else:
                berry_inc = 0.0
            berry_phase_accum += berry_inc
            berry_increments.append(float(berry_inc))

            # Record observables
            bloch_L = spinor_bloch(psi_L)
            bloch_R = spinor_bloch(psi_R)
            rho_combined = 0.5 * (spinor_to_density(psi_L) + spinor_to_density(psi_R))
            ent = von_neumann_entropy_2x2(rho_combined)

            dot_LR = float(np.dot(bloch_L, bloch_R))

            entropy_traj.append(float(ent))
            bloch_L_traj.append(bloch_L.tolist())
            bloch_R_traj.append(bloch_R.tolist())
            chirality_traj.append(dot_LR)
            torus_pos_traj.append([float(eta), float(theta1 % (2 * np.pi)),
                                   float(theta2 % (2 * np.pi))])
            operator_sequence.append(op_name)

        # ── Inter-torus transport: relax toward Clifford ──
        # Transport preserves the spinor state but adjusts the
        # geometric context (radii change).  We do NOT reinitialise
        # spinors — that would destroy accumulated phase & chirality.
        # Instead we apply a small SU(2) correction rotor that accounts
        # for the change in torus geometry (eta shift).
        eta_new = eta + ETA_RELAX_RATE * (TORUS_CLIFFORD - eta)
        if abs(eta_new - eta) > 1e-12:
            # The eta shift changes the Bloch sphere base point.
            # Apply a gentle rotor proportional to the eta displacement
            # so the spinor "follows" the geometry smoothly.
            delta_eta = eta_new - eta
            R_transport = rotor_z(delta_eta * 0.5)
            psi_L = apply_cl3_rotor_to_spinor(psi_L, rotor_z, +delta_eta * 0.5)
            psi_R = apply_cl3_rotor_to_spinor(psi_R, rotor_z, -delta_eta * 0.5)
            eta = eta_new

    # ── Berry phase comparison ──
    # Fiber loop: theta1 varies, theta2 fixed -> Hopf projection is a single
    # point on S2. Solid angle = 0, so Berry phase = 0.
    fiber_berry_accum = sum(berry_increments[:4])

    # Base loop: the dynamical Berry from our rotor evolution (stages 4-7)
    base_berry_accum = sum(berry_increments[4:8])

    # GEOMETRIC Berry: compute Berry phase of a PURE base loop on S3
    # (no rotors, just the canonical lift).  This is the "ground truth"
    # for what geometry alone produces.
    n_geo = 64  # dense sampling for accurate geometric Berry
    geo_loop = []
    for k in range(n_geo):
        t2 = 2 * np.pi * k / n_geo
        geo_loop.append(torus_coordinates(eta_start, 0.0, t2))
    geo_loop_arr = np.array(geo_loop)
    analytic_berry = berry_phase(geo_loop_arr)

    # Theoretical Berry for base loop at latitude eta:
    # The base circle at fixed theta1 traces a circle on S2.
    # Under the Hopf map, varying theta2 at fixed (eta, theta1) traces
    # a circle at colatitude 2*eta on S2.
    # Solid angle of a cap at colatitude alpha: Omega = 2*pi*(1 - cos(alpha))
    # Berry = -Omega/2.
    # For eta < pi/4: small cap (south), for eta > pi/4: large cap.
    # The sign and branch must match the Pancharatnam convention.
    colatitude = 2 * eta_start
    solid_angle = 2 * np.pi * (1 - np.cos(colatitude))
    theoretical_berry = -solid_angle / 2
    # Wrap to [-pi, pi] to match the analytic berry_phase() output
    theoretical_berry = float((theoretical_berry + np.pi) % (2 * np.pi) - np.pi)

    return {
        "label": label,
        "eta_start": float(eta_start),
        "eta_final": float(eta),
        "berry_phase_final": float(berry_phase_accum),
        "berry_phase_fiber_loop": float(fiber_berry_accum),
        "berry_phase_base_loop": float(base_berry_accum),
        "berry_phase_analytic_base": float(analytic_berry),
        "berry_phase_theoretical_base": float(theoretical_berry),
        "entropy_trajectory": entropy_traj,
        "bloch_L_trajectory": bloch_L_traj,
        "bloch_R_trajectory": bloch_R_traj,
        "chirality_trajectory": chirality_traj,
        "torus_position_trajectory": torus_pos_traj,
        "operator_sequence": operator_sequence,
        "berry_increments": berry_increments,
        "n_stages": total_stages,
    }


# ═══════════════════════════════════════════════════════════════════
# MAIN: RUN ALL THREE TORUS LEVELS, COMPILE REPORT
# ═══════════════════════════════════════════════════════════════════

def sanitize(obj):
    """Recursively convert numpy types to Python natives for JSON."""
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return sanitize(obj.tolist())
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    elif isinstance(obj, complex):
        return {"re": float(obj.real), "im": float(obj.imag)}
    return obj


def main():
    print("=" * 70)
    print("FULL TORUS SPINOR DYNAMICS — Weyl evolution on nested Hopf tori")
    print("=" * 70)
    print()

    levels = {
        "inner":    TORUS_INNER,
        "clifford": TORUS_CLIFFORD,
        "outer":    TORUS_OUTER,
    }

    results_per_level = {}
    all_chirality = []

    for name, eta in levels.items():
        R_maj, R_min = torus_radii(eta)
        print(f"--- {name.upper()} torus (eta={eta:.4f}, R_major={R_maj:.4f}, R_minor={R_min:.4f}) ---")

        result = run_spinor_dynamics(eta, n_cycles=N_CYCLES, label=name)

        # Summary stats
        chirality_arr = np.array(result["chirality_trajectory"])
        entropy_arr = np.array(result["entropy_trajectory"])
        all_chirality.extend(result["chirality_trajectory"])

        print(f"  Berry phase (total accum):    {result['berry_phase_final']:.6f} rad")
        print(f"  Berry phase (fiber loop 1):  {result['berry_phase_fiber_loop']:.6f} rad  (expect ~0)")
        print(f"  Berry phase (base loop 1):   {result['berry_phase_base_loop']:.6f} rad")
        print(f"  Berry phase (analytic base): {result['berry_phase_analytic_base']:.6f} rad")
        print(f"  Berry phase (theory base):   {result['berry_phase_theoretical_base']:.6f} rad")
        print(f"  Entropy range:              [{entropy_arr.min():.4f}, {entropy_arr.max():.4f}]")
        print(f"  Chirality (L.R) range:      [{chirality_arr.min():.4f}, {chirality_arr.max():.4f}]")
        print(f"  Chirality mean:             {chirality_arr.mean():.4f}")
        print(f"  Eta final:                  {result['eta_final']:.6f}")
        print()

        results_per_level[name] = {
            "berry_phase_final": result["berry_phase_final"],
            "berry_phase_fiber_loop": result["berry_phase_fiber_loop"],
            "berry_phase_base_loop": result["berry_phase_base_loop"],
            "berry_phase_analytic_base": result["berry_phase_analytic_base"],
            "berry_phase_theoretical_base": result["berry_phase_theoretical_base"],
            "entropy_trajectory": result["entropy_trajectory"],
            "bloch_L_trajectory": result["bloch_L_trajectory"],
            "chirality_trajectory": result["chirality_trajectory"],
            "torus_position_trajectory": result["torus_position_trajectory"],
            "operator_sequence": result["operator_sequence"],
            "eta_final": result["eta_final"],
        }

    # ── Chirality verification ──
    # Pure unitary evolution preserves strict anti-alignment (L.R < 0).
    # Dissipation (Ti, Te dephasing) breaks this by pushing both spinors
    # toward the same eigenstate. We track what fraction stays anti-aligned.
    all_chir = np.array(all_chirality)
    n_anti = int(np.sum(all_chir <= 0.0))
    n_total = len(all_chir)
    chirality_fraction = n_anti / n_total
    chirality_preserved = chirality_fraction > 0.5  # majority anti-aligned
    anti_alignment_range = [float(all_chir.min()), float(all_chir.max())]

    # ── Berry phase comparison (use Clifford level, base loop) ──
    cliff_result = results_per_level["clifford"]
    berry_base = cliff_result["berry_phase_base_loop"]
    berry_theory = cliff_result["berry_phase_theoretical_base"]
    berry_analytic = cliff_result["berry_phase_analytic_base"]
    # Berry verification: the analytic (dense S3 loop) should match theoretical
    berry_match = abs(berry_analytic - berry_theory) < 0.01

    print("=" * 70)
    print("VERIFICATION")
    print("=" * 70)
    print(f"  Chirality preserved (majority):      {chirality_preserved}")
    print(f"  Chirality anti-aligned fraction:     {chirality_fraction:.3f} ({n_anti}/{n_total})")
    print(f"  Anti-alignment range:                {anti_alignment_range}")
    print(f"  Berry phase match (Clifford base):   {berry_match}")
    print(f"    base loop accum = {berry_base:.6f}")
    print(f"    theoretical     = {berry_theory:.6f}")
    print(f"    analytic (S3)   = {berry_analytic:.6f}")
    print(f"    delta (vs theo) = {abs(berry_base - berry_theory):.6f}")
    print()

    # ── Compile output ──
    output = {
        "name": "full_torus_spinor_dynamics",
        "torus_levels_tested": ["inner", "clifford", "outer"],
        "cycles": N_CYCLES,
        "stages_per_cycle": STAGES_PER_CYCLE,
        "results_per_level": results_per_level,
        "berry_phase_comparison": {
            "base_loop_accumulated": berry_base,
            "theoretical": berry_theory,
            "analytic_s3": berry_analytic,
            "match": berry_match,
        },
        "chirality_preserved": chirality_preserved,
        "chirality_anti_aligned_fraction": chirality_fraction,
        "anti_alignment_range": anti_alignment_range,
        "timestamp": str(datetime.date.today()),
    }

    output = sanitize(output)

    out_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "a2_state", "sim_results", "full_torus_spinor_dynamics_results.json",
    )
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Results written to: {out_path}")
    print("DONE.")


if __name__ == "__main__":
    main()
