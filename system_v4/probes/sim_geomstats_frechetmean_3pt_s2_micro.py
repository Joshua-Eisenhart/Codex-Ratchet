#!/usr/bin/env python3
"""geomstats FrechetMean 3-point S2 micro probe.

Tool-stage scope:
  - one tool: geomstats
  - one API surface: geomstats.learning.frechet_mean.FrechetMean
  - one tiny claim: FrechetMean returns a bounded intrinsic mean for a pinned
    three-point fixture on Hypersphere(dim=2), excluding ambient Euclidean
    averaging as the decisive readout.

This is a tool-lego fit probe. It does not promote a lego, coupling, bridge,
axis, or manifold claim.
"""

import json
import os

import numpy as np
from geomstats.geometry.hypersphere import Hypersphere
from geomstats.learning.frechet_mean import FrechetMean

from receipt_boundary import apply_default_receipt_boundary

classification = "tool_lego_fit_probe"
NAME = "sim_geomstats_frechetmean_3pt_s2_micro"
PROBE_FAMILY = "geomstats_frechetmean_3pt_s2_micro"
CONSTRAINT_SET = "bounded_three_point_s2_frechetmean_fixture"
TOL = 1e-6

_NOT_USED_REASON = (
    "not used: this micro probe isolates geomstats FrechetMean on one "
    "three-point S2 fixture; cross-tool coupling and promotion are out of scope."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "pyg": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "z3": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "cvc5": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "sympy": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "clifford": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": (
            "geomstats is load-bearing: FrechetMean.fit on Hypersphere(dim=2) "
            "decides the intrinsic mean, membership, variance, and boundary verdicts."
        ),
    },
    "e3nn": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "xgi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "toponetx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "gudhi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
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

S2 = Hypersphere(dim=2)
BASE = np.array([0.0, 0.0, 1.0])
TANGENT_A = np.array([0.08, 0.0, 0.0])
TANGENT_B = np.array([0.0, 0.06, 0.0])
POINTS = np.array(
    [
        BASE,
        S2.metric.exp(tangent_vec=TANGENT_A, base_point=BASE),
        S2.metric.exp(tangent_vec=TANGENT_B, base_point=BASE),
    ]
)


def _as_vector(point):
    return np.asarray(point, dtype=float).reshape(3)


def _intrinsic_variance(point, points=POINTS):
    distances = [float(S2.metric.dist(point, candidate)) for candidate in points]
    return float(np.sum(np.square(distances))), distances


def _fit_frechet_mean(points=POINTS):
    mean = FrechetMean(space=S2)
    mean.fit(points)
    return _as_vector(mean.estimate_)


def _normalised_euclidean_mean(points=POINTS):
    ambient = np.mean(points, axis=0)
    return ambient / np.linalg.norm(ambient)


def _all_section_admitted(section):
    return all(item.get("admitted", item.get("excluded", False)) for item in section.values())


def run_positive_tests():
    estimate = _fit_frechet_mean()
    belongs = bool(S2.belongs(estimate, atol=TOL))
    variance, distances = _intrinsic_variance(estimate)
    base_variance, _ = _intrinsic_variance(BASE)
    euclidean_unit = _normalised_euclidean_mean()
    distance_to_unit_euclidean = float(S2.metric.dist(estimate, euclidean_unit))

    return {
        "three_point_s2_mean_admitted": {
            "admitted": bool(belongs and variance <= base_variance + TOL),
            "carrier": "ordered finite 3-point subset of Hypersphere(dim=2) in R^3",
            "estimate": estimate.tolist(),
            "belongs_to_s2": belongs,
            "intrinsic_variance": variance,
            "basepoint_variance": base_variance,
            "distances_to_fixture_points": distances,
            "distance_to_normalised_euclidean_mean": distance_to_unit_euclidean,
            "admission_note": (
                "The FrechetMean estimate is admitted only for this pinned "
                "three-point S2 carrier and this intrinsic variance readout."
            ),
        }
    }


def run_negative_tests():
    ambient_mean = np.mean(POINTS, axis=0)
    ambient_norm = float(np.linalg.norm(ambient_mean))
    ambient_belongs = bool(S2.belongs(ambient_mean, atol=TOL))
    frechet_estimate = _fit_frechet_mean()
    frechet_variance, _ = _intrinsic_variance(frechet_estimate)
    unit_ambient = _normalised_euclidean_mean()
    unit_ambient_variance, _ = _intrinsic_variance(unit_ambient)

    return {
        "raw_ambient_average_excluded": {
            "excluded": bool(not ambient_belongs and ambient_norm < 1.0 - TOL),
            "ambient_mean": ambient_mean.tolist(),
            "ambient_norm": ambient_norm,
            "belongs_to_s2": ambient_belongs,
            "exclusion_note": (
                "The raw Euclidean average is excluded as the S2 FrechetMean "
                "readout because it leaves the carrier."
            ),
        },
        "normalised_ambient_average_not_decisive": {
            "excluded": bool(unit_ambient_variance >= frechet_variance - TOL),
            "normalised_ambient_variance": unit_ambient_variance,
            "frechet_variance": frechet_variance,
            "exclusion_note": (
                "A projected Euclidean average is not admitted as the decisive "
                "tool surface; the geomstats FrechetMean objective supplies the verdict."
            ),
        },
    }


