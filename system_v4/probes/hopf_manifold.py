#!/usr/bin/env python3
"""
Hopf Manifold — Layer 0 Geometric Primitives
=============================================
Pure topology. No operators. No dynamics. No entropy.

S³ = SU(2) as unit quaternions, with the Hopf fibration:
  S¹ ↪ S³ → S²

This module implements:
  1. S³ points as unit quaternions / SU(2) matrices
  2. Hopf map π: S³ → S² (quaternion → Bloch vector)
  3. S¹ fiber extraction at each base point
  4. Toroidal coordinates on S³
  5. Density matrices on SU(2) (coherent states)
  6. Berry phase / holonomy computation

All functions are pure geometry — no physical interpretation.
"""

import numpy as np
from typing import Tuple


# ═══════════════════════════════════════════════════════════════════
# 1. S³ POINTS (Unit Quaternions / SU(2) Matrices)
# ═══════════════════════════════════════════════════════════════════

def quaternion_to_su2(q: np.ndarray) -> np.ndarray:
    """Convert unit quaternion (a, b, c, d) to SU(2) matrix.

    q = a + bi + cj + dk → [[a + bi, -c + di], [c + di, a - bi]]

    Args:
        q: Array of shape (4,) with |q| = 1.

    Returns:
        2×2 complex unitary matrix in SU(2).
    """
    a, b, c, d = q
    return np.array([
        [a + 1j * b, -c + 1j * d],
        [c + 1j * d,  a - 1j * b],
    ], dtype=complex)


def su2_to_quaternion(U: np.ndarray) -> np.ndarray:
    """Convert SU(2) matrix to unit quaternion (a, b, c, d).

    Inverse of quaternion_to_su2.
    """
    a = np.real(U[0, 0])
    b = np.imag(U[0, 0])
    c = np.real(U[1, 0])
    d = np.imag(U[1, 0])
    return np.array([a, b, c, d])


def random_s3_point(rng: np.random.Generator = None) -> np.ndarray:
    """Sample a uniformly random point on S³.

    Returns:
        Unit quaternion (a, b, c, d) with |q| = 1.
    """
    if rng is None:
        rng = np.random.default_rng()
    q = rng.normal(size=4)
    q /= np.linalg.norm(q)
    return q


def is_on_s3(q: np.ndarray, tol: float = 1e-10) -> bool:
    """Check if quaternion lies on S³ (|q| = 1)."""
    return abs(np.linalg.norm(q) - 1.0) < tol


def is_su2(U: np.ndarray, tol: float = 1e-10) -> bool:
    """Check if matrix is in SU(2): U†U = I and det(U) = 1."""
    identity_check = np.linalg.norm(U.conj().T @ U - np.eye(2)) < tol
    det_check = abs(np.linalg.det(U) - 1.0) < tol
    return identity_check and det_check


# ═══════════════════════════════════════════════════════════════════
# 2. HOPF MAP π: S³ → S² (Quaternion → Bloch Vector)
# ═══════════════════════════════════════════════════════════════════

def hopf_map(q: np.ndarray) -> np.ndarray:
    """Hopf map π: S³ → S².

    Maps unit quaternion to point on Bloch sphere (S²).
    Using the standard Hopf fibration:
      π(z₁, z₂) = (2·Re(z₁·z₂*), 2·Im(z₁·z₂*), |z₁|² - |z₂|²)
    where (z₁, z₂) ∈ ℂ² with |z₁|² + |z₂|² = 1.

    Args:
        q: Unit quaternion (a, b, c, d).

    Returns:
        (x, y, z) on S² with x² + y² + z² = 1.
    """
    a, b, c, d = q
    # Map quaternion to ℂ² pair: z₁ = a + ib, z₂ = c + id
    z1 = a + 1j * b
    z2 = c + 1j * d

    # Standard physics convention (matches Pauli/Bloch decomposition):
    #   x = 2·Re(z̄₁·z₂)
    #   y = 2·Im(z̄₁·z₂)   ← uses conjugate of z₁
    #   z = |z₁|² − |z₂|²
    x = 2 * np.real(np.conj(z1) * z2)
    y = 2 * np.imag(np.conj(z1) * z2)
    z = abs(z1)**2 - abs(z2)**2

    return np.array([x, y, z])


