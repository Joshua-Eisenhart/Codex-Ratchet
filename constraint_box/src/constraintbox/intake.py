from __future__ import annotations

import json
import math
from typing import Any


class IntakeError(ValueError):
    pass


def _finite_walk(value: Any, path: str = "$") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise IntakeError(f"non-finite number at {path}")
    if isinstance(value, dict):
        for key, child in value.items():
            _finite_walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _finite_walk(child, f"{path}[{index}]")


def parse_json_value(raw: bytes) -> Any:
    """Parse one immutable byte snapshot and reject ambiguous JSON."""

    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in pairs:
            if key in out:
                raise IntakeError(f"duplicate JSON key: {key}")
            out[key] = value
        return out

    def no_constants(token: str) -> None:
        raise IntakeError(f"non-finite JSON token: {token}")

    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=no_duplicates,
            parse_constant=no_constants,
        )
    except IntakeError:
        raise
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        ValueError,
        RecursionError,
    ) as exc:
        raise IntakeError(f"invalid JSON: {exc}") from exc
    try:
        _finite_walk(value)
    except RecursionError as exc:
        raise IntakeError("JSON nesting exceeds the supported depth") from exc
    return value


def parse_json_object(raw: bytes) -> dict[str, Any]:
    value = parse_json_value(raw)
    if not isinstance(value, dict):
        raise IntakeError("root JSON value must be an object")
    return value


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
