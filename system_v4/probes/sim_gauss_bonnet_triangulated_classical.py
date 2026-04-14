#!/usr/bin/env python3
"""Classical baseline sim: Gauss-Bonnet on triangulated 2-surfaces.

Lane B classical baseline (numpy-only). NOT canonical.
Captures: sum of angle defects at vertices equals 2*pi * chi for a
closed triangulated surface (discrete Gauss-Bonnet).
Innately missing: spin structure. Orientability survives; a 2-sheeted
spin cover (Stiefel-Whitney class w2, Pin structure on non-orientable
cases) is invisible. Half-integer topological invariants do not appear.
"""
import json, os
import numpy as np

classification = "classical_baseline"
divergence_log = (
    "discrete Gauss-Bonnet recovers Euler characteristic but is blind to "
    "spin structure; w2, Pin lifts, and half-integer indices are invisible"
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "vector angles and sums"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
    "sympy": {"tried": False, "used": False, "reason": "numeric suffices"},
    "z3": {"tried": False, "used": False, "reason": "no admissibility"},
    "toponetx": {"tried": False, "used": False, "reason": "classical combinatorics only"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "pytorch": "supportive",
    "sympy": "supportive",
}


def vertex_angle(p_center, p_a, p_b):
    u = p_a - p_center
    v = p_b - p_center
    cos = np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v))
    cos = np.clip(cos, -1.0, 1.0)
    return float(np.arccos(cos))


def angle_defect_sum(V, F):
    # For each vertex, angle defect = 2*pi - sum of incident triangle angles
    total_defect = 0.0
    for vi in range(len(V)):
        theta = 0.0
        for f in F:
            if vi in f:
                others = [u for u in f if u != vi]
                theta += vertex_angle(V[vi], V[others[0]], V[others[1]])
        total_defect += (2.0 * np.pi - theta)
    return total_defect


def tetrahedron():
    # Regular tetrahedron vertices (chi = 2)
    V = np.array([
        [1.0, 1.0, 1.0],
        [1.0, -1.0, -1.0],
        [-1.0, 1.0, -1.0],
        [-1.0, -1.0, 1.0],
    ])
    F = [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)]
    return V, F


def octahedron():
    # Regular octahedron (chi = 2)
    V = np.array([
        [1.0, 0, 0], [-1.0, 0, 0],
        [0, 1.0, 0], [0, -1.0, 0],
        [0, 0, 1.0], [0, 0, -1.0],
    ])
    F = [(0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4),
         (0, 5, 2), (2, 5, 1), (1, 5, 3), (3, 5, 0)]
    return V, F


def euler_char(V, F):
    E = set()
    for f in F:
        f = sorted(f)
        E.add((f[0], f[1]))
        E.add((f[0], f[2]))
        E.add((f[1], f[2]))
    return len(V) - len(E) + len(F)


def run_positive_tests():
    results = {}
    for name, builder in [("tetrahedron", tetrahedron), ("octahedron", octahedron)]:
        V, F = builder()
        chi = euler_char(V, F)
        defect = angle_defect_sum(V, F)
        results[f"{name}_chi_is_2"] = chi == 2
        results[f"{name}_gauss_bonnet"] = abs(defect - 2.0 * np.pi * chi) < 1e-8
    return results


def run_negative_tests():
    results = {}
    # Corrupt one face — breaks the triangulation, Euler char changes
    V, F = tetrahedron()
    F_bad = F[:-1]  # remove a face, opens the surface
    chi_bad = euler_char(V, F_bad)
    results["open_surface_chi_not_2"] = chi_bad != 2
    # Flat triangle (planar) has zero angle defect at interior vertices
    V_flat = np.array([[0.0, 0, 0], [1.0, 0, 0], [0.5, 1.0, 0], [0.5, 0.3, 0]])
    F_flat = [(0, 1, 3), (1, 2, 3), (2, 0, 3)]
    # Interior vertex 3 should have defect ~0
    theta = 0.0
    for f in F_flat:
        if 3 in f:
            others = [u for u in f if u != 3]
            theta += vertex_angle(V_flat[3], V_flat[others[0]], V_flat[others[1]])
    results["flat_vertex_zero_defect"] = abs(2 * np.pi - theta) < 1e-8
    # Double-covering a face should break the simple-complex property
    F_dup = F + [F[0]]
    # Euler char changes when counting duplicate face
    results["duplicate_face_breaks_chi"] = euler_char(V, F_dup) != 2
    return results


def run_boundary_tests():
    results = {}
    # Scaling a tetrahedron should not change angle defect or Euler char
    V, F = tetrahedron()
    defect_1 = angle_defect_sum(V, F)
    defect_s = angle_defect_sum(V * 7.3, F)
    results["scale_invariance"] = abs(defect_1 - defect_s) < 1e-8
    # Rotation should not change angle defect
    theta = 0.9
    R = np.array([[np.cos(theta), -np.sin(theta), 0],
                  [np.sin(theta), np.cos(theta), 0],
                  [0, 0, 1]])
    defect_r = angle_defect_sum(V @ R.T, F)
    results["rotation_invariance"] = abs(defect_1 - defect_r) < 1e-8
    return results


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "gauss_bonnet_triangulated_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": [
            "Euler characteristic survives; spin structure does not",
            "cannot detect w2 Stiefel-Whitney obstruction to spin lift",
            "half-integer indices (Atiyah-Singer) invisible",
            "orientability not distinguished from admissibility of a Pin cover",
        ],
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "gauss_bonnet_triangulated_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
