#!/usr/bin/env python3
"""Integrated PEPS3D shell/boundary flux -> Axis0 control battery.

Formal scout only.

Target split:

    J_flux = engine-bound quaternionic chiral boundary current
    Axis0 = signed QIT/FEP entropy gradient read over that current

This row deliberately keeps those objects separate. It reuses the
runtime-bound PEPS3D shell transport fixture, then runs the minimum integrated
controls requested for the next real blocker: sheet erase, shell-time reversal,
engine swap, topology freeze, target/reference scramble, branch-count null,
recovery-only null, held-out shape, boundary sampler variation, and no-refit
calibration.

Passing this row means the blocker/control battery executed and preserved the
claim boundary. It does not admit final Axis0, final flux, Xi/Phi0, full
PEPS3D closure, gravity, Standard Model, Yang-Mills, Riemann, or physics
claims.
"""

from __future__ import annotations

import importlib.util
import json
import math
import pathlib
import sys
import time
from typing import Any

import torch


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "peps3d_shell_boundary_flux_axis0_integrated_controls_probe_results.json"
LOOP4_MODULE_PATH = ROOT / "sim_peps3d_flux_axis0_runtime_bound_loop4_probe.py"

NAME = "peps3d_shell_boundary_flux_axis0_integrated_controls_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical_peps3d_shell_boundary_flux_axis0_integrated_controls"
SOURCE_ALIGNMENT_CATEGORY = "peps3d_shell_boundary_flux_axis0_integrated_control_battery"
PROMOTION_ALLOWED = False
ADMISSION_STATUS = "blocked"
EXPECTED_NONPROMOTION = True
CLAIM_CEILING = (
    "Formal scout only: executes an integrated PEPS3D shell/boundary control "
    "battery while keeping J_flux separate from Axis0. It records blockers "
    "and controls; it does not admit final Axis0, final flux, Xi/Phi0, full "
    "PEPS3D closure, gravity, Standard Model, Yang-Mills, Riemann, or physics "
    "claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing quaternionic flux tensors, finite FEP gradients, "
            "control gaps, null gradients, and boundary sampler comparisons"
        ),
    },
    "peps3d_flux_axis0_runtime_bound_loop4_probe": {
        "tried": True,
        "used": True,
        "reason": (
            "supportive runtime-bound PEPS3D spinor/quaternion shell transport, "
            "boundary contraction, source runtime record binding, and finite "
            "FEP fixture functions"
        ),
    },
    "python_importlib": {"tried": True, "used": True, "reason": "supportive local module loading"},
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "peps3d_flux_axis0_runtime_bound_loop4_probe": "supportive",
    "python_importlib": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

SOURCE_SHAPE = (3, 3, 3)
HELDOUT_SHAPE = (2, 3, 4)
BOUNDARIES = ["canonical", "surface_mean", "runtime_weighted_surface"]
PRIMARY_BOUNDARY = "runtime_weighted_surface"
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


def flux_vector(scaling_module: Any, row: dict[str, Any]) -> torch.Tensor:
    return torch.tensor(
        [row["flux_components"]["i"], row["flux_components"]["j"], row["flux_components"]["k"]],
        dtype=scaling_module.RTYPE,
    )


def probs_from_flux(scaling_module: Any, flux: torch.Tensor) -> torch.Tensor:
    probs = torch.abs(flux) + scaling_module.EPS
    if float(torch.sum(probs).item()) < 10.0 * scaling_module.EPS:
        probs = torch.ones(3, dtype=scaling_module.RTYPE)
    return probs / torch.clamp(torch.sum(probs), min=scaling_module.EPS)


