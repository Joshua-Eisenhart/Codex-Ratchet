#!/usr/bin/env python3
"""Validate the gcm_runtime_flux_3q_v0 scratch diagnostic packet."""

from __future__ import annotations

import json

import gcm_runtime_flux_3q_v0_common as common
from builder_audit_boundary import builder_audit_boundary_errors


def main() -> int:
    payload = common.load_json(common.RESULT_PATH) if common.RESULT_PATH.exists() else common.build_packet(write=True)
    errors = common.validation_errors(payload)
    errors.extend(builder_audit_boundary_errors(payload, common.SIM_DIR / "audit_verdict.md"))
    envelope_ok = common.ENVELOPE_PATH.exists()
    if not envelope_ok:
        errors.append("envelope result missing")
    out = {
        "ok": not errors,
        "errors": errors,
        "result_path": common.rel(common.RESULT_PATH),
        "envelope_path": common.rel(common.ENVELOPE_PATH),
        "classification": payload.get("classification"),
        "claim_ceiling": payload.get("claim_ceiling"),
    }
    common.write_json(common.VALIDATOR_RESULT_PATH, out)
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
