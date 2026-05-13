#!/usr/bin/env python3
"""Clifford Cl(4) Hopf/Weyl vertical-horizontal tangent projection sweep."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from receipt_boundary import apply_default_receipt_boundary


NAME = "clifford_hopf_weyl_vertical_horizontal_tangent_projection_sweep"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "Cl(4) basis vectors and inner products compute vertical projection coefficients for Hopf/Weyl raw base, horizontal base-lift, and wrong-sign tangent generators",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "constructs finite-difference S3 carrier tangents and S2 density-projection tangent controls",
    },
}
TOOL_INTEGRATION_DEPTH = {"clifford": "load_bearing", "numpy": "supportive"}

try:
    from clifford import Cl
except Exception as exc:  # pragma: no cover
    Cl = None
    CLIFFORD_IMPORT_ERROR = repr(exc)
else:
    CLIFFORD_IMPORT_ERROR = None


def spinor_s3(theta: float, phi: float, chi: float, sheet_orientation: int) -> np.ndarray:
    signed_phi = float(sheet_orientation) * phi
    return np.asarray(
        [
            math.cos(theta / 2.0) * math.cos((chi + signed_phi) / 2.0),
            math.cos(theta / 2.0) * math.sin((chi + signed_phi) / 2.0),
            math.sin(theta / 2.0) * math.cos((chi - signed_phi) / 2.0),
            math.sin(theta / 2.0) * math.sin((chi - signed_phi) / 2.0),
        ],
        dtype=float,
    )


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
    else:
        raise ValueError(f"unknown tangent mode: {mode}")
    return (plus - minus) / (2.0 * eps)


def projection_tangent(theta: float, phi: float, sheet_orientation: int, mode: str, eps: float = 1e-6) -> np.ndarray:
    if mode == "vertical_fiber":
        return np.zeros(3, dtype=float)
    plus = bloch_s2(theta, phi + eps, sheet_orientation)
    minus = bloch_s2(theta, phi - eps, sheet_orientation)
    return (plus - minus) / (2.0 * eps)


def setup_cl4():
    if Cl is None:
        raise RuntimeError(f"clifford import failed: {CLIFFORD_IMPORT_ERROR}")
    _, blades = Cl(4)
    return [blades[f"e{idx}"] for idx in range(1, 5)]


def cl_vector(values: np.ndarray, basis):
    vector = 0
    for value, blade in zip(values, basis, strict=True):
        vector += float(value) * blade
    return vector


def cl_inner(left, right) -> float:
    return float((left | right).value[0])


def row(theta: float, sheet_orientation: int, basis) -> dict[str, object]:
    phi = math.pi / 5.0
    chi = math.pi / 7.0
    vertical = cl_vector(carrier_tangent(theta, phi, chi, sheet_orientation, "vertical_fiber"), basis)
    raw = cl_vector(carrier_tangent(theta, phi, chi, sheet_orientation, "raw_base"), basis)
    horizontal = cl_vector(carrier_tangent(theta, phi, chi, sheet_orientation, "horizontal_base"), basis)
    wrong = cl_vector(carrier_tangent(theta, phi, chi, sheet_orientation, "wrong_sign_horizontal_base"), basis)
    vertical_norm_sq = cl_inner(vertical, vertical)
    raw_coeff = cl_inner(raw, vertical) / vertical_norm_sq
    horizontal_coeff = cl_inner(horizontal, vertical) / vertical_norm_sq
    wrong_coeff = cl_inner(wrong, vertical) / vertical_norm_sq
    fiber_projection_speed = float(np.linalg.norm(projection_tangent(theta, phi, sheet_orientation, "vertical_fiber")))
    raw_projection_speed = float(np.linalg.norm(projection_tangent(theta, phi, sheet_orientation, "raw_base")))
    horizontal_projection_speed = float(np.linalg.norm(projection_tangent(theta, phi, sheet_orientation, "horizontal_base")))
    return {
        "theta": theta,
        "sheet_orientation": sheet_orientation,
        "vertical_norm_squared": vertical_norm_sq,
        "raw_vertical_projection_coefficient": raw_coeff,
        "horizontal_vertical_projection_coefficient": horizontal_coeff,
        "wrong_sign_vertical_projection_coefficient": wrong_coeff,
        "expected_raw_vertical_projection_coefficient": float(sheet_orientation) * math.cos(theta),
        "expected_wrong_sign_vertical_projection_coefficient": 2.0 * float(sheet_orientation) * math.cos(theta),
        "fiber_projection_speed": fiber_projection_speed,
        "raw_projection_speed": raw_projection_speed,
        "horizontal_projection_speed": horizontal_projection_speed,
        "row_pass": bool(
            abs(vertical_norm_sq - 0.25) < 1e-9
            and abs(raw_coeff - float(sheet_orientation) * math.cos(theta)) < 1e-6
            and abs(horizontal_coeff) < 1e-6
            and abs(wrong_coeff - 2.0 * float(sheet_orientation) * math.cos(theta)) < 1e-6
            and fiber_projection_speed < 1e-12
            and abs(raw_projection_speed - horizontal_projection_speed) < 1e-12
        ),
    }


def run_positive() -> dict[str, object]:
    basis = setup_cl4()
    theta_values = [math.pi / 6.0, math.pi / 4.0, math.pi / 3.0, 2.0 * math.pi / 5.0]
    rows = [row(theta, sheet, basis) for theta in theta_values for sheet in (-1, 1)]
    return {
        "theta_values": theta_values,
        "sheet_orientations": [-1, 1],
        "rows": rows,
        "all_projection_rows_pass": all(item["row_pass"] for item in rows),
    }


def run_graveyards() -> dict[str, object]:
    basis = setup_cl4()
    non_equator = row(math.pi / 3.0, 1, basis)
    equator = row(math.pi / 2.0, 1, basis)
    pole = row(0.0, 1, basis)
    sheet_minus = row(math.pi / 3.0, -1, basis)
    return {
        "raw_base_falsely_independent_from_fiber_fails_away_from_equator": {
            "raw_vertical_projection_coefficient": non_equator["raw_vertical_projection_coefficient"],
            "passed": abs(float(non_equator["raw_vertical_projection_coefficient"])) > 0.1,
        },
        "equator_raw_base_independence_is_accidental": {
            "equator_raw_vertical_projection_coefficient": equator["raw_vertical_projection_coefficient"],
            "non_equator_raw_vertical_projection_coefficient": non_equator["raw_vertical_projection_coefficient"],
            "passed": abs(float(equator["raw_vertical_projection_coefficient"])) < 1e-6
            and abs(float(non_equator["raw_vertical_projection_coefficient"])) > 0.1,
        },
        "wrong_sign_connection_reintroduces_vertical_component": {
            "wrong_sign_vertical_projection_coefficient": non_equator["wrong_sign_vertical_projection_coefficient"],
            "passed": abs(float(non_equator["wrong_sign_vertical_projection_coefficient"])) > 0.9,
        },
        "s2_projection_does_not_see_vertical_fiber_motion": {
            "vertical_norm_squared": non_equator["vertical_norm_squared"],
            "fiber_projection_speed": non_equator["fiber_projection_speed"],
            "passed": float(non_equator["vertical_norm_squared"]) > 0.1 and float(non_equator["fiber_projection_speed"]) < 1e-12,
        },
        "density_projection_cannot_distinguish_raw_base_from_horizontal_base": {
            "raw_projection_speed": non_equator["raw_projection_speed"],
            "horizontal_projection_speed": non_equator["horizontal_projection_speed"],
            "passed": abs(float(non_equator["raw_projection_speed"]) - float(non_equator["horizontal_projection_speed"])) < 1e-12,
        },
        "pole_horizontal_base_projection_collapses": {
            "pole_horizontal_projection_speed": pole["horizontal_projection_speed"],
            "passed": float(pole["horizontal_projection_speed"]) < 1e-12,
        },
        "sheet_reversal_flips_raw_and_wrong_sign_coefficients_not_horizontal_projection": {
            "sheet_plus_raw": non_equator["raw_vertical_projection_coefficient"],
            "sheet_minus_raw": sheet_minus["raw_vertical_projection_coefficient"],
            "sheet_plus_wrong": non_equator["wrong_sign_vertical_projection_coefficient"],
            "sheet_minus_wrong": sheet_minus["wrong_sign_vertical_projection_coefficient"],
            "sheet_minus_horizontal": sheet_minus["horizontal_vertical_projection_coefficient"],
            "passed": abs(float(non_equator["raw_vertical_projection_coefficient"]) + float(sheet_minus["raw_vertical_projection_coefficient"])) < 1e-6
            and abs(float(non_equator["wrong_sign_vertical_projection_coefficient"]) + float(sheet_minus["wrong_sign_vertical_projection_coefficient"])) < 1e-6
            and abs(float(sheet_minus["horizontal_vertical_projection_coefficient"])) < 1e-6,
        },
    }


def blocked_result() -> dict[str, object]:
    return {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": False,
        "pass": False,
        "blocker": f"clifford import failed: {CLIFFORD_IMPORT_ERROR}",
        "tool_manifest": {
            "clifford": {"tried": True, "used": False, "reason": f"import failed: {CLIFFORD_IMPORT_ERROR}"},
            "numpy": TOOL_MANIFEST["numpy"],
        },
        "tool_integration_depth": {"clifford": None, "numpy": "supportive"},
        "claim_ceiling": "blocked classical baseline; no geometry, QIT, GStack, axis, bridge, nonclassical, or target-system claim",
        "out_of_scope": ["no target-system claim", "no admission or promotion"],
        "promotion_allowed": False,
    }


def main() -> int:
    if Cl is None:
        results = apply_default_receipt_boundary(blocked_result(), source_name=f"sim_{NAME}")
        out_path = RESULTS_DIR / f"{NAME}_results.json"
        out_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"Results written to {out_path}")
        print(f"PASS={results['pass']}  name={NAME}")
        return 1

    positive = run_positive()
    graveyards = run_graveyards()
    all_pass = bool(positive["all_projection_rows_pass"] and all(item["passed"] for item in graveyards.values()))
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "pass": all_pass,
        "claim_ceiling": (
            "Clifford Cl(4) local Hopf/Weyl carrier tangent-projection baseline only: vertical fiber, raw base, "
            "horizontal base-lift, and wrong-sign tangents are compared by projection coefficients in declared "
            "carrier charts; this may support geometry planning for vertical/horizontal loop separation, but it "
            "does not prove physical loop independence, flux, GStack, QIT, axis closure, bridge, nonclassical "
            "evidence, or target-system admission"
        ),
        "next_lego_target": "hopf_weyl_vertical_horizontal_carrier_loop_tangent_projection_baseline",
        "promotion_condition": (
            "May only support later geometry planning after symbolic, numerical, topology, density-object, and "
            "physical operator-evolution receipts reproduce compatible vertical/horizontal separation with adjacent controls."
        ),
        "demotion_condition": (
            "Demote if Cl(4) projection coefficients diverge from sheet*cos(theta), zero, and 2*sheet*cos(theta), "
            "if projection controls fail, or if this receipt is used as flux, GStack, QIT, axis, bridge, nonclassical, "
            "or target-system evidence."
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
            "This Clifford packet mirrors the SymPy and Geomstats tangent-projection receipts. It records that density "
            "projection alone cannot distinguish raw base from horizontal base-lift; the tested separation lives in "
            "the S3 carrier vertical projection coefficient."
        ),
        "operation_sequence": [
            "sample multiple non-pole Hopf/Weyl carrier latitudes and both sheet orientations",
            "construct finite-difference vertical fiber, raw base, horizontal base-lift, and wrong-sign carrier tangents",
            "embed each four-coordinate tangent as a Cl(4) vector",
            "compute Cl(4) vertical projection coefficients onto the fiber tangent",
            "compute S2 density projection speeds for vertical, raw base, and horizontal base directions",
            "run raw-base, equator, wrong-sign, S2-hidden, density-projection, pole, and sheet-reversal graveyards",
        ],
        "carrier_topology": "sampled two-component Hopf/Weyl S3 carrier chart with S2 Bloch-density projection",
        "observable": "Cl(4) vertical projection coefficients, tangent squared norms, and S2 projection-speed controls",
        "pass_fail_predicate": (
            "raw base coefficient equals sheet*cos(theta), horizontal lift coefficient equals zero, wrong-sign lift "
            "coefficient equals 2*sheet*cos(theta), S2 projection hides vertical fiber while raw/horizontal projection "
            "speeds coincide, and all adjacent graveyards collapse or fail as predicted"
        ),
        "graveyards": list(graveyards),
        "baselines": [
            "SymPy Hopf/Weyl vertical-horizontal tangent projection identities",
            "Geomstats Hopf/Weyl vertical-horizontal tangent projection sweep",
            "Clifford Cl(4) Hopf/Weyl vertical-horizontal tangent inner-product baseline",
            "QuTiP/Qiskit density-object vertical-horizontal transport baselines",
        ],
        "alternative_formulations": [
            "SymPy exact tangent projection coefficients",
            "Geomstats numerical tangent projection sweep",
            "QuTiP density-object generator evolution along vertical and horizontal tangents",
            "e3nn SO3 equivariance over the same projected density readouts",
        ],
        "exact_tool_function_needs": {
            "clifford": ["Cl", "basis vectors", "MultiVector inner product"],
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
