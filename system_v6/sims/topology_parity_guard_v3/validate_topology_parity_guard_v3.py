#!/usr/bin/env python3
"""Packet-local validator for topology_parity_guard_v3."""

from __future__ import annotations

import json
import hashlib
import subprocess
from typing import Any

import topology_parity_guard_v3_boundary as boundary
import topology_parity_guard_v3_common as common


TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "writes the validator receipt"},
    "topology_parity_guard_v3_boundary": {"tried": True, "used": True, "reason": "runs packet boundary checks"},
    "topology_parity_guard_v3_common": {"tried": True, "used": True, "reason": "rebuilds the consumer packet for drift checks"},
}
TOOL_INTEGRATION_DEPTH = {
    "json": "supportive",
    "topology_parity_guard_v3_boundary": "load_bearing",
    "topology_parity_guard_v3_common": "load_bearing",
}
REQUIRED_PACKET_FILES = [
    "build_card.md",
    "builder_self_assessment.md",
    "topology_parity_guard_v3.py",
    "topology_parity_guard_v3_envelope.py",
    "topology_parity_guard_v3_common.py",
    "topology_parity_guard_v3_boundary.py",
    "validate_topology_parity_guard_v3.py",
    "tests/test_topology_parity_guard_v3.py",
]


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def hash_exists_in_git_history(expected_hash: str | None, path_text: str | None) -> bool:
    if not expected_hash or not path_text:
        return False
    try:
        commits = subprocess.check_output(
            ["git", "log", "--format=%H", "--", path_text],
            cwd=common.ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).splitlines()
    except (OSError, subprocess.CalledProcessError):
        return False
    for commit in commits:
        try:
            blob = subprocess.check_output(
                ["git", "show", f"{commit}:{path_text}"],
                cwd=common.ROOT,
                stderr=subprocess.DEVNULL,
            )
        except (OSError, subprocess.CalledProcessError):
            continue
        if hashlib.sha256(blob).hexdigest() == expected_hash:
            return True
    return False


def source_complex_lock_for_compare(lock: Any) -> Any:
    clone = json.loads(json.dumps(lock))
    row = clone.get("axis_work_order") if isinstance(clone, dict) else None
    if isinstance(row, dict):
        row.pop("sha256", None)
        row.pop("git_last_commit", None)
    return clone


def source_complex_lock_valid(stored: Any, rebuilt: Any) -> bool:
    if source_complex_lock_for_compare(stored) != source_complex_lock_for_compare(rebuilt):
        return False
    row = stored.get("axis_work_order") if isinstance(stored, dict) else None
    if not isinstance(row, dict):
        return False
    current = (common.ROOT / row.get("path", "")).resolve()
    if current.is_file() and row.get("sha256") == common.sha256_file(current):
        return True
    return hash_exists_in_git_history(row.get("sha256"), row.get("path"))


def load_or_build() -> dict[str, Any]:
    if common.RESULT_PATH.exists():
        return common.load_json(common.RESULT_PATH)
    return common.build_topology_parity_guard_v3_object()


def validate_packet_files(errors: list[str]) -> None:
    for rel_path in REQUIRED_PACKET_FILES:
        require(errors, (common.SIM_DIR / rel_path).is_file(), f"missing required packet file: {rel_path}")
    card = common.SIM_DIR / "build_card.md"
    text = card.read_text(encoding="utf-8") if card.is_file() else ""
    for phrase in (
        common.SIM_ID,
        "G.2a",
        "scratch_diagnostic",
        "target Betti fitting",
        "boundary-matrix-only",
        "L(3,1)",
        "H1 = Z/3",
        "READING_A_REPAIRED_WINS",
        "NO new construction",
    ):
        require(errors, phrase in text, f"build_card missing required phrase: {phrase}")


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    validate_packet_files(errors)
    rebuilt = common.build_topology_parity_guard_v3_object()
    for key in (
        "sim_id",
        "classification",
        "promotion_allowed",
        "formal_admission_allowed",
        "claim_ceiling",
        "expected_profiles_preregistered_from_math",
        "source_complex_lock",
        "reference_gate",
        "math_content_separability",
        "complexes",
        "controls",
        "expectation_results",
        "adjudication",
        "TOOL_MANIFEST",
        "TOOL_INTEGRATION_DEPTH",
        "all_pass",
    ):
        if key == "source_complex_lock":
            require(errors, source_complex_lock_valid(payload.get(key), rebuilt.get(key)), f"{key} drifted")
        else:
            require(errors, payload.get(key) == rebuilt.get(key), f"{key} drifted")
    require(errors, payload.get("TOOL_MANIFEST") == common.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, payload.get("TOOL_INTEGRATION_DEPTH") == common.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    require(errors, payload.get("all_pass") is True, "consumer execution gates must pass")
    errors.extend(boundary.boundary_errors(payload, common.SIM_DIR))
    return errors


def main() -> int:
    payload = load_or_build()
    errors = validate_payload(payload)
    result = {"ok": not errors, "result_json": common.rel(common.RESULT_PATH), "errors": errors}
    common.write_json(common.VALIDATOR_RESULT_PATH, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