def read_flux(
    loop4: Any,
    scaling_module: Any,
    binding_module: Any,
    shape: tuple[int, int, int],
    *,
    engine_type: int,
    lam: float,
    mode: str,
    boundary: str,
    sheet_erased: bool = False,
    topology_freeze: bool = False,
    reversed_shell_time: bool = False,
) -> dict[str, Any]:
    row = loop4.flux_readout(
        scaling_module,
        binding_module,
        shape,
        runtime_bound=True,
        boundary=boundary,
        engine_type=engine_type,
        lam=lam,
        mode=mode,
        sheet_erased=sheet_erased,
        topology_freeze=topology_freeze,
        reversed_shell_time=reversed_shell_time,
    )
    row["J_flux"] = {
        "components": row["flux_components"],
        "norm": row["flux_norm"],
        "jk_norm": row["jk_norm"],
    }
    return row


def finite_fep_control(
    loop4: Any,
    scaling_module: Any,
    binding_module: Any,
    shape: tuple[int, int, int],
    *,
    engine_type: int,
    lam: float,
    mode: str,
    boundary: str,
    target_probs: torch.Tensor,
    target_flux: torch.Tensor,
    cost_scale: float,
    sheet_erased: bool = False,
    topology_freeze: bool = False,
    reversed_shell_time: bool = False,
    branch_count_only: bool = False,
    recovery_only: bool = False,
) -> float:
    row = read_flux(
        loop4,
        scaling_module,
        binding_module,
        shape,
        engine_type=engine_type,
        lam=lam,
        mode=mode,
        boundary=boundary,
        sheet_erased=sheet_erased,
        topology_freeze=topology_freeze,
        reversed_shell_time=reversed_shell_time,
    )
    flux = flux_vector(scaling_module, row)
    flux_probs = probs_from_flux(scaling_module, flux)
    recovery_error = scaling_module.kl_probs(flux_probs, target_probs)
    recovery_gap = float(torch.linalg.vector_norm(flux - target_flux).item())
    compression_gain = math.log(4.0) - row["branch_entropy"]
    transition_cost = cost_scale * lam * lam * (1.0 + row["topology_mutation_norm"])
    recovery_gain = math.exp(-recovery_gap)
    if branch_count_only:
        return row["branch_entropy"]
    if recovery_only:
        return recovery_error - recovery_gain
    return recovery_error + row["branch_entropy"] + transition_cost - compression_gain - recovery_gain


def axis0_gradient(
    loop4: Any,
    scaling_module: Any,
    binding_module: Any,
    shape: tuple[int, int, int],
    *,
    mode: str,
    boundary: str,
    engine_type: int = 0,
    target_lambda: float,
    cost_scale: float,
    sheet_erased: bool = False,
    topology_freeze: bool = False,
    reversed_shell_time: bool = False,
    target_scramble: bool = False,
    branch_count_only: bool = False,
    recovery_only: bool = False,
) -> float:
    target = read_flux(
        loop4,
        scaling_module,
        binding_module,
        shape,
        engine_type=engine_type,
        lam=target_lambda,
        mode=mode,
        boundary=boundary,
        sheet_erased=sheet_erased,
        topology_freeze=topology_freeze,
        reversed_shell_time=reversed_shell_time,
    )
    target_flux = flux_vector(scaling_module, target)
    target_probs = probs_from_flux(scaling_module, target_flux)
    if target_scramble:
        target_flux = -torch.flip(target_flux, dims=[0])
        target_probs = torch.flip(target_probs, dims=[0])
    low = finite_fep_control(
        loop4,
        scaling_module,
        binding_module,
        shape,
        engine_type=engine_type,
        lam=loop4.LAM0 - loop4.DELTA,
        mode=mode,
        boundary=boundary,
        target_probs=target_probs,
        target_flux=target_flux,
        cost_scale=cost_scale,
        sheet_erased=sheet_erased,
        topology_freeze=topology_freeze,
        reversed_shell_time=reversed_shell_time,
        branch_count_only=branch_count_only,
        recovery_only=recovery_only,
    )
    high = finite_fep_control(
        loop4,
        scaling_module,
        binding_module,
        shape,
        engine_type=engine_type,
        lam=loop4.LAM0 + loop4.DELTA,
        mode=mode,
        boundary=boundary,
        target_probs=target_probs,
        target_flux=target_flux,
        cost_scale=cost_scale,
        sheet_erased=sheet_erased,
        topology_freeze=topology_freeze,
        reversed_shell_time=reversed_shell_time,
        branch_count_only=branch_count_only,
        recovery_only=recovery_only,
    )
    return (high - low) / (2.0 * loop4.DELTA)


