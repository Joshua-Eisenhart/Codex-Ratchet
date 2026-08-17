from __future__ import annotations

import json
from pathlib import Path

import constraintbox.codex_cli_adapter as adapter

import pytest

from constraintbox.codex_cli_adapter import REQUEST_SCHEMA, run
from constraintbox.mmm_load_gate import MmmLoadError

from test_mmm_load_gate import mmm_bind


def _runner(path: Path, events: list[dict[str, object]]) -> Path:
    rendered = "".join(f"printf '%s\\n' '{json.dumps(event)}'\n" for event in events)
    path.write_text("#!/bin/sh\n" + rendered, encoding="utf-8")
    path.chmod(0o700)
    return path


def _request(
    path: Path,
    runner: Path,
    prompt: Path,
    cwd: Path,
    *,
    sandbox_mode: str | None = None,
    hierarchy: bool = False,
    bind_mmm: bool = True,
) -> Path:
    request = {
        "schema": REQUEST_SCHEMA,
        "request_id": "codex-adapter-test",
        "runner_path": str(runner),
        "model": "test-model",
        "reasoning_effort": "max",
        "prompt_path": str(prompt),
        "cwd": str(cwd),
    }
    if bind_mmm:
        request.update(mmm_bind(prompt))
    if sandbox_mode is not None:
        request["sandbox_mode"] = sandbox_mode
    if hierarchy:
        request.update(
            {
                "hierarchy_bound": True,
                "parent_id": "child-council",
                "wave_id": "wave-1",
                "round": 1,
                "depth": 2,
            }
        )
    path.write_text(
        json.dumps(request, sort_keys=True),
        encoding="utf-8",
    )
    return path


def test_multiple_agent_messages_with_one_completed_turn_are_observed(tmp_path: Path, monkeypatch) -> None:
    events = [
        {"type": "item.completed", "item": {"type": "agent_message", "text": "progress"}},
        {"type": "item.completed", "item": {"type": "agent_message", "text": "final"}},
        {"type": "turn.completed", "usage": {}},
    ]
    runner = _runner(tmp_path / "runner", events)
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("test", encoding="utf-8")
    monkeypatch.setattr(
        adapter,
        "_codex_rollout_model",
        lambda _stdout, _home: ("test-model", tmp_path / "rollout.jsonl"),
    )
    receipt = run(
        _request(tmp_path / "request.json", runner, prompt, tmp_path),
        response_path=tmp_path / "response.jsonl",
        timeout_seconds=5,
    )
    assert receipt["disposition"] == "OBSERVED"
    assert receipt["agent_message_count"] == 2
    assert receipt["exactly_one_agent_message"] is False
    assert receipt["completed_turn_count"] == 1
    assert receipt["terminal_completion_confirmed"] is True
    assert receipt["final_agent_message_sha256"]


def test_workspace_write_is_explicit_request_data(tmp_path: Path, monkeypatch) -> None:
    events = [
        {"type": "item.completed", "item": {"type": "agent_message", "text": "final"}},
        {"type": "turn.completed", "usage": {}},
    ]
    runner = _runner(tmp_path / "runner", events)
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("test", encoding="utf-8")
    monkeypatch.setattr(
        adapter,
        "_codex_rollout_model",
        lambda _stdout, _home: ("test-model", tmp_path / "rollout.jsonl"),
    )
    receipt = run(
        _request(
            tmp_path / "request.json",
            runner,
            prompt,
            tmp_path,
            sandbox_mode="workspace-write",
        ),
        response_path=tmp_path / "response.jsonl",
        timeout_seconds=5,
    )
    assert receipt["sandbox_mode_requested"] == "workspace-write"
    sandbox_index = receipt["argv"].index("--sandbox")
    assert receipt["argv"][sandbox_index + 1] == "workspace-write"


