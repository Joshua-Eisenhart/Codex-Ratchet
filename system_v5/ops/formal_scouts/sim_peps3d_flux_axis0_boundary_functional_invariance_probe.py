#!/usr/bin/env python3
"""Boundary-functional invariance scout for PEPS3D flux-bound Axis0.

Formal scout only.

The sampler stress row showed that arbitrary deterministic boundary samplers
can flip Axis0 signs. This row separates two claims:

1. A finite all-boundary surface mean is a less arbitrary boundary functional
   than canonical subsampling on the source 8/27/64 shapes.
2. This still does not create sampler invariance or held-out closure: the
   all-boundary functional inherits the (3, 3, 4) homeostatic failure.
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
OUT_PATH = RESULT_DIR / "peps3d_flux_axis0_boundary_functional_invariance_probe_results.json"
SAMPLER_MODULE_PATH = ROOT / "sim_peps3d_flux_axis0_boundary_sampler_stress_probe.py"
SAMPLER_RECEIPT = RESULT_DIR / "peps3d_flux_axis0_boundary_sampler_stress_probe_results.json"

NAME = "peps3d_flux_axis0_boundary_functional_invariance_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical_peps3d_flux_axis0_boundary_functional_invariance"
SOURCE_ALIGNMENT_CATEGORY = "peps3d_flux_bound_axis0_boundary_functional_invariance"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: separates finite all-boundary surface averaging from "
    "arbitrary boundary subsampling for PEPS3D flux-bound Axis0. It does not "
    "admit sampler-invariant Axis0, final flux, full PEPS3D closure, Xi, "
    "Phi0, gravity, Standard Model, Yang-Mills, Riemann, or physics claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing tensor sign/margin checks over boundary-functional gradients",
    },
    "peps3d_flux_axis0_boundary_sampler_stress_probe": {
        "tried": True,
        "used": True,
        "reason": "supportive reuse of sampled/all-boundary flux-gradient functions",
    },
    "peps3d_spinor_network_flux_axis0_scaling_probe": {
        "tried": True,
        "used": True,
        "reason": "supportive PEPS3D spinor/quaternion transport functions used through the boundary sampler module",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive receipt IO and result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "peps3d_flux_axis0_boundary_sampler_stress_probe": "supportive",
    "peps3d_spinor_network_flux_axis0_scaling_probe": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

SOURCE_SHAPES = [(2, 2, 2), (3, 3, 3), (4, 4, 4)]
HELDOUT_SHAPES = [(2, 3, 4), (2, 4, 4), (3, 3, 4)]
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


def shape_key(shape: tuple[int, int, int]) -> str:
    return "x".join(str(item) for item in shape)


def load_sampler_module() -> Any:
    sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location("peps3d_axis0_boundary_sampler", SAMPLER_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {SAMPLER_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    started = time.time()
    sampler_receipt = json.loads(SAMPLER_RECEIPT.read_text(encoding="utf-8"))
    sampler_module = load_sampler_module()
    scaling_module = sampler_module.calibration.load_scaling_module()

    source_all_boundary = [
        row for row in sampler_receipt["sampler_rows"] if row["sampler"] == "all_boundary"
    ]
    source_all_boundary_pass = all(row["homeostatic_pass"] and row["allostatic_pass"] for row in source_all_boundary)
    arbitrary_sampler_failures = sampler_receipt["graveyard_companions"][
        "sampler_invariant_axis0_sign_claim_killed_if_any_fail"
    ]["failed_sign_cells"]

    heldout_rows: list[dict[str, Any]] = []
    for shape in HELDOUT_SHAPES:
        home = sampler_module.gradient_sampled(scaling_module, shape, "homeostatic", "all_boundary")
        allo = sampler_module.gradient_sampled(scaling_module, shape, "allostatic", "all_boundary")
        surface = sampler_module.boundary_surface(scaling_module, shape)
        selected = sampler_module.sampler_sites(scaling_module, shape, "all_boundary")
        heldout_rows.append(
            {
                "shape": shape,
                "shape_key": shape_key(shape),
                "surface_site_count": len(surface),
                "selected_site_count": len(selected),
                "all_boundary_selects_full_surface": set(surface) == set(selected) and len(surface) == len(selected),
                "homeostatic_gradient": home,
                "allostatic_gradient": allo,
                "homeostatic_pass": home < -GAP_FLOOR,
                "allostatic_pass": allo > GAP_FLOOR,
            }
        )

    source_margins = torch.tensor(
        [abs(row["homeostatic_gradient"]) for row in source_all_boundary]
        + [abs(row["allostatic_gradient"]) for row in source_all_boundary],
        dtype=torch.float64,
    )
    heldout_home_values = torch.tensor([row["homeostatic_gradient"] for row in heldout_rows], dtype=torch.float64)
    heldout_allo_values = torch.tensor([row["allostatic_gradient"] for row in heldout_rows], dtype=torch.float64)

    checks = {
        "P1_all_boundary_source_shapes_pass": source_all_boundary_pass,
        "P2_all_boundary_selects_full_surface_on_heldouts": all(row["all_boundary_selects_full_surface"] for row in heldout_rows),
        "P3_arbitrary_subsampler_invariance_claim_killed": len(arbitrary_sampler_failures) > 0,
        "P4_all_boundary_heldout_not_closed": not bool(torch.all(heldout_home_values < -GAP_FLOOR).item()),
        "P5_all_boundary_allostatic_survives_heldouts": bool(torch.all(heldout_allo_values > GAP_FLOOR).item()),
        "P6_source_margin_nonzero": bool(torch.min(source_margins).item() > GAP_FLOOR),
        "P7_nonpromotion_boundary_intact": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False,
    }
    positive = {
        "all_boundary_surface_functional_source_pass": {
            "pass": checks["P1_all_boundary_source_shapes_pass"] and checks["P6_source_margin_nonzero"],
            "source_rows": source_all_boundary,
        },
        "all_boundary_full_surface_selection": {
            "pass": checks["P2_all_boundary_selects_full_surface_on_heldouts"],
            "heldout_surface_counts": {row["shape_key"]: row["surface_site_count"] for row in heldout_rows},
        },
    }
    graveyard = {
        "arbitrary_subsampler_invariant_axis0_sign_claim_killed": {
            "pass": checks["P3_arbitrary_subsampler_invariance_claim_killed"],
            "failed_sign_cells": arbitrary_sampler_failures,
        },
        "all_boundary_does_not_repair_heldout_calibration": {
            "pass": checks["P4_all_boundary_heldout_not_closed"],
            "heldout_rows": heldout_rows,
        },
    }
    boundary = {
        "formal_scout_only": {"pass": checks["P7_nonpromotion_boundary_intact"]},
        "boundary_functional_status": {
            "pass": checks["P1_all_boundary_source_shapes_pass"] and checks["P4_all_boundary_heldout_not_closed"],
            "status": "surface_mean_is_better_scaffold_but_not_sampler_or_shape_invariant_closure",
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
        "positive": as_jsonable(positive),
        "graveyard_companions": as_jsonable(graveyard),
        "boundary": as_jsonable(boundary),
        "heldout_all_boundary_rows": as_jsonable(heldout_rows),
        "checks": checks,
        "functional_status": boundary["boundary_functional_status"]["status"],
        "nearby_variants": {
            "passed": sum(1 for row in variants if row["pass"]) + sum(1 for value in checks.values() if value),
            "total": len(variants) + len(checks),
            "failed_checks": [key for key, value in checks.items() if not value],
        },
        "all_pass": all(checks.values()) and all(row["pass"] for row in variants),
        "why_not_final": [
            "All-boundary surface averaging is still local boundary contraction, not full PEPS3D environment closure.",
            "Arbitrary deterministic subsamplers still kill sampler-invariant sign claims.",
            "The all-boundary functional does not fix held-out homeostatic calibration.",
        ],
        "divergence_log": [
            "Surface-mean and arbitrary-subsampler claims are separated.",
            "Flux presence and sheet-erasure controls remain upstream; this row audits boundary functional status only.",
        ],
        "why_not_v4_probes": "This is a v5 PEPS3D flux-bound Axis0 boundary-functional scout, not a legacy v4 probe.",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "status": result["functional_status"]}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