def signed_pair(
    loop4: Any,
    scaling_module: Any,
    binding_module: Any,
    shape: tuple[int, int, int],
    *,
    boundary: str = PRIMARY_BOUNDARY,
    engine_type: int = 0,
    **controls: Any,
) -> dict[str, float]:
    return {
        "homeostatic": axis0_gradient(
            loop4,
            scaling_module,
            binding_module,
            shape,
            mode="homeostatic",
            boundary=boundary,
            engine_type=engine_type,
            target_lambda=loop4.runtime_record_cardinality_rule(binding_module, scaling_module)[
                "selected_target_lambda"
            ],
            cost_scale=loop4.HOMEOSTATIC_COST_SCALE,
            **controls,
        ),
        "allostatic": axis0_gradient(
            loop4,
            scaling_module,
            binding_module,
            shape,
            mode="allostatic",
            boundary=boundary,
            engine_type=engine_type,
            target_lambda=loop4.ALLOSTATIC_TARGET_LAMBDA,
            cost_scale=loop4.ALLOSTATIC_COST_SCALE,
            **controls,
        ),
    }


def sign_pair_status(pair: dict[str, float]) -> dict[str, bool]:
    return {
        "homeostatic_expected_negative": pair["homeostatic"] < -GAP_FLOOR,
        "allostatic_expected_positive": pair["allostatic"] > GAP_FLOOR,
    }


def sign_match(left: dict[str, float], right: dict[str, float]) -> bool:
    return (left["homeostatic"] < 0.0) == (right["homeostatic"] < 0.0) and (
        left["allostatic"] > 0.0
    ) == (right["allostatic"] > 0.0)


def max_abs_gap(left: dict[str, float], right: dict[str, float]) -> float:
    return max(abs(left[key] - right[key]) for key in ["homeostatic", "allostatic"])


