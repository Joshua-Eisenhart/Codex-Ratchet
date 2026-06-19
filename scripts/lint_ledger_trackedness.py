#!/usr/bin/env python3
"""Flag untracked sim roots and untracked core sim files."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


DEFAULT_LEDGER = Path("system_v6/receipts/qubit_ladder_climb_ledger_20260612.md")
DEFAULT_SIMS = Path("system_v6/sims")


def repo_root() -> Path:
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        raise SystemExit(f"failed to locate git repo: {proc.stderr.strip()}")
    return Path(proc.stdout.strip())


def repo_relative(path: Path, repo: Path) -> str:
    try:
        rel_path = path.relative_to(repo)
    except ValueError as exc:
        raise SystemExit(f"path is outside git repo: {path}") from exc
    return rel_path.as_posix()


def run_git(repo: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def tracked_files_under(repo: Path, sim_dir: Path) -> list[str]:
    proc = run_git(repo, ["ls-files", repo_relative(sim_dir, repo)])
    if proc.returncode != 0:
        raise SystemExit(f"git ls-files failed for {sim_dir}: {proc.stderr.strip()}")
    return [line for line in proc.stdout.splitlines() if line.strip()]


def load_sim_dirs(sims_root: Path) -> list[Path]:
    if not sims_root.is_dir():
        raise SystemExit(f"missing sims dir: {sims_root}")
    return sorted(child for child in sims_root.iterdir() if child.is_dir())


def tracked_files_set(repo: Path, root: Path) -> set[str]:
    proc = run_git(repo, ["ls-files", repo_relative(root, repo)])
    if proc.returncode != 0:
        raise SystemExit(f"git ls-files failed for {root}: {proc.stderr.strip()}")
    return {line for line in proc.stdout.splitlines() if line.strip()}


def core_files(sim_dir: Path) -> list[Path]:
    candidates: set[Path] = set()
    candidates.update(path for path in sim_dir.glob("*.py") if path.is_file())
    candidates.update(path for path in sim_dir.glob("*_common.py") if path.is_file())
    candidates.update(path for path in sim_dir.glob("validate_*.py") if path.is_file())

    results_dir = sim_dir / "results"
    if results_dir.is_dir():
        candidates.update(path for path in results_dir.glob("*.json") if path.is_file())

    return sorted(
        path
        for path in candidates
        if "__pycache__" not in path.parts and path.suffix != ".pyc"
    )


def lint(_ledger: Path, sims_root: Path, repo: Path) -> dict[str, object]:
    flags: list[dict[str, object]] = []
    tracked_files = tracked_files_set(repo, sims_root)

    for sim_dir in load_sim_dirs(sims_root):
        rel_dir = repo_relative(sim_dir, repo)

        if not tracked_files_under(repo, sim_dir):
            flags.append(
                {
                    "dir": rel_dir,
                    "reason": "fully_untracked",
                    "files": [],
                }
            )

        untracked_core = [
            repo_relative(path, repo)
            for path in core_files(sim_dir)
            if repo_relative(path, repo) not in tracked_files
        ]
        if untracked_core:
            flags.append(
                {
                    "dir": rel_dir,
                    "reason": "uncommitted_core_files",
                    "files": untracked_core,
                }
            )

    return {"ok": not flags, "flags": flags}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Lint sim dirs for fully untracked roots and untracked core files."
    )
    parser.add_argument(
        "--ledger",
        type=Path,
        default=DEFAULT_LEDGER,
        help="Retained for CLI compatibility; linting is disk/git based.",
    )
    parser.add_argument("--sims-root", type=Path, default=DEFAULT_SIMS)
    args = parser.parse_args()

    repo = repo_root()
    ledger = args.ledger if args.ledger.is_absolute() else repo / args.ledger
    sims_root = args.sims_root if args.sims_root.is_absolute() else repo / args.sims_root
    result = lint(ledger, sims_root, repo)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
