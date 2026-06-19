"""Helpers for post-audit-idempotent builder/audit file boundaries."""

from __future__ import annotations

from pathlib import Path
from typing import Any


BOUNDARY_KEYS = {
    "no_builder_audit_verdict",
    "no_builder_audit_verdict_envelope_gate",
    "no_audit_verdict",
    "no_audit_verdict_written",
    "no_audit_verdict_emitted",
    "packet_audit_verdict_absent",
    "builder_surface_no_audit_verdict",
    "file_disjoint_packet",
}


def audit_verdict_header_is_independent(audit_path: Path) -> bool:
    if not audit_path.exists():
        return True
    header = "\n".join(audit_path.read_text(encoding="utf-8").splitlines()[:40]).lower()
    return (
        "independent audit verdict" in header
        or "auditor: independent" in header
        or "independent auditor" in header
        or "independent recomputation" in header
        or "fresh audit" in header
        or "read-only audit" in header
        or "audit mode: read-only" in header
        or ("fresh" in header and "audit" in header)
    )


def builder_audit_boundary_ok(audit_path: Path) -> bool:
    return not audit_path.exists() or audit_verdict_header_is_independent(audit_path)


def find_boundary_flags(value: Any) -> list[tuple[str, Any]]:
    found: list[tuple[str, Any]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key in BOUNDARY_KEYS:
                found.append((key, item))
            found.extend(find_boundary_flags(item))
    elif isinstance(value, list):
        for item in value:
            found.extend(find_boundary_flags(item))
    return found


def builder_audit_boundary_errors(envelope: dict[str, Any], audit_path: Path) -> list[str]:
    errors: list[str] = []
    flags = find_boundary_flags(envelope)
    no_builder_flags = [value for key, value in flags if key == "no_builder_audit_verdict"]
    if "no_builder_audit_verdict" in envelope or no_builder_flags:
        if not no_builder_flags:
            errors.append("no_builder_audit_verdict field missing")
        elif not any(value is True for value in no_builder_flags):
            errors.append("no_builder_audit_verdict must be true")
    else:
        envelope.setdefault("boundary_field", "pre_convention_grandfathered")
    if not builder_audit_boundary_ok(audit_path):
        errors.append("audit_verdict.md exists but its header does not declare an independent/fresh audit")
    return errors