def run_boundary_tests():
    duplicate_fixture = np.array([BASE, BASE, POINTS[1]])
    duplicate_estimate = _fit_frechet_mean(duplicate_fixture)
    duplicate_belongs = bool(S2.belongs(duplicate_estimate, atol=TOL))
    duplicate_distance_to_base = float(S2.metric.dist(duplicate_estimate, BASE))

    antipodal_fixture = np.array([BASE, -BASE, POINTS[1]])
    unit_candidates = [np.linalg.norm(point) for point in antipodal_fixture]
    antipodal_input_valid = all(abs(float(norm) - 1.0) <= TOL for norm in unit_candidates)

    return {
        "duplicate_point_boundary_admitted": {
            "admitted": bool(duplicate_belongs and duplicate_distance_to_base < 0.08),
            "carrier": "finite 3-point S2 fixture with a duplicated basepoint",
            "estimate": duplicate_estimate.tolist(),
            "belongs_to_s2": duplicate_belongs,
            "distance_to_basepoint": duplicate_distance_to_base,
            "boundary_note": (
                "The duplicate-point boundary remains a bounded three-point "
                "fixture; no coupling or promotion conclusion follows."
            ),
        },
        "antipodal_boundary_deferred": {
            "admitted": bool(antipodal_input_valid),
            "carrier": "finite 3-point S2 fixture containing an antipodal pair",
            "input_norms": [float(norm) for norm in unit_candidates],
            "boundary_note": (
                "The antipodal fixture is recorded as a valid boundary carrier, "
                "but its cut-locus mean non-uniqueness is deferred outside this micro."
            ),
        },
    }


def _count_admitted(*sections):
    total = 0
    admitted = 0
    for section in sections:
        for item in section.values():
            total += 1
            if item.get("admitted") is True or item.get("excluded") is True:
                admitted += 1
    return admitted, total


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    admitted, total = _count_admitted(positive, negative, boundary)
    all_admitted = admitted == total

    results = {
        "name": NAME,
        "probe_family": PROBE_FAMILY,
        "constraint_set": CONSTRAINT_SET,
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "surviving_alternatives": [
            "Other geomstats FrechetMean fixtures remain uncovered by this micro receipt.",
            "Other Hypersphere dimensions and non-sphere FrechetMean spaces remain separate surfaces.",
        ],
        "claim_ceiling": "tool_lego_fit_probe_only",
        "next_lego_target": "none",
        "promotion_condition": (
            "requires runner execution, result JSON, queue reconciliation, and ledger loopback before citation"
        ),
        "blocked_until": (
            "runner receipt exists and the geomstats tool-depth row is reconciled against the shallow-tool checker"
        ),
        "demotion_condition": (
            "Demote geomstats FrechetMean for this fixture if the estimate leaves S2, "
            "does not reduce intrinsic variance against the basepoint, admits raw ambient averaging, "
            "or loses bounded behavior on the duplicate-point boundary."
        ),
        "out_of_scope": [
            "no lego promotion",
            "no result JSON from authoring-only work",
            "no tool-tool coupling",
            "no bridge, axis, engine, emergence, or manifold claim",
        ],
        "criteria_checked": [
            "FrechetMean estimate belongs to S2 for a pinned three-point fixture",
            "FrechetMean intrinsic variance is bounded against the fixture basepoint",
            "raw Euclidean average is excluded as an S2 readout",
            "projected Euclidean average is not the decisive tool surface",
            "duplicate-point boundary remains bounded",
            "antipodal carrier boundary is recorded but not promoted",
        ],
        "ledger_loopback": {
            "tool_depth_row": "geomstats",
            "threshold": "shallow-tool checker requires >=10 load-bearing geomstats receipts",
            "surface": "FrechetMean on a 3-point Hypersphere(dim=2) fixture",
        },
        "summary": {
            "admitted": admitted,
            "total": total,
            "all_admitted": all_admitted,
            "classification": "tool_lego_fit_probe",
            "promotion_allowed": False,
            "carrier": "ordered finite 3-point subset of Hypersphere(dim=2) in R^3",
            "one_variable": "only geomstats FrechetMean behavior on the pinned fixture is uncertain",
            "claim": (
                "FrechetMean supplies the bounded intrinsic mean readout for one finite "
                "three-point S2 carrier."
            ),
        },
    }
    results = apply_default_receipt_boundary(
        results,
        source_name=NAME,
        target=(
            "Use only as queued geomstats FrechetMean micro-tool evidence after runner execution "
            "and ledger reconciliation."
        ),
    )

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Summary: {admitted}/{total} admitted")

    if not all_admitted:
        raise SystemExit(1)
