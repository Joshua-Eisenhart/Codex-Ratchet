#!/usr/bin/env python3
"""Packet-local validator for manifold_super_sim_v2_weld."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

import manifold_super_sim_v2_weld_common as common


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
    "tests/test_manifold_super_sim_v2_weld.py",
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
    require(errors, build_card.is_file() and "manifold_super_sim_v2_weld" in build_card.read_text(encoding="utf-8"), "build_card.md was not copied")


def validate_parent_hash_pins(errors: list[str], payload: dict[str, Any]) -> None:
    pins = payload.get("source_import_audit", {}).get("parent_hash_pins", {})
    require(errors, set(pins) == {"manifold_super_sim_v0_envelope", "manifold_family_b_integrated_v0_envelope"}, "parent hash pins must name only A/B result envelopes")
    for key, row in pins.items():
        path = str(row.get("path", ""))
        require(errors, path.endswith("_envelope_results.json"), f"{key} must pin a result JSON")
        require(errors, "audit_verdict" not in path, f"{key} must not pin audit verdicts")
        require(errors, bool(row.get("sha256")), f"{key} missing sha256")
    audit_context = payload.get("source_import_audit", {}).get("audit_verdict_citation_context_hashes", {})
    require(errors, bool(audit_context), "audit verdict citation context hashes missing")
    require(errors, all("audit" in str(row.get("path", "")) for row in audit_context.values()), "audit context paths must stay separate from parent hash pins")


def validate_family_objects(errors: list[str], payload: dict[str, Any], rebuilt: dict[str, Any]) -> None:
    families = payload.get("family_state_objects", {})
    require(errors, set(families) == {"A", "B"}, "family_state_objects must contain A and B")
    a = families.get("A", {})
    b = families.get("B", {})
    require(errors, a.get("state_object_id") == common.EXPECTED_A_STATE_ID, "Family A state object id mismatch")
    require(errors, b.get("state_object_id") == common.EXPECTED_B_STATE_ID, "Family B state object id mismatch")
    require(errors, a.get("state_object_id") != b.get("state_object_id"), "A and B state objects were folded together")
    require(errors, a.get("classification") == common.CLASSIFICATION, "Family A classification drift")
    require(errors, b.get("classification") == common.CLASSIFICATION, "Family B classification drift")
    require(errors, b.get("family_a_rows_used") is False, "Family B object must not use Family A rows")
    require(errors, b.get("two_engine_rows_used") is False, "Family B object must not use two-engine rows")
    require(errors, b.get("b_scoped_projection", {}).get("axis0_leak_detected") is False, "B-scoped projection leaked axis0_*")
    require(errors, payload.get("parent_anchor_checks") == rebuilt["parent_anchor_checks"], "fresh rebuilt parent anchor checks drifted")
    require(errors, payload.get("parent_anchor_checks", {}).get("all_pass") is True, "parent anchor checks failed")


def validate_weld_map(errors: list[str], payload: dict[str, Any]) -> None:
    rows = payload.get("declared_weld_map", [])
    require(errors, len(rows) == 8, "declared weld map must contain the eight feedstock rows")
    row_ids = {row.get("row_id") for row in rows}
    require(
        errors,
        row_ids == {
            "state_object",
            "chart_quotient_language",
            "basin_partition",
            "record_conservation",
            "entropy_ledger",
            "backend_contract",
            "trajectory_lineage",
            "two_engine_64_rows",
        },
        "declared weld map row ids mismatch",
    )
    require(errors, all(row.get("pass") is True for row in rows), "not every weld-map row passed")
    relation_classes = {row.get("relation_class") for row in rows}
    require(errors, "independent" in relation_classes and "related_not_shared" in relation_classes, "weld map must distinguish independent and related rows")


def validate_weld_rows(errors: list[str], payload: dict[str, Any]) -> None:
    rows = payload.get("weld_row_table", [])
    require(errors, len(rows) == 8, "weld row table must contain W1-W8")
    require(errors, all(row.get("claim_ceiling") == common.CLASSIFICATION for row in rows), "weld rows must preserve scratch ceiling")
    require(errors, all(row.get("pass") is True for row in rows), "not every weld row passed")
    w3 = next((row for row in rows if row.get("row_id") == "W3_partition_relation"), {})
    require(errors, w3.get("family_a_value") == 3, "W3 A value must bind terminal class count 3")
    require(errors, w3.get("family_b_value") == 8, "W3 B value must bind orbit order 8")
    require(errors, w3.get("computed_relation_value") == 11, "W3 weld relation sum must be 11")
    w4 = next((row for row in rows if row.get("row_id") == "W4_record_conservation_relation"), {})
    require(errors, w4.get("computed_shared_zero_defect") is True, "W4 shared zero-defect relation failed")
    w5 = next((row for row in rows if row.get("row_id") == "W5_entropy_typing_relation"), {})
    require(errors, w5.get("forbidden_cross_type_sum_found") is False, "W5 must reject forbidden cross-type sum")
    require(errors, w5.get("product_convention_declared") is False, "W5 must not silently declare product convention")


def validate_controls(errors: list[str], controls: dict[str, Any]) -> None:
    require(errors, controls.get("all_pass") is True, "cross-family controls all_pass false")
    a_only = controls.get("A_only_perturbation_control", {})
    b_only = controls.get("B_only_perturbation_control", {})
    weld_only = controls.get("weld_only_perturbation_control", {})
    decorative = controls.get("decorative_weld_detector", {})
    stale = controls.get("stale_import_per_family", {})
    require(errors, a_only.get("family_a_anchor_moved") is True, "A-only perturbation did not move A anchor")
    require(errors, a_only.get("family_b_anchors_unchanged") is True, "A-only perturbation moved B anchors")
    require(errors, b_only.get("family_b_anchor_moved") is True, "B-only perturbation did not move B anchor")
    require(errors, b_only.get("family_a_anchors_unchanged") is True, "B-only perturbation moved A anchors")
    require(errors, weld_only.get("family_a_anchors_unchanged") is True, "weld-only perturbation moved A anchors")
    require(errors, weld_only.get("family_b_anchors_unchanged") is True, "weld-only perturbation moved B anchors")
    require(errors, weld_only.get("moved_weld_rows") == ["W3_partition_relation"], "weld-only perturbation must move only admitted W3 row")
    require(errors, decorative.get("decorative_change_detected") is False, "decorative weld detector found no-input row movement")
    require(errors, stale.get("family_a_stale_import_control_fires") is True, "Family A stale-import control did not fire")
    require(errors, stale.get("family_b_stale_import_control_fires") is True, "Family B stale-import control did not fire")


def validate_smt(errors: list[str], rows: dict[str, Any]) -> None:
    expected = {
        "z3_family_a_anchor",
        "cvc5_family_a_anchor",
        "z3_family_b_anchor",
        "cvc5_family_b_anchor",
        "z3_weld_relation",
        "cvc5_weld_relation",
    }
    require(errors, set(rows) == expected, "SMT row set mismatch")
    for name, row in rows.items():
        require(errors, row.get("ran") is True and row.get("load_bearing") is True, f"{name} did not run load-bearing")
        require(errors, row.get("verdict") == "unsat", f"{name} identity verdict must be UNSAT")
        require(errors, row.get("erased_flip_verdict") == "sat", f"{name} erased flip must be SAT")
        require(errors, row.get("asserted_precomputed_boolean") is False, f"{name} must bind values, not booleans")
    z3_rel = rows.get("z3_weld_relation", {})
    cvc5_rel = rows.get("cvc5_weld_relation", {})
    for row in (z3_rel, cvc5_rel):
        require(errors, row.get("bound_family_a_value") == 3, "weld SMT must bind Family A value")
        require(errors, row.get("bound_family_b_value") == 8, "weld SMT must bind Family B value")
        require(errors, row.get("bound_weld_relation_value") == 11, "weld SMT must bind relation value")


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
        require(errors, set(stored.get("family_scopes", [])) == {"A", "B", "WELD"}, "trajectory must include A, B, and WELD scopes")
        rows = stored.get("step_rows", [])
        require(errors, len(rows) >= 5 + 16 + 8, "trajectory row count too small for A/B/weld rows")
        require(errors, all(row.get("trajectory_step_id") for row in rows), "trajectory row missing trajectory_step_id")
        require(errors, all(row.get("row_step_lineage_id") for row in rows), "trajectory row missing row_step_lineage_id")
        require(errors, all(row.get("row_step_class_why") for row in rows), "trajectory row missing class reason")
        require(errors, all(row.get("sha_verified") is True for row in rows), "trajectory row sha verification failed")


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    validate_packet_files(errors)
    rebuilt = common.build_weld_object()
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
    require(errors, payload.get("no_builder_audit_verdict") is True, "no_builder_audit_verdict must be true")
    require(errors, payload.get("no_builder_audit_verdict_envelope_gate") is True, "no_builder_audit_verdict_envelope_gate must be true")
    require(errors, payload.get("builder_gates", {}).get("no_builder_audit_verdict") is True, "builder gate no_builder_audit_verdict false")
    errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))
    validate_parent_hash_pins(errors, payload)
    validate_family_objects(errors, payload, rebuilt)
    validate_weld_map(errors, payload)
    validate_weld_rows(errors, payload)
    validate_controls(errors, payload.get("cross_family_controls", {}))
    validate_smt(errors, payload.get("weld_smt_rows", {}))
    validate_trajectory(errors, payload)
    require(errors, payload.get("TOOL_MANIFEST") == common.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, payload.get("TOOL_INTEGRATION_DEPTH") == common.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    require(errors, payload.get("tool_intent") == common.TOOL_INTENT, "tool_intent mismatch")
    require(errors, payload.get("TOOL_INTENT_MATRIX", {}).get("build_three_engine_envelope"), "TOOL_INTENT_MATRIX missing envelope helper row")
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
