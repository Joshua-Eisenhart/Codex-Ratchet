#!/usr/bin/env python3
"""Write the topology_parity_guard_v3 consumer result packet."""

from __future__ import annotations

import json

import topology_parity_guard_v3_common as common


def main() -> int:
    payload = common.write_result()
    print(json.dumps({"result_path": common.rel(common.RESULT_PATH), "all_pass": payload["all_pass"]}, indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
