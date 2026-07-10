#!/usr/bin/env python3
"""Fail-closed validator for the frozen object-formation preregistration."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
CLASSIFICATION = "scratch_diagnostic"
TOOL_MANIFEST = {
    "python_stdlib": {"tried": True, "used": True, "reason": "Strict JSON, SHA-256 binding, and fail-closed receipt validation."},
}
TOOL_INTEGRATION_DEPTH = {"python_stdlib": "supportive"}
SPEC_PATH = HERE / "spec.json"
PREREG_PATH = HERE / "preregistration_receipt.json"
DEFAULT_OUTPUT = HERE / "results" / "preregistration_validation.json"

SPEC_KEYS = {
    "schema", "sim_id", "classification", "promotion_allowed",
    "formal_admission_allowed", "claim", "explicit_non_claims", "carrier",
    "depth_census", "fixtures", "candidate_cycle", "perspective_contract",
    "gates", "engine_contract", "accepted_green_ceiling",
    "accepted_red_ceiling", "blocked_consumers", "preregistration_correction",
}
PREREG_KEYS = {
    "schema", "sim_id", "frozen_at", "status", "classification",
    "promotion_allowed", "formal_admission_allowed", "spec_path",
    "spec_sha256", "readme_sha256_at_freeze", "frozen_decisions",
    "anti_selection_rules", "required_outputs", "superseded_spec_sha256",
    "correction_path", "correction_sha256",
}
ROLE_NAMES = ["measure", "distinguish", "quotient", "gate"]
EXPECTED_COUNTS = {
    "all": {"1": 4636, "2": 14656, "3": 692, "4": 16},
    "non_discrete": {"1": 618, "2": 1523, "3": 75, "4": 3},
}


class ValidationError(RuntimeError):
    pass


def reject_constant(token: str) -> None:
    raise ValidationError(f"non-finite JSON constant: {token}")


def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_strict(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=reject_constant,
            object_pairs_hook=reject_duplicates,
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain one JSON object")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def require_exact_keys(value: dict[str, Any], expected: set[str], name: str) -> None:
    observed = set(value)
    require(
        observed == expected,
        f"{name} keys differ: missing={sorted(expected - observed)}, "
        f"extra={sorted(observed - expected)}",
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate() -> dict[str, Any]:
    spec = load_strict(SPEC_PATH)
    prereg = load_strict(PREREG_PATH)
    require_exact_keys(spec, SPEC_KEYS, "spec")
    require_exact_keys(prereg, PREREG_KEYS, "preregistration")
    require(spec["sim_id"] == prereg["sim_id"], "sim_id mismatch")
    require(
        prereg["status"] == "frozen_correction_before_result_acceptance",
        "corrected preregistration not frozen",
    )
    require(spec["classification"] == "scratch_diagnostic", "classification drift")
    require(spec["promotion_allowed"] is False, "promotion must remain blocked")
    require(spec["formal_admission_allowed"] is False, "formal admission must remain blocked")
    require(prereg["spec_sha256"] == sha256(SPEC_PATH), "live spec hash differs from freeze")
    correction_path = HERE / "PREREGISTRATION_CORRECTION.md"
    require(
        prereg["correction_sha256"] == sha256(correction_path),
        "correction receipt differs from freeze",
    )
    require(
        prereg["readme_sha256_at_freeze"] == sha256(HERE / "README.md"),
        "README claim boundary differs from freeze",
    )
    require(
        spec["depth_census"]["frozen_expected_counts"] == EXPECTED_COUNTS,
        "frozen census counts drifted",
    )
    require(
        [entry.get("role") for entry in spec["candidate_cycle"]] == ROLE_NAMES,
        "candidate roles or order drifted",
    )
    require(
        spec["fixtures"]["target_depth4_non_discrete"] == [8565, 10288, 19937],
        "target fixture selection drifted",
    )
    require(spec["fixtures"]["depth1_controls"] == [4, 5, 8], "depth-one controls drifted")
    require(spec["fixtures"]["depth2_controls"] == [1, 2, 3], "depth-two controls drifted")
    require(spec["fixtures"]["depth3_controls"] == [11, 19, 37], "depth-three controls drifted")
    require(
        spec["engine_contract"]["mode"] == "julia_canon_jax_workhorse",
        "engine mode drifted",
    )
    require(
        "four roles are not four QIT substages" in spec["explicit_non_claims"],
        "four-count anti-overclaim clause removed",
    )
    return {
        "schema": "codex_ratchet.finite_dual_ratchet_object_formation_v0.preregistration_validation.v1",
        "sim_id": spec["sim_id"],
        "classification": "scratch_diagnostic",
        "all_pass": True,
        "spec_sha256": sha256(SPEC_PATH),
        "preregistration_sha256": sha256(PREREG_PATH),
        "readme_sha256": sha256(HERE / "README.md"),
        "frozen_role_order": ROLE_NAMES,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        result = validate()
    except ValidationError as exc:
        result = {
            "schema": "codex_ratchet.finite_dual_ratchet_object_formation_v0.preregistration_validation.v1",
            "sim_id": "finite_dual_ratchet_object_formation_v0",
            "classification": "scratch_diagnostic",
            "all_pass": False,
            "error": str(exc),
            "promotion_allowed": False,
            "formal_admission_allowed": False,
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
