#!/usr/bin/env python3
"""Packet-local validator for engine_64_stage_full_run_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import engine_64_stage_full_run_v0_common as common


ROOT = common.ROOT
SIM_DIR = common.SIM_DIR
RESULT_PATH = common.RESULT_PATH
ENVELOPE_RESULT = common.RESULT_DIR / f"{common.SIM_ID}_envelope_results.json"
VALIDATOR_RESULT = common.RESULT_DIR / f"{common.SIM_ID}_validator_results.json"

sys.path.insert(0, str(ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


REQUIRED_FILES = [
    "build_card.md",
    f"{common.SIM_ID}.py",
    f"{common.SIM_ID}_common.py",
    f"{common.SIM_ID}_julia.jl",
    f"{common.SIM_ID}_jax.py",
    f"{common.SIM_ID}_envelope.py",
    f"validate_{common.SIM_ID}.py",
    f"results/{common.SIM_ID}_results.json",
    f"results/{common.SIM_ID}_julia_results.json",
    f"results/{common.SIM_ID}_jax_results.json",
    f"results/{common.SIM_ID}_envelope_results.json",
]


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def as_dict(value: Any, errors: list[str], label: str) -> dict[str, Any]:
    require(errors, isinstance(value, dict), f"{label} must be an object")
    return value if isinstance(value, dict) else {}


def validate_required_files(errors: list[str]) -> None:
    for rel_path in REQUIRED_FILES:
        require(errors, (SIM_DIR / rel_path).is_file(), f"missing required packet file: {rel_path}")


def validate_source_hashes(errors: list[str], payload: dict[str, Any]) -> None:
    require(errors, payload.get("source_sha256") == common.sha256_file(common.SOURCE_PATH), "runner source hash drift")
    require(errors, payload.get("common_source_sha256") == common.sha256_file(common.COMMON_PATH), "common source hash drift")
    locks = as_dict(payload.get("parent_source_locks"), errors, "parent_source_locks")
    expected = set(common.PARENT_PATHS)
    require(errors, set(locks) == expected, "parent source-lock set mismatch")
    for name, path in common.PARENT_PATHS.items():
        row = as_dict(locks.get(name), errors, f"parent_source_locks.{name}")
        require(errors, row.get("exists") is True, f"{name} source lock missing file")
        require(errors, row.get("sha256") == common.sha256_file(path), f"{name} source lock hash drift")


def validate_fences(errors: list[str], payload: dict[str, Any]) -> None:
    require(errors, payload.get("classification") == common.CLASSIFICATION, "classification mismatch")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    fences = as_dict(payload.get("fences"), errors, "fences")
    require(errors, fences.get("realization_relative_only") is True, "realization_relative_only fence missing")
    require(errors, fences.get("source_admitted_substage_convention") is False, "substage convention must not be source-admitted")
    require(errors, fences.get("match_lane_claim") is False, "match-lane claim must be false")
    require(errors, fences.get("basin_claim") is False, "basin claim must be false")
    substage = as_dict(payload.get("substage_realization"), errors, "substage_realization")
    require(errors, substage.get("status") == "UNPINNED", "substage status must be UNPINNED")
    require(errors, substage.get("realization_relative_only") is True, "substage realization-relative marker missing")
    require(errors, substage.get("source_admitted") is False, "substage source_admitted must be false")
    disallowed = set(payload.get("disallowed_claims", []))
    require(errors, any("64-subsubbasin" in item for item in disallowed), "64-subsubbasin disallowance missing")


def validate_schedule(errors: list[str], payload: dict[str, Any]) -> None:
    runs = as_dict(payload.get("runs"), errors, "runs")
    full = as_dict(runs.get("full_64_slot_trajectory"), errors, "runs.full_64_slot_trajectory")
    trajectory = full.get("trajectory", [])
    require(errors, isinstance(trajectory, list) and len(trajectory) == 64, "full trajectory must have 64 ledger rows")
    values = as_dict(payload.get("gate_values"), errors, "gate_values")
    require(errors, values.get("total_slots") == 64, "total_slots must be 64")
    require(errors, values.get("type1_slots") == 32, "type1_slots must be 32")
    require(errors, values.get("type2_slots") == 32, "type2_slots must be 32")
    require(errors, values.get("unique_coordinate_count") == 64, "unique_coordinate_count must be 64")
    require(errors, values.get("bad_coordinate_rows") == 0, "bad coordinate rows must be zero")
    require(errors, values.get("truncated_slots") == 32, "truncated schedule must have 32 slots")
    require(errors, values.get("shuffle_differs") == 1, "shuffled schedule control must differ")
    require(errors, values.get("erasure_differs") == 1, "bit-coordinate erasure control must differ")
    require(errors, values.get("erased_unique_coordinate_count", 64) < 64, "erasure control must reduce unique coordinate count")
    seen = set()
    for row in trajectory:
        axis_bits = row.get("axis_bits", {})
        coord = tuple(axis_bits.get(f"axis{i}") for i in range(1, 7))
        seen.add(coord)
        require(errors, row.get("entry_type") == "engine_64_stage_transition", f"bad ledger entry type at slot {row.get('slot_index')}")
        require(errors, row.get("active_operator", {}).get("family") in {"Ti", "Te", "Fi", "Fe"}, f"bad operator family at slot {row.get('slot_index')}")
        require(errors, row.get("active_operator", {}).get("precedence") in {"operator_first", "terrain_first"}, f"bad precedence at slot {row.get('slot_index')}")
        require(errors, row.get("active_terrain", {}).get("terrain_id") in set(common.TERRAIN_SPECS), f"bad terrain at slot {row.get('slot_index')}")
    require(errors, len(seen) == 64, "trajectory does not cover 64 unique coordinate rows")


def validate_coordinate_rows(errors: list[str], payload: dict[str, Any]) -> None:
    block = as_dict(payload.get("coordinate_consistency"), errors, "coordinate_consistency")
    rows = block.get("rows", [])
    require(errors, isinstance(rows, list) and len(rows) == 64, "coordinate consistency must have 64 rows")
    require(errors, block.get("bad_row_count") == 0, "coordinate consistency has bad rows")
    require(errors, block.get("all_rows_pass") is True, "coordinate consistency all_rows_pass must be true")
    for row in rows:
        require(errors, row.get("pass") is True, f"coordinate row failed: {row.get('slot_index')}")
        checks = row.get("checks", {})
        require(errors, checks and all(checks.values()), f"coordinate checks failed: {row.get('slot_index')}")


def validate_controls_and_comparison(errors: list[str], payload: dict[str, Any]) -> None:
    controls = as_dict(payload.get("controls"), errors, "controls")
    for name in ("shuffled_schedule_control", "truncated_schedule_boundary", "bit_coordinate_erasure_control"):
        row = as_dict(controls.get(name), errors, f"controls.{name}")
        require(errors, row.get("pass") is True, f"{name} did not pass")
    comparison = as_dict(payload.get("type1_l_vs_type2_r_comparison"), errors, "type1_l_vs_type2_r_comparison")
    require(errors, comparison.get("same_initial_state") is True, "L/R comparison must use same initial state")
    require(errors, float(comparison.get("final_state_l2", 0.0)) > common.EPS, "L/R final-state difference must be positive")
    require(errors, comparison.get("chirality_difference_detected") is True, "chirality difference not detected")


def validate_proofs_and_tools(errors: list[str], payload: dict[str, Any]) -> None:
    proofs = as_dict(payload.get("crossover_proofs"), errors, "crossover_proofs")
    for name in ("z3", "cvc5"):
        proof = as_dict(proofs.get(name), errors, f"crossover_proofs.{name}")
        require(errors, proof.get("ran") is True, f"{name} did not run")
        require(errors, proof.get("load_bearing") is True, f"{name} not load-bearing")
        require(errors, proof.get("verdict") == "unsat", f"{name} verdict must be unsat")
        require(errors, proof.get("erased_control_verdict") == "sat", f"{name} erased control must be sat")
    manifest = as_dict(payload.get("TOOL_MANIFEST"), errors, "TOOL_MANIFEST")
    depths = as_dict(payload.get("TOOL_INTEGRATION_DEPTH"), errors, "TOOL_INTEGRATION_DEPTH")
    for tool in ("numpy", "z3", "cvc5", "builder_audit_boundary"):
        require(errors, as_dict(manifest.get(tool), errors, f"TOOL_MANIFEST.{tool}").get("used") is True, f"{tool} manifest missing used=true")
        require(errors, depths.get(tool) == "load_bearing", f"{tool} must be load_bearing")
    errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))


def validate_envelope(errors: list[str], payload: dict[str, Any]) -> None:
    if not ENVELOPE_RESULT.exists():
        errors.append("missing envelope result")
        return
    envelope = json.loads(ENVELOPE_RESULT.read_text(encoding="utf-8"))
    require(errors, envelope.get("schema_version") == "three_engine_sim_result_v1", "envelope schema_version mismatch")
    require(errors, envelope.get("sim_id") == common.SIM_ID, "envelope sim_id mismatch")
    require(errors, envelope.get("classification") == common.CLASSIFICATION, "envelope classification mismatch")
    require(errors, envelope.get("promotion_allowed") is False, "envelope promotion_allowed must be false")
    require(errors, envelope.get("formal_admission_allowed") is False, "envelope formal_admission_allowed must be false")
    require(errors, envelope.get("all_pass") is True, "envelope all_pass must be true")
    require(
        errors,
        envelope.get("mode") == "julia_canon_plus_jax_diagnostic_pytorch_omitted",
        "envelope mode must declare honest two-lane plus omitted PyTorch mode",
    )
    require(
        errors,
        envelope.get("build_helper_path") == "scripts/build_three_engine_envelope.py",
        "envelope must name canonical build helper",
    )
    engine_contract = as_dict(envelope.get("engine_contract"), errors, "envelope.engine_contract")
    require(errors, sorted(engine_contract.get("lanes", [])) == ["jax", "julia"], "envelope lanes must be jax+julia")
    require(errors, "pytorch" in engine_contract.get("omitted_lanes", {}), "envelope must honestly omit PyTorch")
    require(errors, set(envelope.get("engines", {})) == {"julia", "jax"}, "envelope engines must be julia+jax only")
    boundary = as_dict(envelope.get("boundary"), errors, "envelope.boundary")
    for key in (
        "realization_relative_only",
        "not_qit_admission",
        "not_axis_admission",
    ):
        require(errors, boundary.get(key) is True, f"envelope boundary missing/false: {key}")
    require(errors, boundary.get("source_admitted_substage_convention") is False, "envelope must not source-admit substage convention")
    require(errors, boundary.get("match_lane_claim") is False, "envelope must not make a match-lane claim")
    require(errors, boundary.get("basin_claim") is False, "envelope must not make a basin claim")
    require(errors, envelope.get("result_values_unchanged") is True, "envelope must declare unchanged values")
    parity = as_dict(envelope.get("engine_value_parity"), errors, "envelope.engine_value_parity")
    for engine in ("julia", "jax"):
        checks = as_dict(parity.get(engine), errors, f"envelope.engine_value_parity.{engine}")
        require(errors, bool(checks), f"{engine} parity checks missing")
        require(errors, all(checks.values()), f"{engine} parity checks must all pass")
    intent = as_dict(envelope.get("TOOL_INTENT_MATRIX"), errors, "envelope.TOOL_INTENT_MATRIX")
    require(errors, "build_three_engine_envelope" in intent, "TOOL_INTENT_MATRIX missing envelope builder")
    require(errors, intent.get("pytorch", {}).get("mode") == "omitted", "TOOL_INTENT_MATRIX must declare PyTorch omitted")
    summary = as_dict(envelope.get("full_run_summary_check"), errors, "envelope.full_run_summary_check")
    require(errors, summary.get("all_required_present") is True, "FULL-RUN summary check must be complete")
    present_absent = as_dict(summary.get("present_absent"), errors, "envelope.full_run_summary_check.present_absent")
    for name in (
        "all_64_slots_executed_per_engine",
        "slot_coordinate_consistency_verdicts",
        "l_vs_r_full_run_comparison",
        "shuffled_schedule_control",
        "truncated_schedule_boundary",
        "bit_coordinate_erasure_control",
    ):
        require(errors, present_absent.get(name) == "present", f"FULL-RUN summary missing: {name}")
    require(errors, envelope.get("base_result_sha256") == common.sha256_file(RESULT_PATH), "envelope base result hash drift")


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    validate_required_files(errors)
    require(errors, payload.get("schema_version") == f"{common.SIM_ID}_result_v1", "schema version mismatch")
    require(errors, payload.get("sim_id") == common.SIM_ID, "sim_id mismatch")
    require(errors, payload.get("mode") == common.MODE, "mode mismatch")
    require(errors, payload.get("all_pass") is True, "top-level all_pass must be true")
    validate_source_hashes(errors, payload)
    validate_fences(errors, payload)
    validate_schedule(errors, payload)
    validate_coordinate_rows(errors, payload)
    validate_controls_and_comparison(errors, payload)
    validate_proofs_and_tools(errors, payload)
    validate_envelope(errors, payload)
    return errors


def main() -> int:
    result_path = Path(sys.argv[1]) if len(sys.argv) > 1 else RESULT_PATH
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    errors = validate_payload(payload)
    result = {
        "ok": not errors,
        "sim_id": common.SIM_ID,
        "result_path": common.rel(result_path),
        "errors": errors,
    }
    common.write_json(VALIDATOR_RESULT, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
