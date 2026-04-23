from __future__ import annotations

import importlib
import io
import json
import os
import sys
import builtins
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


def test_module_prefers_telegram_bot_token_from_configured_codex_env_file(monkeypatch, tmp_path):
    env_path = tmp_path / "telegram_bot.env"
    env_path.write_text('TELEGRAM_BOT_TOKEN=bot_token_from_file\nTELEGRAM_CHAT_ID=8144581887\n', encoding="utf-8")

    monkeypatch.setenv("CODEX_TELEGRAM_ENV_PATH", str(env_path))
    monkeypatch.delenv("TELEGRAM_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    reloaded = importlib.reload(tb)
    try:
        assert reloaded.TELEGRAM_TOKEN == "bot_token_from_file"
        assert reloaded.TELEGRAM_CHAT_ID == "8144581887"
    finally:
        monkeypatch.delenv("CODEX_TELEGRAM_ENV_PATH", raising=False)
        importlib.reload(reloaded)


def test_parse_run_duration_minutes_supports_hours_and_minutes():
    assert tb._parse_run_duration_minutes("Run for 2 hours.") == 120
    assert tb._parse_run_duration_minutes("do a 45 minute bounded run") == 45
    assert tb._parse_run_duration_minutes("run live queue") is None


def test_handle_live_queue_run_reports_missing_controller(monkeypatch):
    monkeypatch.setattr(tb.os.path, "exists", lambda path: False if path == tb.LIVE_QUEUE_CONTROLLER else os.path.exists(path))

    result = tb.handle_live_queue_run("Run for 1 hour.")

    assert result == "live queue controller missing"


def test_dispatch_routes_duration_request_to_live_queue_handler(monkeypatch):
    monkeypatch.setattr(tb, "handle_live_queue_run", lambda text: f"live:{text}")

    result = tb.dispatch("Run for 90 minutes.")

    assert result == "live:Run for 90 minutes."


def test_handle_live_queue_run_starts_controller_with_default_minutes(monkeypatch, tmp_path):
    log_path = tmp_path / "run.log"
    opened = {}
    popen_call = {}
    real_open = builtins.open

    class _FakeProc:
        pid = 4321

    def fake_exists(path):
        if path == tb.LIVE_QUEUE_CONTROLLER:
            return True
        return os.path.exists(path)

    def fake_open(path, mode="r", encoding=None):
        opened["path"] = path
        opened["mode"] = mode
        return real_open(log_path, mode, encoding=encoding)

    def fake_popen(cmd, cwd, env, stdout, stderr, text):
        popen_call["cmd"] = cmd
        popen_call["cwd"] = cwd
        popen_call["env"] = env
        popen_call["stderr"] = stderr
        popen_call["text"] = text
        assert stdout is not None
        return _FakeProc()

    monkeypatch.setattr(tb.os.path, "exists", fake_exists)
    monkeypatch.setattr(tb, "_base_env", lambda: {"TEST_ENV": "1"})
    monkeypatch.setattr(tb, "time", type("FakeTime", (), {"time": staticmethod(lambda: 1710000000)})())
    monkeypatch.setattr(builtins, "open", fake_open)
    monkeypatch.setattr(tb.subprocess, "Popen", fake_popen)

    result = tb.handle_live_queue_run("run live queue")

    assert "live queue run started" in result
    assert "- pid: 4321" in result
    assert "- minutes: 60" in result
    assert popen_call["cmd"] == [tb.PYTHON_BIN, tb.LIVE_QUEUE_CONTROLLER, "--minutes", "60"]
    assert popen_call["cwd"] == tb.PROJECT_DIR
    assert popen_call["env"] == {"TEST_ENV": "1"}
    assert opened["path"] == "/tmp/codex_live_queue_run_1710000000.log"



def test_format_run_status_report_includes_useful_human_fields():
    message = tb.format_run_status_report(
        phase="heartbeat",
        summary="wave G1 still advancing",
        duration_bound="8h",
        primary_lane="geometry spine",
        maintenance_lane="truth/ledger closure",
        current_task="hopf-map packet",
        health="healthy",
        last_success="sim_density_hopf_geometry.py",
        changed_items=["density_hopf_geometry_results.json", "sim_truth_audit.md"],
        next_step="run fiber-equivalence packet",
        closure_state="truth/maintenance on track",
        worker_state="main runner active",
        log_path="/tmp/overnight.log",
    )

    assert "HEARTBEAT" in message
    assert "Duration: 8h" in message
    assert "Primary lane: geometry spine" in message
    assert "Maintenance lane: truth/ledger closure" in message
    assert "Current task: hopf-map packet" in message
    assert "Health: healthy" in message
    assert "Last success: sim_density_hopf_geometry.py" in message
    assert "Changed: density_hopf_geometry_results.json, sim_truth_audit.md" in message
    assert "Next: run fiber-equivalence packet" in message
    assert "Closure: truth/maintenance on track" in message
    assert "Worker: main runner active" in message
