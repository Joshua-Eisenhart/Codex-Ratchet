#!/usr/bin/env python3
"""Packet-local validator for manifold_dynamic_chart_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import manifold_dynamic_chart_v0_common as common


ROOT = common.ROOT
SIM_DIR = common.SIM_DIR
RESULT_DIR = common.RESULT_DIR
ENVELOPE = RESULT_DIR / f"{common.SIM_ID}_envelope_results.json"
VALIDATOR_RESULT = RESULT_DIR / f"{common.SIM_ID}_validator_results.json"

sys.path.insert(0, str(ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402
from validate_three_engine_sim_result import validate as validate_three_engine  # noqa: E402


REQUIRED_PACKET_FILES = [
    "build_card.md",
    f"{common.SIM_ID}_common.py",
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
    build_card = SIM_DIR / "build_card.md"
    text = build_card.read_text(encoding="utf-8") if build_card.exists() else ""
    require(errors, common.SIM_ID in text, "build_card.md missing packet id")
    require(errors, "Family A 33-cell dynamic density-state chart" in text, "build_card.md missing v0 object")
    require(errors, "G.2a idempotency-from-birth" in text, "build_card.md missing G.2a")
    require(errors, "NO Axis-0 admission" in text, "build_card.md missing Axis-0 ceiling")


def validate_ceiling(errors: list[str], payload: dict[str, Any]) -> None:
    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, payload.get("sim_id") == common.SIM_ID, "sim_id mismatch")
    require(errors, payload.get("mode") == common.ENGINE_MODE, "engine mode mismatch")
    require(errors, payload.get("classification") == common.CLASSIFICATION, "classification must be scratch_diagnostic")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("claim_ceiling") == common.CLAIM_CEILING, "claim ceiling mismatch")
    require(errors, payload.get("all_pass") is True, "top-level all_pass must be true")
    for banned in ("Axis-0 admission", "bridge admission", "physics", "final substrate choice"):
        require(errors, banned in payload.get("disallowed_claims", []), f"missing disallowed claim: {banned}")


def validate_dynamic_rows(errors: list[str], payload: dict[str, Any]) -> None:
    require(errors, payload.get("carrier", {}).get("state_count") == common.EXPECTED_STATE_COUNT, "state_count mismatch")
    require(errors, payload.get("carrier", {}).get("edge_count") == common.EXPECTED_EDGE_COUNT, "edge_count mismatch")
    require(errors, payload.get("trajectory", {}).get("T", 0) > 1, "trajectory T must be >1")
    require(errors, len(payload.get("state_rows", [])) == common.EXPECTED_STATE_COUNT * (payload["trajectory"]["T"] + 1), "state row count mismatch")
    require(errors, len(payload.get("dynamic_shell_rows", [])) == payload["trajectory"]["T"] + 1, "shell row count mismatch")
    require(errors, len(payload.get("jk_fuzz_rows", [])) == len(payload.get("state_rows", [])), "jk row count mismatch")
    require(errors, payload.get("entropy_field", {}).get("computed_from") == "density-matrix eigenvalues of rho_c(t)", "entropy source drift")
    require(errors, payload.get("dynamic_shell_motion", {}).get("total_entered_or_exited", 0) > 0, "shells did not move")
    require(errors, payload.get("witness_gates", {}).get("density_validity", {}).get("pass") is True, "density gate failed")
    require(errors, payload.get("witness_gates", {}).get("entropy_source", {}).get("pass") is True, "entropy source gate failed")
    require(errors, payload.get("witness_gates", {}).get("dynamics_nontriviality", {}).get("pass") is True, "dynamics gate failed")
    require(errors, payload.get("witness_gates", {}).get("perturbation_bite", {}).get("pass") is True, "perturbation gate failed")
    require(errors, payload.get("static_phi_bridge_row", {}).get("tested_not_assumed") is True, "static phi bridge not tested")


def validate_controls(errors: list[str], payload: dict[str, Any]) -> None:
    controls = payload.get("controls", {})
    require(errors, controls.get("identity_dynamics", {}).get("classifier_status") == "refuse_degenerate_static", "identity control did not refuse")
    require(errors, controls.get("identity_dynamics", {}).get("dynamics_nontrivial") is False, "identity dynamics moved")
    require(errors, controls.get("scrambled_adjacency", {}).get("ran") is True, "scrambled adjacency control missing")
    require(errors, controls.get("dropped_half_perturbation_family", {}).get("ran") is True, "dropped-half control missing")
    require(errors, controls.get("no_identity_leak", {}).get("classifier_input_fields_exclude_identity") is True, "identity leak control failed")
    classifier = payload.get("axis0_response_protocol_v0", {})
    require(errors, classifier.get("axis0_admission") == "not_admitted_first_honest_attempt", "Axis-0 admission wording drift")
    require(errors, "cell_id" not in classifier.get("classifier_feature_fields", []), "classifier feature leaks cell_id")


def validate_envelope_and_tooling(errors: list[str], payload: dict[str, Any]) -> None:
    require(errors, set(payload.get("engines", {})) == {"julia", "jax", "pytorch"}, "engine set mismatch")
    require(errors, set(payload.get("engine_lanes", [])) == {"julia", "jax", "pytorch"}, "engine_lanes mismatch")
    consensus = payload.get("engine_consensus", {})
    for key in ("state_count_agreement", "state_row_count_agreement", "trajectory_signature_agreement", "entropy_signature_agreement"):
        require(errors, consensus.get(key) is True, f"engine consensus failed: {key}")
    require(errors, payload.get("TOOL_MANIFEST") == common.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, payload.get("TOOL_INTEGRATION_DEPTH") == common.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    require(errors, payload.get("tool_intent") == common.TOOL_INTENT, "tool_intent mismatch")
    require(errors, payload.get("envelope_built_with_helper") is True, "envelope helper flag missing")
    require(errors, payload.get("build_helper_path") == "scripts/build_three_engine_envelope.py", "wrong envelope helper path")
    require(errors, payload.get("builder_gates", {}).get("boundary_helper_fully_used") is True, "boundary helper not used")
    require(errors, payload.get("builder_gates", {}).get("G_2a_idempotency_from_birth") is True, "G.2a gate missing")
    require(errors, payload.get("no_builder_audit_verdict") is True, "no_builder_audit_verdict false")
    require(errors, payload.get("no_builder_audit_verdict_envelope_gate") is True, "boundary gate false")
    errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))
    for engine in ("julia", "jax", "pytorch"):
        lane = load(RESULT_DIR / f"{common.SIM_ID}_{engine}_results.json")
        require(errors, lane.get("all_pass") is True, f"{engine} lane all_pass false")
        require(errors, payload.get("engines", {}).get(engine, {}).get("result_all_pass") is True, f"{engine} envelope result_all_pass false")
        require(errors, payload.get("engines", {}).get(engine, {}).get("reads_peer_result") is False, f"{engine} reads_peer_result must be false")


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    validate_packet_files(errors)
    validate_ceiling(errors, payload)
    validate_dynamic_rows(errors, payload)
    validate_controls(errors, payload)
    validate_envelope_and_tooling(errors, payload)
    packet_errors = common.validate_payload(payload)
    errors.extend(f"packet validator: {err}" for err in packet_errors)
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
