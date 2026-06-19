#!/usr/bin/env python3
"""Validator for the ECD.06 prediction-first discriminator packet."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import ecd06_prediction_first_inference_v0_common as common


sys.path.insert(0, str(common.ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


REQUIRED_PACKET_FILES = [
    "build_card.md",
    "builder_self_assessment.md",
    f"{common.SIM_ID}_common.py",
    f"{common.SIM_ID}.py",
    f"{common.SIM_ID}_jax.py",
    f"{common.SIM_ID}_pytorch.py",
    f"{common.SIM_ID}_julia.jl",
    f"{common.SIM_ID}_envelope.py",
    f"validate_{common.SIM_ID}.py",
    f"tests/test_{common.SIM_ID}.py",
    f"results/{common.SIM_ID}_results.json",
    f"results/{common.SIM_ID}_jax_results.json",
    f"results/{common.SIM_ID}_pytorch_results.json",
    f"results/{common.SIM_ID}_julia_results.json",
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
            require(errors, row.get("user_supplied_hash_hint") == common.USER_HASH_HINTS[name], f"{name} hint mismatch")


def validate_discriminator(errors: list[str], payload: dict[str, Any]) -> None:
    metric = as_dict(payload.get("metric_pin"), errors, "metric_pin")
    require(errors, metric.get("penalizes_trivially_injective_readouts_both_sides") is True, "diversity penalty gate missing")
    qit = as_dict(payload.get("qit_side"), errors, "qit_side")
    baseline = as_dict(payload.get("baseline_side"), errors, "baseline_side")
    require(errors, qit.get("searched") is True, "QIT side must be searched")
    require(errors, baseline.get("searched") is True, "baseline side must be searched")
    require(errors, baseline.get("baseline_able_to_win_positive_predicate") is True, "baseline positive predicate missing")
    require(errors, len(qit.get("candidates", [])) == len(common.QIT_GAINS), "QIT gain search mismatch")
    baseline_policies = {row.get("policy_id") for row in baseline.get("candidates", [])}
    for policy in {
        "mandatory_persistence_identity_inclusive_diagnostic",
        "empirical_one_step_frequency_table_by_generator_leave_one_out",
        "searched_policy_class_generator_family_mean",
    }:
        require(errors, policy in baseline_policies, f"missing baseline policy: {policy}")
    discr = as_dict(payload.get("discriminator"), errors, "discriminator")
    require(errors, discr.get("verdict") in {"SURVIVES_v0", "DIES_v0", "TIE_v0"}, "bad verdict")
    require(errors, discr.get("either_outcome_valid") is True, "either-outcome contract missing")
    require(
        errors,
        abs(float(discr.get("qit_minus_baseline_adjusted_error_margin")) - (
            float(discr.get("qit_best_adjusted_error")) - float(discr.get("baseline_best_fair_adjusted_error"))
        )) < 1.0e-9,
        "margin mismatch",
    )


def validate_controls(errors: list[str], payload: dict[str, Any]) -> None:
    controls = as_dict(payload.get("controls"), errors, "controls")
    leak = as_dict(controls.get("no_identity_leak"), errors, "no_identity_leak")
    require(errors, leak.get("status") == "pass", "no-identity-leak failed")
    require(errors, "identity_leak_detected" in leak, "identity_leak_detected missing")
    require(errors, leak.get("identity_leak_excluded_best_accuracy", 1.0) < 1.0, "identity-excluded predictor perfect")
    require(errors, bool(leak.get("identity_leak_exclusion_rule")), "identity leak exclusion rule missing")
    scrambled = as_dict(controls.get("scrambled_error_regression"), errors, "scrambled_error_regression")
    require(errors, scrambled.get("margin_moved") is True, "scrambled regression did not move")
    dropped = as_dict(controls.get("dropped_half_sensitivity_both_sides"), errors, "dropped_half_sensitivity_both_sides")
    require(errors, set(dropped) == {"first_generator_half", "second_generator_half"}, "dropped-half rows missing")
    collapse = as_dict(controls.get("order_blind_collapse"), errors, "order_blind_collapse")
    require(errors, collapse.get("collapses_order_and_generator_to_global_mean") is True, "order-blind collapse missing")


def validate_fences_tools_boundary(errors: list[str], payload: dict[str, Any]) -> None:
    require(errors, payload.get("classification") == common.CLASSIFICATION, "classification mismatch")
    require(errors, payload.get("promotion_allowed") is False, "promotion must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal admission must be false")
    disallowed = set(payload.get("disallowed_claims", []))
    for phrase in ("holodeck admission", "FEP admission", "physics admission", "stable 3-cell invariant"):
        require(errors, phrase in disallowed, f"missing disallowed claim: {phrase}")
    require(errors, payload.get("TOOL_MANIFEST") == common.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, payload.get("TOOL_INTEGRATION_DEPTH") == common.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    gates = as_dict(payload.get("builder_gates"), errors, "builder_gates")
    require(errors, gates.get("g2a_boundary_helper_from_birth") is True, "G.2a from-birth gate missing")
    errors.extend(builder_audit_boundary_errors(payload, common.SIM_DIR / "audit_verdict.md"))


def validate_three_engine_envelope(errors: list[str]) -> None:
    if not common.ENVELOPE_PATH.exists():
        errors.append("missing envelope")
        return
    cmd = [
        sys.executable,
        str(common.ROOT / "scripts" / "validate_three_engine_sim_result.py"),
        "--require-pytorch",
        str(common.ENVELOPE_PATH),
    ]
    proc = subprocess.run(cmd, cwd=common.ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if proc.returncode != 0:
        errors.append("three-engine envelope validator failed: " + (proc.stdout + proc.stderr).strip())
    envelope = common.load_json(common.ENVELOPE_PATH)
    require(errors, envelope.get("schema_version") == "three_engine_sim_result_v1", "standard envelope schema mismatch")
    require(errors, envelope.get("all_pass") is True, "envelope all_pass must be true")
    require(errors, envelope.get("mode") == "all_three_full_sims", "envelope mode mismatch")
    require(errors, envelope.get("no_builder_audit_verdict") is True, "envelope boundary field missing")
    errors.extend(builder_audit_boundary_errors(envelope, common.SIM_DIR / "audit_verdict.md"))


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for rel_path in REQUIRED_PACKET_FILES:
        require(errors, (common.SIM_DIR / rel_path).is_file(), f"missing packet file: {rel_path}")
    require(errors, payload.get("schema_version") == common.SCHEMA_VERSION, "schema version mismatch")
    require(errors, payload.get("sim_id") == common.SIM_ID, "sim id mismatch")
    require(errors, payload.get("all_pass") is True, "all_pass must be true")
    validate_source_locks(errors, payload)
    validate_discriminator(errors, payload)
    validate_controls(errors, payload)
    validate_fences_tools_boundary(errors, payload)
    validate_three_engine_envelope(errors)
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
