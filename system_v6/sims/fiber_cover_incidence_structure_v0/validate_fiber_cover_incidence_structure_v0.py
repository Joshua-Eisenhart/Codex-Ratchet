#!/usr/bin/env python3
"""Packet-local validator for fiber_cover_incidence_structure_v0."""

from __future__ import annotations

import json
from typing import Any

import fiber_cover_incidence_structure_v0_boundary as boundary
import fiber_cover_incidence_structure_v0_common as common


CLASSIFICATION = "scratch_diagnostic"
TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "writes the validator result receipt"},
    "fiber_cover_incidence_structure_v0_boundary": {"tried": True, "used": True, "reason": "runs packet boundary checks"},
    "fiber_cover_incidence_structure_v0_common": {"tried": True, "used": True, "reason": "rebuilds packet for drift checks"},
}
TOOL_INTEGRATION_DEPTH = {
    "json": "supportive",
    "fiber_cover_incidence_structure_v0_boundary": "supportive",
    "fiber_cover_incidence_structure_v0_common": "supportive",
}
REQUIRED_PACKET_FILES = [
    "build_card.md",
    "builder_self_assessment.md",
    "fiber_cover_incidence_structure_v0.py",
    "fiber_cover_incidence_structure_v0_envelope.py",
    "fiber_cover_incidence_structure_v0_common.py",
    "fiber_cover_incidence_structure_v0_boundary.py",
    "validate_fiber_cover_incidence_structure_v0.py",
    "tests/test_fiber_cover_incidence_structure_v0.py",
]


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def load_or_build() -> dict[str, Any]:
    if common.RESULT_PATH.exists():
        return common.load_json(common.RESULT_PATH)
    return common.build_fiber_cover_incidence_structure_object()


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for rel_path in REQUIRED_PACKET_FILES:
        require(errors, (common.SIM_DIR / rel_path).is_file(), f"missing required packet file: {rel_path}")
    build_card = common.SIM_DIR / "build_card.md"
    text = build_card.read_text(encoding="utf-8") if build_card.is_file() else ""
    require(errors, common.SIM_ID in text, "build_card missing sim id")
    require(errors, "NO Betti" in text, "build_card must state NO Betti boundary")
    require(errors, "G.2a" in text, "build_card missing G.2a boundary")

    rebuilt = common.build_fiber_cover_incidence_structure_object()
    require(errors, payload.get("sim_id") == common.SIM_ID, "sim_id mismatch")
    require(errors, payload.get("classification") == common.CLASSIFICATION, "classification mismatch")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("claim_ceiling") == common.CLAIM_CEILING, "claim ceiling mismatch")
    require(errors, payload.get("source_cover") == rebuilt["source_cover"], "source cover drifted")
    require(errors, payload.get("derivation_honesty") == rebuilt["derivation_honesty"], "derivation honesty drifted")
    require(errors, payload.get("base_incidence", {}).get("chain_sha256") == rebuilt["base_incidence"]["chain_sha256"], "base chain hash drifted")
    require(
        errors,
        payload.get("total_space_incidence", {}).get("chain_sha256") == rebuilt["total_space_incidence"]["chain_sha256"],
        "total chain hash drifted",
    )
    require(errors, payload.get("TOOL_MANIFEST") == common.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, payload.get("TOOL_INTEGRATION_DEPTH") == common.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    require(errors, payload.get("all_pass") is True, "all_pass must be true for incidence packet plumbing")
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
