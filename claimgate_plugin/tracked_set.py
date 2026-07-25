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

AND THE SECOND MISTAKE, worth recording because it looked like the fix. The first
repair re-froze inside a "clean checkout" built as:

    git archive HEAD | tar -x -C $TMP && cd $TMP && git init && git add -A

That is NOT a faithful copy of the committed set. `git add -A` re-applies
.gitignore, but git happily tracks files added BEFORE a matching ignore rule
existed — so the temp repo tracked 1871 receipts where the real repo tracks 2198.
CI then reported 327 NEW ORPHANs, all under system_v4/, and the baseline looked
wrong in the opposite direction from the first attempt.

There is no need for a temp clone at all: `git ls-files` in the real repo already
IS the committed set. Freeze in place, filtered by this module, and verify the
count against a CI run before trusting it. (Working-tree digests equal committed
digests only when no tracked file is dirty — check `git diff --name-only HEAD`
before freezing.)

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
