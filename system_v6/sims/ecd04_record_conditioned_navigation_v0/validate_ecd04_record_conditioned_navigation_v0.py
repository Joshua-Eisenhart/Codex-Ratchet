#!/usr/bin/env python3
"""Validator for ecd04_record_conditioned_navigation_v0."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import ecd04_record_conditioned_navigation_v0_boundary as boundary
import ecd04_record_conditioned_navigation_v0_common as common


sys.path.insert(0, str(common.ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402
from validate_three_engine_sim_result import validate as validate_three_engine  # noqa: E402


REQUIRED_PACKET_FILES = [
    "build_card.md",
    "builder_self_assessment.md",
    f"{common.SIM_ID}_common.py",
    f"{common.SIM_ID}.py",
    f"{common.SIM_ID}_jax.py",
    f"{common.SIM_ID}_pytorch.py",
    f"{common.SIM_ID}_julia.jl",
    f"{common.SIM_ID}_envelope.py",
    f"{common.SIM_ID}_boundary.py",
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


def validate_files(errors: list[str]) -> None:
    for rel_path in REQUIRED_PACKET_FILES:
        require(errors, (common.SIM_DIR / rel_path).is_file(), f"missing packet file: {rel_path}")
    card = common.SIM_DIR / "build_card.md"
    text = card.read_text(encoding="utf-8") if card.exists() else ""
    for phrase in ("two-sided", "equal information", "G.2a", "deaths as results", "searched configurations"):
        require(errors, phrase in text, f"build card missing {phrase}")


def validate_source_locks(errors: list[str], payload: dict[str, Any]) -> None:
    locks = as_dict(payload.get("source_locks"), errors, "source_locks")
    require(errors, set(locks) == set(common.AUTHORITY_PATHS), "source lock set mismatch")
    for name, path in common.AUTHORITY_PATHS.items():
        row = as_dict(locks.get(name), errors, f"source_locks.{name}")
        require(errors, row.get("exists") is True, f"{name} source missing")
        require(errors, source_hash_valid(name, row, path), f"{name} source hash drift")
        if common.USER_HASH_HINTS.get(name):
            require(errors, row.get("user_supplied_hash_hint") == common.USER_HASH_HINTS[name], f"{name} hash hint mismatch")


def validate_search_and_metric(errors: list[str], payload: dict[str, Any]) -> None:
    authority = as_dict(payload.get("authority"), errors, "authority")
    for key in ("two_sided_search_rule", "equal_information_rule", "fair_metric_no_trivial_injective_readouts", "ecd03_scope_lesson_bound", "deaths_are_results"):
        require(errors, authority.get(key) is True, f"authority missing {key}")
    qit = as_dict(payload.get("qit_side"), errors, "qit_side")
    baseline = as_dict(payload.get("baseline_side"), errors, "baseline_side")
    require(errors, qit.get("searched") is True, "QIT side must be searched")
    require(errors, baseline.get("searched") is True, "baseline side must be searched")
    require(errors, qit.get("engine_scope_pin") == "searched_configurations_over_committed_typed_memory_rows_not_committed_rigid_singleton", "engine scope pin mismatch")
    require(errors, qit.get("best", {}).get("primary_eligible") is True, "QIT best must pass target success gate")
    require(errors, baseline.get("best", {}).get("primary_eligible") is True, "baseline best must pass target success gate")
    require(errors, baseline.get("best", {}).get("record_class_count") > qit.get("best", {}).get("record_class_count"), "baseline full record cost must be higher than engine coarse record")
    discr = as_dict(payload.get("discriminator"), errors, "discriminator")
    require(errors, discr.get("verdict") in {"SURVIVES_v0", "DIES_v0", "TIE_v0"}, "bad verdict")
    require(errors, discr.get("either_outcome_valid") is True, "either-outcome contract missing")
    require(errors, abs(discr.get("baseline_minus_qit_cost_margin_nats") - (discr.get("baseline_best_cost_nats") - discr.get("qit_best_cost_nats"))) < 1.0e-12, "margin mismatch")


def validate_controls(errors: list[str], controls: dict[str, Any]) -> None:
    require(errors, controls.get("record_erasure_regression", {}).get("degraded") is True, "record erasure must degrade")
    require(errors, controls.get("scrambled_records", {}).get("degraded") is True, "scrambled records must degrade")
    require(errors, controls.get("order_blind_collapse", {}).get("primary_eligible") is False, "order-blind collapse must fail primary eligibility")
    dropped = as_dict(controls.get("dropped_half_both_sides"), errors, "dropped_half_both_sides")
    require(errors, set(dropped) == {"first_half", "second_half"}, "dropped-half rows missing")
    for half in ("first_half", "second_half"):
        row = as_dict(dropped.get(half), errors, half)
        require(errors, row.get("qit", {}).get("target_success_rate") == 1.0, f"{half} qit dropped-half failed")
        require(errors, row.get("baseline", {}).get("target_success_rate") == 1.0, f"{half} baseline dropped-half failed")
    leak = as_dict(controls.get("no_identity_leak"), errors, "no_identity_leak")
    require(errors, leak.get("identity_leak_detected") is True, "identity leak detection must be reported")
    require(errors, leak.get("identity_leak_excluded_best_accuracy", 1.0) < 1.0, "identity-excluded accuracy must be below 1")


def validate_smt(errors: list[str], payload: dict[str, Any]) -> None:
    proofs = as_dict(payload.get("crossover_proofs"), errors, "crossover_proofs")
    for name in ("z3", "cvc5"):
        row = as_dict(proofs.get(name), errors, f"crossover_proofs.{name}")
        require(errors, row.get("ran") is True and row.get("load_bearing") is True, f"{name} must be load-bearing")
        require(errors, row.get("verdict") == "unsat", f"{name} negated margin must be unsat")
        require(errors, row.get("erased_flip_verdict") == "sat", f"{name} erased flip must be sat")
        require(errors, row.get("asserted_precomputed_boolean") is False, f"{name} must bind values")


def validate_envelope(errors: list[str]) -> None:
    if not common.ENVELOPE_PATH.exists():
        errors.append("missing envelope")
        return
    envelope = common.load_json(common.ENVELOPE_PATH)
    require(errors, envelope.get("schema_version") == "three_engine_sim_result_v1", "envelope schema mismatch")
    require(errors, envelope.get("sim_id") == common.SIM_ID, "envelope sim_id mismatch")
    require(errors, envelope.get("all_pass") is True, "envelope all_pass must be true")
    require(errors, envelope.get("classification") == common.CLASSIFICATION, "envelope classification mismatch")
    require(errors, envelope.get("TOOL_MANIFEST") == common.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, envelope.get("TOOL_INTEGRATION_DEPTH") == common.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    require(errors, envelope.get("TOOL_INTENT_MATRIX") == common.TOOL_INTENT, "TOOL_INTENT mismatch")
    errors.extend(boundary.boundary_errors(envelope, common.SIM_DIR))
    errors.extend(builder_audit_boundary_errors(envelope, common.SIM_DIR / "audit_verdict.md"))
    errors.extend(f"generic three-engine validator: {err}" for err in validate_three_engine(envelope, require_pytorch=True, strict_source_backed=True, require_tool_intent=True))


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    validate_files(errors)
    require(errors, payload.get("schema_version") == common.SCHEMA_VERSION, "schema version mismatch")
    require(errors, payload.get("sim_id") == common.SIM_ID, "sim id mismatch")
    require(errors, payload.get("classification") == common.CLASSIFICATION, "classification mismatch")
    require(errors, payload.get("claim_ceiling") == common.CLAIM_CEILING, "claim ceiling mismatch")
    require(errors, payload.get("promotion_allowed") is False, "promotion must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal admission must be false")
    require(errors, payload.get("all_pass") is True, "base all_pass must be true")
    validate_source_locks(errors, payload)
    errors.extend(boundary.boundary_errors(payload, common.SIM_DIR))
    validate_search_and_metric(errors, payload)
    validate_controls(errors, payload.get("controls", {}))
    validate_smt(errors, payload)
    validate_envelope(errors)
    return errors


def main() -> int:
    payload = common.load_json(common.RESULT_PATH) if common.RESULT_PATH.exists() else {}
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
