#!/usr/bin/env python3
"""Calibration-rule derivation blocker for PEPS3D flux-bound Axis0.

Formal scout only.

The held-out shape stress killed the current shape-agnostic calibration:
homeostasis flips sign on (3, 3, 4). This row tries the smallest admissible
repair family before further retuning:

    lambda_home(shape) = 0.36 + beta * normalized_shape_asymmetry(shape)

The rule is intentionally simple and finite. It must pass the already-green
source shapes by construction at beta=0, then pass all asymmetric held-out
shapes without per-shape constants. The beta family fails, so this receipt is
a blocker: calibration still has to be derived from richer runtime/boundary
structure, not patched by a monotone shape asymmetry scalar.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys
import time
from typing import Any

import torch


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "peps3d_flux_axis0_calibration_rule_derivation_blocker_probe_results.json"
CALIBRATION_MODULE_PATH = ROOT / "sim_peps3d_flux_axis0_calibration_envelope_stress_probe.py"
SCALING_RECEIPT = RESULT_DIR / "peps3d_spinor_network_flux_axis0_scaling_probe_results.json"
ENVELOPE_RECEIPT = RESULT_DIR / "peps3d_flux_axis0_calibration_envelope_stress_probe_results.json"
HELDOUT_RECEIPT = RESULT_DIR / "peps3d_flux_axis0_heldout_shape_stress_probe_results.json"

NAME = "peps3d_flux_axis0_calibration_rule_derivation_blocker_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical_peps3d_flux_axis0_calibration_rule_derivation_blocker"
SOURCE_ALIGNMENT_CATEGORY = "peps3d_flux_bound_axis0_calibration_rule_blocker"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tries a finite shape-adaptive homeostatic calibration "
    "rule against source and held-out PEPS3D flux-bound Axis0 receipts. It "
    "does not admit final Axis0, Xi, Phi0, flux, PEPS3D closure, a "
    "calibration theorem, gravity, Standard Model, Yang-Mills, Riemann, or "
    "physics claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing tensor arithmetic for finite beta-grid margins and sign checks",
    },
    "peps3d_flux_axis0_calibration_envelope_stress_probe": {
        "tried": True,
        "used": True,
        "reason": "supportive recomputation of held-out homeostatic gradients under candidate calibration rules",
    },
    "peps3d_spinor_network_flux_axis0_scaling_probe": {
        "tried": True,
        "used": True,
        "reason": "supportive receipt input for source shape sign margins",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive receipt IO and result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive path handling"},
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

HELDOUT_SHAPES = [(2, 3, 4), (2, 4, 4), (3, 3, 4)]
BETA_GRID = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
BASE_HOMEOSTATIC_TARGET = 0.36
HOMEOSTATIC_COST_SCALE = 0.06
GAP_FLOOR = 1.0e-5


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    return value


def load_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_calibration_module() -> Any:
    sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location("peps3d_axis0_calibration", CALIBRATION_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {CALIBRATION_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def shape_key(shape: tuple[int, int, int]) -> str:
    return "x".join(str(item) for item in shape)


def normalized_shape_asymmetry(shape: tuple[int, int, int]) -> float:
    a, b, c = shape
    return (abs(a - b) + abs(b - c) + abs(a - c)) / float(a + b + c)


def target_for(shape: tuple[int, int, int], beta: float) -> float:
    return BASE_HOMEOSTATIC_TARGET + beta * normalized_shape_asymmetry(shape)


def main() -> int:
    started = time.time()
    scaling = load_json(SCALING_RECEIPT)
    envelope = load_json(ENVELOPE_RECEIPT)
    heldout = load_json(HELDOUT_RECEIPT)
    calibration = load_calibration_module()
    scaling_module = calibration.load_scaling_module()

    source_home = {
        key: row["homeostatic"]
        for key, row in scaling["positive"]["axis0_signed_gradient_scaling_controls"]["gradients"].items()
    }
    envelope_passing_lambdas = envelope["envelope_summary"]["passing_homeostatic_target_lambdas"]
    heldout_current = heldout["graveyard_companions"]["shape_agnostic_current_calibration_claim_killed"][
        "homeostatic_gradients_by_shape"
    ]

    beta_rows: list[dict[str, Any]] = []
    for beta in BETA_GRID:
        gradients: dict[str, float] = {}
        targets: dict[str, float] = {}
        for shape in HELDOUT_SHAPES:
            key = shape_key(shape)
            lam = target_for(shape, beta)
            targets[key] = lam
            gradients[key] = calibration.gradient(
                scaling_module,
                shape,
                "homeostatic",
                lam,
                HOMEOSTATIC_COST_SCALE,
            )
        values = torch.tensor(list(gradients.values()), dtype=torch.float64)
        beta_rows.append(
            {
                "beta": beta,
                "targets_by_shape": targets,
                "heldout_homeostatic_gradients_by_shape": gradients,
                "pass_all_heldouts": bool(torch.all(values < -GAP_FLOOR).item()),
                "worst_value": float(torch.max(values).item()),
                "min_abs_margin": float(torch.min(torch.abs(values)).item()),
            }
        )

    passing_betas = [row["beta"] for row in beta_rows if row["pass_all_heldouts"]]
    source_anchor_pass = all(value < -GAP_FLOOR for value in source_home.values()) and BASE_HOMEOSTATIC_TARGET in envelope_passing_lambdas
    current_heldout_failure_present = any(value > GAP_FLOOR for value in heldout_current.values())
    no_simple_rule_pass = len(passing_betas) == 0
    beta_cross_pressure = any(
        row["heldout_homeostatic_gradients_by_shape"]["2x3x4"] > GAP_FLOOR
        and row["heldout_homeostatic_gradients_by_shape"]["3x3x4"] < -GAP_FLOOR
        for row in beta_rows
    )

    checks = {
        "P1_source_anchor_receipts_green_at_base_target": source_anchor_pass,
        "P2_current_heldout_shape_failure_present": current_heldout_failure_present,
        "P3_simple_shape_asymmetry_beta_grid_has_no_passing_rule": no_simple_rule_pass,
        "P4_beta_grid_exposes_cross_shape_pressure": beta_cross_pressure,
        "P5_allostatic_current_still_survives_heldouts": heldout["positive"][
            "allostatic_current_calibration_survives_all_heldout_shapes"
        ]["pass"],
        "P6_nonpromotion_boundary_intact": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False,
    }
    positive = {
        "receipts_loaded_and_reused": {
            "pass": checks["P1_source_anchor_receipts_green_at_base_target"] and checks["P2_current_heldout_shape_failure_present"],
            "source_homeostatic_gradients_by_site_count": source_home,
            "heldout_current_homeostatic_gradients_by_shape": heldout_current,
        },
        "simple_rule_family_executed": {
            "pass": len(beta_rows) == len(BETA_GRID),
            "beta_grid": BETA_GRID,
            "base_homeostatic_target_lambda": BASE_HOMEOSTATIC_TARGET,
        },
    }
    graveyard = {
        "monotone_shape_asymmetry_rule_not_admitted": {
            "pass": checks["P3_simple_shape_asymmetry_beta_grid_has_no_passing_rule"],
            "passing_betas": passing_betas,
            "meaning": "No tested monotone beta rule fixes every asymmetric held-out shape without per-shape constants.",
        },
        "shape_scalar_cross_pressure": {
            "pass": checks["P4_beta_grid_exposes_cross_shape_pressure"],
            "meaning": "The beta range that fixes 3x3x4 starts breaking 2x3x4, so a one-scalar shape correction is too shallow.",
        },
    }
    boundary = {
        "formal_scout_only": {"pass": checks["P6_nonpromotion_boundary_intact"]},
        "calibration_loop_still_blocked": {
            "pass": checks["P3_simple_shape_asymmetry_beta_grid_has_no_passing_rule"],
            "next_admissible_step": "bind PEPS3D Axis0 rows to source runtime records and boundary functional before another calibration family is promoted",
        },
    }
    variants = list(positive.values()) + list(graveyard.values()) + list(boundary.values())
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
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "beta_rows": beta_rows,
        "checks": checks,
        "calibration_status": "blocked_simple_shape_rule_no_admission",
        "nearby_variants": {
            "passed": sum(1 for row in variants if row["pass"]) + sum(1 for value in checks.values() if value),
            "total": len(variants) + len(checks),
            "failed_checks": [key for key, value in checks.items() if not value],
        },
        "all_pass": all(checks.values()) and all(row["pass"] for row in variants),
        "why_not_final": [
            "The tested calibration family is explicitly killed, not admitted.",
            "The row still uses sampled/local PEPS3D receipts and spot recomputation, not full PEPS3D closure.",
            "Axis0 remains a flux-bound FEP-gradient scout; Xi/Phi0 and physics claims remain blocked.",
        ],
        "divergence_log": [
            "Held-out allostatic signs survive while homeostatic calibration does not.",
            "Path/count-only and neutral explanations remain excluded by upstream receipts.",
            "A one-scalar shape-asymmetry update is too shallow for the current PEPS3D flux-bound Axis0 row.",
        ],
        "why_not_v4_probes": "This is a v5 PEPS3D flux-bound Axis0 calibration blocker, not a legacy v4 probe.",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "status": result["calibration_status"], "passing_betas": passing_betas}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
