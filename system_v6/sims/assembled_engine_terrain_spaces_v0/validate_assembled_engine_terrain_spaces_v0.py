#!/usr/bin/env python3
"""Packet-local validator for assembled_engine_terrain_spaces_v0."""

from __future__ import annotations

import json
from typing import Any

import assembled_engine_terrain_spaces_v0_boundary as boundary
import assembled_engine_terrain_spaces_v0_common as common


TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "writes the validator receipt"},
    "assembled_engine_terrain_spaces_v0_boundary": {"tried": True, "used": True, "reason": "runs packet boundary checks"},
    "assembled_engine_terrain_spaces_v0_common": {"tried": True, "used": True, "reason": "rebuilds terrain-space packet for drift checks"},
}
TOOL_INTEGRATION_DEPTH = {
    "json": "supportive",
    "assembled_engine_terrain_spaces_v0_boundary": "load_bearing",
    "assembled_engine_terrain_spaces_v0_common": "load_bearing",
}
REQUIRED_PACKET_FILES = [
    "build_card.md",
    "builder_self_assessment.md",
    "assembled_engine_terrain_spaces_v0.py",
    "assembled_engine_terrain_spaces_v0_jax.py",
    "assembled_engine_terrain_spaces_v0_pytorch.py",
    "assembled_engine_terrain_spaces_v0_julia.jl",
    "assembled_engine_terrain_spaces_v0_envelope.py",
    "assembled_engine_terrain_spaces_v0_common.py",
    "assembled_engine_terrain_spaces_v0_boundary.py",
    "validate_assembled_engine_terrain_spaces_v0.py",
    "tests/test_assembled_engine_terrain_spaces_v0.py",
]


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def load_or_build() -> dict[str, Any]:
    if common.RESULT_PATH.exists():
        return common.load_json(common.RESULT_PATH)
    return common.build_assembled_engine_terrain_spaces_v0_object()


def validate_packet_files(errors: list[str]) -> None:
    for rel_path in REQUIRED_PACKET_FILES:
        require(errors, (common.SIM_DIR / rel_path).is_file(), f"missing required packet file: {rel_path}")
    card = common.SIM_DIR / "build_card.md"
    text = card.read_text(encoding="utf-8") if card.is_file() else ""
    for phrase in (
        common.SIM_ID,
        "G.2a",
        "scratch_diagnostic",
        "terrain spaces",
        "not the terrains simmed",
        "Topology4 = Se/Ne/Ni/Si",
        "owner may override",
    ):
        require(errors, phrase in text, f"build_card missing required phrase: {phrase}")


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    validate_packet_files(errors)
    rebuilt = common.build_assembled_engine_terrain_spaces_v0_object()
    for key in (
        "schema",
        "sim_id",
        "object_id",
        "classification",
        "promotion_allowed",
        "formal_admission_allowed",
        "claim_ceiling",
        "component_boundary",
        "stage_movement_allowed",
        "source_reuse_lineage",
        "parent_lineage",
        "terrain_spaces",
        "cross_terrain_distinctness",
        "design_conformance",
        "builder_gates",
        "three_engine_scope",
        "TOOL_MANIFEST",
        "TOOL_INTEGRATION_DEPTH",
        "no_builder_audit_verdict",
        "no_builder_audit_verdict_envelope_gate",
        "disallowed_claims",
        "all_pass",
    ):
        require(errors, payload.get(key) == rebuilt.get(key), f"{key} drifted")
    require(errors, payload.get("TOOL_MANIFEST") == common.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, payload.get("TOOL_INTEGRATION_DEPTH") == common.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    require(errors, payload.get("all_pass") is True, "all_pass must be true")
    errors.extend(boundary.boundary_errors(payload, common.SIM_DIR))
    return errors


def main() -> int:
    payload = load_or_build()
    errors = validate_payload(payload)
    result = {
        "ok": not errors,
        "result_json": common.rel(common.RESULT_PATH),
        "errors": errors,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }
    common.write_json(common.VALIDATOR_RESULT_PATH, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
