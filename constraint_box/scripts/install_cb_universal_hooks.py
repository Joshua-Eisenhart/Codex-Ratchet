#!/usr/bin/env python3
"""Install CB universal hook adapter into host hook slots.

Does not encode model names. Idempotent. Does not start Hermes/Codex.
You must restart those hosts yourself for hooks to load.
"""

from __future__ import annotations

import json
from pathlib import Path

HOME = Path.home()
CB = Path(__file__).resolve().parents[1]
SHIM = CB / "hooks" / "universal" / "cb_hook.sh"
PY = CB / ".venv" / "bin" / "python"


def _cmd(host: str) -> str:
    return f"bash {SHIM} {host}"


def install_codex() -> str:
    path = HOME / ".codex" / "hooks.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    body: dict = {"hooks": {}}
    if path.is_file():
        try:
            body = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            body = {"hooks": {}}
    hooks = body.setdefault("hooks", {})
    entry = {
        "matcher": "",
        "hooks": [{"type": "command", "command": _cmd("codex")}],
    }
    # Codex CLI family: PreToolUse list of matcher objects
    pre = hooks.get("PreToolUse") or []
    text = json.dumps(pre)
    if "hook_adapter" not in text and "cb_hook.sh" not in text:
        if isinstance(pre, list):
            pre.append(entry)
        else:
            pre = [entry]
        hooks["PreToolUse"] = pre
        path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
        return f"wrote {path}"
    return f"already present {path}"


def install_grok() -> str:
    path = HOME / ".grok" / "hooks" / "cb-universal.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {"type": "command", "command": _cmd("grok")}
    body: dict = {"hooks": {"PreToolUse": [{"hooks": [entry]}]}}
    if path.is_file():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
        if isinstance(existing, dict) and "cb_hook.sh" in json.dumps(existing):
            return f"already present {path}"
        hooks = existing.setdefault("hooks", {}) if isinstance(existing, dict) else {}
        pre = hooks.get("PreToolUse") if isinstance(hooks, dict) else None
        if not isinstance(pre, list) or not pre:
            hooks["PreToolUse"] = [{"hooks": [entry]}]
        else:
            first = pre[0] if isinstance(pre[0], dict) else {}
            inner = first.setdefault("hooks", [])
            if isinstance(inner, list):
                inner.append(entry)
        existing["hooks"] = hooks
        body = existing
    path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    return f"wrote {path}"


def install_claude_project() -> str:
    """Add universal adapter beside the existing Light install-domain guard."""
    path = CB.parent / ".claude" / "settings.json"
    if not path.is_file():
        return f"missing {path}"
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return f"unreadable {path}"
    if "hooks/universal/cb_hook.sh" in json.dumps(body):
        return f"already present {path}"
    hooks = body.setdefault("hooks", {})
    pre = hooks.setdefault("PreToolUse", [])
    pre.append(
        {
            "matcher": "Bash",
            "hooks": [
                {
                    "type": "command",
                    "command": (
                        'bash "$CLAUDE_PROJECT_DIR/constraint_box/'
                        'hooks/universal/cb_hook.sh" claude'
                    ),
                }
            ],
        }
    )
    path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    return f"wrote extra PreToolUse {path}"


def install_hermes_snippet() -> str:
    """Write a yaml snippet the owner can merge; also try to patch config.yaml."""
    snippet = HOME / ".hermes" / "agent-hooks" / "cb-universal.snippet.yaml"
    snippet.parent.mkdir(parents=True, exist_ok=True)
    text = (
        "# Merge under hooks: in ~/.hermes/config.yaml then restart Hermes.\n"
        "hooks:\n"
        "  pre_tool_call:\n"
        "    - matcher: \"terminal|execute_code|delegate_task\"\n"
        f"      command: \"{_cmd('hermes')}\"\n"
        "      timeout: 30\n"
        "      fail_closed: true\n"
    )
    snippet.write_text(text, encoding="utf-8")
    cfg = HOME / ".hermes" / "config.yaml"
    if cfg.is_file() and "cb_hook.sh" not in cfg.read_text(encoding="utf-8"):
        # Append a clearly marked block; YAML merge of top-level `hooks` is valid.
        with cfg.open("a", encoding="utf-8") as fh:
            fh.write("\n# --- CB universal hook adapter (unmanaged LLM spawn) ---\n")
            fh.write(text)
        return f"appended hooks: to {cfg}; snippet {snippet}"
    if cfg.is_file():
        return f"already present in {cfg}"
    return f"wrote snippet only {snippet}"


def main() -> int:
    if not SHIM.is_file():
        print(f"missing shim {SHIM}")
        return 2
    SHIM.chmod(0o755)
    print(install_codex())
    print(install_grok())
    print(install_hermes_snippet())
    print(install_claude_project())
    print("Restart Codex / Hermes / Grok / Claude yourself. Installer does not restart them.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
