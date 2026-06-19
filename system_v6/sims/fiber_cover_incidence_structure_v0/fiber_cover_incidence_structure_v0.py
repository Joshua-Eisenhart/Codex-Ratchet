#!/usr/bin/env python3
"""Write the fiber_cover_incidence_structure_v0 scratch result."""

from __future__ import annotations

import json

import fiber_cover_incidence_structure_v0_common as common


CLASSIFICATION = "scratch_diagnostic"
TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "prints the packet write receipt"},
    "fiber_cover_incidence_structure_v0_common": {"tried": True, "used": True, "reason": "delegates construction to packet common module"},
}
TOOL_INTEGRATION_DEPTH = {
    "json": "supportive",
    "fiber_cover_incidence_structure_v0_common": "supportive",
}


def main() -> int:
    payload = common.write_result()
    print(
        json.dumps(
            {
                "ok": bool(payload["all_pass"]),
                "result_path": common.rel(common.RESULT_PATH),
                "betti_computed": payload["betti_computed"],
                "betti_lane_status": payload["betti_lane_status"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
