#!/usr/bin/env python3
"""sim_geomstats_deep_spd_affine_invariant_metric
Deep geomstats tool-integration sim. Load-bearing: SPDMatrices + affine-
invariant metric. Candidates survive iff dist is GL(n)-congruence invariant.

scope_note: ENGINE_MATH_REFERENCE.md (SPD/density-matrix layer) +
LADDERS_FENCES_ADMISSION_REFERENCE.md (congruence invariance fence).
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

from geomstats.geometry.spd_matrices import SPDMatrices
TOOL_MANIFEST["geomstats"]["tried"] = True
TOOL_MANIFEST["geomstats"]["used"] = True
TOOL_MANIFEST["geomstats"]["reason"] = "SPDAffineMetric.dist congruence invariance is the decisive probe"
TOOL_INTEGRATION_DEPTH["geomstats"] = "load_bearing"

N = 3
SPD = SPDMatrices(n=N)  # default metric is SPDAffineMetric

def _rand_spd(rng):
    A = rng.normal(size=(N, N))
    return A @ A.T + N * np.eye(N)

def _rand_gl(rng):
    while True:
        G = rng.normal(size=(N, N))
        if abs(np.linalg.det(G)) > 0.3:
            return G

def run_positive_tests():
    rng = np.random.default_rng(5)
    drifts = []
    for _ in range(10):
        A = _rand_spd(rng); B = _rand_spd(rng); G = _rand_gl(rng)
        d0 = float(SPD.metric.dist(A, B))
        Ag = G @ A @ G.T; Bg = G @ B @ G.T
        d1 = float(SPD.metric.dist(Ag, Bg))
        drifts.append(abs(d0 - d1))
    return {"max_congruence_drift": max(drifts), "pass": max(drifts) < 1e-5}

def run_negative_tests():
    # A non-PD matrix is excluded from SPD.
    M = np.array([[1.0, 2.0, 0.0], [2.0, 1.0, 0.0], [0.0, 0.0, 1.0]])  # indefinite
    belongs = bool(SPD.belongs(M, atol=1e-9))
    return {"indefinite_admitted": belongs, "pass": belongs is False}

def run_boundary_tests():
    # Identity distance to itself = 0; near-singular SPD still finite.
    I = np.eye(N)
    d0 = float(SPD.metric.dist(I, I))
    S = np.diag([1e-3, 1.0, 1e3])
    d1 = float(SPD.metric.dist(I, S))
    return {"self_dist": d0, "wide_eig_dist": d1, "pass": d0 < 1e-9 and np.isfinite(d1) and d1 > 0}

if __name__ == "__main__":
    results = {
        "name": "sim_geomstats_deep_spd_affine_invariant_metric",
        "classification": "canonical",
        "scope_note": "ENGINE_MATH_REFERENCE.md (SPD/density) + LADDERS_FENCES_ADMISSION_REFERENCE.md: survivors are SPD candidates whose pairwise distance is invariant under GL(n) congruence; indefinite matrices are excluded.",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    results["overall_pass"] = all(r["pass"] for r in (results["positive"], results["negative"], results["boundary"]))
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_geomstats_deep_spd_affine_invariant_metric_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"PASS={results['overall_pass']} -> {out_path}")
