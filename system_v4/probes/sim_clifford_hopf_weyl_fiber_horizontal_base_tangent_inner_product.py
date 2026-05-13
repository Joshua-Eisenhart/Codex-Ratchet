#!/usr/bin/env python3
"""Clifford Cl(4) Hopf/Weyl fiber and horizontal-base tangent inner products."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from receipt_boundary import apply_default_receipt_boundary


NAME = "clifford_hopf_weyl_fiber_horizontal_base_tangent_inner_product"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "builds Cl(4) carrier tangent vectors and computes inner products for vertical fiber, raw base, and horizontal base-lift directions",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "constructs sampled finite-difference tangent arrays before Cl(4) vector embedding",
    },
}
TOOL_INTEGRATION_DEPTH = {"clifford": "load_bearing", "numpy": "supportive"}

try:
    from clifford import Cl
except Exception as exc:  # pragma: no cover - import failure is receipt data.
    Cl = None
    CLIFFORD_IMPORT_ERROR = repr(exc)
else:
    CLIFFORD_IMPORT_ERROR = None


def spinor_s3(theta: float, phi: float, chi: float, sheet_orientation: int) -> np.ndarray:
    if sheet_orientation not in (-1, 1):
        raise ValueError("sheet_orientation must be -1 or +1")
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


def finite_difference_tangent(theta: float, phi: float, chi: float, sheet_orientation: int, mode: str, eps: float = 1e-6) -> np.ndarray:
    if mode == "fiber":
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


def tangent_readouts(theta: float, phi: float, chi: float, sheet_orientation: int) -> dict[str, float]:
    basis = setup_cl4()
    fiber = cl_vector(finite_difference_tangent(theta, phi, chi, sheet_orientation, "fiber"), basis)
    raw_base = cl_vector(finite_difference_tangent(theta, phi, chi, sheet_orientation, "raw_base"), basis)
    horizontal_base = cl_vector(finite_difference_tangent(theta, phi, chi, sheet_orientation, "horizontal_base"), basis)
    wrong_sign_horizontal = cl_vector(
        finite_difference_tangent(theta, phi, chi, sheet_orientation, "wrong_sign_horizontal_base"),
        basis,
    )
    return {
        "fiber_norm_squared": cl_inner(fiber, fiber),
        "raw_base_norm_squared": cl_inner(raw_base, raw_base),
        "horizontal_base_norm_squared": cl_inner(horizontal_base, horizontal_base),
        "wrong_sign_horizontal_norm_squared": cl_inner(wrong_sign_horizontal, wrong_sign_horizontal),
        "raw_base_fiber_inner_product": cl_inner(raw_base, fiber),
        "horizontal_base_fiber_inner_product": cl_inner(horizontal_base, fiber),
        "wrong_sign_horizontal_fiber_inner_product": cl_inner(wrong_sign_horizontal, fiber),
    }


def run_positive() -> dict[str, object]:
    theta = math.pi / 3.0
    phi = math.pi / 5.0
    chi = math.pi / 7.0
    readouts = tangent_readouts(theta, phi, chi, 1)
    return {
        "theta": theta,
        "phi": phi,
        "chi": chi,
        "sheet_orientation": 1,
        "expected_fiber_norm_squared": 0.25,
        "expected_raw_base_norm_squared": 0.25,
        "expected_horizontal_base_norm_squared": math.sin(theta) ** 2 / 4.0,
        "expected_raw_base_fiber_inner_product": math.cos(theta) / 4.0,
        "tangent_inner_products": readouts,
        "clifford_tangent_controls_pass": bool(
            abs(readouts["fiber_norm_squared"] - 0.25) < 1e-9
            and abs(readouts["raw_base_norm_squared"] - 0.25) < 1e-9
            and abs(readouts["horizontal_base_norm_squared"] - math.sin(theta) ** 2 / 4.0) < 1e-9
            and abs(readouts["raw_base_fiber_inner_product"] - math.cos(theta) / 4.0) < 1e-9
            and abs(readouts["horizontal_base_fiber_inner_product"]) < 1e-9
        ),
    }


def run_graveyards() -> dict[str, object]:
    theta = math.pi / 3.0
    phi = math.pi / 5.0
    chi = math.pi / 7.0
    readouts = tangent_readouts(theta, phi, chi, 1)
    pole = tangent_readouts(0.0, phi, chi, 1)
    equator = tangent_readouts(math.pi / 2.0, phi, chi, 1)
    reversed_sheet = tangent_readouts(theta, phi, chi, -1)
    return {
        "raw_base_tangent_is_not_fiber_independent": {
            "raw_base_fiber_inner_product": readouts["raw_base_fiber_inner_product"],
            "passed": bool(abs(readouts["raw_base_fiber_inner_product"]) > 0.1),
        },
        "horizontal_base_tangent_is_fiber_independent": {
            "horizontal_base_fiber_inner_product": readouts["horizontal_base_fiber_inner_product"],
            "passed": bool(abs(readouts["horizontal_base_fiber_inner_product"]) < 1e-9),
        },
        "wrong_connection_sign_fails_horizontal_independence": {
            "wrong_sign_horizontal_fiber_inner_product": readouts["wrong_sign_horizontal_fiber_inner_product"],
            "passed": bool(abs(readouts["wrong_sign_horizontal_fiber_inner_product"]) > 0.1),
        },
        "horizontal_base_tangent_collapses_at_projection_pole": {
            "pole_horizontal_base_norm_squared": pole["horizontal_base_norm_squared"],
            "passed": bool(abs(pole["horizontal_base_norm_squared"]) < 1e-18),
        },
        "equator_raw_base_independence_is_accidental": {
            "equator_raw_base_fiber_inner_product": equator["raw_base_fiber_inner_product"],
            "non_equator_raw_base_fiber_inner_product": readouts["raw_base_fiber_inner_product"],
            "passed": bool(abs(equator["raw_base_fiber_inner_product"]) < 1e-9 and abs(readouts["raw_base_fiber_inner_product"]) > 0.1),
        },
        "sheet_reversal_flips_raw_connection_sign_not_horizontal_independence": {
            "positive_raw_base_fiber_inner_product": readouts["raw_base_fiber_inner_product"],
            "negative_raw_base_fiber_inner_product": reversed_sheet["raw_base_fiber_inner_product"],
            "negative_horizontal_base_fiber_inner_product": reversed_sheet["horizontal_base_fiber_inner_product"],
            "passed": bool(
                abs(readouts["raw_base_fiber_inner_product"] + reversed_sheet["raw_base_fiber_inner_product"]) < 1e-9
                and abs(reversed_sheet["horizontal_base_fiber_inner_product"]) < 1e-9
            ),
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
            "clifford": {
                "tried": True,
                "used": False,
                "reason": f"import failed: {CLIFFORD_IMPORT_ERROR}",
            },
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
    all_pass = bool(
        positive["clifford_tangent_controls_pass"]
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "Clifford Cl(4) tangent inner-product baseline for declared Hopf/Weyl vertical fiber and horizontal base-lift "
            "directions only; this is local S3 carrier tangent geometry, not physical loop independence in a full nested "
            "Hopf-torus geometric-constraint manifold; no flux representation, no QIT, no GStack, no axis, no bridge, "
            "no nonclassical admission, and no target-system admission"
        ),
        "next_lego_target": "hopf_weyl_carrier_loop_geometry_baseline",
        "promotion_condition": (
            "May only support later geometry planning after symbolic, numerical distance, topology, and physical "
            "operator-evolution receipts reproduce compatible vertical/horizontal separation with adjacent controls."
        ),
        "demotion_condition": (
            "Demote if raw base is treated as independent from fiber, if horizontal base tangent is not orthogonal to "
            "fiber, if the wrong connection sign also passes, or if pole/equator/sheet controls do not collapse."
        ),
        "blocked_until": "blocked from target-system claims until full carrier/topology and physical-evolution receipts exist",
        "out_of_scope": [
            "No full nested Hopf-torus manifold or geometric-constraint manifold.",
            "No flux representation or Pauli-boundary shortcut.",
            "No Lindblad, Hamiltonian, thermodynamic, or information-cycle mechanics.",
            "No QIT, GStack, axis, bridge, nonclassical, or target-system admission.",
        ],
        "divergence_log": (
            "This Cl(4) packet cross-checks the exact SymPy and Geomstats vertical/horizontal geometry receipts using "
            "carrier tangent inner products. It remains local tangent geometry and does not implement the full carrier stack."
        ),
        "operation_sequence": [
            "construct finite-difference S3 carrier tangents for fiber, raw base, and horizontal base-lift directions",
            "embed the four carrier-coordinate tangent arrays as Cl(4) vectors",
            "compute Clifford inner products and squared norms",
            "compare raw-base, horizontal-base, wrong-sign, pole, equator, and sheet-reversal controls",
        ],
        "carrier_topology": "local tangent vectors on a two-component Hopf-coordinate carrier embedded in S3; no full nested-torus manifold",
        "observable": "Cl(4) tangent squared norms and tangent inner products between fiber, raw base, and horizontal base-lift directions",
        "pass_fail_predicate": (
            "fiber and raw-base tangent norms equal 1/4, horizontal-base norm equals sin(theta)^2/4, raw-base/fiber "
            "inner product equals cos(theta)/4, horizontal-base/fiber inner product is zero, and adjacent controls fail or collapse"
        ),
        "graveyards": [
            "raw base tangent is not fiber independent",
            "horizontal base tangent is fiber independent",
            "wrong connection sign fails horizontal independence",
            "horizontal base tangent collapses at projection pole",
            "equator raw-base independence is accidental",
            "sheet reversal flips raw connection sign not horizontal independence",
        ],
        "baselines": [
            "SymPy Hopf/Weyl fiber-horizontal-base loop independence identities",
            "Geomstats Hopf/Weyl fiber-horizontal-base loop distance baseline",
            "Clifford projected Hopf outer-loop rotor readout baseline",
        ],
        "alternative_formulations": [
            "exact symbolic Clifford algebra for the same tangent vectors",
            "QuTiP density-object transport along vertical and horizontal carrier paths",
            "GUDHI/TopoNetX finite-cell carrier topology controls",
            "physical operator-evolution fixture over vertical and horizontal tangent generators",
        ],
        "exact_tool_function_needs": {
            "clifford": ["Cl(4)", "basis blade construction", "vector inner product"],
            "numpy": ["array", "linalg.norm", "finite differences"],
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
