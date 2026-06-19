#!/usr/bin/env python3
"""Write the packet envelope for gcm_ring_checkerboard_runner_v1."""

from __future__ import annotations

import json

import gcm_ring_checkerboard_runner_v1_common as common


def main() -> int:
    payload = common.write_envelope()
    print(
        json.dumps(
            {
                "result": common.rel(common.ENVELOPE_PATH),
                "all_pass": payload["all_pass"],
                "substrate_positive_ok": payload["substrate_positive_ok"],
                "substrate_lineage_free_negative_ok": payload["substrate_lineage_free_negative_ok"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

