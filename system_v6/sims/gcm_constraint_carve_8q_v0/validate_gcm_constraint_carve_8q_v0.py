#!/usr/bin/env python3
"""Validate the LEAN state-fingerprinted 8Q GCM constraint carve packet."""

from __future__ import annotations

import json
from pathlib import Path

from gcm_constraint_carve_8q_v0_common import (
    RESULT_DIR,
    RESULT_PATH,
    SAMPLE_PATH,
    SIM_DIR,
    SIM_ID,
    VALIDATOR_RESULT_PATH,
    directory_size_bytes,
    load_json,
    rel,
    validate_payload,
    write_json,
)

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
TOOL_MANIFEST = {
    "python_stdlib": {"tried": True, "used": True, "reason": "JSON/path validation and validator-result writing"},
}
TOOL_INTEGRATION_DEPTH = {"python_stdlib": "supportive"}


def main() -> int:
    errors: list[str] = []
    if not RESULT_PATH.exists():
        errors.append("missing main result")
        packet = {}
    else:
        packet = load_json(RESULT_PATH)
    if not SAMPLE_PATH.exists():
        errors.append("missing sample matrix result")
        sample = {}
    else:
        sample = load_json(SAMPLE_PATH)
    if packet and sample:
        errors.extend(validate_payload(packet, sample, require_helper_preflight=True))
    oversize_files = [rel(path) for path in SIM_DIR.rglob("*") if path.is_file() and path.stat().st_size > 50_000_000]
    dir_size = directory_size_bytes(SIM_DIR)
    if oversize_files:
        errors.append("file over 50MB found")
    if dir_size >= 50_000_000:
        errors.append("packet directory exceeds 50MB wall")
    payload = {
        "ok": not errors,
        "sim_id": SIM_ID,
        "result_path": rel(RESULT_PATH),
        "sample_path": rel(SAMPLE_PATH),
        "result_size_bytes": RESULT_PATH.stat().st_size if RESULT_PATH.exists() else None,
        "sample_size_bytes": SAMPLE_PATH.stat().st_size if SAMPLE_PATH.exists() else None,
        "dir_size_bytes": dir_size,
        "du_sh_command": f"du -sh {rel(SIM_DIR)}",
        "oversize_check_command": f"find {rel(SIM_DIR)} -type f -size +50M -print",
        "oversize_files_over_50mb": oversize_files,
        "errors": errors,
    }
    write_json(VALIDATOR_RESULT_PATH, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
