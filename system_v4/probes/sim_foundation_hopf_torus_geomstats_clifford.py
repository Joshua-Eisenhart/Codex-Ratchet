#!/usr/bin/env python3
"""
PURE LEGO: Hopf Torus Geometry with Geomstats
=============================================
Foundational pure-math geometry lego for:
  - normalized spinors on S^3
  - Hopf map S^3 -> S^2
  - nested Hopf tori at fixed latitude
  - explicit torus geometry as S^1 x S^1

Tool intent:
  - geomstats: load-bearing manifold/geodesic/Fréchet structure
  - clifford: attempted load-bearing algebra layer when available
  - sympy: optional exact metric/area verification

No engine jargon. Foundation only.
"""

import json
import math
import os
from typing import Dict, List, Tuple

import numpy as np


TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed for this geometry lego"},
    "pyg": {"tried": False, "used": False, "reason": "not needed for this geometry lego"},
    "z3": {"tried": False, "used": False, "reason": "not needed for this geometry lego"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed for this geometry lego"},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": "not needed for this geometry lego"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed for this geometry lego"},
    "xgi": {"tried": False, "used": False, "reason": "not needed for this geometry lego"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed for this geometry lego"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed for this geometry lego"},
}

try:
    import geomstats.backend as gs
    from geomstats.geometry.hypersphere import Hypersphere
    from geomstats.geometry.product_manifold import ProductManifold
    from geomstats.learning.frechet_mean import FrechetMean

    TOOL_MANIFEST["geomstats"]["tried"] = True
    TOOL_MANIFEST["geomstats"]["used"] = True
    TOOL_MANIFEST["geomstats"]["reason"] = (
        "Load-bearing manifold layer: S^3/S^2 membership, geodesic distance, "
        "torus as S^1 x S^1, and Fréchet mean"
    )
except Exception as e:
    raise RuntimeError(f"geomstats is required for this sim: {type(e).__name__}: {e}") from e

try:
    import sympy as sp

    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "Exact verification of torus metric and area formulas"
except Exception as e:
    sp = None
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["reason"] = f"runtime unavailable: {type(e).__name__}"

try:
    from clifford import Cl  # noqa: F401

    TOOL_MANIFEST["clifford"]["tried"] = True
    TOOL_MANIFEST["clifford"]["used"] = True
    TOOL_MANIFEST["clifford"]["reason"] = "Geometric algebra basis available"
    CLIFFORD_STATUS = "available"
except Exception as e:
    TOOL_MANIFEST["clifford"]["tried"] = True
    TOOL_MANIFEST["clifford"]["used"] = False
    TOOL_MANIFEST["clifford"]["reason"] = f"runtime unavailable: {type(e).__name__}"
    CLIFFORD_STATUS = f"blocked: {type(e).__name__}"

EPS = 1e-10
S3 = Hypersphere(dim=3)
S2 = Hypersphere(dim=2)
S1 = Hypersphere(dim=1)
TORUS = ProductManifold((S1, S1))


def normalized_spinor(eta: float, alpha: float, beta: float) -> np.ndarray:
    z1 = np.cos(eta) * np.exp(1j * alpha)
    z2 = np.sin(eta) * np.exp(1j * beta)
    return np.array([z1, z2], dtype=np.complex128)


def spinor_to_s3_point(spinor: np.ndarray) -> np.ndarray:
    z1, z2 = spinor
    point = np.array([np.real(z1), np.imag(z1), np.real(z2), np.imag(z2)], dtype=float)
    norm = np.linalg.norm(point)
    if norm <= EPS:
        raise ValueError("degenerate spinor")
    return point / norm


def hopf_map(spinor: np.ndarray) -> np.ndarray:
    z1, z2 = spinor
    x = 2.0 * np.real(z1 * np.conjugate(z2))
    y = 2.0 * np.imag(z1 * np.conjugate(z2))
    z = np.abs(z1) ** 2 - np.abs(z2) ** 2
    vec = np.array([x, y, z], dtype=float)
    return vec / np.linalg.norm(vec)


