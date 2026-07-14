#!/usr/bin/env python3
"""Fail-closed validator for the hardened Claude-campaign v2 envelope."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


EXPECTED_SCHEMA = "codex-ratchet.hardened-claude-campaign-envelope.v2"
EXPECTED_LANES = {"D", "F", "J", "K", "H"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(raw: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if raw.get("schema") != EXPECTED_SCHEMA:
        errors.append("schema mismatch")
    if raw.get("classification") != "integration_diagnostic":
        errors.append("classification must remain integration_diagnostic")
    if raw.get("promotion_allowed") is not False or raw.get("promotion_eligible") is not False:
        errors.append("promotion must remain blocked")
    if raw.get("formal_admission_allowed") is not False:
        errors.append("formal admission must remain blocked")
    if raw.get("runner_all_completed") is not True:
        errors.append("runner_all_completed must be true")
    if raw.get("capability_fit_all_pass") is not True:
        errors.append("bounded capability lanes must pass")
    if raw.get("all_pass") is not False:
        errors.append("campaign all_pass must remain false")
    if raw.get("truth_state") != "host_recomputed_blocked":
        errors.append("truth_state must remain host_recomputed_blocked")

    runtime_doctor = raw.get("runtime_doctor")
    if not isinstance(runtime_doctor, dict):
        errors.append("runtime_doctor must be present")
    else:
        gates = runtime_doctor.get("gates")
        if runtime_doctor.get("all_gates_pass") is not True or not isinstance(gates, dict) or not gates or not all(value is True for value in gates.values()):
            errors.append("runtime doctor gates must all pass")
        source_path = Path(str(runtime_doctor.get("source_path", "")))
        if not source_path.is_file() or sha256_file(source_path) != runtime_doctor.get("source_sha256"):
            errors.append("runtime doctor source hash mismatch")

    lanes = raw.get("lanes")
    if not isinstance(lanes, list):
        return [*errors, "lanes must be an array"]
    by_id = {lane.get("id"): lane for lane in lanes if isinstance(lane, dict)}
    if set(by_id) != EXPECTED_LANES:
        errors.append("lane ids must be exactly D,F,J,K,H")
        return errors
    for lane_id, lane in by_id.items():
        if lane.get("execution_and_receipt_ok") is not True:
            errors.append(f"lane {lane_id} execution/receipt gates are not true")
        if lane.get("exit_code") != 0:
            errors.append(f"lane {lane_id} exit code is not zero")
        gates = lane.get("gates")
        if not isinstance(gates, dict) or not gates or not all(value is True for value in gates.values()):
            errors.append(f"lane {lane_id} has a false or missing gate")
        result_path = Path(str(lane.get("result_path", "")))
        if not result_path.is_file():
            errors.append(f"lane {lane_id} result path is missing")
        elif sha256_file(result_path) != lane.get("result_sha256"):
            errors.append(f"lane {lane_id} result hash mismatch")
        source_path = Path(str(lane.get("producer_source_path", "")))
        if not source_path.is_file():
            errors.append(f"lane {lane_id} source path is missing")
        elif sha256_file(source_path) != lane.get("producer_source_sha256"):
            errors.append(f"lane {lane_id} source hash mismatch")

    for lane_id in ("D", "F", "J", "K"):
        if by_id[lane_id].get("receipt_all_pass") is not True:
            errors.append(f"lane {lane_id} must be bounded-green")
    if by_id["H"].get("receipt_all_pass") is not False:
        errors.append("lane H must remain false")
    if by_id["H"].get("receipt_audit_completed") is not True:
        errors.append("lane H semantics audit must complete")
    blockers = raw.get("summary", {}).get("semantic_blockers", [])
    if not any(isinstance(row, dict) and row.get("lane") == "H" for row in blockers):
        errors.append("H semantic blocker is missing")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("envelope", type=Path)
    args = parser.parse_args()
    try:
        raw = json.loads(args.envelope.read_text(encoding="utf-8"))
        errors = validate(raw)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        errors = [f"parse failure: {error}"]
    print(json.dumps({"ok": not errors, "errors": errors, "envelope": str(args.envelope.resolve())}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
