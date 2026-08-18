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

def load_wiki_compact_mmm_files(root: Path) -> dict[str, bytes]:
    """Load compact MMM bytes from an explicit run-provided directory."""

    if not isinstance(root, Path) or not root.is_dir():
        raise ZipJobRefusal("HOLD_WIKI_MMM_ROOT_UNBOUND", str(root))
    base = root.resolve()
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
    mmm_root: Path,
    live_paths: dict[str, dict[str, str]],
    live_routes: dict[str, tuple[str, str]],
    seed: int = 461,
    run_id: str = "live-failure-council",
) -> bytes:
    if not isinstance(live_paths, dict) or not isinstance(live_routes, dict):
        raise ZipJobRefusal("HOLD_LIVE_RUN_DATA_UNBOUND", "paths_or_routes")
    if set(live_routes) != set(FAILURE_MEMBERS):
        raise ZipJobRefusal("REFUSE_LIVE_ROUTE_ROSTER", "member_routes")
    agents: list[dict[str, Any]] = []
    extra: dict[str, bytes] = {}
    for member in FAILURE_MEMBERS:
        route = live_routes.get(member)
        if (
            not isinstance(route, (tuple, list))
            or len(route) != 2
            or any(not isinstance(value, str) or not value.strip() for value in route)
        ):
            raise ZipJobRefusal("REFUSE_LIVE_ROUTE_ROSTER", member)
        provider, model = route
        if provider not in {"codex-cli", "grok-cli", "claude-code"}:
            raise ZipJobRefusal("REFUSE_LIVE_ROUTE_ROSTER", provider)
        provider_paths = live_paths.get(provider)
        if not isinstance(provider_paths, dict):
            raise ZipJobRefusal("HOLD_LIVE_PROVIDER_PATHS_UNBOUND", provider)
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
        agents.append(bind_live_agent_fields(raw, paths=provider_paths))
    return build_named_council_packet(
        council_id="failure",
        owner_prompt=owner_prompt,
        seed=seed,
        run_id=run_id,
        agents=agents,
        mmm_files=load_wiki_compact_mmm_files(mmm_root),
        extra_files=extra,
    )
