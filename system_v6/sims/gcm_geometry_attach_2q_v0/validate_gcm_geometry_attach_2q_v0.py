#!/usr/bin/env python3
"""Packet-local validator for gcm_geometry_attach_2q_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import gcm_geometry_attach_2q_v0_boundary as boundary
import gcm_geometry_attach_2q_v0_common as common


ROOT = common.ROOT
SIM_DIR = common.SIM_DIR
RESULT_DIR = common.RESULT_DIR
ENVELOPE = common.ENVELOPE_PATH
VALIDATOR_RESULT = common.VALIDATOR_RESULT_PATH

sys.path.insert(0, str(ROOT / "scripts"))
from gcm_substrate_check import gcm_substrate_check  # noqa: E402
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
    f"results/{common.SIM_ID}_results.json",
    f"results/{common.SIM_ID}_julia_results.json",
    f"results/{common.SIM_ID}_jax_results.json",
    f"results/{common.SIM_ID}_pytorch_results.json",
    f"results/{common.SIM_ID}_envelope_results.json",
]


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


HELPER_OUTPUT_TOP_LEVEL_KEYS = ("substrate_enforcement", "two_q_registry_dependency")
HELPER_SOURCE_LOCK_KEYS = ("substrate_check_helper", "two_q_freeze_registry_dependency")


def without_runtime_fields(payload: dict[str, Any]) -> dict[str, Any]:
    clone = json.loads(json.dumps(payload))
    clone.pop("generated_at", None)
    clone.pop("result_sha256", None)
    for key in HELPER_OUTPUT_TOP_LEVEL_KEYS:
        clone.pop(key, None)
    source_locks = clone.get("source_locks")
    if isinstance(source_locks, dict):
        for row in source_locks.values():
            if isinstance(row, dict):
                row.pop("git_last_commit", None)
        for key in HELPER_SOURCE_LOCK_KEYS:
            source_locks.pop(key, None)
    return clone


def validate_packet_files(errors: list[str]) -> None:
    for rel_path in REQUIRED_PACKET_FILES:
        require(errors, (SIM_DIR / rel_path).is_file(), f"missing required packet file: {rel_path}")
    text = (SIM_DIR / "build_card.md").read_text(encoding="utf-8")
    for required in (
        common.SIM_ID,
        "DECLARE: layers 3-12 + 17-18 | integrated-onto-the-carve | 2Q",
        "gcm_object_id gcmobj_a40e54e13cec01466c9d675028b3574b",
        "544 survivors",
        "16 entangled",
        "Schmidt",
        "fiber over each marginal pair",
        "G.2a",
        "scripts/gcm_substrate_check.py",
        "scratch_diagnostic",
        "carrier-and-pins-relative",
        "NO git add/commit",
    ):
        require(errors, required in text, f"build_card.md missing {required}")


def validate_common_result(errors: list[str], packet: dict[str, Any]) -> None:
    rebuilt = common.build_packet()
    require(errors, without_runtime_fields(packet) == without_runtime_fields(rebuilt), "packet drift against source rebuild")
    errors.extend(f"common packet: {err}" for err in common.validate_payload(packet))
    errors.extend(f"boundary: {err}" for err in boundary.boundary_errors(packet))
    positive = gcm_substrate_check(packet, common.ONE_Q_REGISTRY_PATH)
    negative = gcm_substrate_check(common.lineage_free_variant(packet), common.ONE_Q_REGISTRY_PATH)
    require(errors, positive.get("ok") is True, f"positive gcm_substrate_check failed: {positive.get('errors')}")
    require(errors, negative.get("ok") is False, "lineage-free gcm_substrate_check did not fail")
    require(errors, packet.get("two_q_registry_dependency", {}).get("status") in {"landed_registry_consumed", "not_landed_provisional_ids_derived"}, "2Q registry dependency status missing")
    require(errors, packet.get("controls", {}).get("product_survivor_geometric_marginal_radii", {}).get("all_exact_within_tolerance") is True, "product marginal radii control failed")
    require(errors, packet.get("controls", {}).get("entangled_reduced_radii", {}).get("all_strictly_between_zero_and_one") is True, "entangled radius control failed")
    require(errors, packet.get("controls", {}).get("one_q_regression_through_partial_trace", {}).get("image_equals_1q_attach_hopf_set") is True, "1Q regression failed")


def validate_envelope(errors: list[str], payload: dict[str, Any]) -> None:
    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, payload.get("schema") == "gcm_geometry_attach_2q_v0_envelope_v1", "packet envelope schema mismatch")
    require(errors, payload.get("sim_id") == common.SIM_ID, "sim_id mismatch")
    require(errors, payload.get("mode") == common.ENGINE_MODE, "engine mode mismatch")
    require(errors, payload.get("classification") == common.CLASSIFICATION, "classification mismatch")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("claim_ceiling") == common.CLAIM_CEILING, "claim ceiling mismatch")
    require(errors, payload.get("carrier_and_pins_relative") is True, "carrier_and_pins_relative flag missing")
    require(errors, payload.get("all_pass") is True, "top-level all_pass false")
    require(errors, set(payload.get("engine_lanes", [])) == {"julia", "jax", "pytorch"}, "engine lanes mismatch")
    consensus = payload.get("engine_consensus", {})
    for key in (
        "all_engine_lanes_pass",
        "survivor_count_agreement",
        "product_count_agreement",
        "entangled_count_agreement",
        "entangled_fiber_count_agreement",
        "one_q_regression_agreement",
    ):
        require(errors, consensus.get(key) is True, f"engine consensus failed: {key}")
    require(errors, payload.get("TOOL_MANIFEST") == common.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, payload.get("TOOL_INTEGRATION_DEPTH") == common.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    require(errors, payload.get("tool_intent") == common.TOOL_INTENT, "tool_intent mismatch")
    require(errors, payload.get("envelope_built_with_helper") is True, "envelope helper flag missing")
    require(errors, payload.get("build_helper_path") == "scripts/build_three_engine_envelope.py", "wrong envelope helper path")
    errors.extend(f"boundary: {err}" for err in boundary.boundary_errors(payload))
    for engine in ("julia", "jax", "pytorch"):
        lane = load(RESULT_DIR / f"{common.SIM_ID}_{engine}_results.json")
        require(errors, lane.get("all_pass") is True, f"{engine} lane all_pass false")
        require(errors, payload.get("engines", {}).get(engine, {}).get("result_all_pass") is True, f"{engine} envelope result_all_pass false")
        require(errors, payload.get("engines", {}).get(engine, {}).get("reads_peer_result") is False, f"{engine} reads_peer_result must be false")
    generic_errors = validate_three_engine(
        payload,
        require_pytorch=True,
        strict_source_backed=True,
        require_tool_intent=True,
    )
    errors.extend(f"generic three-engine validator: {err}" for err in generic_errors)


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    validate_packet_files(errors)
    validate_common_result(errors, load(common.RESULT_PATH))
    validate_envelope(errors, payload)
    return errors


def main() -> int:
    payload = load(ENVELOPE)
    errors = validate_payload(payload)
    result = {"ok": not errors, "result_json": common.rel(ENVELOPE), "errors": errors}
    common.write_json(VALIDATOR_RESULT, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
