#!/usr/bin/env python3
"""Validate the bounded one-thing surface for manifold_unified_run_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path

SIM_ID = "manifold_unified_run_v0"
RESULT = Path(__file__).resolve().parent / "results" / f"{SIM_ID}_envelope_results.json"


def main() -> int:
    payload = json.loads(RESULT.read_text(encoding="utf-8"))
    errors: list[str] = []
    if payload.get("classification") != "scratch_diagnostic":
        errors.append("classification must stay scratch_diagnostic")
    if payload.get("promotion_allowed") is not False:
        errors.append("promotion_allowed must be false")
    if payload.get("formal_admission_allowed") is not False:
        errors.append("formal_admission_allowed must be false")
    if payload.get("scope_fence", {}).get("manifold_level_admission") is not False:
        errors.append("scope fence must block manifold admission")
    if payload.get("scope_fence", {}).get("bridge_or_axis_claim") is not False:
        errors.append("scope fence must block bridge/axis claim")
    if payload.get("scope_fence", {}).get("mct_theorem") is not False:
        errors.append("scope fence must block M(C,t) theorem")
    if not payload.get("one_thing_check", {}).get("pass"):
        errors.append("one_thing_check failed")
    if not payload.get("trajectory_artifact", {}).get("verified"):
        errors.append("trajectory artifact was not verified")
    for engine_name, engine in payload.get("engines", {}).items():
        if not engine.get("trajectory_artifact", {}).get("verified"):
            errors.append(f"{engine_name} did not verify trajectory artifact")
    steps = payload.get("trajectory", {}).get("steps", [])
    if [step.get("step_name") for step in steps] != [
        "integrated_seed",
        "leaf_conditioning",
        "lens_quotient",
        "terrain_restriction",
    ]:
        errors.append("trajectory steps are missing or out of order")
    state_ids = {step.get("state_object_id") for step in steps}
    if len(state_ids) != 1:
        errors.append("steps do not share one state_object_id")
    classification = payload.get("row_family_step_classification", {})
    expected_classes = {
        "s2_geometry": "STEP-DEPENDENT",
        "s3_density_probe": "STEP-INVARIANT",
        "spinor_signed_rows": "STEP-INVARIANT",
        "s5_s6_leakage_rows": "STEP-INVARIANT",
        "s6_taxonomy": "STEP-INVARIANT",
        "s5_s6_terrain_flow": "STEP-DEPENDENT",
        "flux_continuity": "STEP-DEPENDENT",
        "entropy_ledger_row": "STEP-DEPENDENT",
        "deformation_mode": "STEP-DEPENDENT",
    }
    for family, step_class in expected_classes.items():
        row = classification.get(family, {})
        if row.get("step_class") != step_class or not row.get("why"):
            errors.append(f"row family classification missing or wrong: {family}")
    one_thing = payload.get("one_thing_check", {})
    if one_thing.get("nested_row_lineage_present") is not True:
        errors.append("nested row lineage ids are missing")
    spectrum_change = one_thing.get("s2_holonomy_spectrum_change", {})
    if spectrum_change.get("changed") is not True:
        errors.append("S2 holonomy spectrum did not change at lens step")
    if spectrum_change.get("pre_lens_value") == spectrum_change.get("lens_value"):
        errors.append("S2 holonomy spectrum pre-lens and lens values are equal")
    if payload.get("cross_layer_findings"):
        errors.append(f"cross-layer findings present: {payload['cross_layer_findings']}")
    if not payload.get("cross_layer_consistency_matrix", {}).get("all_pass"):
        errors.append("cross-layer consistency matrix did not pass")
    if not payload.get("one_to_one_tool_calls", {}).get("pass"):
        errors.append("tool_calls are not one-to-one with capability receipts")
    gates = payload.get("build_gates", {})
    for key in (
        "solver_erased_flips_fire",
        "trajectory_artifact_verified",
        "all_engine_legs_verified_trajectory_artifact",
        "nested_row_lineage_present",
        "step_dependent_s2_holonomy_spectrum_changes",
        "z3_cvc5_agree",
        "julia_z3_agrees",
        "max_divergence_within_tolerance",
        "layer_decoupled_control_pass",
        "active_n4_lane_untouched",
    ):
        if gates.get(key) is not True:
            errors.append(f"build gate failed: {key}")
    print(json.dumps({"ok": not errors, "errors": errors, "result_json": str(RESULT)}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