def is_on_s2(p: np.ndarray, tol: float = 1e-10) -> bool:
    """Check if point lies on S² (|p| = 1)."""
    return abs(np.linalg.norm(p) - 1.0) < tol


# ═══════════════════════════════════════════════════════════════════
# 3. S¹ FIBER EXTRACTION
# ═══════════════════════════════════════════════════════════════════

def fiber_action(q: np.ndarray, theta: float) -> np.ndarray:
    """U(1) fiber action: q → e^{iθ} · q.

    This is the Hopf fiber loop (vertical loop).
    Rotates along the fiber without changing the base point on S².

    Args:
        q: Unit quaternion on S³.
        theta: Angle in radians [0, 2π).

    Returns:
        Rotated quaternion (still on S³, same base point on S²).
    """
    a, b, c, d = q
    z1 = a + 1j * b
    z2 = c + 1j * d

    phase = np.exp(1j * theta)
    z1_new = phase * z1
    z2_new = phase * z2

    return np.array([
        np.real(z1_new), np.imag(z1_new),
        np.real(z2_new), np.imag(z2_new),
    ])


def sample_fiber(q: np.ndarray, n_points: int = 64) -> np.ndarray:
    """Sample n_points along the S¹ fiber through q.

    Returns:
        Array of shape (n_points, 4) — quaternions along the fiber.
    """
    thetas = np.linspace(0, 2 * np.pi, n_points, endpoint=False)
    return np.array([fiber_action(q, theta) for theta in thetas])


# ═══════════════════════════════════════════════════════════════════
# 4. LIFTED BASE LOOP (Horizontal Loop)
# ═══════════════════════════════════════════════════════════════════

def base_loop_point(theta: float, axis: np.ndarray = None) -> np.ndarray:
    """Generate a point on a great circle of S² parametrized by θ.

    Args:
        theta: Angle in radians.
        axis: Rotation axis on S². Default is equatorial circle.

    Returns:
        Point on S².
    """
    if axis is None:
        # Equatorial great circle in the xz-plane
        return np.array([np.sin(theta), 0.0, np.cos(theta)])
    # General great circle: rotate (0,0,1) around axis by theta
    axis = axis / np.linalg.norm(axis)
    cos_t = np.cos(theta)
    sin_t = np.sin(theta)
    # Rodrigues rotation of north pole around axis
    north = np.array([0.0, 0.0, 1.0])
    return (cos_t * north
            + sin_t * np.cross(axis, north)
            + (1 - cos_t) * np.dot(axis, north) * axis)


def lift_base_point(p: np.ndarray) -> np.ndarray:
    """Canonical horizontal lift: S² → S³.

    Lifts a point on S² to the canonical section of the Hopf bundle.
    For p = (x, y, z) on S², returns a quaternion q with π(q) = p.

    Uses the standard section with proper handling of all directions:
      If z > -1: q = (1/√(2(1+z))) · (1+z, 0, x, y)
      If z = -1: q = (0, 1, 0, 0)  (south pole)
    """
    x, y, z = p

    if z > -1 + 1e-12:
        norm = np.sqrt(2 * (1 + z))
        return np.array([(1 + z) / norm, 0.0, x / norm, y / norm])
    else:
        # South pole
        return np.array([0.0, 0.0, 1.0, 0.0])


def lifted_base_loop(n_points: int = 64, axis: np.ndarray = None) -> np.ndarray:
    """Generate a horizontal lift of a great circle on S² into S³.

    The key property: after 360° on S², the lift does NOT close in S³.
    It requires 720° to close (spinor double cover).

    Returns:
        Array of shape (n_points, 4) — quaternions along the lifted loop.
    """
    thetas = np.linspace(0, 2 * np.pi, n_points, endpoint=False)
    return np.array([lift_base_point(base_loop_point(theta, axis)) for theta in thetas])


