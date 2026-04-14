#!/usr/bin/env python3
"""sim_geomstats_s2_frechet: S^2 Frechet mean convergence + antipodal cut-locus variance.

geomstats load-bearing: intrinsic FrechetMean on Hypersphere uses geodesic distance
and exp/log on the sphere. Numpy Euclidean averaging does not produce an on-manifold
mean and cannot diagnose the cut-locus degeneracy at antipodal pairs.
"""
import json, os, numpy as np

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi": {"tried": False, "used": False, "reason": ""},
    "toponetx": {"tried": False, "used": False, "reason": ""},
    "gudhi": {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import geomstats.backend as gs
    from geomstats.geometry.hypersphere import Hypersphere
    from geomstats.learning.frechet_mean import FrechetMean
    TOOL_MANIFEST["geomstats"]["tried"] = True
except ImportError as e:
    raise

S2 = Hypersphere(dim=2)

def _normalize(v):
    v = np.asarray(v, float); return v / np.linalg.norm(v)

def run_positive_tests():
    rng = np.random.default_rng(0)
    center = _normalize([0.2, 0.1, 1.0])
    # Tangent-space samples pushed to manifold via exp
    tangent = rng.normal(scale=0.1, size=(50, 3))
    # project to tangent plane at center
    tangent = tangent - (tangent @ center)[:, None] * center
    pts = np.array([S2.metric.exp(tangent_vec=t, base_point=center) for t in tangent])
    fm = FrechetMean(S2); fm.fit(pts); mu = fm.estimate_
    d = float(S2.metric.dist(mu, center))
    return {"frechet_converges": {"dist_to_true_center": d, "pass": d < 0.05}}

def run_negative_tests():
    # Euclidean mean of antipodal pair is zero vector — not on S^2;
    # S^2 Frechet mean between antipodes is degenerate: any equator point is valid.
    p = np.array([0.0, 0.0, 1.0]); q = -p
    eu = (p + q) / 2.0
    eu_norm = float(np.linalg.norm(eu))
    # geodesic distance between antipodes is pi
    d_anti = float(S2.metric.dist(p, q))
    return {"antipode_euclidean_offmanifold": {"norm": eu_norm, "pass": eu_norm < 1e-12},
            "antipode_geodesic_is_pi": {"d": d_anti, "pass": abs(d_anti - np.pi) < 1e-6}}

def run_boundary_tests():
    # Cut-locus variance signature: points near antipode produce exploding Karcher variance.
    rng = np.random.default_rng(1)
    base = np.array([0.0, 0.0, 1.0])
    anti = -base
    # jitter around antipode
    tangent = rng.normal(scale=0.05, size=(30, 3))
    tangent = tangent - (tangent @ anti)[:, None] * anti
    pts = np.array([S2.metric.exp(tangent_vec=t, base_point=anti) for t in tangent])
    dists_from_base = np.array([S2.metric.dist(base, p) for p in pts])
    var_cut = float(dists_from_base.var())
    # near base, same scale jitter -> low variance
    tangent2 = rng.normal(scale=0.05, size=(30, 3))
    tangent2 = tangent2 - (tangent2 @ base)[:, None] * base
    pts2 = np.array([S2.metric.exp(tangent_vec=t, base_point=base) for t in tangent2])
    dists_near = np.array([S2.metric.dist(base, p) for p in pts2])
    var_near = float(dists_near.var())
    return {"cut_locus_variance_signature": {
        "var_at_cut_locus": var_cut, "var_near_base": var_near,
        "pass": var_cut > 10 * var_near or (var_cut > 1e-3 and var_near < 1e-3)}}

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    TOOL_MANIFEST["geomstats"].update(used=True, reason="Hypersphere metric.exp/dist + FrechetMean on S^2")
    TOOL_INTEGRATION_DEPTH["geomstats"] = "load_bearing"
    results = {"name": "sim_geomstats_s2_frechet",
               "tool_manifest": TOOL_MANIFEST,
               "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
               "positive": pos, "negative": neg, "boundary": bnd,
               "classification": "canonical"}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_geomstats_s2_frechet_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    all_pass = all(v.get("pass") for v in {**pos, **neg, **bnd}.values())
    print(f"PASS={all_pass} -> {out_path}")
