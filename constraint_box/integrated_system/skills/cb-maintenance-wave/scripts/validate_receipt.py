#!/usr/bin/env python3
"""Validate a CB maintenance receipt without trusting its status prose."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Sequence


SCHEMA = "constraintbox.maintenance-receipt.v1"
ALLOWED_CLASSIFICATIONS = {"KEEP_ACTIVE", "MOVE_TO_ARCHIVE", "MOVE_TO_QUARANTINE", "BLOCKED_REQUIRES_PREP"}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def expected_sha(receipt: dict[str, Any]) -> str:
    body = dict(receipt)
    body.pop("receipt_sha256", None)
    return hashlib.sha256(canonical_bytes(body)).hexdigest()


def validate(receipt: dict[str, Any], *, require_ready: bool = False) -> list[str]:
    errors: list[str] = []
    if receipt.get("schema") != SCHEMA:
        errors.append("INVALID_SCHEMA")
    if receipt.get("wave_id") != "cb-maintenance-wave-v1":
        errors.append("INVALID_WAVE_ID")
    if receipt.get("writes_allowed") is not False:
        errors.append("WRITES_NOT_DISABLED")
    if receipt.get("mutation_performed") is not False:
        errors.append("MUTATION_REPORTED")
    if receipt.get("moves_performed") != [] or receipt.get("deletions_performed") != []:
        errors.append("MUTATION_LIST_NOT_EMPTY")
    supplied = receipt.get("receipt_sha256")
    if not isinstance(supplied, str) or supplied != expected_sha(receipt):
        errors.append("RECEIPT_SELF_HASH_MISMATCH")
    for key in ("source_digest", "context_digest", "diagnostics", "candidate_decisions", "blockers", "child_receipts", "preload_receipts", "provider_call_receipt", "cancellation_state", "disagreement_state", "output_digest"):
        if key not in receipt:
            errors.append(f"MISSING_{key.upper()}")
    for decision in receipt.get("candidate_decisions", []):
        if decision.get("classification") not in ALLOWED_CLASSIFICATIONS:
            errors.append("INVALID_CANDIDATE_CLASSIFICATION")
    if receipt.get("status") not in {"READY", "HOLD"}:
        errors.append("INVALID_STATUS")
    if receipt.get("status") == "READY" and receipt.get("blockers"):
        errors.append("READY_WITH_BLOCKERS")
    if require_ready and receipt.get("status") != "READY":
        errors.append("NOT_READY")
    return sorted(set(errors))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args(argv or sys.argv[1:])
    path = Path(args.receipt)
    if not path.is_file():
        print(json.dumps({"valid": False, "errors": ["MISSING_RECEIPT"]}, sort_keys=True))
        return 2
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "errors": [f"INVALID_JSON:{type(exc).__name__}"]}, sort_keys=True))
        return 2
    errors = validate(receipt, require_ready=args.require_ready)
    print(json.dumps({"valid": not errors, "errors": errors, "status": receipt.get("status")}, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
