#!/usr/bin/env python3
"""Validate the state-artifacted 4Q GCM constraint carve packet."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from gcm_constraint_carve_4q_v0_common import (
    ENVELOPE_PATH,
    EXPECTED_QUOTIENT_CLASS_COUNT,
    EXPECTED_SURVIVOR_COUNT,
    RESULT_DIR,
    SIM_ID,
    VALIDATOR_RESULT_PATH,
    load_json,
    rel,
    validate_payload,
    write_json,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from validate_three_engine_sim_result import validate as validate_three_engine  # noqa: E402


def main() -> int:
    errors: list[str] = []
    result_path = RESULT_DIR / f"{SIM_ID}_results.json"
    packet = load_json(result_path)
    errors.extend(validate_payload(packet, require_helper_preflight=True))
    for name in ("julia", "jax", "pytorch"):
        lane_path = RESULT_DIR / f"{SIM_ID}_{name}_results.json"
        if not lane_path.exists():
            errors.append(f"missing {name} result")
            continue
        lane = load_json(lane_path)
        if lane.get("all_pass") is not True:
            errors.append(f"{name} lane all_pass false")
        if lane.get("survivor_count") != EXPECTED_SURVIVOR_COUNT or lane.get("quotient_class_count") != EXPECTED_QUOTIENT_CLASS_COUNT:
            errors.append(f"{name} lane count mismatch")
    if not ENVELOPE_PATH.exists():
        errors.append("missing envelope result")
    else:
        envelope = load_json(ENVELOPE_PATH)
        errors.extend(
            validate_three_engine(
                envelope,
                require_pytorch=True,
                strict_source_backed=True,
                require_tool_intent=True,
            )
        )
    payload = {
        "ok": not errors,
        "sim_id": SIM_ID,
        "result_path": rel(result_path),
        "envelope_path": rel(ENVELOPE_PATH),
        "errors": errors,
    }
    write_json(VALIDATOR_RESULT_PATH, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
