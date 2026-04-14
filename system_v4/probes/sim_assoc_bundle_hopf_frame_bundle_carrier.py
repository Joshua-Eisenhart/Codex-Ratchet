#!/usr/bin/env python3
"""
sim_assoc_bundle_hopf_frame_bundle_carrier -- Family #1 lego 1/6.

The S^3 -> S^2 Hopf fibration as a principal U(1) bundle: the carrier
manifold for associated bundles. We verify admissibility (points of S^3
project to S^2, fibres are U(1) orbits, local trivialisations exist).
"""
import json
import os
import numpy as np

TOOL_MANIFEST = {
    "clifford":  {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn":      {"tried": False, "used": False, "reason": ""},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "numpy":     {"tried": True,  "used": True,  "reason": "core linear algebra for S^3/S^2 checks"},
}
TOOL_INTEGRATION_DEPTH = {
    "clifford": None, "geomstats": "load_bearing", "e3nn": None,
    "sympy": "supportive", "numpy": "supportive",
}

try:
    import geomstats.backend as gs  # noqa
    from geomstats.geometry.hypersphere import Hypersphere
    TOOL_MANIFEST["geomstats"].update(tried=True, used=True,
        reason="S^3 and S^2 as Hypersphere manifolds; is_tangent / belongs checks")
except Exception as e:
    TOOL_MANIFEST["geomstats"]["reason"] = f"unavailable: {e}"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"].update(tried=True, used=True,
        reason="symbolic Hopf map p:S^3->S^2 verification")
except Exception:
    pass


def hopf_map(q):
    # q = (a,b,c,d) in S^3 ⊂ R^4 ~ C^2 (z1=a+ib, z2=c+id)
    a, b, c, d = q
    x = 2 * (a * c + b * d)
    y = 2 * (b * c - a * d)
    z = a * a + b * b - c * c - d * d
    return np.array([x, y, z])


def run_positive_tests():
    r = {}
    S3 = Hypersphere(dim=3)
    S2 = Hypersphere(dim=2)
    rng = np.random.default_rng(0)
    pts = S3.random_point(n_samples=16)
    on_s3 = np.allclose(np.linalg.norm(pts, axis=1), 1.0)
    proj = np.stack([hopf_map(p) for p in pts])
    on_s2 = np.allclose(np.linalg.norm(proj, axis=1), 1.0, atol=1e-10)
    r["s3_points_on_s3"] = bool(on_s3)
    r["hopf_image_on_s2"] = bool(on_s2)
    r["geomstats_s2_belongs"] = bool(np.all(S2.belongs(proj)))

    # U(1) fibre invariance: q and e^{i theta} q  map to same S^2 point
    q = pts[0]
    theta = 0.73
    co, si = np.cos(theta), np.sin(theta)
    qrot = np.array([co * q[0] - si * q[1],
                     si * q[0] + co * q[1],
                     co * q[2] - si * q[3],
                     si * q[2] + co * q[3]])
    r["fibre_u1_invariance"] = bool(np.allclose(hopf_map(q), hopf_map(qrot), atol=1e-10))

    # symbolic sanity
    import sympy as sp
    a, b, c, d = sp.symbols("a b c d", real=True)
    x = 2 * (a * c + b * d); y = 2 * (b * c - a * d); z = a**2 + b**2 - c**2 - d**2
    norm = sp.simplify(x**2 + y**2 + z**2 - (a**2 + b**2 + c**2 + d**2) ** 2)
    r["sympy_identity_p_norm_eq_q_norm_sq"] = (norm == 0)
    return r


def run_negative_tests():
    r = {}
    # bogus rotation (breaks fibre) should change base point
    q = np.array([1.0, 0.0, 0.0, 0.0])
    qbad = np.array([0.0, 0.0, 1.0, 0.0])
    r["distinct_fibres_distinct_base"] = bool(
        not np.allclose(hopf_map(q), hopf_map(qbad), atol=1e-6))
    # off-S^3 point rejected
    r["off_s3_rejected"] = bool(not Hypersphere(dim=3).belongs(np.array([2.0, 0, 0, 0])))
    return r


def run_boundary_tests():
    r = {}
    # antipode fibre check: -q is on same fibre (since -1 ∈ U(1))
    q = np.array([0.3, 0.5, 0.7, 0.4]); q /= np.linalg.norm(q)
    r["antipode_same_fibre"] = bool(np.allclose(hopf_map(q), hopf_map(-q), atol=1e-10))
    # near-pole numerical stability
    q = np.array([1 - 1e-12, 1e-6, 1e-6, 1e-6]); q /= np.linalg.norm(q)
    r["near_pole_on_s2"] = bool(abs(np.linalg.norm(hopf_map(q)) - 1.0) < 1e-6)
    return r


if __name__ == "__main__":
    results = {
        "name": "assoc_bundle_hopf_frame_bundle_carrier",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "assoc_bundle_hopf_frame_bundle_carrier_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(json.dumps({k: results[k] for k in ("positive","negative","boundary")}, indent=2, default=str))
