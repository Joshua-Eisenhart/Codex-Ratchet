#!/usr/bin/env python3
"""
sim_geomstats_capability -- Tool-capability isolation probe for geomstats.

Governing rule (owner+Hermes 2026-04-13): geomstats is load_bearing in
candidate sims and needs an exact capability receipt before any later
tool-lego fit or coupling packet can rely on its manifold APIs.

Witness load-bearing use: system_v4/probes/sim_density_hopf_geometry.py
(uses geomstats manifold distance/geometry APIs in a bounded density/Hopf
geometry receipt).

Contract: ~/wiki/concepts/tool-capability-sim-program.md
  - job: geodesic/metric computations on Riemannian manifolds
  - minimal tasks tested: Hypersphere geodesic, exp/log roundtrip, SPD affine
    metric, Frechet mean, numpy-slerp baseline comparison, off-manifold failure
  - load_bearing here: geomstats decides pass/fail for tests 1-4; its output is
    compared (not replaced) in test 5
"""

classification = "canonical"

import json
import os
import numpy as np

from receipt_boundary import apply_default_receipt_boundary

# =====================================================================
# TOOL MANIFEST
# =====================================================================

_NOT_USED_REASON = (
    "not used: this bounded geomstats capability receipt isolates manifold "
    "geodesic, metric, and Frechet-mean APIs; other tool families require separate receipts."
)

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "pyg":       {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "z3":        {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "cvc5":      {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "sympy":     {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "clifford":  {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": "tool under capability test -- overwritten on import"},
    "e3nn":      {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "xgi":       {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "toponetx":  {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "gudhi":     {"tried": False, "used": False, "reason": _NOT_USED_REASON},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": "load_bearing",
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

try:
    import geomstats  # noqa: F401
    from geomstats.geometry.hypersphere import Hypersphere
    from geomstats.geometry.spd_matrices import SPDMatrices, SPDAffineMetric
    from geomstats.learning.frechet_mean import FrechetMean
    TOOL_MANIFEST["geomstats"]["tried"] = True
    TOOL_MANIFEST["geomstats"]["used"] = True
    TOOL_MANIFEST["geomstats"]["reason"] = (
        "load-bearing capability under test: geomstats Hypersphere metric, "
        "exp/log, SPD affine distance, and FrechetMean APIs decide the receipt verdicts."
    )
    GEOMSTATS_OK = True
except Exception as e:
    GEOMSTATS_OK = False
    TOOL_MANIFEST["geomstats"]["reason"] = f"import failed: {e}"


TOL = 1e-8
LOOSE_TOL = 1e-6


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def test_hypersphere_geodesic():
    """Great-circle geodesic between two S^2 points matches analytical arc."""
    S2 = Hypersphere(dim=2)
    p = np.array([1.0, 0.0, 0.0])
    q = np.array([0.0, 1.0, 0.0])  # orthogonal -> arc length = pi/2
    d = S2.metric.dist(p, q)
    expected = np.pi / 2
    ok = abs(float(d) - expected) < LOOSE_TOL
    return {"geomstats_dist": float(d), "expected": expected,
            "abs_err": abs(float(d) - expected), "pass": bool(ok)}


def test_exp_log_roundtrip():
    """exp_p(log_p(q)) == q on S^2."""
    S2 = Hypersphere(dim=2)
    p = np.array([1.0, 0.0, 0.0])
    q = np.array([0.0, np.sqrt(0.5), np.sqrt(0.5)])
    v = S2.metric.log(point=q, base_point=p)
    q_rt = S2.metric.exp(tangent_vec=v, base_point=p)
    err = float(np.linalg.norm(q - q_rt))
    ok = err < LOOSE_TOL
    return {"roundtrip_err": err, "pass": bool(ok)}


def test_spd_affine_distance():
    """Affine-invariant distance d(I, diag(a,b)) = sqrt(sum log^2(eigvals))."""
    spd = SPDMatrices(n=2)
    metric = SPDAffineMetric(space=spd)
    A = np.eye(2)
    B = np.diag([4.0, 9.0])
    d = metric.dist(A, B)
    expected = float(np.sqrt(np.log(4.0) ** 2 + np.log(9.0) ** 2))
    err = abs(float(d) - expected)
    ok = err < LOOSE_TOL
    return {"geomstats_dist": float(d), "expected": expected,
            "abs_err": err, "pass": bool(ok)}


def test_frechet_mean_convergence():
    """Frechet mean of a small cluster on S^2 sits near the cluster center."""
    S2 = Hypersphere(dim=2)
    # cluster near north pole
    center = np.array([0.0, 0.0, 1.0])
    rng = np.random.default_rng(7)
    pts = []
    for _ in range(16):
        v = rng.normal(size=3) * 0.05
        v[2] = 0.0  # tangent at north pole (perp to z)
        e = S2.metric.exp(tangent_vec=v, base_point=center)
        pts.append(e)
    pts = np.array(pts)
    fm = FrechetMean(space=S2)
    fm.fit(pts)
    mean = fm.estimate_
    # arc distance between computed mean and true center
    d_center = float(S2.metric.dist(mean, center))
    ok = d_center < 0.05
    return {"mean_to_center_arc": d_center, "pass": bool(ok)}


def run_positive_tests():
    return {
        "hypersphere_geodesic": test_hypersphere_geodesic(),
        "exp_log_roundtrip": test_exp_log_roundtrip(),
        "spd_affine_distance": test_spd_affine_distance(),
        "frechet_mean": test_frechet_mean_convergence(),
    }


# =====================================================================
# NEGATIVE / COMPARISON TESTS
# =====================================================================

def numpy_slerp(p, q, t):
    p = p / np.linalg.norm(p)
    q = q / np.linalg.norm(q)
    omega = np.arccos(np.clip(np.dot(p, q), -1.0, 1.0))
    if omega < 1e-12:
        return p
    so = np.sin(omega)
    return (np.sin((1 - t) * omega) / so) * p + (np.sin(t * omega) / so) * q


def test_baseline_slerp_matches_geomstats():
    """geomstats geodesic midpoint must agree with numpy slerp midpoint."""
    S2 = Hypersphere(dim=2)
    p = np.array([1.0, 0.0, 0.0])
    q = np.array([0.0, 1.0, 0.0])
    geod = S2.metric.geodesic(initial_point=p, end_point=q)
    mid_gs = np.array(geod(0.5)).reshape(-1)
    mid_np = numpy_slerp(p, q, 0.5)
    err = float(np.linalg.norm(mid_gs - mid_np))
    ok = err < LOOSE_TOL
    return {"mid_geomstats": mid_gs.tolist(),
            "mid_numpy_slerp": mid_np.tolist(),
            "abs_err": err, "pass": bool(ok)}


def run_negative_tests():
    return {
        "baseline_slerp_comparison": test_baseline_slerp_matches_geomstats(),
    }


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def test_off_manifold_point():
    """Point not on the sphere: geomstats must reject via belongs()."""
    S2 = Hypersphere(dim=2)
    bad = np.array([2.0, 0.0, 0.0])  # |x|=2, not on unit sphere
    good = np.array([1.0, 0.0, 0.0])
    belongs_bad = bool(S2.belongs(bad, atol=1e-10))
    belongs_good = bool(S2.belongs(good, atol=1e-10))
    ok = (not belongs_bad) and belongs_good
    return {"belongs_bad": belongs_bad, "belongs_good": belongs_good,
            "pass": bool(ok)}


def test_antipodal_log_degeneracy():
    """log at antipodal point is ill-defined; probe behavior (no crash)."""
    S2 = Hypersphere(dim=2)
    p = np.array([1.0, 0.0, 0.0])
    ap = -p
    try:
        v = S2.metric.log(point=ap, base_point=p)
        # length of tangent should be pi analytically; geomstats may return
        # 0 at the cut locus (documented antipodal degeneracy). Accept either
        # ~pi or ~0 as predictable no-crash behavior; record the actual value.
        n = float(np.linalg.norm(v))
        near_pi = abs(n - np.pi) < 1e-3
        near_zero = n < 1e-8
        predictable = near_pi or near_zero
        capability_limit = None
        if near_zero:
            capability_limit = ("antipodal log returns zero tangent "
                                "(cut-locus degeneracy) -- do NOT rely on "
                                "log at antipodes")
        return {"tangent_norm": n, "expected_pi_analytic": float(np.pi),
                "near_pi": bool(near_pi), "near_zero": bool(near_zero),
                "capability_limit": capability_limit,
                "pass": bool(predictable)}
    except Exception as e:
        # Only typed, predictable raises (ValueError / RuntimeError /
        # NotImplementedError) count as boundary-predictable. An arbitrary
        # Exception (e.g. AttributeError from an API drift) is a real
        # capability regression.
        etype = type(e).__name__
        predictable = etype in {"ValueError", "RuntimeError",
                                 "NotImplementedError", "ArithmeticError"}
        return {"raised": etype, "message": str(e)[:200],
                "pass": bool(predictable),
                "capability_limit": ("antipodal log raised "
                                     f"{etype} at cut locus")
                                     if predictable else None}


def run_boundary_tests():
    return {
        "off_manifold_belongs": test_off_manifold_point(),
        "antipodal_log": test_antipodal_log_degeneracy(),
    }


# =====================================================================
# MAIN
# =====================================================================

def _collect_pass_flags(d):
    flags = []
    for _, v in d.items():
        if isinstance(v, dict) and "pass" in v:
            flags.append(bool(v["pass"]))
    return flags


if __name__ == "__main__":
    if not GEOMSTATS_OK:
        results = {
            "name": "sim_geomstats_capability",
            "tool_manifest": TOOL_MANIFEST,
            "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
            "classification": "canonical",
            "error": "geomstats not importable",
            "all_pass": False,
            "summary": {"all_pass": False},
            "out_of_scope": [
                "no manifold lego promotion",
                "no Hopf geometry promotion",
                "no bridge claim",
                "no axis claim",
                "no GStack claim",
                "no nonclassical admission",
            ],
        }
    else:
        pos = run_positive_tests()
        neg = run_negative_tests()
        bnd = run_boundary_tests()
        flags = (_collect_pass_flags(pos)
                 + _collect_pass_flags(neg)
                 + _collect_pass_flags(bnd))
        all_pass = bool(flags) and all(flags)
        results = {
            "name": "sim_geomstats_capability",
            "purpose": (
                "bounded isolation probe of geomstats: hypersphere geodesic, "
                "exp/log roundtrip, SPD affine distance, Frechet mean, "
                "numpy-slerp comparison, off-manifold rejection"
            ),
            "witness_loadbearing_use": "system_v4/probes/sim_density_hopf_geometry.py",
            "tool_manifest": TOOL_MANIFEST,
            "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
            "positive": pos,
            "negative": neg,
            "boundary": bnd,
            "classification": "canonical",
            "all_pass": all_pass,
            "pass_count": int(sum(flags)),
            "total_count": int(len(flags)),
            "summary": {"all_pass": all_pass},
            "surviving_alternatives": [
                "This receipt covers only bounded geomstats manifold-metric capability; it does not promote Hopf geometry, manifold lego status, bridge, axis, GStack, or nonclassical admission."
            ],
            "demotion_condition": (
                "Demote this geomstats capability receipt if hypersphere distance, "
                "exp/log roundtrip, SPD affine distance, Frechet mean, slerp comparison, "
                "or off-manifold/cut-locus controls fail on rerun."
            ),
            "out_of_scope": [
                "no manifold lego promotion",
                "no Hopf geometry promotion",
                "no bridge claim",
                "no axis claim",
                "no GStack claim",
                "no nonclassical admission",
            ],
        }
    results = apply_default_receipt_boundary(
        results,
        source_name="sim_geomstats_capability",
        target="Use as bounded geomstats manifold-metric capability evidence before exact manifold lego-fit or coupling packets.",
    )
    results["claim_ceiling"] = (
        "finite sim_geomstats_capability lego receipt only; "
        "no bridge, GStack, axis, or promoted admission"
    )

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_geomstats_capability_results.json")
    matrix_path = os.path.join(out_dir, "geomstats_capability_results.json")
    for path in (out_path, matrix_path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Matrix-compatible results written to {matrix_path}")
    print(f"all_pass={results.get('all_pass')} "
          f"pass={results.get('pass_count')}/{results.get('total_count')}")
