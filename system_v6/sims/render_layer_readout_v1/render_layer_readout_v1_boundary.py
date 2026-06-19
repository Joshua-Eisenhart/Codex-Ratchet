#!/usr/bin/env python3
"""Boundary checks for render_layer_readout_v1."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402

import render_layer_readout_v1_common as common  # noqa: E402


classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
TOOL_MANIFEST = {
    "builder_audit_boundary": {"tried": True, "used": True, "reason": "enforces post-audit-idempotent builder/audit boundary"},
    "render_layer_readout_v1_common": {"tried": True, "used": True, "reason": "provides constants for packet boundary checks"},
}
TOOL_INTEGRATION_DEPTH = {"builder_audit_boundary": "supportive", "render_layer_readout_v1_common": "supportive"}


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def boundary_errors(payload: dict[str, Any], sim_dir: Path) -> list[str]:
    errors: list[str] = []
    require(errors, payload.get("classification") == "scratch_diagnostic", "classification must stay scratch_diagnostic")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("claim_ceiling") == common.CLAIM_CEILING, "claim_ceiling mismatch")
    require(errors, payload.get("no_builder_audit_verdict") is True, "no_builder_audit_verdict helper gate must be true")

    gate = payload.get("repin_reachability_gate", {})
    require(errors, gate.get("gate_name") == "render_polarity_reachability_witness", "missing reachability witness gate")
    require(errors, gate.get("status") == "passed", "reachability witness gate must pass for accepted payload")
    require(errors, gate.get("label_counts", {}).get("reshape_the_render", 0) > 0, "reshape_the_render must be reachable")
    require(errors, gate.get("label_counts", {}).get("resist_the_update", 0) > 0, "resist_the_update must be reachable")
    require(errors, "reshape_the_render" in gate.get("witnesses", {}), "missing reshape witness")
    require(errors, "resist_the_update" in gate.get("witnesses", {}), "missing resist witness")

    require(errors, payload.get("construction_status") == "repin_reachability_passed", "construction status mismatch")
    require(errors, payload.get("readout_table_ran") is True, "readout table must run only after gate passes")
    require(errors, "render_readout" in payload, "accepted payload must include render_readout")

    counts = payload.get("counts", {})
    require(errors, counts.get("reshape_cells", 0) > 0, "reshape_cells must be positive")
    require(errors, counts.get("resist_cells", 0) > 0, "resist_cells must be positive")
    require(errors, counts.get("unique_render_sign_count", 0) >= 2, "render sign vector must be nonconstant")

    controls = payload.get("controls", {})
    old = controls.get("v0_old_pin_regression", {})
    require(errors, old.get("reproduces_unreachable_reshape") is True, "old v0 pin regression must reproduce unreachable reshape")
    require(errors, old.get("readout_table_ran") is False, "old v0 pin regression must refuse readout rows")
    scrambled = controls.get("scrambled_error", {})
    require(errors, scrambled.get("verdict") == "breaks-render-polarity", "scrambled-error control must break v1 polarity")
    require(errors, scrambled.get("same_cell_count", common.EXPECTED_STATE_COUNT) < common.EXPECTED_STATE_COUNT, "scrambled-error same count must be less than full carrier")
    require(errors, scrambled.get("constant_readout") is False, "scrambled-error control must not see a constant readout")
    require(errors, controls.get("no_identity_leak", {}).get("verdict") == "passes-no-identity-leak", "no-identity-leak control failed")

    boundary = payload.get("axis0_boundary", {}).get("boundary_verdict", {})
    require(errors, boundary.get("question") == "same distinction, different distinction, or no stable distinction", "boundary question mismatch")
    require(
        errors,
        boundary.get("relation_to_axis0_phi") in {"same_distinction_alias_into_axis0", "different_distinction_from_axis0", "falsifier"},
        "invalid Axis-0 boundary relation",
    )
    require(errors, boundary.get("expectation_3_falsifier_live") is True, "expectation 3 falsifier must be live after re-pin")

    allowed = set(payload.get("allowed_claims", []))
    disallowed = set(payload.get("disallowed_claims", []))
    require(errors, bool(allowed), "allowed_claims must be non-empty")
    require(errors, bool(disallowed), "disallowed_claims must be non-empty")
    for claim in {"holodeck admission", "FEP admission", "physics admission", "formal admission", "canonical by process", "manifold claim"}:
        require(errors, claim in disallowed, f"disallowed_claims missing {claim}")

    errors.extend(builder_audit_boundary_errors(payload, sim_dir / "audit_verdict.md"))
    return errors
