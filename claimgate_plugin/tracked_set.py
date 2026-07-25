#!/usr/bin/env python3
"""The COMMITTED file set — the only thing CI can ever see.

WHY THIS EXISTS. Every baseline in this layer was first frozen from the WORKING
TREE, and every one of them then failed in CI for the same reason: CI checks out
committed files only. Measured on the first push:

    orphan set    frozen 2851 (working tree) vs 2202 in CI — 651 phantom "resolved"
    fixtures      4 pinned inputs reported PINNED FIXTURE MISSING; all four are
                  GITIGNORED generated files that can never reach CI at all

The inherited claimgate_plugin/ci_ratchet_baseline.json already documented this
trap and even carried the remeasure command. Reading the warning was not enough,
so the guard is now structural: freezing walks `git ls-files`, and a file the repo
does not track cannot be frozen by accident.

Asymmetry, on purpose:
  FREEZING  tracked-only — a baseline must describe what CI will see
  SWEEPING  everything present — a developer's new uncommitted receipt should
            still be checked locally before it is committed
"""
from __future__ import annotations

import subprocess
from pathlib import Path


def tracked_files(root: Path, suffix: str = ".json") -> set[str]:
    """Repo-relative POSIX paths git tracks. Empty set on failure is NOT returned:
    an unreadable index raises, because silently freezing nothing would look like
    a clean baseline."""
    out = subprocess.run(["git", "-C", str(root), "ls-files", "-z", f"*{suffix}"],
                         capture_output=True, text=True, check=True).stdout
    return {p for p in out.split("\0") if p}


def is_tracked(root: Path, rel: str, cache: dict) -> bool:
    if "set" not in cache:
        cache["set"] = tracked_files(root)
    return rel in cache["set"]
