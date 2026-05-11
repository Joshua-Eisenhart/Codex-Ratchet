#!/usr/bin/env python3
"""
Repair duplicate queue completion records.

Done files are currently named as:
  <16hex>.json.<pid>.<hostname>.<worker>

When overlapping controllers processed the same id, multiple done files with the same
<16hex> can appear. That breaks queue-level accounting and can create ambiguous receipts.

This repair pass keeps only one canonical file per id (newest by mtime by default),
and moves duplicate completion records to queue/done/.duplicates for forensics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from datetime import datetime
import os


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DONE_DIR = PROJECT_ROOT / "system_v4" / "probes" / "a2_state" / "queue" / "done"
DUP_DIR = DONE_DIR / ".duplicates"
DEFAULT_REPORT_DIR = PROJECT_ROOT / "overnight_logs"
DEFAULT_REPORT_PATH = DEFAULT_REPORT_DIR / f"queue_done_duplicate_repair_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"


def parse_id(path: Path) -> str:
    name = path.name
    if ".json." not in name:
        return name
    return name.split(".json.")[0]


def _find_duplicates(paths: list[Path]) -> tuple[dict[str, list[Path]], int, int]:
    groups: dict[str, list[Path]] = defaultdict(list)
    for path in paths:
        groups[parse_id(path)].append(path)

    duplicates = {k: v for k, v in groups.items() if len(v) > 1}
    duplicate_bases = len(duplicates)
    duplicate_files = sum(len(v) - 1 for v in duplicates.values())
    return duplicates, duplicate_bases, duplicate_files


def _snapshot_duplicates_in_archive(dup_dir: Path) -> list[str]:
    return sorted(str(path.name) for path in dup_dir.glob("*.json.*"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_record(path: Path, *, base_dir: Path) -> dict[str, Any]:
    return {
        "name": path.name,
        "path": str(path),
        "relative_path": str(path.relative_to(base_dir.parent)),
        "base_id": parse_id(path),
        "sha256": _sha256(path),
        "size_bytes": path.stat().st_size,
        "mtime": path.stat().st_mtime,
    }


def _git_deleted_queue_done_manifest(done_dir: Path, dup_dir: Path) -> dict[str, Any]:
    try:
        status = subprocess.check_output(
            ["git", "status", "--short", "--", str(done_dir)],
            cwd=PROJECT_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        return {
            "available": False,
            "error": str(exc),
            "deleted_count": None,
            "missing_in_archive": [],
            "hash_mismatches": [],
            "records": [],
        }

    records: list[dict[str, Any]] = []
    missing: list[str] = []
    mismatches: list[str] = []
    for line in status.splitlines():
        if len(line) < 4:
            continue
        index_status = line[0]
        worktree_status = line[1]
        if "D" not in {index_status, worktree_status}:
            continue
        rel = line[3:]
        deleted_name = Path(rel).name
        archive_path = dup_dir / deleted_name
        if not archive_path.exists():
            missing.append(rel)
            records.append(
                {
                    "deleted_path": rel,
                    "archive_path": str(archive_path),
                    "archive_exists": False,
                    "head_sha256": None,
                    "archive_sha256": None,
                    "hash_match": False,
                }
            )
            continue
        try:
            head_bytes = subprocess.check_output(
                ["git", "show", f"HEAD:{rel}"],
                cwd=PROJECT_ROOT,
                stderr=subprocess.DEVNULL,
            )
            head_sha = hashlib.sha256(head_bytes).hexdigest()
        except subprocess.CalledProcessError:
            head_sha = None
        archive_sha = _sha256(archive_path)
        hash_match = bool(head_sha and head_sha == archive_sha)
        if not hash_match:
            mismatches.append(rel)
        records.append(
            {
                "deleted_path": rel,
                "archive_path": str(archive_path),
                "archive_exists": True,
                "base_id": parse_id(archive_path),
                "head_sha256": head_sha,
                "archive_sha256": archive_sha,
                "hash_match": hash_match,
            }
        )

    return {
        "available": True,
        "deleted_count": len(records),
        "missing_in_archive": missing,
        "missing_in_archive_count": len(missing),
        "hash_mismatches": mismatches,
        "hash_mismatch_count": len(mismatches),
        "all_deleted_receipts_archived": len(missing) == 0 and len(mismatches) == 0,
        "records": records,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--done-dir",
        type=Path,
        default=DONE_DIR,
        help=(
            "Use this done directory instead of the default project queue path. Useful for tests "
            "and controlled repair runs."
        ),
    )
    parser.add_argument(
        "--duplicates-dir",
        type=Path,
        default=None,
        help=(
            "Directory to quarantine duplicate done records. Defaults to <done-dir>/.duplicates "
            "when omitted."
        ),
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Move duplicate done entries into done/.duplicates. Without this flag, dry-run only.",
    )
    parser.add_argument(
        "--keep-newest",
        action="store_true",
        help="If multiple duplicates exist, keep the newest file and quarantine the rest.",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=None,
        help=(
            "Write report JSON to this path. If omitted, "
            "uses overnight_logs/queue_done_duplicate_repair_<timestamp>.json"
        ),
    )
    parser.add_argument(
        "--skip-archive-manifest",
        action="store_true",
        help="Do not include .duplicates archive snapshot in the repair report.",
    )
    parser.add_argument(
        "--include-git-deleted",
        action="store_true",
        help=(
            "Include a git-status based manifest proving tracked queue/done deletions have "
            "matching byte-for-byte archive files under .duplicates."
        ),
    )
    args = parser.parse_args()

    done_dir = args.done_dir
    dup_dir = args.duplicates_dir if args.duplicates_dir is not None else done_dir / ".duplicates"
    done_dir = Path(done_dir)
    dup_dir = Path(dup_dir)

    if not done_dir.is_dir():
        print(f"missing done_dir={done_dir}")
        return 1

    done = sorted(done_dir.glob("*.json.*"))
    duplicates, duplicate_bases, duplicate_files = _find_duplicates(done)
    pre_move_done_count = len(done)
    pre_move_duplicate_bases = duplicate_bases
    pre_move_duplicate_files = duplicate_files
    pre_archive_files = _snapshot_duplicates_in_archive(dup_dir)

    actions: list[dict[str, Any]] = []
    moved_files: list[str] = []

    for base_id, files in sorted(duplicates.items()):
        if args.keep_newest:
            files_sorted = sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)
        else:
            files_sorted = sorted(files, key=lambda p: p.name)
        keeper = files_sorted[0]
        drop = files_sorted[1:]
        actions.append(
            {
                "base_id": base_id,
                "keeper": keeper.name,
                "keeper_path": str(keeper),
                "keeper_sha256": _sha256(keeper),
                "keep_mtime": keeper.stat().st_mtime,
                "duplicate_count": len(drop),
                "dupes": [p.name for p in sorted(drop, key=lambda p: p.name)],
                "dupe_records": [
                    _file_record(p, base_dir=done_dir) for p in sorted(drop, key=lambda p: p.name)
                ],
            }
        )
        if not args.apply:
            continue
        for path in drop:
            dup_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(dup_dir / path.name))
            moved_files.append(path.name)

    report_path = args.report_path
    if report_path is None:
        report_path = os.environ.get("REPAIR_REPORT_PATH")
        if report_path:
            report_path = Path(report_path)
        else:
            report_path = DEFAULT_REPORT_PATH

    duplicate_manifest: list[dict[str, Any]] = []
    for action in actions:
        duplicate_manifest.append(
            {
                "base_id": action["base_id"],
                "keeper": action["keeper"],
                "keeper_path": action["keeper_path"],
                "keeper_sha256": action["keeper_sha256"],
                "moved": action["dupes"],
                "moved_records": action["dupe_records"],
            }
        )

    post_done = done
    post_duplicate_bases = pre_move_duplicate_bases
    post_duplicate_files = pre_move_duplicate_files
    post_archive_files = pre_archive_files

    if args.apply:
        post_done = sorted(done_dir.glob("*.json.*"))
        _, post_duplicate_bases, post_duplicate_files = _find_duplicates(post_done)
        post_archive_files = _snapshot_duplicates_in_archive(dup_dir)

    moved_from_done = []
    for candidate in post_archive_files:
        if candidate not in pre_archive_files:
            moved_from_done.append(candidate)
    removed_from_archive = [path for path in pre_archive_files if path not in post_archive_files]
    archive_delta = len(moved_from_done) - len(removed_from_archive)

    moved_from_done = sorted(moved_from_done)
    removed_from_archive = sorted(removed_from_archive)

    report = {
        "generated_at": datetime.now().isoformat(),
        "done_dir": str(done_dir),
        "duplicates_dir": str(dup_dir),
        "requested_done_dir": str(args.done_dir),
        "requested_duplicates_dir": str(args.duplicates_dir)
        if args.duplicates_dir is not None
        else None,
        "report_mode": "apply" if args.apply else "dry",
        "apply": bool(args.apply),
        "pre_repair_done_files": pre_move_done_count,
        "pre_repair_duplicate_bases": pre_move_duplicate_bases,
        "pre_repair_duplicate_files": pre_move_duplicate_files,
        "total_duplicate_bases": pre_move_duplicate_bases,
        "total_duplicate_files": pre_move_duplicate_files,
        "total_duplicate_count": len(actions),
        "post_repair_done_files": len(post_done),
        "post_repair_archive_files": len(post_archive_files),
        "post_repair_duplicate_bases": post_duplicate_bases,
        "post_repair_duplicate_files": post_duplicate_files,
        "applied": bool(args.apply),
        "kept_mode": "newest" if args.keep_newest else "lexicographic",
        "moved_count": sum(v["duplicate_count"] for v in actions) if args.apply else 0,
        "duplicate_count": len(actions),
        "actions": actions,
        "forensic_manifest": duplicate_manifest,
        "moved_files": moved_files,
        "moved_file_count": len(moved_files),
        "dry_run": not bool(args.apply),
        "pre_archive_duplicate_count": len(pre_archive_files),
        "post_archive_duplicate_count": len(post_archive_files),
        "archive_duplicate_added": moved_from_done,
        "archive_duplicate_removed": removed_from_archive,
        "archive_duplicate_delta_count": archive_delta,
        "pre_existing_archive_duplicate_files": len(pre_archive_files),
        "pre_existing_archive_duplicate_bases": len(Counter([f.split(".json.")[0] for f in pre_archive_files])),
        "seen_live_duplicate_files": pre_move_duplicate_files,
        "seen_live_duplicate_bases": pre_move_duplicate_bases,
        "archive_snapshot": {
            "pre_repair": sorted(pre_archive_files),
            "post_repair": sorted(post_archive_files),
        },
    }
    if not args.skip_archive_manifest:
        archive_paths = sorted(dup_dir.glob("*.json.*"))
        archived = [path.name for path in archive_paths]
        archived_bases = Counter([path.name.split(".json.")[0] for path in archive_paths])
        report["archive_duplicate_count"] = len(archived)
        report["archive_duplicate_bases"] = len(archived_bases)
        report["archive_duplicate_manifest"] = [
            {
                "base_id": base,
                "file_count": count,
                "files": sorted([n for n in archived if n.startswith(f"{base}.json.")]),
                "records": [
                    _file_record(path, base_dir=done_dir)
                    for path in archive_paths
                    if path.name.startswith(f"{base}.json.")
                ],
            }
            for base, count in sorted(archived_bases.items())
        ]
    if args.include_git_deleted:
        report["git_deleted_receipt_archive_manifest"] = _git_deleted_queue_done_manifest(
            done_dir,
            dup_dir,
        )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
