#!/usr/bin/env python3
"""Write the three-engine envelope for gcm_nesting_tower_le2q_v0."""

from __future__ import annotations

import json

import gcm_nesting_tower_le2q_v0_common as common


def main() -> int:
    envelope = common.build_envelope(write=True)
    print(
        json.dumps(
            {
                "ok": envelope["all_pass"],
                "result": common.rel(common.ENVELOPE_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if envelope["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
