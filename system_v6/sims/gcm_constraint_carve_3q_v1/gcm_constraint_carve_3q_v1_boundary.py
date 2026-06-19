#!/usr/bin/env python3
"""Builder/audit boundary surface for gcm_constraint_carve_3q_v1."""

from __future__ import annotations

import json

from gcm_constraint_carve_3q_v1_common import SIM_DIR
from builder_audit_boundary import builder_audit_boundary_errors, builder_audit_boundary_ok


def boundary_payload() -> dict[str, object]:
    payload = {
        "sim_id": "gcm_constraint_carve_3q_v1",
        "file_disjoint_packet": True,
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
    }
    return {
        **payload,
        "builder_audit_boundary_ok": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
        "errors": builder_audit_boundary_errors(dict(payload), SIM_DIR / "audit_verdict.md"),
    }


def main() -> int:
    payload = boundary_payload()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["builder_audit_boundary_ok"] and not payload["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
