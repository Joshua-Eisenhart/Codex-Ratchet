#!/usr/bin/env python3
"""Packet-local boundary checks for gcm_object_id_freeze_v0."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import gcm_object_id_freeze_v0 as common


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def boundary_errors(payload: dict[str, Any], sim_dir: Path = common.SIM_DIR) -> list[str]:
    errors: list[str] = []
    require(errors, payload.get("classification") == common.CLASSIFICATION, "classification must stay scratch_diagnostic")
    require(errors, payload.get("claim_ceiling") == common.CLAIM_CEILING, "claim_ceiling mismatch")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("not_THE_manifold") is True, "not_THE_manifold flag missing")
    require(errors, payload.get("carrier_and_pins_relative") is True, "carrier_and_pins_relative flag missing")
    require(errors, payload.get("no_builder_audit_verdict") is True, "no_builder_audit_verdict must be true")
    require(errors, payload.get("no_builder_audit_verdict_envelope_gate") is True, "no_builder_audit_verdict_envelope_gate must be true")

    gates = payload.get("builder_gates", {})
    for gate in (
        "G_2a_idempotency_from_birth",
        "file_disjoint_packet",
        "substrate_check_helper_script_side",
        "staleness_tooth_embedded",
        "unknown_object_id_tooth",
    ):
        require(errors, gates.get(gate) is True, f"{gate} gate missing")

    disallowed = set(payload.get("disallowed_claims", []))
    for claim in {"THE manifold", "terrain atlas admission", "axis admission", "engine admission", "physics admission"}:
        require(errors, claim in disallowed, f"missing disallowed claim: {claim}")

    errors.extend(builder_audit_boundary_errors(payload, sim_dir / "audit_verdict.md"))
    return errors
