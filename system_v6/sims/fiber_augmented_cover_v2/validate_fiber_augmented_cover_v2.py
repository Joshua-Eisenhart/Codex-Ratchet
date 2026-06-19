#!/usr/bin/env python3
"""Packet-local validator for fiber_augmented_cover_v2."""

from __future__ import annotations

import json
from typing import Any

import fiber_augmented_cover_v2_boundary as boundary
import fiber_augmented_cover_v2_common as common


TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "writes the validator result receipt"},
    "fiber_augmented_cover_v2_boundary": {"tried": True, "used": True, "reason": "runs packet boundary checks"},
    "fiber_augmented_cover_v2_common": {"tried": True, "used": True, "reason": "rebuilds packet for drift checks"},
}
TOOL_INTEGRATION_DEPTH = {
    "json": "supportive",
    "fiber_augmented_cover_v2_boundary": "supportive",
    "fiber_augmented_cover_v2_common": "supportive",
}
REQUIRED_PACKET_FILES = [
    "build_card.md",
    "builder_self_assessment.md",
    "fiber_augmented_cover_v2.py",
    "fiber_augmented_cover_v2_envelope.py",
    "fiber_augmented_cover_v2_common.py",
    "fiber_augmented_cover_v2_boundary.py",
    "validate_fiber_augmented_cover_v2.py",
    "tests/test_fiber_augmented_cover_v2.py",
]


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def load_or_build() -> dict[str, Any]:
    if common.RESULT_PATH.exists():
        return common.load_json(common.RESULT_PATH)
    return common.build_fiber_augmented_cover_v2_object()


def validate_packet_files(errors: list[str]) -> None:
    for rel_path in REQUIRED_PACKET_FILES:
        require(errors, (common.SIM_DIR / rel_path).is_file(), f"missing required packet file: {rel_path}")
    card = common.SIM_DIR / "build_card.md"
    text = card.read_text(encoding="utf-8") if card.is_file() else ""
    for phrase in ("fiber_augmented_cover_v2", "G.2a", "NO Betti", "dense graph", "cellular sphere"):
        require(errors, phrase in text, f"build_card missing required phrase: {phrase}")


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    validate_packet_files(errors)
    rebuilt = common.build_fiber_augmented_cover_v2_object()
    require(errors, payload.get("schema") == common.SCHEMA, "schema mismatch")
    require(errors, payload.get("sim_id") == common.SIM_ID, "sim_id mismatch")
    require(errors, payload.get("classification") == common.CLASSIFICATION, "classification mismatch")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("claim_ceiling") == common.CLAIM_CEILING, "claim ceiling mismatch")
    require(errors, payload.get("cellular_base", {}).get("chain_sha256") == rebuilt["cellular_base"]["chain_sha256"], "cellular base chain hash drifted")
    require(errors, payload.get("cover", {}).get("cover_sha256") == rebuilt["cover"]["cover_sha256"], "cover hash drifted")
    require(
        errors,
        payload.get("total_space_cellular_structure", {}).get("chain_sha256") == rebuilt["total_space_cellular_structure"]["chain_sha256"],
        "total-space chain hash drifted",
    )
    require(errors, payload.get("relation_sign_vector_sha256") == rebuilt["relation_sign_vector_sha256"], "relation sign vector hash drifted")
    require(errors, payload.get("TOOL_MANIFEST") == common.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, payload.get("TOOL_INTEGRATION_DEPTH") == common.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    require(errors, payload.get("all_pass") is True, "all_pass must be true")
    require(errors, payload.get("betti_computed") is False, "Betti must not be computed")
    require(errors, "betti" not in payload, "top-level betti field is forbidden")
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
