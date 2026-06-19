#!/usr/bin/env python3
"""Validator for the ECD.03 typed co-ratchet discriminator."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from typing import Any

import ecd03_typed_coratchet_v0_common as common


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
        if common.USER_HASH_HINTS.get(name):
            require(errors, row.get("user_supplied_hash_hint") == common.USER_HASH_HINTS[name], f"{name} hash hint mismatch")


def validate_authority_and_search(errors: list[str], payload: dict[str, Any]) -> None:
    authority = as_dict(payload.get("authority"), errors, "authority")
    require(errors, authority.get("two_sided_search_rule") is True, "two-sided search rule missing")
    require(errors, authority.get("equal_information_rule") is True, "equal-information rule missing")
    require(errors, authority.get("fair_metric_no_trivial_injective_readouts") is True, "fair metric rule missing")
    env = as_dict(payload.get("shared_type_ladder_environment"), errors, "shared_type_ladder_environment")
    require(errors, env.get("feed_hash_hint") == "60376bd9f", "feed hash hint missing")
    require(errors, payload.get("shared_environment_hash") == common.stable_sha256(env), "shared environment hash mismatch")
    qit = as_dict(payload.get("qit_side"), errors, "qit_side")
    baseline = as_dict(payload.get("baseline_side"), errors, "baseline_side")
    require(errors, qit.get("searched") is True, "QIT side must be searched")
    require(errors, baseline.get("searched") is True, "baseline side must be searched")
    require(errors, qit.get("shared_environment_hash") == baseline.get("shared_environment_hash"), "equal-information hash mismatch")
    require(errors, qit.get("shared_environment_hash") == payload.get("shared_environment_hash"), "QIT environment hash mismatch")
    require(errors, qit.get("nominal_schedule_count", 0) > 0, "QIT search empty")
    require(errors, baseline.get("nominal_schedule_count", 0) > 0, "baseline search empty")
    require(errors, len(qit.get("sequence_table", [])) == qit.get("computed_sequence_count"), "QIT sequence table/count mismatch")
    require(errors, len(baseline.get("sequence_table", [])) == baseline.get("computed_sequence_count"), "baseline sequence table/count mismatch")


def validate_discriminator(errors: list[str], payload: dict[str, Any]) -> None:
    gate = as_dict(payload.get("availability_nontriviality_gate"), errors, "availability_nontriviality_gate")
    require(errors, gate.get("status") == "pass", "availability nontriviality gate failed")
    discr = as_dict(payload.get("discriminator"), errors, "discriminator")
    qit_only = discr.get("qit_only_sequences", [])
    baseline_only = discr.get("baseline_only_sequences", [])
    require(errors, discr.get("qit_only_sequences_count") == len(qit_only), "QIT-only count mismatch")
    require(errors, discr.get("baseline_only_sequences_count") == len(baseline_only), "baseline-only count mismatch")
    require(errors, discr.get("symmetric_difference_count") == len(qit_only) + len(baseline_only), "symmetric difference mismatch")
    require(errors, discr.get("verdict") in {"SURVIVES_v0", "DIES_v0", "TIE_v0"}, "bad verdict")
    require(errors, discr.get("either_outcome_valid") is True, "either-outcome contract missing")


def validate_controls(errors: list[str], payload: dict[str, Any]) -> None:
    controls = as_dict(payload.get("controls"), errors, "controls")
    permuted = as_dict(controls.get("permuted_ops_regression"), errors, "permuted_ops_regression")
    require(errors, permuted.get("availability_moved") is True, "permuted operation control did not move availability")
    collapse = as_dict(controls.get("order_blind_collapse"), errors, "order_blind_collapse")
    require(errors, collapse.get("collapses_schedule_order") is True, "order-blind collapse did not collapse")
    require(errors, collapse.get("metric_used_for_discriminator") is False, "order-blind metric used for discriminator")
    dropped = as_dict(controls.get("dropped_half_schedule_sensitivity"), errors, "dropped_half_schedule_sensitivity")
    require(errors, as_dict(dropped.get("qit_dropped_half"), errors, "qit_dropped_half").get("nominal_schedule_count", 0) > 0, "QIT dropped-half empty")
    require(errors, as_dict(dropped.get("baseline_dropped_half"), errors, "baseline_dropped_half").get("nominal_schedule_count", 0) > 0, "baseline dropped-half empty")
    leak = as_dict(controls.get("no_identity_leak"), errors, "no_identity_leak")
    require(errors, leak.get("status") == "pass", "identity leak control failed")
    require(errors, leak.get("sequence_fingerprints_label_free") is True, "label-free fingerprint gate missing")


def validate_fences_tools_boundary(errors: list[str], payload: dict[str, Any]) -> None:
    require(errors, payload.get("classification") == common.CLASSIFICATION, "classification mismatch")
    require(errors, payload.get("claim_ceiling") == common.CLAIM_CEILING, "claim ceiling mismatch")
    require(errors, payload.get("promotion_allowed") is False, "promotion must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal admission must be false")
    disallowed = set(payload.get("disallowed_claims", []))
    for phrase in ("QIT-engine admission", "formal theorem", "type order discovered free of all in-packet semantics"):
        require(errors, phrase in disallowed, f"missing disallowed claim: {phrase}")
    require(errors, payload.get("TOOL_MANIFEST") == common.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, payload.get("TOOL_INTEGRATION_DEPTH") == common.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    gates = as_dict(payload.get("builder_gates"), errors, "builder_gates")
    require(errors, gates.get("g2a_boundary_helper_from_birth") is True, "G.2a from-birth gate missing")
    require(errors, gates.get("validator_delegates_to_builder_audit_boundary") is True, "validator boundary gate missing")
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
    require(errors, scope.get("three_engine_mode") == "not_scoped_for_this_packet", "engine scope mismatch")
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
    validate_authority_and_search(errors, payload)
    validate_discriminator(errors, payload)
    validate_controls(errors, payload)
    validate_fences_tools_boundary(errors, payload)
    validate_envelope(errors)
    return errors


def main() -> int:
    if not common.RESULT_PATH.exists():
        errors = ["missing base result"]
    else:
        errors = validate_payload(common.load_json(common.RESULT_PATH))
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
