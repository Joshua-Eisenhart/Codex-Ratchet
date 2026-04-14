#!/usr/bin/env python3
"""Classical baseline sim: Riemannian geodesic on real Grassmannian Gr(n,k).

Lane B classical baseline (numpy-only). NOT canonical.
Captures: principal-angle geodesic between two k-subspaces in R^n via
the SVD of Y_2^T Y_1 where Y_i are orthonormal frames.
Innately missing: complex structure. The real Grassmannian Gr_R(n,k)
has only real principal angles; Gr_C(n,k) Fubini-Study phases and the
associated Kahler structure are invisible.
"""
import json, os
import numpy as np

classification = "classical_baseline"
divergence_log = (
    "real Grassmannian geodesic uses only principal angles; "
    "complex structure J and Kahler form are absent; no phase"
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "SVD and QR"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
    "sympy": {"tried": False, "used": False, "reason": "numeric only"},
    "z3": {"tried": False, "used": False, "reason": "no admissibility"},
    "geomstats": {"tried": False, "used": False, "reason": "real-only baseline; no geomstats"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "pytorch": "supportive",
    "sympy": "supportive",
}


def stiefel_frame(A):
    # Orthonormal basis of column space of A via QR
    Q, _ = np.linalg.qr(A)
    return Q


def principal_angles(Y1, Y2):
    M = Y1.T @ Y2
    s = np.linalg.svd(M, compute_uv=False)
    s = np.clip(s, -1.0, 1.0)
    return np.arccos(s)


def grassmann_dist(Y1, Y2):
    angles = principal_angles(Y1, Y2)
    return float(np.sqrt(np.sum(angles ** 2)))


def run_positive_tests():
    results = {}
    np.random.seed(1)
    n, k = 6, 2
    A = np.random.randn(n, k)
    B = np.random.randn(n, k)
    Y1 = stiefel_frame(A)
    Y2 = stiefel_frame(B)
    # Identity distance
    results["self_distance_zero"] = grassmann_dist(Y1, Y1) < 1e-6
    # Symmetry
    results["symmetry"] = abs(grassmann_dist(Y1, Y2) - grassmann_dist(Y2, Y1)) < 1e-10
    # Right-multiplication by orthogonal matrix (frame change, same subspace)
    O = np.linalg.qr(np.random.randn(k, k))[0]
    results["gauge_invariance_right"] = grassmann_dist(Y1, Y1 @ O) < 1e-6
    # Principal angles in [0, pi/2]
    ang = principal_angles(Y1, Y2)
    results["angles_in_range"] = np.all((ang >= -1e-10) & (ang <= np.pi / 2 + 1e-10))
    return results


def run_negative_tests():
    results = {}
    np.random.seed(2)
    n, k = 5, 2
    Y1 = stiefel_frame(np.random.randn(n, k))
    Y2 = stiefel_frame(np.random.randn(n, k))
    Y3 = stiefel_frame(np.random.randn(n, k))
    # Distinct generic subspaces should have nonzero distance
    results["distinct_subspaces_nonzero"] = grassmann_dist(Y1, Y2) > 1e-3
    # Triangle inequality
    d12 = grassmann_dist(Y1, Y2)
    d23 = grassmann_dist(Y2, Y3)
    d13 = grassmann_dist(Y1, Y3)
    results["triangle_inequality"] = d13 <= d12 + d23 + 1e-8
    # Complex phase should NOT enter real computation — multiplying frame
    # by a real orthogonal matrix yields same subspace; classical sees this
    # fully. (We cannot test complex invariance because baseline is real.)
    results["frame_equivalence_detected"] = grassmann_dist(Y1, Y1 @ (-np.eye(k))) < 1e-10
    return results


def run_boundary_tests():
    results = {}
    n, k = 4, 2
    # Orthogonal subspaces: principal angles all pi/2
    Y1 = np.zeros((n, k)); Y1[0, 0] = 1.0; Y1[1, 1] = 1.0
    Y2 = np.zeros((n, k)); Y2[2, 0] = 1.0; Y2[3, 1] = 1.0
    ang = principal_angles(Y1, Y2)
    results["orthogonal_subspaces_pi_over_2"] = np.allclose(ang, np.pi / 2, atol=1e-10)
    # Very close subspaces: distance scales linearly in perturbation
    Y_base = np.zeros((n, k)); Y_base[0, 0] = 1.0; Y_base[1, 1] = 1.0
    eps = 1e-4
    pert = Y_base.copy(); pert[2, 0] = eps
    Y_pert = stiefel_frame(pert)
    d = grassmann_dist(Y_base, Y_pert)
    results["small_perturbation_distance"] = (d < 5 * eps) and (d > 0.1 * eps)
    return results


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "grassmannian_geodesic_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": [
            "complex structure J on Gr_C(n,k) not representable over reals",
            "no Fubini-Study / Kahler metric; metric is flat on tangent",
            "principal angles carry no phase information",
            "quantum state overlaps (|<psi|phi>|^2) cannot be recovered",
        ],
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "grassmannian_geodesic_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
