"""Thin, host-neutral lifecycle accounting for CB host hooks.

This module is deliberately *not* a policy gate.  A host shim translates its
payload into the small event vocabulary below; this module only records
whether the lifecycle evidence is sufficient to relay or capture an event.
It never chooses a model, evaluates a terrain, or emits a semantic
disposition.

The important distinction is between a lifecycle-valid capture and a result
that is semantically accepted.  The former can be proved here.  The latter is
outside this module and is never represented as ``operation_success=True``.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

SCHEMA = "constraintbox.hook_lifecycle.v1"

SESSION_BIND = "session_bind"
PRE_EXECUTION = "pre_execution"
POST_RESULT = "post_result"
CANCEL = "cancel"
BYPASS = "bypass"

SESSION_BOUND = "SESSION_BOUND"
RELAYED = "RELAYED"
CAPTURED = "CAPTURED"
CANCELLED = "CANCELLED"
CANCELLED_NO_AUTHORITY = "CANCELLED_NO_AUTHORITY"
NO_AUTHORITY = "NO_AUTHORITY"
BYPASS_OBSERVED = "BYPASS_OBSERVED"

_HOSTS = {"codex", "claude", "grok", "hermes", "unknown"}


class HookLifecycleError(RuntimeError):
    """Base error for malformed lifecycle state or an unwritable log."""


class HookChainError(HookLifecycleError):
    """The append-only event log is malformed or has been changed."""


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _first_string(value: Mapping[str, Any], names: tuple[str, ...]) -> str | None:
    for name in names:
        candidate = value.get(name)
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return None


def _nested_maps(payload: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    maps: list[Mapping[str, Any]] = [payload]
    for key in (
        "extra",
        "metadata",
        "context",
        "session",
        "tool",
        "result",
        "args",
        "input",
        "tool_input",
    ):
        value = payload.get(key)
        if isinstance(value, Mapping):
            maps.append(value)
    return tuple(maps)


def _find_string(payload: Mapping[str, Any], names: tuple[str, ...]) -> str | None:
    for source in _nested_maps(payload):
        found = _first_string(source, names)
        if found is not None:
            return found
    return None


def _host_name(payload: Mapping[str, Any], host_hint: str | None) -> str:
    candidate = host_hint or _find_string(
        payload, ("host", "host_name", "hostName", "provider", "source")
    )
    if isinstance(candidate, str):
        value = candidate.strip().lower().replace("_", "-")
        if value in _HOSTS:
            return value
        if value in {"claude-code", "claude_family"}:
            return "claude"
        if value in {"grok-cli", "grok-build"}:
            return "grok"
    # Hermes uses a distinct event spelling and carries task_id in ``extra``.
    raw_event = _find_string(
        payload,
        ("hook_event_name", "hookEventName", "event", "event_type", "type"),
    )
    extra = payload.get("extra")
    if raw_event == "pre_tool_call" or (
        isinstance(extra, Mapping) and isinstance(extra.get("task_id"), str)
    ):
        return "hermes"
    return "unknown"


def _event_name(payload: Mapping[str, Any]) -> str | None:
    return _find_string(
        payload,
        ("hook_event_name", "hookEventName", "event", "event_type", "type"),
    )


def _event_type(payload: Mapping[str, Any], raw_event: str | None) -> tuple[str, str | None]:
    """Map host spellings into lifecycle verbs, never into policy decisions."""

    flags = ("cancelled", "canceled", "cancel", "stop_requested", "bypass", "unmanaged")
    if any(payload.get(flag) is True for flag in flags[:4]):
        return CANCEL, "host_cancel_flag"
    if any(payload.get(flag) is True for flag in flags[4:]):
        return BYPASS, "host_bypass_flag"

    raw = (raw_event or "").strip().lower().replace("-", "_").replace(" ", "_")
    compact = raw.replace("_", "")
    if compact in {"sessionstart", "sessionstarted", "onsessionstart", "bind"}:
        return SESSION_BIND, None
    if compact in {
        "pretooluse",
        "pretoolcall",
        "preexecution",
        "beforetool",
        "beforeexecution",
        "relay",
    }:
        return PRE_EXECUTION, None
    if compact in {
        "posttooluse",
        "posttoolcall",
        "postexecution",
        "aftertool",
        "afterexecution",
        "result",
        "capture",
    }:
        return POST_RESULT, None
    if compact in {
        "stop",
        "onstop",
        "cancel",
        "cancelled",
        "canceled",
        "abort",
        "abortrequested",
        "cancellation",
    }:
        return CANCEL, None
    return BYPASS, "unknown_or_missing_event"


def _result_digest(payload: Mapping[str, Any]) -> str | None:
    for name in (
        "tool_result",
        "toolResult",
        "result",
        "output",
        "tool_output",
        "toolOutput",
    ):
        if name in payload and payload[name] is not None:
            return _digest(payload[name])
    return None


@dataclass(frozen=True, slots=True)
class NormalizedHook:
    """The host-independent facts needed by the lifecycle recorder."""

    host: str
    event_type: str
    source_event: str | None
    session_id: str | None
    invocation_id: str | None
    tool_name: str | None
    result_sha256: str | None
    source_sha256: str
    normalization_note: str | None = None


def normalize_host_payload(
    payload: Mapping[str, Any] | Any,
    *,
    host_hint: str | None = None,
    source_bytes: bytes | None = None,
) -> NormalizedHook:
    """Normalize Codex, Claude, Grok, and Hermes-shaped hook payloads.

    The source digest covers the complete received object (or the original
    bytes when the shim has them).  Only selected identifiers are retained in
    the lifecycle event; tool arguments and result bodies are not interpreted.
    """

    if not isinstance(payload, Mapping):
        raw = source_bytes if source_bytes is not None else repr(payload).encode("utf-8")
        return NormalizedHook(
            host="unknown",
            event_type=BYPASS,
            source_event=None,
            session_id=None,
            invocation_id=None,
            tool_name=None,
            result_sha256=None,
            source_sha256=_digest_bytes(raw),
            normalization_note="non_object_payload",
        )

    raw_event = _event_name(payload)
    event_type, note = _event_type(payload, raw_event)
    session_id = _find_string(
        payload,
        (
            "session_id",
            "sessionId",
            "conversation_id",
            "conversationId",
            "thread_id",
            "threadId",
            "task_id",
        ),
    )
    invocation_id = _find_string(
        payload,
        (
            "tool_use_id",
            "toolUseId",
            "tool_call_id",
            "toolCallId",
            "call_id",
            "callId",
            "invocation_id",
            "invocationId",
        ),
    )
    tool_name = _find_string(payload, ("tool_name", "toolName", "tool", "name"))
    source_sha = (
        _digest_bytes(source_bytes)
        if source_bytes is not None
        else _digest(dict(payload))
    )
    return NormalizedHook(
        host=_host_name(payload, host_hint),
        event_type=event_type,
        source_event=raw_event,
        session_id=session_id,
        invocation_id=invocation_id,
        tool_name=tool_name,
        result_sha256=_result_digest(payload),
        source_sha256=source_sha,
        normalization_note=note,
    )


def _verify_lines(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    previous = ""
    with path.open("r", encoding="utf-8") as handle:
        for expected_sequence, line in enumerate(handle, start=1):
            if not line.strip():
                raise HookChainError(f"blank line at sequence {expected_sequence}")
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise HookChainError(f"invalid JSON at sequence {expected_sequence}") from exc
            if not isinstance(row, dict):
                raise HookChainError(f"non-object event at sequence {expected_sequence}")
            actual_hash = row.pop("event_sha256", None)
            expected_hash = hashlib.sha256(_canonical(row)).hexdigest()
            if actual_hash != expected_hash:
                raise HookChainError(f"event digest mismatch at sequence {expected_sequence}")
            if row.get("sequence") != expected_sequence:
                raise HookChainError(f"sequence mismatch at sequence {expected_sequence}")
            if row.get("previous_event_sha256", "") != previous:
                raise HookChainError(f"chain mismatch at sequence {expected_sequence}")
            row["event_sha256"] = actual_hash
            rows.append(row)
            previous = actual_hash
    return rows


def verify_event_log(path: str | os.PathLike[str]) -> list[dict[str, Any]]:
    """Verify and return a hash-chained lifecycle log."""

    return _verify_lines(Path(path))


class HookLifecycle:
    """Append-only lifecycle recorder with no semantic decision authority."""

    def __init__(
        self,
        path: str | os.PathLike[str],
        *,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.path = Path(path)
        self._clock = clock or time.time
        self._bound: set[str] = set()
        self._cancelled: set[str] = set()
        self._active: dict[str, str] = {}
        self._completed: set[str] = set()
        self._sequence = 0
        self._previous_hash = ""
        for row in _verify_lines(self.path):
            self._replay(row)
            self._sequence = int(row["sequence"])
            self._previous_hash = str(row["event_sha256"])

    def _replay(self, row: Mapping[str, Any]) -> None:
        event_type = row.get("event_type")
        session_id = row.get("session_id")
        invocation_id = row.get("invocation_id")
        status = row.get("status")
        if not isinstance(session_id, str) or not session_id:
            return
        if event_type == SESSION_BIND and status == SESSION_BOUND:
            self._bound.add(session_id)
        elif event_type == PRE_EXECUTION and status == RELAYED and isinstance(invocation_id, str):
            self._active[invocation_id] = session_id
        elif event_type == POST_RESULT and status == CAPTURED and isinstance(invocation_id, str):
            self._active.pop(invocation_id, None)
            self._completed.add(invocation_id)
        elif event_type == CANCEL and status in {CANCELLED, CANCELLED_NO_AUTHORITY}:
            self._cancelled.add(session_id)
            if isinstance(invocation_id, str):
                self._active.pop(invocation_id, None)
            else:
                for active_id, active_session in tuple(self._active.items()):
                    if active_session == session_id:
                        self._active.pop(active_id, None)

    def _append(self, body: dict[str, Any]) -> dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._sequence += 1
        body = {
            "schema": SCHEMA,
            "sequence": self._sequence,
            "event_id": f"hook-{self._sequence:08d}",
            "previous_event_sha256": self._previous_hash,
            **body,
        }
        event_hash = hashlib.sha256(_canonical(body)).hexdigest()
        row = {**body, "event_sha256": event_hash}
        try:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
        except OSError as exc:
            self._sequence -= 1
            raise HookLifecycleError("lifecycle receipt write failed") from exc
        self._previous_hash = event_hash
        return row

    def record(
        self,
        payload: Mapping[str, Any] | Any,
        *,
        host_hint: str | None = None,
        source_bytes: bytes | None = None,
        timestamp: float | None = None,
    ) -> dict[str, Any]:
        """Record one host event and return its lifecycle-only receipt."""

        normalized = normalize_host_payload(
            payload, host_hint=host_hint, source_bytes=source_bytes
        )
        session_id = normalized.session_id
        invocation_id = normalized.invocation_id
        status = NO_AUTHORITY
        note = normalized.normalization_note
        lifecycle_valid = False
        post_capture_eligible = False
        authority_removed = normalized.event_type in {PRE_EXECUTION, CANCEL, BYPASS}
        operation_success: bool | None = None
        before_bound = set(self._bound)
        before_cancelled = set(self._cancelled)
        before_active = dict(self._active)
        before_completed = set(self._completed)

        if normalized.event_type == SESSION_BIND:
            if session_id and session_id not in self._cancelled:
                self._bound.add(session_id)
                status = SESSION_BOUND
                lifecycle_valid = True
            else:
                note = note or "missing_or_cancelled_session"
        elif normalized.event_type == PRE_EXECUTION:
            if not session_id:
                note = note or "missing_session"
            elif session_id not in self._bound:
                note = note or "session_not_bound"
            elif session_id in self._cancelled:
                note = note or "session_cancelled"
            elif not invocation_id:
                note = note or "missing_invocation"
            elif invocation_id in self._active or invocation_id in self._completed:
                note = note or "invocation_reused"
            else:
                self._active[invocation_id] = session_id
                status = RELAYED
                lifecycle_valid = True
        elif normalized.event_type == POST_RESULT:
            if not session_id:
                note = note or "missing_session"
            elif session_id not in self._bound:
                note = note or "session_not_bound"
            elif session_id in self._cancelled:
                note = note or "session_cancelled"
            elif not invocation_id:
                note = note or "missing_invocation"
            elif self._active.get(invocation_id) != session_id:
                note = note or "pre_execution_not_recorded"
            else:
                self._active.pop(invocation_id, None)
                self._completed.add(invocation_id)
                status = CAPTURED
                lifecycle_valid = True
                post_capture_eligible = True
        elif normalized.event_type == CANCEL:
            authority_removed = True
            if session_id:
                self._cancelled.add(session_id)
                if invocation_id:
                    self._active.pop(invocation_id, None)
                else:
                    for active_id, active_session in tuple(self._active.items()):
                        if active_session == session_id:
                            self._active.pop(active_id, None)
                status = CANCELLED if session_id in self._bound else CANCELLED_NO_AUTHORITY
                lifecycle_valid = status == CANCELLED
                operation_success = False
            else:
                status = CANCELLED_NO_AUTHORITY
                operation_success = False
                note = note or "missing_session"
        else:
            status = BYPASS_OBSERVED
            authority_removed = True
            note = note or "bypass_or_unrecognized_event"

        try:
            row = self._append(
                {
                    "timestamp": self._clock() if timestamp is None else float(timestamp),
                    "host": normalized.host,
                    "event_type": normalized.event_type,
                    "source_event": normalized.source_event,
                    "session_id": session_id,
                    "invocation_id": invocation_id,
                    "tool_name": normalized.tool_name,
                    "result_sha256": normalized.result_sha256,
                    "source_sha256": normalized.source_sha256,
                    "status": status,
                    "lifecycle_valid": lifecycle_valid,
                    "post_capture_eligible": post_capture_eligible,
                    "authority_removed": authority_removed,
                    "operation_success": operation_success,
                    "semantic_disposition": None,
                    "note": note,
                }
            )
        except HookLifecycleError:
            # A lifecycle transition is not real until its receipt is durable.
            self._bound = before_bound
            self._cancelled = before_cancelled
            self._active = before_active
            self._completed = before_completed
            raise
        return row

    def events(self) -> list[dict[str, Any]]:
        return verify_event_log(self.path)


__all__ = [
    "BYPASS",
    "BYPASS_OBSERVED",
    "CANCEL",
    "CANCELLED",
    "CANCELLED_NO_AUTHORITY",
    "CAPTURED",
    "HookChainError",
    "HookLifecycle",
    "HookLifecycleError",
    "NormalizedHook",
    "NO_AUTHORITY",
    "POST_RESULT",
    "PRE_EXECUTION",
    "RELAYED",
    "SCHEMA",
    "SESSION_BIND",
    "SESSION_BOUND",
    "normalize_host_payload",
    "verify_event_log",
]
