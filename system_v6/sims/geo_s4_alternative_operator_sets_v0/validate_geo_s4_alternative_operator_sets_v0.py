#!/usr/bin/env python3
"""Packet-local validator for geo_s4_alternative_operator_sets_v0."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s4_alternative_operator_sets_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
DEFAULT_RESULT = SIM_DIR / "results" / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT = SIM_DIR / "results" / f"{SIM_ID}_validator_results.json"

sys.path.insert(0, str(ROOT))
from scripts.builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


def rel(path: Path) -> str:
    if not path.is_absolute():
        path = ROOT / path
    return str(path.relative_to(ROOT))


def require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def as_dict(value: Any, name: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return {}
    return value


def validate(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    require(payload.get("schema_version") == "three_engine_sim_result_v1", errors, "schema_version mismatch")
    require(payload.get("sim_id") == SIM_ID, errors, "sim_id mismatch")
    require(payload.get("classification") == "scratch_diagnostic", errors, "classification must be scratch_diagnostic")
    require(payload.get("promotion_allowed") is False, errors, "promotion_allowed must be false")
    require(payload.get("formal_admission_allowed") is False, errors, "formal_admission_allowed must be false")
    require(payload.get("all_pass") is True, errors, "all_pass must be true")

    anchor = as_dict(payload.get("committed_anchor_reproduction"), "committed_anchor_reproduction", errors)
    require(anchor.get("all_pass") is True, errors, "committed anchor did not reproduce")
    require(anchor.get("pin_sha256_matches_parent") is True, errors, "committed pin hash mismatch")
    require(all(anchor.get("affine_rows_byte_exact", {}).values()), errors, "affine anchor rows not byte-exact")

    matrix = as_dict(payload.get("survival_matrix"), "survival_matrix", errors)
    require(set(matrix) == {"A_y_frame", "B_depolarizing", "C_amplitude_damping", "D_random_hermitian"}, errors, "alternative set coverage mismatch")
    require(payload.get("co_survivors_named") == [], errors, "no alternative co-survivors expected")
    unique = as_dict(payload.get("uniqueness_answer"), "uniqueness_answer", errors)
    require(unique.get("committed_pattern_unique_among_tested_alternatives") is True, errors, "committed uniqueness answer must be true among tested alternatives")
    expected_failures = {
        "A_y_frame": "z_probe_quotient_descent_mortality",
        "B_depolarizing": "commutator_N01_structure",
        "C_amplitude_damping": "commutator_N01_structure",
        "D_random_hermitian": "shell_preservation_leakage",
    }
    for set_id, row_name in expected_failures.items():
        row = as_dict(matrix.get(set_id), f"survival_matrix.{set_id}", errors)
        require(row.get("survives") is False, errors, f"{set_id} must not survive")
        require(row.get("first_failure_row") == row_name, errors, f"{set_id} first failure mismatch")

    controls = as_dict(payload.get("controls"), "controls", errors)
    require(as_dict(controls.get("null_model_dies"), "controls.null_model_dies", errors).get("dies") is True, errors, "null model must die")
    require(as_dict(controls.get("deliberate_non_cptp_fail"), "controls.deliberate_non_cptp_fail", errors).get("dies_as_expected") is True, errors, "non-CPTP control must fail")

    gates = as_dict(payload.get("build_gates"), "build_gates", errors)
    for gate in (
        "classification_ceiling",
        "parent_lineage_hash_bound",
        "committed_anchor_reproduces_parent_byte_exact",
        "all_alternatives_evaluated",
        "same_battery_rows_present",
        "null_model_dies",
        "deliberate_non_cptp_fail_fires",
        "cptp_computed_per_channel",
        "smt_positive_and_erased_flip",
        "julia_sidecar_pass",
        "julia_python_survival_hash_match",
        "one_to_one_tool_calls",
    ):
        require(gates.get(gate) is True, errors, f"gate {gate} must be true")

    proofs = as_dict(payload.get("crossover_proofs"), "crossover_proofs", errors)
    for key in ("z3", "cvc5", "julia_z3"):
        proof = as_dict(proofs.get(key), f"crossover_proofs.{key}", errors)
        require(proof.get("ran") is True, errors, f"{key} must run")
        require(proof.get("load_bearing") is True, errors, f"{key} must be load-bearing")
        require(proof.get("verdict") == "unsat", errors, f"{key} verdict must be unsat")
        require(proof.get("erased_flip_detected") is True, errors, f"{key} erased flip must be detected")
        require(proof.get("asserted_precomputed_boolean") is False, errors, f"{key} must not bind a precomputed boolean")

    calls = payload.get("tool_calls")
    require(isinstance(calls, list) and len(calls) == len(payload.get("claim_path_tools", [])), errors, "one-to-one tool_calls mismatch")
    if isinstance(calls, list):
        require(sorted(call.get("tool") for call in calls) == sorted(payload.get("claim_path_tools", [])), errors, "tool_calls do not match claim_path_tools")
        require(all(call.get("load_bearing") is True for call in calls), errors, "all tool_calls must be load-bearing")

    divergence = as_dict(payload.get("divergence"), "divergence", errors)
    require(divergence.get("julia_authoritative") is True, errors, "divergence.julia_authoritative must be true")
    require(divergence.get("max_divergence") == 0.0, errors, "max_divergence must be 0.0")
    return errors


def main(argv: list[str]) -> int:
    result_path = Path(argv[1]) if len(argv) > 1 else DEFAULT_RESULT
    if not result_path.is_absolute():
        result_path = ROOT / result_path
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    errors = validate(payload)
    errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))
    out = {
        "ok": not errors,
        "validator_ok": not errors,
        "declared_mode": "builder_only_scratch_diagnostic",
        "declared_modes_ok": True,
        "sim_id": SIM_ID,
        "result_path": rel(result_path),
        "validator": rel(Path(__file__)),
        "errors": errors,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    VALIDATOR_RESULT.parent.mkdir(parents=True, exist_ok=True)
    VALIDATOR_RESULT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
