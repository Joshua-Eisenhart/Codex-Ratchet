from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import imessage_bot as im  # noqa: E402


def test_claude_freeform_uses_read_only_tools(monkeypatch):
    captured = {}

    def fake_claude_call(prompt, system_prompt, tools):
        captured["prompt"] = prompt
        captured["system_prompt"] = system_prompt
        captured["tools"] = tools
        return "ok"

    monkeypatch.setattr(im, "_claude_call", fake_claude_call)

    assert im.claude_freeform("what changed?") == "ok"
    assert captured["prompt"] == "what changed?"
    assert captured["tools"] == "Read,Glob,Grep,Bash"
    assert "Do not edit files" in captured["system_prompt"]
    assert "mutate git" in captured["system_prompt"]
    assert "long-running sims" in captured["system_prompt"]


def test_redact_log_text_hides_imessage_handles(monkeypatch):
    monkeypatch.setattr(im, "PHONE_HANDLE", "+1 707 867 3323")
    monkeypatch.setattr(im, "EMAIL_HANDLE", "user@example.com")
    monkeypatch.setattr(im, "REPLY_HANDLE", "reply@example.com")

    redacted = im._redact_log_text(
        "to +1 707 867 3323 from user@example.com reply reply@example.com"
    )

    assert "+1 707 867 3323" not in redacted
    assert "user@example.com" not in redacted
    assert "reply@example.com" not in redacted
    assert "[redacted-number]" in redacted
    assert "[redacted-email]" in redacted
