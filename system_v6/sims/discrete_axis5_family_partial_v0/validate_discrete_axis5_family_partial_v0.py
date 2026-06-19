#!/usr/bin/env python3
"""Packet-local validator for discrete_axis5_family_partial_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import discrete_axis5_family_partial_v0_common as common


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
    text = (SIM_DIR / "build_card.md").read_text(encoding="utf-8") if (SIM_DIR / "build_card.md").exists() else ""
    require(errors, common.SIM_ID in text, "build_card.md missing packet id")
    require(errors, common.CLAIM_CEILING in text, "build_card.md missing claim ceiling")
    require(errors, "PARTIAL" in text, "build_card.md missing PARTIAL boundary")


def validate_ceiling(errors: list[str], payload: dict[str, Any]) -> None:
    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, payload.get("sim_id") == common.SIM_ID, "sim_id mismatch")
    require(errors, payload.get("mode") == common.ENGINE_MODE, "engine mode mismatch")
    require(errors, payload.get("classification") == common.CLASSIFICATION, "classification must be scratch_diagnostic")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("claim_ceiling") == common.CLAIM_CEILING, "claim ceiling mismatch")
    require(errors, payload.get("partial_scope") == common.PARTIAL_SCOPE, "partial scope mismatch")
    require(errors, payload.get("all_pass") is True, "top-level all_pass must be true")
    for banned in (
        "axis admission",
        "Axis-5 completion",
        "axis5_axis6_substage_product",
        "Matrix64 completion",
        "label drift resolution",
        "bridge admission",
        "physics",
    ):
        require(errors, banned in payload.get("disallowed_claims", []), f"missing disallowed claim: {banned}")


def validate_family_table(errors: list[str], payload: dict[str, Any]) -> None:
    rebuilt = common.build_axis5_object()
    require(errors, payload.get("state_object_id") == rebuilt["state_object_id"], "state_object_id mismatch")
    carrier = payload.get("carrier", {})
    require(errors, carrier.get("state_count") == common.EXPECTED_STATE_COUNT, "carrier state_count must be 33")
    table = payload.get("axis5_family_table", [])
    require(errors, len(table) == common.EXPECTED_TABLE_ROWS, "axis5 family table must have 132 rows")
    require(errors, common.stable_sha256(table) == common.stable_sha256(rebuilt["axis5_family_table"]), "family table recompute mismatch")
    counts = payload.get("family_counts", {})
    require(errors, counts.get("dephasing_gradient_side") == 66, "dephasing row count mismatch")
    require(errors, counts.get("unitary_hamiltonian_side") == 66, "unitary row count mismatch")
    require(errors, counts.get("boundary") == 0, "primary table boundary rows must be zero")
    for row in table:
        require(errors, row.get("classification_source") == "computed_witnesses_not_label_resolution", "row classification source drift")
        require(errors, row.get("substage_product_built") is False, "row must not build substage product")


def validate_controls_and_blockers(errors: list[str], payload: dict[str, Any]) -> None:
    controls = payload.get("controls", {})
    for name, row in controls.items():
        require(errors, row.get("fired") is True, f"control did not fire: {name}")
    require(
        errors,
        controls.get("weak_dephasing_near_unitary_boundary", {}).get("classification") == "boundary",
        "weak dephasing boundary control failed",
    )
    require(errors, controls.get("shuffled_order", {}).get("family_counts_preserved") is True, "shuffled-order control failed")
    require(errors, controls.get("commuting_controls", {}).get("Ti_Fe_commutator_neutral") is True, "commuting Ti/Fe failed")
    require(errors, controls.get("pure_controls", {}).get("unitary_purity_preservation") is True, "pure/unitary control failed")

    status = payload.get("substage_product_status", {})
    require(errors, status.get("status") == "blocked", "substage product status must be blocked")
    require(errors, status.get("substage_product_built") is False, "substage product must not be built")
    blocked = payload.get("substage_product_rows", [])
    require(errors, len(blocked) == 4, "blocked substage product rows must cover 2x2 product")
    for row in blocked:
        require(errors, row.get("status") == "blocked_not_built", "substage product row status drift")
        require(
            errors,
            row.get("reason") == "substage_transition_convention_not_owner_pinned",
            "substage product block reason drift",
        )
    require(errors, payload.get("label_drift", {}).get("status") == "unresolved", "label drift must stay unresolved")


def validate_independence(errors: list[str], payload: dict[str, Any]) -> None:
    rows = {row.get("row_id"): row for row in payload.get("independence_rows_vs_axes0_6", [])}
    required = [
        "axis5_not_recoverable_from_axis0_response",
        "axis0_response_not_recoverable_from_axis5",
        "axis5_not_recoverable_from_axis6_precedence",
        "axis6_precedence_not_recoverable_from_axis5",
        "operator_label_identity_leak_report",
    ]
    for row_id in required:
        require(errors, row_id in rows, f"missing independence row: {row_id}")
        require(errors, rows.get(row_id, {}).get("pass") is True, f"independence row did not pass: {row_id}")
    leak = rows.get("operator_label_identity_leak_report", {})
    require(errors, leak.get("identity_leak_detected") is True, "operator-label identity leak must be reported")
    require(errors, leak.get("identity_leak_excluded") is True, "operator-label identity leak must be excluded")


def validate_smt(errors: list[str], rows: dict[str, Any]) -> None:
    require(errors, set(rows) == {"z3", "cvc5"}, "SMT row set mismatch")
    for name, row in rows.items():
        require(errors, row.get("ran") is True and row.get("load_bearing") is True, f"{name} did not run load-bearing")
        require(errors, row.get("verdict") == "unsat", f"{name} verdict must be UNSAT")
        require(errors, row.get("erased_flip_verdict") == "sat", f"{name} erased flip must be SAT")
        require(errors, row.get("asserted_precomputed_boolean") is False, f"{name} must bind values, not booleans")


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
    require(errors, payload.get("lane_comparison", {}).get("all_lanes_same_counts") is True, "lane count comparison mismatch")


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    validate_packet_files(errors)
    validate_ceiling(errors, payload)
    validate_family_table(errors, payload)
    validate_controls_and_blockers(errors, payload)
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
