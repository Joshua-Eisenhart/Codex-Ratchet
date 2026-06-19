#!/usr/bin/env python3
"""Packet validator for render_layer_readout_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import render_layer_readout_v0_common as common


ENVELOPE = common.RESULT_DIR / f"{common.SIM_ID}_envelope_results.json"
JAX = common.RESULT_DIR / f"{common.SIM_ID}_jax_results.json"
PYTORCH = common.RESULT_DIR / f"{common.SIM_ID}_pytorch_results.json"
JULIA = common.RESULT_DIR / f"{common.SIM_ID}_julia_results.json"
VALIDATOR_RESULT = common.RESULT_DIR / f"{common.SIM_ID}_validator_results.json"
AUDIT_VERDICT = common.SIM_DIR / "audit_verdict.md"

sys.path.insert(0, str(common.ROOT / "scripts"))
import validate_three_engine_sim_result as generic_validator  # noqa: E402
from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def validate_payload() -> list[str]:
    errors: list[str] = []
    for path in [ENVELOPE, JAX, PYTORCH, JULIA, common.SIM_DIR / "build_card.md", common.SIM_DIR / "builder_self_assessment.md"]:
        require(errors, path.exists(), f"missing required file: {common.rel(path)}")
    if errors:
        return errors

    payload = load(ENVELOPE)
    jax = load(JAX)
    pytorch = load(PYTORCH)
    julia = load(JULIA)
    boundary = payload["axis0_boundary"]["boundary_verdict"]

    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, payload.get("sim_id") == common.SIM_ID, "sim_id mismatch")
    require(errors, payload.get("classification") == "scratch_diagnostic", "classification must stay scratch_diagnostic")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("all_pass") is True, "envelope all_pass must be true")
    require(errors, sorted(payload.get("engines", {})) == ["jax", "julia", "pytorch"], "all three lanes must be present")
    require(errors, len(payload["render_readout"]["sign_vector"]) == common.EXPECTED_STATE_COUNT, "render sign vector length mismatch")
    require(errors, len(payload["trajectory"]) == common.TRAJECTORY_LENGTH, "trajectory length mismatch")
    require(errors, boundary["relation_to_axis0_phi"] == "falsifier", "expected no-stable falsifier on current carrier")
    require(errors, boundary["verdict"] == "no_stable_distinction", "boundary verdict mismatch")
    require(errors, "quantization correction load" in boundary["reads"], "own readout description missing")
    require(errors, payload["counts"]["axis0_disagreement_cells"] > 0, "render row must not alias Axis-0 under this result")
    require(errors, payload["controls"]["identity_dynamics_degeneracy"]["verdict"] == "identity-dynamics-degenerates-render-readout", "identity control failed")
    require(errors, payload["controls"]["scrambled_error"]["verdict"] == "constant-readout-not-breakable-no-stable", "scrambled-error control should expose no-stable constant row")
    require(errors, payload["controls"]["no_identity_leak"]["verdict"] == "passes-no-identity-leak", "identity leak control failed")
    require(errors, payload["controls"]["positive_predicate_boundary"]["verdict"] == "positive-predicate-admits-anchor", "positive predicate control failed")
    require(errors, payload["build_gates"]["decorative_falsifier_recorded"] is True, "decorative falsifier gate not recorded")
    require(errors, payload["divergence"]["max_divergence"] == 0, "lane divergence mismatch")

    generic_errors = generic_validator.validate(payload, require_pytorch=True, require_tool_intent=False)
    errors.extend([f"generic validator: {error}" for error in generic_errors])
    errors.extend([f"builder boundary: {error}" for error in builder_audit_boundary_errors(payload, AUDIT_VERDICT)])

    for name, lane in [("jax", jax), ("pytorch", pytorch), ("julia", julia)]:
        require(errors, lane["all_pass"] is True, f"{name} lane all_pass false")
        require(errors, lane["reads_peer_result"] is False, f"{name} reads peer result")
        require(errors, lane["classification"] == "scratch_diagnostic", f"{name} classification mismatch")

    return errors


def main() -> int:
    errors = validate_payload()
    result = {
        "schema": f"{common.SIM_ID}_validator_v1",
        "sim_id": common.SIM_ID,
        "result_path": common.rel(VALIDATOR_RESULT),
        "validated_envelope": common.rel(ENVELOPE),
        "all_pass": not errors,
        "errors": errors,
    }
    common.write_json(VALIDATOR_RESULT, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
