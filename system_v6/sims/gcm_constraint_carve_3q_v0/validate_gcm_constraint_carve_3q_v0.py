#!/usr/bin/env python3
"""Packet-local validator for gcm_constraint_carve_3q_v0."""

from __future__ import annotations

import json
import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Any

import gcm_constraint_carve_3q_v0_boundary as boundary
import gcm_constraint_carve_3q_v0_common as common


ROOT = common.ROOT
SIM_DIR = common.SIM_DIR
RESULT_DIR = common.RESULT_DIR
ENVELOPE = common.ENVELOPE_PATH
VALIDATOR_RESULT = common.VALIDATOR_RESULT_PATH

sys.path.insert(0, str(ROOT / "scripts"))
from validate_three_engine_sim_result import validate as validate_three_engine  # noqa: E402


CLASSIFICATION = common.CLASSIFICATION
TOOL_MANIFEST = common.TOOL_MANIFEST
TOOL_INTEGRATION_DEPTH = common.TOOL_INTEGRATION_DEPTH

REQUIRED_PACKET_FILES = [
    "build_card.md",
    f"{common.SIM_ID}_common.py",
    f"{common.SIM_ID}_boundary.py",
    f"{common.SIM_ID}.py",
    f"{common.SIM_ID}_julia.jl",
    f"{common.SIM_ID}_jax.py",
    f"{common.SIM_ID}_pytorch.py",
    "write_envelope_spec.py",
    f"{common.SIM_ID}_envelope.py",
    f"validate_{common.SIM_ID}.py",
    f"tests/test_{common.SIM_ID}.py",
]


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def hash_exists_in_git_history(expected_hash: str | None, path_text: str | None) -> bool:
    if not expected_hash or not path_text:
        return False
    try:
        commits = subprocess.check_output(
            ["git", "log", "--format=%H", "--", path_text],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).splitlines()
    except (OSError, subprocess.CalledProcessError):
        return False
    for commit in commits:
        try:
            blob = subprocess.check_output(
                ["git", "show", f"{commit}:{path_text}"],
                cwd=ROOT,
                stderr=subprocess.DEVNULL,
            )
        except (OSError, subprocess.CalledProcessError):
            continue
        if hashlib.sha256(blob).hexdigest() == expected_hash:
            return True
    return False


def historical_source_lock_valid(packet: dict[str, Any], key: str) -> bool:
    row = packet.get("source_locks", {}).get(key, {})
    if not isinstance(row, dict):
        return False
    path_text = row.get("path")
    current_path = ROOT / path_text if isinstance(path_text, str) else None
    if current_path and current_path.is_file() and row.get("sha256") == common.sha256_file(current_path):
        return True
    return hash_exists_in_git_history(row.get("sha256"), path_text)


def without_runtime_fields(payload: dict[str, Any]) -> dict[str, Any]:
    clone = json.loads(json.dumps(payload))
    clone.pop("generated_at", None)
    clone.pop("result_sha256", None)
    source_locks = clone.get("source_locks")
    if isinstance(source_locks, dict):
        for row in source_locks.values():
            if isinstance(row, dict):
                row.pop("git_last_commit", None)
        if "climb_ledger_correction" in source_locks:
            source_locks["climb_ledger_correction"].pop("sha256", None)
    return clone


def validate_packet_files(errors: list[str]) -> None:
    for rel_path in REQUIRED_PACKET_FILES:
        require(errors, (SIM_DIR / rel_path).is_file(), f"missing required packet file: {rel_path}")
    text = (SIM_DIR / "build_card.md").read_text(encoding="utf-8")
    for required in (
        "DECLARE: layers 1-2 (+17 tensor) | carve | 3Q",
        "gcmobj_a40e54e13cec01466c9d675028b3574b",
        "gcm_constraint_carve_2q_v0",
        "geo_s1_three_qubit_floor_exact_v0",
        "stage_lifted_spinor_shell_n3_v0",
        "f7b0ee5fe",
        "CKW",
        "GHZ",
        "W",
        "G.2a",
        "NO git add/commit",
        "scratch_diagnostic",
    ):
        require(errors, required in text, f"build_card.md missing {required}")


