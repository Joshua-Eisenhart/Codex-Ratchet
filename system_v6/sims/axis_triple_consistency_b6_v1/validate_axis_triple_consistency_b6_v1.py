#!/usr/bin/env python3
"""Packet-local validator for axis_triple_consistency_b6_v1."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import axis_triple_consistency_b6_v1_common as common


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
    "tests/test_axis_triple_consistency_b6_v1.py",
]


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_packet_files(errors: list[str]) -> None:
    for rel_path in REQUIRED_PACKET_FILES:
        require(errors, (SIM_DIR / rel_path).is_file(), f"missing required packet file: {rel_path}")
    text = (SIM_DIR / "build_card.md").read_text(encoding="utf-8") if (SIM_DIR / "build_card.md").is_file() else ""
    require(errors, common.SIM_ID in text, "build_card missing sim id")
    require(errors, "blocked_open_no_faithful_axis3_on_33_cell_adapter" in text, "build_card missing carrier blocker")
    require(errors, "Reading A" in text, "build_card missing Reading A adjudication")


def validate_source_locks(errors: list[str], payload: dict[str, Any]) -> None:
    pins = payload.get("source_import_audit", {}).get("parent_hash_pins", {})
    expected = {
        "v0_envelope",
        "axis0_envelope",
        "axis0_common",
        "axis3_envelope",
        "axis3_common",
        "axis3_audit",
        "axis6_envelope",
        "axis6_common",
        "axis6_audit",
        "weld_envelope",
    }
    require(errors, set(pins) == expected, "parent hash pin set mismatch")
    for key, row in pins.items():
        require(errors, row.get("exists") is True, f"{key} source lock missing file")
        require(errors, bool(row.get("sha256")), f"{key} source lock missing sha256")
    require(
        errors,
        payload.get("source_import_audit", {}).get("raw_parent_result_rows_imported_as_classification") is False,
        "raw parent rows must not be imported as classification",
    )


def validate_shared_carrier(errors: list[str], payload: dict[str, Any]) -> None:
    decision = payload.get("shared_carrier_decision", {})
    faith = payload.get("carrier_faithfulness_audit", {})
    require(errors, decision.get("status") == "blocked_open_no_faithful_axis3_on_33_cell_adapter", "wrong shared carrier decision")
    require(errors, decision.get("faithful_axis3_on_preferred_carrier") is False, "faithful Axis3 on 33-cell must be false")
    require(errors, decision.get("proxy_table_status") == "computed_contrast_only", "proxy table status mismatch")
    require(errors, faith.get("state_count") == common.EXPECTED_STATE_COUNT, "faith carrier state_count mismatch")
    require(errors, faith.get("edge_count") == common.EXPECTED_EDGE_COUNT, "faith carrier edge_count mismatch")
    require(errors, faith.get("axis0_axis6_same_carrier") is True, "Axis0/Axis6 same carrier false")
    require(
        errors,
        faith.get("faithful_33_cell_placement_possible_from_current_sources") is False,
        "faithful 33-cell placement must remain blocked",
    )
    require(
        errors,
        faith.get("carrier_adjudication", {}).get("current_repo_carrier_that_hosts_all_three_faithfully") is None,
        "must not name a current all-three faithful carrier",
    )


def validate_table(errors: list[str], payload: dict[str, Any], rebuilt: dict[str, Any]) -> None:
    table = payload.get("consistency_table", [])
    summary = payload.get("consistency_summary", {})
    require(errors, table == rebuilt["consistency_table"], "fresh consistency table rebuild drifted")
    require(errors, summary == rebuilt["consistency_summary"], "fresh summary rebuild drifted")
    require(errors, len(table) == common.EXPECTED_STATE_COUNT, "consistency table must have 33 rows")
    require(errors, summary.get("sample_total") == 33, "sample_total must be 33")
    require(errors, summary.get("agreement_count") == 16, "agreement_count must be 16 for proxy contrast")
    require(errors, summary.get("violation_count") == 17, "violation_count must be 17 for proxy contrast")
    require(errors, summary.get("nonneutral_total") == 32, "nonneutral_total must be 32")
    require(errors, summary.get("nonneutral_agreement_count") == 15, "nonneutral agreement must be 15")
    require(errors, summary.get("relation_can_fail") is True, "relation_can_fail must be true")
    require(errors, payload.get("sign_vector_sha256") == rebuilt["sign_vector_sha256"], "sign hash drifted")
    for row in table:
        require(errors, row.get("faithful_axis3_on_33_cell") is False, f"row claims faithful Axis3: {row.get('row_id')}")
        require(errors, "anti_by_construction_guard" in row, f"row missing anti guard: {row.get('row_id')}")


def validate_controls(errors: list[str], payload: dict[str, Any]) -> None:
    controls = payload.get("controls", {})
    require(
        errors,
        controls.get("convention_flip_control", {}).get("panel8_expected_target_after_flip") == "b6=+b0*b3",
        "convention flip target mismatch",
    )
    require(
        errors,
        controls.get("scrambled_b6_control", {}).get("panel8_expected_chance") == 0.5,
        "scrambled chance mismatch",
    )
    require(
        errors,
        controls.get("relation_can_fail_control", {}).get("relation_can_fail") is True,
        "relation-can-fail control false",
    )
    v0 = controls.get("v0_regression_contrast", {})
    require(errors, v0.get("matches_expected_v0_negative") is True, "v0 regression contrast mismatch")
    require(errors, v0.get("total_agreement") == 16 and v0.get("total_violations") == 32, "v0 regression counts mismatch")
    require(errors, v0.get("nonneutral_agreement") == 16 and v0.get("nonneutral_total") == 32, "v0 nonneutral counts mismatch")


def validate_panel_and_smt(errors: list[str], payload: dict[str, Any]) -> None:
    panel = payload.get("panel_anchor_checks", [])
    require(errors, len(panel) == 2, "panel anchor count must be 2")
    for row in panel:
        require(errors, row.get("computed_b6_sign") == -1, f"panel b6 mismatch: {row.get('panel_point_id')}")
        require(errors, row.get("matches_panel_expected") is True, f"panel expected mismatch: {row.get('panel_point_id')}")
        require(errors, row.get("matches_relation_expected") is True, f"panel relation mismatch: {row.get('panel_point_id')}")
    for name, row in payload.get("smt_rows", {}).items():
        require(errors, row.get("ran") is True, f"{name} did not run")
        require(errors, row.get("load_bearing") is True, f"{name} not load-bearing")
        require(errors, row.get("verdict") == "unsat", f"{name} verdict mismatch")
        require(errors, row.get("erased_flip_verdict") == "sat", f"{name} erased flip mismatch")
        require(errors, row.get("asserted_precomputed_boolean") is False, f"{name} asserted boolean")


def validate_lanes(errors: list[str], payload: dict[str, Any], rebuilt: dict[str, Any]) -> None:
    expected = common.engine_computed_values(rebuilt)
    hashes = payload.get("per_lane_sign_vector_hashes", {})
    for engine in ("julia", "jax", "pytorch"):
        lane = load(RESULT_DIR / f"{common.SIM_ID}_{engine}_results.json")
        envelope_lane = payload.get("engines", {}).get(engine, {})
        require(errors, lane.get("all_pass") is True, f"{engine} lane all_pass false")
        require(errors, envelope_lane.get("result_all_pass") is True, f"{engine} envelope result_all_pass false")
        require(errors, envelope_lane.get("reads_peer_result") is False, f"{engine} reads_peer_result must be false")
        require(errors, lane.get("per_row_sign_vector_sha256") == expected["sign_vector_sha256"], f"{engine} sign hash mismatch")
        require(errors, hashes.get(engine) == expected["sign_vector_sha256"], f"{engine} envelope sign hash mismatch")
        values = lane.get("computed_values", {})
        for key in (
            "shared_carrier_status",
            "sample_total",
            "agreement_count",
            "violation_count",
            "nonneutral_total",
            "nonneutral_agreement_count",
            "faithful_33_cell_placement_possible",
            "panel_pass_count",
            "sign_vector_sha256",
        ):
            require(errors, values.get(key) == expected[key], f"{engine}.{key} mismatch")


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    validate_packet_files(errors)
    rebuilt = common.build_axis_triple_object()
    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, payload.get("sim_id") == common.SIM_ID, "sim_id mismatch")
    require(errors, payload.get("mode") == common.ENGINE_MODE, "engine mode mismatch")
    require(errors, payload.get("classification") == common.CLASSIFICATION, "classification mismatch")
    require(errors, payload.get("claim_ceiling") == common.CLAIM_CEILING, "claim ceiling mismatch")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("all_pass") is True, "top-level all_pass must be true")
    require(errors, payload.get("state_object_id") == rebuilt["state_object_id"], "state_object_id mismatch")
    require(errors, payload.get("envelope_built_with_helper") is True, "envelope helper missing")
    require(errors, payload.get("build_helper_path") == "scripts/build_three_engine_envelope.py", "wrong build helper")
    errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))
    validate_source_locks(errors, payload)
    validate_shared_carrier(errors, payload)
    validate_table(errors, payload, rebuilt)
    validate_controls(errors, payload)
    validate_panel_and_smt(errors, payload)
    validate_lanes(errors, payload, rebuilt)
    require(errors, payload.get("TOOL_MANIFEST") == common.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, payload.get("TOOL_INTEGRATION_DEPTH") == common.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    require(errors, payload.get("tool_intent") == common.TOOL_INTENT, "tool_intent mismatch")
    require(errors, payload.get("reading_A_adjudication", {}).get("answer") == "neither_restored_nor_killed", "Reading A answer mismatch")
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
    result = {"ok": not errors, "result_json": common.rel(ENVELOPE), "errors": errors}
    common.write_json(VALIDATOR_RESULT, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
