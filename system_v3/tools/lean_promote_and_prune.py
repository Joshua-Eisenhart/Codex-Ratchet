#!/usr/bin/env python3
"""
Lean housekeeping for Codex Ratchet.

Goal: keep the repo usable by deleting disposable artifacts (runs/work caches)
after their useful outputs are promoted into persistent state (A2/A1 brains, specs).

This tool is intentionally conservative by default:
- It DRY-RUNs unless --apply is provided.
- It deletes only within known bloat roots: system_v3/runs, work, archive/work_archives__*
- It uses an allowlist of paths to KEEP under those roots.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import shutil
import stat
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Policy:
    name: str
    roots: tuple[Path, ...]
    keep_globs: tuple[str, ...]
    # Safety: never delete these even if not matched by keep globs (within roots only).
    hard_keep_globs: tuple[str, ...] = ()


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except Exception:
        return str(path)


def _matches_any_glob(rel_path: str, globs: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(rel_path, g) for g in globs)


def _iter_children(root: Path) -> Iterable[Path]:
    if not root.exists():
        return
    for child in sorted(root.iterdir()):
        yield child


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
        return
    if path.is_dir():
        def _onerror(func, p, exc_info):  # noqa: ANN001
            # Best-effort: make writable and retry.
            try:
                os.chmod(p, stat.S_IWUSR | stat.S_IRUSR | stat.S_IXUSR)
            except Exception:
                pass
            try:
                func(p)
            except Exception:
                pass

        # On macOS/APFS we can see transient "Directory not empty" if something
        # is writing into the directory while we delete. Retry a few times.
        last_exc: Exception | None = None
        for _ in range(5):
            try:
                shutil.rmtree(path, onerror=_onerror)
                last_exc = None
                break
            except OSError as e:
                last_exc = e
                time.sleep(0.1)
        if last_exc is not None:
            raise last_exc
        return
    # Fallback (e.g., weird types)
    path.unlink(missing_ok=True)


def _policy_default() -> Policy:
    """
    Default policy: keep only persistent brains/specs + audit harness + current templates.

    This matches the user's stated intent: "learn and delete", and that anything deleted
    can be regenerated, with the persistent brain being the long-term memory.
    """
    roots = (
        REPO_ROOT / "system_v3" / "runs",
        REPO_ROOT / "work",
        REPO_ROOT / "archive",
    )

    keep = (
        # system_v3/runs: keep minimal pointers/state only
        "system_v3/runs/_CURRENT_STATE/**",
        "system_v3/runs/_CURRENT_RUN.txt",
        "system_v3/runs/_RUNS_REGISTRY.jsonl",
        "system_v3/runs/_save_exports/**",
        # work: keep tooling + templates + audits + curated
        "work/golden_tests/**",
        "work/zip_dropins/**",
        "work/zip_job_templates/**",
        "work/zip_subagents/**",
        "work/curated_zips/**",
        # shared coordination surfaces (Codex <-> Minimax)
        "work/coordination_sandbox__codex_minimax__noncanonical_delete_safe/**",
        "work/minimax_spillover_quarantine/**",
        "work/ANALYSIS_SUMMARY.md",
        "work/00_READ_FIRST__A2_A1_REFINERY_v1.md",
        "work/LEAN_POLICY__READ_ME_FIRST__v1.md",
        # if you keep a persistent brain snapshot outside system_v3, keep it explicitly
        "work/a2_brain_persistent__v1/**",
        "work/a1_brain_persistent__v1/**",
        # operator-facing "current context" and inbox for cross-agent handoff
        "work/_KEEP/**",
        "work/INBOX/**",
        "work/CURRENT.md",
        # archive: keep nothing by default; if you want to preserve specific archives,
        # add explicit keep globs for them.
    )

    hard_keep = (
        # never delete git or core docs, even if rooted misconfigured
        ".git/**",
        "core_docs/**",
        "system_v3/a2_state/**",
        "system_v3/specs/**",
        "system_v3/runtime/**",
        "system_v3/tools/**",
    )

    return Policy(
        name="default_lean_policy_v1",
        roots=roots,
        keep_globs=keep,
        hard_keep_globs=hard_keep,
    )


def _collect_deletions(policy: Policy) -> tuple[list[Path], list[Path]]:
    delete: list[Path] = []
    keep: list[Path] = []

    keep_globs = tuple(policy.keep_globs) + tuple(policy.hard_keep_globs)

    for root in policy.roots:
        for child in _iter_children(root):
            rel_child = _rel(child)
            if _matches_any_glob(rel_child, keep_globs) or _matches_any_glob(rel_child + "/**", keep_globs):
                keep.append(child)
                continue

            # If the child is a directory, we might still want to keep some nested keep_globs.
            # Rule: if any keep glob is under this directory, keep it.
            prefix = rel_child.rstrip("/") + "/"
            if any(g.startswith(prefix) for g in keep_globs):
                keep.append(child)
                continue

            delete.append(child)

    return delete, keep


def _bytes(path: Path) -> int:
    if path.is_symlink() or path.is_file():
        try:
            return path.lstat().st_size
        except Exception:
            return 0
    total = 0
    try:
        for p in path.rglob("*"):
            if p.is_file() and not p.is_symlink():
                try:
                    total += p.stat().st_size
                except Exception:
                    pass
    except Exception:
        pass
    return total


def _format_bytes(n: int) -> str:
    # Simple human formatter
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.1f}{unit}" if unit != "B" else f"{n}B"
        n /= 1024
    return f"{n:.1f}TB"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Actually delete files. Default is dry-run.")
    ap.add_argument("--json", action="store_true", help="Emit JSON report to stdout.")
    ap.add_argument("--max-delete", type=int, default=10_000, help="Safety cap on number of deletions.")
    args = ap.parse_args()

    policy = _policy_default()
    to_delete, to_keep = _collect_deletions(policy)

    if len(to_delete) > args.max_delete:
        raise SystemExit(f"Refusing: delete_count={len(to_delete)} exceeds --max-delete={args.max_delete}")

    delete_bytes = sum(_bytes(p) for p in to_delete)

    report = {
        "schema": "LEAN_PROMOTE_AND_PRUNE_REPORT_v1",
        "policy_name": policy.name,
        "repo_root": str(REPO_ROOT),
        "apply": bool(args.apply),
        "delete_count": len(to_delete),
        "delete_bytes": delete_bytes,
        "delete_bytes_human": _format_bytes(delete_bytes),
        "delete_paths": [_rel(p) for p in to_delete],
        "keep_roots": [_rel(r) for r in policy.roots],
        "keep_globs": list(policy.keep_globs),
        "hard_keep_globs": list(policy.hard_keep_globs),
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"policy={policy.name}")
        print(f"apply={args.apply}")
        print(f"delete_count={len(to_delete)} delete_bytes={report['delete_bytes_human']}")
        print("first_50_delete_paths:")
        for p in report["delete_paths"][:50]:
            print(f"- {p}")
        if len(report["delete_paths"]) > 50:
            print(f"... ({len(report['delete_paths']) - 50} more)")

    if not args.apply:
        return 0

    # Apply deletions
    for p in to_delete:
        # final safety: only delete inside policy roots
        if not any(str(p).startswith(str(r) + os.sep) or p == r for r in policy.roots):
            raise SystemExit(f"Refusing to delete outside roots: {_rel(p)}")
        _remove_path(p)

    return 0


if __name__ == "__main__":
    sys.exit(main())
