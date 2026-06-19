#!/usr/bin/env python3
"""Write the topology_parity_cell_model_v1 envelope result."""

from __future__ import annotations

import json

import topology_parity_cell_model_v1_common as common


CLASSIFICATION = "scratch_diagnostic"
TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "prints the envelope write receipt"},
    "topology_parity_cell_model_v1_common": {"tried": True, "used": True, "reason": "delegates envelope construction to the common module"},
}
TOOL_INTEGRATION_DEPTH = {
    "json": "supportive",
    "topology_parity_cell_model_v1_common": "supportive",
}


def main() -> int:
    envelope = common.write_envelope()
    print(
        json.dumps(
            {
                "ok": True,
                "result_path": common.rel(common.ENVELOPE_RESULT_PATH),
                "guard_status": envelope["parity_adjudication"]["guard_status"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
