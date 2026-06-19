#!/usr/bin/env python3
"""Build the standard three-engine envelope for the 6Q carve packet."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from gcm_constraint_carve_6q_v0_common import ENVELOPE_PATH, rel, write_json
from write_envelope_spec import build_spec

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from build_three_engine_envelope import build_envelope  # noqa: E402

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
TOOL_MANIFEST = {
    "build_three_engine_envelope": {"tried": True, "used": True, "reason": "standard three-engine envelope assembly for the 6Q carve packet"},
    "python_stdlib": {"tried": True, "used": True, "reason": "JSON, path, and result writing support"},
}
TOOL_INTEGRATION_DEPTH = {
    "build_three_engine_envelope": "load_bearing",
    "python_stdlib": "supportive",
}


def main() -> int:
    envelope = build_envelope(**build_spec())
    write_json(ENVELOPE_PATH, envelope)
    print(json.dumps({"ok": True, "result": rel(ENVELOPE_PATH)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
