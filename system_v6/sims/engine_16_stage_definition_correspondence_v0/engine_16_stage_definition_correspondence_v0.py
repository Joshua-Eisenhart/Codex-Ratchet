#!/usr/bin/env python3
"""Build engine_16_stage_definition_correspondence_v0."""

from __future__ import annotations

import json

import engine_16_stage_definition_correspondence_v0_common as common


def main() -> int:
    payload = common.build_and_write()
    print(
        json.dumps(
            {
                "ok": payload["all_pass"],
                "result": common.rel(common.RESULT_PATH),
                "correspondence_result": payload["summary"]["correspondence_result"],
                "defined_distinct": payload["summary"]["defined_distinct_component_count"],
                "exact_matches": payload["summary"]["exact_matched_component_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
