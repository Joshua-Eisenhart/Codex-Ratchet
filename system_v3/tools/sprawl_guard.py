#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet")

ALLOWED_TOP_LEVEL_DIRS = {
    ".cursor",
    ".git",
    "archive",
    "core_docs",
    "system_v3",
}


def _dir_size_bytes(root: Path) -> int:
    total = 0
    if not root.exists():
        return total
    for p in root.rglob("*"):
        if p.is_file():
            total += p.stat().st_size
    return total


def main() -> int:
    parser = argparse.ArgumentParser(description="Guard top-level and run-surface sprawl.")
    parser.add_argument("--max-runs-total-bytes", type=int, default=2_000_000_000)
    parser.add_argument("--max-runs-count", type=int, default=200)
    parser.add_argument("--top-n-largest-runs", type=int, default=10)
    args = parser.parse_args()

    unexpected = []
    for p in sorted(ROOT.iterdir(), key=lambda x: x.name.lower()):
        if not p.is_dir():
            continue
        if p.name not in ALLOWED_TOP_LEVEL_DIRS:
            unexpected.append(str(p))

    runs_root = ROOT / "system_v3" / "runs"
    run_dirs = []
    if runs_root.exists():
        for p in runs_root.iterdir():
            if not p.is_dir():
                continue
            # Non-run buckets are explicitly prefixed.
            if p.name.startswith("_"):
                continue
            if p.name.startswith("LEGACY__"):
                continue
            run_dirs.append(p)
        run_dirs.sort(key=lambda p: p.name)
    largest_runs = []
    runs_total_bytes = 0
    for run_dir in run_dirs:
        size = _dir_size_bytes(run_dir)
        runs_total_bytes += size
        largest_runs.append({"run_id": run_dir.name, "bytes": size})
    largest_runs = sorted(largest_runs, key=lambda x: x["bytes"], reverse=True)[: max(0, int(args.top_n_largest_runs))]

    runs_count_ok = len(run_dirs) <= int(args.max_runs_count)
    runs_bytes_ok = runs_total_bytes <= int(args.max_runs_total_bytes)
    top_level_ok = len(unexpected) == 0

    report = {
        "root": str(ROOT),
        "allowed_top_level_dirs": sorted(ALLOWED_TOP_LEVEL_DIRS),
        "unexpected_top_level_dirs": unexpected,
        "run_surface": {
            "runs_root": str(runs_root),
            "runs_count": len(run_dirs),
            "runs_total_bytes": runs_total_bytes,
            "max_runs_count": int(args.max_runs_count),
            "max_runs_total_bytes": int(args.max_runs_total_bytes),
            "largest_runs": largest_runs,
            "runs_count_ok": runs_count_ok,
            "runs_bytes_ok": runs_bytes_ok,
        },
        "status": "PASS" if (top_level_ok and runs_count_ok and runs_bytes_ok) else "FAIL",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
