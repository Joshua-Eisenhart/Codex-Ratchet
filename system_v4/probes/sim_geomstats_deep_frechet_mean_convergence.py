#!/usr/bin/env python3
"""sim_geomstats_deep_frechet_mean_convergence
Deep geomstats tool-integration sim. Load-bearing: FrechetMean on S^2
converges to the intrinsic (Riemannian) mean; the ambient Euclidean mean is
excluded as the wrong candidate.

scope_note: ENGINE_MATH_REFERENCE.md (mean/centroid layer) +
LADDERS_FENCES_ADMISSION_REFERENCE.md (intrinsic-vs-ambient fence).
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

from geomstats.geometry.hypersphere import Hypersphere
from geomstats.learning.frechet_mean import FrechetMean
TOOL_MANIFEST["geomstats"]["tried"] = True
TOOL_MANIFEST["geomstats"]["used"] = True
TOOL_MANIFEST["geomstats"]["reason"] = "FrechetMean iterative solver on Hypersphere metric is load-bearing"
TOOL_INTEGRATION_DEPTH["geomstats"] = "load_bearing"

S2 = Hypersphere(dim=2)

def _sample_near(base, rng, eps=0.2, n=25):
    pts = []
    for _ in range(n):
        amb = rng.normal(size=3)
        t = S2.to_tangent(amb, base_point=base)
        t = t / (np.linalg.norm(t) + 1e-12) * eps * rng.uniform(0, 1)
        pts.append(np.asarray(S2.metric.exp(t, base_point=base)))
    return np.stack(pts)

def run_positive_tests():
    rng = np.random.default_rng(8)
    base = np.array([0.0, 0.0, 1.0])
    pts = _sample_near(base, rng)
    fm = FrechetMean(S2)
    fm.fit(pts)
    mu = np.asarray(fm.estimate_)
    err = float(S2.metric.dist(mu, base))
    on = bool(S2.belongs(mu, atol=1e-6))
    return {"dist_to_base": err, "on_manifold": on, "pass": err < 0.15 and on}

def run_negative_tests():
    # Ambient arithmetic mean is NOT on S^2 (excluded candidate).
    rng = np.random.default_rng(9)
    base = np.array([0.0, 0.0, 1.0])
    pts = _sample_near(base, rng, eps=0.4)
    amb = pts.mean(axis=0)
    on = bool(S2.belongs(amb, atol=1e-6))
    return {"ambient_mean_on_manifold": on, "pass": on is False}

def run_boundary_tests():
    # Single-point input: Frechet mean = that point.
    p = np.asarray(S2.random_point())
    fm = FrechetMean(S2)
    fm.fit(np.stack([p]))
    mu = np.asarray(fm.estimate_)
    err = float(np.linalg.norm(mu - p))
    return {"single_point_err": err, "pass": err < 1e-6}

if __name__ == "__main__":
    results = {
        "name": "sim_geomstats_deep_frechet_mean_convergence",
        "classification": "canonical",
        "scope_note": "ENGINE_MATH_REFERENCE.md (mean/centroid) + LADDERS_FENCES_ADMISSION_REFERENCE.md: Frechet-mean candidate survives on S^2; ambient arithmetic mean is excluded by belongs().",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    results["overall_pass"] = all(r["pass"] for r in (results["positive"], results["negative"], results["boundary"]))
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_geomstats_deep_frechet_mean_convergence_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"PASS={results['overall_pass']} -> {out_path}")
