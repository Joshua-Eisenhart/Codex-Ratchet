#!/usr/bin/env python3
"""Preflight for v5 clean rebuild batches."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[3]
V4_PROBES = pathlib.Path("system_v4/probes")
V5_ALLOWED_PREFIXES = (
    "system_v5/docs/",
    "system_v5/ops/formal_scouts/",
    "system_v5/ops/queue_cleanup/",
    "system_v5/ops/quarantine/",
    "system_v5/evidence/",
    ".tmp/",
)
GENERATED_SIZE_WARNING_BYTES = 1_000_000


def git_status() -> list[dict[str, str]]:
    proc = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    rows = []
    for line in proc.stdout.splitlines():
        if not line:
            continue
        rows.append({"status": line[:2].strip(), "path": line[3:]})
    return rows


def staged_files() -> list[pathlib.Path]:
    proc = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return [pathlib.Path(line) for line in proc.stdout.splitlines() if line]


def main() -> int:
    status_rows = git_status()
    staged = staged_files()
    errors = []
    warnings = []

    staged_v4 = [str(path) for path in staged if path.parts[:2] == V4_PROBES.parts]
    if staged_v4:
        errors.append({"kind": "staged_v4_probe_change", "paths": staged_v4[:50], "count": len(staged_v4)})

    staged_outside = [
        str(path)
        for path in staged
        if not any(path.as_posix().startswith(prefix) for prefix in V5_ALLOWED_PREFIXES)
    ]
    if staged_outside:
        warnings.append({"kind": "staged_outside_v5_rebuild_surfaces", "paths": staged_outside[:50], "count": len(staged_outside)})

    large_staged = []
    for path in staged:
        full = ROOT / path
        if full.exists() and full.stat().st_size > GENERATED_SIZE_WARNING_BYTES:
            large_staged.append({"path": str(path), "bytes": full.stat().st_size})
    if large_staged:
        warnings.append({"kind": "large_staged_artifact", "files": large_staged})

    pycache_dirs = [str(path.relative_to(ROOT)) for path in (ROOT / "system_v5" / "ops").rglob("__pycache__")]
    if pycache_dirs:
        errors.append({"kind": "runtime_byproduct_pycache", "paths": pycache_dirs})

    summary = {
        "schema": "V5_REBUILD_PREFLIGHT_v1",
        "staged_count": len(staged),
        "status_counts": {
            key: sum(1 for row in status_rows if row["status"] == key)
            for key in sorted({row["status"] for row in status_rows})
        },
        "errors": errors,
        "warnings": warnings,
        "pass": not errors,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
