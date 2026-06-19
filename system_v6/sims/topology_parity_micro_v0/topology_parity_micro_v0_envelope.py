#!/usr/bin/env python3
"""Write the topology_parity_micro_v0 envelope result."""

from __future__ import annotations

import json

import topology_parity_micro_v0_common as common


CLASSIFICATION = "scratch_diagnostic"
TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "prints the envelope write receipt"},
    "topology_parity_micro_v0_common": {"tried": True, "used": True, "reason": "delegates envelope construction to the packet common module"},
}
TOOL_INTEGRATION_DEPTH = {
    "json": "supportive",
    "topology_parity_micro_v0_common": "supportive",
}


def main() -> int:
    payload = common.write_envelope()
    print(json.dumps({"ok": True, "envelope_path": common.rel(common.ENVELOPE_RESULT_PATH), "all_pass": payload["all_pass"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
