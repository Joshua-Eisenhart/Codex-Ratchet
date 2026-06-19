#!/usr/bin/env python3
"""Packet-local boundary checks for gcm_nesting_tower_le2q_v0."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


def boundary_errors(payload: dict[str, Any], sim_dir: Path) -> list[str]:
    errors = []
    errors.extend(builder_audit_boundary_errors(payload, sim_dir / "audit_verdict.md"))
    if payload.get("classification") != "scratch_diagnostic":
        errors.append("classification must remain scratch_diagnostic")
    if payload.get("promotion_allowed") is not False:
        errors.append("promotion_allowed must be false")
    if payload.get("formal_admission_allowed") is not False:
        errors.append("formal_admission_allowed must be false")
    if payload.get("carrier_and_pins_relative") is not True:
        errors.append("carrier_and_pins_relative must be true")
    disallowed = set(payload.get("disallowed_claims", []))
    for claim in ("canonical by process", "formal admission", "THE manifold", "axis admission"):
        if claim not in disallowed:
            errors.append(f"missing disallowed claim: {claim}")
    return errors
