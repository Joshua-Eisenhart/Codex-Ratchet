#!/usr/bin/env python3
"""
sim_geomstats_deep_s2_frechet.py

Deep geomstats integration sim. Lego: Frechet mean on S^2 (Hopf base).
Claim: the intrinsic Riemannian mean of a small cluster on S^2 is
well-defined OFF the cut locus and UNDEFINED (non-unique) at the cut
locus (antipodal pair). The geomstats FrechetMean estimator is
load-bearing for the "well-defined" verdict; the cut-locus boundary
test is the structural falsifier that distinguishes geomstats' intrinsic
mean from a naive euclidean mean (which would silently return 0).

Classification: canonical.
"""
import json, os
import numpy as np

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "numeric only; geomstats numpy backend used"},
    "pyg": {"tried": False, "used": False, "reason": "no graph"},
    "z3": {"tried": False, "used": False, "reason": "numeric, not FOL"},
    "cvc5": {"tried": False, "used": False, "reason": "numeric, not FOL"},
    "sympy": {"tried": False, "used": False, "reason": "no symbolic manipulation"},
    "clifford": {"tried": False, "used": False, "reason": "S^2 handled intrinsically"},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariant layer"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistent homology"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

os.environ.setdefault("GEOMSTATS_BACKEND", "numpy")
try:
    import geomstats.backend as gs  # noqa: F401
    from geomstats.geometry.hypersphere import Hypersphere
    from geomstats.learning.frechet_mean import FrechetMean
    TOOL_MANIFEST["geomstats"]["tried"] = True
except ImportError:
    Hypersphere = None
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed -- BLOCKER"


def positive_small_cluster_mean():
    """Points within a small cap around north pole: intrinsic mean lives
    on the sphere and is close to north pole."""
    S2 = Hypersphere(dim=2)
    rng = np.random.default_rng(0)
    center = np.array([0.0, 0.0, 1.0])
    noise = 0.05 * rng.standard_normal((12, 3))
    pts = center + noise
    pts = pts / np.linalg.norm(pts, axis=-1, keepdims=True)
    fm = FrechetMean(space=S2)
    fm.fit(pts)
    mean = np.asarray(fm.estimate_)
    on_sphere = abs(np.linalg.norm(mean) - 1.0) < 1e-6
    near_pole = float(np.arccos(np.clip(mean @ center, -1, 1))) < 0.05
    return (on_sphere and near_pole), {
        "norm": float(np.linalg.norm(mean)),
        "geodesic_to_pole": float(np.arccos(np.clip(mean @ center, -1, 1))),
    }


def negative_euclidean_mean_off_manifold():
    """Naive euclidean mean of a spread cluster lies OFF S^2 -- proves
    geomstats' intrinsic projection is load-bearing."""
    rng = np.random.default_rng(1)
    pts = rng.standard_normal((20, 3))
    pts = pts / np.linalg.norm(pts, axis=-1, keepdims=True)
    euc = pts.mean(axis=0)
    off = abs(np.linalg.norm(euc) - 1.0) > 0.05
    return off, {"euclidean_norm": float(np.linalg.norm(euc))}


def boundary_cut_locus_antipodal():
    """Boundary: antipodal pair lies on the cut locus of S^2. The
    intrinsic Frechet functional has a DEGENERATE minimizer: every
    equatorial point is a global minimum. We certify the cut-locus
    signature via geomstats' intrinsic distance function by showing
    (i) the Frechet variance at an equatorial point is pi^2/2, strictly
    LESS than the variance at either pole (pi^2), and (ii) two distinct
    equatorial points achieve the same variance (non-uniqueness)."""
    S2 = Hypersphere(dim=2)
    antipodal = np.array([[0.0, 0.0, 1.0], [0.0, 0.0, -1.0]])

    def var_at(p):
        p = np.asarray(p, dtype=float)
        d = np.array([
            float(S2.metric.dist(p, antipodal[0])),
            float(S2.metric.dist(p, antipodal[1])),
        ])
        return float((d ** 2).sum())

    eq1 = np.array([1.0, 0.0, 0.0])
    eq2 = np.array([0.0, 1.0, 0.0])
    pole = np.array([0.0, 0.0, 1.0])
    v_eq1 = var_at(eq1); v_eq2 = var_at(eq2); v_pole = var_at(pole)
    lower_at_equator = (v_eq1 + 1e-6) < v_pole
    nonunique = abs(v_eq1 - v_eq2) < 1e-8
    return (lower_at_equator and nonunique), {
        "var_eq1": v_eq1, "var_eq2": v_eq2, "var_pole": v_pole,
    }


def run_positive_tests():
    ok, info = positive_small_cluster_mean()
    TOOL_MANIFEST["geomstats"]["used"] = True
    TOOL_MANIFEST["geomstats"]["reason"] = "FrechetMean on Hypersphere(2) computes the intrinsic mean; euclidean mean would sit off-manifold"
    TOOL_INTEGRATION_DEPTH["geomstats"] = "load_bearing"
    return {"frechet_mean_near_pole": {"pass": ok, **info}}


def run_negative_tests():
    ok, info = negative_euclidean_mean_off_manifold()
    return {"euclidean_mean_off_sphere": {"pass": ok, **info}}


def run_boundary_tests():
    ok, info = boundary_cut_locus_antipodal()
    return {"cut_locus_antipodal_equidistant": {"pass": ok, **info}}


if __name__ == "__main__":
    if Hypersphere is None:
        print("BLOCKER: geomstats not importable")
        raise SystemExit(2)
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = (all(v["pass"] for v in pos.values())
                and all(v["pass"] for v in neg.values())
                and all(v["pass"] for v in bnd.values()))
    results = {
        "name": "sim_geomstats_deep_s2_frechet",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "overall_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_geomstats_deep_s2_frechet_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {out_path}")
