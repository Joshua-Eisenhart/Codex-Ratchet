#!/usr/bin/env python3
"""sim_geomstats_deep_grassmannian_distinguishability
Deep geomstats tool-integration sim. Load-bearing: Grassmannian dist is
invariant under change of basis within a subspace (indistinguishable
candidates); distinct subspaces remain distinguishable.

scope_note: ENGINE_MATH_REFERENCE.md (Grassmann layer) +
LADDERS_FENCES_ADMISSION_REFERENCE.md (gauge-invariance fence).
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

from geomstats.geometry.grassmannian import Grassmannian
TOOL_MANIFEST["geomstats"]["tried"] = True
TOOL_MANIFEST["geomstats"]["used"] = True
TOOL_MANIFEST["geomstats"]["reason"] = "Grassmannian.metric.dist is decisive for subspace-equivalence probe"
TOOL_INTEGRATION_DEPTH["geomstats"] = "load_bearing"

N, K = 5, 2
Gr = Grassmannian(n=N, p=K)

def _proj_from_basis(U):
    Q, _ = np.linalg.qr(U)
    return Q @ Q.T

def run_positive_tests():
    rng = np.random.default_rng(6)
    drifts = []
    for _ in range(10):
        U = rng.normal(size=(N, K))
        Q, _ = np.linalg.qr(U)
        R = np.linalg.qr(rng.normal(size=(K, K)))[0]  # change of basis within subspace
        P1 = Q @ Q.T
        P2 = (Q @ R) @ (Q @ R).T
        d = float(Gr.metric.dist(P1, P2))
        drifts.append(d)
    return {"max_same_subspace_dist": max(drifts), "pass": max(drifts) < 1e-6}

def run_negative_tests():
    rng = np.random.default_rng(7)
    U1 = rng.normal(size=(N, K)); U2 = rng.normal(size=(N, K))
    P1 = _proj_from_basis(U1); P2 = _proj_from_basis(U2)
    d = float(Gr.metric.dist(P1, P2))
    return {"distinct_subspace_dist": d, "pass": d > 1e-3}

def run_boundary_tests():
    # Non-projector (not idempotent) excluded from Grassmannian.
    M = 0.5 * np.eye(N)
    belongs = bool(Gr.belongs(M, atol=1e-9))
    return {"non_projector_admitted": belongs, "pass": belongs is False}

if __name__ == "__main__":
    results = {
        "name": "sim_geomstats_deep_grassmannian_distinguishability",
        "classification": "canonical",
        "scope_note": "ENGINE_MATH_REFERENCE.md (Grassmann) + LADDERS_FENCES_ADMISSION_REFERENCE.md: within-subspace basis changes are indistinguishable (dist=0); distinct subspaces remain distinguishable; non-projectors are excluded.",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    results["overall_pass"] = all(r["pass"] for r in (results["positive"], results["negative"], results["boundary"]))
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_geomstats_deep_grassmannian_distinguishability_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"PASS={results['overall_pass']} -> {out_path}")