def validate_common_result(errors: list[str], packet: dict[str, Any]) -> None:
    rebuilt = common.build_packet()
    require(errors, historical_source_lock_valid(packet, "climb_ledger_correction"), "climb_ledger_correction source lock history missing")
    require(errors, without_runtime_fields(packet) == without_runtime_fields(rebuilt), "packet drift against source rebuild")
    errors.extend(common.validate_payload(packet))
    errors.extend(f"boundary: {err}" for err in boundary.boundary_errors(packet))
    require(errors, packet.get("schema") == "gcm_constraint_carve_3q_v0_result_v1", "common schema mismatch")
    require(errors, packet.get("coordinates") == {"layer": "layers 1-2 (+17 tensor)", "nesting": "carve", "qubit_depth": "3Q"}, "coordinates mismatch")
    require(errors, packet.get("survivor_count") == common.EXPECTED_SURVIVOR_COUNT, "survivor count mismatch")
    require(errors, packet.get("quotient", {}).get("class_count") == common.EXPECTED_QUOTIENT_CLASS_COUNT, "quotient class count mismatch")
    require(errors, packet.get("monogamy_ckw_row", {}).get("all_survivors_satisfy_ckw") is True, "CKW row failed")
    require(errors, packet.get("ghz_vs_w_admissibility", {}).get("constraints_distinguish_GHZ_and_W") is True, "GHZ/W distinction missing")
    require(errors, packet.get("controls", {}).get("probe_scramble", {}).get("quotient_moved") is True, "probe scramble did not move quotient")
    require(errors, all(row.get("bite") is True for row in packet.get("controls", {}).get("erasure_bite", [])), "not every erasure bites")


def validate_envelope(errors: list[str], payload: dict[str, Any]) -> None:
    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, payload.get("schema") == "gcm_constraint_carve_3q_v0_envelope_v1", "packet envelope schema mismatch")
    require(errors, payload.get("sim_id") == common.SIM_ID, "sim_id mismatch")
    require(errors, payload.get("mode") == common.ENGINE_MODE, "engine mode mismatch")
    require(errors, payload.get("classification") == common.CLASSIFICATION, "classification mismatch")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("claim_ceiling") == common.CLAIM_CEILING, "claim ceiling mismatch")
    require(errors, payload.get("all_pass") is True, "top-level all_pass false")
    require(errors, set(payload.get("engine_lanes", [])) == {"julia", "jax", "pytorch"}, "engine_lanes mismatch")
    consensus = payload.get("engine_consensus", {})
    for key in ("survivor_count_agreement", "quotient_class_count_agreement", "ckw_survivor_count_agreement", "floor_row_agreement"):
        require(errors, consensus.get(key) is True, f"engine consensus failed: {key}")
    require(errors, payload.get("TOOL_MANIFEST") == common.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, payload.get("TOOL_INTEGRATION_DEPTH") == common.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    require(errors, payload.get("tool_intent") == common.TOOL_INTENT, "tool_intent mismatch")
    errors.extend(f"boundary: {err}" for err in boundary.boundary_errors(payload))
    for engine in ("julia", "jax", "pytorch"):
        lane = load(RESULT_DIR / f"{common.SIM_ID}_{engine}_results.json")
        require(errors, lane.get("all_pass") is True, f"{engine} lane all_pass false")
        require(errors, payload.get("engines", {}).get(engine, {}).get("result_all_pass") is True, f"{engine} envelope result_all_pass false")
        require(errors, payload.get("engines", {}).get(engine, {}).get("reads_peer_result") is False, f"{engine} reads_peer_result must be false")
    generic_errors = validate_three_engine(payload, require_pytorch=True)
    errors.extend(f"generic three-engine validator: {err}" for err in generic_errors)


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    validate_packet_files(errors)
    packet = load(common.RESULT_PATH)
    validate_common_result(errors, packet)
    validate_envelope(errors, payload)
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
