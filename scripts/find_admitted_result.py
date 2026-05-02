#!/usr/bin/env python3
"""Locate the strict-admissible result JSON for a just-run probe."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

from receipt_schema import relpath, repo_root, result_dir, validate_result_path


RESULT_LITERAL_RE = re.compile(r"([A-Za-z0-9_./ -]+_results\.json)")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--basename", required=True, help="Probe basename without .py.")
    parser.add_argument("--probe", default=None, help="Probe path that was just executed.")
    parser.add_argument(
        "--run-start",
        type=float,
        default=0.0,
        help="Unix timestamp captured immediately before the probe process started.",
    )
    parser.add_argument("--repo-root", default=str(root))
    parser.add_argument("--result-dir", default=None)
    parser.add_argument(
        "--path-only",
        action="store_true",
        help="Print only the admitted result path and suppress JSON output.",
    )
    return parser.parse_args()


def _add_unique(paths: list[Path], path: Path) -> None:
    if path not in paths:
        paths.append(path)


def _literal_result_paths(probe: Path, result_root: Path, root: Path) -> Iterable[Path]:
    try:
        text = probe.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    paths: list[Path] = []
    for raw in RESULT_LITERAL_RE.findall(text):
        path = Path(raw)
        if path.is_absolute():
            paths.append(path)
        elif path.parent == Path("."):
            paths.append(result_root / path.name)
        elif path.parts and path.parts[0] == "system_v4":
            paths.append(root / path)
        else:
            paths.append(probe.parent / path)
    return paths


def candidate_paths(
    *,
    root: Path,
    basename: str,
    probe: Path,
    result_root: Path,
    run_start: float,
) -> list[Path]:
    candidates: list[Path] = []
    _add_unique(candidates, result_root / f"{basename}_results.json")
    if basename.startswith("sim_"):
        _add_unique(candidates, result_root / f"{basename.removeprefix('sim_')}_results.json")

    for path in _literal_result_paths(probe, result_root, root):
        _add_unique(candidates, path if path.is_absolute() else root / path)

    if result_root.exists() and run_start > 0:
        recent = sorted(
            (
                path
                for path in result_root.glob("*_results.json")
                if path.stat().st_mtime >= run_start - 2
            ),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        for path in recent:
            _add_unique(candidates, path)

    return candidates


def find_admitted_result(
    *,
    root: Path,
    basename: str,
    probe: Path,
    result_root: Path,
    run_start: float,
) -> dict[str, object]:
    candidates = candidate_paths(
        root=root,
        basename=basename,
        probe=probe,
        result_root=result_root,
        run_start=run_start,
    )
    rejections: list[dict[str, object]] = []
    for path in candidates:
        if not path.exists():
            rejections.append(
                {
                    "path": relpath(path, root),
                    "exists": False,
                    "hard_finding_count": 1,
                }
            )
            continue
        record = validate_result_path(
            path,
            root=root,
            strict_scope=True,
            require_executable=True,
            require_run_boundary=True,
        )
        if record["ok"]:
            return {
                "all_pass": True,
                "admitted_result": str(path),
                "admitted_result_rel": relpath(path, root),
                "candidate_count": len(candidates),
                "rejections": rejections,
            }
        rejections.append(
            {
                "path": relpath(path, root),
                "exists": True,
                "hard_finding_count": len(record.get("hard_findings", [])),
                "warning_count": len(record.get("warnings", [])),
            }
        )

    return {
        "all_pass": False,
        "admitted_result": None,
        "candidate_count": len(candidates),
        "rejections": rejections[:20],
    }


def main() -> int:
    args = parse_args()
    root = Path(args.repo_root)
    result_root = Path(args.result_dir) if args.result_dir else result_dir(root)
    probe = Path(args.probe) if args.probe else root / "system_v4" / "probes" / f"{args.basename}.py"
    report = find_admitted_result(
        root=root,
        basename=args.basename,
        probe=probe,
        result_root=result_root,
        run_start=args.run_start,
    )
    if args.path_only:
        if report["all_pass"] and report["admitted_result"]:
            print(report["admitted_result"])
            return 0
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
