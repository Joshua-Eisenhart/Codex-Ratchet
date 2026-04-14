#!/usr/bin/env python3
"""sim_geomstats_deep_stiefel_orthogonality_excludes
Deep geomstats tool-integration sim. Load-bearing: Stiefel manifold
admissibility via column orthonormality; canonical metric distance is finite
between random Stiefel points, and non-orthonormal matrices are excluded.

scope_note: ENGINE_MATH_REFERENCE.md (Stiefel/frame layer) +
LADDERS_FENCES_ADMISSION_REFERENCE.md (orthonormality fence).
"""
import json, os, numpy as np

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": "no graph"},
    "z3": {"tried": False, "used": False, "reason": "continuous"},
    "cvc5": {"tried": False, "used": False, "reason": "continuous"},
    "sympy": {"tried": False, "used": False, "reason": "numeric"},
    "clifford": {"tried": False, "used": False, "reason": "not decisive"},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": "no irrep"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistence"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

from geomstats.geometry.stiefel import Stiefel
TOOL_MANIFEST["geomstats"]["tried"] = True
TOOL_MANIFEST["geomstats"]["used"] = True
TOOL_MANIFEST["geomstats"]["reason"] = "Stiefel.belongs + canonical metric dist are the decisive admissibility probes"
TOOL_INTEGRATION_DEPTH["geomstats"] = "load_bearing"

N, P = 5, 3
St = Stiefel(n=N, p=P)

def run_positive_tests():
    rng = np.random.default_rng(10)
    admits = 0
    for _ in range(20):
        X = np.asarray(St.random_point())
        if bool(St.belongs(X, atol=1e-6)):
            admits += 1
    return {"admits": admits, "n": 20, "pass": admits == 20}

def run_negative_tests():
    # A random Gaussian matrix is NOT on Stiefel.
    rng = np.random.default_rng(11)
    M = rng.normal(size=(N, P))
    belongs = bool(St.belongs(M, atol=1e-6))
    return {"gaussian_admitted": belongs, "pass": belongs is False}

def run_boundary_tests():
    rng = np.random.default_rng(12)
    X = np.asarray(St.random_point()); Y = np.asarray(St.random_point())
    d = float(St.metric.dist(X, Y))
    d_self = float(St.metric.dist(X, X))
    return {"dist_XY": d, "dist_self": d_self,
            "pass": np.isfinite(d) and d > 0 and d_self < 1e-6}

if __name__ == "__main__":
    results = {
        "name": "sim_geomstats_deep_stiefel_orthogonality_excludes",
        "classification": "canonical",
        "scope_note": "ENGINE_MATH_REFERENCE.md (Stiefel) + LADDERS_FENCES_ADMISSION_REFERENCE.md: frames survive iff columns are orthonormal; generic Gaussian matrices are excluded.",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    results["overall_pass"] = all(r["pass"] for r in (results["positive"], results["negative"], results["boundary"]))
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_geomstats_deep_stiefel_orthogonality_excludes_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"PASS={results['overall_pass']} -> {out_path}")
