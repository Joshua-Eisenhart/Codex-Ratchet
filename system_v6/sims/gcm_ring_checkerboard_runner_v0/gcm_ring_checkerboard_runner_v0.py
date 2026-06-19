#!/usr/bin/env python3
"""Run the GCM ring-checkerboard runner v0 packet."""

from __future__ import annotations

import json

import gcm_ring_checkerboard_runner_v0_common as common


def main() -> int:
    payload = common.write_result()
    print(
        json.dumps(
            {
                "result": common.rel(common.RESULT_PATH),
                "all_pass": payload["all_pass"],
                "gcm_object_id": payload["gcm_object_id"],
                "alternating_period_spectrum": payload["dynamics"]["alternating_AB"]["periods"]["spectrum"],
                "paired_period_spectrum": payload["dynamics"]["paired_AABB"]["periods"]["spectrum"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

