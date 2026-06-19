#!/usr/bin/env python3
"""Packet-local validator for gcm_constraint_carve_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import gcm_constraint_carve_v0_boundary as boundary
import gcm_constraint_carve_v0_common as common


ROOT = common.ROOT
SIM_DIR = common.SIM_DIR
RESULT_DIR = common.RESULT_DIR
ENVELOPE = common.ENVELOPE_PATH
VALIDATOR_RESULT = common.VALIDATOR_RESULT_PATH

sys.path.insert(0, str(ROOT / "scripts"))
from validate_three_engine_sim_result import validate as validate_three_engine  # noqa: E402


REQUIRED_PACKET_FILES = [
    "build_card.md",
    f"{common.SIM_ID}_common.py",
    f"{common.SIM_ID}_boundary.py",
    f"{common.SIM_ID}_julia.jl",
    f"{common.SIM_ID}_jax.py",
    f"{common.SIM_ID}_pytorch.py",
    "write_envelope_spec.py",
    f"validate_{common.SIM_ID}.py",
    "builder_self_assessment.md",
    f"tests/test_{common.SIM_ID}.py",
]


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_packet_files(errors: list[str]) -> None:
    for rel_path in REQUIRED_PACKET_FILES:
        require(errors, (SIM_DIR / rel_path).is_file(), f"missing required packet file: {rel_path}")
    card = SIM_DIR / "build_card.md"
    text = card.read_text(encoding="utf-8") if card.exists() else ""
    for required in (
        common.SIM_ID,
        "M(C) = {x : x admissible under C}",
        "G.2a idempotency-from-birth",
        "scripts/builder_audit_boundary.py",
        "scratch_diagnostic",
        "not THE manifold",
        "NO git add/commit",
    ):
        require(errors, required in text, f"build_card.md missing {required}")


def validate_common_result(errors: list[str], packet: dict[str, Any]) -> None:
    errors.extend(f"common packet: {err}" for err in common.validate_payload(packet))
    errors.extend(f"boundary: {err}" for err in boundary.boundary_errors(packet))
    require(errors, packet.get("schema") == "gcm_constraint_carve_v0_result_v1", "common schema mismatch")
    require(errors, packet.get("survivor_count") == common.EXPECTED_SURVIVOR_COUNT, "survivor_count mismatch")
    require(errors, packet.get("quotient", {}).get("class_count") == common.EXPECTED_QUOTIENT_CLASS_COUNT, "quotient class count mismatch")
    require(errors, len(packet.get("kill_ledger", [])) == common.EXPECTED_CANDIDATE_COUNT - common.EXPECTED_SURVIVOR_COUNT, "kill ledger size mismatch")
    require(errors, all(row.get("bite") is True for row in packet.get("controls", {}).get("constraint_erasure", [])), "not every constraint erasure bites")
    require(errors, packet.get("existence_tests", {}).get("stable") is True, "stability existence probe failed")
    require(errors, packet.get("existence_tests", {}).get("independent") is True, "independence existence probe failed")
    require(errors, packet.get("existence_tests", {}).get("chart_recoverable") is True, "chart recovery failed")
    require(errors, packet.get("existence_tests", {}).get("negative_controlled") is True, "negative controls failed")
    require(errors, packet.get("terrain_question", {}).get("answer") == "partial_macro_match_not_full_atlas", "terrain answer drift")
    require(errors, packet.get("M_C_t_hook", {}).get("survivor_count") == 4, "M(C,t) survivor count drift")


def validate_envelope(errors: list[str], payload: dict[str, Any]) -> None:
    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, payload.get("schema") == "gcm_constraint_carve_v0_envelope_v1", "packet envelope schema mismatch")
    require(errors, payload.get("sim_id") == common.SIM_ID, "sim_id mismatch")
    require(errors, payload.get("mode") == common.ENGINE_MODE, "engine mode mismatch")
    require(errors, payload.get("classification") == common.CLASSIFICATION, "classification mismatch")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("claim_ceiling") == common.CLAIM_CEILING, "claim ceiling mismatch")
    require(errors, payload.get("carrier_and_pins_relative") is True, "carrier_and_pins_relative flag missing")
    require(errors, payload.get("not_THE_manifold") is True, "not_THE_manifold flag missing")
    require(errors, payload.get("all_pass") is True, "top-level all_pass false")
    require(errors, set(payload.get("engine_lanes", [])) == {"julia", "jax", "pytorch"}, "engine_lanes mismatch")
    require(errors, set(payload.get("engines", {})) == {"julia", "jax", "pytorch"}, "engines mismatch")
    consensus = payload.get("engine_consensus", {})
    for key in (
        "all_engine_lanes_pass",
        "survivor_count_agreement",
        "quotient_class_count_agreement",
        "component_count_agreement",
    ):
        require(errors, consensus.get(key) is True, f"engine consensus failed: {key}")
    require(errors, payload.get("TOOL_MANIFEST") == common.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, payload.get("TOOL_INTEGRATION_DEPTH") == common.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    require(errors, payload.get("tool_intent") == common.TOOL_INTENT, "tool_intent mismatch")
    require(errors, payload.get("envelope_built_with_helper") is True, "envelope helper flag missing")
    require(errors, payload.get("build_helper_path") == "scripts/build_three_engine_envelope.py", "wrong envelope helper path")
    require(errors, payload.get("no_builder_audit_verdict") is True, "no_builder_audit_verdict false")
    require(errors, payload.get("no_builder_audit_verdict_envelope_gate") is True, "boundary gate false")
    errors.extend(f"boundary: {err}" for err in boundary.boundary_errors(payload))
    for engine in ("julia", "jax", "pytorch"):
        lane = load(RESULT_DIR / f"{common.SIM_ID}_{engine}_results.json")
        require(errors, lane.get("all_pass") is True, f"{engine} lane all_pass false")
        require(errors, payload.get("engines", {}).get(engine, {}).get("result_all_pass") is True, f"{engine} envelope result_all_pass false")
        require(errors, payload.get("engines", {}).get(engine, {}).get("reads_peer_result") is False, f"{engine} reads_peer_result must be false")


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    validate_packet_files(errors)
    packet = load(common.RESULT_PATH)
    validate_common_result(errors, packet)
    validate_envelope(errors, payload)
    generic_errors = validate_three_engine(
        payload,
        require_pytorch=True,
        strict_source_backed=True,
        require_tool_intent=True,
    )
    errors.extend(f"generic three-engine validator: {err}" for err in generic_errors)
    return errors


def main() -> int:
    payload = load(ENVELOPE)
    errors = validate_payload(payload)
    result = {
        "ok": not errors,
        "result_json": common.rel(ENVELOPE),
        "errors": errors,
    }
    common.write_json(VALIDATOR_RESULT, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
