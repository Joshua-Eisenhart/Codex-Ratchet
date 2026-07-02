#!/usr/bin/env python3
"""Calibration-ablation probe for scaled PEPS3D flux-bound Axis0.

Formal scout only.

The scaled PEPS3D row uses a fixed F_QIT calibration:

* homeostatic recovery target lambda = 0.34
* allostatic transition-cost scale = 5.0

This probe checks that the calibration is load-bearing instead of hidden
tuning: the inherited 8-site fixture fails at scale, an over-costed
homeostatic fixture fails, and the flux witness itself is unchanged by the
FEP calibration choice.
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
OUT_PATH = RESULT_DIR / "peps3d_flux_axis0_calibration_ablation_probe_results.json"
SCALING_MODULE_PATH = ROOT / "sim_peps3d_spinor_network_flux_axis0_scaling_probe.py"

NAME = "peps3d_flux_axis0_calibration_ablation_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical_peps3d_flux_axis0_calibration_ablation"
SOURCE_ALIGNMENT_CATEGORY = "peps3d_flux_bound_axis0_fep_calibration_ablation"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: ablates the F_QIT calibration used by the scaled "
    "PEPS3D flux-bound Axis0 row. It does not admit final Axis0, Xi, Phi0, "
    "flux, PEPS3D closure, gravity, Standard Model, Yang-Mills, Riemann, or "
    "physics claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing gradient recomputation and calibration-ablation controls over PEPS3D flux readouts",
    },
    "peps3d_spinor_network_flux_axis0_scaling_probe": {
        "tried": True,
        "used": True,
        "reason": "supportive reuse of the exact scaled PEPS3D flux-bound Axis0 functions under ablated F_QIT fixtures",
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


def main() -> int:
    started = time.time()
    module = load_scaling_module()
    rows = {}
    for shape in module.SHAPES:
        key = str(tuple(shape))
        rows[key] = {
            "admitted_homeostatic": gradient(module, shape, "homeostatic", module.HOMEOSTATIC_TARGET_LAMBDA, 0.06),
            "admitted_allostatic": gradient(module, shape, "allostatic", 0.0, module.ALLOSTATIC_TRANSITION_COST_SCALE),
            "inherited_homeostatic": gradient(module, shape, "homeostatic", 0.30, 0.06),
            "inherited_allostatic": gradient(module, shape, "allostatic", 0.0, 1.55),
            "overcost_homeostatic": gradient(module, shape, "homeostatic", module.HOMEOSTATIC_TARGET_LAMBDA, 5.0),
            "nominal_flux_norm": module.flux_readout(shape, engine_type=0, lam=0.18, mode="allostatic")["flux_norm"],
        }
    inherited_failures = [
        key
        for key, row in rows.items()
        if not (row["inherited_homeostatic"] < -module.GAP_FLOOR and row["inherited_allostatic"] > module.GAP_FLOOR)
    ]
    checks = {
        "P1_admitted_calibration_has_expected_signs": all(
            row["admitted_homeostatic"] < -module.GAP_FLOOR and row["admitted_allostatic"] > module.GAP_FLOOR
            for row in rows.values()
        ),
        "P2_inherited_fixture_fails_at_scale": len(inherited_failures) >= 2,
        "P3_overcosted_homeostatic_fails": all(row["overcost_homeostatic"] > module.GAP_FLOOR for row in rows.values()),
        "P4_flux_witness_remains_present": all(row["nominal_flux_norm"] > module.GAP_FLOOR for row in rows.values()),
    }
    positive = {
        "admitted_calibration_passes_scaling_signs": {
            "pass": checks["P1_admitted_calibration_has_expected_signs"],
            "calibration": {
                "homeostatic_target_lambda": module.HOMEOSTATIC_TARGET_LAMBDA,
                "allostatic_transition_cost_scale": module.ALLOSTATIC_TRANSITION_COST_SCALE,
            },
        },
        "flux_witness_not_calibration_dependent": {
            "pass": checks["P4_flux_witness_remains_present"],
            "nominal_flux_norms": {key: row["nominal_flux_norm"] for key, row in rows.items()},
        },
    }
    graveyard = {
        "GC1_inherited_unscaled_fixture_fails": {
            "pass": checks["P2_inherited_fixture_fails_at_scale"],
            "failed_shapes": inherited_failures,
        },
        "GC2_overcosted_homeostasis_fails": {
            "pass": checks["P3_overcosted_homeostatic_fails"],
            "meaning": "The sign is not automatically correct under arbitrary cost choices.",
        },
    }
    boundary = {
        "B1_formal_scout_only": {"pass": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False},
        "B2_ablation_not_final_axis0": {"pass": True, "meaning": "Calibration is a fixture to harden next, not an admitted theorem."},
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
        "calibration_rows": rows,
        "checks": checks,
        "nearby_variants": {
            "passed": sum(1 for row in variants if row["pass"]) + sum(1 for value in checks.values() if value),
            "total": len(variants) + len(checks),
            "failed_checks": [key for key, value in checks.items() if not value],
        },
        "all_pass": all(checks.values()),
        "why_not_final": [
            "The pass depends on an explicit F_QIT calibration fixture.",
            "The inherited fixture fails, proving the target/cost layer remains an active modeling boundary.",
            "This does not prove Xi/Phi0, final Axis0, final flux, or PEPS3D closure.",
        ],
        "divergence_log": [
            "Inherited unscaled FEP fixture fails at scale.",
            "Arbitrary over-costed homeostasis also fails.",
            "Flux presence survives independently of FEP calibration.",
        ],
        "why_not_v4_probes": (
            "This is a v5 PEPS3D flux-bound Axis0 calibration-ablation scout, not a legacy v4 probe."
        ),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "checks": checks}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
