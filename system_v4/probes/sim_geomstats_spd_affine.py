#!/usr/bin/env python3
"""sim_geomstats_spd_affine: SPD(n) affine-invariant distance disagrees with Euclidean Frobenius.

geomstats load-bearing: SPDMetricAffine implements d(A,B)=||log(A^{-1/2} B A^{-1/2})||_F.
Euclidean Frobenius on ambient matrix space is congruence-variant and not invariant
under A -> GAG^T for general G in GL(n).
"""
import json, os, numpy as np

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

from geomstats.geometry.spd_matrices import SPDMatrices, SPDAffineMetric
TOOL_MANIFEST["geomstats"]["tried"] = True

N = 3
SPD = SPDMatrices(n=N)
try:
    metric = SPDAffineMetric(space=SPD)
except TypeError:
    metric = SPDAffineMetric(n=N)

def _rand_spd(rng, n=N, cond=2.0):
    A = rng.normal(size=(n, n)); A = A @ A.T + cond * np.eye(n)
    return A

def run_positive_tests():
    rng = np.random.default_rng(3); results = {}; pairs_disagree = 0; total = 10
    max_ratio = 0.0
    for _ in range(total):
        A = _rand_spd(rng); B = _rand_spd(rng)
        d_aff = float(metric.dist(A, B))
        d_frob = float(np.linalg.norm(A - B, "fro"))
        if abs(d_aff - d_frob) / max(d_aff, d_frob, 1e-9) > 0.05:
            pairs_disagree += 1
        max_ratio = max(max_ratio, abs(d_aff - d_frob)/max(d_aff,1e-9))
    results["metrics_disagree"] = {"disagree_count": pairs_disagree, "total": total,
                                   "max_rel_diff": max_ratio, "pass": pairs_disagree == total}
    return results

def run_negative_tests():
    # Affine-invariance: d(GAG^T, GBG^T) == d(A,B); Frobenius violates.
    rng = np.random.default_rng(4)
    A = _rand_spd(rng); B = _rand_spd(rng)
    G = rng.normal(size=(N, N));
    # ensure invertible
    while abs(np.linalg.det(G)) < 0.1:
        G = rng.normal(size=(N, N))
    GA = G @ A @ G.T; GB = G @ B @ G.T
    d_aff_1 = float(metric.dist(A, B)); d_aff_2 = float(metric.dist(GA, GB))
    d_frob_1 = float(np.linalg.norm(A - B, "fro")); d_frob_2 = float(np.linalg.norm(GA - GB, "fro"))
    aff_inv = abs(d_aff_1 - d_aff_2) < 1e-6
    frob_inv = abs(d_frob_1 - d_frob_2) < 1e-6
    return {"affine_invariance_holds_for_affine_not_frob": {
        "aff_invariant": aff_inv, "frob_invariant": frob_inv,
        "pass": aff_inv and not frob_inv}}

def run_boundary_tests():
    # Identity distance zero; near-singular SPD still finite affine distance.
    I = np.eye(N); d0 = float(metric.dist(I, I))
    eps = 1e-6
    A_near = np.diag([eps, 1.0, 1.0]); B = np.eye(N)
    d_near = float(metric.dist(A_near, B))
    return {"identity_zero": {"d": d0, "pass": abs(d0) < 1e-8},
            "near_singular_finite": {"d": d_near, "pass": np.isfinite(d_near) and d_near > 0}}

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    TOOL_MANIFEST["geomstats"].update(used=True, reason="SPDAffineMetric intrinsic distance")
    TOOL_INTEGRATION_DEPTH["geomstats"] = "load_bearing"
    results = {"name":"sim_geomstats_spd_affine","tool_manifest":TOOL_MANIFEST,
               "tool_integration_depth":TOOL_INTEGRATION_DEPTH,
               "positive":pos,"negative":neg,"boundary":bnd,"classification":"canonical"}
    out_dir = os.path.join(os.path.dirname(__file__),"a2_state","sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir,"sim_geomstats_spd_affine_results.json")
    with open(out_path,"w") as f: json.dump(results, f, indent=2, default=str)
    all_pass = all(v.get("pass") for v in {**pos,**neg,**bnd}.values())
    print(f"PASS={all_pass} -> {out_path}")
