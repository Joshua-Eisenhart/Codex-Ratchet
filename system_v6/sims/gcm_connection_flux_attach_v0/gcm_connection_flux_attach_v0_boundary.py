#!/usr/bin/env python3
"""Packet-local G.2a boundary checks for gcm_connection_flux_attach_v0."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import gcm_connection_flux_attach_v0_common as common


def boundary_errors(payload: dict[str, Any], sim_dir: Path = common.SIM_DIR) -> list[str]:
    errors: list[str] = []
    gates = payload.get("builder_gates", {})
    if gates.get("file_disjoint_packet") is not True:
        errors.append("file_disjoint_packet gate missing")
    if gates.get("boundary_helper_fully_used") is not True:
        errors.append("boundary_helper_fully_used gate missing")
    if gates.get("G_2a_idempotency_from_birth") is not True:
        errors.append("G_2a_idempotency_from_birth gate missing")
    if gates.get("lineage_free_negative_required") is not True:
        errors.append("lineage_free_negative_required gate missing")
    if payload.get("no_builder_audit_verdict") is not True:
        errors.append("no_builder_audit_verdict must be true")
    if payload.get("no_builder_audit_verdict_envelope_gate") is not True:
        errors.append("no_builder_audit_verdict_envelope_gate must be true")
    errors.extend(common.builder_audit_boundary_errors(payload, sim_dir / "audit_verdict.md"))
    return errors
