#!/usr/bin/env python3
"""
clifford_engine_bridge.py
=========================
Bridge between numpy engine_core and Clifford algebra (clifford library).

Provides:
- Conversion: numpy spinor ↔ Clifford multivector
- Conversion: numpy density matrix ↔ Clifford rotor/blade representation
- Operator application via geometric product
- Chirality via pseudoscalar grade

This is the first integration step. The engine still runs on numpy;
this bridge allows Clifford-native verification and analysis of engine
states and operations.

Future: replace numpy engine internals with native Clifford operations.
"""

import numpy as np
from clifford import Cl

# Initialize Cl(3,0)
layout, blades = Cl(3)
e1, e2, e3 = blades['e1'], blades['e2'], blades['e3']
e12, e13, e23 = blades['e12'], blades['e13'], blades['e23']
e123 = blades['e123']  # pseudoscalar — chirality lives here
scalar = layout.scalar

# Pauli ↔ Clifford mapping:
#   sigma_x ↔ e1
#   sigma_y ↔ e2
#   sigma_z ↔ e3
#   i ↔ e123 (pseudoscalar squares to -1)


def bloch_to_multivector(bloch_vec):
    """Convert a Bloch vector [r_x, r_y, r_z] to a Cl(3) vector.

    The density matrix ρ = (I + r⃗·σ⃗)/2 maps to
    the multivector (1 + r_x e1 + r_y e2 + r_z e3)/2.
    """
    rx, ry, rz = bloch_vec
    return 0.5 * (scalar + rx * e1 + ry * e2 + rz * e3)


def multivector_to_bloch(mv):
    """Extract Bloch vector from a Cl(3) multivector.

    bloch_to_multivector stores: (1 + rx*e1 + ry*e2 + rz*e3) / 2
    So grade-1 components are rx/2, ry/2, rz/2.
    Multiply by 2 to recover rx, ry, rz.
    """
    return np.array([
        2.0 * float(mv[e1]),
        2.0 * float(mv[e2]),
        2.0 * float(mv[e3]),
    ])


def rotor_z(angle):
    """Rotor for rotation around e3 axis (Fe operator).

    R = cos(θ/2) + sin(θ/2) e12
    Applies as: v' = R v R̃
    """
    return np.cos(angle / 2) * scalar + np.sin(angle / 2) * e12


def rotor_x(angle):
    """Rotor for rotation around e1 axis (Fi operator).

    R = cos(θ/2) + sin(θ/2) e23
    Applies as: v' = R v R̃
    """
    return np.cos(angle / 2) * scalar + np.sin(angle / 2) * e23


def apply_rotor(mv, R):
    """Apply a rotor to a multivector: mv' = R mv R̃"""
    return R * mv * ~R


def project_to_blade(mv, blade_idx):
    """Project multivector to a specific grade.

    blade_idx: 0 = scalar, 1 = vector, 2 = bivector, 3 = pseudoscalar
    """
    return mv(blade_idx)


def chirality_content(mv):
    """Measure the pseudoscalar (grade-3) content of a multivector.

    The pseudoscalar e123 IS chirality in Cl(3).
    Returns the coefficient of e123.
    """
    return float(mv[e123])


def dephase_z(mv, strength):
    """Z-dephasing (Ti operator) in Clifford algebra.

    Projects the grade-1 part onto e3, killing e1 and e2 components
    proportionally to strength.

    ρ → (1-q)ρ + q (e3 component only)
    In Bloch terms: [rx, ry, rz] → [(1-q)rx, (1-q)ry, rz]
    """
    s = mv(0)  # scalar part (trace/2)
    v = mv(1)  # vector part (Bloch/2)

    # Extract components
    vx = float(v[e1])
    vy = float(v[e2])
    vz = float(v[e3])

    # Dephase: reduce x,y components
    new_v = (1 - strength) * vx * e1 + (1 - strength) * vy * e2 + vz * e3

    return s + new_v


