#!/usr/bin/env python3
"""Packet-local validator for fiber_augmented_cover_v0."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import fiber_augmented_cover_v0_boundary as boundary
import fiber_augmented_cover_v0_common as common


REQUIRED_PACKET_FILES = [
    "build_card.md",
    "fiber_augmented_cover_v0.py",
    "fiber_augmented_cover_v0_common.py",
    "fiber_augmented_cover_v0_boundary.py",
    "validate_fiber_augmented_cover_v0.py",
    "tests/test_fiber_augmented_cover_v0.py",
]


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def load_or_build() -> dict[str, Any]:
    if common.RESULT_PATH.exists():
        return common.load_json(common.RESULT_PATH)
    return common.build_fiber_augmented_cover_object()


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for rel_path in REQUIRED_PACKET_FILES:
        require(errors, (common.SIM_DIR / rel_path).is_file(), f"missing required packet file: {rel_path}")
    build_card = common.SIM_DIR / "build_card.md"
    text = build_card.read_text(encoding="utf-8") if build_card.is_file() else ""
    require(errors, common.SIM_ID in text, "build_card missing sim id")
    require(errors, "fiber-augmented 33-cell cover" in text, "build_card missing object name")

    rebuilt = common.build_fiber_augmented_cover_object()
    require(errors, payload.get("sim_id") == common.SIM_ID, "sim_id mismatch")
    require(errors, payload.get("state_object_id") == rebuilt["state_object_id"], "state_object_id mismatch")
    require(errors, payload.get("cover", {}).get("cover_state_count") == 132, "cover state count mismatch")
    require(errors, payload.get("quotient_projection") == rebuilt["quotient_projection"], "quotient projection drifted")
    require(errors, payload.get("faithfulness") == rebuilt["faithfulness"], "faithfulness drifted")
    require(errors, payload.get("b6_law_test") == rebuilt["b6_law_test"], "b6 law summary drifted")
    require(errors, payload.get("relation_sign_vector_sha256") == rebuilt["relation_sign_vector_sha256"], "sign vector hash drifted")
    require(errors, payload.get("controls") == rebuilt["controls"], "controls drifted")
    require(errors, payload.get("TOOL_MANIFEST") == common.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, payload.get("TOOL_INTEGRATION_DEPTH") == common.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    require(errors, payload.get("all_pass") is True, "all_pass must be true for packet execution even if law fails")
    errors.extend(boundary.boundary_errors(payload, common.SIM_DIR))
    return errors


def main() -> int:
    payload = load_or_build()
    errors = validate_payload(payload)
    result = {"ok": not errors, "result_json": common.rel(common.RESULT_PATH), "errors": errors}
    common.write_json(common.VALIDATOR_RESULT_PATH, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
