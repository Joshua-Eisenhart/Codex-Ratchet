#!/usr/bin/env python3
"""Write the ECD.03 result envelope."""

from __future__ import annotations

import json

import ecd03_typed_coratchet_v0_common as common


def main() -> int:
    if not common.RESULT_PATH.exists():
        payload = common.build_typed_coratchet_object()
        common.write_json(common.RESULT_PATH, payload)
    base = common.load_json(common.RESULT_PATH)
    envelope = common.build_envelope(base)
    common.write_json(common.ENVELOPE_PATH, envelope)
    print(
        json.dumps(
            {
                "ok": envelope["all_pass"],
                "result": common.rel(common.ENVELOPE_PATH),
                "verdict": envelope["discriminator"]["verdict"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if envelope["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
