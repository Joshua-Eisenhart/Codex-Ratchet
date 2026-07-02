#!/usr/bin/env python3
"""Runtime-cardinality homeostatic calibration gate for PEPS3D Axis0.

Formal scout only.

This row splits the smallest homeostatic calibration question out of the
four-loop runtime-bound scout:

    lambda_home = LAM0 + DELTA * unique_slot_operator_count

The rule is frozen from enriched runtime records only, then stressed on
held-out shapes. A held-out failure kills the stronger calibration-closure
claim without hiding the source pass.

This row verifies one formula is stable under the current runtime record
surface. It does not derive the constants `LAM0=0.18` or `DELTA=0.04` from
first principles.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys
import time
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "peps3d_flux_axis0_runtime_cardinality_calibration_gate_probe_results.json"
LOOP4_MODULE_PATH = ROOT / "sim_peps3d_flux_axis0_runtime_bound_loop4_probe.py"

NAME = "peps3d_flux_axis0_runtime_cardinality_calibration_gate_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical_peps3d_flux_axis0_runtime_cardinality_calibration_gate"
SOURCE_ALIGNMENT_CATEGORY = "peps3d_flux_bound_axis0_runtime_cardinality_calibration_gate"
PROMOTION_ALLOWED = False
ADMISSION_STATUS = "blocked"
EXPECTED_NONPROMOTION = True
CLAIM_CEILING = (
    "Formal scout only: freezes a homeostatic Axis0 target rule from enriched "
    "runtime-record cardinality and stresses held-out PEPS3D shapes. This is "
    "a one-feature incomplete calibration family; it does not derive LAM0 or "
    "DELTA and does not admit final Axis0, final flux, Xi, Phi0, full PEPS3D "
    "closure, gravity, Standard Model, Yang-Mills, Riemann, or physics claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing runtime-bound PEPS3D flux gradients and margin checks through the loop4 module",
    },
    "peps3d_flux_axis0_runtime_bound_loop4_probe": {
        "tried": True,
        "used": True,
        "reason": "load-bearing consumed receipt/module supplying runtime-bound transport, inherited constants, source-only cardinality rule, and gradient functions",
    },
    "peps3d_flux_axis0_runtime_record_binding_gate_probe": {
        "tried": True,
        "used": True,
        "reason": "load-bearing consumed receipt/module supplying enriched runtime records consumed by the loop4 module",
    },
    "peps3d_spinor_network_flux_axis0_scaling_probe": {
        "tried": True,
        "used": True,
        "reason": "load-bearing consumed receipt/module supplying PEPS3D spinor/quaternion substrate functions through the loop4 module",
    },
    "python_importlib": {"tried": True, "used": True, "reason": "supportive local module loading"},
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "peps3d_flux_axis0_runtime_bound_loop4_probe": "load_bearing",
    "peps3d_flux_axis0_runtime_record_binding_gate_probe": "load_bearing",
    "peps3d_spinor_network_flux_axis0_scaling_probe": "load_bearing",
    "python_importlib": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

SOURCE_SHAPES = [(2, 2, 2), (3, 3, 3)]
HELDOUT_SHAPES = [(2, 3, 4), (2, 4, 4), (3, 3, 4)]
CALIBRATION_RULE_DOCTRINE = {
    "rule_family": "one_feature_runtime_cardinality",
    "constants_derived_here": False,
    "lam0_source": "inherited_loop4_fixture",
    "delta_source": "inherited_loop4_fixture",
    "formula_correctness_proven": False,
    "formula_stability_checked": True,
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    try:
        import torch

        if isinstance(value, torch.Tensor):
            if value.numel() == 1:
                return as_jsonable(value.detach().cpu().item())
            return as_jsonable(value.detach().cpu().tolist())
    except Exception:
        pass
    return value


def load_module(path: pathlib.Path, name: str) -> Any:
    sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def shape_key(shape: tuple[int, int, int]) -> str:
    return "x".join(str(item) for item in shape)


def homeostatic_gradient(loop4: Any, scaling_module: Any, binding_module: Any, shape: tuple[int, int, int], target_lambda: float) -> float:
    return loop4.gradient(
        scaling_module,
        binding_module,
        shape,
        runtime_bound=True,
        boundary="canonical",
        mode="homeostatic",
        target_lambda=target_lambda,
        cost_scale=loop4.HOMEOSTATIC_COST_SCALE,
    )


def main() -> int:
    started = time.time()
    loop4 = load_module(LOOP4_MODULE_PATH, "peps3d_axis0_runtime_bound_loop4")
    scaling_module = loop4.load_module(loop4.SCALING_MODULE_PATH, "peps3d_axis0_scaling")
    binding_module = loop4.load_module(loop4.BINDING_MODULE_PATH, "peps3d_axis0_runtime_binding")
    coverage = loop4.runtime_record_coverage(binding_module, scaling_module)
    rule = loop4.runtime_record_cardinality_rule(binding_module, scaling_module)
    target_lambda = float(rule["selected_target_lambda"])

    source = {
        shape_key(shape): homeostatic_gradient(loop4, scaling_module, binding_module, shape, target_lambda)
        for shape in SOURCE_SHAPES
    }
    heldout = {
        shape_key(shape): homeostatic_gradient(loop4, scaling_module, binding_module, shape, target_lambda)
        for shape in HELDOUT_SHAPES
    }
    source_status = {key: value < -loop4.GAP_FLOOR for key, value in source.items()}
    heldout_status = {key: value < -loop4.GAP_FLOOR for key, value in heldout.items()}

    raw = loop4.flux_readout(
        scaling_module,
        binding_module,
        (3, 3, 3),
        runtime_bound=False,
        boundary="canonical",
        engine_type=0,
        lam=loop4.LAM0,
        mode="homeostatic",
    )
    bound = loop4.flux_readout(
        scaling_module,
        binding_module,
        (3, 3, 3),
        runtime_bound=True,
        boundary="canonical",
        engine_type=0,
        lam=loop4.LAM0,
        mode="homeostatic",
    )
    erased = loop4.flux_readout(
        scaling_module,
        binding_module,
        (3, 3, 3),
        runtime_bound=True,
        boundary="canonical",
        engine_type=0,
        lam=loop4.LAM0,
        mode="homeostatic",
        sheet_erased=True,
    )
    reversed_shell = loop4.flux_readout(
        scaling_module,
        binding_module,
        (3, 3, 3),
        runtime_bound=True,
        boundary="canonical",
        engine_type=0,
        lam=loop4.LAM0,
        mode="homeostatic",
        reversed_shell_time=True,
    )
    runtime_flux_gap = abs(bound["flux_norm"] - raw["flux_norm"])
    sheet_erased_ratio = erased["flux_norm"] / max(bound["flux_norm"], scaling_module.EPS)
    shell_reversal_gap = abs(bound["jk_norm"] - reversed_shell["jk_norm"])
    heldout_failures = [key for key, passed in heldout_status.items() if not passed]

    checks = {
        "P1_runtime_binding_surface_valid": coverage["record_count"] == 384
        and coverage["terrain_realization_count"] == 8
        and coverage["substage_token_count"] == 32,
        "P2_runtime_record_cardinality_formula_stable_not_derived": rule["unique_slot_operator_count"] == 4
        and abs(target_lambda - 0.34) < 1.0e-12,
        "P3_no_heldout_refit": rule["source_only"]
        and not rule["uses_heldout_gradients"]
        and not rule["uses_beta_grid"]
        and not rule["uses_per_shape_constants"],
        "P4_source_homeostatic_signs_pass": all(source_status.values()),
        "P5_heldout_homeostatic_stress_reported": len(heldout_status) == len(HELDOUT_SHAPES),
        "P6_runtime_cardinality_closure_claim_killed_if_any_heldout_fails": len(heldout_failures) > 0,
        "P7_runtime_binding_load_bearing": runtime_flux_gap > loop4.GAP_FLOOR,
        "P8_chiral_controls_nontrivial": sheet_erased_ratio < 0.75 and shell_reversal_gap > loop4.GAP_FLOOR,
        "P9_formal_scout_boundary": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False,
    }
    positive = {
        "source_homeostatic_cardinality_rule_passes": {
            "pass": checks["P1_runtime_binding_surface_valid"]
            and checks["P2_runtime_record_cardinality_formula_stable_not_derived"]
            and checks["P3_no_heldout_refit"]
            and checks["P4_source_homeostatic_signs_pass"],
            "rule": rule,
            "calibration_rule_doctrine": CALIBRATION_RULE_DOCTRINE,
            "source_gradients": source,
            "source_status": source_status,
        },
        "runtime_binding_is_load_bearing_for_canonical_homeostasis": {
            "pass": checks["P7_runtime_binding_load_bearing"] and checks["P8_chiral_controls_nontrivial"],
            "raw_flux_norm_27": raw["flux_norm"],
            "runtime_bound_flux_norm_27": bound["flux_norm"],
            "runtime_flux_gap_27": runtime_flux_gap,
            "sheet_erased_flux_ratio_27": sheet_erased_ratio,
            "shell_reversal_jk_gap_27": shell_reversal_gap,
        },
    }
    graveyard = {
        "heldout_complete_runtime_cardinality_calibration_claim_killed": {
            "pass": checks["P5_heldout_homeostatic_stress_reported"]
            and checks["P6_runtime_cardinality_closure_claim_killed_if_any_heldout_fails"],
            "heldout_gradients": heldout,
            "heldout_status": heldout_status,
            "heldout_failures": heldout_failures,
        },
        "allostatic_calibration_not_claimed_by_this_row": {
            "pass": True,
            "reason": "This gate isolates homeostatic target calibration; allostatic source failures remain covered by loop4.",
        },
        "constants_not_derived_by_this_row": {
            "pass": not CALIBRATION_RULE_DOCTRINE["constants_derived_here"]
            and not CALIBRATION_RULE_DOCTRINE["formula_correctness_proven"],
            "doctrine": CALIBRATION_RULE_DOCTRINE,
        },
    }
    boundary = {
        "formal_scout_only": {"pass": checks["P9_formal_scout_boundary"]},
        "admission_status_blocked": {
            "pass": ADMISSION_STATUS == "blocked" and EXPECTED_NONPROMOTION is True,
            "admission_status": ADMISSION_STATUS,
            "expected_nonpromotion": EXPECTED_NONPROMOTION,
        },
        "next_admissible_step": {
            "pass": True,
            "step": "Use the heldout failure to derive a richer no-refit runtime/boundary calibration rule; do not tune on heldouts.",
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
        "admission_status": ADMISSION_STATUS,
        "expected_nonpromotion": EXPECTED_NONPROMOTION,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "CONSUMED_RECEIPT_DEPTH": {
            "peps3d_flux_axis0_runtime_bound_loop4_probe": "load_bearing",
            "peps3d_flux_axis0_runtime_record_binding_gate_probe": "load_bearing",
            "peps3d_spinor_network_flux_axis0_scaling_probe": "load_bearing",
        },
        "calibration_rule_doctrine": CALIBRATION_RULE_DOCTRINE,
        "positive": as_jsonable(positive),
        "graveyard_companions": as_jsonable(graveyard),
        "boundary": as_jsonable(boundary),
        "checks": checks,
        "runtime_record_coverage": coverage,
        "source_shapes": [shape_key(shape) for shape in SOURCE_SHAPES],
        "heldout_shapes": [shape_key(shape) for shape in HELDOUT_SHAPES],
        "nearby_variants": {
            "passed": sum(1 for row in variants if row["pass"]) + sum(1 for value in checks.values() if value),
            "total": len(variants) + len(checks),
            "failed_checks": [key for key, value in checks.items() if not value],
        },
        "all_pass": all(checks.values()) and all(row["pass"] for row in variants),
        "why_not_final": [
            "The runtime-cardinality rule passes source homeostasis but fails at least one held-out shape.",
            "The constants LAM0=0.18 and DELTA=0.04 are inherited fixture constants, not derived by this row.",
            "P2 checks formula stability for the current fixture; it does not prove formula correctness.",
            "This row isolates homeostatic target calibration and does not repair allostatic sign failures.",
            "The rule is a finite formal-scout fixture, not Xi/Phi0 or full PEPS3D closure.",
        ],
        "divergence_log": [
            "Held-out failure is preserved as evidence against a complete runtime-cardinality calibration rule.",
            "The source-only 0.34 rule is not retuned, beta-fit, or shape-fit.",
            "The row records that its inherited constants are not a derived Axis0 calibration law.",
        ],
        "why_not_v4_probes": "This is a v5 PEPS3D flux-bound Axis0 runtime-cardinality calibration gate, not a legacy v4 probe.",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "failed_checks": result["nearby_variants"]["failed_checks"],
                "source_status": source_status,
                "heldout_status": heldout_status,
                "heldout_failures": heldout_failures,
                "wrote": str(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
