#!/usr/bin/env python3
"""Packet-local validator for discrete_axis0_field_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import discrete_axis0_field_v0_common as common


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
    "tests/test_discrete_axis0_field_v0.py",
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
    require(errors, "discrete_axis0_field_v0" in text, "build_card.md missing packet id")
    require(errors, "axis_readout_candidate_only" in text, "build_card.md missing claim ceiling")


def validate_ceiling(errors: list[str], payload: dict[str, Any]) -> None:
    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, payload.get("sim_id") == common.SIM_ID, "sim_id mismatch")
    require(errors, payload.get("mode") == common.ENGINE_MODE, "engine mode mismatch")
    require(errors, payload.get("classification") == common.CLASSIFICATION, "classification must be scratch_diagnostic")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("claim_ceiling") == common.CLAIM_CEILING, "claim ceiling mismatch")
    require(errors, payload.get("all_pass") is True, "top-level all_pass must be true")
    for banned in ("axis admission", "bridge admission", "physics", "canonical Axis-0", "manifold promotion"):
        require(errors, banned in payload.get("disallowed_claims", []), f"missing disallowed claim: {banned}")


def validate_carrier_and_gradients(errors: list[str], payload: dict[str, Any]) -> None:
    rebuilt = common.build_axis0_object()
    require(errors, payload.get("state_object_id") == rebuilt["state_object_id"], "state_object_id mismatch")
    carrier = payload.get("carrier", {})
    require(errors, carrier.get("state_count") == common.EXPECTED_STATE_COUNT, "carrier state_count must be 33")
    require(errors, carrier.get("edge_count") == common.EXPECTED_EDGE_COUNT, "carrier edge_count must be 198")
    require(errors, carrier.get("family_a_commit") == common.PARENT_COMMITS["manifold_super_sim_v0"], "Family A commit pin mismatch")
    require(errors, carrier.get("weld_commit") == common.PARENT_COMMITS["manifold_super_sim_v2_weld"], "weld commit pin mismatch")
    field_by_cell = {row["cell_id"]: row["phi"] for row in payload.get("readout_table", [])}
    require(errors, len(field_by_cell) == common.EXPECTED_STATE_COUNT, "readout_table must have 33 rows")
    for row in payload.get("gradient_table", []):
        expected = common.sub_fraction(field_by_cell[row["dst"]], field_by_cell[row["src"]])
        require(errors, expected == row["directed_gradient_phi"], f"gradient recompute mismatch edge {row.get('edge_id')}")
    summary = payload.get("gradient_summary", {})
    require(errors, summary.get("edge_count") == common.EXPECTED_EDGE_COUNT, "gradient edge_count mismatch")
    require(errors, summary.get("nonzero_gradient_edges", 0) > 0, "nonzero gradients missing")
    require(errors, payload.get("field_formula", {}).get("denominator") == common.FIELD_DENOMINATOR, "field denominator mismatch")


def validate_controls(errors: list[str], controls: dict[str, Any]) -> None:
    for name, row in controls.items():
        require(errors, row.get("fired") is True, f"control did not fire: {name}")
    require(errors, controls.get("constant_field", {}).get("all_degenerate_no_polarity") is True, "constant control not degenerate")
    require(errors, controls.get("constant_field", {}).get("nonzero_gradient_edges") == 0, "constant control has nonzero gradients")
    require(errors, controls.get("shuffled_adjacency", {}).get("edge_count_preserved") is True, "shuffle did not preserve edge count")
    require(errors, controls.get("reversed_orientation", {}).get("all_edge_gradients_flip_sign") is True, "reverse control did not flip all gradients")
    require(errors, controls.get("label_shuffle", {}).get("label_only_reproduction_pass") is False, "label-only branch passed")
    require(errors, controls.get("frozen_factor_projection", {}).get("partition_majority_accuracy", 1.0) < 1.0, "partition projection recovered A0")


def validate_independence_and_stability(errors: list[str], payload: dict[str, Any]) -> None:
    stability = payload.get("stability_under_committed_dynamics", {})
    require(errors, stability.get("edge_count") == common.EXPECTED_EDGE_COUNT, "stability edge count mismatch")
    require(errors, stability.get("stable_edge_count", 0) > 0, "readout changes under every step")
    require(errors, stability.get("changed_edge_count", 0) > 0, "readout has no changed edge")
    require(errors, stability.get("all_changed_every_step") is False, "all_changed_every_step must be false")
    independence = payload.get("three_polarities_independence", {})
    require(errors, independence.get("axis0_not_recoverable_from_axis3_placement") is True, "A0 recovered from A3 placement")
    require(errors, independence.get("axis0_not_recoverable_from_axis6_order") is True, "A0 recovered from A6 order")
    require(errors, independence.get("axis3_witness_pair", {}).get("same_axis3_style_placement_key") is True, "A3 witness missing")
    require(errors, independence.get("axis6_witness_pair", {}).get("same_axis6_style_order_key") is True, "A6 witness missing")


def validate_smt(errors: list[str], rows: dict[str, Any]) -> None:
    require(errors, set(rows) == {"z3", "cvc5"}, "SMT row set mismatch")
    for name, row in rows.items():
        require(errors, row.get("ran") is True and row.get("load_bearing") is True, f"{name} did not run load-bearing")
        require(errors, row.get("verdict") == "unsat", f"{name} identity verdict must be UNSAT")
        require(errors, row.get("erased_flip_verdict") == "sat", f"{name} erased flip must be SAT")
        require(errors, row.get("asserted_precomputed_boolean") is False, f"{name} must bind values, not booleans")
        bound = row.get("bound_values", {})
        require(errors, bound.get("stable_edge_count", 0) > 0, f"{name} did not bind stable count")
        require(errors, bound.get("nonzero_gradient_edges", 0) > 0, f"{name} did not bind nonzero gradients")


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


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    validate_packet_files(errors)
    validate_ceiling(errors, payload)
    validate_carrier_and_gradients(errors, payload)
    validate_controls(errors, payload.get("controls", {}))
    validate_independence_and_stability(errors, payload)
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
