#!/usr/bin/env python3
"""Target-scramble controls for PEPS3D flux-bound Axis0 calibration.

Formal scout only.

The current F_QIT calibration uses target fluxes/probabilities derived from
matching homeostatic/allostatic regimes. This row checks wrong-object targets:
permuted flux components, permuted target probabilities, swapped shape targets,
and wrong-regime targets. If wrong targets preserve every sign, the calibration
is too shallow.
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
OUT_PATH = RESULT_DIR / "peps3d_flux_axis0_target_scramble_control_probe_results.json"

NAME = "peps3d_flux_axis0_target_scramble_control_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical_peps3d_flux_axis0_target_scramble_control"
SOURCE_ALIGNMENT_CATEGORY = "peps3d_flux_bound_axis0_wrong_target_controls"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests wrong-object target controls for PEPS3D "
    "flux-bound Axis0 F_QIT calibration. It does not admit final Axis0, "
    "Xi, Phi0, flux, PEPS3D closure, gravity, Standard Model, Yang-Mills, "
    "Riemann, or physics claims."
)

TEST_SHAPES = [(2, 2, 2), (3, 3, 3), (4, 4, 4)]
PERMUTATION = torch.tensor([1, 2, 0], dtype=torch.long)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing target flux/probability scramble tensors and signed F_QIT gradient recomputation",
    },
    "peps3d_flux_axis0_calibration_envelope_stress_probe": {
        "tried": True,
        "used": True,
        "reason": "supportive reuse of current calibration constants and gradient construction",
    },
    "peps3d_spinor_network_flux_axis0_scaling_probe": {
        "tried": True,
        "used": True,
        "reason": "supportive reuse of PEPS3D flux readouts and finite F_QIT terms",
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


def target_for(module: Any, shape: tuple[int, int, int], mode: str) -> tuple[torch.Tensor, torch.Tensor]:
    target_lambda = module.HOMEOSTATIC_TARGET_LAMBDA if mode == "homeostatic" else 0.0
    target = module.flux_readout(shape, engine_type=0, lam=target_lambda, mode=mode)
    target_flux = torch.tensor([target["flux_components"]["i"], target["flux_components"]["j"], target["flux_components"]["k"]], dtype=module.RTYPE)
    target_probs = torch.abs(target_flux) + module.EPS
    if float(torch.sum(target_probs).item()) < 10.0 * module.EPS:
        target_probs = torch.ones(3, dtype=module.RTYPE)
    target_probs = target_probs / torch.clamp(torch.sum(target_probs), min=module.EPS)
    return target_flux, target_probs


def fep_with_target(
    module: Any,
    shape: tuple[int, int, int],
    *,
    lam: float,
    mode: str,
    target_flux: torch.Tensor,
    target_probs: torch.Tensor,
) -> float:
    row = module.flux_readout(shape, engine_type=0, lam=lam, mode=mode)
    flux = torch.tensor([row["flux_components"]["i"], row["flux_components"]["j"], row["flux_components"]["k"]], dtype=module.RTYPE)
    flux_probs = torch.abs(flux) + module.EPS
    flux_probs = flux_probs / torch.clamp(torch.sum(flux_probs), min=module.EPS)
    recovery_error = module.kl_probs(flux_probs, target_probs)
    recovery_gap = float(torch.linalg.vector_norm(flux - target_flux).item())
    compression_gain = math.log(4.0) - row["branch_entropy"]
    cost_scale = 0.06 if mode == "homeostatic" else module.ALLOSTATIC_TRANSITION_COST_SCALE
    transition_cost = cost_scale * lam * lam * (1.0 + row["topology_mutation_norm"])
    recovery_gain = math.exp(-recovery_gap)
    return recovery_error + row["branch_entropy"] + transition_cost - compression_gain - recovery_gain


def gradient_with_target(module: Any, shape: tuple[int, int, int], mode: str, target_flux: torch.Tensor, target_probs: torch.Tensor) -> float:
    low = fep_with_target(module, shape, lam=0.14, mode=mode, target_flux=target_flux, target_probs=target_probs)
    high = fep_with_target(module, shape, lam=0.22, mode=mode, target_flux=target_flux, target_probs=target_probs)
    return (high - low) / 0.08


def target_variants(module: Any, shape: tuple[int, int, int], mode: str) -> dict[str, tuple[torch.Tensor, torch.Tensor]]:
    correct_flux, correct_probs = target_for(module, shape, mode)
    wrong_mode = "allostatic" if mode == "homeostatic" else "homeostatic"
    wrong_mode_flux, wrong_mode_probs = target_for(module, shape, wrong_mode)
    shape_idx = TEST_SHAPES.index(shape)
    swapped_shape = TEST_SHAPES[(shape_idx + 1) % len(TEST_SHAPES)]
    swapped_flux, swapped_probs = target_for(module, swapped_shape, mode)
    return {
        "correct": (correct_flux, correct_probs),
        "permute_flux_only": (correct_flux[PERMUTATION], correct_probs),
        "permute_probs_only": (correct_flux, correct_probs[PERMUTATION]),
        "permute_flux_and_probs": (correct_flux[PERMUTATION], correct_probs[PERMUTATION]),
        "wrong_regime": (wrong_mode_flux, wrong_mode_probs),
        "swapped_shape": (swapped_flux, swapped_probs),
    }


def expected_sign(mode: str, value: float, gap_floor: float) -> bool:
    if mode == "homeostatic":
        return value < -gap_floor
    return value > gap_floor


def main() -> int:
    started = time.time()
    module = calibration.load_scaling_module()
    rows: list[dict[str, Any]] = []
    for shape in TEST_SHAPES:
        for mode in ["homeostatic", "allostatic"]:
            for variant, (target_flux, target_probs) in target_variants(module, shape, mode).items():
                value = gradient_with_target(module, shape, mode, target_flux, target_probs)
                rows.append(
                    {
                        "shape": shape,
                        "site_count": math.prod(shape),
                        "mode": mode,
                        "target_variant": variant,
                        "gradient": value,
                        "expected_sign_pass": expected_sign(mode, value, module.GAP_FLOOR),
                        "target_flux": target_flux,
                        "target_probs": target_probs,
                    }
                )
    correct_rows = [row for row in rows if row["target_variant"] == "correct"]
    wrong_rows = [row for row in rows if row["target_variant"] != "correct"]
    wrong_survivors = [
        f"{row['site_count']}:{row['mode']}:{row['target_variant']}"
        for row in wrong_rows
        if row["expected_sign_pass"]
    ]
    wrong_failures = [
        f"{row['site_count']}:{row['mode']}:{row['target_variant']}"
        for row in wrong_rows
        if not row["expected_sign_pass"]
    ]
    positive = {
        "correct_targets_preserve_current_fixture_signs": {
            "pass": all(row["expected_sign_pass"] for row in correct_rows),
            "correct_gradients": {
                f"{row['site_count']}:{row['mode']}": row["gradient"] for row in correct_rows
            },
        },
        "wrong_target_grid_executed": {
            "pass": len(wrong_rows) == len(TEST_SHAPES) * 2 * 5,
            "wrong_variant_count": len(wrong_rows),
        },
    }
    graveyard = {
        "wrong_targets_do_not_all_preserve_signs": {
            "pass": len(wrong_failures) > 0,
            "wrong_target_failures": wrong_failures,
            "wrong_target_survivors": wrong_survivors,
            "meaning": "At least one wrong-object target breaks the calibrated sign, so target choice is load-bearing.",
        },
        "wrong_targets_still_have_survivors": {
            "pass": len(wrong_survivors) > 0,
            "wrong_target_survivors": wrong_survivors,
            "meaning": "Some wrong targets still preserve signs, so target specificity is incomplete and not a theorem.",
        },
    }
    boundary = {
        "formal_scout_only": {"pass": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False},
        "target_scramble_not_axis0_theorem": {"pass": True, "promotion_allowed": PROMOTION_ALLOWED},
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
        "positive": as_jsonable(positive),
        "graveyard_companions": as_jsonable(graveyard),
        "boundary": as_jsonable(boundary),
        "target_rows": as_jsonable(rows),
        "stress_outcome": {
            "wrong_target_failures": wrong_failures,
            "wrong_target_survivors": wrong_survivors,
            "status": "target_choice_load_bearing_but_not_unique",
        },
        "nearby_variants": {
            "passed": sum(1 for row in variants if row["pass"]),
            "total": len(variants),
            "failed": [key for section in (positive, graveyard, boundary) for key, row in section.items() if not row["pass"]],
        },
        "all_pass": all(row["pass"] for row in variants),
        "why_not_final": [
            "Wrong targets break some signs but not all signs.",
            "The target construction is load-bearing and not uniquely derived by this row.",
            "This does not prove Xi/Phi0, final Axis0, final flux, PEPS3D closure, or physics.",
        ],
        "divergence_log": [
            "Permuted, swapped, and wrong-regime targets are graveyard controls.",
            "Correct target signs are checked separately from wrong-target specificity.",
        ],
        "why_not_v4_probes": "This is a v5 PEPS3D flux-bound Axis0 target-scramble scout, not a legacy v4 probe.",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "wrong_failures": len(wrong_failures), "wrong_survivors": len(wrong_survivors)}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