def berry_phase(loop_on_s3: np.ndarray) -> float:
    """Compute the Berry phase (geometric phase) accumulated along a loop on S³.

    Uses the Pancharatnam connection: the Berry phase is the argument of
    the product of overlaps ⟨ψ_i|ψ_{i+1}⟩ around the loop.

    For a closed loop on S² with solid angle Ω, the Berry phase = −Ω/2.

    Args:
        loop_on_s3: Array of shape (N, 4) — quaternion path on S³.

    Returns:
        Berry phase in radians.
    """
    N = len(loop_on_s3)
    # Compute product of inner products ⟨ψ_i|ψ_{i+1}⟩
    product = 1.0 + 0j
    for i in range(N):
        j = (i + 1) % N
        q_i = loop_on_s3[i]
        q_j = loop_on_s3[j]
        # Convert to ℂ²
        z_i = np.array([q_i[0] + 1j * q_i[1], q_i[2] + 1j * q_i[3]])
        z_j = np.array([q_j[0] + 1j * q_j[1], q_j[2] + 1j * q_j[3]])
        inner = np.vdot(z_i, z_j)  # ⟨z_i|z_j⟩
        product *= inner / abs(inner)  # Track only the phase

    return float(-np.angle(product))  # Negate to match physics convention: Berry = -Ω/2


# ═══════════════════════════════════════════════════════════════════
# 5. TOROIDAL COORDINATES ON S³
# ═══════════════════════════════════════════════════════════════════

def torus_coordinates(eta: float, theta1: float, theta2: float) -> np.ndarray:
    """Parametrize S³ via nested tori.

    S³ decomposes into a family of flat tori T² parametrized by η ∈ [0, π/2]:
      q = (cos(η)·e^{iθ₁}, sin(η)·e^{iθ₂})

    Special cases:
      η = 0: degenerate torus (circle z₂ = 0)
      η = π/4: Clifford torus (maximal flat torus)
      η = π/2: degenerate torus (circle z₁ = 0)

    Args:
        eta: Torus parameter [0, π/2].
        theta1: Angle on first circle [0, 2π).
        theta2: Angle on second circle [0, 2π).

    Returns:
        Unit quaternion on S³.
    """
    z1 = np.cos(eta) * np.exp(1j * theta1)
    z2 = np.sin(eta) * np.exp(1j * theta2)
    return np.array([np.real(z1), np.imag(z1), np.real(z2), np.imag(z2)])


def clifford_torus_sample(n_theta1: int = 32, n_theta2: int = 32) -> np.ndarray:
    """Sample points on the Clifford torus (η = π/4).

    The Clifford torus is the unique flat, minimal torus in S³
    that divides S³ into two congruent solid tori.

    Returns:
        Array of shape (n_theta1 * n_theta2, 4).
    """
    eta = np.pi / 4
    points = []
    for t1 in np.linspace(0, 2 * np.pi, n_theta1, endpoint=False):
        for t2 in np.linspace(0, 2 * np.pi, n_theta2, endpoint=False):
            points.append(torus_coordinates(eta, t1, t2))
    return np.array(points)


# ═══════════════════════════════════════════════════════════════════
# 6. DENSITY MATRICES ON SU(2)
# ═══════════════════════════════════════════════════════════════════

def coherent_state_density(q: np.ndarray) -> np.ndarray:
    """Create a pure-state density matrix from an S³ point.

    ρ = |ψ⟩⟨ψ| where |ψ⟩ = (z₁, z₂)ᵀ ∈ ℂ².

    Args:
        q: Unit quaternion on S³.

    Returns:
        2×2 density matrix (rank 1, trace 1, PSD).
    """
    a, b, c, d = q
    psi = np.array([a + 1j * b, c + 1j * d], dtype=complex)
    rho = np.outer(psi, np.conj(psi))
    return rho


