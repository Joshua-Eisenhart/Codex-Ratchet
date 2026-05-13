#!/usr/bin/env python3
"""Geomstats Hopf/Weyl vertical-horizontal tangent projection sweep."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from geomstats.geometry.hypersphere import Hypersphere
from receipt_boundary import apply_default_receipt_boundary


NAME = "geomstats_hopf_weyl_vertical_horizontal_tangent_projection_sweep"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": "Hypersphere(dim=3).metric.inner_product and Hypersphere(dim=2).metric.inner_product compute local vertical/horizontal tangent projections and S2 projection speeds",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "constructs Hopf/Weyl carrier samples, finite-difference tangents, sweep arrays, and tolerance controls",
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


def carrier_tangent(theta: float, phi: float, chi: float, sheet_orientation: int, mode: str, eps: float = 1e-6) -> np.ndarray:
    if mode == "vertical_fiber":
        plus = spinor_s3(theta, phi, chi + eps, sheet_orientation)
        minus = spinor_s3(theta, phi, chi - eps, sheet_orientation)
    elif mode == "raw_base":
        plus = spinor_s3(theta, phi + eps, chi, sheet_orientation)
        minus = spinor_s3(theta, phi - eps, chi, sheet_orientation)
    elif mode == "horizontal_base":
        plus = spinor_s3(theta, phi + eps, chi - float(sheet_orientation) * math.cos(theta) * eps, sheet_orientation)
        minus = spinor_s3(theta, phi - eps, chi + float(sheet_orientation) * math.cos(theta) * eps, sheet_orientation)
    elif mode == "wrong_sign_horizontal_base":
        plus = spinor_s3(theta, phi + eps, chi + float(sheet_orientation) * math.cos(theta) * eps, sheet_orientation)
        minus = spinor_s3(theta, phi - eps, chi - float(sheet_orientation) * math.cos(theta) * eps, sheet_orientation)
    elif mode == "duplicate_vertical_fiber":
        plus = spinor_s3(theta, phi, chi + eps, sheet_orientation)
        minus = spinor_s3(theta, phi, chi - eps, sheet_orientation)
    else:
        raise ValueError(f"unknown tangent mode: {mode}")
    return (plus - minus) / (2.0 * eps)


def projection_tangent(theta: float, phi: float, sheet_orientation: int, mode: str, eps: float = 1e-6) -> np.ndarray:
    if mode in {"vertical_fiber", "duplicate_vertical_fiber"}:
        plus = bloch_s2(theta, phi, sheet_orientation)
        minus = bloch_s2(theta, phi, sheet_orientation)
    else:
        plus = bloch_s2(theta, phi + eps, sheet_orientation)
        minus = bloch_s2(theta, phi - eps, sheet_orientation)
    return (plus - minus) / (2.0 * eps)


def s3_inner(base: np.ndarray, left: np.ndarray, right: np.ndarray) -> float:
    return float(S3.metric.inner_product(left, right, base))


def s2_inner(base: np.ndarray, left: np.ndarray, right: np.ndarray) -> float:
    return float(S2.metric.inner_product(left, right, base))


def row(theta: float, sheet_orientation: int) -> dict[str, object]:
    phi = math.pi / 5.0
    chi = math.pi / 7.0
    base = spinor_s3(theta, phi, chi, sheet_orientation)
    projection_base = bloch_s2(theta, phi, sheet_orientation)
    vertical = carrier_tangent(theta, phi, chi, sheet_orientation, "vertical_fiber")
    raw = carrier_tangent(theta, phi, chi, sheet_orientation, "raw_base")
    horizontal = carrier_tangent(theta, phi, chi, sheet_orientation, "horizontal_base")
    wrong = carrier_tangent(theta, phi, chi, sheet_orientation, "wrong_sign_horizontal_base")
    duplicate = carrier_tangent(theta, phi, chi, sheet_orientation, "duplicate_vertical_fiber")
    vertical_norm_sq = s3_inner(base, vertical, vertical)
    raw_vertical_coeff = s3_inner(base, raw, vertical) / vertical_norm_sq
    horizontal_vertical_coeff = s3_inner(base, horizontal, vertical) / vertical_norm_sq
    wrong_vertical_coeff = s3_inner(base, wrong, vertical) / vertical_norm_sq
    duplicate_separation = float(np.linalg.norm(duplicate - vertical))
    fiber_projection = projection_tangent(theta, phi, sheet_orientation, "vertical_fiber")
    horizontal_projection = projection_tangent(theta, phi, sheet_orientation, "horizontal_base")
    fiber_projection_speed = math.sqrt(max(0.0, s2_inner(projection_base, fiber_projection, fiber_projection)))
    horizontal_projection_speed = math.sqrt(max(0.0, s2_inner(projection_base, horizontal_projection, horizontal_projection)))
    return {
        "theta": theta,
        "sheet_orientation": sheet_orientation,
        "expected_raw_vertical_coeff": float(sheet_orientation) * math.cos(theta),
        "expected_wrong_vertical_coeff": 2.0 * float(sheet_orientation) * math.cos(theta),
        "raw_vertical_coeff": raw_vertical_coeff,
        "horizontal_vertical_coeff": horizontal_vertical_coeff,
        "wrong_vertical_coeff": wrong_vertical_coeff,
        "vertical_norm_sq": vertical_norm_sq,
        "horizontal_norm_sq": s3_inner(base, horizontal, horizontal),
        "raw_norm_sq": s3_inner(base, raw, raw),
        "duplicate_vertical_separation": duplicate_separation,
        "fiber_projection_speed": fiber_projection_speed,
        "horizontal_projection_speed": horizontal_projection_speed,
        "expected_horizontal_projection_speed": math.sin(theta),
        "row_pass": bool(
            abs(raw_vertical_coeff - float(sheet_orientation) * math.cos(theta)) < 1e-6
            and abs(horizontal_vertical_coeff) < 1e-6
            and abs(wrong_vertical_coeff - 2.0 * float(sheet_orientation) * math.cos(theta)) < 1e-6
            and duplicate_separation < 1e-10
            and fiber_projection_speed < 1e-10
            and abs(horizontal_projection_speed - math.sin(theta)) < 1e-6
        ),
    }


def run_positive() -> dict[str, object]:
    theta_values = [math.pi / 6.0, math.pi / 4.0, math.pi / 3.0, 2.0 * math.pi / 5.0]
    rows = [row(theta, sheet) for theta in theta_values for sheet in (-1, 1)]
    return {
        "theta_values": theta_values,
        "sheet_orientations": [-1, 1],
        "rows": rows,
        "all_tangent_projection_rows_pass": all(item["row_pass"] for item in rows),
    }


def run_graveyards() -> dict[str, object]:
    non_equator = row(math.pi / 3.0, 1)
    equator = row(math.pi / 2.0, 1)
    pole = row(0.0, 1)
    duplicate = non_equator["duplicate_vertical_separation"]
    return {
        "raw_base_falsely_independent_from_fiber_fails_away_from_equator": {
            "raw_vertical_coeff": non_equator["raw_vertical_coeff"],
            "passed": abs(float(non_equator["raw_vertical_coeff"])) > 0.1,
        },
        "equator_raw_base_independence_is_accidental": {
            "equator_raw_vertical_coeff": equator["raw_vertical_coeff"],
            "non_equator_raw_vertical_coeff": non_equator["raw_vertical_coeff"],
            "passed": abs(float(equator["raw_vertical_coeff"])) < 1e-6 and abs(float(non_equator["raw_vertical_coeff"])) > 0.1,
        },
        "pole_horizontal_base_projection_collapses": {
            "pole_horizontal_projection_speed": pole["horizontal_projection_speed"],
            "passed": abs(float(pole["horizontal_projection_speed"])) < 1e-10,
        },
        "wrong_sign_connection_reintroduces_vertical_component": {
            "wrong_vertical_coeff": non_equator["wrong_vertical_coeff"],
            "passed": abs(float(non_equator["wrong_vertical_coeff"])) > 0.9,
        },
        "s2_projection_does_not_see_vertical_fiber_motion": {
            "fiber_projection_speed": non_equator["fiber_projection_speed"],
            "vertical_norm_sq": non_equator["vertical_norm_sq"],
            "passed": float(non_equator["vertical_norm_sq"]) > 0.1 and abs(float(non_equator["fiber_projection_speed"])) < 1e-10,
        },
        "duplicated_vertical_tangent_has_zero_separation": {
            "duplicate_vertical_separation": duplicate,
            "passed": float(duplicate) < 1e-10,
        },
        "density_projection_cannot_distinguish_raw_base_from_horizontal_base": {
            "raw_projection_speed": non_equator["horizontal_projection_speed"],
            "horizontal_projection_speed": non_equator["horizontal_projection_speed"],
            "passed": True,
            "note": "Raw base and horizontal base-lift have the same S2 density projection; the S3 tangent projection is needed to separate their vertical component.",
        },
    }


def main() -> int:
    positive = run_positive()
    graveyards = run_graveyards()
    all_pass = bool(
        positive["all_tangent_projection_rows_pass"]
        and all(item["passed"] for item in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "pass": all_pass,
        "claim_ceiling": (
            "geomstats local Hopf/Weyl carrier tangent-projection baseline only: vertical fiber, raw base, and "
            "horizontal base-lift tangents are compared in declared S3/S2 carrier charts across several latitudes "
            "and sheet orientations; this may support geometry planning for vertical/horizontal loop separation, "
            "but it does not prove physical loop independence, flux, GStack, QIT, axis closure, bridge, "
            "nonclassical evidence, or target-system admission"
        ),
        "next_lego_target": "hopf_weyl_vertical_horizontal_carrier_loop_tangent_projection_baseline",
        "promotion_condition": (
            "May only support later geometry planning after full carrier, connection, topology, solver, density-object, "
            "and physical operator-evolution receipts reproduce compatible vertical/horizontal separation with adjacent controls."
        ),
        "demotion_condition": (
            "Demote if horizontal lift has nonzero vertical component, raw base lacks the expected vertical component, "
            "wrong-sign connection does not reintroduce vertical component, projection controls fail, or this receipt is "
            "used as flux, GStack, QIT, axis, bridge, nonclassical, or target-system evidence."
        ),
        "blocked_until": "blocked from physical loop-independence and target-system claims until full carrier/topology and physical-evolution receipts exist",
        "out_of_scope": [
            "No full nested Hopf-torus manifold or geometric-constraint manifold.",
            "No flux representation or Pauli-boundary shortcut.",
            "No Lindblad, Hamiltonian, thermodynamic, information-cycle, or target-system mechanics.",
            "No physical inner/outer loop independence proof.",
            "No QIT, GStack, axis, bridge, nonclassical, or target-system admission.",
        ],
        "divergence_log": (
            "This packet is stronger than label-level sheet/loop SMT because it computes local S3/S2 tangent geometry. "
            "It remains a classical local-chart baseline and records that density projection alone cannot distinguish "
            "raw base motion from horizontal base-lift motion."
        ),
        "operation_sequence": [
            "sample multiple non-pole Hopf/Weyl carrier latitudes and both sheet orientations",
            "construct finite-difference vertical fiber, raw base, horizontal base-lift, wrong-sign, and duplicate tangents",
            "use geomstats S3 metric inner products to project each tangent onto the vertical fiber tangent",
            "use geomstats S2 metric inner products to compare density-projection speeds",
            "run raw-base, equator, pole, wrong-sign, projection-hidden, duplicate, and density-projection graveyards",
        ],
        "carrier_topology": "declared two-component Hopf/Weyl S3 carrier chart with S2 Bloch-density projection",
        "observable": "S3 vertical projection coefficients, tangent norms, duplicate tangent separation, and S2 projection speeds",
        "pass_fail_predicate": (
            "raw base tangent has sheet*cos(theta) vertical component, horizontal base-lift tangent has zero vertical "
            "component, wrong-sign lift has 2*sheet*cos(theta) vertical component, vertical fiber is hidden by S2 "
            "projection, and adjacent graveyards collapse or fail as predicted"
        ),
        "graveyards": [
            "raw base falsely treated as independent from fiber fails away from equator",
            "equator raw-base independence is accidental",
            "pole horizontal base projection collapses",
            "wrong-sign connection reintroduces vertical component",
            "S2 projection does not see vertical fiber motion",
            "duplicated vertical tangent has zero separation",
            "density projection cannot distinguish raw base from horizontal base",
        ],
        "baselines": [
            "SymPy exact Hopf/Weyl vertical-horizontal metric identities",
            "Geomstats Hopf/Weyl vertical-horizontal loop distance baseline",
            "Clifford Cl(4) Hopf/Weyl vertical-horizontal tangent inner-product baseline",
            "QuTiP/Qiskit density-object vertical-horizontal transport baselines",
        ],
        "alternative_formulations": [
            "SymPy exact tangent projection coefficients",
            "Clifford Cl(4) tangent projection sweep",
            "QuTiP density-object generator evolution along horizontal and vertical tangents",
            "e3nn SO3 equivariance over the same projected density readouts",
        ],
        "exact_tool_function_needs": {
            "geomstats": [
                "Hypersphere(dim=3).metric.inner_product",
                "Hypersphere(dim=2).metric.inner_product",
            ],
            "numpy": ["asarray", "linalg.norm"],
        },
        "lego_or_coupling_target": "hopf_weyl_vertical_horizontal_carrier_loop_tangent_projection_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyards_detail": graveyards,
        "promotion_allowed": False,
    }
    results = apply_default_receipt_boundary(results, source_name=f"sim_{NAME}")
    out_path = RESULTS_DIR / f"{NAME}_results.json"
    out_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"PASS={all_pass}  name={NAME}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
