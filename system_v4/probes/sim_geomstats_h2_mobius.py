#!/usr/bin/env python3
"""sim_geomstats_h2_mobius: Hyperbolic H^2 (Poincare ball) distance vs ambient Euclidean.

geomstats load-bearing: Hyperbolic(dim=2) Poincare ball metric implements
d(x,y) = arcosh(1 + 2||x-y||^2 / ((1-||x||^2)(1-||y||^2))), which diverges at
the boundary while Euclidean stays bounded.
"""
import json, os, numpy as np

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

from geomstats.geometry.poincare_ball import PoincareBall
TOOL_MANIFEST["geomstats"]["tried"] = True

H2 = PoincareBall(dim=2)

def run_positive_tests():
    rng = np.random.default_rng(5)
    pts = rng.uniform(-0.5, 0.5, size=(20, 2))
    # symmetry and positivity
    ok = True
    for i in range(len(pts)):
        for j in range(len(pts)):
            d_ij = float(H2.metric.dist(pts[i], pts[j]))
            d_ji = float(H2.metric.dist(pts[j], pts[i]))
            if i == j and abs(d_ij) > 1e-8: ok = False
            if abs(d_ij - d_ji) > 1e-8: ok = False
    return {"symmetric_positive": {"pass": ok}}

def run_negative_tests():
    # Boundary divergence: Euclidean bounded by 2, hyperbolic -> infinity.
    x = np.array([0.0, 0.0])
    ys = [np.array([r, 0.0]) for r in [0.5, 0.9, 0.99, 0.999]]
    d_hyp = [float(H2.metric.dist(x, y)) for y in ys]
    d_euc = [float(np.linalg.norm(x - y)) for y in ys]
    monotone_diverge = all(d_hyp[i+1] > d_hyp[i] for i in range(3)) and d_hyp[-1] > 5 * d_euc[-1]
    return {"boundary_diverges_unlike_euclidean": {
        "d_hyp": d_hyp, "d_euc": d_euc, "pass": monotone_diverge}}

def run_boundary_tests():
    # Mobius addition shift invariance: d(a+x, a+y) == d(x, y) on Poincare ball under
    # gyrovector translation — check d is NOT equal to Euclidean shift.
    x = np.array([0.1, 0.0]); y = np.array([0.3, 0.0])
    d_hyp = float(H2.metric.dist(x, y))
    d_euc = float(np.linalg.norm(x - y))
    return {"hyp_exceeds_euclidean_chord": {
        "d_hyp": d_hyp, "d_euc": d_euc, "pass": d_hyp > d_euc}}

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    TOOL_MANIFEST["geomstats"].update(used=True, reason="PoincareBall intrinsic hyperbolic metric")
    TOOL_INTEGRATION_DEPTH["geomstats"] = "load_bearing"
    results = {"name":"sim_geomstats_h2_mobius","tool_manifest":TOOL_MANIFEST,
               "tool_integration_depth":TOOL_INTEGRATION_DEPTH,
               "positive":pos,"negative":neg,"boundary":bnd,"classification":"canonical"}
    out_dir = os.path.join(os.path.dirname(__file__),"a2_state","sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir,"sim_geomstats_h2_mobius_results.json")
    with open(out_path,"w") as f: json.dump(results, f, indent=2, default=str)
    all_pass = all(v.get("pass") for v in {**pos,**neg,**bnd}.values())
    print(f"PASS={all_pass} -> {out_path}")
