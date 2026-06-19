#!/usr/bin/env python3
"""Validator for the ECD.05 instruction-machine discriminator."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import ecd05_instruction_machine_v0_common as common


sys.path.insert(0, str(common.ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


REQUIRED_PACKET_FILES = [
    "build_card.md",
    "builder_self_assessment.md",
    f"{common.SIM_ID}_common.py",
    f"{common.SIM_ID}.py",
    f"{common.SIM_ID}_envelope.py",
    f"validate_{common.SIM_ID}.py",
    f"tests/test_{common.SIM_ID}.py",
    f"results/{common.SIM_ID}_results.json",
    f"results/{common.SIM_ID}_envelope_results.json",
]


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def as_dict(value: Any, errors: list[str], label: str) -> dict[str, Any]:
    require(errors, isinstance(value, dict), f"{label} must be an object")
    return value if isinstance(value, dict) else {}


def hash_exists_in_git_history(expected_hash: str | None, path: Any) -> bool:
    if not expected_hash:
        return False
    rel_path = common.rel(path)
    try:
        commits = subprocess.check_output(
            ["git", "log", "--format=%H", "--", rel_path],
            cwd=common.ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).splitlines()
    except (OSError, subprocess.CalledProcessError):
        return False
    for commit in commits:
        try:
            blob = subprocess.check_output(
                ["git", "show", f"{commit}:{rel_path}"],
                cwd=common.ROOT,
                stderr=subprocess.DEVNULL,
            )
        except (OSError, subprocess.CalledProcessError):
            continue
        if hashlib.sha256(blob).hexdigest() == expected_hash:
            return True
    return False


def source_hash_valid(name: str, row: dict[str, Any], path: Any) -> bool:
    if row.get("sha256") == common.sha256_file(path):
        return True
    return name == "ecd_supplement_1" and hash_exists_in_git_history(row.get("sha256"), path)


def validate_source_locks(errors: list[str], payload: dict[str, Any]) -> None:
    locks = as_dict(payload.get("source_locks"), errors, "source_locks")
    require(errors, set(locks) == set(common.AUTHORITY_PATHS), "source lock set mismatch")
    for name, path in common.AUTHORITY_PATHS.items():
        row = as_dict(locks.get(name), errors, f"source_locks.{name}")
        require(errors, row.get("exists") is True, f"{name} source missing")
        require(errors, source_hash_valid(name, row, path), f"{name} source hash drift")
        require(errors, row.get("user_supplied_hash_hint") == common.USER_HASH_HINTS.get(name), f"{name} hash hint mismatch")


def validate_program_searches(errors: list[str], payload: dict[str, Any]) -> None:
    pin = as_dict(payload.get("program_space_pin"), errors, "program_space_pin")
    require(errors, pin.get("program_length") == common.PROGRAM_LENGTH, "program length pin mismatch")
    require(errors, pin.get("same_pinned_realization") is True, "same realization pin missing")
    qit = as_dict(payload.get("qit_side"), errors, "qit_side")
    baseline = as_dict(payload.get("baseline_side"), errors, "baseline_side")
    require(errors, qit.get("policy_id") == "qit_schedule_order_subsequence_search_v0", "QIT policy mismatch")
    require(errors, qit.get("nominal_program_count") == common.comb(64, common.PROGRAM_LENGTH), "QIT program count mismatch")
    require(errors, qit.get("computed_distinct_channel_count", 0) > 0, "QIT diversity missing")
    require(errors, isinstance(qit.get("channel_table"), list), "QIT channel table missing")
    require(errors, len(qit.get("channel_table", [])) == qit.get("computed_distinct_channel_count"), "QIT table/count mismatch")
    require(
        errors,
        baseline.get("policy_id") == "strongest_classical_same_64_slot_alphabet_free_order_with_repetition_v0",
        "baseline policy mismatch",
    )
    require(errors, baseline.get("nominal_program_count") == 64 ** common.PROGRAM_LENGTH, "baseline program count mismatch")
    require(errors, baseline.get("computed_distinct_channel_count", 0) > 0, "baseline diversity missing")
    require(errors, baseline.get("complete_table_materialized") is True, "baseline search must be complete")
    require(errors, baseline.get("channel_table_sha256"), "baseline table hash missing")
    outcome = as_dict(payload.get("discriminator"), errors, "discriminator")
    require(errors, outcome.get("qit_max") == qit.get("computed_distinct_channel_count"), "QIT max mismatch")
    require(errors, outcome.get("baseline_max") == baseline.get("computed_distinct_channel_count"), "baseline max mismatch")
    require(
        errors,
        outcome.get("qit_minus_baseline_margin") == outcome.get("qit_max") - outcome.get("baseline_max"),
        "margin mismatch",
    )
    require(errors, outcome.get("verdict") in {"SURVIVES_v0", "DIES_v0", "TIE_v0"}, "bad discriminator verdict")


def validate_controls(errors: list[str], payload: dict[str, Any]) -> None:
    controls = as_dict(payload.get("controls"), errors, "controls")
    collapse = as_dict(controls.get("commuting_order_blind_collapse"), errors, "commuting_order_blind_collapse")
    require(errors, collapse.get("collapses_channel_family_to_component_multisets") is True, "order-blind collapse missing")
    require(errors, collapse.get("control_count_lte_qit_channels") is True, "order-blind control exceeded QIT diversity")
    require(
        errors,
        isinstance(collapse.get("extra_order_sensitive_channels_over_component_multisets"), int),
        "order-sensitive excess count missing",
    )
    require(errors, collapse.get("fingerprints_read_slot_labels") is False, "collapse control leaks slot labels")
    dropped = as_dict(controls.get("dropped_half_program_space_sensitivity"), errors, "dropped_half_program_space_sensitivity")
    qit_half = as_dict(dropped.get("qit_dropped_half"), errors, "qit_dropped_half")
    baseline_half = as_dict(dropped.get("baseline_dropped_half"), errors, "baseline_dropped_half")
    require(errors, qit_half.get("computed_distinct_channel_count", 0) > 0, "QIT dropped-half search missing")
    require(errors, baseline_half.get("computed_distinct_channel_count", 0) > 0, "baseline dropped-half search missing")
    require(errors, qit_half.get("nominal_program_count") == common.comb(32, common.PROGRAM_LENGTH), "QIT half count mismatch")
    require(errors, baseline_half.get("nominal_program_count") == 32 ** common.PROGRAM_LENGTH, "baseline half count mismatch")
    leak = as_dict(controls.get("no_identity_leak"), errors, "no_identity_leak")
    require(errors, leak.get("status") == "pass", "identity leak control failed")
    require(errors, leak.get("fingerprints_read_slot_labels") is False, "fingerprints read slot labels")
    require(errors, leak.get("fingerprint_ids_unchanged_under_label_rename") is True, "label rename changed fingerprints")
    require(errors, leak.get("stage_component_count") == 16, "stage component count must remain 16")
    scrambled = as_dict(controls.get("scrambled_schedule_regression"), errors, "scrambled_schedule_regression")
    require(errors, scrambled.get("scrambled_differs_from_pinned") is True, "scrambled schedule regression did not move")


def validate_fences_and_tools(errors: list[str], payload: dict[str, Any]) -> None:
    require(errors, payload.get("classification") == common.CLASSIFICATION, "classification mismatch")
    require(errors, payload.get("claim_ceiling") == common.CLAIM_CEILING, "claim ceiling mismatch")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    fence = as_dict(payload.get("realization_relativity_fence"), errors, "realization_relativity_fence")
    require(errors, fence.get("same_pinned_realization_for_all_programs") is True, "same-realization fence missing")
    require(errors, fence.get("engine_64_run_hash_hint") == "23cfa5536", "64-run hash hint missing")
    require(errors, fence.get("no_substage_semantics_claim") is True, "substage semantics fence missing")
    require(errors, fence.get("source_admitted_substage_convention") is False, "substage convention must not be source-admitted")
    disallowed = set(payload.get("disallowed_claims", []))
    for phrase in ("universal computer", "Turing-complete machine", "QIT-engine admission", "64-subsubbasin proof"):
        require(errors, phrase in disallowed, f"missing disallowed claim: {phrase}")
    require(errors, payload.get("TOOL_MANIFEST") == common.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, payload.get("TOOL_INTEGRATION_DEPTH") == common.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    errors.extend(builder_audit_boundary_errors(payload, common.SIM_DIR / "audit_verdict.md"))


def validate_envelope(errors: list[str]) -> None:
    if not common.ENVELOPE_PATH.exists():
        errors.append("missing envelope result")
        return
    envelope = common.load_json(common.ENVELOPE_PATH)
    require(errors, envelope.get("schema_version") == common.ENVELOPE_SCHEMA_VERSION, "envelope schema mismatch")
    require(errors, envelope.get("sim_id") == common.SIM_ID, "envelope sim_id mismatch")
    require(errors, envelope.get("all_pass") is True, "envelope all_pass must be true")
    require(errors, envelope.get("base_result_sha256") == common.sha256_file(common.RESULT_PATH), "envelope base hash drift")
    scope = as_dict(envelope.get("engine_scope"), errors, "engine_scope")
    require(errors, scope.get("three_engine_mode") == "not_scoped_for_this_packet", "engine scope must be not scoped")
    require(errors, envelope.get("TOOL_MANIFEST") == common.TOOL_MANIFEST, "envelope TOOL_MANIFEST mismatch")
    require(errors, envelope.get("TOOL_INTEGRATION_DEPTH") == common.TOOL_INTEGRATION_DEPTH, "envelope TOOL_INTEGRATION_DEPTH mismatch")
    errors.extend(builder_audit_boundary_errors(envelope, common.SIM_DIR / "audit_verdict.md"))


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for rel_path in REQUIRED_PACKET_FILES:
        require(errors, (common.SIM_DIR / rel_path).is_file(), f"missing packet file: {rel_path}")
    require(errors, payload.get("schema_version") == common.SCHEMA_VERSION, "schema version mismatch")
    require(errors, payload.get("sim_id") == common.SIM_ID, "sim id mismatch")
    require(errors, payload.get("all_pass") is True, "all_pass must be true")
    validate_source_locks(errors, payload)
    validate_program_searches(errors, payload)
    validate_controls(errors, payload)
    validate_fences_and_tools(errors, payload)
    validate_envelope(errors)
    return errors


def main() -> int:
    if not common.RESULT_PATH.exists():
        errors = ["missing base result"]
    else:
        payload = common.load_json(common.RESULT_PATH)
        errors = validate_payload(payload)
    result = {
        "ok": not errors,
        "result_json": common.rel(common.RESULT_PATH),
        "envelope_json": common.rel(common.ENVELOPE_PATH),
        "errors": errors,
    }
    common.write_json(common.VALIDATOR_RESULT_PATH, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