def bloch_to_density(p: np.ndarray) -> np.ndarray:
    """Convert Bloch vector to density matrix.

    ρ = (I + p·σ) / 2 where σ = (σ_x, σ_y, σ_z).
    """
    sx = np.array([[0, 1], [1, 0]], dtype=complex)
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    sz = np.array([[1, 0], [0, -1]], dtype=complex)
    return (np.eye(2, dtype=complex) + p[0] * sx + p[1] * sy + p[2] * sz) / 2


def density_to_bloch(rho: np.ndarray) -> np.ndarray:
    """Extract Bloch vector from 2×2 density matrix.

    p = (Tr(ρ·σ_x), Tr(ρ·σ_y), Tr(ρ·σ_z)).
    """
    sx = np.array([[0, 1], [1, 0]], dtype=complex)
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    sz = np.array([[1, 0], [0, -1]], dtype=complex)
    return np.array([
        np.real(np.trace(rho @ sx)),
        np.real(np.trace(rho @ sy)),
        np.real(np.trace(rho @ sz)),
    ])


def von_neumann_entropy_2x2(rho: np.ndarray) -> float:
    """Von Neumann entropy S(ρ) = -Tr(ρ log₂ ρ) for 2×2 density matrix."""
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > 1e-15]
    return float(-np.sum(evals * np.log2(evals)))


# ═══════════════════════════════════════════════════════════════════
# 7. STEREOGRAPHIC PROJECTION (for visualization)
# ═══════════════════════════════════════════════════════════════════

def stereographic_s3_to_r3(q: np.ndarray) -> np.ndarray:
    """Stereographic projection S³ → ℝ³ (from north pole).

    Projects from (0,0,0,1) pole:
      (a, b, c, d) → (a, b, c) / (1 - d)

    Args:
        q: Unit quaternion on S³.

    Returns:
        Point in ℝ³.
    """
    a, b, c, d = q
    if abs(1 - d) < 1e-12:
        return np.array([1e6, 1e6, 1e6])  # near pole → infinity
    scale = 1.0 / (1 - d)
    return np.array([a * scale, b * scale, c * scale])


# ═══════════════════════════════════════════════════════════════════
# 8. NESTED HOPF TORI
# ═══════════════════════════════════════════════════════════════════

# Three nested tori at different latitudes
TORUS_INNER = np.pi / 8     # η = π/8: small inner torus
TORUS_CLIFFORD = np.pi / 4  # η = π/4: Clifford (maximal flat)
TORUS_OUTER = 3 * np.pi / 8 # η = 3π/8: large outer torus

NESTED_TORI = [TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER]

def torus_radii(eta: float) -> Tuple[float, float]:
    """Major and minor radii of the torus T²(η) in S³.

    R_major = cos(η)  (radius of z₁ circle)
    R_minor = sin(η)  (radius of z₂ circle)

    At η = π/4 (Clifford): R_major = R_minor = 1/√2 (flat, symmetric).
    """
    return float(np.cos(eta)), float(np.sin(eta))


def sample_nested_torus(eta: float, n_theta1: int = 32,
                        n_theta2: int = 32) -> np.ndarray:
    """Sample points on the torus T²(η) in S³.

    Returns:
        Array of shape (n_theta1 * n_theta2, 4).
    """
    points = []
    for t1 in np.linspace(0, 2 * np.pi, n_theta1, endpoint=False):
        for t2 in np.linspace(0, 2 * np.pi, n_theta2, endpoint=False):
            points.append(torus_coordinates(eta, t1, t2))
    return np.array(points)


def inter_torus_transport(q: np.ndarray, eta_from: float,
                          eta_to: float) -> np.ndarray:
    """Transport a point from torus T²(η_from) to T²(η_to).

    Preserves the angular coordinates (θ₁, θ₂) while changing
    the torus latitude η. This is a smooth deformation, not a jump.

    Args:
        q: Unit quaternion on T²(η_from).
        eta_from: Source torus latitude.
        eta_to: Target torus latitude.

    Returns:
        Unit quaternion on T²(η_to) with same angles.
    """
    # Extract angles from current point
    a, b, c, d = q
    z1 = a + 1j * b
    z2 = c + 1j * d

    # Extract phases
    r1 = abs(z1)
    r2 = abs(z2)
    theta1 = np.angle(z1) if r1 > 1e-12 else 0.0
    theta2 = np.angle(z2) if r2 > 1e-12 else 0.0

    # Reconstruct at new η
    return torus_coordinates(eta_to, theta1, theta2)