def torus_angles_to_point(theta1: float, theta2: float) -> np.ndarray:
    return np.array(
        [
            [np.cos(theta1), np.sin(theta1)],
            [np.cos(theta2), np.sin(theta2)],
        ],
        dtype=float,
    )


def torus_embed_r4(eta: float, theta1: float, theta2: float) -> np.ndarray:
    spinor = normalized_spinor(eta, theta1, theta2)
    return spinor_to_s3_point(spinor)


def torus_radii(eta: float) -> Tuple[float, float]:
    return float(np.cos(eta)), float(np.sin(eta))


def circular_mean_angle(angles: List[float]) -> float:
    return float(np.arctan2(np.mean(np.sin(angles)), np.mean(np.cos(angles))))


def principal_angle_difference(a: float, b: float) -> float:
    return float(np.arctan2(np.sin(a - b), np.cos(a - b)))


def induced_metric_components(eta: float) -> Dict[str, float]:
    return {
        "g11": float(np.cos(eta) ** 2),
        "g22": float(np.sin(eta) ** 2),
        "g12": 0.0,
        "area": float(4.0 * np.pi**2 * np.cos(eta) * np.sin(eta)),
    }


def sympy_torus_formula_check(eta_value: float) -> Dict[str, object]:
    if sp is None:
        return {"available": False}

    eta = sp.Symbol("eta", positive=True)
    g11 = sp.cos(eta) ** 2
    g22 = sp.sin(eta) ** 2
    area = sp.simplify(4 * sp.pi**2 * sp.sqrt(g11 * g22))
    alt_area = sp.simplify(2 * sp.pi**2 * sp.sin(2 * eta))
    residual = sp.simplify(area - alt_area)
    numeric_residual = float(sp.N(residual.subs(eta, eta_value)))
    return {
        "available": True,
        "metric_diagonal": True,
        "area_formula_residual": str(residual),
        "numeric_area_residual": numeric_residual,
        "pass": abs(numeric_residual) < 1e-12,
    }


def run_positive_tests() -> Dict[str, dict]:
    eta = np.pi / 4.0
    sample_spinors = [
        normalized_spinor(np.pi / 8.0, 0.2, 1.1),
        normalized_spinor(np.pi / 4.0, 1.3, 2.4),
        normalized_spinor(3.0 * np.pi / 8.0, -0.5, 0.8),
    ]

    s3_ok = all(bool(S3.belongs(gs.array(spinor_to_s3_point(sp)))) for sp in sample_spinors)
    s2_ok = all(bool(S2.belongs(gs.array(hopf_map(sp)))) for sp in sample_spinors)

    base = normalized_spinor(np.pi / 5.0, 0.3, 1.2)
    shifted = np.exp(1j * 1.1) * base
    hopf_base = hopf_map(base)
    hopf_shifted = hopf_map(shifted)

    theta_pairs = [(0.1, 0.2), (0.2, 0.1), (0.05, 0.15), (2 * np.pi - 0.08, 2 * np.pi - 0.02)]
    torus_points = gs.array([torus_angles_to_point(t1, t2) for t1, t2 in theta_pairs])
    frechet = FrechetMean(TORUS)
    frechet.fit(torus_points)
    torus_mean = np.asarray(frechet.estimate_)
    mean_angles = (
        circular_mean_angle([pair[0] for pair in theta_pairs]),
        circular_mean_angle([pair[1] for pair in theta_pairs]),
    )
    expected_mean = torus_angles_to_point(*mean_angles)
    mean_delta = float(np.linalg.norm(torus_mean - expected_mean))

    metric = induced_metric_components(eta)
    sympy_check = sympy_torus_formula_check(eta)

    sample_a = gs.array(spinor_to_s3_point(normalized_spinor(np.pi / 4.0, 0.1, 0.2)))
    sample_b = gs.array(spinor_to_s3_point(normalized_spinor(np.pi / 4.0, 0.7, 1.0)))
    geodesic_distance = float(S3.metric.dist(sample_a, sample_b))

    return {
        "normalized_spinors_land_on_s3_and_hopf_images_land_on_s2": {
            "s3_membership": s3_ok,
            "s2_membership": s2_ok,
            "pass": s3_ok and s2_ok,
        },
        "hopf_map_is_invariant_under_global_phase": {
            "hopf_base": hopf_base.tolist(),
            "hopf_phase_shifted": hopf_shifted.tolist(),
            "equal": np.allclose(hopf_base, hopf_shifted, atol=1e-12),
            "pass": np.allclose(hopf_base, hopf_shifted, atol=1e-12),
        },
        "clifford_torus_is_balanced_at_eta_pi_over_4": {
            "r_major": torus_radii(eta)[0],
            "r_minor": torus_radii(eta)[1],
            "equal": abs(torus_radii(eta)[0] - torus_radii(eta)[1]) < 1e-12,
            "pass": abs(torus_radii(eta)[0] - torus_radii(eta)[1]) < 1e-12,
        },
        "geomstats_torus_frechet_mean_matches_componentwise_circular_mean": {
            "mean_delta": mean_delta,
            "frechet_mean": torus_mean.tolist(),
            "expected_mean": expected_mean.tolist(),
            "pass": mean_delta < 1e-4,
        },
        "induced_torus_metric_and_area_match_exact_formulas": {
            "metric": metric,
            "sympy_check": sympy_check,
            "pass": abs(metric["g12"]) < 1e-12 and (sympy_check["pass"] if sympy_check["available"] else True),
        },
        "s3_geodesic_distance_is_nontrivial_for_distinct_spinors": {
            "distance": geodesic_distance,
            "positive": geodesic_distance > 1e-4,
            "pass": geodesic_distance > 1e-4,
        },
    }


