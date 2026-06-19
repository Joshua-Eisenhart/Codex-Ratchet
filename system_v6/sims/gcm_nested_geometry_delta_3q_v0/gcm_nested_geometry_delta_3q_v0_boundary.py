#!/usr/bin/env python3
"""Boundary assertions for the 3Q nested geometry-delta builder."""

from __future__ import annotations

from pathlib import Path

from gcm_nested_geometry_delta_3q_v0_common import AUDIT_VERDICT_PATH, SIM_DIR, builder_audit_boundary_ok, rel


def boundary_payload() -> dict[str, object]:
    return {
        "file_disjoint_packet": rel(SIM_DIR),
        "no_builder_audit_verdict": True,
        "audit_verdict_path": rel(AUDIT_VERDICT_PATH),
        "builder_audit_boundary_ok": builder_audit_boundary_ok(Path(AUDIT_VERDICT_PATH)),
    }
