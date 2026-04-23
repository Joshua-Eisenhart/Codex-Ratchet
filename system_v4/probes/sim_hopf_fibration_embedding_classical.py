#!/usr/bin/env python3
"""Classical baseline sim: Hopf fibration embedding S^3 -> S^2.

Lane B classical baseline (numpy-only). NOT canonical.
Captures: the real stereographic-like map (a,b,c,d) in S^3 ->
(2(ac + bd), 2(bc - ad), a^2 + b^2 - c^2 - d^2) in S^2.
Innately missing: the U(1) phase fibre coordinate. The map is
many-to-one and the classical embedding discards the overall phase
(rotation in the fibre). Quantum state = ray; classical here = point.
"""
import json, os
import numpy as np

classification = "classical_baseline"
divergence_log = (
    "real Hopf map drops U(1) fibre phase; "
    "preimages differing by overall phase map to the same base point"
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "real coordinate embedding"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline only"},
    "sympy": {"tried": False, "used": False, "reason": "numeric suffices"},
    "z3": {"tried": False, "used": False, "reason": "no admissibility"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "pytorch": "supportive",
    "sympy": "supportive",
}


def hopf(x):
    a, b, c, d = x
    return np.array([2 * (a * c + b * d), 2 * (b * c - a * d),
                     a * a + b * b - c * c - d * d])


def rand_S3(n):
    v = np.random.randn(n, 4)
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    return v


def run_positive_tests():
    results = {}
    np.random.seed(0)
    pts = rand_S3(50)
    images = np.array([hopf(p) for p in pts])
    norms = np.linalg.norm(images, axis=1)
    results["image_on_S2"] = np.allclose(norms, 1.0, atol=1e-10)
    # Phase invariance: (a,b,c,d) and rotated fibre element map to same base
    # Fibre action: (a,b,c,d) -> (a cos t - b sin t, a sin t + b cos t,
    #                              c cos t - d sin t, c sin t + d cos t)
    t = 0.37
    p = pts[0]
    ct, st = np.cos(t), np.sin(t)
    p2 = np.array([p[0] * ct - p[1] * st, p[0] * st + p[1] * ct,
                   p[2] * ct - p[3] * st, p[2] * st + p[3] * ct])
    results["fibre_invariance"] = np.allclose(hopf(p), hopf(p2), atol=1e-10)
    # Standard fibre: (cos t, sin t, 0, 0) all map to (0,0,1)
    ts = np.linspace(0, 2 * np.pi, 8, endpoint=False)
    fibre = np.array([hopf(np.array([np.cos(t), np.sin(t), 0, 0])) for t in ts])
    results["standard_fibre_collapses"] = np.allclose(fibre - np.array([0, 0, 1]), 0, atol=1e-12)
    return results


def run_negative_tests():
    results = {}
    # Map is many-to-one: two antipodal points on a fibre map to same base
    p = np.array([1.0, 0, 0, 0])
    q = -p
    results["antipodes_same_image"] = np.allclose(hopf(p), hopf(q), atol=1e-12)
    # A point not on S^3 must NOT produce a unit image
    bad = np.array([2.0, 0, 0, 0])
    results["non_S3_bad_image_norm"] = abs(np.linalg.norm(hopf(bad)) - 1.0) > 1e-3
    # Hopf map should not be injective (no inverse)
    p1 = np.array([1.0, 0, 0, 0])
    p2 = np.array([0.0, 1, 0, 0])
    results["not_injective"] = np.allclose(hopf(p1), hopf(p2), atol=1e-12)
    return results


def run_boundary_tests():
    results = {}
    # Opposite poles on S^2 correspond to orthogonal fibres in S^3
    north = hopf(np.array([1.0, 0, 0, 0]))
    south = hopf(np.array([0.0, 0, 1, 0]))
    results["north_south_antipodal_on_S2"] = np.allclose(north, -south, atol=1e-12)
    # Fibre through any point is a great circle on S^3 (stays on S^3)
    p = np.array([0.5, 0.5, 0.5, 0.5])
    ts = np.linspace(0, 2 * np.pi, 50)
    ok = True
    for t in ts:
        ct, st = np.cos(t), np.sin(t)
        q = np.array([p[0] * ct - p[1] * st, p[0] * st + p[1] * ct,
                      p[2] * ct - p[3] * st, p[2] * st + p[3] * ct])
        if abs(np.linalg.norm(q) - 1.0) > 1e-10:
            ok = False
            break
    results["fibre_stays_on_S3"] = ok
    return results


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "hopf_fibration_embedding_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": [
            "U(1) fibre coordinate (global phase) discarded",
            "map is many-to-one; no section recovers the phase",
            "Chern number of Hopf bundle not computable from real embedding alone",
            "quantum ray vs point distinction invisible classically",
        ],
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "hopf_fibration_embedding_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
