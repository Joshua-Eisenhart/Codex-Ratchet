#!/usr/bin/env python3
"""Packet-local validator for manifold_ab_weld_relation_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import manifold_ab_weld_relation_v0_common as common


ROOT = common.ROOT
SIM_DIR = common.SIM_DIR
RESULT_DIR = common.RESULT_DIR
ENVELOPE = RESULT_DIR / f"{common.SIM_ID}_envelope_results.json"
VALIDATOR_RESULT = RESULT_DIR / f"{common.SIM_ID}_validator_results.json"
AUDIT_VERDICT = SIM_DIR / "audit_verdict.md"

sys.path.insert(0, str(ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402
from validate_three_engine_sim_result import validate as validate_three_engine  # noqa: E402


REQUIRED_PACKET_FILES = [
    "build_card.md",
    "builder_self_assessment.md",
    f"{common.SIM_ID}_common.py",
    f"{common.SIM_ID}_julia.jl",
    f"{common.SIM_ID}_jax.py",
    f"{common.SIM_ID}_pytorch.py",
    "write_envelope_spec.py",
    f"validate_{common.SIM_ID}.py",
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
    if card.is_file():
        text = card.read_text(encoding="utf-8")
        require(errors, "manifold_ab_weld_relation_v0" in text, "build_card.md missing sim id")
        require(errors, "G.2a" in text, "build_card.md missing G.2a boundary note")


def validate_source_pins(errors: list[str], payload: dict[str, Any]) -> None:
    pins = payload.get("source_import_audit", {}).get("source_hash_pins", {})
    require(errors, set(pins) == set(common.SOURCE_PINS), "source hash pin set mismatch")
    for key, expected in common.SOURCE_PINS.items():
        row = pins.get(key, {})
        require(errors, row.get("path") == expected["path"], f"{key} path mismatch")
        require(errors, row.get("expected_sha256") == expected["sha256"], f"{key} expected sha mismatch")
        require(errors, row.get("observed_sha256") == expected["sha256"], f"{key} observed sha mismatch")
        require(errors, row.get("hash_verified") is True, f"{key} hash not verified")
    require(errors, payload.get("source_import_audit", {}).get("state_object_inputs") == ["family_a_envelope", "family_b_envelope"], "state object inputs must be only A and B")
    require(errors, payload.get("source_import_audit", {}).get("family_c_used_as_relation_input") is False, "Family C must not be a relation input")


def validate_state_objects(errors: list[str], payload: dict[str, Any], rebuilt: dict[str, Any]) -> None:
    states = payload.get("pinned_state_objects", {})
    require(errors, set(states) == {"A", "B"}, "pinned_state_objects must contain only A and B")
    a = states.get("A", {})
    b = states.get("B", {})
    require(errors, a.get("state_object_id") == common.EXPECTED_A_STATE_ID, "Family A state id mismatch")
    require(errors, b.get("state_object_id") == common.EXPECTED_B_STATE_ID, "Family B state id mismatch")
    require(errors, a.get("state_object_id") != b.get("state_object_id"), "A and B state ids folded together")
    require(errors, a.get("loaded_by_hash") is True and b.get("loaded_by_hash") is True, "A/B must be loaded by hash")
    require(errors, payload.get("parent_anchor_checks") == rebuilt["parent_anchor_checks"], "rebuilt parent anchor checks drifted")
    require(errors, payload.get("parent_anchor_checks", {}).get("all_pass") is True, "parent anchor checks failed")


def validate_coordinate_map(errors: list[str], payload: dict[str, Any]) -> None:
    rows = payload.get("coordinate_map", [])
    require(errors, len(rows) == 8, "coordinate_map must contain the eight packet coordinates")
    ids = {row.get("coordinate_id") for row in rows}
    require(
        errors,
        ids == {
            "state_object_identity",
            "chart_carrier",
            "finite_carrier_size",
            "partition_order",
            "zero_record_conservation",
            "entropy_type_surface",
            "trajectory_lineage_standard",
            "backend_scope",
        },
        "coordinate_map coordinate ids mismatch",
    )
    classes = {row.get("classification") for row in rows}
    require(errors, classes <= {"shared", "related", "independent"}, "coordinate classes outside shared/related/independent")
    require(errors, {"shared", "related", "independent"} <= classes, "coordinate map must include shared, related, and independent rows")
    require(errors, all(row.get("classification_computed") is True for row in rows), "coordinate classifications must be computed")
    require(errors, all(row.get("pass") is True for row in rows), "coordinate map row failed")
    partition = next((row for row in rows if row.get("coordinate_id") == "partition_order"), {})
    require(errors, partition.get("computed_relation_value") == 11, "partition_order relation must compute 11")
    require(errors, payload.get("coordinate_map_signature_sha256") == common.signature_rows(rows), "coordinate map signature mismatch")


def validate_weld_only(errors: list[str], payload: dict[str, Any]) -> None:
    rows = payload.get("weld_only_rows", [])
    require(errors, len(rows) == 6, "weld_only_rows must contain six relation rows")
    require(errors, all(row.get("exists_only_when_map_binds_A_and_B") is True for row in rows), "weld-only row missing A+B binding flag")
    require(errors, all(row.get("recoverable_from_A_alone") is False for row in rows), "weld row recoverable from A alone")
    require(errors, all(row.get("recoverable_from_B_alone") is False for row in rows), "weld row recoverable from B alone")
    require(errors, all(row.get("claim_ceiling") == common.CLASSIFICATION for row in rows), "weld-only row ceiling mismatch")
    require(errors, all(row.get("pass") is True for row in rows), "weld-only row failed")
    by_id = {row["row_id"]: row for row in rows}
    require(errors, by_id.get("WO2_partition_sum_relation", {}).get("computed_value") == 11, "partition sum relation must be 11")
    require(errors, by_id.get("WO3_partition_product_relation", {}).get("computed_value") == 24, "partition product relation must be 24")
    require(errors, by_id.get("WO4_zero_pair_relation", {}).get("computed_value") is True, "zero pair relation must be true")
    require(errors, by_id.get("WO6_relation_polynomial_residual", {}).get("computed_value") == 0, "relation residual must be zero")
    require(errors, payload.get("weld_only_rows_signature_sha256") == common.signature_rows(rows), "weld-only signature mismatch")


def validate_nonrecoverability(errors: list[str], payload: dict[str, Any]) -> None:
    rows = payload.get("nonrecoverability_table", [])
    require(errors, len(rows) == 6, "nonrecoverability_table must contain six rows")
    require(errors, all(row.get("A_erased_status") == "not_recoverable" for row in rows), "A-erased nonrecoverability failed")
    require(errors, all(row.get("B_erased_status") == "not_recoverable" for row in rows), "B-erased nonrecoverability failed")
    require(errors, all(row.get("both_erased_status") == "not_recoverable" for row in rows), "both-erased nonrecoverability failed")
    require(errors, all(row.get("computed_nonrecoverable_from_either_alone") is True for row in rows), "nonrecoverability boolean failed")
    require(errors, all(row.get("pass") is True for row in rows), "nonrecoverability row failed")
    require(errors, payload.get("nonrecoverability_signature_sha256") == common.signature_rows(rows), "nonrecoverability signature mismatch")


def validate_controls(errors: list[str], controls: dict[str, Any]) -> None:
    require(errors, controls.get("all_pass") is True, "cross-family controls failed")
    a_only = controls.get("A_only_perturbation", {})
    b_only = controls.get("B_only_perturbation", {})
    weld_only = controls.get("weld_only_perturbation", {})
    no_input = controls.get("no_input_no_movement", {})
    require(errors, bool(a_only.get("moved_A_internal_rows")), "A-only did not move A rows")
    require(errors, a_only.get("moved_B_internal_rows") == [], "A-only moved B-internal rows")
    require(errors, bool(a_only.get("moved_weld_rows")), "A-only did not move weld rows")
    require(errors, b_only.get("moved_A_internal_rows") == [], "B-only moved A-internal rows")
    require(errors, bool(b_only.get("moved_B_internal_rows")), "B-only did not move B rows")
    require(errors, bool(b_only.get("moved_weld_rows")), "B-only did not move weld rows")
    require(errors, weld_only.get("moved_A_internal_rows") == [], "weld-only moved A-internal rows")
    require(errors, weld_only.get("moved_B_internal_rows") == [], "weld-only moved B-internal rows")
    require(errors, bool(weld_only.get("moved_weld_rows")), "weld-only did not move weld rows")
    require(errors, no_input.get("moved_A_internal_rows") == [], "no-input moved A rows")
    require(errors, no_input.get("moved_B_internal_rows") == [], "no-input moved B rows")
    require(errors, no_input.get("moved_weld_rows") == [], "no-input moved weld rows")


def validate_smt(errors: list[str], rows: dict[str, Any]) -> None:
    require(errors, set(rows) == {"z3_weld_relation_sum", "cvc5_weld_relation_sum"}, "SMT row set mismatch")
    for name, row in rows.items():
        require(errors, row.get("ran") is True and row.get("load_bearing") is True, f"{name} did not run load-bearing")
        require(errors, row.get("verdict") == "unsat", f"{name} valid polarity must be UNSAT")
        require(errors, row.get("erased_flip_verdict") == "sat", f"{name} erased flip must be SAT")
        require(errors, row.get("perturbed_A_flip_verdict") == "sat", f"{name} perturbed A flip must be SAT")
        require(errors, row.get("perturbed_B_flip_verdict") == "sat", f"{name} perturbed B flip must be SAT")
        require(errors, row.get("bound_family_a_value") == 3, f"{name} must bind A=3")
        require(errors, row.get("bound_family_b_value") == 8, f"{name} must bind B=8")
        require(errors, row.get("bound_weld_relation_value") == 11, f"{name} must bind W=11")
        require(errors, row.get("asserted_precomputed_boolean") is False, f"{name} must not assert a precomputed boolean")
        require(errors, row.get("pass") is True, f"{name} pass flag false")


def validate_trajectory(errors: list[str], payload: dict[str, Any]) -> None:
    artifact = payload.get("trajectory_artifact", {})
    artifact_path = ROOT / artifact.get("path", "")
    sha_path = ROOT / artifact.get("sha_path", "")
    require(errors, artifact.get("sha_verified") is True, "trajectory artifact sha verification failed")
    require(errors, artifact_path.exists(), "trajectory artifact missing")
    require(errors, sha_path.exists(), "trajectory sha sidecar missing")
    if artifact_path.exists() and sha_path.exists():
        stored = common.load_json(artifact_path)
        require(errors, common.content_sha256_without_self(stored) == stored.get("content_sha256"), "trajectory content sha mismatch")
        file_digest = common.sha256_file(artifact_path)
        sidecar = sha_path.read_text(encoding="utf-8").split()[0]
        require(errors, file_digest == sidecar == artifact.get("artifact_file_sha256"), "trajectory file sha mismatch")
        require(errors, {"A+B", "WELD", "CONTROL", "SMT"} <= set(stored.get("family_scopes", [])), "trajectory scopes missing")
        rows = stored.get("step_rows", [])
        require(errors, len(rows) >= 26, "trajectory row count too small")
        require(errors, all(row.get("trajectory_step_id") for row in rows), "trajectory row missing step id")
        require(errors, all(row.get("row_step_lineage_id") for row in rows), "trajectory row missing lineage id")
        require(errors, all(row.get("row_step_class_why") for row in rows), "trajectory row missing reason")
        require(errors, all(row.get("sha_verified") is True for row in rows), "trajectory row sha flag false")


def validate_family_c_fence(errors: list[str], fence: dict[str, Any]) -> None:
    require(errors, fence.get("state_object_id") == common.EXPECTED_C_STATE_ID, "Family C fence state id mismatch")
    require(errors, fence.get("input_to_relation") is False, "Family C must not be input to relation")
    require(errors, fence.get("consumed_as") == "fence_check_citation_only", "Family C consumed as wrong role")
    require(errors, fence.get("disallowed_claims_include_ab_weld_relation") is True, "Family C fence does not cite A+B weld exclusion")
    require(errors, fence.get("pass") is True, "Family C fence failed")


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    validate_packet_files(errors)
    rebuilt = common.build_relation_object()
    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, payload.get("sim_id") == common.SIM_ID, "sim_id mismatch")
    require(errors, payload.get("mode") == common.ENGINE_MODE, "engine mode mismatch")
    require(errors, payload.get("classification") == common.CLASSIFICATION, "classification must be scratch_diagnostic")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("all_pass") is True, "top-level all_pass must be true")
    require(errors, payload.get("state_object_id") == rebuilt["state_object_id"], "state_object_id mismatch")
    require(errors, payload.get("envelope_built_with_helper") is True, "envelope helper gate missing")
    require(errors, payload.get("build_helper_path") == "scripts/build_three_engine_envelope.py", "wrong envelope helper path")
    require(errors, payload.get("builder_gates", {}).get("G_2a_idempotency_from_birth") is True, "G.2a gate missing")
    require(errors, payload.get("builder_gates", {}).get("builder_self_assessment_present") is True, "builder self-assessment gate missing")
    errors.extend(builder_audit_boundary_errors(payload, AUDIT_VERDICT))
    validate_source_pins(errors, payload)
    validate_state_objects(errors, payload, rebuilt)
    validate_coordinate_map(errors, payload)
    validate_weld_only(errors, payload)
    validate_nonrecoverability(errors, payload)
    validate_controls(errors, payload.get("cross_family_controls", {}))
    validate_smt(errors, payload.get("weld_relation_smt", {}))
    validate_family_c_fence(errors, payload.get("family_c_fence", {}))
    validate_trajectory(errors, payload)
    require(errors, payload.get("TOOL_MANIFEST") == common.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, payload.get("TOOL_INTEGRATION_DEPTH") == common.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    require(errors, payload.get("tool_intent") == common.TOOL_INTENT, "tool_intent mismatch")
    for section in ("positive", "negative", "boundary"):
        require(errors, bool(payload.get("claim_sections", {}).get(section)), f"claim_sections.{section} missing")
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
