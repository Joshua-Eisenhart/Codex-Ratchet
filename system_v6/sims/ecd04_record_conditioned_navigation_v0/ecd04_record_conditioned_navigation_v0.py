#!/usr/bin/env python3
"""Run the ECD.04 record-conditioned navigation discriminator."""

from __future__ import annotations

import json

import ecd04_record_conditioned_navigation_v0_common as common


def main() -> int:
    payload = common.build_navigation_object()
    common.write_json(common.RESULT_PATH, payload)
    print(
        json.dumps(
            {
                "ok": payload["all_pass"],
                "result": common.rel(common.RESULT_PATH),
                "verdict": payload["discriminator"]["verdict"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
