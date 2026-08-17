"""Regression tests for the one contained CB Light runtime/hook spine."""

from __future__ import annotations

import json
from pathlib import Path

from constraintbox.core_cli import build_parser
from hookkernel.cb_light_gate import DEFAULT_INTERPRETER
from hookkernel.cb_light_runtime import MANDATED_INTERPRETER, same_declared_interpreter


CB = Path(__file__).resolve().parents[1]
REPO = CB.parent
EXTERNAL_MAIN = "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3"


def _commands(settings: dict, event: str) -> list[str]:
    return [
        hook["command"]
        for group in settings["hooks"][event]
        for hook in group.get("hooks", [])
        if hook.get("type") == "command"
    ]


def test_manifest_gate_and_hooks_share_the_contained_interpreter() -> None:
    manifest = json.loads(
        (CB / "config" / "cb_light_tools_v1.json").read_text(encoding="utf-8")
    )
    expected = CB / ".venv" / "bin" / "python"
    assert same_declared_interpreter(MANDATED_INTERPRETER, expected)
    assert same_declared_interpreter(DEFAULT_INTERPRETER, expected)
    assert same_declared_interpreter(CB / manifest["mandated_interpreter"], expected)

    settings = json.loads((REPO / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert _commands(settings, "SessionStart") == [
        'bash "$CLAUDE_PROJECT_DIR/.claude/hooks/session-start.sh"'
    ]
    assert _commands(settings, "PreToolUse") == [
        'bash "$CLAUDE_PROJECT_DIR/.claude/hooks/cb_pretooluse_guard.sh"'
    ]
    assert _commands(settings, "PostToolUse") == [
        'bash "$CLAUDE_PROJECT_DIR/.claude/hooks/cb_posttooluse_record.sh"'
    ]

    for name in (
        "cb_pretooluse_guard.sh",
        "cb_posttooluse_record.sh",
        "session-start.sh",
    ):
        text = (REPO / ".claude" / "hooks" / name).read_text(encoding="utf-8")
        assert ".venv/bin/python" in text
        assert "-I" in text
        assert "hookkernel.cb_light_gate" in text
        assert EXTERNAL_MAIN not in text


def test_legacy_install_wrappers_are_adapters_not_a_second_controller() -> None:
    expected = {
        "pre_tool.sh": ".claude/hooks/cb_pretooluse_guard.sh",
        "post_tool.sh": ".claude/hooks/cb_posttooluse_record.sh",
        "session_start.sh": ".claude/hooks/session-start.sh",
    }
    for name, target in expected.items():
        text = (CB / "hooks" / name).read_text(encoding="utf-8")
        assert 'exec bash "$repo/' in text
        assert target in text
        assert "cb_light_hook.py" not in text


def test_public_cli_exposes_the_gate_front_door() -> None:
    parser = build_parser()
    subparsers = next(
        action for action in parser._actions if getattr(action, "choices", None)
    )
    assert "cb-light" in subparsers.choices
    parsed = parser.parse_args(["cb-light", "probe", "--output", "gate.json"])
    assert parsed.gate_args == ["probe", "--output", "gate.json"]
