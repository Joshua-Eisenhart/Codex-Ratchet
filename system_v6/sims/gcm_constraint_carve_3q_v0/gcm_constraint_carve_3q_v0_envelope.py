#!/usr/bin/env python3
"""Three-lane envelope for gcm_constraint_carve_3q_v0."""

from __future__ import annotations

import json
import sys

import gcm_constraint_carve_3q_v0_common as common
import write_envelope_spec


CLASSIFICATION = common.CLASSIFICATION
TOOL_MANIFEST = common.TOOL_MANIFEST
TOOL_INTEGRATION_DEPTH = common.TOOL_INTEGRATION_DEPTH

if str(common.SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(common.SCRIPTS_DIR))

from build_three_engine_envelope import build_envelope  # noqa: E402


def build_result() -> dict:
    spec = write_envelope_spec.build_spec()
    payload = build_envelope(**spec)
    common.write_json(common.ENVELOPE_PATH, payload)
    return payload


def main() -> int:
    payload = build_result()
    ok = bool(payload.get("all_pass"))
    print(json.dumps({"ok": ok, "result": common.rel(common.ENVELOPE_PATH)}, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