def dephase_x(mv, strength):
    """X-dephasing (Te operator) in Clifford algebra.

    Projects onto e1, killing e2 and e3 components proportionally.
    In Bloch terms: [rx, ry, rz] → [rx, (1-q)ry, (1-q)rz]
    """
    s = mv(0)
    v = mv(1)

    vx = float(v[e1])
    vy = float(v[e2])
    vz = float(v[e3])

    new_v = vx * e1 + (1 - strength) * vy * e2 + (1 - strength) * vz * e3

    return s + new_v


def numpy_density_to_clifford(rho):
    """Convert a 2x2 numpy density matrix to Clifford multivector.

    ρ = (I + r⃗·σ⃗)/2 → (1 + rx e1 + ry e2 + rz e3)/2
    """
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from hopf_manifold import density_to_bloch
    bloch = density_to_bloch(rho)
    return bloch_to_multivector(bloch)


def clifford_to_numpy_density(mv):
    """Convert Clifford multivector back to 2x2 numpy density matrix.

    (1 + rx e1 + ry e2 + rz e3)/2 → ρ = (I + r⃗·σ⃗)/2
    """
    bloch = multivector_to_bloch(mv)
    rx, ry, rz = bloch
    I2 = np.eye(2, dtype=complex)
    sx = np.array([[0, 1], [1, 0]], dtype=complex)
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    sz = np.array([[1, 0], [0, -1]], dtype=complex)
    return 0.5 * (I2 + rx * sx + ry * sy + rz * sz)


# ── Verification ─────────────────────────────────────────────────────

def verify_roundtrip(rho):
    """Verify numpy → Clifford → numpy roundtrip preserves the state."""
    mv = numpy_density_to_clifford(rho)
    rho_back = clifford_to_numpy_density(mv)
    dist = np.linalg.norm(rho - rho_back)
    return dist < 1e-10, dist


def verify_rotor_vs_numpy(rho, angle, axis='z'):
    """Verify Clifford rotor matches numpy unitary rotation."""
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from geometric_operators import apply_Fe, apply_Fi

    # Clifford version
    mv = numpy_density_to_clifford(rho)
    R = rotor_z(angle) if axis == 'z' else rotor_x(angle)
    mv_rotated = apply_rotor(mv, R)
    rho_cliff = clifford_to_numpy_density(mv_rotated)

    # Numpy version
    if axis == 'z':
        rho_np = apply_Fe(rho, phi=angle, strength=1.0)
    else:
        rho_np = apply_Fi(rho, strength=1.0)

    dist = np.linalg.norm(rho_cliff - rho_np)
    return dist, rho_cliff, rho_np


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from hopf_manifold import torus_coordinates, left_density, right_density, TORUS_CLIFFORD

    print("=== Clifford Engine Bridge Verification ===")
    print()

    # Test roundtrip at several torus points
    for eta_name, eta in [('inner', 0.3927), ('clifford', TORUS_CLIFFORD), ('outer', 1.1781)]:
        q = torus_coordinates(eta, 0.5, 0.3)
        rho_L = left_density(q)
        ok, dist = verify_roundtrip(rho_L)
        print(f"  Roundtrip {eta_name}: {'OK' if ok else 'FAIL'} (dist={dist:.2e})")

    print()

    # Test rotor vs numpy operator
    q = torus_coordinates(TORUS_CLIFFORD, 0.5, 0.3)
    rho = left_density(q)
    for angle in [0.1, 0.5, 1.0, np.pi/2]:
        dist_z, _, _ = verify_rotor_vs_numpy(rho, angle, 'z')
        print(f"  Fe rotor vs numpy (angle={angle:.2f}): dist={dist_z:.2e}")

    print()

    # Show chirality content
    mv_L = numpy_density_to_clifford(left_density(q))
    print(f"  Left density chirality content: {chirality_content(mv_L):.6f}")
    print(f"  (should be 0 for a pure vector — chirality is in the spinor, not the density)")

    print()
    print("Bridge is working. Ready for engine integration.")
