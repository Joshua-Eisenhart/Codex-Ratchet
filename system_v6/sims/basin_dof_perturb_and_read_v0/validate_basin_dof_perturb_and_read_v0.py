#!/usr/bin/env python3
"""Packet-local validator for basin_dof_perturb_and_read_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import basin_dof_perturb_and_read_v0_common as common


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
    "tests/test_basin_dof_perturb_and_read_v0.py",
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
    require(errors, common.CLAIM_CEILING in text, "build_card.md missing claim ceiling")
    require(errors, "NO git add/commit" in text, "build_card.md missing no-git boundary")


def validate_ceiling(errors: list[str], payload: dict[str, Any]) -> None:
    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, payload.get("sim_id") == common.SIM_ID, "sim_id mismatch")
    require(errors, payload.get("mode") == common.ENGINE_MODE, "engine mode mismatch")
    require(errors, payload.get("classification") == common.CLASSIFICATION, "classification must be scratch_diagnostic")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("claim_ceiling") == common.CLAIM_CEILING, "claim ceiling mismatch")
    require(errors, payload.get("all_pass") is True, "top-level all_pass must be true")
    for banned in ("axis admission", "basin theorem", "manifold existence proof", "bridge admission", "physics", "canonical promotion"):
        require(errors, banned in payload.get("disallowed_claims", []), f"missing disallowed claim: {banned}")


def validate_dof_table(errors: list[str], payload: dict[str, Any]) -> None:
    rebuilt = common.build_packet_object()
    table = payload.get("dof_classification_table", [])
    require(errors, common.stable_sha256(table) == common.stable_sha256(rebuilt["dof_classification_table"]), "DoF table recompute mismatch")
    by_id = {row.get("dof_id"): row for row in table}
    require(errors, set(common.EXPECTED_DOF_IDS) <= set(by_id), "required DoF rows missing")
    require(errors, by_id.get("G0", {}).get("classification") == "RETURN", "G0 must RETURN")
    require(errors, by_id.get("G2", {}).get("classification") == "RETURN", "G2 must RETURN")
    for dof_id in ("G1", "G3L", "G3R", "G5"):
        require(errors, by_id.get(dof_id, {}).get("classification") == "BOUNDARY", f"{dof_id} must BOUNDARY")
    require(errors, payload.get("result_summary", {}).get("return_dof_count", 0) >= 1, "missing RETURN DoF")
    require(errors, payload.get("result_summary", {}).get("boundary_dof_count", 0) >= 1, "missing BOUNDARY DoF")
    require(
        errors,
        payload.get("result_summary", {}).get("pre_registered_expectation_2_pass") is True,
        "pre-registered expectation 2 failed",
    )
    for row in table:
        require(errors, row.get("claim_ceiling") == common.CLAIM_CEILING, f"{row.get('dof_id')} claim ceiling mismatch")
        require(errors, bool(row.get("trajectory_rows")), f"{row.get('dof_id')} trajectory rows missing")
        require(errors, bool(row.get("pinned_perturbation_sizes")), f"{row.get('dof_id')} perturb sizes missing")
        require(errors, row.get("absent_exit_checked") is True, f"{row.get('dof_id')} absent-exit check missing")
        require(errors, row.get("axis0_recomputed_by_source") is True, f"{row.get('dof_id')} axis0 source recompute missing")
        if row.get("classification") == "RETURN":
            require(errors, row.get("returned_to_prior_terminal_class") is True, f"{row.get('dof_id')} did not return spatially")
            require(errors, row.get("axis0_readout_reconverged") is True, f"{row.get('dof_id')} readout did not reconverge")
        if row.get("classification") == "BOUNDARY":
            require(errors, row.get("boundary_found") is True, f"{row.get('dof_id')} boundary flag missing")
            require(errors, row.get("escaped_to_different_terminal_class") is True, f"{row.get('dof_id')} escape flag missing")


def validate_controls(errors: list[str], controls: dict[str, Any]) -> None:
    require(errors, controls.get("zero_perturbation", {}).get("classification") == "RETURN", "zero control must RETURN")
    require(
        errors,
        controls.get("zero_perturbation", {}).get("trivial_return_calibration") is True,
        "zero control not a trivial return calibration",
    )
    require(errors, controls.get("over_perturbation", {}).get("classification") == "BOUNDARY", "over control must BOUNDARY")
    require(errors, controls.get("over_perturbation", {}).get("past_basin_scale") is True, "over control not past basin scale")
    require(
        errors,
        controls.get("probe_erased_constant_field", {}).get("classification") == "DEGRADED",
        "probe-erased control must degrade",
    )
    require(
        errors,
        controls.get("probe_erased_constant_field", {}).get("axis_readout_load_bearing") is True,
        "axis readout not load-bearing under erasure",
    )
    require(
        errors,
        controls.get("shuffled_order_N01", {}).get("n01_order_control_fired") is True,
        "N01 shuffled-order control did not fire",
    )


def validate_axis0(errors: list[str], payload: dict[str, Any]) -> None:
    axis0 = payload.get("axis0_readout_rebuild", {})
    require(errors, axis0.get("source_sim_id") == "discrete_axis0_field_v0", "axis0 source sim mismatch")
    require(errors, axis0.get("commit_hint") == common.AXIS0_COMMIT_HINT, "axis0 commit hint mismatch")
    require(errors, axis0.get("recomputed") is True, "axis0 was not recomputed")
    require(errors, bool(axis0.get("polarity_counts")), "axis0 polarity counts missing")


def validate_smt(errors: list[str], rows: dict[str, Any]) -> None:
    require(errors, set(rows) >= {"z3", "cvc5"}, "SMT row set mismatch")
    for name in ("z3", "cvc5"):
        row = rows.get(name, {})
        require(errors, row.get("ran") is True and row.get("load_bearing") is True, f"{name} did not run load-bearing")
        require(errors, row.get("verdict") == "unsat", f"{name} identity verdict must be UNSAT")
        require(errors, row.get("erased_flip_verdict") == "sat", f"{name} erased flip must be SAT")
        require(errors, row.get("asserted_precomputed_boolean") is False, f"{name} must bind values, not booleans")
        bound = row.get("bound_values", {})
        require(errors, bound.get("return_dof_count", 0) >= 1, f"{name} did not bind return count")
        require(errors, bound.get("boundary_dof_count", 0) >= 1, f"{name} did not bind boundary count")


def validate_tooling(errors: list[str], payload: dict[str, Any]) -> None:
    require(errors, payload.get("TOOL_MANIFEST") == common.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, payload.get("TOOL_INTEGRATION_DEPTH") == common.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    require(errors, payload.get("tool_intent") == common.TOOL_INTENT, "tool_intent mismatch")
    require(errors, payload.get("envelope_built_with_helper") is True, "envelope helper gate missing")
    require(errors, payload.get("build_helper_path") == "scripts/build_three_engine_envelope.py", "wrong envelope helper path")
    require(errors, payload.get("no_builder_audit_verdict") is True, "no_builder_audit_verdict must be true")
    require(errors, payload.get("no_builder_audit_verdict_envelope_gate") is True, "no_builder_audit_verdict_envelope_gate must be true")
    require(errors, payload.get("builder_gates", {}).get("packet_audit_verdict_absent") is True, "audit verdict absent gate failed")
    errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))
    require(errors, set(payload.get("engines", {})) == {"julia", "jax", "pytorch"}, "all three engine lanes required")
    require(errors, payload.get("engine_contract", {}).get("omitted_lanes") == {}, "no omitted lanes allowed")
    for engine in ("julia", "jax", "pytorch"):
        lane_path = RESULT_DIR / f"{common.SIM_ID}_{engine}_results.json"
        lane = load(lane_path)
        require(errors, lane.get("all_pass") is True, f"{engine} lane all_pass false")
        require(errors, lane.get("reads_peer_result") is False, f"{engine} reads_peer_result must be false")
        require(errors, bool(lane.get("packages_used")), f"{engine} packages_used missing")
        require(errors, bool(lane.get("aligned_packages_load_bearing")), f"{engine} load-bearing packages missing")
        require(errors, payload.get("engines", {}).get(engine, {}).get("result_all_pass") is True, f"{engine} envelope result_all_pass false")
        require(errors, payload.get("engines", {}).get(engine, {}).get("reads_peer_result") is False, f"{engine} envelope reads_peer_result false")


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    validate_packet_files(errors)
    validate_ceiling(errors, payload)
    validate_dof_table(errors, payload)
    validate_controls(errors, payload.get("controls", {}))
    validate_axis0(errors, payload)
    validate_smt(errors, payload.get("crossover_proofs", {}))
    validate_tooling(errors, payload)
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
        "validator": common.rel(Path(__file__).resolve()),
    }
    common.write_json(VALIDATOR_RESULT, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
