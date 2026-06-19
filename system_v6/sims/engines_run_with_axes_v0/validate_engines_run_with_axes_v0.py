#!/usr/bin/env python3
"""Packet-local validator for engines_run_with_axes_v0."""

from __future__ import annotations

import json

import engines_run_with_axes_v0_common as common


def main() -> int:
    payload = json.loads(common.RESULT_PATH.read_text(encoding="utf-8"))
    errors = common.validate_payload(payload)
    result = {
        "ok": not errors,
        "result_json": common.rel(common.RESULT_PATH),
        "errors": errors,
        "validator": common.rel(common.SIM_DIR / "validate_engines_run_with_axes_v0.py"),
    }
    common.write_json(common.VALIDATOR_RESULT, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