def main() -> int:
    started = time.time()
    loop4 = load_module(LOOP4_MODULE_PATH, "peps3d_axis0_loop4")
    scaling_module = loop4.load_module(loop4.SCALING_MODULE_PATH, "peps3d_axis0_scaling")
    binding_module = loop4.load_module(loop4.BINDING_MODULE_PATH, "peps3d_axis0_runtime_binding")

    nominal_flux = read_flux(
        loop4,
        scaling_module,
        binding_module,
        SOURCE_SHAPE,
        engine_type=0,
        lam=loop4.LAM0,
        mode="allostatic",
        boundary=PRIMARY_BOUNDARY,
    )
    erased_flux = read_flux(
        loop4,
        scaling_module,
        binding_module,
        SOURCE_SHAPE,
        engine_type=0,
        lam=loop4.LAM0,
        mode="allostatic",
        boundary=PRIMARY_BOUNDARY,
        sheet_erased=True,
    )
    reversed_flux = read_flux(
        loop4,
        scaling_module,
        binding_module,
        SOURCE_SHAPE,
        engine_type=0,
        lam=loop4.LAM0,
        mode="allostatic",
        boundary=PRIMARY_BOUNDARY,
        reversed_shell_time=True,
    )
    swapped_engine_flux = read_flux(
        loop4,
        scaling_module,
        binding_module,
        SOURCE_SHAPE,
        engine_type=1,
        lam=loop4.LAM0,
        mode="allostatic",
        boundary=PRIMARY_BOUNDARY,
    )
    frozen_flux = read_flux(
        loop4,
        scaling_module,
        binding_module,
        SOURCE_SHAPE,
        engine_type=0,
        lam=loop4.LAM0,
        mode="allostatic",
        boundary=PRIMARY_BOUNDARY,
        topology_freeze=True,
    )

    source_axis0 = signed_pair(loop4, scaling_module, binding_module, SOURCE_SHAPE)
    heldout_axis0 = signed_pair(loop4, scaling_module, binding_module, HELDOUT_SHAPE)
    sheet_erased_axis0 = signed_pair(loop4, scaling_module, binding_module, SOURCE_SHAPE, sheet_erased=True)
    reversed_axis0 = signed_pair(loop4, scaling_module, binding_module, SOURCE_SHAPE, reversed_shell_time=True)
    engine_swapped_axis0 = signed_pair(loop4, scaling_module, binding_module, SOURCE_SHAPE, engine_type=1)
    topology_frozen_axis0 = signed_pair(loop4, scaling_module, binding_module, SOURCE_SHAPE, topology_freeze=True)
    target_scrambled_axis0 = signed_pair(loop4, scaling_module, binding_module, SOURCE_SHAPE, target_scramble=True)
    branch_count_null_axis0 = signed_pair(
        loop4,
        scaling_module,
        binding_module,
        SOURCE_SHAPE,
        branch_count_only=True,
    )
    recovery_only_null_axis0 = signed_pair(
        loop4,
        scaling_module,
        binding_module,
        SOURCE_SHAPE,
        recovery_only=True,
    )

    boundary_rows: dict[str, dict[str, Any]] = {}
    for boundary in BOUNDARIES:
        pair = signed_pair(loop4, scaling_module, binding_module, SOURCE_SHAPE, boundary=boundary)
        flux = read_flux(
            loop4,
            scaling_module,
            binding_module,
            SOURCE_SHAPE,
            engine_type=0,
            lam=loop4.LAM0,
            mode="allostatic",
            boundary=boundary,
        )
        boundary_rows[boundary] = {
            "Axis0": pair,
            "status": sign_pair_status(pair),
            "flux_norm": flux["flux_norm"],
            "topology_mutation_norm": flux["topology_mutation_norm"],
            "sampled_site_count": flux["sampled_site_count"],
        }

    source_status = sign_pair_status(source_axis0)
    heldout_status = sign_pair_status(heldout_axis0)
    boundary_signatures = {
        boundary: (
            row["Axis0"]["homeostatic"] < -GAP_FLOOR,
            row["Axis0"]["allostatic"] > GAP_FLOOR,
        )
        for boundary, row in boundary_rows.items()
    }
    unique_boundary_signatures = sorted(set(boundary_signatures.values()))

    flux_controls = {
        "sheet_erase": {
            "flux_ratio": erased_flux["flux_norm"] / max(nominal_flux["flux_norm"], scaling_module.EPS),
            "axis0_gap": max_abs_gap(source_axis0, sheet_erased_axis0),
        },
        "shell_time_reversal": {
            "jk_gap": abs(nominal_flux["jk_norm"] - reversed_flux["jk_norm"]),
            "axis0_gap": max_abs_gap(source_axis0, reversed_axis0),
        },
        "engine_swap": {
            "flux_gap": float(
                torch.linalg.vector_norm(
                    flux_vector(scaling_module, nominal_flux) - flux_vector(scaling_module, swapped_engine_flux)
                ).item()
            ),
            "axis0_gap": max_abs_gap(source_axis0, engine_swapped_axis0),
        },
        "topology_freeze": {
            "topology_mutation_gap": abs(
                nominal_flux["topology_mutation_norm"] - frozen_flux["topology_mutation_norm"]
            ),
            "axis0_gap": max_abs_gap(source_axis0, topology_frozen_axis0),
        },
    }
    null_controls = {
        "target_reference_scramble": {
            "Axis0": target_scrambled_axis0,
            "gap_vs_full": max_abs_gap(source_axis0, target_scrambled_axis0),
            "matches_full_sign": sign_match(source_axis0, target_scrambled_axis0),
        },
        "branch_count_only": {
            "Axis0": branch_count_null_axis0,
            "gap_vs_full": max_abs_gap(source_axis0, branch_count_null_axis0),
            "matches_full_sign": sign_match(source_axis0, branch_count_null_axis0),
        },
        "recovery_only": {
            "Axis0": recovery_only_null_axis0,
            "gap_vs_full": max_abs_gap(source_axis0, recovery_only_null_axis0),
            "matches_full_sign": sign_match(source_axis0, recovery_only_null_axis0),
        },
    }

    checks = {
        "P1_flux_and_axis0_objects_are_separate": "J_flux" in nominal_flux and isinstance(source_axis0, dict),
        "P2_nominal_flux_present": nominal_flux["flux_norm"] > GAP_FLOOR,
        "P3_sheet_erase_control_changes_flux": flux_controls["sheet_erase"]["flux_ratio"] < 0.75,
        "P4_shell_time_reversal_changes_jk_layer": flux_controls["shell_time_reversal"]["jk_gap"] > GAP_FLOOR,
        "P5_engine_swap_changes_flux": flux_controls["engine_swap"]["flux_gap"] > GAP_FLOOR,
        "P6_topology_freeze_changes_topology_readout": flux_controls["topology_freeze"]["topology_mutation_gap"]
        > GAP_FLOOR,
        "P7_null_controls_do_not_collapse_to_full_axis0": any(
            not row["matches_full_sign"] or row["gap_vs_full"] > GAP_FLOOR for row in null_controls.values()
        ),
        "P8_heldout_no_refit_status_reported": isinstance(heldout_status["homeostatic_expected_negative"], bool)
        and isinstance(heldout_status["allostatic_expected_positive"], bool),
        "P9_boundary_sampler_variation_reported": len(boundary_rows) == len(BOUNDARIES)
        and (
            len(unique_boundary_signatures) > 1
            or max(abs(row["Axis0"]["homeostatic"] - source_axis0["homeostatic"]) for row in boundary_rows.values())
            > GAP_FLOOR
        ),
        "P10_nonpromotion_boundary_intact": CLASSIFICATION == "formal_scout"
        and PROMOTION_ALLOWED is False
        and ADMISSION_STATUS == "blocked"
        and EXPECTED_NONPROMOTION is True,
    }

    source_passes_expected_sign = all(source_status.values())
    heldout_passes_expected_sign = all(heldout_status.values())
    sampler_sensitive = len(unique_boundary_signatures) > 1
    null_mimics_full = {name: row["matches_full_sign"] for name, row in null_controls.items()}
    candidate_survived = bool(
        source_passes_expected_sign
        and heldout_passes_expected_sign
        and not sampler_sensitive
        and not all(null_mimics_full.values())
    )

    positive = {
        "engine_bound_quaternionic_flux_present": {
            "pass": checks["P1_flux_and_axis0_objects_are_separate"] and checks["P2_nominal_flux_present"],
            "J_flux": nominal_flux["J_flux"],
            "topology_mutation_norm": nominal_flux["topology_mutation_norm"],
        },
        "required_controls_executed": {
            "pass": all(
                checks[key]
                for key in [
                    "P3_sheet_erase_control_changes_flux",
                    "P4_shell_time_reversal_changes_jk_layer",
                    "P5_engine_swap_changes_flux",
                    "P6_topology_freeze_changes_topology_readout",
                ]
            ),
            "flux_controls": flux_controls,
        },
        "axis0_signed_gradient_computed": {
            "pass": isinstance(source_axis0["homeostatic"], float) and isinstance(source_axis0["allostatic"], float),
            "source_axis0": source_axis0,
            "source_sign_status": source_status,
        },
    }
    graveyard = {
        "heldout_shape_no_refit_is_not_promotion": {
            "pass": checks["P8_heldout_no_refit_status_reported"],
            "heldout_shape": shape_key(HELDOUT_SHAPE),
            "heldout_axis0": heldout_axis0,
            "heldout_sign_status": heldout_status,
            "heldout_passes_expected_sign": heldout_passes_expected_sign,
        },
        "boundary_sampler_variation_blocks_closure": {
            "pass": checks["P9_boundary_sampler_variation_reported"],
            "boundary_rows": boundary_rows,
            "unique_boundary_signatures": unique_boundary_signatures,
            "sampler_sensitive": sampler_sensitive,
        },
        "null_controls_are_not_formal_proofs": {
            "pass": checks["P7_null_controls_do_not_collapse_to_full_axis0"],
            "null_controls": null_controls,
        },
    }
    boundary = {
        "formal_scout_only": {"pass": checks["P10_nonpromotion_boundary_intact"]},
        "admission_status": {
            "pass": ADMISSION_STATUS == "blocked" and EXPECTED_NONPROMOTION is True,
            "status": ADMISSION_STATUS,
            "expected_nonpromotion": EXPECTED_NONPROMOTION,
        },
        "candidate_not_promoted": {
            "pass": candidate_survived is False,
            "candidate_survived": candidate_survived,
            "reason": (
                "Integrated controls executed, but heldout/sampler/null-control boundaries are stress receipts, "
                "not final closure."
            ),
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
        "positive": as_jsonable(positive),
        "graveyard_companions": as_jsonable(graveyard),
        "boundary": as_jsonable(boundary),
        "checks": checks,
        "source_shape": shape_key(SOURCE_SHAPE),
        "heldout_shape": shape_key(HELDOUT_SHAPE),
        "primary_boundary": PRIMARY_BOUNDARY,
        "conceptual_split": {
            "J_flux": "engine-bound quaternionic chiral boundary current",
            "Axis0": "signed QIT/FEP entropy gradient read over J_flux",
            "collapsed": False,
        },
        "candidate_survived": candidate_survived,
        "stress_summary": {
            "source_passes_expected_sign": source_passes_expected_sign,
            "heldout_passes_expected_sign": heldout_passes_expected_sign,
            "sampler_sensitive": sampler_sensitive,
            "null_mimics_full": null_mimics_full,
        },
        "nearby_variants": {
            "passed": sum(1 for row in variants if row["pass"]) + sum(1 for value in checks.values() if value),
            "total": len(variants) + len(checks),
            "failed_checks": [key for key, value in checks.items() if not value],
        },
        "all_pass": all(checks.values()) and all(row["pass"] for row in variants),
        "why_not_final": [
            "This uses runtime-bound local PEPS3D boundary contractions, not full PEPS3D environment closure.",
            "No-refit heldout status is reported, not tuned.",
            "Boundary sampler variation is a closure blocker unless independently derived or made invariant.",
            "Null controls show why J_flux, branch entropy, and recovery terms cannot be collapsed into one scalar proof.",
            "Xi/Phi0 remains open; this row only hardens a formal scout layer.",
        ],
        "divergence_log": [
            "J_flux and Axis0 are computed as separate readouts.",
            "Sheet erasure, shell-time reversal, engine swap, and topology freeze are controls, not fit knobs.",
            "Target/reference scramble, branch-count-only, and recovery-only nulls are reported as graveyard companions.",
            "Heldout shape and boundary sampler variation are reported without refitting calibration constants.",
        ],
        "why_not_v4_probes": "This is a v5 PEPS3D shell/boundary formal scout, not a legacy v4 probe.",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "candidate_survived": candidate_survived,
                "failed_checks": result["nearby_variants"]["failed_checks"],
                "stress_summary": result["stress_summary"],
                "wrote": str(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
