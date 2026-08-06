"""Fixed fresh-child verifier for one already-dispatched repair rerun."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from .capability_origin import CAPABILITY_FLOW_RESULT_NAME
from .failure_repair import verify_capability_result
from .intake import IntakeError, canonical_json, parse_json_object


REQUEST_SCHEMA = "constraintbox.repair-outcome-replay-request.v1"
RESULT_SCHEMA = "constraintbox.repair-outcome-replay-result.v1"
_REQUEST_FIELDS = frozenset({"schema", "run_root"})


class RepairOutcomeReplayWorkerError(ValueError):
    """The parent supplied no strict, bounded rerun-verification request."""


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _request_from_stdin() -> Path:
    raw = sys.stdin.buffer.read()
    try:
        value = parse_json_object(raw)
    except IntakeError as exc:
        raise RepairOutcomeReplayWorkerError(
            f"replay request is invalid strict JSON: {exc}"
        ) from exc
    if raw != canonical_json(value):
        raise RepairOutcomeReplayWorkerError("replay request is not canonical JSON")
    if not isinstance(value, dict) or set(value) != _REQUEST_FIELDS:
        raise RepairOutcomeReplayWorkerError("replay request fields differ")
    if value.get("schema") != REQUEST_SCHEMA or not isinstance(value.get("run_root"), str):
        raise RepairOutcomeReplayWorkerError("replay request differs")
    root = Path(value["run_root"])
    if not root.is_absolute() or root.is_symlink():
        raise RepairOutcomeReplayWorkerError("replay run root must be absolute and non-symlink")
    try:
        root = root.resolve(strict=True)
    except OSError as exc:
        raise RepairOutcomeReplayWorkerError(f"replay run root is unavailable: {exc}") from exc
    if not root.is_dir():
        raise RepairOutcomeReplayWorkerError("replay run root must be one directory")
    return root


def _load_result(root: Path) -> dict[str, Any]:
    path = root / CAPABILITY_FLOW_RESULT_NAME
    try:
        raw = path.read_bytes()
        result = parse_json_object(raw)
    except (OSError, IntakeError) as exc:
        raise RepairOutcomeReplayWorkerError(
            f"canonical capability result is unavailable: {exc}"
        ) from exc
    if raw != canonical_json(result) + b"\n":
        raise RepairOutcomeReplayWorkerError("canonical capability result differs")
    return result


def main() -> int:
    try:
        root = _request_from_stdin()
        result = _load_result(root)
        evidence = verify_capability_result(result, expected_run_root=root)
    except (OSError, ValueError) as exc:
        print(
            f"repair-outcome replay failed: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 5
    output = {
        "schema": RESULT_SCHEMA,
        "capability_id": result["capability_id"],
        "disposition": result["disposition"],
        "capability_result_sha256": _sha256(canonical_json(result)),
        "origin_attestation_sha256": evidence["origin_attestation_sha256"],
        "flow_ledger_head_sha256": evidence["flow_ledger_head_sha256"],
        "runtime_identity_sha256": evidence["runtime_identity_sha256"],
        "independent_replay": True,
    }
    sys.stdout.buffer.write(canonical_json(output) + b"\n")
    return {
        "ELIGIBLE": 0,
        "BLOCKED": 1,
        "PARKED": 4,
    }[result["disposition"]]


if __name__ == "__main__":
    raise SystemExit(main())
