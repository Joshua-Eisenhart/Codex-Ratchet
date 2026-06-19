#!/usr/bin/env python3
"""Boundary checks for fiber_augmented_cover_v0."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


REQUIRED_CEILING = "axis_readout_candidate_only + faithful_fiber_augmented_cover_b6_law_test_v0"
REQUIRED_STATUS = {
    "holds_on_faithful_cover",
    "fails_on_faithful_cover",
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
        errors.append("no_builder_audit_verdict must be true")
    errors.extend(builder_audit_boundary_errors(payload, sim_dir / "audit_verdict.md"))

    relation = payload.get("b6_law_test", {})
    if relation.get("table_kind") != "faithful_fiber_augmented_cover_table":
        errors.append("b6 law table must be the faithful cover table")
    if relation.get("law_test_status") not in REQUIRED_STATUS:
        errors.append("b6 law test has an invalid status")
    if relation.get("relation_not_used_to_assign_axis3") is not True:
        errors.append("Axis3 must not be assigned from the b6 relation")

    faith = payload.get("faithfulness", {})
    for axis in ("axis0", "axis3", "axis6"):
        if axis not in faith:
            errors.append(f"missing faithfulness block: {axis}")
    if faith.get("axis0", {}).get("projects_to_committed_axis0") is not True:
        errors.append("Axis0 pullback does not project to committed Axis0")
    if faith.get("axis3", {}).get("source_backed_equivalent_adapter") is not True:
        errors.append("Axis3 adapter is not marked source-backed")
    if faith.get("axis6", {}).get("projects_to_committed_axis6") is not True:
        errors.append("Axis6 pullback does not project to committed Axis6")

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
    }
    if not forbidden_claims <= disallowed:
        errors.append("disallowed_claims missing standard overclaim blockers")
    return errors
