#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNS_ROOT = ROOT / "system_v3" / "runs"
LEGACY_MIGRATED_ROOT = RUNS_ROOT / "LEGACY__MIGRATED__"
CURRENT_STATE_ROOT = RUNS_ROOT / "_CURRENT_STATE"
DEFAULT_BOOKKEEPING_DIR = Path(os.environ.get("CODEX_RATCHET_BOOKKEEPING_DIR", "")).expanduser()

LEGACY_DUP_DIR_NAMES = {"snapshots", "sim", "a1_strategies", "outbox"}
EXCLUDED_GIT = ROOT / ".git"


def _iter_legacy_duplicate_dirs() -> list[Path]:
    # Legacy cleanup paths are optional and may live outside the repo.
    env_root = os.environ.get("CODEX_RATCHET_LEGACY_RUNS_ROOT", "")
    legacy_runs_root = Path(env_root).expanduser() if env_root else LEGACY_MIGRATED_ROOT
    if not legacy_runs_root.is_dir():
        return []
    out: list[Path] = []
    runs_root_resolved = RUNS_ROOT.resolve()
    legacy_migrated_resolved = LEGACY_MIGRATED_ROOT.resolve()
    for dirpath, dirnames, _filenames in os.walk(legacy_runs_root):
        for name in dirnames:
            if name in LEGACY_DUP_DIR_NAMES:
                candidate = (Path(dirpath) / name).resolve()
                # Never janitor canonical runtime fixture directories.
                # Only sweep duplicate surfaces inside the LEGACY migration bucket.
                try:
                    candidate.relative_to(runs_root_resolved)
                except ValueError:
                    continue
                try:
                    candidate.relative_to(legacy_migrated_resolved)
                except ValueError:
                    continue
                out.append(candidate)
    return sorted(out)


def _iter_cache_files() -> tuple[list[Path], list[Path]]:
    pycache_dirs: list[Path] = []
    ds_store_files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        current = Path(dirpath)
        if current == EXCLUDED_GIT:
            dirnames[:] = []
            continue
        if "__pycache__" in dirnames:
            pycache_dirs.append(current / "__pycache__")
        for filename in filenames:
            if filename == ".DS_Store":
                ds_store_files.append(current / filename)
    return sorted(pycache_dirs), sorted(ds_store_files)


def _iter_current_state_history_cache() -> list[Path]:
    """
    `_CURRENT_STATE/` is a derived/resume cache surface. Only `state.json` and
    `sequence_state.json` are used by the runtime. Any numbered history files are
    deletable noise that causes save-surface bloat.
    """
    if not CURRENT_STATE_ROOT.is_dir():
        return []
    out: list[Path] = []
    for p in CURRENT_STATE_ROOT.glob("state *.json"):
        out.append(p)
    for p in CURRENT_STATE_ROOT.glob("sequence_state *.json"):
        out.append(p)
    return sorted(out)


def _path_size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    total = 0
    for p in path.rglob("*"):
        if p.is_file():
            total += p.stat().st_size
    return total


def _delete_path(path: Path) -> None:
    if not path.exists():
        return
    if path.is_file() or path.is_symlink():
        path.unlink()
        return
    shutil.rmtree(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic storage janitor for archive/cache noise.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply deletions. Default is dry-run audit only.",
    )
    parser.add_argument(
        "--write-bookkeeping-log",
        action="store_true",
        help="Write a bookkeeping JSON file after run (see --bookkeeping-dir).",
    )
    parser.add_argument(
        "--bookkeeping-dir",
        type=str,
        default=str(DEFAULT_BOOKKEEPING_DIR) if str(DEFAULT_BOOKKEEPING_DIR) else "",
        help=(
            "Directory to write bookkeeping JSON into. Recommended: an external archive/ops_logs/ "
            "outside the repo. Can also be set via CODEX_RATCHET_BOOKKEEPING_DIR."
        ),
    )
    args = parser.parse_args()

    legacy_dup_dirs = _iter_legacy_duplicate_dirs()
    pycache_dirs, ds_store_files = _iter_cache_files()
    current_state_history = _iter_current_state_history_cache()

    groups = {
        "legacy_duplicate_dirs": legacy_dup_dirs,
        "current_state_history_cache": current_state_history,
        "pycache_dirs": pycache_dirs,
        "ds_store_files": ds_store_files,
    }

    before_total_bytes = _path_size_bytes(ROOT)
    before_system_v3_bytes = _path_size_bytes(ROOT / "system_v3")

    planned = {}
    for key, paths in groups.items():
        planned[key] = {
            "count": len(paths),
            "bytes": sum(_path_size_bytes(path) for path in paths),
            "paths": [str(path) for path in paths],
        }

    deleted = {"paths": [], "errors": []}
    if args.apply:
        for paths in groups.values():
            for path in paths:
                try:
                    _delete_path(path)
                    deleted["paths"].append(str(path))
                except Exception as exc:  # pragma: no cover - defensive
                    deleted["errors"].append({"path": str(path), "error": str(exc)})

    after_total_bytes = _path_size_bytes(ROOT)
    after_system_v3_bytes = _path_size_bytes(ROOT / "system_v3")

    payload = {
        "schema": "SYSTEM_STORAGE_JANITOR_RESULT_v1",
        "root": str(ROOT),
        "apply": bool(args.apply),
        "before": {
            "total_bytes": before_total_bytes,
            "system_v3_bytes": before_system_v3_bytes,
        },
        "planned": planned,
        "deleted": deleted,
        "after": {
            "total_bytes": after_total_bytes,
            "system_v3_bytes": after_system_v3_bytes,
        },
        "freed_total_bytes": max(0, before_total_bytes - after_total_bytes),
    }

    if args.write_bookkeeping_log:
        if not args.bookkeeping_dir:
            raise SystemExit("--write-bookkeeping-log requires --bookkeeping-dir (or CODEX_RATCHET_BOOKKEEPING_DIR).")
        bookkeeping_root = Path(args.bookkeeping_dir).expanduser()
        bookkeeping_root.mkdir(parents=True, exist_ok=True)
        ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out = bookkeeping_root / f"CLEANUP_BOOKKEEPING__{ts}.json"
        out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        payload["bookkeeping_file"] = str(out)

    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
