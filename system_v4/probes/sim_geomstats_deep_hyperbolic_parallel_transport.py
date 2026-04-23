#!/usr/bin/env python3
"""sim_geomstats_deep_hyperbolic_parallel_transport
Deep geomstats tool-integration sim. Load-bearing: Hyperboloid parallel
transport preserves the Minkowski inner product along geodesics.

scope_note: ENGINE_MATH_REFERENCE.md (hyperbolic layer) +
LADDERS_FENCES_ADMISSION_REFERENCE.md (isometry fence).
"""
import json, os, numpy as np

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": "no graph"},
    "z3": {"tried": False, "used": False, "reason": "continuous manifold"},
    "cvc5": {"tried": False, "used": False, "reason": "continuous manifold"},
    "sympy": {"tried": False, "used": False, "reason": "numeric"},
    "clifford": {"tried": False, "used": False, "reason": "Cl(1,2) parallel, not decisive"},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": "no irrep"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistence"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

from geomstats.geometry.hyperboloid import Hyperboloid
TOOL_MANIFEST["geomstats"]["tried"] = True
TOOL_MANIFEST["geomstats"]["used"] = True
TOOL_MANIFEST["geomstats"]["reason"] = "Hyperboloid.metric.parallel_transport + inner_product are the decisive isometry probes"
TOOL_INTEGRATION_DEPTH["geomstats"] = "load_bearing"

H2 = Hyperboloid(dim=2)

def _tangent(base, rng):
    amb = rng.normal(size=3)
    return np.asarray(H2.to_tangent(amb, base_point=base))

def run_positive_tests():
    rng = np.random.default_rng(2)
    max_drift = 0.0
    for _ in range(10):
        p = np.asarray(H2.random_point())
        q = np.asarray(H2.random_point())
        v = _tangent(p, rng)
        w = _tangent(p, rng)
        vt = np.asarray(H2.metric.parallel_transport(v, p, end_point=q))
        wt = np.asarray(H2.metric.parallel_transport(w, p, end_point=q))
        ip0 = float(H2.metric.inner_product(v, w, base_point=p))
        ip1 = float(H2.metric.inner_product(vt, wt, base_point=q))
        max_drift = max(max_drift, abs(ip0 - ip1))
    return {"max_ip_drift": max_drift, "pass": max_drift < 1e-6}

def run_negative_tests():
    # The ambient Euclidean inner product is NOT preserved by Minkowski transport.
    # Candidates that use naive Euclidean ip are excluded from H^2 geometry.
    rng = np.random.default_rng(3)
    p = np.asarray(H2.random_point()); q = np.asarray(H2.random_point())
    v = _tangent(p, rng); w = _tangent(p, rng)
    vt = np.asarray(H2.metric.parallel_transport(v, p, end_point=q))
    wt = np.asarray(H2.metric.parallel_transport(w, p, end_point=q))
    eu0 = float(np.dot(v, w))
    eu1 = float(np.dot(vt, wt))
    return {"euclidean_ip_drift": abs(eu0 - eu1),
            "pass": abs(eu0 - eu1) > 1e-6}

def run_boundary_tests():
    # Transport a vector to itself when end==base; must be identity.
    rng = np.random.default_rng(4)
    p = np.asarray(H2.random_point())
    v = _tangent(p, rng)
    vt = np.asarray(H2.metric.parallel_transport(v, p, end_point=p))
    err = float(np.linalg.norm(v - vt))
    return {"self_transport_err": err, "pass": err < 1e-6}

if __name__ == "__main__":
    results = {
        "name": "sim_geomstats_deep_hyperbolic_parallel_transport",
        "classification": "canonical",
        "scope_note": "ENGINE_MATH_REFERENCE.md (hyperbolic) + LADDERS_FENCES_ADMISSION_REFERENCE.md: candidates that preserve the Minkowski inner product under transport are admitted; naive Euclidean translation is excluded.",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    results["overall_pass"] = all(r["pass"] for r in (results["positive"], results["negative"], results["boundary"]))
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_geomstats_deep_hyperbolic_parallel_transport_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"PASS={results['overall_pass']} -> {out_path}")
