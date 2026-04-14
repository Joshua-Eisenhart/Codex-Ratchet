#!/usr/bin/env python3
"""Classical baseline sim: parallel transport on the 2-sphere S^2.

Lane B classical baseline (numpy-only). NOT canonical.
Captures: parallel transport of a tangent vector along a piecewise
great-circle loop on S^2 accumulates a rotation equal to the enclosed
solid angle (Gauss-Bonnet).
Innately missing: Berry phase. For the same closed loop, a quantum
state over S^2 picks up a geometric phase of Omega/2 (spin-1/2) — half
the solid angle with a sign reflecting spinor structure. The classical
transport holonomy is a real rotation of the tangent frame; the
quantum U(1) Berry phase and its half-factor are invisible.
"""
import json, os
import numpy as np

classification = "classical_baseline"
divergence_log = (
    "tangent parallel transport recovers solid angle Omega; Berry phase Omega/2 "
    "and the spin-1/2 sign ambiguity are not representable"
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "frame rotation on sphere"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
    "sympy": {"tried": False, "used": False, "reason": "numeric sufficient"},
    "z3": {"tried": False, "used": False, "reason": "no admissibility"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "pytorch": "supportive",
    "sympy": "supportive",
}


def normalize(v):
    return v / np.linalg.norm(v)


def rotate_axis_angle(v, axis, theta):
    a = normalize(axis)
    c, s = np.cos(theta), np.sin(theta)
    return v * c + np.cross(a, v) * s + a * np.dot(a, v) * (1 - c)


def transport_along_arc(vec_start, p_start, p_end, steps=200):
    """Levi-Civita transport of a tangent vector along the great-circle arc."""
    # Axis is p_start x p_end, angle is arc length
    axis = np.cross(p_start, p_end)
    if np.linalg.norm(axis) < 1e-14:
        return vec_start.copy()
    axis = normalize(axis)
    total = np.arccos(np.clip(np.dot(p_start, p_end), -1.0, 1.0))
    dtheta = total / steps
    p = p_start.copy()
    v = vec_start.copy()
    for _ in range(steps):
        # rotate base point and tangent by dtheta around axis
        p_new = rotate_axis_angle(p, axis, dtheta)
        v = rotate_axis_angle(v, axis, dtheta)
        # reproject v onto tangent space at p_new (should already be tangent)
        v = v - np.dot(v, p_new) * p_new
        p = p_new
    return v


def transport_loop_octant():
    """Transport around the spherical triangle N=(0,0,1), E=(1,0,0), F=(0,1,0).
    Solid angle = pi/2. Expect holonomy rotation angle = pi/2.
    """
    N = np.array([0.0, 0, 1.0])
    E = np.array([1.0, 0, 0])
    F = np.array([0.0, 1, 0])
    # Start with tangent vector at N pointing toward E
    v = np.array([1.0, 0, 0])  # tangent at N, points toward E
    v = transport_along_arc(v, N, E)
    v = transport_along_arc(v, E, F)
    v = transport_along_arc(v, F, N)
    return v


def angle_between_tangent(v_initial, v_final, base_point):
    # Both tangent to base_point; measure oriented angle in tangent plane
    v1 = v_initial - np.dot(v_initial, base_point) * base_point
    v2 = v_final - np.dot(v_final, base_point) * base_point
    v1 = normalize(v1); v2 = normalize(v2)
    cos = np.clip(np.dot(v1, v2), -1.0, 1.0)
    sin = np.dot(base_point, np.cross(v1, v2))
    return float(np.arctan2(sin, cos))


def run_positive_tests():
    results = {}
    N = np.array([0.0, 0, 1.0])
    v0 = np.array([1.0, 0, 0])
    v_final = transport_loop_octant()
    theta = angle_between_tangent(v0, v_final, N)
    # Solid angle of this triangle is pi/2 -> holonomy rotation ~pi/2
    results["octant_holonomy_pi_over_2"] = abs(abs(theta) - np.pi / 2) < 5e-2
    # Transport along a single arc and back is the identity
    E = np.array([1.0, 0, 0])
    v_there = transport_along_arc(v0, N, E)
    v_back = transport_along_arc(v_there, E, N)
    results["round_trip_identity"] = np.linalg.norm(v_back - v0) < 1e-6
    # Norm preserved under transport
    results["norm_preserved"] = abs(np.linalg.norm(v_final) - 1.0) < 1e-6
    return results


def run_negative_tests():
    results = {}
    N = np.array([0.0, 0, 1.0])
    v0 = np.array([1.0, 0, 0])
    v_final = transport_loop_octant()
    # Closed loop holonomy should NOT be zero (sphere has curvature)
    results["nonzero_curvature_holonomy"] = np.linalg.norm(v_final - v0) > 1e-2
    # Transport of a tangent vector must stay tangent at every step
    E = np.array([1.0, 0, 0])
    v_mid = transport_along_arc(v0, N, E, steps=1)
    # After one small step the new base is near N, check orthogonality mild
    results["stays_tangent_after_step"] = abs(np.dot(v_mid, E)) < 5e-1  # loose; measures radial leakage
    # Tangent vector cannot exit sphere ambient (still 3D but tangent)
    results["output_is_3d"] = v_final.shape == (3,)
    return results


def run_boundary_tests():
    results = {}
    # Half-sphere (hemispherical cap bounded by equator): solid angle 2*pi
    # Transport along the equator back to start — classically, holonomy = 0
    # (equator is a geodesic and closes up; axis is the pole).
    # A geodesic loop (equator) back to self: tangent returns unchanged.
    # Parameterize equator by angle.
    steps = 200
    ts = np.linspace(0, 2 * np.pi, steps, endpoint=False)
    p0 = np.array([1.0, 0, 0])
    v0 = np.array([0.0, 0, 1.0])  # tangent at p0 pointing to N
    v = v0.copy()
    p_prev = p0.copy()
    for i in range(1, steps + 1):
        t = (i % steps) * (2 * np.pi / steps)
        p = np.array([np.cos(t), np.sin(t), 0])
        v = transport_along_arc(v, p_prev, p, steps=1)
        p_prev = p
    # After going around the equator (a geodesic), tangent should be very close to v0
    results["equator_geodesic_trivial"] = np.linalg.norm(v - v0) < 5e-2
    # Zero-length loop: identity
    v_zero = transport_along_arc(v0, p0, p0)
    results["zero_loop_identity"] = np.allclose(v_zero, v0, atol=1e-10)
    return results


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "parallel_transport_s2_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": [
            "Berry phase = Omega/2 for spin-1/2 is null classically",
            "no U(1) fibre to support a geometric phase",
            "spinor sign ambiguity around closed loop unrepresentable",
            "holonomy is a real frame rotation, not a complex phase",
        ],
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "parallel_transport_s2_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