def test_zip_leaf_hierarchy_is_accepted_and_bound(tmp_path: Path, monkeypatch) -> None:
    events = [
        {"type": "item.completed", "item": {"type": "agent_message", "text": "final"}},
        {"type": "turn.completed", "usage": {}},
    ]
    runner = _runner(tmp_path / "runner", events)
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("test", encoding="utf-8")
    monkeypatch.setattr(
        adapter,
        "_codex_rollout_model",
        lambda _stdout, _home: ("test-model", tmp_path / "rollout.jsonl"),
    )
    receipt = run(
        _request(
            tmp_path / "request.json",
            runner,
            prompt,
            tmp_path,
            sandbox_mode="workspace-write",
            hierarchy=True,
        ),
        response_path=tmp_path / "response.jsonl",
        timeout_seconds=5,
    )
    assert {key: receipt[key] for key in ("hierarchy_bound", "parent_id", "wave_id", "round", "depth")} == {
        "hierarchy_bound": True,
        "parent_id": "child-council",
        "wave_id": "wave-1",
        "round": 1,
        "depth": 2,
    }


def test_rollout_lookup_retries_without_falling_back_to_requested_model(
    tmp_path: Path, monkeypatch
) -> None:
    events = [
        {"type": "thread.started", "thread_id": "thread-a"},
        {"type": "item.completed", "item": {"type": "agent_message", "text": "final"}},
        {"type": "turn.completed", "usage": {}},
    ]
    runner = _runner(tmp_path / "runner", events)
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("test", encoding="utf-8")
    calls = {"count": 0}

    def delayed(_stdout: str, _home: Path):
        calls["count"] += 1
        if calls["count"] < 3:
            return None, None
        return "test-model", str(tmp_path / "rollout.jsonl")

    monkeypatch.setattr(adapter, "_codex_rollout_model", delayed)
    monkeypatch.setattr("constraintbox.codex_cli_adapter.time.sleep", lambda _seconds: None)
    receipt = run(
        _request(tmp_path / "request.json", runner, prompt, tmp_path),
        response_path=tmp_path / "response.jsonl",
        timeout_seconds=5,
    )
    assert receipt["disposition"] == "OBSERVED"
    assert receipt["rollout_lookup_attempts"] == 3
    assert calls["count"] == 3


def test_missing_completed_turn_is_hold(tmp_path: Path, monkeypatch) -> None:
    events = [
        {"type": "item.completed", "item": {"type": "agent_message", "text": "partial"}},
    ]
    runner = _runner(tmp_path / "runner", events)
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("test", encoding="utf-8")
    monkeypatch.setattr(
        adapter,
        "_codex_rollout_model",
        lambda _stdout, _home: ("test-model", tmp_path / "rollout.jsonl"),
    )
    receipt = run(
        _request(tmp_path / "request.json", runner, prompt, tmp_path),
        response_path=tmp_path / "response.jsonl",
        timeout_seconds=5,
    )
    assert receipt["disposition"] == "HOLD"
    assert receipt["reason_code"] == "HOLD_CODEX_CLI_INCOMPLETE"
    assert receipt["terminal_completion_confirmed"] is False


def test_missing_mmm_refuses_before_spawn(tmp_path: Path) -> None:
    sentinel = tmp_path / "spawned"
    runner = tmp_path / "runner"
    runner.write_text(f"#!/bin/sh\nprintf spawned > '{sentinel}'\n", encoding="utf-8")
    runner.chmod(0o700)
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("no packs", encoding="utf-8")
    with pytest.raises(MmmLoadError) as caught:
        run(
            _request(
                tmp_path / "request.json",
                runner,
                prompt,
                tmp_path,
                bind_mmm=False,
            ),
            response_path=tmp_path / "response.jsonl",
            timeout_seconds=5,
        )
    assert caught.value.reason_code == "REFUSE_MMM_LOAD_MISSING"
    assert not sentinel.exists()


def test_confirmed_mmm_is_bound_on_observed_receipt(tmp_path: Path, monkeypatch) -> None:
    events = [
        {"type": "item.completed", "item": {"type": "agent_message", "text": "final"}},
        {"type": "turn.completed", "usage": {}},
    ]
    runner = _runner(tmp_path / "runner", events)
    prompt = tmp_path / "prompt.txt"
    monkeypatch.setattr(
        adapter,
        "_codex_rollout_model",
        lambda _stdout, _home: ("test-model", tmp_path / "rollout.jsonl"),
    )
    receipt = run(
        _request(tmp_path / "request.json", runner, prompt, tmp_path),
        response_path=tmp_path / "response.jsonl",
        timeout_seconds=5,
    )
    assert receipt["disposition"] == "OBSERVED"
    assert receipt["mmm_load_confirmed"] is True
    assert receipt["mmm_packs"] == ["nominalist", "smt"]
    assert receipt["mmm_sha256"]
