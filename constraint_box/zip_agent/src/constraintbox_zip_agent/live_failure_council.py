from __future__ import annotations

from pathlib import Path
from typing import Any

from .council_zip import (
    FAILURE_MEMBERS,
    VOICES,
    bind_live_agent_fields,
    build_named_council_packet,
)
from .protocol import ZipJobRefusal

WIKI_COMPACT = Path(
    "/Users/joshuaeisenhart/wiki/wizard/packet-v4-3-current/mmm/mini/compact/voices/md"
)
DEFAULT_LIVE_PATHS = {
    "codex-cli": {
        "runner_path": "/usr/local/bin/codex",
        "codex_home": str(Path.home() / ".codex"),
    },
    "grok-cli": {
        "runner_path": str(Path.home() / ".local/bin/grok"),
    },
    "claude-code": {
        "runner_path": "/usr/local/bin/claude",
        "bridge_path": str(Path.home() / ".codex/skills/claude-bridge/scripts/claude_bridge.py"),
    },
}
DEFAULT_LIVE_ROUTES = {
    "likely": ("codex-cli", "gpt-5.6-luna"),
    "dangerous": ("grok-cli", "grok-4.6"),
    "assumption": ("claude-code", "claude-sonnet-5"),
}


def load_wiki_compact_mmm_files(root: Path | None = None) -> dict[str, bytes]:
    base = root or WIKI_COMPACT
    files: dict[str, bytes] = {}
    for voice in VOICES:
        path = base / f"MMM_VOICE_{voice.upper()}_COMPACT_v4_1.md"
        if not path.is_file():
            raise ZipJobRefusal("HOLD_WIKI_MMM_MISSING", str(path))
        files[f"MMMS/{voice}.md"] = path.read_bytes()
    return files


def build_live_failure_council_packet(
    *,
    owner_prompt: bytes,
    seed: int = 461,
    run_id: str = "live-failure-council",
    live_paths: dict[str, dict[str, str]] | None = None,
) -> bytes:
    paths = live_paths or DEFAULT_LIVE_PATHS
    agents: list[dict[str, Any]] = []
    extra: dict[str, bytes] = {}
    for member in FAILURE_MEMBERS:
        provider, model = DEFAULT_LIVE_ROUTES[member]
        extra[f"AGENTS/{member}.md"] = (
            f"role: {member}\n"
            "Write only the declared output. Copy every required token. "
            "Do not promote. Do not launch children.\n"
        ).encode()
        raw = {
            "agent_id": member,
            "agent_path": f"AGENTS/{member}.md",
            "output_path": f"output/{member}.md",
            "provider": provider,
            "model_requested": model,
            "required_fragments": [
                f"council: {member}",
                "support: observed",
                "falsifier:",
            ],
            "max_output_bytes": 16384,
            "max_attempts": 2,
            "timeout_seconds": 240,
        }
        if provider == "claude-code":
            raw["budget_usd"] = 1.0
            raw["reasoning_effort"] = "high"
        if provider == "grok-cli":
            raw["max_turns"] = 8
        agents.append(bind_live_agent_fields(raw, paths=paths[provider]))
    return build_named_council_packet(
        council_id="failure",
        owner_prompt=owner_prompt,
        seed=seed,
        run_id=run_id,
        agents=agents,
        mmm_files=load_wiki_compact_mmm_files(),
        extra_files=extra,
    )
