#!/usr/bin/env python3
"""Geomstats Hopf/Weyl vertical fiber and horizontal base-lift loop distances."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from geomstats.geometry.hypersphere import Hypersphere
from receipt_boundary import apply_default_receipt_boundary


NAME = "geomstats_hopf_weyl_fiber_horizontal_base_loop_distance"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": "computes intrinsic S3 carrier and S2 projection distances for vertical fiber and horizontal base-lift Hopf/Weyl loop samples",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "constructs sampled Hopf-coordinate carrier arrays and finite-difference tangent controls",
    },
}
TOOL_INTEGRATION_DEPTH = {"geomstats": "load_bearing", "numpy": "supportive"}

S3 = Hypersphere(dim=3)
S2 = Hypersphere(dim=2)


def spinor_s3(theta: float, phi: float, chi: float, sheet_orientation: int) -> np.ndarray:
    if sheet_orientation not in (-1, 1):
        raise ValueError("sheet_orientation must be -1 or +1")
    signed_phi = float(sheet_orientation) * phi
    point = np.asarray(
        [
            math.cos(theta / 2.0) * math.cos((chi + signed_phi) / 2.0),
            math.cos(theta / 2.0) * math.sin((chi + signed_phi) / 2.0),
            math.sin(theta / 2.0) * math.cos((chi - signed_phi) / 2.0),
            math.sin(theta / 2.0) * math.sin((chi - signed_phi) / 2.0),
        ],
        dtype=float,
    )
    return point / float(np.linalg.norm(point))


def bloch_s2(theta: float, phi: float, sheet_orientation: int) -> np.ndarray:
    signed_phi = float(sheet_orientation) * phi
    return np.asarray(
        [
            math.sin(theta) * math.cos(signed_phi),
            math.sin(theta) * math.sin(signed_phi),
            math.cos(theta),
        ],
        dtype=float,
    )


def fiber_path(theta: float, phi: float, chi0: float, sheet_orientation: int, samples: int) -> list[tuple[np.ndarray, np.ndarray]]:
    return [
        (spinor_s3(theta, phi, float(chi), sheet_orientation), bloch_s2(theta, phi, sheet_orientation))
        for chi in np.linspace(chi0, chi0 + 2.0 * math.pi, samples)
    ]


def raw_base_path(theta: float, phi0: float, chi0: float, sheet_orientation: int, samples: int) -> list[tuple[np.ndarray, np.ndarray]]:
    return [
        (spinor_s3(theta, float(phi), chi0, sheet_orientation), bloch_s2(theta, float(phi), sheet_orientation))
        for phi in np.linspace(phi0, phi0 + 2.0 * math.pi, samples)
    ]


def horizontal_base_path(theta: float, phi0: float, chi0: float, sheet_orientation: int, samples: int) -> list[tuple[np.ndarray, np.ndarray]]:
    rows: list[tuple[np.ndarray, np.ndarray]] = []
    for phi in np.linspace(phi0, phi0 + 2.0 * math.pi, samples):
        delta_phi = float(phi - phi0)
        chi = chi0 - float(sheet_orientation) * math.cos(theta) * delta_phi
        rows.append((spinor_s3(theta, float(phi), chi, sheet_orientation), bloch_s2(theta, float(phi), sheet_orientation)))
    return rows


def path_metrics(path: list[tuple[np.ndarray, np.ndarray]]) -> dict[str, float]:
    s3_points = [row[0] for row in path]
    s2_points = [row[1] for row in path]
    s3_steps = [float(S3.metric.dist(s3_points[idx], s3_points[idx + 1])) for idx in range(len(s3_points) - 1)]
    s2_steps = [float(S2.metric.dist(s2_points[idx], s2_points[idx + 1])) for idx in range(len(s2_points) - 1)]
    return {
        "s3_path_length": float(sum(s3_steps)),
        "s2_path_length": float(sum(s2_steps)),
        "s3_start_end_distance": float(S3.metric.dist(s3_points[0], s3_points[-1])),
        "s2_start_end_distance": float(S2.metric.dist(s2_points[0], s2_points[-1])),
        "s3_max_step": float(max(s3_steps)),
        "s2_max_step": float(max(s2_steps)),
    }


def tangent(theta: float, phi: float, chi: float, sheet_orientation: int, mode: str, eps: float = 1e-6) -> np.ndarray:
    if mode == "fiber":
        plus = spinor_s3(theta, phi, chi + eps, sheet_orientation)
        minus = spinor_s3(theta, phi, chi - eps, sheet_orientation)
    elif mode == "raw_base":
        plus = spinor_s3(theta, phi + eps, chi, sheet_orientation)
        minus = spinor_s3(theta, phi - eps, chi, sheet_orientation)
    elif mode == "horizontal_base":
        plus = spinor_s3(theta, phi + eps, chi - float(sheet_orientation) * math.cos(theta) * eps, sheet_orientation)
        minus = spinor_s3(theta, phi - eps, chi + float(sheet_orientation) * math.cos(theta) * eps, sheet_orientation)
    else:
        raise ValueError(f"unknown tangent mode: {mode}")
    return (plus - minus) / (2.0 * eps)


def tangent_controls(theta: float, phi: float, chi: float, sheet_orientation: int) -> dict[str, float]:
    fiber = tangent(theta, phi, chi, sheet_orientation, "fiber")
    raw_base = tangent(theta, phi, chi, sheet_orientation, "raw_base")
    horizontal_base = tangent(theta, phi, chi, sheet_orientation, "horizontal_base")
    return {
        "fiber_norm": float(np.linalg.norm(fiber)),
        "raw_base_norm": float(np.linalg.norm(raw_base)),
        "horizontal_base_norm": float(np.linalg.norm(horizontal_base)),
        "raw_base_fiber_dot": float(np.dot(raw_base, fiber)),
        "horizontal_base_fiber_dot": float(np.dot(horizontal_base, fiber)),
    }


def run_positive() -> dict[str, object]:
    theta = math.pi / 3.0
    phi0 = math.pi / 5.0
    chi0 = math.pi / 7.0
    samples = 513
    fiber = path_metrics(fiber_path(theta, phi0, chi0, 1, samples))
    raw_base = path_metrics(raw_base_path(theta, phi0, chi0, 1, samples))
    horizontal_base = path_metrics(horizontal_base_path(theta, phi0, chi0, 1, samples))
    controls = tangent_controls(theta, phi0, chi0, 1)
    return {
        "theta": theta,
        "phi0": phi0,
        "chi0": chi0,
        "samples": samples,
        "expected_fiber_s3_length": math.pi,
        "expected_horizontal_base_s3_length": math.pi * math.sin(theta),
        "expected_base_s2_length": 2.0 * math.pi * math.sin(theta),
        "fiber_loop": fiber,
        "raw_base_loop": raw_base,
        "horizontal_base_loop": horizontal_base,
        "finite_difference_tangent_controls": controls,
        "survives_geomstats_horizontal_distance": bool(
            abs(fiber["s3_path_length"] - math.pi) < 0.02
            and fiber["s2_path_length"] < 1e-9
            and abs(horizontal_base["s3_path_length"] - math.pi * math.sin(theta)) < 0.02
            and abs(horizontal_base["s2_path_length"] - 2.0 * math.pi * math.sin(theta)) < 0.04
            and abs(controls["raw_base_fiber_dot"]) > 0.1
            and abs(controls["horizontal_base_fiber_dot"]) < 1e-9
        ),
    }


def run_graveyards() -> dict[str, object]:
    theta = math.pi / 3.0
    phi0 = math.pi / 5.0
    chi0 = math.pi / 7.0
    samples = 513
    fiber = path_metrics(fiber_path(theta, phi0, chi0, 1, samples))
    raw_base = path_metrics(raw_base_path(theta, phi0, chi0, 1, samples))
    horizontal_base = path_metrics(horizontal_base_path(theta, phi0, chi0, 1, samples))
    pole_horizontal = path_metrics(horizontal_base_path(0.0, phi0, chi0, 1, samples))
    equator_controls = tangent_controls(math.pi / 2.0, phi0, chi0, 1)
    reversed_horizontal = path_metrics(horizontal_base_path(theta, phi0, chi0, -1, samples))
    controls = tangent_controls(theta, phi0, chi0, 1)
    return {
        "raw_base_path_has_same_length_as_fiber_but_not_same_connection_component": {
            "raw_base_s3_path_length": raw_base["s3_path_length"],
            "fiber_s3_path_length": fiber["s3_path_length"],
            "raw_base_fiber_dot": controls["raw_base_fiber_dot"],
            "passed": bool(abs(raw_base["s3_path_length"] - fiber["s3_path_length"]) < 0.02 and abs(controls["raw_base_fiber_dot"]) > 0.1),
        },
        "horizontal_base_is_metric_orthogonal_to_fiber": {
            "horizontal_base_fiber_dot": controls["horizontal_base_fiber_dot"],
            "passed": bool(abs(controls["horizontal_base_fiber_dot"]) < 1e-9),
        },
        "horizontal_base_collapses_at_projection_pole": {
            "pole_horizontal_s3_path_length": pole_horizontal["s3_path_length"],
            "pole_horizontal_s2_path_length": pole_horizontal["s2_path_length"],
            "passed": bool(pole_horizontal["s3_path_length"] < 1e-9 and pole_horizontal["s2_path_length"] < 1e-9),
        },
        "fiber_motion_is_hidden_by_s2_projection": {
            "fiber_s3_path_length": fiber["s3_path_length"],
            "fiber_s2_path_length": fiber["s2_path_length"],
            "passed": bool(fiber["s3_path_length"] > 3.0 and fiber["s2_path_length"] < 1e-9),
        },
        "equator_raw_base_orthogonality_is_accidental": {
            "equator_raw_base_fiber_dot": equator_controls["raw_base_fiber_dot"],
            "non_equator_raw_base_fiber_dot": controls["raw_base_fiber_dot"],
            "passed": bool(abs(equator_controls["raw_base_fiber_dot"]) < 1e-9 and abs(controls["raw_base_fiber_dot"]) > 0.1),
        },
        "sheet_reversal_preserves_horizontal_metric_lengths": {
            "positive_horizontal_s3_path_length": horizontal_base["s3_path_length"],
            "negative_horizontal_s3_path_length": reversed_horizontal["s3_path_length"],
            "passed": bool(abs(horizontal_base["s3_path_length"] - reversed_horizontal["s3_path_length"]) < 1e-9),
        },
    }


def main() -> int:
    positive = run_positive()
    graveyards = run_graveyards()
    all_pass = bool(
        positive["survives_geomstats_horizontal_distance"]
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "Geomstats sampled-distance baseline for Hopf/Weyl vertical fiber and horizontal base-lift loop geometry only; "
            "it numerically cross-checks local S3/S2 path lengths and finite-difference tangent separation, not physical "
            "loop independence in a full nested Hopf-torus geometric-constraint manifold; no flux representation, no QIT, "
            "no GStack, no axis, no bridge, no nonclassical admission, and no target-system admission"
        ),
        "next_lego_target": "hopf_weyl_carrier_loop_geometry_baseline",
        "promotion_condition": (
            "May only support later geometry planning after symbolic, topology, Clifford/spinor, and physical operator-evolution "
            "receipts reproduce compatible vertical/horizontal separation with adjacent controls."
        ),
        "demotion_condition": (
            "Demote if the horizontal path is not shorter than the raw base/fiber path away from the equator, if finite-difference "
            "horizontal tangent is not orthogonal to fiber, or if pole/fiber/equator/sheet controls do not collapse."
        ),
        "blocked_until": "blocked from target-system claims until full carrier/topology and physical-evolution receipts exist",
        "out_of_scope": [
            "No full nested Hopf-torus manifold or geometric-constraint manifold.",
            "No flux representation or Pauli-boundary shortcut.",
            "No Lindblad, Hamiltonian, thermodynamic, or information-cycle mechanics.",
            "No QIT, GStack, axis, bridge, nonclassical, or target-system admission.",
        ],
        "divergence_log": (
            "This sampled distance packet cross-checks the exact SymPy vertical/horizontal identity packet. It still remains "
            "local coordinate geometry; it does not run a physical carrier stack or admit a target-system axis."
        ),
        "operation_sequence": [
            "sample vertical fiber loop by varying chi at fixed theta and phi",
            "sample raw base loop by varying phi at fixed theta and chi",
            "sample horizontal base lift by varying phi while applying the Hopf connection chi correction",
            "compute Geomstats S3 carrier and S2 projection path lengths",
            "compute finite-difference tangent dot products for fiber, raw base, and horizontal base",
            "run raw-base, horizontal-orthogonal, pole, projection-hidden, equator, and sheet-reversal controls",
        ],
        "carrier_topology": "sampled two-component Hopf-coordinate carrier embedded in S3 with S2 projection; no full nested-torus manifold",
        "observable": "S3/S2 intrinsic path lengths, endpoint distances, finite-difference tangent norms, and tangent dot products",
        "pass_fail_predicate": (
            "fiber S3 length approximates pi and has zero S2 length; horizontal base S3 length approximates pi*sin(theta) "
            "and S2 length approximates 2*pi*sin(theta); raw base has nonzero fiber dot product while horizontal base dot "
            "fiber is zero; adjacent controls collapse as predicted"
        ),
        "graveyards": [
            "raw base path has same length as fiber but not same connection component",
            "horizontal base is metric-orthogonal to fiber",
            "horizontal base collapses at projection pole",
            "fiber motion is hidden by S2 projection",
            "equator raw-base orthogonality is accidental",
            "sheet reversal preserves horizontal metric lengths",
        ],
        "baselines": [
            "SymPy Hopf/Weyl fiber-horizontal-base loop independence identities",
            "Geomstats Hopf/Weyl S3 carrier and S2 projection distance baseline",
            "SciPy Hopf horizontal-lift chi-shift baseline",
        ],
        "alternative_formulations": [
            "QuTiP density-object transport along the same vertical and horizontal paths",
            "Clifford rotor/spinor representation of vertical-horizontal metric separation",
            "GUDHI/TopoNetX finite-cell carrier topology controls",
            "physical operator-evolution fixture over vertical and horizontal carrier paths",
        ],
        "exact_tool_function_needs": {
            "geomstats": ["Hypersphere(dim=3).metric.dist", "Hypersphere(dim=2).metric.dist"],
            "numpy": ["array", "linspace", "linalg.norm", "dot"],
        },
        "lego_or_coupling_target": "hopf_weyl_carrier_loop_geometry_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyards_detail": graveyards,
        "promotion_allowed": False,
        "pass": all_pass,
    }
    results = apply_default_receipt_boundary(results, source_name=f"sim_{NAME}")
    out_path = RESULTS_DIR / f"{NAME}_results.json"
    out_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"PASS={results['pass']}  name={NAME}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
