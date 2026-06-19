#!/usr/bin/env python3
"""Packet-local validator for discrete_axis3_placement_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import discrete_axis3_placement_v0_common as common


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
    "tests/test_discrete_axis3_placement_v0.py",
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


def validate_ceiling(errors: list[str], payload: dict[str, Any]) -> None:
    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, payload.get("sim_id") == common.SIM_ID, "sim_id mismatch")
    require(errors, payload.get("classification") == common.CLASSIFICATION, "classification must be scratch_diagnostic")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("claim_ceiling") == common.CLAIM_CEILING, "claim ceiling mismatch")
    require(errors, payload.get("all_pass") is True, "top-level all_pass must be true")
    for banned in ("canonical Axis-3", "Axis-0 response replacement", "Axis-6 precedence replacement", "physics"):
        require(errors, banned in payload.get("disallowed_claims", []), f"missing disallowed claim: {banned}")


def validate_placement(errors: list[str], payload: dict[str, Any]) -> None:
    rebuilt = common.build_axis3_object()
    require(errors, payload.get("state_object_id") == rebuilt["state_object_id"], "state_object_id mismatch")
    table = payload.get("placement_table", [])
    require(errors, len(table) == 48, "placement table must have 48 nondegenerate rows")
    counts = payload.get("placement_counts", {})
    require(errors, counts.get("axis3_minus_fiber_placed_gamma_in") == 24, "fiber placement count mismatch")
    require(errors, counts.get("axis3_plus_base_placed_gamma_out") == 24, "base placement count mismatch")
    for row in table:
        if row["pinned_family_formula"] == "gamma_in":
            require(errors, row["density_stationary"] is True, f"gamma_in not density-stationary: {row['loop_id']}")
            require(errors, row["placement_sign"] == -1, f"gamma_in wrong placement sign: {row['loop_id']}")
        if row["pinned_family_formula"] == "gamma_out":
            require(errors, row["density_traversing"] is True, f"gamma_out not density-traversing: {row['loop_id']}")
            require(errors, row["horizontal_condition_A_dot_gamma_zero"] is True, f"gamma_out not horizontal: {row['loop_id']}")
            require(errors, row["placement_sign"] == 1, f"gamma_out wrong placement sign: {row['loop_id']}")


def validate_controls(errors: list[str], controls: dict[str, Any]) -> None:
    for name, row in controls.items():
        require(errors, row.get("fired") is True, f"control did not fire: {name}")
    require(errors, controls.get("placement_degenerate_control", {}).get("neutral_count") == 8, "degenerate neutral count mismatch")
    shuffle = controls.get("shuffled_connection_control", {})
    require(errors, shuffle.get("changed_count") == shuffle.get("gamma_out_rows_checked") == 24, "shuffled connection did not change all gamma_out rows")
    require(errors, controls.get("falsifier_reachability", {}).get("classification_under_failure") != "axis3_plus_base_placed_gamma_out", "falsifier still classified as base")
    frozen = controls.get("frozen_factor_projection", {})
    require(errors, frozen.get("placement_not_recovered") is True, "frozen factor projection recovered placement")


def validate_independence_and_stability(errors: list[str], payload: dict[str, Any]) -> None:
    stability = payload.get("stability_under_committed_dynamics", {})
    require(errors, stability.get("stable_edge_count", 0) > 0, "readout dynamics changed under every step")
    require(errors, stability.get("changed_edge_count", 0) > 0, "readout dynamics fully frozen")
    require(errors, stability.get("all_stable_every_step") is False, "all_stable_every_step must be false")
    require(errors, stability.get("all_changed_every_step") is False, "all_changed_every_step must be false")
    independence = payload.get("independence_rows_vs_axis0", {})
    require(errors, independence.get("placement_not_recoverable_from_axis0_response") is True, "placement recovered from Axis-0")
    require(errors, independence.get("axis0_response_not_recoverable_from_placement") is True, "Axis-0 recovered from placement")
    require(errors, bool(independence.get("same_axis0_response_different_placement_witness")), "missing same-A0/different-placement witness")
    require(errors, bool(independence.get("same_placement_different_axis0_response_witness")), "missing same-placement/different-A0 witness")


def validate_smt(errors: list[str], rows: dict[str, Any]) -> None:
    require(errors, set(rows) == {"z3", "cvc5"}, "SMT row set mismatch")
    for name, row in rows.items():
        require(errors, row.get("ran") is True and row.get("load_bearing") is True, f"{name} did not run load-bearing")
        require(errors, row.get("verdict") == "unsat", f"{name} identity verdict must be UNSAT")
        require(errors, row.get("erased_flip_verdict") == "sat", f"{name} erased flip must be SAT")
        require(errors, row.get("asserted_precomputed_boolean") is False, f"{name} must bind values, not booleans")
        bound = row.get("bound_values", {})
        require(errors, bound.get("fiber_count", 0) > 0 and bound.get("base_count", 0) > 0, f"{name} missing placement counts")


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
    validate_placement(errors, payload)
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
    result = {"ok": not errors, "result_json": common.rel(ENVELOPE), "errors": errors}
    common.write_json(VALIDATOR_RESULT, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
