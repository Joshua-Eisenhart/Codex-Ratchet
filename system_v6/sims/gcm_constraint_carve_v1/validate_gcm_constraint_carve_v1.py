#!/usr/bin/env python3
"""Packet-local validator for gcm_constraint_carve_v1."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import gcm_constraint_carve_v1_boundary as boundary
import gcm_constraint_carve_v1_common as common


ROOT = common.ROOT
SIM_DIR = common.SIM_DIR
RESULT_DIR = common.RESULT_DIR
ENVELOPE = common.ENVELOPE_PATH
ENVELOPE_SPEC = SIM_DIR / f"{common.SIM_ID}_envelope_spec.json"
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


def pinned_blindness_guard() -> dict[str, Any]:
    if ENVELOPE_SPEC.exists():
        spec = load(ENVELOPE_SPEC)
        guard = spec.get("terrain_blindness_guard")
        if not isinstance(guard, dict):
            guard = spec.get("extra_fields", {}).get("terrain_blindness_guard")
        if isinstance(guard, dict):
            return guard
    packet_guard = load(common.RESULT_PATH).get("terrain_blindness_guard")
    return packet_guard if isinstance(packet_guard, dict) else {}


def forbidden_token_errors(text: str, constraint_id: str, tokens: list[str]) -> list[str]:
    errors: list[str] = []
    lowered = text.lower()
    for token in tokens:
        if token in {"Se", "Ne", "Ni", "Si"}:
            matched = re.search(rf"\b{re.escape(token)}\b", text) is not None
        else:
            matched = token.lower() in lowered
        if matched:
            errors.append(f"{constraint_id}: forbidden predicate token {token!r}")
    return errors


def recompute_source_blindness_guard(pinned_guard: dict[str, Any]) -> dict[str, Any]:
    tokens = pinned_guard.get("forbidden_tokens")
    scope = pinned_guard.get("checked_constraint_ids")
    if not isinstance(tokens, list) or not all(isinstance(token, str) for token in tokens):
        tokens = list(common.FORBIDDEN_PREDICATE_TOKENS)
    if not isinstance(scope, list) or not all(isinstance(constraint_id, str) for constraint_id in scope):
        scope = [row["id"] for row in common.CONSTRAINTS]

    by_id = {row.get("id"): row for row in common.CONSTRAINTS}
    predicate_texts: list[str] = []
    errors: list[str] = []
    for constraint_id in scope:
        constraint = by_id.get(constraint_id)
        if constraint is None:
            errors.append(f"{constraint_id}: missing current source constraint")
            continue
        text = common.constraint_predicate_text(constraint)
        predicate_texts.append(text)
        errors.extend(forbidden_token_errors(text, constraint_id, tokens))

    return {
        "guard": "admissibility_predicate_token_guard",
        "forbidden_tokens": tokens,
        "checked_constraint_ids": scope,
        "predicate_text_sha256": common.stable_sha256(predicate_texts),
        "errors": errors,
        "clean": not errors,
    }


def validate_current_source_blindness(errors: list[str], packet: dict[str, Any]) -> None:
    emitted = packet.get("terrain_blindness_guard")
    require(errors, isinstance(emitted, dict), "terrain blindness guard missing from result packet")
    if not isinstance(emitted, dict):
        return
    pinned = pinned_blindness_guard()
    require(errors, bool(pinned), "terrain blindness guard missing from pinned envelope spec")
    fresh = recompute_source_blindness_guard(pinned)
    require(errors, fresh.get("clean") is True, "current source terrain blindness recompute failed")
    for err in fresh.get("errors", []):
        errors.append(f"current source terrain blindness: {err}")
    for key in ("guard", "forbidden_tokens", "checked_constraint_ids", "predicate_text_sha256", "errors", "clean"):
        require(
            errors,
            emitted.get(key) == fresh.get(key),
            f"terrain blindness guard stale/mismatch: {key}",
        )


def validate_packet_files(errors: list[str]) -> None:
    for rel_path in REQUIRED_PACKET_FILES:
        require(errors, (SIM_DIR / rel_path).is_file(), f"missing required packet file: {rel_path}")
    card = SIM_DIR / "build_card.md"
    text = card.read_text(encoding="utf-8") if card.exists() else ""
    for required in (
        common.SIM_ID,
        "M(C)",
        "Split C4 out of the admissibility carve",
        "C2 predicate source line",
        "identity_leak_*",
        "G.2a",
        "scripts/builder_audit_boundary.py",
        "scratch_diagnostic",
        "not THE manifold",
        "NO git add/commit",
    ):
        require(errors, required in text, f"build_card.md missing {required}")


def validate_common_result(errors: list[str], packet: dict[str, Any]) -> None:
    errors.extend(f"common packet: {err}" for err in common.validate_payload(packet))
    errors.extend(f"boundary: {err}" for err in boundary.boundary_errors(packet))
    require(errors, packet.get("schema") == "gcm_constraint_carve_v1_result_v1", "common schema mismatch")
    require(errors, packet.get("standards_version") == "audit_standards_codex_v1", "standards_version missing")
    require(errors, packet.get("survivor_count") == common.EXPECTED_SURVIVOR_COUNT, "survivor_count mismatch")
    require(errors, packet.get("quotient", {}).get("class_count") == common.EXPECTED_QUOTIENT_CLASS_COUNT, "quotient class count mismatch")
    require(errors, len(packet.get("constraint_family_C", [])) == 3, "active C must contain exactly C1-C3")
    require(
        errors,
        all(row.get("id") != "v0_rejected_C4_terrain_framed_residency_variant" for row in packet.get("constraint_family_C", [])),
        "v0 C4 must not appear in active constraint_family_C",
    )
    require(errors, packet.get("terrain_blindness_guard", {}).get("clean") is True, "terrain blindness guard failed")
    validate_current_source_blindness(errors, packet)
    require(
        errors,
        packet.get("controls", {}).get("blindness_control", {}).get("injected_variant_caught") is True,
        "blindness control did not catch injected variant",
    )
    require(errors, len(packet.get("kill_ledger", [])) == common.EXPECTED_CANDIDATE_COUNT - common.EXPECTED_SURVIVOR_COUNT, "kill ledger size mismatch")
    require(
        errors,
        packet.get("kill_counts_by_constraint")
        == {
            "C1_finite_density_carrier": 92,
            "C2_probe_distinguishability_xz_local_adapter_pin": 5,
            "C3_persistence_n01_order_gap": 12,
        },
        "kill counts mismatch",
    )
    require(errors, all(row.get("bite") is True for row in packet.get("controls", {}).get("constraint_erasure", [])), "not every constraint erasure bites")
    existence = packet.get("existence_tests", {})
    require(errors, existence.get("stable") is True, "stability existence probe failed")
    require(errors, existence.get("independent") is True, "independence existence probe failed")
    require(errors, existence.get("identity_leak_detected") is True, "identity leak field missing/false")
    require(errors, existence.get("identity_leak_excluded_best_accuracy", 1.0) < 1.0, "identity-excluded accuracy must be < 1.0")
    require(errors, existence.get("chart_recoverable") is True, "chart recovery failed")
    require(errors, existence.get("negative_controlled") is True, "negative controls failed")
    readout = packet.get("post_carve_terrain_readout", {})
    require(errors, readout.get("can_affect_survival") is False, "post-carve readout can affect survival")
    require(errors, readout.get("survival_inputs") == [], "post-carve readout has survival inputs")
    require(errors, packet.get("M_C_t_hook", {}).get("survivor_count") == common.EXPECTED_MCT_SURVIVOR_COUNT, "M(C,t) survivor count drift")
    require(errors, packet.get("M_C_t_hook", {}).get("quotient_class_count") == common.EXPECTED_MCT_QUOTIENT_CLASS_COUNT, "M(C,t) class count drift")
    regression = packet.get("v0_regression_row", {})
    require(errors, regression.get("v0_regression_survivor_count") == common.EXPECTED_V0_REGRESSION_SURVIVOR_COUNT, "v0 regression survivor count drift")
    require(errors, regression.get("v0_regression_quotient_class_count") == common.EXPECTED_V0_REGRESSION_CLASS_COUNT, "v0 regression class count drift")
    require(errors, regression.get("diff_demonstrates_contamination") is True, "v0 regression diff not demonstrated")


def validate_envelope(errors: list[str], payload: dict[str, Any]) -> None:
    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, payload.get("schema") == "gcm_constraint_carve_v1_envelope_v1", "packet envelope schema mismatch")
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
        "v0_regression_survivor_count_agreement",
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
    packet = load(common.RESULT_PATH)
    validate_common_result(errors, packet)
    validate_envelope(errors, payload)
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
