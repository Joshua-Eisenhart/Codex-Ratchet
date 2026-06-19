#!/usr/bin/env python3
"""Write the assembled_engine_terrain_spaces_v0 envelope."""

from __future__ import annotations

import json

import assembled_engine_terrain_spaces_v0_common as common


def main() -> int:
    envelope = common.build_envelope()
    print(json.dumps({"envelope_path": common.rel(common.ENVELOPE_RESULT_PATH), "all_pass": envelope["all_pass"]}, indent=2, sort_keys=True))
    return 0 if envelope["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

