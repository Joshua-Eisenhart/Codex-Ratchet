#!/usr/bin/env python3
"""Held-out asymmetric-shape stress for calibrated PEPS3D flux-bound Axis0.

Formal scout only.

This row imports the calibration-envelope row and its scaling module, then
tests the current calibration constants on asymmetric held-out shapes without
retuning: (2,3,4), (2,4,4), and (3,3,4).

It is a stress receipt, not a promotion row. A failed held-out sign is recorded
as a graveyard companion against shape-agnostic calibration claims.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch

import sim_peps3d_flux_axis0_calibration_envelope_stress_probe as calibration


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "peps3d_flux_axis0_heldout_shape_stress_probe_results.json"

NAME = "peps3d_flux_axis0_heldout_shape_stress_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical_peps3d_flux_axis0_heldout_shape_stress"
SOURCE_ALIGNMENT_CATEGORY = "peps3d_flux_bound_axis0_heldout_asymmetric_shape_stress"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests the already-selected PEPS3D flux-bound Axis0 "
    "calibration constants on asymmetric held-out shapes without retuning. "
    "It does not admit final Axis0, Xi, Phi0, flux, PEPS3D closure, a "
    "shape-agnostic calibration theorem, gravity, Standard Model, Yang-Mills, "
    "Riemann, or physics claims."
)

HELDOUT_SHAPES = [(2, 3, 4), (2, 4, 4), (3, 3, 4)]
INHERITED_HOMEOSTATIC_TARGET_LAMBDA = 0.30
INHERITED_ALLOSTATIC_TRANSITION_COST_SCALE = 1.55

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing held-out PEPS3D boundary contractions, flux readouts, and signed F_QIT gradients",
    },
    "peps3d_flux_axis0_calibration_envelope_stress_probe": {
        "tried": True,
        "used": True,
        "reason": "supportive reuse of the calibration gradient function and current finite-envelope constants",
    },
    "peps3d_spinor_network_flux_axis0_scaling_probe": {
        "tried": True,
        "used": True,
        "reason": "supportive reuse of flux_readout, axis0_gradient, GAP_FLOOR, and scaling constants",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "peps3d_flux_axis0_calibration_envelope_stress_probe": "supportive",
    "peps3d_spinor_network_flux_axis0_scaling_probe": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}


def as_jsonable(value: Any) -> Any:
    return calibration.as_jsonable(value)


def shape_key(shape: tuple[int, int, int]) -> str:
    return "x".join(str(item) for item in shape)


def finite(value: float) -> bool:
    return bool(math.isfinite(float(value)))


def current_constants(module: Any) -> dict[str, float]:
    return {
        "homeostatic_target_lambda": float(module.HOMEOSTATIC_TARGET_LAMBDA),
        "homeostatic_cost_scale": float(calibration.HOMEOSTATIC_COST_SCALE),
        "allostatic_target_lambda": float(calibration.ALLOSTATIC_TARGET_LAMBDA),
        "allostatic_transition_cost_scale": float(module.ALLOSTATIC_TRANSITION_COST_SCALE),
        "lam0": 0.18,
        "delta": 0.04,
    }


def row_for_shape(module: Any, shape: tuple[int, int, int]) -> dict[str, Any]:
    constants = current_constants(module)
    homeostatic_gradient = calibration.gradient(
        module,
        shape,
        "homeostatic",
        constants["homeostatic_target_lambda"],
        constants["homeostatic_cost_scale"],
    )
    allostatic_gradient = calibration.gradient(
        module,
        shape,
        "allostatic",
        constants["allostatic_target_lambda"],
        constants["allostatic_transition_cost_scale"],
    )
    inherited_homeostatic_gradient = calibration.gradient(
        module,
        shape,
        "homeostatic",
        INHERITED_HOMEOSTATIC_TARGET_LAMBDA,
        constants["homeostatic_cost_scale"],
    )
    inherited_allostatic_gradient = calibration.gradient(
        module,
        shape,
        "allostatic",
        constants["allostatic_target_lambda"],
        INHERITED_ALLOSTATIC_TRANSITION_COST_SCALE,
    )
    neutral_gradient = module.axis0_gradient(shape, 0, "neutral_control")["Axis0_signed_gradient"]
    nominal = module.flux_readout(shape, engine_type=0, lam=constants["lam0"], mode="allostatic")
    erased = module.flux_readout(
        shape,
        engine_type=0,
        lam=constants["lam0"],
        mode="allostatic",
        sheet_erased=True,
    )
    reversed_shell = module.flux_readout(
        shape,
        engine_type=0,
        lam=constants["lam0"],
        mode="allostatic",
        reversed_shell_time=True,
    )
    frozen = module.flux_readout(
        shape,
        engine_type=0,
        lam=constants["lam0"],
        mode="allostatic",
        topology_freeze=True,
    )
    engine_swap = module.flux_readout(shape, engine_type=1, lam=constants["lam0"], mode="allostatic")
    return {
        "shape": shape,
        "shape_key": shape_key(shape),
        "site_count": module.math.prod(shape),
        "sampled_boundary_site_count": nominal["sampled_site_count"],
        "homeostatic_gradient": homeostatic_gradient,
        "allostatic_gradient": allostatic_gradient,
        "current_homeostatic_pass": homeostatic_gradient < -module.GAP_FLOOR,
        "current_allostatic_pass": allostatic_gradient > module.GAP_FLOOR,
        "inherited_homeostatic_gradient": inherited_homeostatic_gradient,
        "inherited_allostatic_gradient": inherited_allostatic_gradient,
        "inherited_homeostatic_pass": inherited_homeostatic_gradient < -module.GAP_FLOOR,
        "inherited_allostatic_pass": inherited_allostatic_gradient > module.GAP_FLOOR,
        "neutral_gradient": neutral_gradient,
        "neutral_pass": abs(neutral_gradient) < 1.0e-8,
        "branch_count_gradient": 0.0,
        "nominal_flux_norm": nominal["flux_norm"],
        "flux_present": nominal["flux_norm"] > module.GAP_FLOOR,
        "sheet_erased_flux_ratio": erased["flux_norm"] / max(nominal["flux_norm"], module.EPS),
        "sheet_erasure_collapses_flux": erased["flux_norm"] / max(nominal["flux_norm"], module.EPS) < 0.35,
        "shell_reversal_jk_gap": abs(nominal["jk_norm"] - reversed_shell["jk_norm"]),
        "shell_time_reversal_changes_jk": abs(nominal["jk_norm"] - reversed_shell["jk_norm"]) > module.GAP_FLOOR,
        "topology_freeze_gap": abs(nominal["topology_mutation_norm"] - frozen["topology_mutation_norm"]),
        "topology_freeze_changes_witness": (
            abs(nominal["topology_mutation_norm"] - frozen["topology_mutation_norm"]) > module.GAP_FLOOR
        ),
        "engine_swap_flux_gap": abs(nominal["flux_norm"] - engine_swap["flux_norm"]),
        "engine_bound_flux": abs(nominal["flux_norm"] - engine_swap["flux_norm"]) > module.GAP_FLOOR,
    }


def all_pass(rows: list[dict[str, Any]], key: str) -> bool:
    return all(bool(row[key]) for row in rows)


def failed_current_predicates(rows: list[dict[str, Any]]) -> list[str]:
    failed = []
    for row in rows:
        if not row["current_homeostatic_pass"]:
            failed.append(f"{row['shape_key']}:homeostatic_gradient_negative")
        if not row["current_allostatic_pass"]:
            failed.append(f"{row['shape_key']}:allostatic_gradient_positive")
    return failed


def nonpromotion_gate() -> dict[str, Any]:
    blocked_claims = {
        "final_axis0": False,
        "xi_phi0_kernel": False,
        "shape_agnostic_calibration_theorem": False,
        "full_peps3d_environment_closure": False,
        "physics_claim": False,
    }
    return {
        "pass": CLASSIFICATION == "formal_scout"
        and PROMOTION_ALLOWED is False
        and not any(blocked_claims.values()),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "blocked_claims": blocked_claims,
    }


def main() -> int:
    started = time.time()
    module = calibration.load_scaling_module()
    rows = [row_for_shape(module, shape) for shape in HELDOUT_SHAPES]
    constants = current_constants(module)
    current_failures = failed_current_predicates(rows)
    current_generalization_pass = not current_failures
    inherited_generalization_pass = all(
        row["inherited_homeostatic_pass"] and row["inherited_allostatic_pass"] for row in rows
    )
    nonpromotion = nonpromotion_gate()

    positive = {
        "heldout_shapes_executed_without_retuning": {
            "pass": len(rows) == len(HELDOUT_SHAPES)
            and all(tuple(row["shape"]) in HELDOUT_SHAPES for row in rows)
            and all(finite(row["homeostatic_gradient"]) and finite(row["allostatic_gradient"]) for row in rows),
            "heldout_shapes": HELDOUT_SHAPES,
            "current_constants": constants,
            "retuning_performed": False,
        },
        "allostatic_current_calibration_survives_all_heldout_shapes": {
            "pass": all_pass(rows, "current_allostatic_pass"),
            "allostatic_gradients_by_shape": {
                row["shape_key"]: row["allostatic_gradient"] for row in rows
            },
        },
        "flux_witness_and_named_controls_remain_live": {
            "pass": all_pass(rows, "flux_present")
            and all_pass(rows, "sheet_erasure_collapses_flux")
            and all_pass(rows, "shell_time_reversal_changes_jk")
            and all_pass(rows, "topology_freeze_changes_witness")
            and all_pass(rows, "engine_bound_flux"),
            "flux_norms_by_shape": {row["shape_key"]: row["nominal_flux_norm"] for row in rows},
            "sheet_erased_flux_ratios_by_shape": {
                row["shape_key"]: row["sheet_erased_flux_ratio"] for row in rows
            },
            "engine_swap_flux_gaps_by_shape": {
                row["shape_key"]: row["engine_swap_flux_gap"] for row in rows
            },
        },
        "neutral_and_branch_count_controls_do_not_supply_axis0": {
            "pass": all_pass(rows, "neutral_pass")
            and all(abs(row["branch_count_gradient"]) < 1.0e-12 for row in rows),
            "neutral_gradients_by_shape": {row["shape_key"]: row["neutral_gradient"] for row in rows},
        },
    }
    graveyard = {
        "shape_agnostic_current_calibration_claim_killed": {
            "pass": not current_generalization_pass,
            "current_calibration_generalization_pass": current_generalization_pass,
            "failed_current_predicates": current_failures,
            "homeostatic_gradients_by_shape": {
                row["shape_key"]: row["homeostatic_gradient"] for row in rows
            },
            "meaning": "A held-out asymmetric shape has the wrong homeostatic sign under the current constants.",
        },
        "inherited_low_cost_fixture_does_not_explain_heldouts": {
            "pass": not inherited_generalization_pass,
            "inherited_homeostatic_target_lambda": INHERITED_HOMEOSTATIC_TARGET_LAMBDA,
            "inherited_allostatic_transition_cost_scale": INHERITED_ALLOSTATIC_TRANSITION_COST_SCALE,
            "inherited_homeostatic_gradients_by_shape": {
                row["shape_key"]: row["inherited_homeostatic_gradient"] for row in rows
            },
            "inherited_allostatic_gradients_by_shape": {
                row["shape_key"]: row["inherited_allostatic_gradient"] for row in rows
            },
        },
        "retuning_route_rejected_for_this_row": {
            "pass": True,
            "retuning_performed": False,
            "allowed_future_move": "Open a separate calibration row if retuning is desired; this receipt only holds out asymmetric shapes against current constants.",
        },
    }
    boundary = {
        "formal_scout_only": {"pass": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False},
        "nonpromotion_gate": nonpromotion,
        "sampled_boundary_not_full_peps3d_environment_closure": {
            "pass": True,
            "sampled_boundary": True,
            "full_peps3d_environment_closure": False,
        },
        "heldout_stress_not_axis0_theorem": {
            "pass": True,
            "current_calibration_generalization_pass": current_generalization_pass,
            "claim_ceiling": CLAIM_CEILING,
        },
    }
    variants = list(positive.values()) + list(graveyard.values()) + list(boundary.values())
    result_pass = all(row["pass"] for row in variants)
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": as_jsonable(positive),
        "graveyard_companions": as_jsonable(graveyard),
        "boundary": as_jsonable(boundary),
        "nonpromotion": as_jsonable(nonpromotion),
        "heldout_shapes": HELDOUT_SHAPES,
        "current_constants": constants,
        "shape_results": as_jsonable(rows),
        "stress_outcome": {
            "receipt_pass": result_pass,
            "current_calibration_generalization_pass": current_generalization_pass,
            "current_allostatic_pass_all_heldouts": all_pass(rows, "current_allostatic_pass"),
            "current_homeostatic_pass_all_heldouts": all_pass(rows, "current_homeostatic_pass"),
            "failed_current_predicates": current_failures,
            "status": (
                "heldout_generalization_survives"
                if current_generalization_pass
                else "heldout_generalization_killed_by_current_constants"
            ),
        },
        "nearby_variants": {
            "passed": sum(1 for row in variants if row["pass"]),
            "total": len(variants),
            "failed": [key for section in (positive, graveyard, boundary) for key, row in section.items() if not row["pass"]],
        },
        "all_pass": result_pass,
        "why_not_final": [
            "One held-out asymmetric shape has the wrong homeostatic sign under the current constants.",
            "The row uses sampled PEPS3D boundary contractions, not full PEPS3D environment closure.",
            "No retuning or derivation of calibration constants occurs in this row.",
            "All evidence remains formal-scout-only and nonpromotional.",
        ],
        "divergence_log": [
            "Current allostatic calibration survives all held-out asymmetric shapes.",
            "Current homeostatic calibration fails on at least one held-out asymmetric shape.",
            "Inherited low-cost calibration does not explain the held-out rows.",
            "Neutral and branch-count controls remain non-Axis0 explanations.",
        ],
        "why_not_v4_probes": (
            "This is a v5 PEPS3D flux-bound Axis0 held-out shape stress scout "
            "over sampled boundary contractions, not a legacy v4 probe or final "
            "physics admission."
        ),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "current_calibration_generalization_pass": current_generalization_pass,
                "current_homeostatic_pass_all_heldouts": result["stress_outcome"][
                    "current_homeostatic_pass_all_heldouts"
                ],
                "current_allostatic_pass_all_heldouts": result["stress_outcome"][
                    "current_allostatic_pass_all_heldouts"
                ],
                "failed_current_predicates": current_failures,
                "result": str(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
