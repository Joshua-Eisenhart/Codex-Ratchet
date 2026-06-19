from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = Path(__file__).resolve().parent
AUDIT_PATH = SIM_DIR / "audit_verdict.md"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.builder_audit_boundary import builder_audit_boundary_errors


REQUIRED_BUILDER_GATES = {
    "G_2a_idempotency_from_birth",
    "boundary_helper_fully_used",
    "file_disjoint_packet",
    "lineage_free_negative_required",
    "wrong_substrate_negative_required",
    "no_builder_audit_verdict",
    "no_builder_audit_verdict_envelope_gate",
    "substrate_check_helper_script_side",
}


def boundary_errors(payload: dict[str, Any], audit_path: Path = AUDIT_PATH) -> list[str]:
    errors: list[str] = []
    gates = payload.get("builder_gates", {})
    for key in sorted(REQUIRED_BUILDER_GATES):
        if gates.get(key) is not True:
            errors.append(f"builder gate {key} must be true")
    if payload.get("no_builder_audit_verdict") is not True:
        errors.append("no_builder_audit_verdict must be true")
    if payload.get("no_builder_audit_verdict_envelope_gate") is not True:
        errors.append("no_builder_audit_verdict_envelope_gate must be true")
    errors.extend(builder_audit_boundary_errors(payload, audit_path))
    return errors


def boundary_ok(payload: dict[str, Any], audit_path: Path = AUDIT_PATH) -> bool:
    return not boundary_errors(payload, audit_path)
