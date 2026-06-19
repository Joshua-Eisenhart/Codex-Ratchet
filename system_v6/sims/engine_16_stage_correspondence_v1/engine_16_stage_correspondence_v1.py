#!/usr/bin/env python3
"""Build the primary engine_16_stage_correspondence_v1 packet."""

from __future__ import annotations

import json

import engine_16_stage_correspondence_v1_common as common


def main() -> int:
    payload = common.build_packet()
    common.write_json(common.RESULT_PATH, payload)
    common.write_lineage_free_negative(
        {
            "sim_id": common.SIM_ID,
            "classification": common.CLASSIFICATION,
            "note": "intentional lineage-free negative control; scripts/gcm_substrate_check.py must reject this file",
        }
    )
    print(
        json.dumps(
            {
                "ok": payload["all_pass"],
                "result": common.rel(common.RESULT_PATH),
                "lineage_free_negative": common.rel(common.LINEAGE_FREE_NEGATIVE_PATH),
                "correspondence_verdict": payload["summary"]["correspondence_verdict"],
                "exact_matched_component_count": payload["summary"]["exact_matched_component_count"],
                "defined_distinct_component_count": payload["summary"]["defined_distinct_component_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
