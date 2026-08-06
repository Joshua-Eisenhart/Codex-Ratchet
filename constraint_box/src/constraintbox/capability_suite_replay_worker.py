"""Fixed child entry point for suite-side independent receipt replay."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from .failure_repair import (
    CAPABILITY_FLOW_RESULT_NAME,
    REPAIR_PLAN_NAME,
    verify_capability_result,
    write_repair_plan_for_run,
)
from .intake import IntakeError, canonical_json, parse_json_object


REQUEST_SCHEMA = "constraintbox.capability-suite-replay-request.v1"
RESULT_SCHEMA = "constraintbox.capability-suite-replay-result.v1"
_FIELDS = frozenset({"schema", "run_root"})


class CapabilitySuiteReplayWorkerError(ValueError):
    """The parent supplied no valid capability replay request."""


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _request_from_stdin() -> Path:
    try:
        value = json.loads(sys.stdin.buffer.read())
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CapabilitySuiteReplayWorkerError(
            f"replay request is invalid JSON: {exc}"
        ) from exc
    if not isinstance(value, dict) or set(value) != _FIELDS:
        raise CapabilitySuiteReplayWorkerError("replay request fields differ")
    if value.get("schema") != REQUEST_SCHEMA or not isinstance(value.get("run_root"), str):
        raise CapabilitySuiteReplayWorkerError("replay request differs")
    root = Path(value["run_root"])
    if not root.is_absolute():
        raise CapabilitySuiteReplayWorkerError("replay run root must be absolute")
    return root


def _load_result(root: Path) -> tuple[dict[str, Any], bytes]:
    path = root / CAPABILITY_FLOW_RESULT_NAME
    try:
        raw = path.read_bytes()
        result = parse_json_object(raw)
    except (OSError, IntakeError) as exc:
        raise CapabilitySuiteReplayWorkerError(
            f"canonical capability result is unavailable: {exc}"
        ) from exc
    if raw != canonical_json(result) + b"\n":
        raise CapabilitySuiteReplayWorkerError("canonical capability result differs")
    return result, raw


def main() -> int:
    try:
        root = _request_from_stdin()
        result, raw_result = _load_result(root)
        evidence = verify_capability_result(result, expected_run_root=root)
        repair_plan = None
        if result["disposition"] in {"BLOCKED", "PARKED"}:
            repair_plan = write_repair_plan_for_run(root)
    except (OSError, ValueError) as exc:
        print(
            f"capability-suite replay failed: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 5
    output: dict[str, Any] = {
        "schema": RESULT_SCHEMA,
        "capability_id": result["capability_id"],
        "disposition": result["disposition"],
        "capability_result_sha256": _sha256(canonical_json(result)),
        "origin_attestation_sha256": evidence["origin_attestation_sha256"],
        "flow_ledger_head_sha256": evidence["flow_ledger_head_sha256"],
        "independent_replay": True,
        "repair_plan": None,
    }
    if repair_plan is not None:
        output["repair_plan"] = {
            "path": str(root / REPAIR_PLAN_NAME),
            "repair_plan_sha256": repair_plan["repair_plan_sha256"],
            "selected_action": repair_plan["repair_plan"]["selected_action"],
            "execution_authorized": False,
        }
    sys.stdout.buffer.write(canonical_json(output) + b"\n")
    return {
        "ELIGIBLE": 0,
        "BLOCKED": 1,
        "PARKED": 4,
    }[result["disposition"]]


if __name__ == "__main__":
    raise SystemExit(main())
