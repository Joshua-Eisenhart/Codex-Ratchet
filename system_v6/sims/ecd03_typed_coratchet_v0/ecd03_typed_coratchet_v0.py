#!/usr/bin/env python3
"""Run the ECD.03 typed co-ratchet discriminator."""

from __future__ import annotations

import json

import ecd03_typed_coratchet_v0_common as common


def main() -> int:
    common.RESULT_DIR.mkdir(parents=True, exist_ok=True)
    payload = common.build_typed_coratchet_object()
    common.write_json(common.RESULT_PATH, payload)
    summary = {
        "ok": payload["all_pass"],
        "result": common.rel(common.RESULT_PATH),
        "verdict": payload["discriminator"]["verdict"],
        "qit_sequences": payload["qit_side"]["computed_sequence_count"],
        "baseline_sequences": payload["baseline_side"]["computed_sequence_count"],
        "qit_only": payload["discriminator"]["qit_only_sequences_count"],
        "baseline_only": payload["discriminator"]["baseline_only_sequences_count"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
