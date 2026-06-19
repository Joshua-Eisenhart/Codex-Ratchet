#!/usr/bin/env python3
"""Write the fiber_augmented_cover_v1 scratch result."""

from __future__ import annotations

import json

import fiber_augmented_cover_v1_common as common


CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "prints the packet write receipt"},
    "fiber_augmented_cover_v1_common": {"tried": True, "used": True, "reason": "delegates construction to the packet common module"},
}
TOOL_INTEGRATION_DEPTH = {
    "json": "supportive",
    "fiber_augmented_cover_v1_common": "supportive",
}


def main() -> int:
    common.write_result()
    print(json.dumps({"ok": True, "result_path": common.rel(common.RESULT_PATH)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
