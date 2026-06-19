#!/usr/bin/env python3
"""Write engines_run_with_axes_v0 result JSON."""

from __future__ import annotations

import json

import engines_run_with_axes_v0_common as common


def main() -> int:
    payload = common.build_packet()
    common.write_json(common.RESULT_PATH, payload)
    print(json.dumps({"ok": payload["all_pass"], "result": common.rel(common.RESULT_PATH)}, indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
