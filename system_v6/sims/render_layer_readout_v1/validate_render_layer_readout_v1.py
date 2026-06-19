#!/usr/bin/env python3
"""Packet validator for render_layer_readout_v1."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import render_layer_readout_v1_boundary as boundary
import render_layer_readout_v1_common as common


ENVELOPE = common.RESULT_DIR / f"{common.SIM_ID}_envelope_results.json"
JAX = common.RESULT_DIR / f"{common.SIM_ID}_jax_results.json"
PYTORCH = common.RESULT_DIR / f"{common.SIM_ID}_pytorch_results.json"
JULIA = common.RESULT_DIR / f"{common.SIM_ID}_julia_results.json"
VALIDATOR_RESULT = common.RESULT_DIR / f"{common.SIM_ID}_validator_results.json"

sys.path.insert(0, str(common.ROOT / "scripts"))
import validate_three_engine_sim_result as generic_validator  # noqa: E402


REQUIRED_PACKET_FILES = [
    "build_card.md",
    "builder_self_assessment.md",
    "render_layer_readout_v1.py",
    "render_layer_readout_v1_common.py",
    "render_layer_readout_v1_boundary.py",
    "render_layer_readout_v1_jax.py",
    "render_layer_readout_v1_pytorch.py",
    "render_layer_readout_v1_julia.jl",
    "render_layer_readout_v1_envelope.py",
    "validate_render_layer_readout_v1.py",
    "tests/test_render_layer_readout_v1.py",
]
classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
TOOL_MANIFEST = {
    "validate_three_engine_sim_result": {"tried": True, "used": True, "reason": "validates standard three-engine envelope shape"},
    "render_layer_readout_v1_boundary": {"tried": True, "used": True, "reason": "runs packet-local boundary checks"},
    "json": {"tried": True, "used": True, "reason": "writes the validator receipt"},
}
TOOL_INTEGRATION_DEPTH = {
    "validate_three_engine_sim_result": "load_bearing",
    "render_layer_readout_v1_boundary": "load_bearing",
    "json": "supportive",
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def validate_payload() -> list[str]:
    errors: list[str] = []
    for rel_path in REQUIRED_PACKET_FILES:
        require(errors, (common.SIM_DIR / rel_path).is_file(), f"missing required packet file: {rel_path}")
    build_card = common.SIM_DIR / "build_card.md"
    text = build_card.read_text(encoding="utf-8") if build_card.is_file() else ""
    require(errors, common.SIM_ID in text, "build_card missing sim id")
    require(errors, "reachability witness" in text, "build_card missing reachability witness")
    require(errors, "v0 distance" in text, "build_card missing v0 distance regression")
    require(errors, "builder_audit_boundary" in text, "build_card missing builder boundary helper")
    if errors:
        result = {"schema": f"{common.SIM_ID}_validator_v1", "sim_id": common.SIM_ID, "all_pass": False, "errors": errors}
        common.write_json(VALIDATOR_RESULT, result)
        return errors

    payload = load(ENVELOPE)
    jax = load(JAX)
    pytorch = load(PYTORCH)
    julia = load(JULIA)
    rebuilt = common.build_core()
    boundary_verdict = payload["axis0_boundary"]["boundary_verdict"]

    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, payload.get("sim_id") == common.SIM_ID, "sim_id mismatch")
    require(errors, payload.get("classification") == "scratch_diagnostic", "classification must stay scratch_diagnostic")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("all_pass") is True, "envelope all_pass must be true")
    require(errors, sorted(payload.get("engines", {})) == ["jax", "julia", "pytorch"], "all three lanes must be present")
    require(errors, payload.get("claim_ceiling") == common.CLAIM_CEILING, "claim_ceiling mismatch")
    require(errors, payload["repin_reachability_gate"] == rebuilt["repin_reachability_gate"], "reachability gate drifted")
    require(errors, payload["render_readout"]["sign_vector"] == rebuilt["render_readout"]["sign_vector"], "render sign vector drifted")
    require(errors, payload["controls"]["v0_old_pin_regression"] == rebuilt["controls"]["v0_old_pin_regression"], "old pin regression drifted")
    require(errors, payload["controls"]["scrambled_error"] == rebuilt["controls"]["scrambled_error"], "scrambled control drifted")
    require(errors, len(payload["render_readout"]["sign_vector"]) == common.EXPECTED_STATE_COUNT, "render sign vector length mismatch")
    require(errors, len(payload["trajectory"]) == common.TRAJECTORY_LENGTH, "trajectory length mismatch")
    require(errors, payload["counts"]["reshape_cells"] > 0, "reshape_cells must be positive")
    require(errors, payload["counts"]["resist_cells"] > 0, "resist_cells must be positive")
    require(errors, payload["counts"]["unique_render_sign_count"] >= 2, "readout must be nonconstant")
    require(errors, boundary_verdict["relation_to_axis0_phi"] == "different_distinction_from_axis0", "expected own readout family under v1 pin")
    require(errors, boundary_verdict["verdict"] == "own_readout_family", "boundary verdict mismatch")
    require(errors, payload["controls"]["scrambled_error"]["verdict"] == "breaks-render-polarity", "scrambled-error control must break v1 readout")
    require(errors, payload["controls"]["v0_old_pin_regression"]["reproduces_unreachable_reshape"] is True, "old pin regression failed")
    require(errors, payload["controls"]["v0_old_pin_regression"]["readout_table_ran"] is False, "old pin must refuse readout rows")
    require(errors, payload["build_gates"]["boundary_helper_ok"] is True, "boundary helper gate failed")
    require(errors, payload["divergence"]["max_divergence"] == 0, "lane divergence mismatch")

    generic_errors = generic_validator.validate(payload, require_pytorch=True, require_tool_intent=False)
    errors.extend([f"generic validator: {error}" for error in generic_errors])
    errors.extend([f"builder boundary: {error}" for error in boundary.boundary_errors(payload, common.SIM_DIR)])

    expected_hash = payload["computed_hashes"]["lane_render_sign_vector_sha256"]["jax"]
    for name, lane in [("jax", jax), ("pytorch", pytorch), ("julia", julia)]:
        require(errors, lane["all_pass"] is True, f"{name} lane all_pass false")
        require(errors, lane["reads_peer_result"] is False, f"{name} reads peer result")
        require(errors, lane["classification"] == "scratch_diagnostic", f"{name} classification mismatch")
        require(errors, lane["computed_hashes"]["render_sign_vector_sha256"] == expected_hash, f"{name} sign hash mismatch")

    result = {
        "schema": f"{common.SIM_ID}_validator_v1",
        "sim_id": common.SIM_ID,
        "result_path": common.rel(VALIDATOR_RESULT),
        "validated_envelope": common.rel(ENVELOPE),
        "all_pass": not errors,
        "errors": errors,
    }
    common.write_json(VALIDATOR_RESULT, result)
    return errors


def main() -> int:
    errors = validate_payload()
    result = load(VALIDATOR_RESULT)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
