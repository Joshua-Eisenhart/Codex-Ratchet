"""Deterministic host-shim and lifecycle tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import constraintbox.hook_lifecycle as hook_lifecycle_module

from constraintbox.hook_lifecycle import (
    BYPASS_OBSERVED,
    CANCELLED,
    CANCELLED_NO_AUTHORITY,
    CAPTURED,
    HookChainError,
    HookLifecycle,
    NO_AUTHORITY,
    RELAYED,
    SESSION_BOUND,
    normalize_host_payload,
    verify_event_log,
)


def _session(host: str, session_id: str) -> dict:
    if host == "hermes":
        return {"event": "on_session_start", "extra": {"task_id": session_id}}
    if host == "grok":
        return {"hookEventName": "SessionStart", "sessionId": session_id}
    return {"hook_event_name": "SessionStart", "session_id": session_id}


def _pre(host: str, session_id: str, invocation_id: str) -> dict:
    if host == "hermes":
        return {
            "event": "pre_tool_call",
            "extra": {"task_id": session_id},
            "tool": "terminal",
            "args": {"invocation_id": invocation_id},
        }
    if host == "grok":
        return {
            "hookEventName": "pre_tool_use",
            "sessionId": session_id,
            "toolUseId": invocation_id,
            "toolName": "terminal",
            "toolInput": {"command": "echo probe"},
        }
    return {
        "hook_event_name": "PreToolUse",
        "session_id": session_id,
        "tool_use_id": invocation_id,
        "tool_name": "Bash",
        "tool_input": {"command": "echo probe"},
    }


def _post(host: str, session_id: str, invocation_id: str) -> dict:
    if host == "hermes":
        return {
            "event": "post_tool_call",
            "extra": {"task_id": session_id, "call_id": invocation_id},
            "result": {"exit_code": 0},
        }
    if host == "grok":
        return {
            "hookEventName": "post_tool_use",
            "sessionId": session_id,
            "toolUseId": invocation_id,
            "toolOutput": {"exit_code": 0},
        }
    return {
        "hook_event_name": "PostToolUse",
        "session_id": session_id,
        "tool_use_id": invocation_id,
        "tool_result": {"exit_code": 0},
    }


@pytest.mark.parametrize("host", ["codex", "claude", "grok", "hermes"])
def test_four_host_shapes_normalize(host: str) -> None:
    session_id = f"s-{host}"
    invocation_id = f"i-{host}"
    assert normalize_host_payload(_session(host, session_id), host_hint=host).event_type == "session_bind"
    pre = normalize_host_payload(_pre(host, session_id, invocation_id), host_hint=host)
    post = normalize_host_payload(_post(host, session_id, invocation_id), host_hint=host)
    assert pre.event_type == "pre_execution"
    assert pre.session_id == session_id
    assert pre.invocation_id == invocation_id
    assert post.event_type == "post_result"
    assert post.result_sha256
    assert pre.host == post.host == host


def test_hermes_host_can_be_inferred_from_event() -> None:
    normalized = normalize_host_payload(_session("hermes", "s-hermes"))
    assert normalized.host == "hermes"


def test_session_pre_post_is_lifecycle_only(tmp_path: Path) -> None:
    log = tmp_path / "events.jsonl"
    life = HookLifecycle(log, clock=lambda: 100.0)
    session = life.record(_session("claude", "s1"), host_hint="claude", timestamp=1)
    pre = life.record(_pre("claude", "s1", "i1"), host_hint="claude", timestamp=2)
    post = life.record(_post("claude", "s1", "i1"), host_hint="claude", timestamp=3)

    assert session["status"] == SESSION_BOUND
    assert pre["status"] == RELAYED
    assert pre["authority_removed"] is True
    assert post["status"] == CAPTURED
    assert post["post_capture_eligible"] is True
    assert post["operation_success"] is None
    assert post["semantic_disposition"] is None
    assert verify_event_log(log)[-1]["event_sha256"] == post["event_sha256"]


def test_post_without_session_or_pre_has_no_authority(tmp_path: Path) -> None:
    life = HookLifecycle(tmp_path / "events.jsonl", clock=lambda: 1.0)
    missing_session = life.record(_post("codex", "unknown", "i1"), host_hint="codex")
    assert missing_session["status"] == NO_AUTHORITY
    assert missing_session["post_capture_eligible"] is False
    assert missing_session["operation_success"] is None

    life.record(_session("codex", "s1"), host_hint="codex")
    missing_pre = life.record(_post("codex", "s1", "i2"), host_hint="codex")
    assert missing_pre["status"] == NO_AUTHORITY
    assert missing_pre["note"] == "pre_execution_not_recorded"
    assert missing_pre["post_capture_eligible"] is False


def test_cancellation_never_becomes_success(tmp_path: Path) -> None:
    life = HookLifecycle(tmp_path / "events.jsonl", clock=lambda: 1.0)
    life.record(_session("grok", "s1"), host_hint="grok")
    life.record(_pre("grok", "s1", "i1"), host_hint="grok")
    cancelled = life.record(
        {"hookEventName": "Stop", "sessionId": "s1", "toolUseId": "i1"},
        host_hint="grok",
    )
    assert cancelled["status"] == CANCELLED
    assert cancelled["operation_success"] is False
    assert cancelled["post_capture_eligible"] is False
    after = life.record(_post("grok", "s1", "i1"), host_hint="grok")
    assert after["status"] == NO_AUTHORITY
    assert after["note"] == "session_cancelled"
    assert after["operation_success"] is None


def test_cancel_without_bound_session_is_not_authority(tmp_path: Path) -> None:
    life = HookLifecycle(tmp_path / "events.jsonl")
    result = life.record(
        {"event": "on_stop", "extra": {"task_id": "never-bound"}},
        host_hint="hermes",
    )
    assert result["status"] == CANCELLED_NO_AUTHORITY
    assert result["operation_success"] is False


def test_unknown_event_is_explicit_bypass(tmp_path: Path) -> None:
    life = HookLifecycle(tmp_path / "events.jsonl")
    result = life.record(
        {"hookEventName": "some_future_event", "sessionId": "s1"},
        host_hint="codex",
    )
    assert result["status"] == BYPASS_OBSERVED
    assert result["authority_removed"] is True
    assert result["lifecycle_valid"] is False
    assert result["semantic_disposition"] is None


def test_chain_is_hash_linked_and_tamper_detected(tmp_path: Path) -> None:
    log = tmp_path / "events.jsonl"
    life = HookLifecycle(log, clock=lambda: 1.0)
    life.record(_session("codex", "s1"), host_hint="codex")
    life.record(_pre("codex", "s1", "i1"), host_hint="codex")
    rows = verify_event_log(log)
    assert rows[0]["previous_event_sha256"] == ""
    assert rows[1]["previous_event_sha256"] == rows[0]["event_sha256"]

    lines = log.read_text(encoding="utf-8").splitlines()
    changed = json.loads(lines[1])
    changed["status"] = "CAPTURED"
    lines[1] = json.dumps(changed, sort_keys=True, separators=(",", ":"))
    log.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(HookChainError):
        verify_event_log(log)
    with pytest.raises(HookChainError):
        HookLifecycle(log)


def test_fixed_inputs_and_clock_produce_fixed_bytes(tmp_path: Path) -> None:
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"
    for path in (first, second):
        life = HookLifecycle(path, clock=lambda: 42.0)
        life.record(_session("claude", "s1"), host_hint="claude", timestamp=1)
        life.record(_pre("claude", "s1", "i1"), host_hint="claude", timestamp=2)
    assert first.read_bytes() == second.read_bytes()


def test_source_bytes_are_bound_without_interpreting_body() -> None:
    raw = b'{"event":"pre_tool_call","extra":{"task_id":"s"}}'
    normalized = normalize_host_payload(
        {"event": "pre_tool_call", "extra": {"task_id": "s"}},
        source_bytes=raw,
    )
    assert normalized.source_sha256
    assert normalized.source_sha256 != ""


def test_no_model_roster_or_basin_policy_in_module() -> None:
    source = Path(hook_lifecycle_module.__file__).read_text(encoding="utf-8").lower()
    assert "gpt-" not in source
    assert "luna" not in source
    assert "sonnet" not in source
    assert "fable" not in source
