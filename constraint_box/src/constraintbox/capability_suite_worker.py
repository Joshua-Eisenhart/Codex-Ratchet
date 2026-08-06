"""Fixed child entry point for one capability-suite component.

The parent suite deliberately uses a fresh CPython process for each external
profile. This prevents an optional package's process state, allocator pressure,
or native-library failure from silently contaminating later profiles. The
parent owns the finite order and consumes the resulting artifacts separately.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from .capability_dispatch import run_capability_flow
from .intake import canonical_json


REQUEST_SCHEMA = "constraintbox.capability-suite-component-request.v1"
_FIELDS = frozenset({"schema", "capability_id", "request_id", "run_root"})


class CapabilitySuiteWorkerError(ValueError):
    """The parent supplied no valid fixed component request."""


def _request_from_stdin() -> dict[str, Any]:
    try:
        value = json.loads(sys.stdin.buffer.read())
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CapabilitySuiteWorkerError(f"component request is invalid JSON: {exc}") from exc
    if not isinstance(value, dict) or set(value) != _FIELDS:
        raise CapabilitySuiteWorkerError("component request fields differ")
    if value.get("schema") != REQUEST_SCHEMA:
        raise CapabilitySuiteWorkerError("component request schema differs")
    if not isinstance(value.get("capability_id"), str) or not isinstance(
        value.get("request_id"), str
    ):
        raise CapabilitySuiteWorkerError("component request identifiers are invalid")
    run_root = value.get("run_root")
    if not isinstance(run_root, str):
        raise CapabilitySuiteWorkerError("component request run root is invalid")
    path = Path(run_root)
    if not path.is_absolute():
        raise CapabilitySuiteWorkerError("component request run root must be absolute")
    return value


def main() -> int:
    try:
        request = _request_from_stdin()
        result = run_capability_flow(
            capability_id=request["capability_id"],
            request_id=request["request_id"],
            run_root=Path(request["run_root"]),
        )
    except (OSError, ValueError) as exc:
        print(f"capability-suite component failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 5
    sys.stdout.buffer.write(canonical_json(result) + b"\n")
    return {
        "ELIGIBLE": 0,
        "BLOCKED": 1,
        "PARKED": 4,
        "HOLD": 5,
    }.get(result.get("disposition"), 5)


if __name__ == "__main__":
    raise SystemExit(main())
