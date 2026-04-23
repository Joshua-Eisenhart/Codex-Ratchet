from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARCHIVE_ROOT = REPO_ROOT / "archive"


def _candidate_archive_roots() -> list[Path]:
    roots: list[Path] = []
    raw = os.environ.get("CODEX_RATCHET_GRAPH_ARCHIVE_DIR", "").strip()
    if raw:
        roots.append(Path(raw))
    roots.append(DEFAULT_ARCHIVE_ROOT)
    return roots


def resolve_graph_path(root: Path, rel_path: str) -> Path:
    rel = Path(rel_path)
    live_path = rel if rel.is_absolute() else root / rel
    if live_path.exists():
        return live_path

    for archive_root in _candidate_archive_roots():
        archived_path = archive_root / rel.name
        if archived_path.exists():
            return archived_path

        for candidate in archive_root.rglob(rel.name):
            if candidate.exists():
                return candidate

    dvc_path = live_path.with_name(live_path.name + ".dvc")
    if dvc_path.exists():
        raise FileNotFoundError(
            f"Graph payload missing at {live_path} but DVC sidecar exists at {dvc_path}. "
            "Restore the payload or point CODEX_RATCHET_GRAPH_ARCHIVE_DIR at an archived copy."
        )

    raise FileNotFoundError(f"Graph payload missing: {live_path}")


def load_graph_json(root: Path, rel_path: str, *, default: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        graph_path = resolve_graph_path(root, rel_path)
    except FileNotFoundError:
        if default is not None:
            return default
        raise

    return json.loads(graph_path.read_text(encoding="utf-8"))
