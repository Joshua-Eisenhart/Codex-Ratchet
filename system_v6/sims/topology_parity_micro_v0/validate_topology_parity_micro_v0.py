#!/usr/bin/env python3
"""Packet-local validator for topology_parity_micro_v0."""

from __future__ import annotations

import json
from typing import Any

import topology_parity_micro_v0_boundary as boundary
import topology_parity_micro_v0_common as common


CLASSIFICATION = "scratch_diagnostic"
TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "writes the validator result receipt"},
    "topology_parity_micro_v0_boundary": {"tried": True, "used": True, "reason": "runs packet boundary checks"},
    "topology_parity_micro_v0_common": {"tried": True, "used": True, "reason": "rebuilds the packet for drift checks"},
}
TOOL_INTEGRATION_DEPTH = {
    "json": "supportive",
    "topology_parity_micro_v0_boundary": "supportive",
    "topology_parity_micro_v0_common": "supportive",
}
REQUIRED_PACKET_FILES = [
    "build_card.md",
    "builder_self_assessment.md",
    "topology_parity_micro_v0.py",
    "topology_parity_micro_v0_envelope.py",
    "topology_parity_micro_v0_common.py",
    "topology_parity_micro_v0_boundary.py",
    "validate_topology_parity_micro_v0.py",
    "tests/test_topology_parity_micro_v0.py",
]


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def load_or_build() -> dict[str, Any]:
    if common.RESULT_PATH.exists():
        return common.load_json(common.RESULT_PATH)
    return common.build_topology_parity_object()


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for rel_path in REQUIRED_PACKET_FILES:
        require(errors, (common.SIM_DIR / rel_path).is_file(), f"missing required packet file: {rel_path}")

    build_card = common.SIM_DIR / "build_card.md"
    text = build_card.read_text(encoding="utf-8") if build_card.is_file() else ""
    require(errors, common.SIM_ID in text, "build_card missing sim id")
    require(errors, "G.2a" in text, "build_card missing G.2a boundary")
    require(errors, "S3-like" in text and "S2xS1" in text, "build_card missing preregistered topology profiles")

    rebuilt = common.build_topology_parity_object()
    require(errors, payload.get("sim_id") == common.SIM_ID, "sim_id mismatch")
    require(errors, payload.get("complexes") == rebuilt["complexes"], "complex analysis drifted")
    require(errors, payload.get("controls") == rebuilt["controls"], "controls drifted")
    require(errors, payload.get("parity_adjudication") == rebuilt["parity_adjudication"], "parity adjudication drifted")
    require(errors, payload.get("TOOL_MANIFEST") == common.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, payload.get("TOOL_INTEGRATION_DEPTH") == common.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    require(errors, payload.get("all_pass") is True, "all_pass must be true for packet execution")
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
