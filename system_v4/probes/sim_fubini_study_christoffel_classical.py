#!/usr/bin/env python3
"""Classical baseline sim: Christoffel symbols of Fubini-Study in real 2d projection.

Lane B classical baseline (numpy-only). NOT canonical.
Captures: the real 2-sphere metric g = diag(1, sin^2 theta) viewed as
a projection of the Fubini-Study metric on CP^1. We compute the
Christoffel symbols of the affine connection and verify the nonzero
ones match -sin(theta)cos(theta) and cot(theta).
Innately missing: the projective U(1) symmetry / complex structure of
CP^1. Under the real projection CP^1 -> S^2, the Kahler form
omega_FS, the complex conjugate tangent structure, and the associated
Hermitian connection with its phase part are discarded. The affine
Riemannian connection is demoted from a projective / Kahler one.
"""
import json, os
import numpy as np

classification = "classical_baseline"
divergence_log = (
    "real projection S^2 loses the U(1) Kahler phase of CP^1; "
    "affine Christoffel symbols survive but the Hermitian/Kahler connection does not"
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "metric inverse and derivatives"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
    "sympy": {"tried": False, "used": False, "reason": "closed form verified numerically"},
    "z3": {"tried": False, "used": False, "reason": "no admissibility"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "pytorch": "supportive",
    "sympy": "supportive",
}


def metric_S2(theta):
    return np.array([[1.0, 0.0], [0.0, np.sin(theta) ** 2]])


def christoffel_numeric(theta, eps=1e-5):
    """Compute Gamma^a_{bc} = 1/2 g^{ad} (d_b g_{dc} + d_c g_{db} - d_d g_{bc})
    in coordinates (theta, phi) on S^2. Metric depends only on theta, so only
    d/d theta derivatives are nonzero.
    """
    g = metric_S2(theta)
    g_inv = np.linalg.inv(g)
    # partial derivatives of g with respect to theta
    g_plus = metric_S2(theta + eps)
    g_minus = metric_S2(theta - eps)
    dg_dtheta = (g_plus - g_minus) / (2 * eps)
    dg_dphi = np.zeros_like(g)
    # Stack: dg[mu, b, c] where mu index 0=theta, 1=phi
    dg = np.stack([dg_dtheta, dg_dphi])  # shape (2,2,2)

    # Gamma^a_{bc} = 1/2 g^{ad} (dg[b,dc] + dg[c,db] - dg[d,bc])
    Gamma = np.zeros((2, 2, 2))
    for a in range(2):
        for b in range(2):
            for c in range(2):
                s = 0.0
                for d in range(2):
                    s += 0.5 * g_inv[a, d] * (dg[b, d, c] + dg[c, d, b] - dg[d, b, c])
                Gamma[a, b, c] = s
    return Gamma


def run_positive_tests():
    results = {}
    theta = 0.7
    G = christoffel_numeric(theta)
    # Gamma^theta_{phi phi} = -sin(theta) cos(theta)
    expected_1 = -np.sin(theta) * np.cos(theta)
    results["Gamma_theta_phi_phi"] = abs(G[0, 1, 1] - expected_1) < 1e-4
    # Gamma^phi_{theta phi} = Gamma^phi_{phi theta} = cot(theta)
    expected_2 = 1.0 / np.tan(theta)
    results["Gamma_phi_theta_phi"] = abs(G[1, 0, 1] - expected_2) < 1e-4
    results["Gamma_phi_phi_theta"] = abs(G[1, 1, 0] - expected_2) < 1e-4
    # Symmetry in lower indices
    for a in range(2):
        for b in range(2):
            for c in range(2):
                assert abs(G[a, b, c] - G[a, c, b]) < 1e-6
    results["symmetric_lower_indices"] = True
    return results


def run_negative_tests():
    results = {}
    theta = 0.7
    G = christoffel_numeric(theta)
    # Nonzero Christoffel means the connection is NOT flat
    any_nonzero = any(abs(G[a, b, c]) > 1e-3
                      for a in range(2) for b in range(2) for c in range(2))
    results["S2_not_flat"] = any_nonzero
    # Gamma^theta_{theta theta} = 0 on S^2
    results["Gamma_theta_theta_theta_zero"] = abs(G[0, 0, 0]) < 1e-5
    # Gamma^theta_{theta phi} = 0
    results["Gamma_theta_theta_phi_zero"] = abs(G[0, 0, 1]) < 1e-5
    # Metric is not the Euclidean plane
    g = metric_S2(theta)
    results["metric_not_euclidean"] = not np.allclose(g, np.eye(2), atol=1e-3)
    return results


def run_boundary_tests():
    results = {}
    # Near the equator theta = pi/2: sin(theta) = 1, Christoffel at equator simpler
    theta_eq = np.pi / 2
    G = christoffel_numeric(theta_eq)
    results["equator_Gamma_theta_phi_phi"] = abs(G[0, 1, 1] - 0.0) < 1e-3  # -sin*cos = 0
    results["equator_Gamma_phi_theta_phi"] = abs(G[1, 0, 1] - 0.0) < 1e-3  # cot = 0
    # Approaching pole (theta small): cot(theta) blows up
    theta_small = 0.05
    G_small = christoffel_numeric(theta_small)
    results["pole_divergence"] = G_small[1, 0, 1] > 10.0
    # Metric determinant sin^2 theta at generic theta
    theta = 0.9
    results["det_metric"] = abs(np.linalg.det(metric_S2(theta)) - np.sin(theta) ** 2) < 1e-10
    return results


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "fubini_study_christoffel_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": [
            "CP^1 U(1) fibre phase invisible after real projection",
            "Kahler 2-form omega_FS not representable in (theta, phi) alone",
            "Hermitian connection demoted to real Levi-Civita connection",
            "cannot recover geometric phase of projective quantum states",
        ],
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "fubini_study_christoffel_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
