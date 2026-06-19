#!/usr/bin/env python3
"""Boundary checks for engine_16_stage_definition_correspondence_v0."""

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
CLAIM_CEILING = "macro_stage_definition_correspondence_proposal_only"


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def boundary_errors(payload: dict[str, Any], sim_dir: Path) -> list[str]:
    errors: list[str] = []
    require(errors, payload.get("classification") == CLASSIFICATION, "classification must stay scratch_diagnostic")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("claim_ceiling") == CLAIM_CEILING, "claim_ceiling mismatch")
    require(errors, payload.get("no_builder_audit_verdict") is True, "no_builder_audit_verdict must be true")
    require(
        errors,
        payload.get("no_builder_audit_verdict_envelope_gate") is True,
        "no_builder_audit_verdict_envelope_gate must be true",
    )

    gates = payload.get("builder_gates", {})
    require(errors, gates.get("G_2a_idempotency_from_birth") is True, "G.2a gate missing")
    require(errors, gates.get("G7_definitions_pinned_before_correspondence") is True, "G7 definition pin missing")
    require(errors, gates.get("file_disjoint_packet") is True, "file-disjoint boundary missing")
    require(errors, gates.get("no_engine_stage_admission") is True, "engine-stage admission fence missing")
    require(errors, gates.get("rx_dz_fixture_fence_carried") is True, "R_x/D_z fixture fence missing")

    controls = payload.get("controls", {})
    require(errors, controls.get("identity_stages", {}).get("n_distinct") == 1, "identity control must collapse to 1")
    require(
        errors,
        controls.get("erase_order_polarity", {}).get("n_distinct", 99) <= 8,
        "order-erased control must collapse toward 8",
    )
    require(
        errors,
        controls.get("erase_chirality", {}).get("all_lr_pairs_merge") is True,
        "chirality-erased control must merge L/R pairs",
    )
    require(
        errors,
        controls.get("scramble_operator_assignments", {}).get("does_not_improve_correspondence") is True,
        "scramble control improved correspondence",
    )

    disallowed = set(payload.get("disallowed_claims", []))
    for claim in (
        "engine-stage admission",
        "Matrix64 admission",
        "QIT-engine admission",
        "axis admission",
        "bridge admission",
        "manifold admission",
        "physics claim",
    ):
        require(errors, claim in disallowed, f"missing disallowed claim: {claim}")

    errors.extend(builder_audit_boundary_errors(payload, sim_dir / "audit_verdict.md"))
    return errors
