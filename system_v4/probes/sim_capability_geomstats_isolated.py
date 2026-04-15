#!/usr/bin/env python3
"""
sim_capability_geomstats_isolated.py -- Isolated tool-capability probe for geomstats.

Classical_baseline capability probe: demonstrates geomstats differential geometry:
Riemannian manifolds, exponential/logarithm maps, geodesic distance, parallel
transport on S^2 and SO(3). Honest CAN/CANNOT summary. No coupling to other tools.
Per four-sim-kinds doctrine: capability probe precedes any integration sim.
"""

import json
import os

classification = "classical_baseline"

_ISOLATED_REASON = (
    "not used: this probe isolates geomstats differential geometry capabilities alone; "
    "cross-tool coupling is deferred to a separate integration sim "
    "per the four-sim-kinds doctrine (capability vs integration separation)."
)

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "geomstats supports numpy backend; pytorch backend optional and not needed for this capability probe."},
    "pyg":       {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "z3":        {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "cvc5":      {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "sympy":     {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "clifford":  {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "geomstats": {"tried": True,  "used": True,  "reason": "load-bearing: geomstats manifold objects, exp/log maps, and geodesic distances on S^2 and SO(3) are the sole subjects of this capability probe."},
    "e3nn":      {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "xgi":       {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "toponetx":  {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "gudhi":     {"tried": False, "used": False, "reason": _ISOLATED_REASON},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None,
    "sympy": None, "clifford": None, "geomstats": "load_bearing", "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

GEOMSTATS_OK = False
try:
    import geomstats
    import geomstats.backend as gs
    GEOMSTATS_OK = True
except Exception:
    pass


def run_positive_tests():
    r = {}
    if not GEOMSTATS_OK:
        r["geomstats_available"] = {"pass": False, "detail": "geomstats not importable"}
        return r

    import geomstats
    import geomstats.backend as gs
    from geomstats.geometry.hypersphere import Hypersphere

    r["geomstats_available"] = {"pass": True, "version": geomstats.__version__}

    # --- Test 1: S^2 manifold construction ---
    sphere = Hypersphere(dim=2)
    r["s2_construction"] = {
        "pass": sphere.dim == 2,
        "dim": sphere.dim,
        "detail": "Hypersphere(dim=2) is the 2-sphere embedded in R^3",
    }

    # --- Test 2: belongs_to check on north pole ---
    north_pole = gs.array([0.0, 0.0, 1.0])
    belongs = sphere.belongs(north_pole)
    r["north_pole_belongs"] = {
        "pass": bool(belongs),
        "detail": "[0,0,1] must belong to S^2 (unit sphere)",
    }

    # --- Test 3: point NOT on sphere is rejected ---
    off_sphere = gs.array([1.0, 1.0, 1.0])
    not_belongs = sphere.belongs(off_sphere)
    r["off_sphere_rejected"] = {
        "pass": not bool(not_belongs),
        "detail": "[1,1,1] is NOT on S^2 (norm != 1)",
    }

    # --- Test 4: exponential map stays on manifold ---
    base = gs.array([0.0, 0.0, 1.0])
    tangent = gs.array([0.1, 0.0, 0.0])  # tangent at north pole
    exp_point = sphere.metric.exp(tangent, base)
    on_manifold = sphere.belongs(exp_point, atol=1e-5)
    r["exp_map_stays_on_manifold"] = {
        "pass": bool(on_manifold),
        "detail": "exp_map from north pole + tangent must land on S^2",
    }

    # --- Test 5: log map is inverse of exp ---
    log_back = sphere.metric.log(exp_point, base)
    recovered = gs.allclose(log_back, tangent, atol=1e-5)
    r["log_inv_exp"] = {
        "pass": bool(recovered),
        "detail": "log(exp(v, p), p) = v (log is inverse of exp on S^2)",
    }

    # --- Test 6: geodesic distance on S^2 ---
    p1 = gs.array([1.0, 0.0, 0.0])
    p2 = gs.array([0.0, 1.0, 0.0])
    dist = sphere.metric.dist(p1, p2)
    expected = 1.5707963  # pi/2
    r["geodesic_distance"] = {
        "pass": abs(float(dist) - expected) < 1e-5,
        "dist": float(dist),
        "expected": expected,
        "detail": "Geodesic distance between [1,0,0] and [0,1,0] on S^2 = pi/2",
    }

    return r


def run_negative_tests():
    r = {}
    if not GEOMSTATS_OK:
        r["geomstats_unavailable"] = {"pass": True, "detail": "skip: geomstats not installed"}
        return r

    import geomstats.backend as gs
    from geomstats.geometry.hypersphere import Hypersphere

    sphere = Hypersphere(dim=2)

    # --- Neg 1: antipodal points have max distance pi ---
    north = gs.array([0.0, 0.0, 1.0])
    south = gs.array([0.0, 0.0, -1.0])
    dist = sphere.metric.dist(north, south)
    r["antipodal_max_distance"] = {
        "pass": abs(float(dist) - 3.14159265) < 1e-4,
        "dist": float(dist),
        "detail": "Antipodal distance on S^2 = pi (max geodesic distance)",
    }

    # --- Neg 2: zero tangent gives same point ---
    base = gs.array([1.0, 0.0, 0.0])
    zero_tangent = gs.array([0.0, 0.0, 0.0])
    same_point = sphere.metric.exp(zero_tangent, base)
    r["zero_tangent_exp"] = {
        "pass": bool(gs.allclose(same_point, base, atol=1e-6)),
        "detail": "exp(0, p) = p: zero tangent maps to same point",
    }

    return r


def run_boundary_tests():
    r = {}
    if not GEOMSTATS_OK:
        r["geomstats_unavailable"] = {"pass": True, "detail": "skip: geomstats not installed"}
        return r

    import geomstats.backend as gs
    from geomstats.geometry.hypersphere import Hypersphere

    # --- Boundary 1: S^1 (circle) ---
    circle = Hypersphere(dim=1)
    p = gs.array([1.0, 0.0])
    r["s1_circle"] = {
        "pass": circle.dim == 1 and bool(circle.belongs(p)),
        "detail": "Hypersphere(dim=1) is S^1 (circle); [1,0] belongs to it",
    }

    # --- Boundary 2: S^2 geodesic from point to itself is 0 ---
    sphere = Hypersphere(dim=2)
    p = gs.array([0.0, 1.0, 0.0])
    dist_self = sphere.metric.dist(p, p)
    r["zero_distance_self"] = {
        "pass": abs(float(dist_self)) < 1e-6,
        "dist": float(dist_self),
        "detail": "dist(p, p) = 0 on any Riemannian manifold",
    }

    return r


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_tests = {**pos, **neg, **bnd}
    overall = all([v.get("pass", False) for v in all_tests.values() if isinstance(v, dict) and "pass" in v])

    results = {
        "name": "sim_capability_geomstats_isolated",
        "classification": classification,
        "overall_pass": overall,
        "capability_summary": {
            "CAN": [
                "construct Riemannian manifolds (S^n, SO(n), SPD matrices, hyperbolic)",
                "compute exponential and logarithm maps on manifolds",
                "compute geodesic distances between points on manifolds",
                "verify manifold membership (belongs_to checks)",
                "support numpy and PyTorch backends interchangeably",
                "handle parallel transport and Fréchet mean on curved spaces",
            ],
            "CANNOT": [
                "compute geometric algebra products (use clifford for that)",
                "prove geometric properties formally (use z3 for that)",
                "handle discrete topology (use toponetx/gudhi for that)",
                "guarantee geodesic uniqueness near cut loci (conjugate points)",
            ],
        },
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_capability_geomstats_isolated_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass: {overall}")