def torus_transport_fraction(eta_from: float, eta_to: float) -> float:
    """Normalized distance between two named torus latitudes."""
    return float(min(abs(eta_to - eta_from) / (np.pi / 4), 1.0))


def s3_interpolate(q0: np.ndarray, q1: np.ndarray, alpha: float) -> np.ndarray:
    """Conservative interpolation on S^3 by reprojecting to the sphere."""
    alpha = float(np.clip(alpha, 0.0, 1.0))
    q = (1.0 - alpha) * q0 + alpha * q1
    norm = np.linalg.norm(q)
    if norm < 1e-12:
        return q0.copy()
    return q / norm


def inter_torus_transport_partial(q: np.ndarray, eta_from: float,
                                  eta_to: float, alpha: float) -> np.ndarray:
    """Partial transport between nested tori along a stable S^3 path."""
    q_target = inter_torus_transport(q, eta_from, eta_to)
    return s3_interpolate(q, q_target, alpha)


# ═══════════════════════════════════════════════════════════════════
# 9. WEYL SPINORS (LEFT / RIGHT)
# ═══════════════════════════════════════════════════════════════════

def left_weyl_spinor(q: np.ndarray) -> np.ndarray:
    """Left Weyl spinor from S³ point.

    ψ_L = (z₁, z₂)ᵀ  [fundamental SU(2) representation]

    Under SU(2) rotation U:  ψ_L → U · ψ_L
    Under fiber action e^{iθ}:  ψ_L → e^{+iθ} ψ_L  (positive phase)
    """
    a, b, c, d = q
    return np.array([a + 1j * b, c + 1j * d], dtype=complex)


def right_weyl_spinor(q: np.ndarray) -> np.ndarray:
    """Right Weyl spinor from S³ point.

    ψ_R = (z̄₂, -z̄₁)ᵀ  [conjugate SU(2) representation]

    Under SU(2) rotation U:  ψ_R → U* · ψ_R  (complex conjugate)
    Under fiber action e^{iθ}:  ψ_R → e^{-iθ} ψ_R  (negative phase)

    This is the charge-conjugate spinor: ψ_R = iσ₂ · ψ_L*
    """
    a, b, c, d = q
    z1 = a + 1j * b
    z2 = c + 1j * d
    return np.array([np.conj(z2), -np.conj(z1)], dtype=complex)


def left_density(q: np.ndarray) -> np.ndarray:
    """Density matrix from left Weyl spinor: ρ_L = |ψ_L⟩⟨ψ_L|."""
    psi = left_weyl_spinor(q)
    return np.outer(psi, np.conj(psi))


def right_density(q: np.ndarray) -> np.ndarray:
    """Density matrix from right Weyl spinor: ρ_R = |ψ_R⟩⟨ψ_R|."""
    psi = right_weyl_spinor(q)
    return np.outer(psi, np.conj(psi))


def rotate_left(psi_L: np.ndarray, U: np.ndarray) -> np.ndarray:
    """Rotate left Weyl spinor: ψ_L → U · ψ_L."""
    return U @ psi_L


def rotate_right(psi_R: np.ndarray, U: np.ndarray) -> np.ndarray:
    """Rotate right Weyl spinor: ψ_R → U* · ψ_R."""
    return np.conj(U) @ psi_R


def fiber_phase_left(psi_L: np.ndarray, theta: float) -> np.ndarray:
    """Fiber action on left spinor: ψ_L → e^{+iθ} ψ_L."""
    return np.exp(1j * theta) * psi_L


def fiber_phase_right(psi_R: np.ndarray, theta: float) -> np.ndarray:
    """Fiber action on right spinor: ψ_R → e^{-iθ} ψ_R."""
    return np.exp(-1j * theta) * psi_R