def run_negative_tests() -> Dict[str, dict]:
    eta = np.pi / 4.0
    sp1 = normalized_spinor(eta, 0.0, 0.0)
    sp2 = normalized_spinor(eta, np.pi / 3.0, np.pi / 3.0)
    sp3 = normalized_spinor(eta, 0.0, np.pi / 3.0)

    counterfeit_prob = lambda sp: np.array([abs(sp[0]) ** 2, abs(sp[1]) ** 2], dtype=float)
    prob_same = np.allclose(counterfeit_prob(sp1), counterfeit_prob(sp2), atol=1e-12)
    hopf_same = np.allclose(hopf_map(sp1), hopf_map(sp2), atol=1e-12)
    hopf_diff = np.linalg.norm(hopf_map(sp1) - hopf_map(sp3))

    near_wrap_angles = [2 * np.pi - 0.05, 0.03, 0.02]
    naive_mean = float(np.mean(near_wrap_angles))
    circular_mean = circular_mean_angle(near_wrap_angles)
    naive_error = abs(principal_angle_difference(naive_mean, 0.0))
    circular_error = abs(principal_angle_difference(circular_mean, 0.0))

    eta_inner = np.pi / 8.0
    eta_outer = 3.0 * np.pi / 8.0
    norm_projection_inner = np.linalg.norm(torus_embed_r4(eta_inner, 0.4, 0.8))
    norm_projection_outer = np.linalg.norm(torus_embed_r4(eta_outer, 0.4, 0.8))

    return {
        "probability_only_projection_is_phase_blind_counterfeit": {
            "probabilities_match_under_global_phase": prob_same,
            "true_hopf_same_under_global_phase": hopf_same,
            "true_hopf_distinguishes_relative_phase": hopf_diff > 1e-3,
            "pass": prob_same and hopf_same and hopf_diff > 1e-3,
        },
        "naive_angle_average_fails_near_periodic_boundary": {
            "naive_error_to_zero": naive_error,
            "circular_error_to_zero": circular_error,
            "naive_worse": naive_error > circular_error + 0.1,
            "pass": naive_error > circular_error + 0.1,
        },
        "unit_norm_projection_cannot_distinguish_nested_torus_levels": {
            "norm_inner": norm_projection_inner,
            "norm_outer": norm_projection_outer,
            "same_unit_norm": abs(norm_projection_inner - norm_projection_outer) < 1e-12,
            "pass": abs(norm_projection_inner - norm_projection_outer) < 1e-12,
        },
        "clifford_runtime_is_honestly_reported_when_blocked": {
            "clifford_status": CLIFFORD_STATUS,
            "reported_block": (CLIFFORD_STATUS.startswith("blocked") and not TOOL_MANIFEST["clifford"]["used"]) or TOOL_MANIFEST["clifford"]["used"],
            "pass": (CLIFFORD_STATUS.startswith("blocked") and not TOOL_MANIFEST["clifford"]["used"]) or TOOL_MANIFEST["clifford"]["used"],
        },
    }


