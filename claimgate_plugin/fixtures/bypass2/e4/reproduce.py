"""Reproduce the index-tree versus export-archive lease mismatch."""
from __future__ import annotations

import subprocess
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from constraintbox.lease import VALID, issue_lease, materialize_tree, staged_tree_id, verify_lease


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )


def reproduce() -> dict[str, object]:
    repo = Path(tempfile.mkdtemp(prefix="claimgate-e4-git-")).resolve()
    checkout = Path(__file__).resolve().parents[5]
    if repo == checkout or checkout in repo.parents:
        raise RuntimeError("refusing to run Git inside the Codex-Ratchet checkout")

    try:
        _git(repo, "init", "-q")
        (repo / ".gitattributes").write_text(
            "bound-but-not-run.txt export-ignore\n", encoding="utf-8"
        )
        (repo / "bound-but-not-run.txt").write_text(
            "present in the bound index tree\n", encoding="utf-8"
        )
        (repo / "visible.txt").write_text(
            "present in both byte sets\n", encoding="utf-8"
        )
        _git(repo, "add", ".gitattributes", "bound-but-not-run.txt", "visible.txt")

        tree_id = staged_tree_id(repo)
        tree_files = _git(
            repo, "ls-tree", "-r", "--name-only", tree_id
        ).stdout.splitlines()
        with tempfile.TemporaryDirectory(prefix="claimgate-e4-materialized-") as temp:
            materialized = materialize_tree(repo, tree_id, Path(temp))
            materialized_files = sorted(
                str(path.relative_to(materialized))
                for path in materialized.rglob("*")
                if path.is_file()
            )

        absence_runner = [
            sys.executable,
            "-c",
            (
                "from pathlib import Path; "
                "raise SystemExit(1 if Path('bound-but-not-run.txt').exists() else 0)"
            ),
        ]
        lease = issue_lease(repo, [absence_runner], ttl_seconds=60.0)
        verdict = verify_lease(lease, staged_tree_id(repo), datetime.now(timezone.utc))
        admitted = (
            "bound-but-not-run.txt" in tree_files
            and "bound-but-not-run.txt" not in materialized_files
            and lease["tree_id"] == tree_id
            and lease["runners"][0]["exit_code"] == 0
            and verdict.status == VALID
        )
        return {
            "admitted": admitted,
            "temporary_repo_cleaned": True,
            "tree_id": tree_id,
            "tree_files": tree_files,
            "materialized_files": materialized_files,
            "lease_tree_match": lease["tree_id"] == tree_id,
            "runner_exit": lease["runners"][0]["exit_code"],
            "verdict": verdict.status,
            "reason": verdict.reason,
        }
    finally:
        shutil.rmtree(repo)
