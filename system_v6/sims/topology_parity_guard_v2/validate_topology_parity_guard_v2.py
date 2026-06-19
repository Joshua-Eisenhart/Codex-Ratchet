#!/usr/bin/env python3
"""Packet-local validator for topology_parity_guard_v2."""

from __future__ import annotations

import json
from typing import Any

import topology_parity_guard_v2_boundary as boundary
import topology_parity_guard_v2_common as common


TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "writes the validator receipt"},
    "topology_parity_guard_v2_boundary": {"tried": True, "used": True, "reason": "runs packet boundary checks"},
    "topology_parity_guard_v2_common": {"tried": True, "used": True, "reason": "rebuilds the consumer packet for drift checks"},
}
TOOL_INTEGRATION_DEPTH = {
    "json": "supportive",
    "topology_parity_guard_v2_boundary": "load_bearing",
    "topology_parity_guard_v2_common": "load_bearing",
}
REQUIRED_PACKET_FILES = [
    "build_card.md",
    "builder_self_assessment.md",
    "topology_parity_guard_v2.py",
    "topology_parity_guard_v2_envelope.py",
    "topology_parity_guard_v2_common.py",
    "topology_parity_guard_v2_boundary.py",
    "validate_topology_parity_guard_v2.py",
    "tests/test_topology_parity_guard_v2.py",
]


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def load_or_build() -> dict[str, Any]:
    if common.RESULT_PATH.exists():
        return common.load_json(common.RESULT_PATH)
    return common.build_topology_parity_guard_v2_object()


def validate_packet_files(errors: list[str]) -> None:
    for rel_path in REQUIRED_PACKET_FILES:
        require(errors, (common.SIM_DIR / rel_path).is_file(), f"missing required packet file: {rel_path}")
    card = common.SIM_DIR / "build_card.md"
    text = card.read_text(encoding="utf-8") if card.is_file() else ""
    for phrase in (
        common.SIM_ID,
        "G.2a",
        "scratch_diagnostic",
        "target Betti fitting",
        "consumer",
        "S3-like",
        "S2xS1",
        "NO new construction",
    ):
        require(errors, phrase in text, f"build_card missing required phrase: {phrase}")


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    validate_packet_files(errors)
    rebuilt = common.build_topology_parity_guard_v2_object()
    for key in (
        "sim_id",
        "classification",
        "promotion_allowed",
        "formal_admission_allowed",
        "claim_ceiling",
        "source_complex_lock",
        "reference_gate",
        "complexes",
        "controls",
        "parity_adjudication",
        "TOOL_MANIFEST",
        "TOOL_INTEGRATION_DEPTH",
        "all_pass",
    ):
        require(errors, payload.get(key) == rebuilt.get(key), f"{key} drifted")
    require(errors, payload.get("TOOL_MANIFEST") == common.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, payload.get("TOOL_INTEGRATION_DEPTH") == common.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    require(errors, payload.get("all_pass") is True, "consumer execution gates must pass")
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
