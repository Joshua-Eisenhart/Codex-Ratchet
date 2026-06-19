#!/usr/bin/env python3
"""Write the fiber_augmented_cover_v2_1 envelope result."""

from __future__ import annotations

import json

import fiber_augmented_cover_v2_1_common as common


def main() -> int:
    payload = common.write_envelope_result()
    print(json.dumps({"result": common.rel(common.ENVELOPE_RESULT_PATH), "all_pass": payload["all_pass"]}, indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
