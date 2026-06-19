#!/usr/bin/env python3
"""Packet-local validator for carnot_szilard_basin_cycle_v0."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

import carnot_szilard_basin_cycle_v0_common as common


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
    f"{common.SIM_ID}_envelope_spec.json",
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
    for rel_path in [
        f"results/{common.SIM_ID}_julia_results.json",
        f"results/{common.SIM_ID}_jax_results.json",
        f"results/{common.SIM_ID}_pytorch_results.json",
        f"results/{common.SIM_ID}_envelope_results.json",
    ]:
        require(errors, (SIM_DIR / rel_path).is_file(), f"missing required result file: {rel_path}")
    build_card = SIM_DIR / "build_card.md"
    text = build_card.read_text(encoding="utf-8") if build_card.exists() else ""
    require(errors, common.SIM_ID in text, "build_card.md missing packet id")
    require(errors, "NO git add/commit" in text, "build_card.md missing no-git boundary")
    require(errors, "boundaries 1 and 4 stay open" in text, "build_card.md missing open boundary clause")


def validate_ceiling(errors: list[str], payload: dict[str, Any]) -> None:
    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, payload.get("sim_id") == common.SIM_ID, "sim_id mismatch")
    require(errors, payload.get("mode") == common.ENGINE_MODE, "engine mode mismatch")
    require(errors, payload.get("classification") == common.CLASSIFICATION, "classification must be scratch_diagnostic")
    require(errors, payload.get("row_classification") == common.ROW_CLASSIFICATION, "row classification must be classical_baseline")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("claim_ceiling") == common.CLAIM_CEILING, "claim ceiling mismatch")
    require(errors, payload.get("all_pass") is True, "top-level all_pass must be true")
    for banned in (
        "physics",
        "bridge admission",
        "M(C) admission",
        "Axis0 admission",
        "engine placement",
        "QCA/index claim",
        "manifold admission",
        "thermodynamic heat/work claim on basin carrier",
    ):
        require(errors, banned in payload.get("disallowed_claims", []), f"missing disallowed claim: {banned}")


def validate_cycle_rows(errors: list[str], payload: dict[str, Any]) -> None:
    rebuilt = common.build_packet_object()
    require(
        errors,
        common.stable_sha256(payload.get("basin_cycle_rows", [])) == common.stable_sha256(rebuilt["basin_cycle_rows"]),
        "basin_cycle_rows recompute mismatch",
    )
    rows = payload.get("basin_cycle_rows", [])
    require(errors, {row.get("dof_id") for row in rows} == set(common.RETURN_DOF_IDS), "RETURN DoF row set mismatch")
    for row in rows:
        require(errors, row.get("row_classification") == common.ROW_CLASSIFICATION, f"{row.get('dof_id')} row classification mismatch")
        require(errors, row.get("m_sample") == 9, f"{row.get('dof_id')} m_sample must compute as 9")
        require(errors, row.get("m_full_graph") == 33, f"{row.get('dof_id')} m_full_graph must compute as 33")
        require(errors, row.get("m_readings_reported") == ["sample", "full_graph"], f"{row.get('dof_id')} m readings missing")
        require(errors, len(row.get("sample_perturbed_cells", [])) == 9, f"{row.get('dof_id')} sample cells not recomputed")
        require(errors, len(row.get("full_graph_merge_cells", [])) == 33, f"{row.get('dof_id')} full graph cells not recomputed")
        for reading in ("sample", "full_graph"):
            account = row.get("readings", {}).get(reading, {})
            m = account.get("m")
            expected_floor = math.log(m)
            require(errors, abs(account.get("floor_nats", 0.0) - expected_floor) < 1.0e-12, f"{row.get('dof_id')} {reading} floor mismatch")
            require(errors, account.get("floor_test", {}).get("status") == "pass", f"{row.get('dof_id')} {reading} floor failed")
            require(
                errors,
                account.get("closure_account", {}).get("closed_under_state_plus_record") is True,
                f"{row.get('dof_id')} {reading} closure failed",
            )
            require(
                errors,
                account.get("record_variant", {}).get("honesty_clause_pass") is True,
                f"{row.get('dof_id')} {reading} honesty clause failed",
            )
            require(
                errors,
                account.get("record_erased_control", {}).get("status") == "floor_binds",
                f"{row.get('dof_id')} {reading} erased floor not binding",
            )
            require(
                errors,
                account.get("over_recorded_control", {}).get("reset_charge_appears") is True,
                f"{row.get('dof_id')} {reading} over-record reset missing",
            )


def validate_controls(errors: list[str], controls: dict[str, Any]) -> None:
    require(errors, controls.get("record_erased", {}).get("all_floor_rows_bind") is True, "record_erased control failed")
    require(errors, controls.get("over_recorded", {}).get("all_reset_charges_appear") is True, "over_recorded control failed")
    require(errors, controls.get("commuting_control_D_I", {}).get("D_equals_I") is True, "commuting D/I control failed")
    require(errors, controls.get("shuffled_order_N01", {}).get("status") in {"BOUNDARY", "fail"}, "shuffled order control missing")
    require(
        errors,
        controls.get("misledgered_omitted_entry", {}).get("caught_by_closure_gate") is True,
        "misledgered omitted-entry control not caught",
    )


def validate_alternation(errors: list[str], alternation: dict[str, Any]) -> None:
    require(errors, alternation.get("commuting_control", {}).get("D_equals_I") is True, "commuting control did not collapse")
    row = alternation.get("noncommuting_small_stroke", {})
    require(errors, row.get("gap_matches_leading_order") is True, "noncommuting gap did not match leading order")
    require(errors, row.get("gap_norm", 0.0) > 0.0, "noncommuting gap is zero")
    require(errors, row.get("relative_error", 1.0) < 0.03, "leading-order relative error too high")


def validate_smt(errors: list[str], rows: dict[str, Any]) -> None:
    require(errors, set(rows) >= {"z3", "cvc5"}, "SMT row set mismatch")
    for name in ("z3", "cvc5"):
        row = rows.get(name, {})
        require(errors, row.get("ran") is True and row.get("load_bearing") is True, f"{name} did not run load-bearing")
        require(errors, row.get("verdict") == "unsat", f"{name} real row verdict must be UNSAT")
        require(errors, row.get("erased_flip_verdict") == "sat", f"{name} erased flip must be SAT")
        require(errors, row.get("misledger_flip_verdict") == "sat", f"{name} misledger flip must be SAT")
        require(errors, row.get("asserted_precomputed_boolean") is False, f"{name} must bind values, not booleans")
        bound = row.get("bound_values", {})
        require(errors, bound.get("sample_m") == 9, f"{name} sample_m binding mismatch")
        require(errors, bound.get("full_graph_m") == 33, f"{name} full_graph_m binding mismatch")


def validate_tooling(errors: list[str], payload: dict[str, Any]) -> None:
    require(errors, payload.get("TOOL_MANIFEST") == common.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, payload.get("TOOL_INTEGRATION_DEPTH") == common.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    require(errors, payload.get("TOOL_INTENT_MATRIX") == common.TOOL_INTENT_MATRIX, "TOOL_INTENT_MATRIX mismatch")
    require(errors, payload.get("tool_intent") == common.TOOL_INTENT_MATRIX, "tool_intent mismatch")
    require(errors, payload.get("envelope_built_with_helper") is True, "envelope helper gate missing")
    require(errors, payload.get("build_helper_path") == "scripts/build_three_engine_envelope.py", "wrong envelope helper path")
    require(errors, payload.get("no_builder_audit_verdict") is True, "no_builder_audit_verdict must be true")
    require(errors, payload.get("no_builder_audit_verdict_envelope_gate") is True, "no_builder_audit_verdict_envelope_gate must be true")
    require(errors, payload.get("builder_gates", {}).get("packet_audit_verdict_absent") is True, "audit verdict absent gate failed")
    require(errors, payload.get("builder_gates", {}).get("no_heat_work_or_bath_gate_faked") is True, "heat/work boundary gate failed")
    errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))
    require(errors, set(payload.get("engines", {})) == {"julia", "jax", "pytorch"}, "all three engine lanes required")
    require(errors, payload.get("engine_contract", {}).get("omitted_lanes") == {}, "no omitted lanes allowed")
    for engine in ("julia", "jax", "pytorch"):
        lane = load(RESULT_DIR / f"{common.SIM_ID}_{engine}_results.json")
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
    validate_cycle_rows(errors, payload)
    validate_controls(errors, payload.get("controls", {}))
    validate_alternation(errors, payload.get("alternation_rows", {}))
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
