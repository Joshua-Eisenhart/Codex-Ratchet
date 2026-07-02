#!/usr/bin/env python3
"""Calibration-envelope stress probe for scaled PEPS3D flux-bound Axis0.

Formal scout only.

The scaled PEPS3D row survives 8/27/64 sampled boundary carriers under an
explicit F_QIT calibration. This row stress-tests that calibration as an
envelope rather than treating the selected constants as admitted theory.

It asks three narrower questions:

* Does the current calibration sit inside a finite passing envelope?
* Do inherited / nearby wrong fixtures fail?
* Is the envelope narrow enough to keep final Axis0 and final flux blocked?

This is not full PEPS3D closure and does not admit a calibration-free Axis0.
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
OUT_PATH = RESULT_DIR / "peps3d_flux_axis0_calibration_envelope_stress_probe_results.json"
SCALING_MODULE_PATH = ROOT / "sim_peps3d_spinor_network_flux_axis0_scaling_probe.py"

NAME = "peps3d_flux_axis0_calibration_envelope_stress_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical_peps3d_flux_axis0_calibration_envelope_stress"
SOURCE_ALIGNMENT_CATEGORY = "peps3d_flux_bound_axis0_fep_calibration_envelope"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: stress-tests the explicit F_QIT calibration envelope "
    "for PEPS3D flux-bound Axis0 across 8/27/64 sampled boundary carriers. "
    "It does not admit final Axis0, Xi, Phi0, flux, PEPS3D closure, gravity, "
    "Standard Model, Yang-Mills, Riemann, or physics claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing gradient recomputation over finite calibration grids and PEPS3D flux readouts",
    },
    "peps3d_spinor_network_flux_axis0_scaling_probe": {
        "tried": True,
        "used": True,
        "reason": "supportive reuse of the exact scaled PEPS3D flux-bound Axis0 functions under finite calibration sweeps",
    },
    "python_importlib": {"tried": True, "used": True, "reason": "supportive local module loading"},
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "peps3d_spinor_network_flux_axis0_scaling_probe": "supportive",
    "python_importlib": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

HOMEOSTATIC_TARGET_GRID = [0.26, 0.30, 0.32, 0.34, 0.36, 0.38, 0.42]
ALLOSTATIC_COST_GRID = [1.55, 2.50, 3.50, 4.50, 5.00, 5.50, 6.50]
HOMEOSTATIC_COST_SCALE = 0.06
ALLOSTATIC_TARGET_LAMBDA = 0.0


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


def load_scaling_module() -> Any:
    sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location("peps3d_flux_axis0_scaling", SCALING_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {SCALING_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def gradient(module: Any, shape: tuple[int, int, int], mode: str, target_lambda: float, cost_scale: float) -> float:
    lam0 = 0.18
    delta = 0.04
    target = module.flux_readout(shape, engine_type=0, lam=target_lambda, mode=mode)
    target_flux = torch.tensor(
        [target["flux_components"]["i"], target["flux_components"]["j"], target["flux_components"]["k"]],
        dtype=module.RTYPE,
    )
    target_probs = torch.abs(target_flux) + module.EPS
    if float(torch.sum(target_probs).item()) < 10.0 * module.EPS:
        target_probs = torch.ones(3, dtype=module.RTYPE)
    target_probs = target_probs / torch.clamp(torch.sum(target_probs), min=module.EPS)

    values = []
    for lam in [lam0 - delta, lam0 + delta]:
        row = module.flux_readout(shape, engine_type=0, lam=lam, mode=mode)
        flux = torch.tensor(
            [row["flux_components"]["i"], row["flux_components"]["j"], row["flux_components"]["k"]],
            dtype=module.RTYPE,
        )
        flux_probs = torch.abs(flux) + module.EPS
        flux_probs = flux_probs / torch.clamp(torch.sum(flux_probs), min=module.EPS)
        recovery_error = module.kl_probs(flux_probs, target_probs)
        recovery_gap = float(torch.linalg.vector_norm(flux - target_flux).item())
        compression_gain = module.math.log(4.0) - row["branch_entropy"]
        transition_cost = cost_scale * lam * lam * (1.0 + row["topology_mutation_norm"])
        recovery_gain = module.math.exp(-recovery_gap)
        values.append(recovery_error + row["branch_entropy"] + transition_cost - compression_gain - recovery_gain)
    return (values[1] - values[0]) / (2.0 * delta)


def sign_margin(values: list[float], *, direction: str) -> dict[str, Any]:
    if direction == "negative":
        passes = all(value < 0.0 for value in values)
    elif direction == "positive":
        passes = all(value > 0.0 for value in values)
    else:
        raise ValueError(direction)
    return {
        "pass": passes,
        "min_abs_margin": min(abs(value) for value in values),
        "worst_value": max(values) if direction == "negative" else min(values),
    }


def contiguous_suffix(values: list[float], passing: set[float]) -> bool:
    first_passing = None
    for idx, value in enumerate(values):
        if value in passing:
            first_passing = idx
            break
    if first_passing is None:
        return False
    return set(values[first_passing:]) == passing


def main() -> int:
    started = time.time()
    module = load_scaling_module()
    shapes = list(module.SHAPES)
    current_lambda = float(module.HOMEOSTATIC_TARGET_LAMBDA)
    current_cost = float(module.ALLOSTATIC_TRANSITION_COST_SCALE)

    homeostatic_rows: dict[str, dict[str, Any]] = {}
    for target_lambda in HOMEOSTATIC_TARGET_GRID:
        gradients = [
            gradient(module, shape, "homeostatic", target_lambda, HOMEOSTATIC_COST_SCALE)
            for shape in shapes
        ]
        homeostatic_rows[f"{target_lambda:.2f}"] = {
            "target_lambda": target_lambda,
            "gradients_by_site_count": {
                str(module.math.prod(shape)): value for shape, value in zip(shapes, gradients, strict=True)
            },
            **sign_margin(gradients, direction="negative"),
        }

    allostatic_rows: dict[str, dict[str, Any]] = {}
    for cost_scale in ALLOSTATIC_COST_GRID:
        gradients = [
            gradient(module, shape, "allostatic", ALLOSTATIC_TARGET_LAMBDA, cost_scale)
            for shape in shapes
        ]
        allostatic_rows[f"{cost_scale:.2f}"] = {
            "transition_cost_scale": cost_scale,
            "gradients_by_site_count": {
                str(module.math.prod(shape)): value for shape, value in zip(shapes, gradients, strict=True)
            },
            **sign_margin(gradients, direction="positive"),
        }

    passing_lambdas = {
        row["target_lambda"] for row in homeostatic_rows.values() if row["pass"]
    }
    passing_costs = {
        row["transition_cost_scale"] for row in allostatic_rows.values() if row["pass"]
    }
    best_lambda_row = max(
        (row for row in homeostatic_rows.values() if row["pass"]),
        key=lambda row: row["min_abs_margin"],
        default=None,
    )
    best_cost_row = max(
        (row for row in allostatic_rows.values() if row["pass"]),
        key=lambda row: row["min_abs_margin"],
        default=None,
    )
    nominal_flux_norms = {
        str(module.math.prod(shape)): module.flux_readout(shape, engine_type=0, lam=0.18, mode="allostatic")[
            "flux_norm"
        ]
        for shape in shapes
    }

    inherited_lambda = 0.30
    inherited_cost = 1.55
    checks = {
        "P1_current_calibration_inside_finite_envelope": current_lambda in passing_lambdas and current_cost in passing_costs,
        "P2_inherited_fixture_outside_envelope": inherited_lambda not in passing_lambdas and inherited_cost not in passing_costs,
        "P3_envelope_is_bounded_not_all_grid": 0 < len(passing_lambdas) < len(HOMEOSTATIC_TARGET_GRID)
        and 0 < len(passing_costs) < len(ALLOSTATIC_COST_GRID),
        "P4_homeostatic_envelope_not_single_point": len(passing_lambdas) >= 2,
        "P5_allostatic_threshold_is_suffix": contiguous_suffix(ALLOSTATIC_COST_GRID, passing_costs),
        "P6_current_selection_not_unique_derivation": best_lambda_row is not None
        and (
            abs(best_lambda_row["target_lambda"] - current_lambda) > 1.0e-9
            or len(passing_lambdas) > 1
        ),
        "P7_flux_witness_remains_present": all(value > module.GAP_FLOOR for value in nominal_flux_norms.values()),
        "P8_nonpromotion_boundary_intact": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False,
    }

    positive = {
        "finite_calibration_envelope_found": {
            "pass": checks["P1_current_calibration_inside_finite_envelope"]
            and checks["P3_envelope_is_bounded_not_all_grid"],
            "passing_homeostatic_target_lambdas": sorted(passing_lambdas),
            "passing_allostatic_transition_cost_scales": sorted(passing_costs),
        },
        "flux_witness_survives_envelope_stress": {
            "pass": checks["P7_flux_witness_remains_present"],
            "nominal_flux_norms": nominal_flux_norms,
        },
    }
    graveyard = {
        "GC1_inherited_fixture_outside_envelope": {
            "pass": checks["P2_inherited_fixture_outside_envelope"],
            "inherited_homeostatic_target_lambda": inherited_lambda,
            "inherited_allostatic_transition_cost_scale": inherited_cost,
        },
        "GC2_broad_grid_not_automatically_passing": {
            "pass": checks["P3_envelope_is_bounded_not_all_grid"],
            "failed_homeostatic_target_lambdas": sorted(set(HOMEOSTATIC_TARGET_GRID) - passing_lambdas),
            "failed_allostatic_transition_cost_scales": sorted(set(ALLOSTATIC_COST_GRID) - passing_costs),
        },
        "GC3_current_constants_not_unique_derivation": {
            "pass": checks["P6_current_selection_not_unique_derivation"],
            "best_homeostatic_by_min_margin": best_lambda_row,
            "best_allostatic_by_min_margin": best_cost_row,
            "meaning": "The envelope exists, but the exact constants are not yet a calibration-free theorem.",
        },
    }
    boundary = {
        "B1_formal_scout_only": {"pass": checks["P8_nonpromotion_boundary_intact"]},
        "B2_sampled_boundary_not_full_closure": {
            "pass": True,
            "sampled_boundary": True,
            "full_peps3d_environment_closure": False,
        },
        "B3_calibration_stress_not_axis0_theorem": {
            "pass": True,
            "meaning": "Envelope survival is evidence for the fixture, not admission of final Axis0.",
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
        "homeostatic_target_grid": HOMEOSTATIC_TARGET_GRID,
        "allostatic_cost_grid": ALLOSTATIC_COST_GRID,
        "homeostatic_rows": homeostatic_rows,
        "allostatic_rows": allostatic_rows,
        "envelope_summary": {
            "current_homeostatic_target_lambda": current_lambda,
            "current_allostatic_transition_cost_scale": current_cost,
            "passing_homeostatic_target_lambdas": sorted(passing_lambdas),
            "passing_allostatic_transition_cost_scales": sorted(passing_costs),
            "best_homeostatic_by_min_margin": best_lambda_row,
            "best_allostatic_by_min_margin": best_cost_row,
            "status": "survives_finite_envelope_but_not_calibration_free",
        },
        "checks": checks,
        "nearby_variants": {
            "passed": sum(1 for row in variants if row["pass"]) + sum(1 for value in checks.values() if value),
            "total": len(variants) + len(checks),
            "failed_checks": [key for key, value in checks.items() if not value],
        },
        "all_pass": all(checks.values()),
        "why_not_final": [
            "The passing homeostatic target band is narrow on the sampled grid.",
            "The exact current constants are not uniquely derived by this finite envelope stress.",
            "The row reuses sampled local PEPS3D boundary contractions, not full PEPS3D environment closure.",
            "This does not prove Xi/Phi0, final Axis0, final flux, or physics.",
        ],
        "divergence_log": [
            "Inherited unscaled fixture must fall outside the passing envelope.",
            "Most nearby homeostatic target lambdas must fail at least one shape.",
            "Low allostatic transition cost must fail the 8-site allostatic sign.",
            "Flux presence is checked separately from the F_QIT sign calibration.",
        ],
        "why_not_v4_probes": (
            "This is a v5 PEPS3D flux-bound Axis0 calibration-envelope stress "
            "scout, not a legacy v4 probe."
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
                "checks": checks,
                "passing_homeostatic_target_lambdas": sorted(passing_lambdas),
                "passing_allostatic_transition_cost_scales": sorted(passing_costs),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
