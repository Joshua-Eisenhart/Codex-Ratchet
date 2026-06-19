#!/usr/bin/env python3
"""Packet-local validator for axis_triple_consistency_b6_v0."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

import axis_triple_consistency_b6_v0_common as common


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
    "tests/test_axis_triple_consistency_b6_v0.py",
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
    text = build_card.read_text(encoding="utf-8") if build_card.is_file() else ""
    require(errors, common.SIM_ID in text, "build_card.md missing sim id")
    require(errors, "b_6 = -b_0 b_3" in text, "build_card.md missing scaffold quote")
    require(errors, common.CLAIM_CEILING in text, "build_card.md missing claim ceiling")


def validate_source_locks(errors: list[str], payload: dict[str, Any]) -> None:
    audit = payload.get("source_import_audit", {})
    pins = audit.get("parent_hash_pins", {})
    expected = {
        "axis0_envelope",
        "axis0_common",
        "axis3_envelope",
        "axis3_common",
        "axis6_envelope",
        "axis6_common",
        "geo_s4_envelope",
        "geo_s5_envelope",
    }
    require(errors, set(pins) == expected, "parent hash pin set mismatch")
    for key, row in pins.items():
        require(errors, row.get("exists") is True, f"{key} source lock missing file")
        require(errors, bool(row.get("sha256")), f"{key} source lock missing sha256")
    require(errors, audit.get("raw_parent_result_rows_imported") is False, "must not import raw parent result rows as classifications")


def validate_table(errors: list[str], payload: dict[str, Any], rebuilt: dict[str, Any]) -> None:
    summary = payload.get("consistency_summary", {})
    require(errors, payload.get("consistency_table") == rebuilt["consistency_table"], "fresh consistency table rebuild drifted")
    require(errors, payload.get("violation_rows") == rebuilt["violation_rows"], "fresh violation rows rebuild drifted")
    require(errors, summary == rebuilt["consistency_summary"], "fresh summary rebuild drifted")
    require(errors, summary.get("sample_total") == 48, "sample_total must be 48")
    require(errors, summary.get("agreement_count") == 16, "agreement_count must be 16")
    require(errors, summary.get("violation_count") == 32, "violation_count must be 32")
    require(errors, math.isclose(summary.get("agreement_fraction", -1), 16 / 48), "agreement fraction mismatch")
    require(errors, summary.get("nonneutral_total") == 32, "nonneutral_total must be 32")
    require(errors, summary.get("nonneutral_agreement_count") == 16, "nonneutral agreement must be 16")
    require(errors, len(payload.get("consistency_table", [])) == 48, "consistency table length mismatch")
    require(errors, len(payload.get("violation_rows", [])) == 32, "violation rows length mismatch")
    for row in payload.get("consistency_table", []):
        require(errors, "b0_sign" in row and "b3_sign" in row and "computed_b6_sign" in row, f"row missing sign fields: {row.get('sample_id')}")
        require(errors, row.get("anti_by_construction_guard"), f"row missing anti-by-construction guard: {row.get('sample_id')}")


def validate_panel(errors: list[str], payload: dict[str, Any], rebuilt: dict[str, Any]) -> None:
    panel = payload.get("panel_point_checks", [])
    require(errors, panel == rebuilt["panel_point_checks"], "panel checks rebuild drifted")
    require(errors, len(panel) == 2, "panel must have two rows")
    for row in panel:
        require(errors, row.get("computed_b6_sign") == -1, f"panel computed b6 mismatch: {row.get('panel_point_id')}")
        require(errors, row.get("panel_expected_b6") == -1, f"panel expected b6 mismatch: {row.get('panel_point_id')}")
        require(errors, row.get("matches_panel_expected") is True, f"panel row did not match expected: {row.get('panel_point_id')}")
        require(errors, row.get("matches_relation_expected") is True, f"panel row did not match relation: {row.get('panel_point_id')}")


def validate_controls(errors: list[str], payload: dict[str, Any]) -> None:
    controls = payload.get("controls", {})
    require(errors, controls.get("convention_flip_control", {}).get("all_flipped_expected_equals_positive_product") is True, "convention flip target did not flip")
    scrambled = controls.get("scrambled_b6_control", {})
    require(errors, scrambled.get("agreement_fraction_nonzero_expected", 1.0) <= 0.75, "scrambled-b6 control too strong")
    require(errors, controls.get("commuting_control", {}).get("all_neutral") is True, "commuting control not all neutral")
    require(errors, controls.get("commuting_control", {}).get("neutral_count") == 48, "commuting neutral count must be 48")
    require(errors, controls.get("relation_can_fail_control", {}).get("violation_count") == 32, "relation-can-fail control mismatch")
    require(errors, controls.get("relation_can_fail_control", {}).get("relation_can_fail") is True, "relation-can-fail control false")
    require(errors, payload.get("independence_reminder_row") == common.INDEPENDENCE_REMINDER_ROW, "independence reminder row mismatch")


def validate_smt(errors: list[str], payload: dict[str, Any]) -> None:
    rows = payload.get("smt_rows", {})
    require(errors, set(rows) == {"z3_computed_table", "cvc5_computed_table"}, "SMT row set mismatch")
    for name, row in rows.items():
        require(errors, row.get("ran") is True, f"{name} did not run")
        require(errors, row.get("load_bearing") is True, f"{name} not load-bearing")
        require(errors, row.get("verdict") == "unsat", f"{name} real verdict must be unsat")
        require(errors, row.get("erased_flip_verdict") == "sat", f"{name} erased flip must be sat")
        require(errors, row.get("asserted_precomputed_boolean") is False, f"{name} must not assert a precomputed boolean")
        require(errors, row.get("bound_agreement_count") == 16, f"{name} agreement bind mismatch")
        require(errors, row.get("bound_violation_count") == 32, f"{name} violation bind mismatch")


def validate_lanes(errors: list[str], payload: dict[str, Any], rebuilt: dict[str, Any]) -> None:
    expected = common.engine_computed_values(rebuilt)
    for engine in ("julia", "jax", "pytorch"):
        lane = load(RESULT_DIR / f"{common.SIM_ID}_{engine}_results.json")
        envelope_lane = payload.get("engines", {}).get(engine, {})
        require(errors, lane.get("all_pass") is True, f"{engine} lane all_pass false")
        require(errors, envelope_lane.get("result_all_pass") is True, f"{engine} envelope result_all_pass false")
        require(errors, envelope_lane.get("reads_peer_result") is False, f"{engine} reads_peer_result must be false")
        values = lane.get("computed_values", {})
        for key in ("sample_total", "agreement_count", "violation_count", "nonneutral_total", "nonneutral_agreement_count"):
            require(errors, values.get(key) == expected[key], f"{engine}.{key} mismatch")
        panel = lane.get("panel_point_checks", [])
        require(errors, len(panel) == 2 and all(row.get("computed_b6_sign") == -1 for row in panel), f"{engine} panel check failed")


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    validate_packet_files(errors)
    rebuilt = common.build_axis_triple_object()
    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, payload.get("sim_id") == common.SIM_ID, "sim_id mismatch")
    require(errors, payload.get("mode") == common.ENGINE_MODE, "engine mode mismatch")
    require(errors, payload.get("classification") == common.CLASSIFICATION, "classification must be scratch_diagnostic")
    require(errors, payload.get("claim_ceiling") == common.CLAIM_CEILING, "claim ceiling mismatch")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("all_pass") is True, "top-level all_pass must be true")
    require(errors, payload.get("state_object_id") == rebuilt["state_object_id"], "state object id mismatch")
    require(errors, payload.get("envelope_built_with_helper") is True, "envelope helper gate missing")
    require(errors, payload.get("build_helper_path") == "scripts/build_three_engine_envelope.py", "wrong envelope helper path")
    require(errors, payload.get("no_builder_audit_verdict") is True, "no_builder_audit_verdict must be true")
    require(errors, payload.get("no_builder_audit_verdict_envelope_gate") is True, "no_builder_audit_verdict_envelope_gate must be true")
    require(errors, payload.get("builder_gates", {}).get("no_builder_audit_verdict") is True, "builder gate false")
    errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))
    validate_source_locks(errors, payload)
    validate_table(errors, payload, rebuilt)
    validate_panel(errors, payload, rebuilt)
    validate_controls(errors, payload)
    validate_smt(errors, payload)
    validate_lanes(errors, payload, rebuilt)
    require(errors, payload.get("TOOL_MANIFEST") == common.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, payload.get("TOOL_INTEGRATION_DEPTH") == common.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    require(errors, payload.get("tool_intent") == common.TOOL_INTENT, "tool_intent mismatch")
    require(errors, payload.get("TOOL_INTENT_MATRIX", {}).get("build_three_engine_envelope"), "TOOL_INTENT_MATRIX missing envelope helper row")
    for section in ("positive", "negative", "boundary"):
        require(errors, bool(payload.get("claim_sections", {}).get(section)), f"claim_sections.{section} missing")
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
