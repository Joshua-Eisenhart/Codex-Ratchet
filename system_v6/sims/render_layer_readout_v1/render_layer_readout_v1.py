#!/usr/bin/env python3
"""Build the render_layer_readout_v1 core result."""

from __future__ import annotations

import json

import render_layer_readout_v1_common as common


classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
TOOL_MANIFEST = {
    "render_layer_readout_v1_common": {"tried": True, "used": True, "reason": "builds the bounded v1 core payload"},
    "json": {"tried": True, "used": True, "reason": "prints the build receipt"},
}
TOOL_INTEGRATION_DEPTH = {"render_layer_readout_v1_common": "supportive", "json": "supportive"}


def main() -> int:
    result = common.build_core()
    common.write_json(common.RESULT_PATH, result)
    print(json.dumps({"result_path": common.rel(common.RESULT_PATH), "all_pass": result["all_pass"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
