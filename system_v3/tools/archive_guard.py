#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def _infer_repo_root(start: Path) -> Path:
    cur = start.resolve()
    if cur.is_file():
        cur = cur.parent
    for _ in range(10):
        if (cur / "system_v3").is_dir():
            return cur
        cur = cur.parent
    return start.resolve()


def _resolve_repo_root(repo_root_raw: str) -> Path:
    raw = str(repo_root_raw or "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    env = str(os.environ.get("CODEX_RATCHET_ROOT", "") or "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return _infer_repo_root(Path(__file__).resolve())


def _dir_size_bytes(root: Path) -> int:
    total = 0
    if not root.exists():
        return total
    for p in root.rglob("*"):
        if p.is_file():
            total += p.stat().st_size
    return total


def _largest_files(root: Path, top_n: int) -> list[dict]:
    rows: list[dict] = []
    if not root.exists():
        return rows
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        try:
            size = p.stat().st_size
        except FileNotFoundError:
            continue
        rows.append({"path": str(p), "bytes": int(size)})
    rows.sort(key=lambda r: r["bytes"], reverse=True)
    return rows[: max(0, int(top_n))]


def main() -> int:
    parser = argparse.ArgumentParser(description="Report archive tier sizes and largest files.")
    parser.add_argument(
        "--repo-root",
        default="",
        help="Repository root. If omitted, uses $CODEX_RATCHET_ROOT, else infers from script path.",
    )
    parser.add_argument("--max-cache-bytes", type=int, default=2_000_000_000)
    parser.add_argument("--max-deep-bytes", type=int, default=20_000_000_000)
    parser.add_argument("--top-n", type=int, default=20)
    args = parser.parse_args()

    root = _resolve_repo_root(args.repo_root)

    archive_root = root / "archive"
    cache_root = archive_root / "CACHE__HIGH_ENTROPY__RECENT__PURGEABLE"
    deep_root = archive_root / "DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY"
    legacy_root = archive_root / "LEGACY_REFERENCE__READ_ONLY"

    cache_bytes = _dir_size_bytes(cache_root)
    deep_bytes = _dir_size_bytes(deep_root)
    legacy_bytes = _dir_size_bytes(legacy_root)
    total_bytes = _dir_size_bytes(archive_root)

    report = {
        "root": str(archive_root),
        "tiers": {
            "cache": {"path": str(cache_root), "bytes": cache_bytes, "max_bytes": int(args.max_cache_bytes)},
            "deep": {"path": str(deep_root), "bytes": deep_bytes, "max_bytes": int(args.max_deep_bytes)},
            "legacy_reference": {"path": str(legacy_root), "bytes": legacy_bytes},
        },
        "total_bytes": total_bytes,
        "largest_files": _largest_files(archive_root, top_n=args.top_n),
        "status": "PASS" if (cache_bytes <= int(args.max_cache_bytes) and deep_bytes <= int(args.max_deep_bytes)) else "FAIL",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
