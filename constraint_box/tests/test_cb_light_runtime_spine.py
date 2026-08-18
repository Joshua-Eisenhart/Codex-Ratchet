"""Regression tests for the one contained CB Light runtime/hook spine."""

from __future__ import annotations

import json
import shutil
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


def test_manifest_gate_and_hooks_share_the_contained_interpreter(tmp_path: Path) -> None:
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
        "post_tool_failure.sh",
        "task_completed.sh",
        "subagent_stop.sh",
        "post_tool_batch.sh",
        "stop.sh",
        "config_change.sh",
        "file_changed.sh",
    ):
        text = (CB / "hooks" / name).read_text(encoding="utf-8")
        assert ".venv/bin/python" in text
        assert '"$interpreter" -B -I ' in text
        assert "cb_light_hook.py" in text
        assert EXTERNAL_MAIN not in text

    portable_root = tmp_path / "portable-project"
    portable_claude = portable_root / ".claude"
    shutil.copytree(CB / "integrated_system" / "hooks" / "claude", portable_claude)
    portable_settings = json.loads(
        (portable_claude / "settings.json").read_text(encoding="utf-8")
    )
    portable_expected = {
        "SessionStart": 'bash "$CLAUDE_PROJECT_DIR/.claude/hooks/session-start.sh"',
        "PostCompact": 'bash "$CLAUDE_PROJECT_DIR/.claude/hooks/post-compact.sh"',
        "PreToolUse": 'bash "$CLAUDE_PROJECT_DIR/.claude/hooks/cb_pretooluse_guard.sh"',
        "PostToolUse": 'bash "$CLAUDE_PROJECT_DIR/.claude/hooks/cb_posttooluse_record.sh"',
        "PostToolUseFailure": 'bash "$CLAUDE_PROJECT_DIR/constraint_box/hooks/post_tool_failure.sh"',
        "TaskCompleted": 'bash "$CLAUDE_PROJECT_DIR/constraint_box/hooks/task_completed.sh"',
        "SubagentStop": 'bash "$CLAUDE_PROJECT_DIR/constraint_box/hooks/subagent_stop.sh"',
        "PostToolBatch": 'bash "$CLAUDE_PROJECT_DIR/constraint_box/hooks/post_tool_batch.sh"',
        "Stop": 'bash "$CLAUDE_PROJECT_DIR/constraint_box/hooks/stop.sh"',
        "ConfigChange": 'bash "$CLAUDE_PROJECT_DIR/constraint_box/hooks/config_change.sh"',
        "FileChanged": 'bash "$CLAUDE_PROJECT_DIR/constraint_box/hooks/file_changed.sh"',
    }
    for event, command in portable_expected.items():
        assert _commands(portable_settings, event) == [command]
    portable_matchers = {
        "SessionStart": "startup|resume|clear|compact",
        "PostCompact": "",
        "PreToolUse": "Bash|Edit|Write|NotebookEdit",
        "PostToolUse": "Bash|Edit|Write|NotebookEdit",
        "PostToolUseFailure": "Bash",
        "TaskCompleted": "",
        "SubagentStop": "",
        "PostToolBatch": "",
        "Stop": "",
        "ConfigChange": "user_settings|project_settings|local_settings|policy_settings|skills",
        "FileChanged": "settings.json|cb_light_contract_v1.json|cb_light_tools_v1.json|constraintbox-py313-macos-estate.lock",
    }
    for event, matcher in portable_matchers.items():
        assert [group.get("matcher") for group in portable_settings["hooks"][event]] == [matcher]
    for name in (
        "cb_pretooluse_guard.sh",
        "cb_posttooluse_record.sh",
        "session-start.sh",
        "post-compact.sh",
    ):
        text = (portable_claude / "hooks" / name).read_text(encoding="utf-8")
        assert "product_root=$project_root/constraint_box" in text
        assert '"$product_root/.venv/bin/python"' in text
        assert 'exec "$hooks_dir/cb_hook.sh" claude' in text
        assert "integrated_system/hooks" in text
        assert "cb_light_hook.py" not in text
        assert "LEV OS" not in text
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
