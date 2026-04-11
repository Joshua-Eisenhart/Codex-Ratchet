from __future__ import annotations

import importlib
import io
import json
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import telegram_bot as tb  # noqa: E402


class _FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb_):
        return False


def test_send_message_surfaces_api_failure(monkeypatch):
    monkeypatch.setattr(tb, "TELEGRAM_CHAT_ID", "123")

    def fake_api(method, **params):
        return {"ok": False, "error": "bad request"}

    monkeypatch.setattr(tb, "_api", fake_api)

    result = tb.send_message("hello")

    assert result["ok"] is False
    assert result["sent_count"] == 0
    assert result["attempted_count"] == 1
    assert "bad request" in result["errors"][0]


def test_get_updates_surfaces_transport_error(monkeypatch, capsys):
    def fake_urlopen(*args, **kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr(tb.urllib.request, "urlopen", fake_urlopen)

    result = tb.get_updates(7)

    captured = capsys.readouterr()
    assert result == []
    assert "get_updates error" in captured.err
    assert "network down" in captured.err


def test_dispatch_matches_run_bang_before_run(monkeypatch):
    monkeypatch.setattr(tb, "_sim_allowlist", lambda: {"foo"})
    monkeypatch.setattr(tb, "_run_sim", lambda name: f"ran {name}")

    assert tb.dispatch("run! foo") == "ran foo"


def test_unconfigured_chat_is_not_auto_bound():
    chat_id, should_process, notice = tb.resolve_incoming_chat("", "999")

    assert chat_id == ""
    assert should_process is False
    assert "Set TELEGRAM_CHAT_ID" in notice


def test_get_updates_returns_payload_on_success(monkeypatch):
    payload = {"result": [{"update_id": 1, "message": {"text": "hi"}}]}

    monkeypatch.setattr(tb.urllib.request, "urlopen", lambda *args, **kwargs: _FakeResponse(payload))

    result = tb.get_updates(0)

    assert result == payload["result"]


def test_load_env_file_reads_hermes_style_entries(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text('TELEGRAM_BOT_TOKEN="abc123"\nTELEGRAM_CHAT_ID=8144581887\n', encoding="utf-8")

    loaded = tb._load_env_file(str(env_path))

    assert loaded["TELEGRAM_BOT_TOKEN"] == "abc123"
    assert loaded["TELEGRAM_CHAT_ID"] == "8144581887"


def test_module_prefers_telegram_bot_token_from_env_file(monkeypatch, tmp_path):
    hermes_dir = tmp_path / ".hermes"
    hermes_dir.mkdir()
    env_path = hermes_dir / ".env"
    env_path.write_text('TELEGRAM_BOT_TOKEN=bot_token_from_file\nTELEGRAM_CHAT_ID=8144581887\n', encoding="utf-8")

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("TELEGRAM_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    reloaded = importlib.reload(tb)
    try:
        assert reloaded.TELEGRAM_TOKEN == "bot_token_from_file"
        assert reloaded.TELEGRAM_CHAT_ID == "8144581887"
    finally:
        importlib.reload(reloaded)
