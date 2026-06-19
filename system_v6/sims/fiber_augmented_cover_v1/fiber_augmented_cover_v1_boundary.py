#!/usr/bin/env python3
"""Boundary checks for fiber_augmented_cover_v1."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


CLASSIFICATION = "scratch_diagnostic"
TOOL_MANIFEST = {
    "builder_audit_boundary": {"tried": True, "used": True, "reason": "checks post-audit-idempotent builder/audit boundary flags"},
    "pathlib": {"tried": True, "used": True, "reason": "resolves packet and helper paths for boundary checks"},
}
TOOL_INTEGRATION_DEPTH = {
    "builder_audit_boundary": "supportive",
    "pathlib": "supportive",
}
REQUIRED_CEILING = "axis_readout_candidate_only + nontrivial_cover_faithful_fiber_augmented_cover_b6_law_test_v1"
REQUIRED_STATUS = {
    "holds_on_nontrivial_faithful_cover",
    "fails_on_nontrivial_faithful_cover",
    "inconclusive_no_nonneutral_rows",
}


def boundary_errors(payload: dict[str, Any], sim_dir: Path) -> list[str]:
    errors: list[str] = []
    if payload.get("classification") != "scratch_diagnostic":
        errors.append("classification must stay scratch_diagnostic")
    if payload.get("promotion_allowed") is not False:
        errors.append("promotion_allowed must be false")
    if payload.get("formal_admission_allowed") is not False:
        errors.append("formal_admission_allowed must be false")
    if payload.get("claim_ceiling") != REQUIRED_CEILING:
        errors.append("claim_ceiling mismatch")
    if payload.get("no_builder_audit_verdict") is not True:
        errors.append("no_builder_audit_verdict helper gate must be true")

    witness = payload.get("bundle_witness", {})
    if witness.get("loop_name") != "committed_equatorial_loop":
        errors.append("bundle witness must be computed on the committed equatorial loop")
    if witness.get("directed_winding") not in {-1, 1}:
        errors.append("main packet witness must be +/-1")
    if witness.get("nontrivial_gate_passed") is not True:
        errors.append("nontrivial witness gate must pass before law rows")

    cover = payload.get("cover", {})
    if cover.get("fiber_phase_count_per_cell") != 3:
        errors.append("v1 must pin |F|=3 for directed winding")
    shift_counts = cover.get("base_lift_phase_shift_counts", {})
    if not any(int(shift) != 0 and count > 0 for shift, count in shift_counts.items()):
        errors.append("base-lift phase shifts must include nonzero transition rows")

    relation = payload.get("b6_law_test", {})
    if relation.get("table_kind") != "faithful_nontrivial_fiber_augmented_cover_table":
        errors.append("b6 law table must be the faithful nontrivial cover table")
    if relation.get("witness_gate_required") is not True or relation.get("witness_gate_passed") is not True:
        errors.append("b6 law table must record a passed witness gate")
    if relation.get("law_test_status") not in REQUIRED_STATUS:
        errors.append("b6 law test has an invalid status")
    if relation.get("relation_not_used_to_assign_axis3") is not True:
        errors.append("Axis3 must not be assigned from the b6 relation")
    if relation.get("null_model") != "independent_random_signs_match_product_law_with_p_0_5":
        errors.append("chance null model must be explicit")

    if len(payload.get("sign_variant_table", [])) != 8:
        errors.append("full 8-sign-variant table is required")

    faith = payload.get("faithfulness", {})
    for axis in ("axis0", "axis3", "axis6"):
        if axis not in faith:
            errors.append(f"missing faithfulness block: {axis}")
    if faith.get("axis0", {}).get("projects_to_committed_axis0") is not True:
        errors.append("Axis0 pullback does not project to committed Axis0")
    if faith.get("axis3", {}).get("source_backed_equivalent_adapter") is not True:
        errors.append("Axis3 adapter is not marked source-backed")
    if faith.get("axis3", {}).get("predicate_mismatch_count") != 0:
        errors.append("Axis3 predicate mismatch count must be zero")
    if faith.get("axis6", {}).get("projects_to_committed_axis6") is not True:
        errors.append("Axis6 pullback does not project to committed Axis6")

    controls = payload.get("controls", {})
    trivial = controls.get("v0_trivial_bundle_regression", {})
    if trivial.get("witness_zero") is not True:
        errors.append("v0 trivial-bundle regression must compute witness zero")
    if trivial.get("law_table_refused") is not True:
        errors.append("v0 trivial-bundle regression must exercise v1 law-table refusal")
    if trivial.get("v0_law_table_reproduced_at_chance") is not True:
        errors.append("v0 trivial-bundle regression must preserve at-chance law result")
    if controls.get("scrambled_control", {}).get("ran") is not True:
        errors.append("scrambled control must run")
    if controls.get("convention_flip_control", {}).get("ran") is not True:
        errors.append("convention-flip control must run")

    allowed = set(payload.get("allowed_claims", []))
    disallowed = set(payload.get("disallowed_claims", []))
    if not allowed:
        errors.append("allowed_claims must be non-empty")
    if not disallowed:
        errors.append("disallowed_claims must be non-empty")
    forbidden_claims = {
        "Axis3 placement on the 33-cell quotient without the finite fiber",
        "axis independence proof",
        "physics/manifold claim",
        "formal admission",
        "canonical by process",
    }
    if not forbidden_claims <= disallowed:
        errors.append("disallowed_claims missing standard overclaim blockers")

    errors.extend(builder_audit_boundary_errors(payload, sim_dir / "audit_verdict.md"))
    return errors
