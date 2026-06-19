#!/usr/bin/env python3
"""Build the standard three-engine envelope."""

from __future__ import annotations

import json
import sys

from gcm_constraint_carve_3q_v1_common import ENVELOPE_PATH, rel, write_json
from write_envelope_spec import build_spec

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3] / "scripts"))
from build_three_engine_envelope import build_envelope  # noqa: E402


def main() -> int:
    envelope = build_envelope(**build_spec())
    write_json(ENVELOPE_PATH, envelope)
    print(json.dumps({"ok": True, "result": rel(ENVELOPE_PATH)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
