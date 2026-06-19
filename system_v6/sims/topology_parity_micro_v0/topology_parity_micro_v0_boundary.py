#!/usr/bin/env python3
"""Boundary checks for topology_parity_micro_v0."""

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
REQUIRED_CEILING = "scratch_diagnostic_independent_topology_guard_for_fiber_augmented_cover_v1_only"
TOOL_MANIFEST = {
    "builder_audit_boundary": {"tried": True, "used": True, "reason": "checks post-audit-idempotent builder/audit boundary flags"},
    "pathlib": {"tried": True, "used": True, "reason": "resolves packet and helper paths for boundary checks"},
}
TOOL_INTEGRATION_DEPTH = {
    "builder_audit_boundary": "supportive",
    "pathlib": "supportive",
}


def boundary_errors(payload: dict[str, Any], sim_dir: Path) -> list[str]:
    errors: list[str] = []
    if payload.get("classification") != CLASSIFICATION:
        errors.append("classification must stay scratch_diagnostic")
    if payload.get("promotion_allowed") is not False:
        errors.append("promotion_allowed must be false")
    if payload.get("formal_admission_allowed") is not False:
        errors.append("formal_admission_allowed must be false")
    if payload.get("claim_ceiling") != REQUIRED_CEILING:
        errors.append("claim_ceiling mismatch")
    if payload.get("no_builder_audit_verdict") is not True:
        errors.append("no_builder_audit_verdict must be true")
    if payload.get("preregistration_order") != "expected_profiles_declared_before_computation":
        errors.append("expected profiles must be preregistered before computation")

    expected = payload.get("expected_profiles_preregistered_from_math", {})
    if expected.get("v1_degree_one_cover", {}).get("expected_betti_b0_b1_b2_b3") != [1, 0, 0, 1]:
        errors.append("v1 ideal expected Betti profile mismatch")
    if expected.get("zero_shift_product_cover", {}).get("expected_betti_b0_b1_b2_b3") != [1, 1, 1, 1]:
        errors.append("product ideal expected Betti profile mismatch")

    controls = payload.get("controls", {})
    if controls.get("all_reference_controls_pass") is not True:
        errors.append("reference controls must pass before cover parity is considered")
    if controls.get("mislabeled_torus_as_sphere_negative", {}).get("pass") is not True:
        errors.append("mislabeled-complex negative must pass")

    complexes = payload.get("complexes", {})
    for key in ("v1_degree_one_cover", "zero_shift_product_cover"):
        row = complexes.get(key, {})
        if row.get("vertex_count") != 99:
            errors.append(f"{key} must have 99 cover-state vertices")
        if row.get("gudhi_hodge_agree_through_b2") is not True:
            errors.append(f"{key} GUDHI Betti and TopoNetX Hodge kernels must agree through b2")
        if not row.get("source_cover_sha256"):
            errors.append(f"{key} missing source cover hash")

    parity = payload.get("parity_adjudication", {})
    if parity.get("guard_status") not in {
        "earned_independent_topology_guard",
        "not_earned_resolution_insufficient",
        "not_earned_profiles_equal",
    }:
        errors.append("invalid parity guard status")
    if parity.get("ideal_profiles_match") is not True and parity.get("complex_building_resolution_indicted") is not True:
        errors.append("non-ideal profile outcomes must indict complex-building resolution")

    forbidden_claims = {"new bundle claim", "formal admission", "canonical by process", "axis-level closure", "physics/manifold claim"}
    if not forbidden_claims <= set(payload.get("disallowed_claims", [])):
        errors.append("disallowed_claims missing standard blockers")

    errors.extend(builder_audit_boundary_errors(payload, sim_dir / "audit_verdict.md"))
    return errors
