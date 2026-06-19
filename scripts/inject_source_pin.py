#!/usr/bin/env python3
"""Inject current source SHA-256 pins into foundation result JSON files.

This is a metadata-only hardening pass. It reads each result's recorded
``source_path`` and writes only the top-level ``source_sha256`` field when the
field is absent or stale.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "system_v5/ops/formal_scouts/results"
PATTERNS = ("foundation_*results.json", "foundation_foundation_*results.json")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def foundation_results(results_dir: Path) -> list[Path]:
    files: set[Path] = set()
    for pattern in PATTERNS:
        files.update(results_dir.glob(pattern))
    return sorted(files)


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} is not a JSON object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def resolve_source(source_path: str) -> Path:
    path = Path(source_path)
    if not path.is_absolute():
        path = ROOT / path
    return path


def inject(results_dir: Path, apply: bool) -> dict[str, Any]:
    report: dict[str, Any] = {
        "matched": 0,
        "pinned": 0,
        "already_matching": 0,
        "stale_source_sha256": [],
        "missing_source_path": [],
        "missing_source_file": [],
        "errors": [],
    }
    for result_path in foundation_results(results_dir):
        report["matched"] += 1
        try:
            payload = load_json(result_path)
        except Exception as exc:
            report["errors"].append({"result": str(result_path), "error": str(exc)})
            continue

        source_value = payload.get("source_path")
        if not source_value:
            report["missing_source_path"].append(str(result_path))
            continue

        source_path = resolve_source(str(source_value))
        if not source_path.exists():
            report["missing_source_file"].append(
                {"result": str(result_path), "source_path": str(source_path)}
            )
            continue

        current_sha = sha256_file(source_path)
        recorded_sha = payload.get("source_sha256")
        if recorded_sha == current_sha:
            report["already_matching"] += 1
            continue

        if recorded_sha is not None:
            report["stale_source_sha256"].append(
                {
                    "result": str(result_path),
                    "recorded": recorded_sha,
                    "current": current_sha,
                }
            )
        payload["source_sha256"] = current_sha
        report["pinned"] += 1
        if apply:
            write_json(result_path, payload)

    report["applied"] = apply
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report changes without writing. Default writes metadata pins.",
    )
    args = parser.parse_args()

    report = inject(args.results_dir, apply=not args.check)
    print(json.dumps(report, indent=2))
    return 1 if report["missing_source_path"] or report["missing_source_file"] or report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
