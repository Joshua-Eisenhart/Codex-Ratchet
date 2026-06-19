#!/usr/bin/env python3
"""Write the topology_parity_cell_model_v1 scratch result."""

from __future__ import annotations

import json

import topology_parity_cell_model_v1_common as common


CLASSIFICATION = "scratch_diagnostic"
TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "prints the result write receipt"},
    "topology_parity_cell_model_v1_common": {"tried": True, "used": True, "reason": "delegates construction to the packet common module"},
}
TOOL_INTEGRATION_DEPTH = {
    "json": "supportive",
    "topology_parity_cell_model_v1_common": "supportive",
}


def main() -> int:
    payload = common.write_result()
    print(
        json.dumps(
            {
                "ok": True,
                "result_path": common.rel(common.RESULT_PATH),
                "guard_status": payload["parity_adjudication"]["guard_status"],
                "independent_guard_earned": payload["result_summary"]["independent_guard_earned"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
