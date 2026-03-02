#!/usr/bin/env python3
"""
Lean pruning for large, regenerable directories.

Design intent (per operator):
- "Learn and delete": keep only persistent brains + specs + small coordination surfaces.
- Everything else is disposable and can be re-generated.

This tool is intentionally conservative about *where* it can delete:
- system_v3/runs/_save_exports
- work/zip_dropins

Dry-run by default. Use --apply to actually delete.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import stat
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parents[2]


def _on_rm_error(func, path, exc_info):
    try:
        os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
        func(path)
    except Exception:
        raise


def _safe_unlink(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
        return
    shutil.rmtree(path, onerror=_on_rm_error)


def _iter_entries(dir_path: Path) -> List[Path]:
    if not dir_path.exists():
        return []
    return sorted(dir_path.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)


@dataclass(frozen=True)
class DeleteCandidate:
    path: Path
    bytes: int


def _sizeof_path(path: Path) -> int:
    if path.is_symlink():
        return 0
    if path.is_file():
        try:
            return path.stat().st_size
        except FileNotFoundError:
            return 0
    total = 0
    for root, _, files in os.walk(path):
        for name in files:
            fp = Path(root) / name
            try:
                if fp.is_symlink():
                    continue
                total += fp.stat().st_size
            except FileNotFoundError:
                continue
    return total


def plan_prune_zip_dropins(
    keep_newest: int,
    keep_regex: Optional[re.Pattern[str]],
) -> Tuple[List[Path], List[DeleteCandidate]]:
    dir_path = REPO_ROOT / "work" / "zip_dropins"
    entries = _iter_entries(dir_path)

    keep: List[Path] = []
    delete: List[DeleteCandidate] = []

    for idx, entry in enumerate(entries):
        if entry.name in {"builds", ".DS_Store"}:
            keep.append(entry)
            continue
        if keep_regex and keep_regex.search(entry.name):
            keep.append(entry)
            continue
        if idx < keep_newest:
            keep.append(entry)
            continue
        delete.append(DeleteCandidate(entry, _sizeof_path(entry)))

    return keep, delete


def _save_kind_key(name: str) -> Optional[str]:
    # Example: SYSTEM_SAVE__bootstrap__20260224_234245Z.zip
    if not name.startswith("SYSTEM_SAVE__"):
        return None
    parts = name.split("__")
    if len(parts) < 3:
        return None
    return f"{parts[0]}__{parts[1]}"


def plan_prune_save_exports(keep_last_per_kind: int) -> Tuple[List[Path], List[DeleteCandidate]]:
    dir_path = REPO_ROOT / "system_v3" / "runs" / "_save_exports"
    entries = _iter_entries(dir_path)

    by_kind: dict[str, List[Path]] = {}
    other_keep: List[Path] = []
    for entry in entries:
        if entry.name == ".DS_Store":
            other_keep.append(entry)
            continue
        key = _save_kind_key(entry.name)
        if key is None:
            other_keep.append(entry)
            continue
        by_kind.setdefault(key, []).append(entry)

    keep: List[Path] = list(other_keep)
    delete: List[DeleteCandidate] = []
    for _, kind_entries in by_kind.items():
        kind_entries_sorted = sorted(kind_entries, key=lambda p: p.stat().st_mtime, reverse=True)
        keep.extend(kind_entries_sorted[:keep_last_per_kind])
        for entry in kind_entries_sorted[keep_last_per_kind:]:
            delete.append(DeleteCandidate(entry, _sizeof_path(entry)))

    return keep, delete


def _fmt_bytes(n: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    v = float(n)
    for u in units:
        if v < 1024.0 or u == units[-1]:
            if u == "B":
                return f"{int(v)}{u}"
            return f"{v:.1f}{u}"
        v /= 1024.0
    return f"{n}B"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Actually delete (default: dry-run).")
    parser.add_argument(
        "--zip-dropins-keep-newest",
        type=int,
        default=15,
        help="Keep N newest entries in work/zip_dropins (default: 15).",
    )
    parser.add_argument(
        "--zip-dropins-keep-regex",
        default=r"__v7_2_4\b",
        help=r"Regex for zip_dropins entries to always keep (default: '__v7_2_4\\b'). Use '' to disable.",
    )
    parser.add_argument(
        "--save-exports-keep-last-per-kind",
        type=int,
        default=1,
        help="Keep last N save exports per kind (default: 1). Kind = 'SYSTEM_SAVE__<kind>'.",
    )
    args = parser.parse_args()

    keep_regex = None
    if args.zip_dropins_keep_regex:
        keep_regex = re.compile(args.zip_dropins_keep_regex)

    keep_zip, delete_zip = plan_prune_zip_dropins(args.zip_dropins_keep_newest, keep_regex)
    keep_save, delete_save = plan_prune_save_exports(args.save_exports_keep_last_per_kind)

    delete_all = delete_zip + delete_save
    total_bytes = sum(c.bytes for c in delete_all)

    print(f"repo_root={REPO_ROOT}")
    print(f"apply={args.apply}")
    print(f"zip_dropins_keep_newest={args.zip_dropins_keep_newest} zip_dropins_keep_regex={args.zip_dropins_keep_regex!r}")
    print(f"save_exports_keep_last_per_kind={args.save_exports_keep_last_per_kind}")
    print(f"delete_count={len(delete_all)} delete_bytes={_fmt_bytes(total_bytes)}")

    if delete_all:
        print("first_50_delete_paths:")
        for cand in delete_all[:50]:
            print(f"- {cand.path.relative_to(REPO_ROOT)} ({_fmt_bytes(cand.bytes)})")

    if not args.apply:
        return 0

    for cand in delete_all:
        _safe_unlink(cand.path)
        # allow filesystem to settle for large deletes
        time.sleep(0.01)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