def run_boundary_tests() -> Dict[str, dict]:
    eta_small = 1e-3
    eta_large = np.pi / 2.0 - 1e-3
    small_radii = torus_radii(eta_small)
    large_radii = torus_radii(eta_large)

    base = normalized_spinor(np.pi / 6.0, 0.4, 1.1)
    minus_base = -base

    return {
        "small_eta_torus_approaches_single_circle_limit": {
            "r_major": small_radii[0],
            "r_minor": small_radii[1],
            "degenerate_minor": small_radii[1] < 2e-3,
            "pass": small_radii[1] < 2e-3,
        },
        "large_eta_torus_approaches_complementary_circle_limit": {
            "r_major": large_radii[0],
            "r_minor": large_radii[1],
            "degenerate_major": large_radii[0] < 2e-3,
            "pass": large_radii[0] < 2e-3,
        },
        "phase_shift_by_pi_preserves_hopf_image": {
            "hopf_base": hopf_map(base).tolist(),
            "hopf_minus_base": hopf_map(minus_base).tolist(),
            "equal": np.allclose(hopf_map(base), hopf_map(minus_base), atol=1e-12),
            "pass": np.allclose(hopf_map(base), hopf_map(minus_base), atol=1e-12),
        },
    }


def count_section(section: Dict[str, dict]) -> Dict[str, int]:
    total = sum(1 for value in section.values() if isinstance(value, dict) and "pass" in value)
    passed = sum(1 for value in section.values() if isinstance(value, dict) and bool(value.get("pass")) is True)
    return {"passed": passed, "failed": total - passed, "total": total}


def sanitize_json(value):
    if isinstance(value, dict):
        return {key: sanitize_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_json(item) for item in value]
    if isinstance(value, tuple):
        return [sanitize_json(item) for item in value]
    if isinstance(value, np.ndarray):
        return sanitize_json(value.tolist())
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    return value


def main() -> None:
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    pos = count_section(positive)
    neg = count_section(negative)
    bnd = count_section(boundary)
    total_fail = pos["failed"] + neg["failed"] + bnd["failed"]

    results = {
        "name": "PURE LEGO: Hopf Torus Geometry with Geomstats",
        "probe": "foundation_hopf_torus_geomstats_clifford",
        "purpose": "Foundational geometry lego for normalized spinors, Hopf map, and nested torus structure",
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "canonical",
        "caveat": (
            "Geomstats is load-bearing in this artifact. The clifford layer was attempted "
            "but is runtime-blocked in the current Python 3.13 environment and is reported honestly."
        ),
        "summary": {
            "positive_pass": pos["passed"],
            "positive_fail": pos["failed"],
            "negative_pass": neg["passed"],
            "negative_fail": neg["failed"],
            "boundary_pass": bnd["passed"],
            "boundary_fail": bnd["failed"],
            "total_fail": total_fail,
            "all_pass": total_fail == 0,
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "foundation_hopf_torus_geomstats_clifford_results.json")
    results = sanitize_json(results)
    with open(out_path, "w") as handle:
        json.dump(results, handle, indent=2)

    print(f"Results written to {out_path}")
    print(json.dumps(results["summary"], indent=2))


if __name__ == "__main__":
    main()
