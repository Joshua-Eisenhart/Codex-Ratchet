#!/usr/bin/env python3
"""Run the ECD.05 instruction-machine discriminator search."""

from __future__ import annotations

import json

import ecd05_instruction_machine_v0_common as common


def main() -> int:
    common.RESULT_DIR.mkdir(parents=True, exist_ok=True)
    payload = common.build_instruction_machine_object()
    common.write_json(common.RESULT_PATH, payload)
    summary = {
        "ok": payload["all_pass"],
        "result": common.rel(common.RESULT_PATH),
        "qit_max": payload["discriminator"]["qit_max"],
        "baseline_max": payload["discriminator"]["baseline_max"],
        "margin": payload["discriminator"]["qit_minus_baseline_margin"],
        "verdict": payload["discriminator"]["verdict"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
