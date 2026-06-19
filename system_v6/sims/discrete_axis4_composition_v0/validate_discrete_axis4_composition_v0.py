#!/usr/bin/env python3
"""Packet-local validator for discrete_axis4_composition_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import discrete_axis4_composition_v0_common as common


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
    "tests/test_discrete_axis4_composition_v0.py",
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
    require(errors, "tau_R = 1" in text and "tau_C = 1" in text, "build_card.md missing tau pins")


def validate_ceiling(errors: list[str], payload: dict[str, Any]) -> None:
    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, payload.get("sim_id") == common.SIM_ID, "sim_id mismatch")
    require(errors, payload.get("mode") == common.ENGINE_MODE, "engine mode mismatch")
    require(errors, payload.get("classification") == common.CLASSIFICATION, "classification must be scratch_diagnostic")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("claim_ceiling") == common.CLAIM_CEILING, "claim ceiling mismatch")
    require(errors, payload.get("all_pass") is True, "top-level all_pass must be true")
    for banned in ("axis admission", "Axis-6 precedence claim", "bridge admission", "physics", "canonical Axis-4 readout"):
        require(errors, banned in payload.get("disallowed_claims", []), f"missing disallowed claim: {banned}")


def validate_carrier_pins_and_table(errors: list[str], payload: dict[str, Any]) -> None:
    rebuilt = common.build_axis4_object()
    require(errors, payload.get("state_object_id") == rebuilt["state_object_id"], "state_object_id mismatch")
    carrier = payload.get("carrier", {})
    require(errors, carrier.get("state_count") == common.EXPECTED_STATE_COUNT, "carrier state_count must be 33")
    require(errors, carrier.get("edge_count") == common.EXPECTED_EDGE_COUNT, "carrier edge_count must be 198")
    require(errors, carrier.get("generator_names") == rebuilt["carrier"]["generator_names"], "carrier generators mismatch")
    pinning = payload.get("pinning", {})
    require(errors, pinning.get("source", {}).get("pin_sha256") == common.S4_PIN_SHA256, "S4 pin hash mismatch")
    require(errors, pinning.get("R", {}).get("id") == "S4:R_x", "R pin id mismatch")
    require(errors, pinning.get("C", {}).get("id") == "S4:D_z", "C pin id mismatch")
    require(errors, pinning.get("R", {}).get("tau") == 1.0, "tau_R mismatch")
    require(errors, pinning.get("C", {}).get("tau") == 1.0, "tau_C mismatch")
    require(errors, pinning.get("R", {}).get("max_abs_delta_vs_committed") == 0.0, "R_x exponential pin mismatch")
    require(errors, pinning.get("C", {}).get("max_abs_delta_vs_committed", 1.0) <= 1.0e-12, "D_z exponential pin mismatch")
    table = payload.get("axis4_readout_table", [])
    require(errors, len(table) == common.EXPECTED_STATE_COUNT, "axis4 table must have 33 rows")
    require(errors, common.stable_sha256(table) == common.stable_sha256(rebuilt["axis4_readout_table"]), "axis4 table recompute mismatch")
    counts = payload.get("axis4_counts", {})
    require(errors, counts.get("positive") == 14, "positive Axis-4 count mismatch")
    require(errors, counts.get("negative") == 14, "negative Axis-4 count mismatch")
    require(errors, counts.get("neutral") == 5, "neutral Axis-4 count mismatch")
    require(errors, counts.get("nonneutral") == 28, "nonneutral Axis-4 count mismatch")


def validate_controls(errors: list[str], controls: dict[str, Any]) -> None:
    require(errors, controls.get("commuting_pair_all_neutral", {}).get("all_cells_neutral") is True, "commuting control not all-neutral")
    require(errors, controls.get("commuting_pair_all_neutral", {}).get("neutral_count") == common.EXPECTED_STATE_COUNT, "commuting neutral count mismatch")
    leading = controls.get("panel7_leading_order_2ue_commutator", {})
    require(errors, leading.get("pass") is True, "panel7 leading-order control failed")
    require(errors, leading.get("relative_error", 1.0) < 5.0e-4, "panel7 leading-order relative error too large")
    shuffled = controls.get("shuffled_order_not_primary", {})
    require(errors, shuffled.get("pass") is True, "shuffled-order control failed")
    require(errors, shuffled.get("changed_count", 0) > 0, "shuffled-order did not change the sign vector")
    axis6 = controls.get("axis4_vs_axis6_discriminator", {})
    require(errors, axis6.get("pass") is True, "axis6-vs-axis4 discriminator failed")
    require(errors, axis6.get("axis6_predicts_axis4_majority_accuracy", 1.0) < 1.0, "axis6 perfectly predicts axis4")


def validate_independence(errors: list[str], payload: dict[str, Any]) -> None:
    require(errors, payload.get("axis0_alignment", {}).get("same_carrier") is True, "Axis0 carrier mismatch")
    require(errors, payload.get("axis6_alignment", {}).get("same_carrier") is True, "Axis6 carrier mismatch")
    rows = {row.get("row_id"): row for row in payload.get("carrier_honest_independence_matrix", [])}
    for row_id in (
        "axis4_not_recoverable_from_axis0_response",
        "axis0_response_not_recoverable_from_axis4",
        "axis4_not_recoverable_from_axis6_precedence",
        "axis6_precedence_not_recoverable_from_axis4",
        "best_predictor_full_0_4_6_feature_report",
    ):
        require(errors, row_id in rows, f"missing independence row: {row_id}")
        require(errors, rows.get(row_id, {}).get("pass") is True, f"independence row did not pass: {row_id}")
    best = rows.get("best_predictor_full_0_4_6_feature_report", {})
    require(errors, best.get("identity_leak_detected") is True, "identity leak caveat not reported")
    require(errors, best.get("identity_leak_excluded_best_accuracy", 1.0) < 1.0, "identity-leak-excluded predictor recovered axis4")
    require(errors, payload.get("axis6_alignment", {}).get("axis6_readout_parent_commit") == "b6fafc67f", "axis6 parent commit mismatch")


def validate_smt(errors: list[str], rows: dict[str, Any]) -> None:
    require(errors, set(rows) == {"z3", "cvc5"}, "SMT row set mismatch")
    for name, row in rows.items():
        require(errors, row.get("ran") is True and row.get("load_bearing") is True, f"{name} did not run load-bearing")
        require(errors, row.get("verdict") == "unsat", f"{name} identity verdict must be UNSAT")
        require(errors, row.get("erased_flip_verdict") == "sat", f"{name} erased flip must be SAT")
        require(errors, row.get("asserted_precomputed_boolean") is False, f"{name} must bind values, not booleans")
        bound = row.get("bound_values", {})
        require(errors, bound.get("positive") == 14, f"{name} did not bind positive count")
        require(errors, bound.get("negative") == 14, f"{name} did not bind negative count")


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
    for engine in ("julia", "jax", "pytorch"):
        lane = load(RESULT_DIR / f"{common.SIM_ID}_{engine}_results.json")
        require(errors, lane.get("all_pass") is True, f"{engine} lane all_pass false")
        require(errors, payload.get("engines", {}).get(engine, {}).get("result_all_pass") is True, f"{engine} envelope result_all_pass false")
        require(errors, payload.get("engines", {}).get(engine, {}).get("reads_peer_result") is False, f"{engine} reads_peer_result must be false")
    comparison = payload.get("lane_comparison", {})
    require(errors, comparison.get("all_lanes_same_counts") is True, "lane count comparison mismatch")


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    validate_packet_files(errors)
    validate_ceiling(errors, payload)
    validate_carrier_pins_and_table(errors, payload)
    validate_controls(errors, payload.get("controls", {}))
    validate_independence(errors, payload)
    validate_smt(errors, payload.get("smt_rows", {}))
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
    }
    common.write_json(VALIDATOR_RESULT, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
